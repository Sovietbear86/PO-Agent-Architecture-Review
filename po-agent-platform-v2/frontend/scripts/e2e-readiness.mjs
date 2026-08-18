const FRONTEND_URL = process.env.PO_E2E_FRONTEND_URL ?? 'http://127.0.0.1:5175'
const timeoutMs = Number(process.env.PO_E2E_TIMEOUT_MS ?? 5000)

function fail(message) {
  console.error(`E2E_READINESS_FAIL: ${message}`)
  process.exitCode = 1
}

async function request(path, init = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    return await fetch(`${FRONTEND_URL}${path}`, { ...init, signal: controller.signal })
  } finally {
    clearTimeout(timer)
  }
}

async function main() {
  console.log(`PO Agent frontend E2E readiness: ${FRONTEND_URL}`)

  const ui = await request('/')
  if (!ui.ok) return fail(`frontend returned HTTP ${ui.status}`)
  const html = await ui.text()
  if (!html.includes('id="root"')) return fail('frontend HTML does not contain #root mount point')
  console.log('PASS frontend shell reachable')

  const health = await request('/api/v1/health')
  if (!health.ok) return fail(`backend health through Vite proxy returned HTTP ${health.status}`)
  const healthPayload = await health.json()
  if (!['healthy', 'degraded'].includes(healthPayload.status)) {
    return fail(`unexpected health status: ${String(healthPayload.status)}`)
  }
  if (!healthPayload.runtime || !healthPayload.adapter) {
    return fail('health payload misses runtime/adapter identity')
  }
  console.log(`PASS API proxy -> ${healthPayload.runtime} / ${healthPayload.adapter} / ${healthPayload.status}`)

  const query = await request('/api/v1/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: 'Найди login', session_id: 'e2e-readiness' }),
  })
  if (!query.ok) return fail(`query returned HTTP ${query.status}`)
  const result = await query.json()
  if (!result.status || !result.trace_id || !result.session_id || !Array.isArray(result.evidence)) {
    return fail('query response does not satisfy frontend Harness contract')
  }
  if (!['COMPLETED', 'NEEDS_CLARIFICATION', 'PARTIAL', 'FAILED'].includes(result.status)) {
    return fail(`unknown Harness status: ${String(result.status)}`)
  }
  console.log(`PASS UI proxy -> FastAPI -> Harness query (${result.status}, trace=${result.trace_id})`)

  console.log('E2E_READINESS_GREEN')
}

main().catch((error) => {
  fail(error instanceof Error ? error.stack ?? error.message : String(error))
})
