import { expect, Page, Request, Route, test } from '@playwright/test'

type QueryResponse = {
  status: string
  answer?: string | null
  question?: string | null
  trace_id: string
  session_id: string
  runtime?: string
  ui?: { result_kind?: string; preferred_widget?: string | null } | null
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
  await expect(page.getByTestId('agent-runtime')).toContainText(/Agent Core v4|Legacy Harness/)
}

async function sessionId(page: Page): Promise<string> {
  const id = await page.evaluate(key => window.sessionStorage.getItem(key), SESSION_KEY)
  if (!id) throw new Error('Session ID missing in sessionStorage')
  return id
}

async function expectVisibleSession(page: Page, expected: string) {
  await expect(page.getByTestId('agent-session')).toHaveText(`session: ${expected}`)
}

async function ask(page: Page, query: string): Promise<QueryObservation> {
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
      if (request.method() === 'POST' && headers['x-session-id'] === browserSessionId) resolveDrawerRequest(request)
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
    const renderedText = payload.status === 'NEEDS_CLARIFICATION' ? payload.question : payload.answer
    if (renderedText) await expect(page.getByText(renderedText, { exact: true }).last()).toBeVisible({ timeout: 300_000 })
    await expectVisibleSession(page, browserSessionId)
    return { payload, browserSessionId, requestHeaderSessionId }
  } finally {
    await page.unroute('**/api/v1/query', routeHandler)
  }
}

function v4Meta(payload: QueryResponse): Record<string, unknown> | null {
  const meta = payload.data?.['_agent_core_v4']
  return meta && typeof meta === 'object' ? meta as Record<string, unknown> : null
}

test.describe('V4 real Workspace browser C', () => {
  test('session isolation and new conversation remain browser-authoritative', async ({ browser }) => {
    const context = await browser.newContext()
    const first = await context.newPage()
    await openAgent(first)

    const firstSession = await sessionId(first)
    expect(firstSession).toMatch(/^ui-/)
    await expectVisibleSession(first, firstSession)

    await first.getByRole('button', { name: 'Новый диалог' }).click()
    const resetSession = await sessionId(first)
    expect(resetSession).toMatch(/^ui-/)
    expect(resetSession).not.toBe(firstSession)
    await expectVisibleSession(first, resetSession)

    const second = await context.newPage()
    await openAgent(second)
    const secondSession = await sessionId(second)
    expect(secondSession).toMatch(/^ui-/)
    expect(secondSession).not.toBe(resetSession)
    expect(await sessionId(first)).toBe(resetSession)

    const observed = await ask(first, 'Покажи задачу DMS-380')
    expect(observed.browserSessionId).toBe(resetSession)
    expect(observed.requestHeaderSessionId).toBe(resetSession)
    expect(observed.payload.session_id).toBe(resetSession)
    await context.close()
  })

  const pilots = [
    'Покажи задачу DMS-380 и затем задачи ее исполнителя',
    'Покажи активные спринты DMS',
    'Покажи задачи текущего спринта DMS',
  ]

  for (const query of pilots) {
    test(`v4 browser pilot: ${query}`, async ({ page }) => {
      await openAgent(page)
      await expect(page.getByTestId('agent-runtime')).toContainText('Agent Core v4')
      await page.getByRole('button', { name: 'Новый диалог' }).click()
      const browserSession = await sessionId(page)

      const observed = await ask(page, query)
      const payload = observed.payload
      expect(observed.requestHeaderSessionId).toBe(browserSession)
      expect(payload.session_id).toBe(browserSession)
      expect(payload.runtime).toBe('agent_core_v4')
      expect(payload.status).toBe('COMPLETED')

      const meta = v4Meta(payload)
      expect(meta, 'Expected _agent_core_v4 metadata').not.toBeNull()
      expect(meta?.semantic_prepass_used).toBe(false)

      if (payload.ui) {
        await expect(page.getByTestId('v4-result-panel').last()).toBeVisible()
      }

      await page.getByRole('button', { name: /Evidence .* trace/ }).last().click()
      await expect(page.getByText(`trace_id: ${payload.trace_id}`)).toBeVisible()
      await expect(page.getByText(`session_id: ${browserSession}`)).toBeVisible()
      await expect(page.getByText(/runtime: Agent Core v4/)).toBeVisible()
    })
  }

  test('browser preserves fail-closed negative state', async ({ page }) => {
    await openAgent(page)
    const observed = await ask(page, 'Покажи задачи несуществующего человека Абракадаброва в DMS')
    expect(['FAILED', 'NEEDS_CLARIFICATION']).toContain(observed.payload.status)
    expect(observed.payload.runtime).toBe('agent_core_v4')
    expect((observed.payload.evidence ?? []).length).toBe(0)
  })
})
