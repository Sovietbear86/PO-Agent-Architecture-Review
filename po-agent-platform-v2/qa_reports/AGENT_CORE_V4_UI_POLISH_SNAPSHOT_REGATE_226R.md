# A226R — UI polish + snapshot final re-gate

**Verdict: `AGENT_CORE_V4_UI_POLISH_SNAPSHOT_RED_A226R`**
Classification: `RED_P3_UNSCOPED_TEXT_SEARCH_SOURCE_SCALE` (first failing boundary = P3; pre-existing source-scale class surfaced by the mandatory spec scenario)

- Branch: `feat/core8-real-query-hardening-v2`
- START_HEAD: `c7ad7c79fcf4d6f77d1e09afed4617a5c4e6c56e`
- Prior verdict: `AGENT_CORE_V4_UI_POLISH_SNAPSHOT_RED_A226` (D-A226-1 timestamp plumbing, D-A226-2 placeholder query)
- Services: agent 8004 (PID 67374, vite proxy target), task-api 8241 (PID 66122, system py3), MCP-SWTR 3000 (PID 25954), vite `[::1]:5175` (PID 67855)
- Browser: Node `@playwright/test` 1.62.1 (chromium), viewport 1440×900 (480×900 for P9)

## Phase summary

| Phase | Result | Anchor |
|---|---|---|
| P0 build/diff/tests | GREEN | no core/planner drift; task-api = timestamp plumbing only; frontend UX/session/presentation only; tsc + vite build clean |
| P1 team-scoped Aging re-gate | GREEN | DMS:15 = 41/41 exact keyset+age; WMB:7 = 0/0 REAL_EMPTY; 0 rows missing source created_at; 16 bounded assignee reads; fail-closed proven |
| P2 dark structured surfaces | GREEN | Daily Brief wrapper lum 0.062 / th 0.189 / td 0.082, body rgb(209,230,239); 0 raw MD; V4 panel + competency unchanged |
| **P3 Tasks text/attachment search** | **RED** | **D-A226R-1** (below) |
| P4 local task UX + addendum | GREEN (+D-A226R-2) | all 10 addendum items exact; new non-blocking defect D-A226R-2 |
| P5 Quality persisted interaction | GREEN | task + aging criteria persist; page refresh honors explicit criteria |
| P6 Sprint/Release single refresh | GREEN (+F1) | exactly one Обновить, no header refresh, stale-during-refresh, nonce vs new-entity semantics |
| P7 brand + Daily Brief | GREEN | "Platform V" (no WORKS); brief 2 sections / 5 attention rows / 10 fact rows / GROUNDED |
| P8 snapshot policy + isolation | GREEN | failed-refresh stale+error label+recovery; 45s idle 0 POSTs; 6/6 context isolations; storage policy exact |
| P9 retained smoke + audit | GREEN | 0 overflow ×12 (1440+480); 6 distinct backgrounds; chips OLAP+DataMarts; attention 101/360px scroll; business values exact; audit clean (5 bare scans = P3 case only) |
| D-A226-2 re-gate (mandatory) | CLOSED | 0 `__none__` payloads; fresh mount 1 POST (page search only); SPA revisit 0 POSTs; full reload 0 POSTs |

## D-A226R-1 (BLOCKING, P3) — unscoped text/attachment search cannot return WMB matches

Spec scenario: Text mode + `БП 2027` + Найти → "returned keys exactly match independent Agent/API/Oracle search".

Proven (independent per-space task-api probes):
- WMB: **99 real title/description matches** ("Подготовка к БП2027…" etc.), 28.9s, 200 OK
- DMS: 0, OLP: 0 (real empties)
- STS: **502** (141s), CRPV: **502** (107s) — both exceed the task-query hard cap `limit=100 × max_pages=100 = 10,000` rows (STS ≈460k, CRPV ≈150k)
- UI Text mode has no space scoping → production query = unscoped `task-query?phrase=БП 2027` → iterates all 5 spaces → STS/CRPV 502 sinks the whole query.

Browser proof (P3 + P3b):
- fresh /tasks (default text `БП 2027`): POST issued, UI stuck "Обновляем…" for **>152s** with no typed failure shown; server-side the phrase fan-out finally 502s at agent log 22:18:10 (`task-query?phrase=БП 2027 → 502`), i.e. **>6.5 min** from POST; 0 cards, no false zero.
- Excel mode same text: typed `FAILED` 200 in 42s (`loaded_skills: [tasks.search, task.search_excel, task.search_text]`), cached as snapshot, 0 cards, no fake empty.
- Safety intact: typed fail-closed, no fabrication, no false zero.
- State persistence around the failure is GREEN: mode+text+snapshot survive SPA return (0 POSTs) and full reload (0 POSTs); header refresh re-fires the same query (1 POST).

Classification: **pre-existing source-scale limitation** (A224 pagination-cap lineage; A223R2 F-A223R2-1 bare task-query 502 class), not introduced by the A226R diff — but it blocks the spec's exact-key-parity requirement for the mandatory scenario.

Owner fix (smallest, task-api only, proven pattern from A224 per-space isolation):
1. In `task-query` phrase mode: execute per-space with **per-space error isolation** — a space exceeding the pagination cap returns typed per-space `source_unavailable` (or an ES count fallback) instead of 502-sinking the whole query; union of completed spaces + explicit `incomplete_spaces` warning.
2. Non-mocked regression: phrase search over a space set containing STS/CRPV must complete with WMB matches present.
Optional product decision: add a space selector to UI text/attachment modes (scope the query).

## D-A226R-2 (non-blocking, P4) — AI launcher covers the local-task drawer submit button

- Empirical (1440×900, deterministic): `document.elementFromPoint` at the "Создать/Сохранить" button center (1371, 857) returns `.agent-launcher`; Playwright click intercepted 30s timeout.
- Geometry: submit button rect (1321.8, 833.9, 98×46) vs launcher rect (1362, 824, 52×52) → **52×42px overlap**; launcher occupies right:26/bottom:24 of the viewport, the drawer submit sits at the form bottom-right.
- Introduced by A226R commit `14927a7` (Теги + tag-suggestions + Дедлайн fields make the form taller; the submit button moved down into the launcher zone).
- Root cause note for owner: despite `.task-drawer{z-index:55}` > `.agent-launcher{z-index:40}` and the drawer box fully covering the point, Chromium hit-testing returns the launcher (verified with `elementsFromPoint` paint stack: launcher listed above the drawer subtree; runtime z-index changes 40→44 and transform→none did **not** change the outcome; removing the launcher fixes the hit). The sibling `.agent-drawer` (z50, chat) stacks correctly — the anomaly is specific to the nested transformed `.task-drawer`.
- Impact: mouse click on the submit button at common laptop heights (≤ ~956px) opens the PO Agent chat instead of submitting. Workarounds exist: Enter key submits the `<form>` (used by QA), or clicking the unobscured left sliver (~40px) of the button.
- Suggested owner fix (any one): hide `.agent-launcher` while any drawer is open (scrim already covers the page — launcher is meaningless then); or render task drawers as direct children of WorkspaceApp (same stacking level as `.agent-drawer`, which provably stacks correctly); or move form-actions up / add bottom padding.

## P4 — local task UX + addendum (GREEN)

All 10 addendum items proven in one browser session (0 AS21 POSTs from local operations; 2 POSTs total = initial page auto-queries only):
1. create with deadline via visible native date picker (`input[type=date]`, value 2026-10-15 → renders "дедлайн 15.10.2026") ✓
2. LOCAL-NNNN display (4-digit zero-padded): LOCAL-0001 → LOCAL-0002 → LOCAL-0003 ✓; no `№N` anywhere; drawer kicker shows the same code ✓
3. click row → edit drawer opens prefilled (kicker = task number, title/description/owner/priority/status/tags/deadline) ✓
4. edit title + deadline → save → list + localStorage updated, **number preserved** ✓
5. reload → all edits persist ✓
6. second task = max+1 (LOCAL-0002) ✓
7. delete first → remaining **not renumbered** (LOCAL-0002 stays LOCAL-0002) ✓
8. create after delete → LOCAL-0003 (max+1, deleted 1 not reused) ✓
9. technical timestamp ids (`LOCAL-1790624125145`) in storage only, never rendered; display code separate from title ✓
10. zero AS21 writes ✓
11. old-schema migration: seeded 2 rows without `number` (createdAt order) + 1 with `number:7` → rendered LOCAL-0008, LOCAL-0009, LOCAL-0007 (existing number preserved, sequential fill from max) — exact ✓
12. priority submit gating: disabled before title, enabled after ✓

## P5 — Quality persisted interaction (GREEN)

- Task: default WMB-102 (4 POSTs on load) → change to WMB-30000 + Проверить (3 new POSTs) → result: 85/100 good, Acceptance 0/100, Пробелы 1, REWORK (typed, source-backed).
- Navigate away/back: **0 new POSTs**; task input `WMB-30000`, submitted task, all 4 metric cards + decision + snapshot timestamp restored.
- Aging: select DMS + 15 → Обновить (1 POST, `Покажи старые задачи команды DMS старше 15 дней`) → count **41** (= P1 independent oracle, cross-phase exact). Away/back: 0 POSTs, DMS/15 + count 41 restored.
- Re-press Aging Обновить with identical criteria: **0 new POSTs** — snapshot reuse (sessionStorage cache hit), criteria not replaced by defaults. (Spec's "re-read from source" for an identical re-press is effectively served by the page-level refresh; see finding F2.)
- Page-level refresh: re-runs exactly the **persisted** criteria — WMB-30000 ×3 + DMS:15 (payload-verified), not the defaults WMB-102/WMB:7; snapshot label advances; explicit control semantics not overwritten. ✓

## P6 — Sprint/Release single refresh control (GREEN)

- Exactly **one** Обновить per entity (`updateButtons=1` on every capture); **no** header-level refresh beside "Спросить PO Agent" (`headerRefresh=false`); toolbar shows `Последнее обновление: <date> <time>` (see F1 for locale).
- Sprint: default WMB-SPRNT-1 → 6 POSTs, real data (Scope 2, Completed 0, Velocity 0, throughput 0, WIP 0, 0% — source-exact stale sprint). Change → DMS-SPRNT-3 (6 POSTs): Scope 74, Completed 22, Velocity 22 tasks/sprint, throughput 1.571, WIP 32, 29.7%. Away/back: 0 POSTs, input+snapshot+metrics restored. Unchanged re-press → 6 POSTs with the same DMS-SPRNT-3 queries; **mid-refresh stale data remains visible** (button "Обновляем…", metrics unchanged); after settle label advances.
- Release: default WMB-2024-Q3 → 5 POSTs, all metrics "—" (honest typed non-business, no fake zeros); change → 1.6.0 (5 POSTs, "—" = SOURCE_CONDITIONAL lineage, OLP 1.6.0 membership unpopulated); away/back 0 POSTs + state restored; unchanged re-press → 5 POSTs same queries.

## P8 — snapshot policy + isolation (GREEN)

- **Failed refresh** (client-side request abort on Sprint, DMS-SPRNT-3): stale metrics (74/22/22/1.571/32/29.7%) remain fully visible; error label `Не удалось обновить · данные на 09/28/2026, 11:13 PM` (stale timestamp preserved); recovery refresh → 6 POSTs, error cleared, label advances. ✓
- **No background polling**: 45s idle on a data-populated page → **0 new POSTs**. ✓
- **Context isolation (6/6, all 0 POSTs on return to A, A-snapshot restored byte-identically):**
  - Tasks: Zhdanov.A.Ni (10 cards, first DMS-371) ↔ Semavin.M.M (343 cards, first OLP-3233)
  - Sprint: DMS-SPRNT-3 (74/22/22/1.571/32/29.7%) ↔ OLP-SPRNT-8 (76/9/9/1.291/48/11.8%)
  - Release: 1.6.0 ↔ 24Q1 (both typed "—")
  - Team: DMS (52 active / 32 WIP / 2 blocked) ↔ OLP (67 / 48 / 5)
  - Quality task: WMB-30000 ↔ WMB-102 (both 85/0/1 REWORK, decision label follows submitted task)
  - Quality aging: DMS:15 (41) ↔ OLP:7 (80)
- **Storage policy**: sessionStorage keys = `po-page-ui:v1:*`, `po-page-snapshot:v1:*`, `po-agent-runtime-session-id` only; localStorage = `po-local-tasks` only; no AS21 snapshot data in localStorage. ✓

## P9 — retained business/design smoke + audit (GREEN)

- Overflow: **0 of 12** (6 pages × {1440, 480}); scrollWidth == innerWidth everywhere.
- Backgrounds: 6 distinct slide-derived SVGs (`/design/{overview,tasks,sprint,releases,team,quality}-bg.svg`, Vite origin) on all pages at both widths.
- Topbar chips: exactly `OLAP` + `DataMarts` on all pages.
- Overview attention: "Очередь внимания PO **101**" in `.overview-scroll-body` (scrollH 8698 / clientH 360 — bounded scroll retained); top rows DMS-352 (blocked·aging_14d), DMS-379. Daily Brief GROUNDED. (By-space cards load in ~60s — known A226 behavior, not a defect.)
- Retained business values (UI ↔ agent API cross-check):
  - team.utilization_actual DMS: 9 members; Semavin.M.M 94.0h / 12 worklogs / 133.1% OVER; total **626.5h / 95 worklogs** — exact A215F2 parity (live worklog backfill since A215G 64h/8); numerator REAL_AS21_WORKLOGS, denominator OWNER_POLICY (70.65h/15d, policy metadata intact)
  - Sprint DMS-SPRNT-3: API total 74 / completed 22 / active 14 / blocked 2 / 29.7% == UI (P8)
  - Quality WMB-102: 85/100 good, Acceptance 0, missing 1 (`acceptance_expectations`), REWORK — exact A223 semantics
  - Competency (DMS-380): recommendation Kalachanov.V.V, 12 candidates, declared-competency method, authoritative_current_sprint load scope, REAL_AS21_PLUS_TEAM_CONFIG
  - Releases: all "—" + forecast note "Forecast не активирован… не показывает псевдопрогноз" — honest source limitation retained
- **Audit (whole session logs):**
  - 0 AS21 mutations (task-api: no POST/PUT/DELETE/PATCH on swtr-read)
  - 0 local factual fallback (agent: 0 `GET /api/v1/tasks` reads)
  - 0 tenant-wide scans **except 5** — all `task-query?phrase=БП 2027` from the P3 D-A226R-1 case (no other page emitted bare scans; 144 person-scoped reads = certified person contract)
  - 0 extra source traffic from cached page revisits (0 POSTs on every revisit: P3b/P5/P6/P8)
  - manual refresh traffic bounded to current page/context (re-run payloads = same entity's queries only)

## Non-blocking findings

- **F1 (P6, locale):** snapshot label uses `toLocaleString([], {…})` → renders `09/28/2026, 10:50 PM` (en-US) in the QA browser; spec asks for `DD.MM.YYYY HH:MM`. Fix: `toLocaleString('ru-RU', …)` in `snapshotLabel` (frontend/src/recovery/pageSnapshot.tsx).
- **F2 (P5, semantics):** re-pressing Aging Обновить with identical criteria reuses the sessionStorage snapshot (0 source reads) instead of forcing a re-read; page-level refresh does re-read with persisted criteria. If the spec strictly requires a source re-read on identical re-press, wire the aging form submit to a nonce (same pattern as Sprint/Release unchanged-repress).
- **F3 (P3b UX, part of D-A226R-1):** during the unscoped text search the UI shows "Обновляем…" with no progress/bounded failure for >2.5 min (server completes at ~6.5 min). A bounded client timeout or per-space progressive results would make the failure visible.
- **F4 (P9):** by-space cards ("Задачи по пространствам") render 0 until the ~60s 16-assignee collection completes — known A226 timing, consider a loading state.

## Drift notes (live source, all verified against fresh oracles)

- DMS-SPRNT-3: 73→74 tasks, 17→22 completed, risk queue 38→37 (A223R2 baseline)
- Semavin all-spaces: 325→343; Zhdanov 10 (first DMS-371); OLP-SPRNT-8: 69→76
- Team DMS: 54/31/2 → 52/32/2; team utilization total 626.5h/95 = A215F2 exact (member-level values drifted with live worklog backfill)
- Attention queue: 107 → 101

## QA artifacts

- `/private/tmp/qa226r_browser/`: p3b.json (payloads incl. refresh), p4.json, p5.json, p6.json, p8.json, p9.json, p9_api.json, p9_api2.json, screenshots (p4_overlap.png, p4_tasks_local.png, p5_quality.png, p6_releases.png, p8_quality.png, p9_overview_attention.png, p2_p7_overview.png, d2262_tasks_final.png)
- `/private/tmp/qa226r_agent.log`, `qa226r_taskapi.log`, `qa226r_vite.log`, `qa226r_oracle_p1.json`, `qa226r_capability_direct.json`
- Harnesses (untracked, repo root / frontend): `qa_226r_check_stack.sh`, `qa_226r_p9_api.py`, `qa_226r_p9_api2.py`, `po-agent-platform-v2/frontend/qa_226r_{p3b,p4,p5,p6,p8,p9,probe,probe2}.mjs`

## Next owner action

1. **Fix D-A226R-1** (task-api per-space isolation for phrase task-query, pattern from A224 /task-count) + optional UI space selector for text/attachment modes.
2. **Fix D-A226R-2** (launcher vs drawer hit-test; hide launcher while a drawer is open is the smallest fix).
3. Optional: F1 locale, F2 aging re-press nonce.
4. Then **A226R2 re-gate**: P3 (expect WMB 99 exact keys or typed partial with explicit incomplete_spaces), P4 submit-button clickability, quick regression of P5-P9 anchors above.

Per RED protocol: STOP — no checkpoint, no next wave.
