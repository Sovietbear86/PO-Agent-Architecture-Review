# A226 — Final UI polish + actual utilization + team aging + page snapshots

**Verdict:** `AGENT_CORE_V4_UI_POLISH_SNAPSHOT_RED_A226`

**Classification:** two independent confirmed defects —
1. **D-A226-1** `RED_SOURCE_TIMESTAMP_PLUMBING` (P4): team-scoped `task.aging` depends on the live assignee route, which does not expose source `created_at`; the capability therefore fails closed on every space.
2. **D-A226-2** `RED_SNAPSHOT_POLICY_PLACEHOLDER_QUERY` (P5): the tasks page's always-mounted `TaskDetailsDrawer` issues a live `Найди __none__` query on every mount (fresh load = 2 POSTs, nav-return = 1 POST), bypassing the snapshot layer and violating the "no new source reads on return" policy.

**Test HEAD / START_HEAD:** `de4cc9c07395c4f8760ef3ca7d85c970d1e50378`
**Frozen baseline:** A225 `AGENT_CORE_V4_UI_VISUAL_DESIGN_GREEN_A225` at `09bcbd22d87b478396970d0ddf89cbf6d531d421` (diff base for this assignment)
**Test stack:** agent 8212 (PID 42486 at P0–P4; the P5 harness performed the spec'd refresh-failure test, which killed and restarted the agent → current PID 42740, same `PO_AGENT_EXPECTED_HEAD=de4cc9c`), task-api 8241 (PID 26008, system py3), MCP-SWTR 3000 (PID 25954), vite `[::1]:5175` (PID 42534 → 42797 after the P5-harness restart, same build). All 200 throughout; agent `/live` 200 verified after restart.
**Artifacts:** `po-agent-platform-v2/qa_artifacts/qa_226_browser/` (`capability_direct.json`, `oracle_p2.json`, `oracle_p4.json`, `p1_dark_surfaces.json`, `p1_brief_dom_hash.json`, `p1_brief_raw_answer.txt`, `p1_overview_brief.png`, `p1_v4_result_panel.png`, `p1_competency.png`, `p2_team_dms.png`, `p4_agent_api.json`, `p4_agent_trajectory.json`, `p4_quality_aging_ui.png`, `p5_snapshot_policy.json`, `p5_tasks_forensic.json`, `p5_tasks_forensic.log`, `p5_run.log`, `p5_refresh_failure.png`, `p5_refresh_retry_ok.png`, `p7_backgrounds_overflow.json`, `p2_team_p4_ui.json`).

**STOP rule applied (initial report):** first confirmed boundary reached at **P4** (below). P1 and P5 were subsequently gated in this session (continuation); **P5 confirmed a second, independent defect D-A226-2** (tasks page live placeholder query on every mount). P6 (full snapshot context isolation) and the full P8 audit remain **not gated**. Evidence for both confirmed boundaries is preserved below and in artifacts.

---

## Phase results

| Phase | Result | Note |
|---|---|---|
| P0 diff/build/architecture | **GREEN** | 0 Agent Core/planner/runtime drift; backend deltas = plugin team-aging + utilization worklog_count only; frontend = presentation/snapshot wiring; 0 mutation verbs added |
| P1 dark structured surfaces | **GREEN** | Daily Brief table, V4 result panel, competency table all dark glass; `#` raw-MD flag was a false positive (`<TH>` rank cell); no raw-markdown regression |
| P2 Team actual utilization | **GREEN** | exact per-member parity DMS 9/9 + OLP REAL_EMPTY; worklog_count present; numerator REAL_AS21 / denominator OWNER_POLICY; 40ч visible; no false SOURCE_UNAVAILABLE |
| P3 top-right products | **GREEN** | exactly `OLAP` + `DataMarts`; DTMS absent; click inert (no query fired); route nav unaffected |
| P4 team-scoped Aging | **RED (first confirmed boundary, D-A226-1)** | `/assignee-tasks` route lacks `created_at` → `task.aging` team_scope fails closed on every space |
| P5 snapshot policy | **RED (D-A226-2)** | 5/6 pages exact policy; tasks page fires a live `Найди __none__` placeholder query on **every mount** (fresh=2, return=1 POST) — always-mounted `TaskDetailsDrawer` uses non-snapshot `useHarness` |
| P6 snapshot context isolation | **SUBSET GREEN / full NOT GATED** | Team DMS↔OLP subset (run inside the P5 harness): OLP first load 6 live POSTs (uncached — correct), back to DMS **0** POSTs, DMS data byte-identical |
| P7 retained design smoke | **GREEN (backgrounds + overflow portion)** | 6 distinct slide-derived backgrounds; 0 document overflow at 1440 and 480 |
| P8 audit | **PARTIAL (clean so far)** | 0 AS21 mutations, 0 local `/api/v1/tasks` reads, 0 tenant-wide scans in the tested window; full audit deferred by STOP |

---

## P0 — diff / build / architecture — GREEN

Diff `09bcbd2..de4cc9c` (excluding docs + A225 artifacts): **14 code files**.

Backend (`po_agent`):
- `harness/v4_plugins/_task_live_handlers.py` (+31) — adds `team_scope` to `build_task_aging`: when `team_scope`+`space` (no single assignee), it reads the 16 configured member logins from `get_all_member_logins()`, performs one bounded `_live_rows(space, assignee=login)` per member, dedupes by task key, and **raises `AS21SourceUnavailable` if any member read fails** (complete-reads-required). Read-only.
- `harness/v4_plugins/task_catalog.py` (+4) — capability/skill spec text for `team_scope` (documentation of the new optional arg).
- `harness/v4_plugins/time_accounting_aggregate.py` (+11) — `build_team_utilization_actual` now emits per-member `worklog_count` (a `Counter` over the same in-period worklog entries already read for `by_member`). No new source call.

Frontend:
- `recovery/pageSnapshot.tsx` (NEW, +97) — `useSnapshotHarness` + `SnapshotRefresh`: `sessionStorage`-keyed (`po-page-snapshot:v1:<ns>:<query>`) session snapshot with manual `Обновить`; cached context restores without a live request; on refresh failure keeps old data + shows `Не удалось обновить · данные на HH:MM`.
- `recovery/{OverviewDashboard,Pages,QualityDashboard,TeamDashboard}.tsx`, `components/V4ResultPanel.tsx`, `recovery/WorkspaceApp.tsx` — wire every page to `useSnapshotHarness` + `SnapshotRefresh`; Team page switches the utilization card to `team.utilization_actual` (query `Покажи фактическую утилизацию команды {space}`); Quality aging query now `…задачи команды {space} старше N дней` (team scope); top-right chips reduced to OLAP + DataMarts.
- `recovery/workspace.css` (+31), `OverviewDashboard.css` — dark glass theme for `.v4-result-*` and `.answer-table-*` (structured V4 result + markdown tables), snapshot control styling.

Proven:
- **0 Agent Core / planner / runtime / session-architecture changes** — diff touches only plugin capability output + spec text + frontend presentation. No changes to `agent_core_v4*.py`, `capacity_policy.py`, adapters, `task-api/`.
- Backend semantic deltas limited to **plugin-level** team-aging team-scope + actual-utilization `worklog_count`.
- **No AS21 mutation capability added** — added backend lines are read-only aggregation; a mutation-verb scan of the `po_agent` diff is empty.
- `tsc --noEmit` → exit 0. `vite build` → green (101 modules; CSS 44.51 kB, JS 273.92 kB).
- Focused tests: `test_agent_core_v4_team_aging.py` + `test_agent_core_v4_time_accounting_aggregate.py` → **9/9 passed**. Broader `v4/plugin/task_catalog/registry/time_accounting/team_aging` selection → 276 passed, 1 failed: `test_skill_registry.py::test_get_active_skills`.

**Pre-existing failure (not A226):** `test_skill_registry.py::test_get_active_skills` fails **identically on the A225 checkpoint** `09bcbd2` (reproduced in a read-only worktree: same `assert 8 == 9`). It passes in isolation on both. This is a legacy test-isolation artifact (shared `INITIAL_SKILLS` registry state under broad `-k` selection), present before A226; A226 only *added* 2 passing tests (274→276). Out of scope.

**Test-masking (non-blocking, relevant to P4 fix):** the new `test_agent_core_v4_team_aging.py` builds `_task()` with `source_data={"_canonical_created_at_from_source": True}` and monkeypatches `_live_rows`. It therefore never exercises the real route; the production fail-closed branch (the only branch that fires live, because the real assignee route has no `created_at`) is untested. See P4 owner fix.

---

## P1 — Dark structured surfaces — GREEN

Browser C across the structured (table/panel) surfaces that carry real data (`p1_dark_surfaces.json`, `p1_overview_brief.png`, `p1_v4_result_panel.png`, `p1_competency.png`):

- **Daily Brief table (Overview):** dark glass theme — wrapper luminance 0.062, `<th>` 0.189, `<td>` 0.082, text `rgb(227,243,248)`. No white-dominant cells.
- **V4 result panel (V4ResultPanel):** dark gradient `linear-gradient(145deg, rgba(5,25,43,0.9), rgba(3,17,31,0.84))`, 2 structured rows rendered, text `rgb(220,238,246)`.
- **Competency table:** dark `<th>`/`<td>` surfaces, no raw-markdown cells.
- **No raw-markdown regression.** The initial automated flag `raw_md_hash_heading: true` was a **false positive**: the detected `#` is the content of a `<TH>` cell (rank column of a rendered table), not an unparsed markdown heading. All `##`/`###` headings render as `.answer-heading` divs and pipe tables render as real `<table>` elements (forensic DOM inspection, `p1_brief_dom_hash.json` + `p1_brief_raw_answer.txt`).
- **Non-blocking observation (pre-existing, not an A226 regression):** the V4 panel shows 2 structured rows because `structuredRows()` picks the top-level `results` array (2 items) before descending to the nested `tasks` array (74 items). This field-order logic predates the A226 diff; the panel itself is dark-themed and correct.

---

## P2 — Team actual utilization — GREEN

Independent **Oracle B** (raw task-api reads, no agent runtime): resolve current sprint + period → complete sprint membership (`/sprints/{id}/tasks?complete=true`) → bounded per-task worklogs (`/tasks/{key}/work-logs`) → aggregate by worklog-author `external_id` → owner capacity policy computed from first principles (247 workdays × 0.87 × 8h / 365 × calendar days).

Live source: DMS current sprint **DMS-SPRNT-3** (2026-09-13→2026-09-27, 15 cal days, capacity **70.65h**); OLP **OLP-SPRNT-8** (2026-09-21→2026-10-05).

**DMS** (Oracle B = production capability driver, exact parity, 9/9 members):

| member | actual_hours | worklog_count | capacity | util% | over |
|---|---|---|---|---|---|
| Semavin.M.M | 94.0 | 12 | 70.65 | 133.1 | True |
| Alekseev.K.S | 88.0 | 21 | 70.65 | 124.6 | True |
| Galtsov.A.A | 80.0 | 10 | 70.65 | 113.2 | True |
| Moiseev.A.N | 80.0 | 10 | 70.65 | 113.2 | True |
| Zhdanov.A.Ni | 80.0 | 10 | 70.65 | 113.2 | True |
| Garanin.R.V | 72.0 | 9 | 70.65 | 101.9 | True |
| Kondratchikova.P.I | 52.5 | 13 | 70.65 | 74.3 | False |
| Agataeva.A.Z | 40.0 | 5 | 70.65 | 56.6 | False |
| Dolgovskoy.E.N | 40.0 | 5 | 70.65 | 56.6 | False |

Total 626.5h, 95 in-period entries. Every member's `actual_hours`, `worklog_count`, `available_capacity_hours`, `utilization_percent`, `over_capacity` **match exactly**.

**OLP** = REAL_EMPTY (76 tasks, 0 in-period worklogs → 0 members, total 0) — correct: no fabricated zeros, no SOURCE_UNAVAILABLE.

UI (Team/DMS, `p2_team_dms.png`): capacity table renders **9 rows**; the new **Списания** (worklog_count) column is present and populated; the "40 ч" weekly-baseline owner-policy note is visible; **no** `SOURCE_UNAVAILABLE`/«Источник недоступен» in the capacity panel (estimate absence does not mis-fire — the underlying skill is `team.utilization_actual`, not estimate-based `team.capacity`).

- Underlying skill = **`team.utilization_actual`** (confirmed in UI meta + API), **not** `team.capacity`.
- `numerator_source = REAL_AS21_WORKLOGS`, `denominator_source = OWNER_POLICY`, `source = REAL_AS21_PLUS_OWNER_POLICY`.
- `worklog_count` (the A226 addition) is present per member and matches Oracle B.

> Oracle note: an earlier single-shot oracle read 586.5h/8 members vs the production 626.5h/9. The delta is **live worklog backfill** — members keep adding worklog entries dated within the sprint window after the first read. A back-to-back re-read reconciled exactly to 626.5h/9 (Dolgovskoy.E.N's 40h appeared between reads). This is source freshness, not a product bug; production and a fresh oracle agree.

---

## P3 — Top-right products — GREEN

`.topbar-actions` renders **exactly two** buttons: `OLAP`, `DataMarts`. `has_DTMS=false`. Clicking a chip fires **no** `/api/v1/query` (request delta = 0). Route navigation unaffected (`/tasks`, `/team` both resolve).

---

## P4 — Team-scoped Aging queue — RED (first confirmed boundary)

**Requirement under test:** Quality Aging for WMB:7 and DMS:15, `task.aging` with `team_scope=true`, no whole-space scan, exact task-key/count/age parity with Oracle B; fail closed if any member read unavailable; REAL_EMPTY only when complete reads prove empty.

**Agent side (LLM-independent + live, both deterministic):**
- Planner routes correctly to `task.aging` with `team_scope=true` (API trajectory, `p4_agent_trajectory.json`):
  - DMS:15 → turn2 `call task.aging {space: DMS, threshold_days: 15, team_scope: True}`
  - WMB:7 → turn2 `call task.aging {space: WMB, threshold_days: 7, team_scope: True}`
- **No whole-space corpus scan** — the capability issues one bounded `task-query?space=<X>&assignee=<login>` per configured member (16 reads), never an unscoped `task-query`.
- Result: **`status=FAILED`, `warnings=['source_unavailable']`, `answer` = "Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат."** — safe fail-closed, zero fabricated rows, no false empty.
- **LLM-independent capability driver** (`capability_direct.json`, bypasses the planner entirely) reproduces the exact same `AS21SourceUnavailable: REAL AS21 task rows do not expose source creation timestamps required for task.aging` for **both** WMB:7 and DMS:15. So the failure is in the source plumbing, not the LLM/planner.

**Root cause (localized, deterministic):**
1. `task.aging` team-scope reads rows via `_live_rows(space, assignee)`, which hits `GET /api/v1/swtr-read/task-query?space=&assignee=`; for a pure-assignee query that route delegates to `get_assignee_tasks` (`task-api/app/routers/swtr_assignee.py:256`), the **live assignee route**.
2. That route's TQL `attributes` list (`swtr_assignee.py:272-281`) requests only `code, summary, assigned_to, space, workflow_status, scrum_board_plugin_sprint, fix_version_s` — **no `created_at`/`createdAt`/`updated_at`/`deadline`**. Its `_canonical_row` (`swtr_assignee.py:~100-140`) therefore never emits a `created_at` field (contrast the sprint route's `_canonical_sprint_task_row` at `swtr_read.py:230` which does `created_at = pick("created_at","createdAt")`).
3. The production adapter maps `_canonical_created_at_from_source = source_created is not None` (`task_api.py:441`) → **False on 100% of assignee-route rows**.
4. `task.aging` filters to `with_source_age` and raises `AS21SourceUnavailable` when the corpus is non-empty but has no source timestamps (`_task_live_handlers.py:380-381`).

**Oracle B (independent, `oracle_p4.json`):** the 16 configured member reads return real tasks (DMS = 315 unique team tasks, WMB = 6; 0 member failures), but **0 rows carry a source `created_at`** from this route → `with_source_created_at = 0`. So the assignee route is the missing boundary. The true source answer is **not** empty — A224R2 certified DMS:15 = 72 rows and WMB:7 = 265 rows via routes that do carry `created_at` (sprint/point reads). The source *has* the data; the specific route team-scoped aging depends on does not expose it.

This is the same defect class as **A185 B1 / A210** (source timestamp not plumbed through the route a capability consumes). The owner's A226 change is correct at the capability layer (team-scope reads, dedup, complete-reads-required fail-closed, `team_member_count` provenance) and the planner wiring is correct — but the feature cannot be gated GREEN because its source route lacks `created_at`.

**Owner fix (minimal, task-api only, two-part):**
1. In `swtr_assignee.py` `get_assignee_tasks`, add `created_at, createdAt, updated_at, updatedAt, deadline, dueDate` to the TQL `attributes` list (mirror `swtr_read.py:_tql_sprint_tasks`).
2. In `swtr_assignee.py` `_canonical_row`, surface `created_at`/`updated_at`/`deadline` onto the canonical row (`pick`-style, as `_canonical_sprint_task_row` does) so the adapter sets `_canonical_created_at_from_source=True`.
3. Add a **non-mocked** regression: team-scoped `task.aging` on a real space returns source-backed rows (or deterministically fails only if the source genuinely has no ts), driving the real assignee route — the current `test_agent_core_v4_team_aging.py` masks this by hardcoding `_canonical_created_at_from_source: True` + monkeypatching `_live_rows`.

**UI note (non-blocking, timing only):** the Quality page fires 4 LLM-backed queries on mount; under the congested Qwen3.8-27B endpoint the aging panel was still in its loading state in all 3 captures (up to 95s). This is endpoint latency, not a state-semantics defect: the panel renders `ResultStatePanel result={aging}` for non-business states, so once the FAILED result returns it shows the honest source message (verified in code). The API-level fail-closed above is the authoritative, deterministic evidence.

---

## P5 — Snapshot policy — RED (D-A226-2)

**Requirement under test:** fresh live load runs the page query set once; navigating away and back restores from `sessionStorage` snapshot with **no new source reads** (ts unchanged, data identical); manual `Обновить` re-runs the exact query set with old data visible during the refresh; no background polling while idle; refresh failure keeps the old snapshot + data and shows `Не удалось обновить · данные на HH:MM`; recovery retry succeeds. Expected per-page query sets: overview 4, tasks 1, sprint 6, releases 5, team 6, quality 4. Storage policy: snapshots in `sessionStorage` only (`po-page-snapshot:v1:`), nothing in `localStorage` except `po-local-tasks`.

**Per-page matrix** (`p5_snapshot_policy.json`; each page in a fresh browser context = fresh session):

| page | fresh posts (exp.) | back posts | ts same | data same | refresh posts (exp.) | ts updated | old data during refresh | idle 30s posts |
|---|---|---|---|---|---|---|---|---|
| overview | 4 (4) | **0** | ✓ | ✓ | 4 (4) | ✓ | ✓ | 0 |
| tasks | **2 (1)** | **1** ⚠ | ✓ | ✓ | 1 (1) | ✓ | ✓ | 0 |
| sprint | 6 (6) | **0** | ✓ | ✓ | 6 (6) | ✓ | ✓ | 0 |
| releases | 5 (5) | **0** | ✓ | ✓ | 5 (5) | ✓ | ✓ | 0 |
| team | 6 (6) | **0** | ✓ | ✓ | 6 (6) | ✓ | ✓ | 0 |
| quality | 4 (4) | **0** | ✓ | ✓ | 4 (4) | ✓ | ✓ | 0 |

**5 of 6 pages satisfy the policy exactly.** The tasks page's *snapshot mechanism itself* works (ts/data restored from snapshot, refresh runs exactly the 1 expected query, old data stays visible during refresh, zero idle polling) — the violation is an **extra live query** (below).

### D-A226-2 — tasks page fires a live placeholder query on every mount

**Observed (payload-proven, `p5_tasks_forensic.json`):** every mount of `/tasks` — fresh load, SPA nav-return, and full document reload — issues `POST /api/v1/query` with body `{"query":"Найди __none__"}`. Fresh load = 2 POSTs (`Найди __none__` + `Найди login` at t≈343ms), SPA nav-return = 1 POST (`Найди __none__` at t≈88.6s), full reload = 1 POST. The snapshot layer is not involved for this query (only one snapshot key exists: `po-page-snapshot:v1:tasks:text:login:Найди login`).

**Root cause (code, deterministic):** `TasksPage` always renders `<TaskDetailsDrawer task={selectedTask} …/>` (drawer closed ⇒ `task=null`). The drawer's body hook is `useHarness(key ? intelligenceQuery(key, mode) : 'Найди __none__')` (`Pages.tsx:108`), and `useHarness` (`Pages.tsx:23-26`) **unconditionally** fires `agent.query({ query })` on mount (its effect has no enabled-guard, no snapshot). So every page mount performs one wasted LLM+source round-trip whose result is never rendered (the drawer body is gated by `{task && …}`).

**Impact:** (1) violates the P5 "no new source reads on nav-return" acceptance criterion for the tasks page; (2) one wasted agent query (LLM + bounded source reads) per visit to `/tasks`, even with the drawer never opened. No data corruption, no false state — the list itself is snapshot-correct.

**Owner fix (minimal, frontend only, generic):** mount the intelligence panel only when a task is selected — extract the drawer's intelligence block into a child component (e.g. `<TaskIntelligence key={task.key} task={task} />`) rendered only when `task` is non-null, so `useHarness` runs only for user-initiated drills and the `Найди __none__` placeholder disappears entirely. Alternative: add an `enabled` flag to the hook and skip the load while disabled. Regression: with the drawer closed, mounting `/tasks` (and returning to it) must produce **zero** `/api/v1/query` POSTs beyond the single snapshot query.

### Refresh-failure behavior — GREEN

Killed the agent (spec'd local failure), clicked `Обновить`: state = `Не удалось обновить · данные на 08:30 PM` (old timestamp preserved), old data still visible (workload 14 rows, capacity 9 rows), **snapshot not erased** (6 sessionStorage keys before and after; `p5_refresh_failure.png`). Restarted the agent at the same HEAD; retry refresh succeeded with exactly 6 POSTs and identical data (`p5_refresh_retry_ok.png`).

### P6 subset (snapshot context isolation, Team DMS↔OLP) — GREEN

Same context: switch Team space to OLP (uncached) → 6 live POSTs (correct — first load is live); switch back to DMS → **0** POSTs, DMS data byte-identical to the original load (14/9 rows). No cross-space snapshot leakage in the tested direction. Full P6 (all pages × contexts) remains not gated.

### Storage policy — GREEN

Fresh browser context (no prior visits): `sessionStorage` snapshot keys = **0** (only `po-agent-runtime-session-id`), `localStorage` = **0** keys (the `po-local-tasks` key appears only after local-task CRUD, per A225). No snapshot data written to `localStorage` anywhere in the run.

---

## P7 — Retained design smoke (backgrounds + overflow) — GREEN

`p7_backgrounds_overflow.json`: **6 distinct** slide-derived SVG backgrounds, one per page (`overview/tasks/sprint/releases/team/quality-bg.svg`), all matched by computed `background-image`. **0** document overflow at 1440 and **0** at 480 across all six pages. (A225's 107-row Attention internal scroll, Tasks filters/CRUD, Sprint throughput/risk, Releases honest limitation, WMB-102 quality semantics, competency, and Evidence/Trace lineage were NOT re-gated this pass — STOP at P4; they were all GREEN at the A225 baseline and the A226 diff does not touch their data paths.)

---

## P8 — audit (partial, clean in the tested window)

From the agent log (agent PID 42486, session window):
- **0 AS21 mutations** — no POST/PUT/PATCH/DELETE to any `swtr-read`/`swtr`/`as21` path (only GET reads + the expected `chat/completions` + `/api/v1/query`).
- **0 local factual fallback reads** — 0 `GET /api/v1/tasks` (local store).
- **0 tenant-wide scans** — the only `task-query` calls without a `space=` param are bounded **per-assignee** reads (`task-query?…&assignee=<login>`), i.e. the certified person-scoped contract (A195D/A221R2), not unscoped tenant scans. 1371 total `swtr-read` reads, all bounded.
- **Post-restart window (agent PID 42740, P5 harness):** 25 `/api/v1/query` POSTs, all 200 (the P5 per-page query sets + P6 subset + retry); the same mutation/local-fallback/unscoped scan checks hold (all are the certified page query sets, space-scoped or person-scoped). The `sessionStorage`/`localStorage` policy portion was completed in P5 (see above). Full cross-process audit remains not gated.

---

## Environment / tooling notes
- Qwen3.8-27B endpoint (`https://api.ai.sbt/openai/v1`, model `Qwen/Qwen3.8-27B`) was **degraded in a window** during the session (direct agent API calls returned `planner failed robust bounded repair: [ReadTimeout ×4]`); it **recovered** mid-session (direct 3-probe: HTTP 200 in <5s). The P4 RED is **not** endpoint-related — it reproduces with zero LLM via the capability driver.
- `curl` is blocked by corporate policy; all HTTP done via `python urllib`. `timeout`/`pgrep`/`$(…)` unavailable in the shell (use `lsof -nP -iTCP:<port>`, `$!`, background `&`).
- Python Playwright is not in the `po-agent-platform-v2/.venv`; Browser C used Node `@playwright/test` 1.62.1 (chromium-1234 present).

## Recommendation
**STOP.** Verdict remains **RED** with **two** independent confirmed defects:

1. **D-A226-1 (P4, task-api only):** plumb `created_at`/`updated_at`/`deadline` through the live assignee route (`swtr_assignee.py` TQL attributes + `_canonical_row`) + non-mocked regression (the current test masks the production branch).
2. **D-A226-2 (P5, frontend only):** stop the always-live `Найди __none__` placeholder — mount the drawer's intelligence panel only when a task is selected (or add an `enabled` guard to the hook) + regression asserting zero extra `/api/v1/query` POSTs on `/tasks` mount/return with the drawer closed.

Gated GREEN and retained: P0, P1, P2, P3, P7 (backgrounds/overflow), P5 refresh-failure + storage + 5/6 pages, P6 subset (Team DMS↔OLP).

**A226R re-gate scope after owner fixes:** P4 (WMB:7 + DMS:15 exact parity, source-backed rows), P5 tasks page (fresh=1, back=0, drawer-open drill still works), and the remaining not-gated items (full P6 context isolation, full P8 audit) — in one consolidated pass. Do not start the Learning Reviewer.
