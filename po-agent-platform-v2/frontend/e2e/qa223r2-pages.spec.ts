import { test, expect } from '@playwright/test'
import fs from 'node:fs'

// A223R2 — P3: finish P5-P8 from A223R on the new code (HEAD 970f15f).
// SprintPage was the only prod change, so this re-confirms Releases/Team/Tasks/Chat.
// New focus: Tasks LIST-MODE non-empty renders task cards from unwrapped payload.
test.setTimeout(30_000_000)
const ROOT = '/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness'
const OUT = `${ROOT}/po-agent-platform-v2/qa_artifacts/a223r2_pages.json`
const SHOTS = `${ROOT}/qa_223r2_browser_c`
const BASE = 'http://localhost:5175'

function lastCap(data: any): any {
  const rows = data?.results
  if (!Array.isArray(rows)) return null
  let cap: any = null
  for (const row of rows) if (row?.data && typeof row.data === 'object' && !Array.isArray(row.data)) cap = row.data
  return cap
}

const domScan = () => {
  const metricCards = Array.from(document.querySelectorAll('.metric-card')).map(el => ({ label: el.querySelector('span')?.textContent?.trim() ?? '', value: el.querySelector('strong')?.textContent?.trim() ?? '' }))
  const statePanels = Array.from(document.querySelectorAll('[data-testid="result-state-panel"]')).map(el => ({ state: el.getAttribute('data-state'), text: (el.textContent || '').trim().slice(0, 140) }))
  const body = document.body.innerText || ''
  const rawMd = { hash: (body.match(/##/g) || []).length, bold: (body.match(/\*\*/g) || []).length, tableSep: (body.match(/\|\s*:?-{3,}:?\s*\|/g) || []).length, nan: (body.match(/NaN|Infinity/g) || []).length }
  const taskCards = Array.from(document.querySelectorAll('.task-card')).map(c => (c.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 70))
  const muted = Array.from(document.querySelectorAll('.muted')).map(m => (m.textContent || '').trim())
  const gridCount = document.querySelector('.panel-title')?.parentElement?.querySelector('.panel-title span')?.textContent ?? null
  return { metricCards, statePanels, rawMd, taskCards: taskCards.length, taskCardSample: taskCards.slice(0, 3), muted, gridCount }
}

async function countLoading(page: any) { return page.evaluate(() => document.querySelectorAll('[data-state="LOADING"]').length) }

async function capture(page: any, key: string, path: string, setup: (page: any) => Promise<void>, targetToken: string, expected: number) {
  const backend: any = {}
  const onResponse = async (res: any) => {
    if (!res.url().includes('/api/v1/query')) return
    let body: any = null; try { body = await res.json() } catch { return }
    let q = ''; try { q = res.request().postDataJSON()?.query ?? '' } catch { return }
    if (q.includes(targetToken)) backend[q] = { status: body?.status, capData: lastCap(body?.data), warnings: body?.warnings ?? [] }
  }
  page.on('response', onResponse)
  await page.goto(BASE + path, { waitUntil: 'domcontentloaded', timeout: 60_000 })
  let d = Date.now() + 90_000
  while (Date.now() < d && (await countLoading(page)) > 0) await page.waitForTimeout(1000)
  if (setup) await setup(page)
  d = Date.now() + 210_000
  while (Date.now() < d) {
    const tq = Object.keys(backend).length
    if (tq >= expected && (await countLoading(page)) === 0) break
    await page.waitForTimeout(1500)
  }
  await page.waitForTimeout(700)
  page.off('response', onResponse)
  const dom = await page.evaluate(domScan)
  const shot = `${SHOTS}/${key}.png`
  await page.screenshot({ path: shot, fullPage: true })
  return { key, backend, ...dom, screenshot: shot }
}

async function setEntity(page: any, value: string) {
  await page.locator('.entity-toolbar input').fill(value)
  await page.getByRole('button', { name: 'Обновить' }).click()
}
async function taskMode(page: any, modeLabel: string, value: string) {
  await page.getByRole('button', { name: modeLabel, exact: true }).first().click()
  await page.locator('.filter-input-row input').fill(value)
  await page.getByRole('button', { name: 'Найти' }).click()
}
async function captureChat(page: any, query: string): Promise<any> {
  const backend: any = {}
  const onResponse = async (res: any) => {
    if (!res.url().includes('/api/v1/query')) return
    let body: any = null; try { body = await res.json() } catch { return }
    backend[(res.request().postDataJSON()?.query ?? '?')] = { status: body?.status, warnings: body?.warnings ?? [] }
  }
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
      lastBubble: last.slice(0, 400),
      raw: { hash: (last.match(/##/g) || []).length, bold: (last.match(/\*\*/g) || []).length, tableSep: (last.match(/\|\s*:?-{3,}:?\s*\|/g) || []).length },
      hasRichTable: document.querySelectorAll('.agent-drawer .answer-table').length,
      hasHeading: document.querySelectorAll('.agent-drawer .answer-heading').length,
      hasEvidence: document.querySelectorAll('.agent-drawer .chat-evidence').length,
      hasFeedback: document.querySelectorAll('.agent-drawer .feedback-row').length,
    }
  })
  const shot = `${SHOTS}/chat_${query.replace(/[^\w-]+/g, '_').slice(0, 24)}.png`
  await page.screenshot({ path: shot, fullPage: false })
  return { query, backendStatuses: Object.values(backend).map(b => b.status), ...dom, screenshot: shot }
}

test('A223R2 P3: releases/team/tasks/chat', async ({ browser }) => {
  fs.mkdirSync(SHOTS, { recursive: true })
  const out: any = { pages: {}, chat: {} }
  try { Object.assign(out, JSON.parse(fs.readFileSync(OUT, 'utf-8'))) } catch { }
  const context = await browser.newContext()
  const page = await context.newPage()

  const tasks = [
    { key: 'p5_release_olp160', run: () => capture(page, 'p5_release_olp160', '/releases', (p) => setEntity(p, 'OLP 1.6.0'), 'OLP 1.6.0', 5) },
    { key: 'p6_team', run: () => capture(page, 'p6_team', '/team', null, 'команды', 6) },
    { key: 'p7_tasks_sprint', run: () => capture(page, 'p7_tasks_sprint', '/tasks', (p) => taskMode(p, 'Спринт', 'DMS-SPRNT-3'), 'DMS-SPRNT-3', 1) },
    { key: 'p7_tasks_clarify', run: () => capture(page, 'p7_tasks_clarify', '/tasks', null, 'login', 1) },
    { key: 'p7_tasks_typed_empty', run: () => capture(page, 'p7_tasks_typed_empty', '/tasks', (p) => taskMode(p, 'Текст', 'zzzqqqxyz123'), 'zzzqqqxyz123', 1) },
  ]
  for (const t of tasks) {
    if (out.pages[t.key]) { console.log(`[skip] ${t.key}`); continue }
    const rec = await t.run()
    out.pages[t.key] = rec
    fs.writeFileSync(OUT, JSON.stringify(out, null, 2))
    const sp = rec.statePanels.map((s: any) => s.state).join(',')
    console.log(`[${t.key}] states=[${sp}] nan=${rec.rawMd.nan} taskCards=${rec.taskCards} muted=${JSON.stringify(rec.muted.slice(0, 2))}`)
    console.log(`   cards=${JSON.stringify(rec.metricCards)} sample=${JSON.stringify(rec.taskCardSample)}`)
  }
  for (const cq of ['Сделай daily brief', 'рекомендуй исполнителя для DMS-380']) {
    const tag = cq.replace(/[^\w-]+/g, '_').slice(0, 24)
    if (out.chat[tag]) { console.log(`[skip chat] ${tag}`); continue }
    const rec = await captureChat(page, cq)
    out.chat[tag] = rec
    fs.writeFileSync(OUT, JSON.stringify(out, null, 2))
    console.log(`[chat:${tag}] status=${JSON.stringify(rec.backendStatuses)} raw=${rec.raw.hash}h/${rec.raw.bold}b/${rec.raw.tableSep}t table=${rec.hasRichTable} head=${rec.hasHeading} ev=${rec.hasEvidence} fb=${rec.hasFeedback}`)
  }
  console.log('A223R2 P3 capture done')
})
