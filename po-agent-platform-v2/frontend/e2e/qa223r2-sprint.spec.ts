import { test, expect } from '@playwright/test'
import fs from 'node:fs'

// A223R2 — P1 BLOCKING Sprint re-gate (DMS-SPRNT-3) + P2 regression.
// Verifies owner fix b069550: throughput `td.throughput`, risk queue `rd.queue`
// with row fields task_key/rank/reasons. Preserves rendered DOM + backend capData.
test.setTimeout(30_000_000)
const ROOT = '/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness'
const OUT = `${ROOT}/po-agent-platform-v2/qa_artifacts/a223r2_sprint.json`
const SHOTS = `${ROOT}/qa_223r2_browser_c`
const BASE = 'http://localhost:5175'

function lastCap(data: any): any {
  const rows = data?.results
  if (!Array.isArray(rows)) return null
  let cap: any = null
  for (const row of rows) if (row?.data && typeof row.data === 'object' && !Array.isArray(row.data)) cap = row.data
  return cap
}

async function captureSprint(page: any, sprint: string, key: string) {
  const backend: any = {}
  const onResponse = async (res: any) => {
    if (!res.url().includes('/api/v1/query')) return
    let body: any = null; try { body = await res.json() } catch { return }
    let q = ''; try { q = res.request().postDataJSON()?.query ?? '' } catch { return }
    if (q.includes(sprint)) backend[q] = { status: body?.status, capData: lastCap(body?.data), warnings: body?.warnings ?? [] }
  }
  page.on('response', onResponse)
  await page.goto(BASE + '/sprint', { waitUntil: 'domcontentloaded', timeout: 60_000 })
  // wait initial idle
  let d = Date.now() + 90_000
  while (Date.now() < d && (await page.evaluate(() => document.querySelectorAll('[data-state="LOADING"]').length)) > 0) await page.waitForTimeout(1000)
  await page.locator('.entity-toolbar input').fill(sprint)
  await page.getByRole('button', { name: 'Обновить' }).click()
  d = Date.now() + 210_000
  while (Date.now() < d) {
    const loading = await page.evaluate(() => document.querySelectorAll('[data-state="LOADING"]').length)
    if (loading === 0 && backend[`Покажи риски спринта ${sprint}`]) break
    await page.waitForTimeout(1500)
  }
  await page.waitForTimeout(800)
  page.off('response', onResponse)

  const dom = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.metric-card')).map(el => ({ label: el.querySelector('span')?.textContent?.trim() ?? '', value: el.querySelector('strong')?.textContent?.trim() ?? '' }))
    const insights = Array.from(document.querySelectorAll('.insight-card')).map(c => ({ title: c.querySelector('.panel-title strong')?.textContent?.trim(), value: c.querySelector('.insight-value')?.textContent?.trim(), muted: c.querySelector('.muted')?.textContent?.trim() }))
    const panels = Array.from(document.querySelectorAll('.panel'))
    const rq = panels.find(p => /Risk Queue/i.test(p.querySelector('.panel-title')?.textContent ?? ''))
    const rqTitle = rq?.querySelector('.panel-title span')?.textContent?.trim() ?? null
    const rqRows = rq ? Array.from(rq.querySelectorAll('.risk-row')).map(r => ({ key: r.querySelector('b')?.textContent?.trim(), mid: r.querySelector('span')?.textContent?.trim(), score: r.querySelector('em')?.textContent?.trim() })) : null
    const rqMuted = rq?.querySelector('.muted')?.textContent?.trim() ?? null
    const statePanels = Array.from(document.querySelectorAll('[data-testid="result-state-panel"]')).map(el => ({ state: el.getAttribute('data-state'), text: (el.textContent || '').trim().slice(0, 140) }))
    const body = document.body.innerText || ''
    return { cards, insights, rqTitle, rqRowCount: rqRows?.length ?? null, rqRows: (rqRows ?? []).slice(0, 4), rqMuted, statePanels, nan: (body.match(/NaN|Infinity/g) || []).length }
  })
  const shot = `${SHOTS}/${key}.png`
  await page.screenshot({ path: shot, fullPage: true })
  return { sprint, key, backend, ...dom, screenshot: shot }
}

test('A223R2 P1 sprint DMS-SPRNT-3 + P2 regression', async ({ browser }) => {
  fs.mkdirSync(SHOTS, { recursive: true })
  const out: any = {}
  const context = await browser.newContext()
  const page = await context.newPage()

  // P1 blocking: source-ready sprint with 38 risks
  const p1 = await captureSprint(page, 'DMS-SPRNT-3', 'p1_dms3')
  out.p1_dms3 = p1
  fs.writeFileSync(OUT, JSON.stringify(out, null, 2))
  console.log(`P1 DMS-SPRNT-3: rqTitle=${p1.rqTitle} rows=${p1.rqRowCount} muted=${JSON.stringify(p1.rqMuted)}`)
  console.log(`  rows sample=${JSON.stringify(p1.rqRows)}`)
  console.log(`  throughput=${p1.insights.find(i=>/Throughput/.test(i.title))?.value} wip=${p1.insights.find(i=>/WIP/.test(i.title))?.value} ready=${p1.insights.find(i=>/Готовность/.test(i.title))?.value}`)
  console.log(`  cards=${JSON.stringify(p1.cards)} nan=${p1.nan}`)
  console.log(`  backend throughput=${p1.backend['Покажи throughput DMS-SPRNT-3']?.capData?.throughput} risks.count=${p1.backend['Покажи риски спринта DMS-SPRNT-3']?.capData?.count} queue_len=${p1.backend['Покажи риски спринта DMS-SPRNT-3']?.capData?.queue?.length}`)

  // P2 regression: a sprint whose risk queue is genuinely empty (WMB-SPRNT-2 = 1 task)
  const p2 = await captureSprint(page, 'WMB-SPRNT-2', 'p2_wmb2')
  out.p2_wmb2 = p2
  fs.writeFileSync(OUT, JSON.stringify(out, null, 2))
  console.log(`P2 WMB-SPRNT-2 (empty-risk control): rqTitle=${p2.rqTitle} rows=${p2.rqRowCount} muted=${JSON.stringify(p2.rqMuted)} cards=${JSON.stringify(p2.cards)}`)
  console.log(`  backend risks.count=${p2.backend['Покажи риски спринта WMB-SPRNT-2']?.capData?.count} queue_len=${p2.backend['Покажи риски спринта WMB-SPRNT-2']?.capData?.queue?.length} status=${p2.backend['Покажи риски спринта WMB-SPRNT-2']?.status}`)
  console.log('A223R2 sprint re-gate capture done')
})
