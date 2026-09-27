import { test } from '@playwright/test'

// A223R2 — P9 audit repro: does the (unchanged) Overview page / portfolio queries
// issue a bare task-query (no space/assignee)? Confirms the 2 observed 502s are
// pre-existing portfolio behavior, not the A223R2 SprintPage change.
test.setTimeout(30_000_000)
const BASE = 'http://localhost:5175'

test('A223R2 audit repro: Overview page loads x3', async ({ page }) => {
  let bare = 0
  page.on('response', async (res) => {
    const u = res.url()
    if (u.includes('task-query?limit=100&max_pages=100&') === false && u.includes('task-query?limit=100&max_pages=100 ')) {
      bare++
      console.log(`[bare task-query] status=${res.status()}`)
    }
  })
  for (let i = 1; i <= 3; i++) {
    await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 60_000 })
    let d = Date.now() + 120_000
    while (Date.now() < d && (await page.evaluate(() => document.querySelectorAll('[data-state="LOADING"]').length)) > 0) await page.waitForTimeout(1000)
    console.log(`[overview load ${i}] settled`)
  }
  console.log(`TOTAL bare task-query across 3 Overview loads: ${bare}`)
})
