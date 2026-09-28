# A226 — Final UI polish + actual utilization + team aging + page snapshots

**Verdict:** `AGENT_CORE_V4_UI_POLISH_SNAPSHOT_RED_A226`

**Classification:** `RED_SOURCE_TIMESTAMP_PLUMBING` (team-scoped `task.aging` depends on the live assignee route, which does not expose source `created_at`; the capability therefore fails closed on every space)

**Test HEAD / START_HEAD:** `de4cc9c07395c4f8760ef3ca7d85c970d1e50378`
**Frozen baseline:** A225 `AGENT_CORE_V4_UI_VISUAL_DESIGN_GREEN_A225` at `09bcbd22d87b478396970d0ddf89cbf6d531d421` (diff base for this assignment)
**Test stack:** agent 8212 (PID 42486, `PO_AGENT_EXPECTED_HEAD=de4cc9c`, fresh restart at report time), task-api 8241 (PID 26008, system py3), MCP-SWTR 3000 (PID 25954), vite `[::1]:5175` (PID 42534, fresh). All 200 at session start; agent `/live` 200.
**Artifacts:** `po-agent-platform-v2/qa_artifacts/qa_226_browser/` (`capability_direct.json`, `oracle_p2.json`, `oracle_p4.json`, `p2_team_dms.png`, `p4_agent_api.json`, `p4_agent_trajectory.json`, `p4_quality_aging_ui.png`, `p7_backgrounds_overflow.json`, `p2_team_p4_ui.json`).

**STOP rule applied:** first confirmed boundary reached at **P4**; P1 (Browser C dark surfaces), P5 (snapshot policy), P6 (snapshot context isolation) and the full P8 audit were **not** gated (spec: "identify first confirmed boundary … STOP"). Evidence for the boundary (screenshots + source + API trajectory + Oracle B) is preserved below and in artifacts.

---

## Phase results

| Phase | Result | Note |
|---|---|---|
| P0 diff/build/architecture | **GREEN** | 0 Agent Core/planner/runtime drift; backend deltas = plugin team-aging + utilization worklog_count only; frontend = presentation/snapshot wiring; 0 mutation verbs added |
| P1 dark structured surfaces | **NOT GATED** | STOP at P4 |
| P2 Team actual utilization | **GREEN** | exact per-member parity DMS 9/9 + OLP REAL_EMPTY; worklog_count present; numerator REAL_AS21 / denominator OWNER_POLICY; 40ч visible; no false SOURCE_UNAVAILABLE |
| P3 top-right products | **GREEN** | exactly `OLAP` + `DataMarts`; DTMS absent; click inert (no query fired); route nav unaffected |
| P4 team-scoped Aging | **RED (first confirmed boundary)** | `/assignee-tasks` route lacks `created_at` → `task.aging` team_scope fails closed on every space |
| P5 snapshot policy | **NOT GATED** | STOP at P4 (snapshot layer code-reviewed, see below) |
| P6 snapshot context isolation | **NOT GATED** | STOP at P4 |
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

## P7 — Retained design smoke (backgrounds + overflow) — GREEN

`p7_backgrounds_overflow.json`: **6 distinct** slide-derived SVG backgrounds, one per page (`overview/tasks/sprint/releases/team/quality-bg.svg`), all matched by computed `background-image`. **0** document overflow at 1440 and **0** at 480 across all six pages. (A225's 107-row Attention internal scroll, Tasks filters/CRUD, Sprint throughput/risk, Releases honest limitation, WMB-102 quality semantics, competency, and Evidence/Trace lineage were NOT re-gated this pass — STOP at P4; they were all GREEN at the A225 baseline and the A226 diff does not touch their data paths.)

---

## P8 — audit (partial, clean in the tested window)

From the agent log (agent PID 42486, session window):
- **0 AS21 mutations** — no POST/PUT/PATCH/DELETE to any `swtr-read`/`swtr`/`as21` path (only GET reads + the expected `chat/completions` + `/api/v1/query`).
- **0 local factual fallback reads** — 0 `GET /api/v1/tasks` (local store).
- **0 tenant-wide scans** — the only `task-query` calls without a `space=` param are bounded **per-assignee** reads (`task-query?…&assignee=<login>`), i.e. the certified person-scoped contract (A195D/A221R2), not unscoped tenant scans. 1371 total `swtr-read` reads, all bounded.
- (Full-window audit + snapshot-traffic isolation + `localStorage`/`sessionStorage` policy not completed — STOP at P4.)

---

## Environment / tooling notes
- Qwen3.8-27B endpoint (`https://api.ai.sbt/openai/v1`, model `Qwen/Qwen3.8-27B`) was **degraded in a window** during the session (direct agent API calls returned `planner failed robust bounded repair: [ReadTimeout ×4]`); it **recovered** mid-session (direct 3-probe: HTTP 200 in <5s). The P4 RED is **not** endpoint-related — it reproduces with zero LLM via the capability driver.
- `curl` is blocked by corporate policy; all HTTP done via `python urllib`. `timeout`/`pgrep`/`$(…)` unavailable in the shell (use `lsof -nP -iTCP:<port>`, `$!`, background `&`).
- Python Playwright is not in the `po-agent-platform-v2/.venv`; Browser C used Node `@playwright/test` 1.62.1 (chromium-1234 present).

## Recommendation
**STOP.** Do not proceed to P1/P5/P6/remaining P7/P8 or to the Learning Reviewer. Owner should apply the P4 two-part task-api fix (plumb `created_at` through the live assignee route) + the non-mocked regression, then re-gate P4 (WMB:7 + DMS:15 exact parity, both must complete with source-backed rows) and the not-yet-gated phases (P1 dark surfaces, P5 snapshot policy, P6 context isolation, full P8 audit) in one consolidated A226R.
