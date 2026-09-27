import { test, expect } from '@playwright/test'
import fs from 'node:fs'

// A223 — Browser C: UI state-lineage remediation batch 1.
// Walks all 6 pages + chat drawer. Captures backend /api/v1/query payloads,
// result-state panels, metric cards, raw-markdown scan. Hard RED determination
// is done in post-analysis; this spec captures rich data (always passes).
test.setTimeout(30_000_000)

const ROOT = '/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness'
const OUT = `${ROOT}/po-agent-platform-v2/qa_artifacts/a223_browser_c.json`
const SHOTS = `${ROOT}/qa_223_browser_c`
const BASE = 'http://localhost:5175'

type QP = { query: string; status: string | null; data: any; warnings: string[]; answer: string }

const PAGES = [
  { id: 'overview', path: '/' },
  { id: 'tasks', path: '/tasks' },
  { id: 'sprint', path: '/sprint' },
  { id: 'releases', path: '/releases' },
  { id: 'team', path: '/team' },
  { id: 'quality', path: '/quality' },
]

async function capturePage(page: any, id: string, path: string, expected: number): Promise<any> {
  const queries: QP[] = []
  const seen = new Set<string>()
  const onResponse = async (res: any) => {
    if (!res.url().includes('/api/v1/query')) return
    let body: any = null
    try { body = await res.json() } catch { body = null }
    let q = '?'
    try { q = res.request().postDataJSON()?.query ?? '?' } catch { q = '?' }
    const key = `${q}|${queries.length}`
    if (seen.has(q)) return
    seen.add(q)
    queries.push({
      query: q,
      status: body?.status ?? null,
      data: body?.data ?? null,
      warnings: Array.isArray(body?.warnings) ? body.warnings : [],
      answer: body?.answer ?? '',
    })
  }
  page.on('response', onResponse)
  await page.goto(BASE + path, { waitUntil: 'domcontentloaded', timeout: 60_000 })
  // wait for up to `expected` query responses or a settle timeout
  const deadline = Date.now() + 210_000
  while (Date.now() < deadline) {
    await page.waitForTimeout(1500)
    if (queries.length >= expected) break
    // settle early if nothing new for a long time is handled by deadline
  }
  page.off('response', onResponse)
  await page.waitForTimeout(800)

  const dom = await page.evaluate(() => {
    const statePanels = Array.from(document.querySelectorAll('[data-testid="result-state-panel"]')).map(el => ({
      state: el.getAttribute('data-state'),
      text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 300),
    }))
    const metricCards = Array.from(document.querySelectorAll('.metric-card')).map(el => {
      const span = el.querySelector('span')?.textContent?.trim() ?? ''
      const strong = el.querySelector('strong')?.textContent?.trim() ?? ''
      const small = el.querySelector('small')?.textContent?.trim() ?? ''
      return { label: span, value: strong, hint: small }
    })
    const bodyText = document.body.innerText || ''
    const rawMd = {
      hash: (bodyText.match(/##/g) || []).length,
      bold: (bodyText.match(/\*\*/g) || []).length,
      tableSep: (bodyText.match(/\|\s*:?-{3,}:?\s*\|/g) || []).length,
    }
    const briefCopy = document.querySelector('.brief-copy')?.textContent?.trim()?.slice(0, 600) ?? null
    const answerTables = document.querySelectorAll('.answer-table').length
    const answerHeadings = document.querySelectorAll('.answer-heading').length
    return { statePanels, metricCards, rawMd, briefCopy, answerTables, answerHeadings }
  })

  // page-specific captures
  const extras: any = {}
  if (id === 'team') {
    extras.capacityInput = await page.evaluate(() => {
      const inp = document.querySelector('input[placeholder="Пусто = owner policy"]') as HTMLInputElement | null
      return inp ? { value: inp.value, placeholder: inp.placeholder } : null
    })
    const capNote = await page.evaluate(() => document.querySelector('.release-note')?.textContent?.trim() ?? null)
    extras.competencyNote = capNote
  }
  if (id === 'quality') {
    extras.decision = await page.evaluate(() => {
      const pill = document.querySelector('.quality-decision .status-pill, .quality-decision .attention-badge, .quality-decision .green-badge')
      return pill ? pill.textContent?.trim() : null
    })
  }
  if (id === 'sprint' || id === 'releases') {
    extras.riskText = await page.evaluate(() => {
      const rows = Array.from(document.querySelectorAll('.risk-row'))
      const muted = Array.from(document.querySelectorAll('.muted')).map(m => m.textContent?.trim())
      return { riskRows: rows.length, muted: muted }
    })
  }

  const shot = `${SHOTS}/${id}.png`
  await page.screenshot({ path: shot, fullPage: true })
  return { id, path, queries, statePanels: dom.statePanels, metricCards: dom.metricCards, rawMd: dom.rawMd, briefCopy: dom.briefCopy, answerTables: dom.answerTables, answerHeadings: dom.answerHeadings, extras, screenshot: shot }
}

async function captureChat(page: any, query: string): Promise<any> {
  const queries: QP[] = []
  const onResponse = async (res: any) => {
    if (!res.url().includes('/api/v1/query')) return
    let body: any = null
    try { body = await res.json() } catch { body = null }
    let q = '?'
    try { q = res.request().postDataJSON()?.query ?? '?' } catch { q = '?' }
    queries.push({ query: q, status: body?.status ?? null, data: body?.data ?? null, warnings: Array.isArray(body?.warnings) ? body.warnings : [], answer: body?.answer ?? '' })
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
    const raw = {
      hash: (last.match(/##/g) || []).length,
      bold: (last.match(/\*\*/g) || []).length,
      tableSep: (last.match(/\|\s*:?-{3,}:?\s*\|/g) || []).length,
    }
    return {
      lastBubble: last.slice(0, 1500),
      raw,
      hasResultPanel: document.querySelectorAll('.agent-drawer [data-testid="result-state-panel"]').length,
      hasRichTable: document.querySelectorAll('.agent-drawer .answer-table').length,
      hasHeading: document.querySelectorAll('.agent-drawer .answer-heading').length,
      hasEvidence: document.querySelectorAll('.agent-drawer .chat-evidence').length,
      hasFeedback: document.querySelectorAll('.agent-drawer .feedback-row').length,
      optionButtons: document.querySelectorAll('.agent-drawer .option-row button').length,
    }
  })
  const shot = `${SHOTS}/chat_${query.replace(/[^\w-]+/g, '_').slice(0, 30)}.png`
  await page.screenshot({ path: shot, fullPage: false })
  return { query, queries, ...dom, screenshot: shot }
}

test('A223 Browser C: all 6 pages + chat', async ({ browser }) => {
  fs.mkdirSync(SHOTS, { recursive: true })
  const out: any = { pages: {}, chat: {} }
  try { Object.assign(out, JSON.parse(fs.readFileSync(OUT, 'utf-8'))) } catch { }

  const context = await browser.newContext()
  const page = await context.newPage()

  const expected: Record<string, number> = { overview: 4, tasks: 1, sprint: 6, releases: 5, team: 6, quality: 4 }
  for (const p of PAGES) {
    if (out.pages[p.id]) { console.log(`[skip] ${p.id}`); continue }
    const rec = await capturePage(page, p.id, p.path, expected[p.id])
    out.pages[p.id] = rec
    fs.writeFileSync(OUT, JSON.stringify(out, null, 2))
    const sp = rec.statePanels.map((s: any) => s.state).join(',')
    const md = `${rec.rawMd.hash}h/${rec.rawMd.bold}b/${rec.rawMd.tableSep}t`
    console.log(`[${p.id}] q=${rec.queries.length} states=[${sp}] rawmd=${md} cards=${rec.metricCards.length}`)
  }

  // chat: rich markdown answer (competency recommendation table) + daily brief
  for (const cq of ['рекомендуй исполнителя для DMS-380', 'Сделай daily brief']) {
    const tag = cq.replace(/[^\w-]+/g, '_').slice(0, 30)
    if (out.chat[tag]) { console.log(`[skip chat] ${tag}`); continue }
    const rec = await captureChat(page, cq)
    out.chat[tag] = rec
    fs.writeFileSync(OUT, JSON.stringify(out, null, 2))
    console.log(`[chat:${tag}] status=${rec.queries[0]?.status} raw=${rec.raw.hash}h/${rec.raw.bold}b/${rec.raw.tableSep}t table=${rec.hasRichTable} head=${rec.hasHeading} ev=${rec.hasEvidence} fb=${rec.hasFeedback}`)
  }

  const summary: Record<string, any> = {}
  for (const [k, v] of Object.entries(out.pages)) {
    const pv = v as any
    summary[k] = { queries: pv.queries.length, states: pv.statePanels.map((s: any) => s.state), rawMd: pv.rawMd }
  }
  console.log('A223 Browser C capture summary:', JSON.stringify(summary))
})
