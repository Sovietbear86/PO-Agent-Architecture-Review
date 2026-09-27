import { test, expect } from '@playwright/test'
import fs from 'node:fs'

// A223R — P3..P8: re-gate all routed pages + chat against nested V4 payload.
// Captures the actual backend /api/v1/query capData the UI received AND the
// rendered DOM values, so post-analysis compares UI-vs-payload directly.
// Resumable per variant-key to a223r_pages.json. Capture-mode (always passes).
test.setTimeout(30_000_000)

const ROOT = '/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness'
const OUT = `${ROOT}/po-agent-platform-v2/qa_artifacts/a223r_pages.json`
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

function makeRecorder(page: any, seen: Set<string>, queries: any[]) {
  const onResponse = async (res: any) => {
    if (!res.url().includes('/api/v1/query')) return
    let body: any = null
    try { body = await res.json() } catch { body = null }
    let q = '?'
    try { q = res.request().postDataJSON()?.query ?? '?' } catch { q = '?' }
    const k = `${q}|${queries.length}`
    if (seen.has(k)) return
    seen.add(k)
    queries.push({ query: q, status: body?.status ?? null, capData: lastCapData(body?.data), warnings: Array.isArray(body?.warnings) ? body.warnings : [], answer: (body?.answer ?? '').slice(0, 400) })
  }
  return onResponse
}

const domScan = () => {
  const metricCards = Array.from(document.querySelectorAll('.metric-card')).map(el => ({ label: el.querySelector('span')?.textContent?.trim() ?? '', value: el.querySelector('strong')?.textContent?.trim() ?? '' }))
  const statePanels = Array.from(document.querySelectorAll('[data-testid="result-state-panel"]')).map(el => ({ state: el.getAttribute('data-state'), text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 200) }))
  const bodyText = document.body.innerText || ''
  const rawMd = { hash: (bodyText.match(/##/g) || []).length, bold: (bodyText.match(/\*\*/g) || []).length, tableSep: (bodyText.match(/\|\s*:?-{3,}:?\s*\|/g) || []).length, nan: (bodyText.match(/NaN|Infinity/g) || []).length }
  return { metricCards, statePanels, rawMd }
}

async function capturePage(page: any, key: string, path: string, setup: (page: any) => Promise<void>, expected: number) {
  const queries: any[] = []
  const seen = new Set<string>()
  const onResponse = makeRecorder(page, seen, queries)
  page.on('response', onResponse)
  await page.goto(BASE + path, { waitUntil: 'domcontentloaded', timeout: 60_000 })
  if (setup) await setup(page)
  const deadline = Date.now() + 210_000
  while (Date.now() < deadline) { await page.waitForTimeout(1500); if (queries.length >= expected) break }
  await page.waitForTimeout(900)
  page.off('response', onResponse)

  const dom = await page.evaluate(domScan)
  const shot = `${SHOTS}/${key}.png`
  await page.screenshot({ path: shot, fullPage: true })
  return { key, path, queries, ...dom, screenshot: shot }
}

async function setEntity(page: any, value: string, submitName: string) {
  const input = page.locator('.entity-toolbar input')
  await input.fill(value)
  await page.getByRole('button', { name: submitName }).click()
}

async function setTaskSearch(page: any, modeLabel: string, value: string) {
  if (modeLabel !== 'Текст') await page.getByRole('button', { name: modeLabel, exact: true }).first().click()
  const input = page.locator('.filter-input-row input')
  await input.fill(value)
  await page.getByRole('button', { name: 'Найти' }).click()
}

async function captureChat(page: any, query: string): Promise<any> {
  const queries: any[] = []
  const seen = new Set<string>()
  const onResponse = makeRecorder(page, seen, queries)
  page.on('response', onResponse)
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 60_000 })
  await page.getByRole('button', { name: 'Открыть PO Agent' }).click()
  await expect(page.getByPlaceholder('Спросите естественным языком…')).toBeVisible({ timeout: 30_000 })
  await page.getByPlaceholder('Спросите естественным языком…').fill(query)
  await page.getByRole('button', { name: 'Отправить' }).click()
  const loading = page.locator('[data-testid="agent-loading"]')
  await loading.waitFor({ state: 'visible', timeout: 30_000 })
  await loading.waitFor({ state: 'detached', timeout: 240_000 })
  await page.waitForTimeout(800)
  page.off('response', onResponse)
  const dom = await page.evaluate(() => {
    const bubbles = Array.from(document.querySelectorAll('.agent-drawer .message.agent .bubble')).map(b => (b.textContent || '').trim())
    const last = bubbles[bubbles.length - 1] ?? ''
    return {
      lastBubble: last.slice(0, 1200),
      raw: { hash: (last.match(/##/g) || []).length, bold: (last.match(/\*\*/g) || []).length, tableSep: (last.match(/\|\s*:?-{3,}:?\s*\|/g) || []).length },
      hasRichTable: document.querySelectorAll('.agent-drawer .answer-table').length,
      hasHeading: document.querySelectorAll('.agent-drawer .answer-heading').length,
      hasEvidence: document.querySelectorAll('.agent-drawer .chat-evidence').length,
      hasFeedback: document.querySelectorAll('.agent-drawer .feedback-row').length,
      optionButtons: document.querySelectorAll('.agent-drawer .option-row button').length,
    }
  })
  const shot = `${SHOTS}/chat_${query.replace(/[^\w-]+/g, '_').slice(0, 28)}.png`
  await page.screenshot({ path: shot, fullPage: false })
  return { query, queries, ...dom, screenshot: shot }
}

test('A223R P3-P8: pages + chat', async ({ browser }) => {
  fs.mkdirSync(SHOTS, { recursive: true })
  const out: any = { pages: {}, chat: {} }
  try { Object.assign(out, JSON.parse(fs.readFileSync(OUT, 'utf-8'))) } catch { }
  const context = await browser.newContext()
  const page = await context.newPage()

  const tasks: Array<{ key: string; run: () => Promise<any> }> = [
    { key: 'p3_overview', run: () => capturePage(page, 'p3_overview', '/', null, 4) },
    { key: 'p4_sprint_dms', run: () => capturePage(page, 'p4_sprint_dms', '/sprint', async (p) => { await setEntity(p, 'DMS-SPRNT-3', 'Обновить') }, 6) },
    { key: 'p5_release_wmb24q1', run: () => capturePage(page, 'p5_release_wmb24q1', '/releases', async (p) => { await setEntity(p, 'WMB 24Q1', 'Обновить') }, 5) },
    { key: 'p5_release_olp160', run: () => capturePage(page, 'p5_release_olp160', '/releases', async (p) => { await setEntity(p, 'OLP 1.6.0', 'Обновить') }, 5) },
    { key: 'p6_team', run: () => capturePage(page, 'p6_team', '/team', null, 6) },
    { key: 'p7_tasks_clarify', run: () => capturePage(page, 'p7_tasks_clarify', '/tasks', null, 1) },
    { key: 'p7_tasks_nonempty', run: () => capturePage(page, 'p7_tasks_nonempty', '/tasks', async (p) => { await setTaskSearch(p, 'Текст', 'DMS-380') }, 1) },
    { key: 'p7_tasks_notfound', run: () => capturePage(page, 'p7_tasks_notfound', '/tasks', async (p) => { await setTaskSearch(p, 'Текст', 'DMS-999999') }, 1) },
  ]

  for (const t of tasks) {
    if (out.pages[t.key]) { console.log(`[skip] ${t.key}`); continue }
    const rec = await t.run()
    out.pages[t.key] = rec
    fs.writeFileSync(OUT, JSON.stringify(out, null, 2))
    const sp = rec.statePanels.map((s: any) => s.state).join(',')
    console.log(`[${t.key}] q=${rec.queries.length} states=[${sp}] rawmd=${rec.rawMd.hash}h/${rec.rawMd.bold}b/${rec.rawMd.tableSep}t/nan=${rec.rawMd.nan} cards=${JSON.stringify(rec.metricCards)}`)
  }

  const chats = ['Сделай daily brief', 'рекомендуй исполнителя для DMS-380']
  for (const cq of chats) {
    const tag = cq.replace(/[^\w-]+/g, '_').slice(0, 28)
    if (out.chat[tag]) { console.log(`[skip chat] ${tag}`); continue }
    const rec = await captureChat(page, cq)
    out.chat[tag] = rec
    fs.writeFileSync(OUT, JSON.stringify(out, null, 2))
    console.log(`[chat:${tag}] status=${rec.queries[0]?.status} raw=${rec.raw.hash}h/${rec.raw.bold}b/${rec.raw.tableSep}t table=${rec.hasRichTable} head=${rec.hasHeading} ev=${rec.hasEvidence} fb=${rec.hasFeedback} opt=${rec.optionButtons}`)
  }
  console.log('A223R P3-P8 capture done')
})
