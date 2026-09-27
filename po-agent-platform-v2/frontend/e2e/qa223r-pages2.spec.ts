import { test, expect } from '@playwright/test'
import fs from 'node:fs'

// A223R — P3..P8 re-capture with DOM-based settle (fixes A223R-1 timing bug).
// For input-change pages: wait for initial idle, submit new value, then wait for
// (a) target-token queries to arrive AND (b) zero LOADING panels, then capture.
// Compares rendered DOM values against the actual backend capData received.
test.setTimeout(30_000_000)

const ROOT = '/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness'
const OUT = `${ROOT}/po-agent-platform-v2/qa_artifacts/a223r_pages2.json`
const SHOTS = `${ROOT}/qa_223r_browser_c`
const BASE = 'http://localhost:5175'

function lastCapData(data: any): any {
  const rows = data?.results
  if (!Array.isArray(rows)) return null
  let cap: any = null
  for (const row of rows) {
    if (row && typeof row === 'object' && !Array.isArray(row) && row.data && typeof row.data === 'object' && !Array.isArray(row.data)) cap = row.data
  }
  return cap
}

const domScan = () => {
  const metricCards = Array.from(document.querySelectorAll('.metric-card')).map(el => ({ label: el.querySelector('span')?.textContent?.trim() ?? '', value: el.querySelector('strong')?.textContent?.trim() ?? '' }))
  const statePanels = Array.from(document.querySelectorAll('[data-testid="result-state-panel"]')).map(el => ({ state: el.getAttribute('data-state'), text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 160) }))
  const bodyText = document.body.innerText || ''
  const rawMd = { hash: (bodyText.match(/##/g) || []).length, bold: (bodyText.match(/\*\*/g) || []).length, tableSep: (bodyText.match(/\|\s*:?-{3,}:?\s*\|/g) || []).length, nan: (bodyText.match(/NaN|Infinity/g) || []).length }
  const insightValues = Array.from(document.querySelectorAll('.insight-value')).map(e => e.textContent?.trim())
  const riskRows = Array.from(document.querySelectorAll('.risk-row')).map(r => (r.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 80))
  const muted = Array.from(document.querySelectorAll('.muted')).map(m => (m.textContent || '').trim())
  const memberRows = Array.from(document.querySelectorAll('.team-member-row')).map(r => (r.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 120))
  const taskCards = Array.from(document.querySelectorAll('.task-card')).map(c => (c.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 80))
  const factRows = Array.from(document.querySelectorAll('.fact-row')).map(f => (f.textContent || '').trim().replace(/\s+/g, ' '))
  const taskRows = Array.from(document.querySelectorAll('.task-row')).map(t => (t.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 80))
  const capacityRows = Array.from(document.querySelectorAll('.capacity-row')).map(c => (c.textContent || '').trim().replace(/\s+/g, ' '))
  return { metricCards, statePanels, rawMd, insightValues, riskRows: riskRows.length, riskRowText: riskRows.slice(0, 3), muted, memberRows, taskCards, factRows, taskRows, capacityRows, loadingCount: document.querySelectorAll('[data-state="LOADING"]').length }
}

async function countLoading(page: any): Promise<number> {
  return await page.evaluate(() => document.querySelectorAll('[data-state="LOADING"]').length)
}

async function capturePage(page: any, key: string, path: string, setup: (page: any) => Promise<void>, targetToken: string, expected: number) {
  const queries: any[] = []
  const onResponse = async (res: any) => {
    if (!res.url().includes('/api/v1/query')) return
    let body: any = null
    try { body = await res.json() } catch { body = null }
    let q = '?'
    try { q = res.request().postDataJSON()?.query ?? '?' } catch { q = '?' }
    queries.push({ query: q, status: body?.status ?? null, capData: lastCapData(body?.data), warnings: Array.isArray(body?.warnings) ? body.warnings : [] })
  }
  page.on('response', onResponse)
  await page.goto(BASE + path, { waitUntil: 'domcontentloaded', timeout: 60_000 })

  // 1) wait for initial default load to be idle
  let d = Date.now() + 90_000
  while (Date.now() < d && (await countLoading(page)) > 0) await page.waitForTimeout(1000)

  // 2) submit the target value
  if (setup) await setup(page)

  // 3) wait until target-token queries arrive AND no LOADING panels
  d = Date.now() + 210_000
  while (Date.now() < d) {
    const targetCount = queries.filter(q => q.query.includes(targetToken)).length
    const loading = await countLoading(page)
    if (targetCount >= expected && loading === 0) break
    await page.waitForTimeout(1500)
  }
  await page.waitForTimeout(700)
  page.off('response', onResponse)

  const dom = await page.evaluate(domScan)
  const shot = `${SHOTS}/${key}.png`
  await page.screenshot({ path: shot, fullPage: true })
  const targetQueries = queries.filter(q => q.query.includes(targetToken))
  return { key, path, targetQueries, allQueryCount: queries.length, ...dom, screenshot: shot }
}

async function setEntity(page: any, value: string, submitName: string) {
  await page.locator('.entity-toolbar input').fill(value)
  await page.getByRole('button', { name: submitName }).click()
}
async function setTaskSearch(page: any, value: string) {
  await page.locator('.filter-input-row input').fill(value)
  await page.getByRole('button', { name: 'Найти' }).click()
}

test('A223R P3-P8 re-capture (settled)', async ({ browser }) => {
  fs.mkdirSync(SHOTS, { recursive: true })
  const out: any = { pages: {}, chat: {} }
  try { Object.assign(out, JSON.parse(fs.readFileSync(OUT, 'utf-8'))) } catch { }
  const context = await browser.newContext()
  const page = await context.newPage()

  const tasks = [
    { key: 'p4_sprint_dms', run: () => capturePage(page, 'p4_sprint_dms', '/sprint', (p) => setEntity(p, 'DMS-SPRNT-3', 'Обновить'), 'DMS-SPRNT-3', 6) },
    { key: 'p5_release_olp160', run: () => capturePage(page, 'p5_release_olp160', '/releases', (p) => setEntity(p, 'OLP 1.6.0', 'Обновить'), 'OLP 1.6.0', 5) },
    { key: 'p5_release_wmb24q1', run: () => capturePage(page, 'p5_release_wmb24q1', '/releases', (p) => setEntity(p, 'WMB 24Q1', 'Обновить'), 'WMB 24Q1', 5) },
    { key: 'p6_team_bare', run: () => capturePage(page, 'p6_team_bare', '/team', null, 'команды', 6) },
    { key: 'p7_tasks_nonempty', run: () => capturePage(page, 'p7_tasks_nonempty', '/tasks', (p) => setTaskSearch(p, 'DMS-380'), 'DMS-380', 1) },
    { key: 'p7_tasks_empty', run: () => capturePage(page, 'p7_tasks_empty', '/tasks', (p) => setTaskSearch(p, 'zzzqqqxyz123'), 'zzzqqqxyz123', 1) },
    { key: 'p7_tasks_clarify', run: () => capturePage(page, 'p7_tasks_clarify', '/tasks', null, 'login', 1) },
  ]

  for (const t of tasks) {
    if (out.pages[t.key]) { console.log(`[skip] ${t.key}`); continue }
    const rec = await t.run()
    out.pages[t.key] = rec
    fs.writeFileSync(OUT, JSON.stringify(out, null, 2))
    const sp = rec.statePanels.map((s: any) => s.state).join(',')
    console.log(`[${t.key}] tq=${rec.targetQueries.length}/${t.key.includes('sprint')?6:5} states=[${sp}] nan=${rec.rawMd.nan} cards=${JSON.stringify(rec.metricCards)}`)
    if (rec.riskRows != null) console.log(`   riskRows=${rec.riskRows} muted=${JSON.stringify(rec.muted.slice(0,2))} insight=${JSON.stringify(rec.insightValues)}`)
    if (rec.taskCards) console.log(`   taskCards=${rec.taskCards.length} ${JSON.stringify(rec.taskCards.slice(0,2))}`)
    if (rec.memberRows) console.log(`   memberRows=${rec.memberRows.length} ${JSON.stringify(rec.memberRows.slice(0,2))} capRows=${rec.capacityRows.length}`)
  }
  console.log('A223R re-capture done')
})
