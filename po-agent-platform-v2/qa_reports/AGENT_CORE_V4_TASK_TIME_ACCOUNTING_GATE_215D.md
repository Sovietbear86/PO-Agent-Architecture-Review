# A215D — Task Time-Accounting Gate (task.time_spent / task.worklogs, DMS-380)

**Verdict:** `TASK_TIME_ACCOUNTING_GREEN_A215D`

**START_HEAD:** `5e641bd82a22e282b079cda401c2cecfedfd3809`
**Role:** QA/adversarial tester + service operator only. No production code modified.
**Date:** 2026-09-25

---

## Owner implementation (4 commits)
- `c81c721` — task-api `GET /api/v1/swtr-read/tasks/{task_code}/work-logs` (bounded `get_work_sum` + paginated `get_work_report`, page_size ≤1000, max_pages ≤500, `complete = not has_next`, ms→hours, convention metadata).
- `e93d579` — `TaskApiAS21Adapter.get_task_worklogs` (key regex, typed 404/502/503/504 mapping, response shape validation).
- `040fc33` — plugin `builtin.time_accounting.task` (skills `task.time_spent`, `task.worklogs`).
- `51c97a6` — focused tests.

## Phase 0 — architecture invariant: PASS
- Diff `5b2fc71..5e641bd` (src+task-api+tests) = exactly the 4 owner files + docs. **No Agent Core/planner/runtime change.**
- Plugin registry discovers both skills (`builtin.time_accounting.task`); CompletionContract + UIContract present.
- dummy-55 / plugin-registry tests 13/13.

## Phase 1 — focused tests: GREEN
- `test_agent_core_v4_time_accounting.py`: **5/5** (complete bounded collection required; aggregate/entry mismatch fails closed; user/date/type/duration preserved; no local fallback).
- All V4 suites: **170 passed / 1 failed** — sole failure is the A215B known test-logic artifact (`test_team_capacity_fails_on_source_estimates_before_asking_for_baseline`, unassigned missing-estimate fixture; production proven correct in A215B). Unexplained failures: 0.

## Phase 2 — direct MCP vs Task API parity (DMS-380): **EXACT**
- direct MCP `get_work_sum`: 172,800,000 ms = **48.0h**; `get_work_report`: **6 entries**, `hasNext=false`, entry sum 172,800,000 ms = 48.0h.
- Task API route: `total_hours=48.0`, `entry_total_hours=48.0`, 6 entries, `complete=true`, `pages_read=1`, `source=REAL_AS21`, `convention={worklog_day_hours:8, worklog_week_days:5}`.
- Field-by-field exact: worklog ids, dates, user externalIds, type codes+names, raw millis, durations. **No dropped or fabricated entry.**
- Entry set: Garanin.R.V ×4 (2026-09-04..07, code 61 "2Р_Кодирование", PT8H each); Semavin.M.M ×2 (2026-09-01/02, code 44 "4Р_Тестирование компонента", PT8H each).

## Phase 3 — production adapter parity: **EXACT**
- `TaskApiAS21Adapter.get_task_worklogs("DMS-380")`: byte-identical entries to Task API route and direct MCP; total 48.0, complete=True.
- Negatives fail closed: `DMS-999999` → `AS21SourceError Task DMS-999999 worklogs not found` (source 404); `not a key!!` → `AS21SourceError Invalid task key` (rejected before source). No tenant scan, no local task-DB read.

## Phase 4 — task.time_spent NL gate: 5/5 EXACT 48h
| form | result |
|------|--------|
| `сколько времени списано на DMS-380` | COMPLETED `task.time_spent`, 48.0h, DMS-380, n=6 |
| `сколько затрачено на DMS-380` | COMPLETED, 48.0h |
| `фактические трудозатраты по DMS-380` | COMPLETED, 48.0h |
| `time spent DMS-380` | COMPLETED, 48.0h |
| concise `время DMS-380` | COMPLETED, 48.0h |
- No estimate/capacity substitution; `source=REAL_AS21, complete=true`; no planner invention.
- F1 (non-blocking): Cyrillic variant `ДМС-380 время` → planner passes the non-canonical key verbatim → adapter rejects → typed `source_protocol_error` fail-closed (2/2 reproducible). Safe: no fabrication, no local fallback. Pre-existing planner task-key transliteration class, not a time-accounting defect.

## Phase 5 — task.worklogs NL gate: 4/4 EXACT 6-entry parity
| form | skill | result |
|------|-------|--------|
| `кто и когда списывал время на DMS-380` | task.worklogs | EXACT 6 entries |
| `worklogs DMS-380` | task.worklogs | EXACT 6 entries |
| `журнал списания времени по задаче DMS-380` | task.worklogs | EXACT 6 entries |
| `покажи список списаний времени по DMS-380` | task.worklogs | EXACT 6 entries |
- Verified: **Semavin.M.M = 2 × 8h; Garanin.R.V = 4 × 8h**; all dates and work types exact; total 48.0h.
- F2 (non-blocking): the 4th mandated form `покажи списания по DMS-380` deterministically (2/2) routes to `task.time_spent` instead of `task.worklogs`; the answer remains source-accurate (48h, worklog_count=6, COMPLETED). Planner skill-selection ambiguity on "списания", not a source/skill defect. A cleaner 4th worklogs form is exact (see table).

## Phase 6 — Browser C: 2/2 GREEN
- C1 (time_spent): COMPLETED, "48" visible, no generic ERROR, no source-limitation text, no stale source error, no stack/session/contract leak.
- C2 (worklogs): COMPLETED, 48h visible + both members (Семавин/Гаранин) + 2026-09-0x dates + work types (Кодирование/Тестирование) visible in the UI. No leaks.
- Screenshots: `qa_215d_browser_c/`.

## Phase 7 — empty/zero task proof: **REAL_EMPTY proven**
- Source-proven zero: `get_work_sum("DMS-423")` = `{time: 0, duration: "PT0S"}`; `get_work_report` = 0 entries, `hasNext=false`.
- Task API route: `total_hours=0.0, entries=[], complete=true`.
- NL agent "сколько времени списано на DMS-423": COMPLETED, `time_spent_hours=0.0, worklog_count=0, source=REAL_AS21` — answer "По задаче DMS-423 списано 0 ч. (записей в worklog нет)". Source-backed REAL_EMPTY, **not** SOURCE_UNAVAILABLE, no fabricated entries.
- Bonus source fact: durations are not 8h-quantized (DMS-274 = PT10H30M) — the facade `convention` metadata is display-only; no computation depends on it.

## Phase 8 — retained smoke: GREEN
- team.workload DMS: COMPLETED 52 active / 18 completed / 5 unassigned / 13 members (live drift verified: DMS-SPRNT-3 membership grew 68→70 since A215; agent matches live source).
- team.capacity DMS: terminal typed `v4_capability_unavailable` (A215B fail-closed retained).
- release.search WMB: `[24Q1, 24Q2, 25Q1]` (A212 parity).
- release.health 24Q1/WMB: typed SOURCE_CONDITIONAL (A214 parity).
- Batch 3 plugin discovery: `builtin.batch3.team_release` in registry; registry 13/13 + batch3 tests 6/6.
- dummy-55: GREEN.

## Phase 9 — source audit: GREEN
- A215D task-api window (fresh log after restart): **local factual `/api/v1/tasks` reads = 0; unscoped tenant-wide scans = 0.**
- 21 worklog route calls — all bounded per-task `GET /swtr-read/tasks/{code}/work-logs` (DMS-380 ×19, DMS-423 ×1, DMS-999999 ×1 404-negative). Route code invokes only `get_work_sum` + `get_work_report`; **no mutation tools reachable or called.**

## Non-blocking findings
- **F1** Cyrillic task key "ДМС-380" → typed fail-closed `source_protocol_error` (safe; planner transliteration class).
- **F2** "покажи списания" → aggregate skill routing (answer still source-accurate).
- **F3 (observation)** facade hardcodes `convention {worklog_day_hours: 8, worklog_week_days: 5}`; A215C proved 8h as DMS-380's entry quantum, and worklog durations are demonstrably not 8h-quantized elsewhere (PT10H30M) — owner may want the convention derived from the source or explicitly marked illustrative.

## Services left running
- agent 8212 (PID 82001 @ 5e641bd, 127.0.0.1)
- task-api 8241 (PID 81954, system python3, SSE 48 tools, new work-logs route)
- MCP-SWTR 3000 (PID 29268)
- UI 5175 (PID 85296, [::1]) / 5176 (PID 12824)

## Recommendation
Freeze an immutable **time-accounting checkpoint** and resume **A216 / Batch 3 QA**. Keep sprint/team `time_spent` as the next source-bounded extension after Batch 3 unless the owner explicitly prioritizes it.
