# A225 — Cookbook-derived visual design gate (slide-derived backgrounds + dark glass theme)

**Verdict:** `AGENT_CORE_V4_UI_VISUAL_DESIGN_GREEN_A225`

**Test HEAD:** `09bcbd22d87b478396970d0ddf89cbf6d531d421` (A225 spec commit; latest visual implementation)
**Functional baseline:** A224R2 GREEN at `612116894572f72af4f024486799458d3870d539` (spec tag `checkpoint/v4-ui-usability-green-a224r2` not published as git ref — F1; effective base = SHA)
**Test stack:** agent 8212 (PID 61601, `PO_AGENT_EXPECTED_HEAD=09bcbd2…`), task-api 8241 (PID 26008, system py3), MCP-SWTR 3000 (PID 25954), vite `[::1]:5175` (PID 61656). All 200 at session start.
**Artifacts:** `po-agent-platform-v2/qa_artifacts/qa_225_browser/` (result JSON, P9 log windows, 1440px/480px screenshots, drawer/state captures). Full-page originals (incl. 8.7MB Quality full-page) remain at `/private/tmp/qa225_browser/`; committed Quality shots are viewport-only (477KB/217KB) to keep the commit light.

---

## P0 — diff / build / architecture — GREEN (re-verified at report time)

Diff `6121168..09bcbd2` = **16 files, 814 insertions, 120 deletions**:

| Class | Files |
|---|---|
| Docs (4) | `GIGACODE_NEXT_ACTION.md`, `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`, `UI_VISUAL_DESIGN_2026_SPEC.md`, `V4_DOD_LOCK.md` |
| Static assets (6) | `frontend/public/design/{overview,tasks,sprint,releases,team,quality}-bg.svg` |
| Frontend TSX (5) | `ResultStatePanel.tsx`, `OverviewDashboard.tsx`, `Pages.tsx`, `QualityDashboard.tsx`, `TeamDashboard.tsx` |
| Frontend CSS (1) | `workspace.css` (+302) |

- Non-frontend, non-md files: **0** → 0 Agent Core / planner / runtime / plugin / source / task-api changes.
- No `package.json` / lockfile in diff → **0 new npm dependencies**.
- No V4 state-adapter file (`resultState.ts`) in diff → state semantics untouched (proven live in P4).
- No AS21 mutation path introduced (frontend is read-only; P9 proves 0 non-GET at the source).
- `tsc --noEmit` → exit 0. `vite build` → green (100 modules; CSS 42.56 kB, JS 270.35 kB — no raster bloat).

## P1 — asset and page mapping — GREEN 6/6

Per `p1_p2_p8_results.json`: each page's computed `background-image` is exactly its mapped asset, loaded 200 from the Vite origin; `network.failed = []` (no 404s); `console_errors = []`.

| Page | Background | 200 |
|---|---|---|
| Overview `/` | `/design/overview-bg.svg` | ✓ |
| Tasks `/tasks` | `/design/tasks-bg.svg` | ✓ |
| Sprints `/sprint` | `/design/sprint-bg.svg` | ✓ |
| Releases `/releases` | `/design/releases-bg.svg` | ✓ |
| Team `/team` | `/design/team-bg.svg` | ✓ |
| Quality `/quality` | `/design/quality-bg.svg` | ✓ |

- 6 distinct backgrounds (`distinct_backgrounds: 6`).
- Route navigation (6 steps in sequence): each step shows the correct new background, `retained_previous: null` on all — no stale background retention.
- Decorative-only: all six SVGs are pure vector (991–1442 bytes) with **no `<text>` elements** — zero operational copy in the assets.
- 1440px screenshots captured per page (`1440_*.png`).

## P2 — shared visual language — GREEN

Identical computed theme on all six pages:

- Canvas: `body bg rgb(2, 10, 19)` (dark navy/near-black), primary text `rgb(244, 251, 255)`, H1 `rgb(247, 253, 255)`.
- Glass cards: `backdrop-filter blur(16px)`, thin cyan border `rgba(126, 226, 255, 0.18)`, transparent base.
- Chrome `WORKS / PO Space / DB Tribe` present on all 6 pages; `nav_active_found: true` on all 6; sidebar/topbar styling constant (same computed values page-to-page — one design system, not six unrelated styles).
- White-surface dominance scan (P7): **0 light offenders** on all 6 pages (one minor white blob on Overview — F3, non-dominant).
- Muted secondary text consistent (`rgb(169, 195, 210)` family across panels).

## P3 — readability / state semantics — GREEN

Representative typed states re-rendered after styling (`p3_p4_results.json`, `p3_states.json`):

- **SUCCESS_WITH_DATA**: by-space cards / sprint metrics / quality score all data-populated (P4).
- **SOURCE_UNAVAILABLE**: Releases ×2 + Team capacity panels — label «Источник недоступен» (`rgb(233,250,255)`, high luminance) + message «Источник временно недоступен. Нули не подставляются.» (`rgb(169,195,210)`); state legible against the glass panel gradient `rgba(6,29,49,0.82)→rgba(4,20,35,0.72)`.
- **NEEDS_CLARIFICATION**: Releases third panel (typed clarification, not a fake zero).
- **LOADING**: «Загрузка / Получаем данные из источника…» (observed pre-settle on Releases).
- 4/4 state panels have both text label and message (`all_have_label`, `all_have_message`); states distinguished by text, never color-only.
- A224R2 zero/empty semantics unchanged («Нули не подставляются» retained verbatim).
- Evidence / Trace / Skill lineage readable: Releases evidence count 3, `trace_present: true`; 0 console errors.

## P4 — functional retained smoke — GREEN (values identical to source truth at capture)

- **Overview**: team-scoped by-space cards exact — CRPV 510/249/261/8, DMS 313/188/125/2, OLP 399/200/199/5, STS 3201/663/2538/0, WMB 6/0/6/0 (A224R2 Oracle B classes, within live drift); attention queue **107 rows**; daily brief visible.
- **Tasks**: 340 cards, header `340/340` (count matches rendered set); AS21/local filter surface + local CRUD re-verified in P5/P6 runs.
- **Sprints**: scope 73, completed 19, velocity 19 tasks/sprint, risk queue 38 rows; predictability honestly `—` with hint «нужен source-backed baseline старта спринта» (no fake %).
- **Releases**: 3 panels `SOURCE_UNAVAILABLE / SOURCE_UNAVAILABLE / NEEDS_CLARIFICATION`, scope `—`, `no_fake_zero: true`.
- **Team**: active 54 / WIP 31 / blocked 2, workload 13 rows; capacity `SOURCE_UNAVAILABLE` (no 40h default, no Recalculate).
- **Quality**: WMB-102 = 85/100, acceptance 0/100, gaps 1, decision **REWORK** (A223R2 semantics intact); scoped WMB≥7d aging = 265 (A224R2 exact).
- **Chat**: rich markdown/table rendering retained (P8 console clean; RichAnswer paths unchanged in diff).

## P5 — responsive 1440px + 480px — GREEN (12/12 captures)

`p5_1440.json` + `p5_480.json`: on **all 12 page×viewport captures** `document scrollWidth == clientWidth` (overflow 0). The `offenders` lists are the off-canvas *closed* drawers (`agent-drawer`/`task-drawer` parked at right 940/1919) — they do not extend the document (F2).

**Mandatory A224R2 regression — PO Attention at 480px — CLOSED:**

```
attention_480: rows 107, body clientH 360 / scrollH 10781 (usable internal scroll),
badge max-width 72px, white-space normal, title-wrap anywhere, row min-width 0px,
first DMS-352 → last OLP-3333 reached via vertical scroll, overflow 0
```

The previous 14–75px badge-forced overflow is gone (`attention_480_overflow_ok: true`).

## P6 — drawer / overlay styling — GREEN

All three drawers rendered dark and coherent (`p6_p7_results.json`):

- PO Agent drawer: gradient `rgb(6,24,41)→rgb(3,17,31)`, text `rgb(244,251,255)`, input `rgb(7,29,48)`.
- Task details drawer: same dark shell, high-contrast text.
- Local task create drawer: dark shell, input `rgba(2,16,29,0.72)`, local-only note present.
- Scrim `rgba(1,8,16,0.48)` opacity 1 — correct layering; open/close during capture behaved as before (session behavior unchanged; evidence/clarification/feedback controls live inside the same drawer path verified in A224R2).
- No white legacy drawer shell dominates (P7 scan: 0 light offenders).

## P7 — visual regression by page — GREEN

- **Overview**: 5 by-space cards readable over the lens background (card text cyan `rgb(121,233,251)`); attention + daily brief comparable visible height (screenshot `1440_Overview.png`).
- **Tasks**: search/filter surface reads as one control area; local tasks same product system; 340-card grid readable.
- **Sprints**: crystal/timeline background decorative only; risk queue + metrics dominant (38 rows, P4).
- **Releases**: 3 source-limited panels look intentional (`p3_releases.png`), decorative grid does not imply fake data.
- **Team**: workload/WIP lists readable (13 rows, `p3_team.png`); capacity source-unavailable state looks intentional, not broken.
- **Quality**: REWORK decision + Quality/Aging dominate the KPI/fins background (Quality viewport shots).
- `no_white_dominance: true` on all six pages.

## P8 — performance / asset hygiene — GREEN

`p7_white_p8_external.json` (full browser request log):

- All browser requests go to `[::1]:5175` (Vite origin; agent/task-api/MCP only via its proxy). `browser_request_hosts` (non-5175) = **[]**.
- Six SVG backgrounds served locally from static assets; 0 external image/font/domain dependencies; 0 failed requests.
- No raster background payloads (largest SVG 1442 B); bundle CSS 42.56 kB / JS 270.35 kB.
- Route switch: each page loads exactly its own SVG (6 unique, no accumulation/leak); 0 console errors caused by SVG/CSS.

## P9 — source/write audit — GREEN (two windows)

**Window A — fresh session, Overview + Tasks filter** (`p9_audit.json`, `p9_log_window.txt`, 52 HTTP lines):

- Mutations (POST/PUT/PATCH/DELETE, excl. `/api/v1/query`): **0**
- Local factual fallbacks (`GET /api/v1/tasks`): **0**
- task-query reads: 17, **0 unscoped** (16 = the A224R2 team-scoped by-space card assignee reads, identical route/params; 1 = explicit Zhdanov.A.Ni filter on Tasks)
- All lines GET 200; localStorage keys = `["po-local-tasks"]` (local tasks only)

**Window B — six-page route navigation** (`p9b_audit.json`, `p9b_log_window.txt`, 84 HTTP lines):

- All GET, all 200; non-GET = **0**; non-2xx = **0**
- Classification: health 6, current-sprint 26, sprint-tasks 30, task-query-scoped 16, versions 3, point-read 1 (Quality WMB-102), `spaces/WMB/sprints` 2 (pre-existing functional sprint-list route, F4)
- **Unknown endpoints: 0; unscoped task-query: 0** → zero source reads attributable to visual styling
- Design assets: exactly 6 requests, all `[::1]:5175` origin, 0 off-origin — no visual traffic hits agent/task-api/MCP

All five P9 requirements PASS: 0 AS21 mutations; 0 new source reads from styling; 0 local fallbacks; A224R2 team-scoped reads unchanged; localStorage only `po-local-tasks`.

---

## Findings (non-blocking)

- **F1:** spec-referenced tag `checkpoint/v4-ui-usability-green-a224r2` is not published as a git ref (effective base `6121168`). Owner should publish checkpoint tags (also for the new `checkpoint/v4-ui-visual-design-green-a225`).
- **F2:** P5 `offenders` entries are the off-canvas *closed* PO-agent/task drawers (right 940 @480 / 1919 @1440). Expected closed-state parking; document overflow is 0 on all 12 captures.
- **F3:** one minor white blob detected on Overview @1440 (small element; 0 light offenders, no dominance).
- **F4:** 2× `GET /swtr-read/spaces/WMB/sprints` in the 6-page window = pre-existing functional sprint-list route (Releases default scope WMB), not an A225 addition.

## Verdict

`AGENT_CORE_V4_UI_VISUAL_DESIGN_GREEN_A225`

**Recommendation:** freeze `checkpoint/v4-ui-visual-design-green-a225`. Next owner phase = PO visual acceptance + final Browser UX re-gate. Learning Reviewer still does NOT start until owner/PO acceptance.

**Services left running:** UI 5175 `[::1]` (PID 61656), agent 8212 (PID 61601 @ 09bcbd2), task-api 8241 (PID 26008, system py3), MCP-SWTR 3000 (PID 25954).
