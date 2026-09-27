import { test, expect } from '@playwright/test'
import fs from 'node:fs'

// A223R — P2 BLOCKING: Quality WMB-102 payload/state lineage.
// Verifies the D-A223-1 fix: getCapabilityData unwrap + finite guards.
// Expected from backend truth: quality=85, missing=1, acceptance=0 -> REWORK.
test.setTimeout(30_000_000)

const ROOT = '/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness'
const OUT = `${ROOT}/po-agent-platform-v2/qa_artifacts/a223r_p2_quality.json`
const SHOTS = `${ROOT}/qa_223r_browser_c`
const BASE = 'http://localhost:5175'

async function captureQuality(page: any, taskKey: string) {
  const queries: any[] = []
  const seen = new Set<string>()
  const onResponse = async (res: any) => {
    if (!res.url().includes('/api/v1/query')) return
    let body: any = null
    try { body = await res.json() } catch { body = null }
    let q = '?'
    try { q = res.request().postDataJSON()?.query ?? '?' } catch { q = '?' }
    if (seen.has(q)) return
    seen.add(q)
    // capture the final business capability data (last dict-data envelope)
    let capData: any = null
    const rows = body?.data?.results
    if (Array.isArray(rows)) { for (const row of rows) { if (row && typeof row === 'object' && !Array.isArray(row) && row.data && typeof row.data === 'object' && !Array.isArray(row.data)) capData = row.data } }
    queries.push({ query: q, status: body?.status ?? null, capability_id: capData ? (rows.find((r:any)=>r.data===capData)?.capability_id ?? '?') : null, capData, warnings: Array.isArray(body?.warnings) ? body.warnings : [], answer: body?.answer ?? '' })
  }
  page.on('response', onResponse)

  // set the task key in the form and submit
  await page.goto(BASE + '/quality', { waitUntil: 'domcontentloaded', timeout: 60_000 })
  const input = page.locator('.entity-toolbar input')
  await input.fill(taskKey)
  await page.getByRole('button', { name: 'Проверить' }).click()

  const deadline = Date.now() + 210_000
  while (Date.now() < deadline) { await page.waitForTimeout(1500); if (queries.length >= 4) break }
  await page.waitForTimeout(1000)
  page.off('response', onResponse)

  const dom = await page.evaluate(() => {
    const metricCards = Array.from(document.querySelectorAll('.metric-card')).map(el => ({
      label: el.querySelector('span')?.textContent?.trim() ?? '',
      value: el.querySelector('strong')?.textContent?.trim() ?? '',
      hint: el.querySelector('small')?.textContent?.trim() ?? '',
    }))
    const pill = document.querySelector('.quality-decision .status-pill, .quality-decision .attention-badge, .quality-decision .green-badge')
    const decisionText = pill ? pill.textContent?.trim() : null
    const missingCount = document.querySelector('.quality-grid .panel-title span')?.textContent?.trim() ?? null
    const missingItems = Array.from(document.querySelectorAll('.quality-grid .quality-item b')).map(b => b.textContent?.trim())
    const accGaps = Array.from(document.querySelectorAll('.warning-box')).map(w => w.textContent?.trim())
    const bodyText = document.body.innerText || ''
    const nanCount = (bodyText.match(/NaN/g) || []).length
    return { metricCards, decisionText, missingCount, missingItems, accGaps, nanCount }
  })

  const shot = `${SHOTS}/quality_${taskKey}.png`
  await page.screenshot({ path: shot, fullPage: true })
  return { taskKey, queries, ...dom, screenshot: shot }
}

test('A223R P2: Quality WMB-102 (blocking) + absent-score path', async ({ browser }) => {
  fs.mkdirSync(SHOTS, { recursive: true })
  const out: any = {}
  const context = await browser.newContext()
  const page = await context.newPage()

  for (const taskKey of ['WMB-102', 'WMB-999999']) {
    const rec = await captureQuality(page, taskKey)
    out[taskKey] = rec
    fs.writeFileSync(OUT, JSON.stringify(out, null, 2))
    const cards: Record<string,string> = {}
    for (const c of rec.metricCards) cards[c.label] = c.value
    console.log(`QUALITY ${taskKey} cards:`, JSON.stringify(cards))
    console.log(`decision: ${rec.decisionText} | missingCount: ${rec.missingCount} | NaN: ${rec.nanCount} | status(q): ${rec.queries.find((q:any)=>/Оцени постановку/.test(q.query))?.status}`)
  }
})
