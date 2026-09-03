import { expect, Page, test } from '@playwright/test'

type QueryResponse = {
  status: string
  answer?: string | null
  question?: string | null
  trace_id: string
  session_id: string
  data?: Record<string, unknown> | null
  evidence?: Array<{ entity_id?: string | null; label?: string; source?: string }>
  warnings?: string[]
}

async function openAgent(page: Page) {
  await page.goto('/')
  await page.getByRole('button', { name: 'Открыть PO Agent' }).click()
  await expect(page.getByText(/Agent Core v3|Legacy Harness/).first()).toBeVisible()
}

async function sessionId(page: Page): Promise<string> {
  const text = await page.getByText(/^session: /).textContent()
  if (!text) throw new Error('Visible UI session id is missing')
  return text.replace(/^session:\s*/, '').trim()
}

async function ask(page: Page, query: string): Promise<QueryResponse> {
  const responsePromise = page.waitForResponse(response =>
    response.url().includes('/api/v1/query') && response.request().method() === 'POST'
  )
  const input = page.getByPlaceholder('Спросите естественным языком…')
  await input.fill(query)
  await page.getByRole('button', { name: 'Отправить' }).click()
  const response = await responsePromise
  expect(response.ok(), `Query HTTP ${response.status()} for ${query}`).toBeTruthy()
  const payload = await response.json() as QueryResponse

  await expect(page.getByText(new RegExp(`Agent Core v3.*${payload.status}`)).last()).toBeVisible({ timeout: 300_000 })
  const renderedText = payload.status === 'NEEDS_CLARIFICATION' ? payload.question : payload.answer
  if (renderedText) await expect(page.getByText(renderedText, { exact: true }).last()).toBeVisible({ timeout: 300_000 })
  return payload
}

function v3Meta(payload: QueryResponse): Record<string, unknown> | null {
  const meta = payload.data?.['_agent_core_v3']
  return meta && typeof meta === 'object' ? meta as Record<string, unknown> : null
}

test.describe('H0 real Workspace browser harness', () => {
  test('session isolation and new conversation are real browser behavior', async ({ browser }) => {
    const context = await browser.newContext()
    const first = await context.newPage()
    await openAgent(first)
    await expect(first.getByText(/Agent Core v3/).first()).toBeVisible()

    const firstSession = await sessionId(first)
    expect(firstSession).toMatch(/^ui-/)

    await first.getByRole('button', { name: 'Новый диалог' }).click()
    const resetSession = await sessionId(first)
    expect(resetSession).toMatch(/^ui-/)
    expect(resetSession).not.toBe(firstSession)
    await expect(first.getByText('Новый диалог создан. Предыдущий transient dialogue state не используется.')).toBeVisible()

    const second = await context.newPage()
    await openAgent(second)
    const secondSession = await sessionId(second)
    expect(secondSession).toMatch(/^ui-/)
    expect(secondSession).not.toBe(resetSession)
    expect(await sessionId(first)).toBe(resetSession)

    const firstTurn = await ask(first, 'Задачи Гаранина')
    expect(firstTurn.session_id).toBe(resetSession)
    expect(firstTurn.status).not.toBe('NEEDS_CLARIFICATION')
    expect(firstTurn.warnings ?? []).not.toContain('correction_recheck')
    expect(firstTurn.warnings ?? []).not.toContain('correction_clarification')
    await context.close()
  })

  const pilots = [
    'Задачи Гаранина',
    'Задачи Гаранина в DMS',
    'Задачи Калачанова в WMB',
    'Покажи DMS-380',
  ]

  for (const query of pilots) {
    test(`v3 browser pilot: ${query}`, async ({ page }) => {
      await openAgent(page)
      await expect(page.getByText(/Agent Core v3/).first()).toBeVisible()
      await page.getByRole('button', { name: 'Новый диалог' }).click()
      const visibleSession = await sessionId(page)

      const payload = await ask(page, query)
      expect(payload.status).toBe('COMPLETED')
      expect(payload.session_id).toBe(visibleSession)
      const meta = v3Meta(payload)
      expect(meta, 'Expected _agent_core_v3 metadata').not.toBeNull()
      expect(meta?.llm_used).toBe(true)

      await page.getByRole('button', { name: /Evidence .* trace/ }).last().click()
      await expect(page.getByText(`trace_id: ${payload.trace_id}`)).toBeVisible()
      await expect(page.getByText(`session_id: ${visibleSession}`)).toBeVisible()
      await expect(page.getByText(/runtime: Agent Core v3/)).toBeVisible()

      if (query.includes('WMB')) {
        const evidenceIds = (payload.evidence ?? []).map(item => item.entity_id).filter(Boolean) as string[]
        expect(evidenceIds.every(key => key.startsWith('WMB-')), `Wrong-space evidence: ${evidenceIds.join(', ')}`).toBeTruthy()
      }
      if (query.includes('DMS-380')) {
        await expect(page.getByText('DMS-380').last()).toBeVisible()
      }
    })
  }
})
