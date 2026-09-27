import { test, expect } from '@playwright/test'
import fs from 'node:fs'

// A223R — P4 focused probe: Sprint DMS-SPRNT-3 Risk Queue title vs body + Throughput.
// Preserves the exact rendered panel text + the backend capData that caused it.
test.setTimeout(30_000_000)
const ROOT = '/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness'
const OUT = `${ROOT}/po-agent-platform-v2/qa_artifacts/a223r_p4_red.json`
const SHOTS = `${ROOT}/qa_223r_browser_c`
const BASE = 'http://localhost:5175'

test('A223R P4 red probe: sprint DMS-SPRNT-3', async ({ browser }) => {
  const context = await browser.newContext()
  const page = await context.newPage()
  const backend: any = {}
  page.on('response', async (res) => {
    if (!res.url().includes('/api/v1/query')) return
    let body: any = null; try { body = await res.json() } catch { return }
    let q = ''; try { q = res.request().postDataJSON()?.query ?? '' } catch { return }
    const rows = body?.data?.results
    let cap: any = null
    if (Array.isArray(rows)) for (const row of rows) { if (row?.data && typeof row.data === 'object') cap = row.data }
    backend[q] = { status: body?.status, capData: cap }
  })
  await page.goto(BASE + '/sprint', { waitUntil: 'domcontentloaded', timeout: 60_000 })
  // wait initial idle
  let d = Date.now() + 90_000
  while (Date.now() < d && (await page.evaluate(() => document.querySelectorAll('[data-state="LOADING"]').length)) > 0) await page.waitForTimeout(1000)
  await page.locator('.entity-toolbar input').fill('DMS-SPRNT-3')
  await page.getByRole('button', { name: 'Обновить' }).click()
  d = Date.now() + 210_000
  while (Date.now() < d) {
    const tq = await page.evaluate(() => 0)
    const loading = await page.evaluate(() => document.querySelectorAll('[data-state="LOADING"]').length)
    if (loading === 0 && backend['Покажи риски спринта DMS-SPRNT-3']) break
    await page.waitForTimeout(1500)
  }
  await page.waitForTimeout(700)

  const dom = await page.evaluate(() => {
    // find the Risk Queue panel (by its title)
    const panels = Array.from(document.querySelectorAll('.panel'))
    const rq = panels.find(p => /Risk Queue/i.test(p.querySelector('.panel-title')?.textContent ?? ''))
    const rqTitle = rq?.querySelector('.panel-title span')?.textContent?.trim() ?? null
    const rqBody = rq ? Array.from(rq.querySelectorAll('.risk-row')).map(r => (r.textContent || '').trim().slice(0, 60)) : null
    const rqMuted = rq?.querySelector('.muted')?.textContent?.trim() ?? null
    // Throughput insight card
    const insights = Array.from(document.querySelectorAll('.insight-card'))
    const tp = insights.find(c => /Throughput/.test(c.querySelector('.panel-title')?.textContent ?? ''))
    const tpValue = tp?.querySelector('.insight-value')?.textContent?.trim() ?? null
    const tpMuted = tp?.querySelector('.muted')?.textContent?.trim() ?? null
    return { rqTitle, rqBodyCount: rqBody?.length ?? null, rqBody: (rqBody ?? []).slice(0, 3), rqMuted, tpValue, tpMuted }
  })

  fs.writeFileSync(OUT, JSON.stringify({ dom, backend }, null, 2))
  console.log('RISK QUEUE:', JSON.stringify(dom.rqTitle), 'rows=', dom.rqBodyCount, 'muted=', JSON.stringify(dom.rqMuted))
  console.log('THROUGHPUT value=', JSON.stringify(dom.tpValue), 'muted=', JSON.stringify(dom.tpMuted))
  console.log('BACKEND risks capData count/queue:', JSON.stringify({ count: backend['Покажи риски спринта DMS-SPRNT-3']?.capData?.count, queueLen: backend['Покажи риски спринта DMS-SPRNT-3']?.capData?.queue?.length, sampleKeys: Object.keys(backend['Покажи риски спринта DMS-SPRNT-3']?.capData?.queue?.[0] ?? {}) }))
  console.log('BACKEND throughput capData:', JSON.stringify(backend['Покажи throughput DMS-SPRNT-3']?.capData))
  const shot = `${SHOTS}/p4_red_sprint.png`
  await page.screenshot({ path: shot, fullPage: true })
})
