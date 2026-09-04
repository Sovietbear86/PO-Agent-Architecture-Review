import { expect, Page, Request, Route, test } from '@playwright/test'

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

type QueryObservation = {
  payload: QueryResponse
  browserSessionId: string
  requestHeaderSessionId: string | null
}

const SESSION_KEY = 'po-agent-runtime-session-id'

async function openAgent(page: Page) {
  await page.goto('/')
  await page.getByRole('button', { name: 'Открыть PO Agent' }).click()
  await expect(page.getByText(/Agent Core v3|Legacy Harness/).first()).toBeVisible()
}

/** Authoritative browser-side conversation identity. */
async function sessionId(page: Page): Promise<string> {
  const id = await page.evaluate(key => window.sessionStorage.getItem(key), SESSION_KEY)
  if (!id) throw new Error('Session ID missing in sessionStorage')
  return id
}

/** UI is observability only, but must eventually render the authoritative identity. */
async function expectVisibleSession(page: Page, expected: string) {
  await expect(page.getByText(`session: ${expected}`, { exact: true })).toBeVisible({ timeout: 10_000 })
}

async function ask(page: Page, query: string): Promise<QueryObservation> {
  // OverviewDashboard launches four unrelated background /api/v1/query calls.
  // Correlate the drawer call at REQUEST time, where Playwright exposes the
  // request headers reliably, then await the response belonging to that exact
  // Request object. This avoids both arbitrary-response races and the response
  // context limitations seen in Assignments 153-156.
  const browserSessionId = await sessionId(page)
  await expectVisibleSession(page, browserSessionId)

  let resolveDrawerRequest!: (request: Request) => void
  let rejectDrawerRequest!: (error: Error) => void
  const drawerRequestPromise = new Promise<Request>((resolve, reject) => {
    resolveDrawerRequest = resolve
    rejectDrawerRequest = reject
  })

  const routeHandler = async (route: Route) => {
    try {
      const request = route.request()
      const headers = request.headers()
      if (request.method() === 'POST' && headers['x-session-id'] === browserSessionId) {
        resolveDrawerRequest(request)
      }
      await route.continue()
    } catch (error) {
      rejectDrawerRequest(error instanceof Error ? error : new Error(String(error)))
      throw error
    }
  }

  await page.route('**/api/v1/query', routeHandler)

  try {
    const input = page.getByPlaceholder('Спросите естественным языком…')
    await input.fill(query)
    await page.getByRole('button', { name: 'Отправить' }).click()

    const request = await drawerRequestPromise
    const response = await request.response()
    if (!response) throw new Error(`No response object for drawer query: ${query}`)
    expect(response.ok(), `Query HTTP ${response.status()} for ${query}`).toBeTruthy()

    const requestHeaderSessionId = request.headers()['x-session-id'] ?? null
    const payload = await response.json() as QueryResponse

    await expect(page.getByText(new RegExp(`Agent Core v3.*${payload.status}`)).last()).toBeVisible({ timeout: 300_000 })
    const renderedText = payload.status === 'NEEDS_CLARIFICATION' ? payload.question : payload.answer
    if (renderedText) await expect(page.getByText(renderedText, { exact: true }).last()).toBeVisible({ timeout: 300_000 })
    await expectVisibleSession(page, browserSessionId)
    return { payload, browserSessionId, requestHeaderSessionId }
  } finally {
    await page.unroute('**/api/v1/query', routeHandler)
  }
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
    await expectVisibleSession(first, firstSession)

    await first.getByRole('button', { name: 'Новый диалог' }).click()
    const resetSession = await sessionId(first)
    expect(resetSession).toMatch(/^ui-/)
    expect(resetSession).not.toBe(firstSession)
    await expectVisibleSession(first, resetSession)
    await expect(first.getByText('Новый диалог создан. Предыдущий transient dialogue state не используется.')).toBeVisible()

    const second = await context.newPage()
    await openAgent(second)
    const secondSession = await sessionId(second)
    expect(secondSession).toMatch(/^ui-/)
    expect(secondSession).not.toBe(resetSession)
    await expectVisibleSession(second, secondSession)
    expect(await sessionId(first)).toBe(resetSession)
    await expectVisibleSession(first, resetSession)

    const observed = await ask(first, 'Задачи Гаранина')
    expect(observed.browserSessionId).toBe(resetSession)
    expect(observed.requestHeaderSessionId).toBe(resetSession)
    expect(observed.payload.session_id).toBe(resetSession)
    expect(observed.payload.status).not.toBe('NEEDS_CLARIFICATION')
    expect(observed.payload.warnings ?? []).not.toContain('correction_recheck')
    expect(observed.payload.warnings ?? []).not.toContain('correction_clarification')
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
      const browserSession = await sessionId(page)
      await expectVisibleSession(page, browserSession)

      const observed = await ask(page, query)
      const payload = observed.payload
      expect(observed.browserSessionId).toBe(browserSession)
      expect(observed.requestHeaderSessionId).toBe(browserSession)
      expect(payload.status).toBe('COMPLETED')
      expect(payload.session_id).toBe(browserSession)
      const meta = v3Meta(payload)
      expect(meta, 'Expected _agent_core_v3 metadata').not.toBeNull()
      expect(meta?.llm_used).toBe(true)

      await page.getByRole('button', { name: /Evidence .* trace/ }).last().click()
      await expect(page.getByText(`trace_id: ${payload.trace_id}`)).toBeVisible()
      await expect(page.getByText(`session_id: ${browserSession}`)).toBeVisible()
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
