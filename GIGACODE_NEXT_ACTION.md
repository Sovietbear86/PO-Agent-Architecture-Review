# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_215D_TASK_TIME_ACCOUNTING_GATE

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT start A216 / Batch 3.
Commit/push only the QA report.

## Baseline
A215C forensic verdict:
`TIME_ACCOUNTING_SOURCE_READY_FOR_OWNER_IMPLEMENTATION`

Source facts already proven:
- DMS-380 total work time = 48h;
- six dated, user-attributed worklog entries exist in REAL AS21;
- UI "1н. 1д." exactly corresponds to the 48h source total under the source-proven 8h/day, 5d/week convention;
- per-task worklogs are bounded and authoritative;
- utilization remains blocked because no authoritative capacity denominator exists.

## Owner implementation
Commits:
- `c81c721417bf42ac99bff4d4b6c46e6e8b0c3ba1` — bounded Task API worklog facade;
- `e93d579e1fd580186c1b29c7de0e66dd4f427407` — production adapter worklog read;
- `040fc339a4a7042cee93859bb87177d69dd33536` — plugin skills `task.time_spent` and `task.worklogs`;
- `51c97a6ce4c6c9e3678ada1f733d2fffab676d23` — focused tests.

No Agent Core/planner/runtime business routing was added.

## Goal
Certify task-level time accounting end-to-end against REAL AS21, especially DMS-380.

## Phase 0 — architecture invariant
1. Pull branch and record START_HEAD.
2. Diff from A215C baseline.
3. Prove:
   - changes are source facade + adapter + plugin + tests only;
   - no skill-specific branch in Agent Core/planner/runtime;
   - plugin registry discovers both new skills;
   - CompletionContract/UIContract exist;
   - dummy-55 remains GREEN.

## Phase 1 — focused tests
Run:
- `tests/test_agent_core_v4_time_accounting.py`
- relevant plugin-registry/V4 suites

Require:
- complete bounded collection required;
- aggregate/entry mismatch fails closed;
- user/date/type/duration preserved;
- no local fallback.

## Phase 2 — direct source vs Task API parity
For DMS-380:
1. direct MCP `get_work_sum`
2. direct MCP `get_work_report`
3. Task API `GET /api/v1/swtr-read/tasks/DMS-380/work-logs`

Require exact:
- total = 48h;
- entry total = 48h;
- six entries;
- same worklog ids;
- same dates;
- same user externalIds;
- same work types;
- same durations;
- complete=true.

Any dropped or fabricated entry => RED.

## Phase 3 — production adapter parity
Call `TaskApiAS21Adapter.get_task_worklogs("DMS-380")`.

Require exact parity with Phase 2 and no tenant scan/local task DB read.

## Phase 4 — task.time_spent natural-language gate
Run at least 5 forms, including:
- `сколько времени списано на DMS-380`
- `сколько затрачено на DMS-380`
- `фактические трудозатраты по DMS-380`
- `time spent DMS-380`
- one concise variant.

Require:
- correct skill load;
- task key grounded in user query;
- terminal result = 48h;
- no estimate/capacity substitution;
- no planner invention.

## Phase 5 — task.worklogs natural-language gate
Run at least 4 forms, including:
- `покажи списания по DMS-380`
- `кто и когда списывал время на DMS-380`
- `worklogs DMS-380`

Require exact six-entry parity with direct source.

Verify specifically:
- Semavin.M.M has 2 entries × 8h;
- Garanin.R.V has 4 entries × 8h;
- dates and work types exact.

## Phase 6 — Browser C
Real UI for:
- task.time_spent DMS-380;
- task.worklogs DMS-380.

Require:
- readable 48h total;
- worklog table/detail contains user/date/type/duration;
- no generic ERROR;
- no source limitation;
- no stack/session/contract leak.

## Phase 7 — empty/zero task proof
Use at least one REAL AS21 task with no worklogs if source can prove one safely.

Expected:
- source-backed zero is REAL_EMPTY/0h, not SOURCE_UNAVAILABLE;
- no fabricated entries.

If no such task can be proven within bounded QA budget, mark this subcase SOURCE_CONDITIONAL, not RED.

## Phase 8 — retained smoke
Re-run:
- team.workload DMS;
- team.capacity DMS remains terminal SOURCE_CONDITIONAL;
- release.search;
- release.health source-conditional;
- one Batch 3 plugin discovery check;
- dummy-55.

## Phase 9 — source audit
Require:
- local factual /api/v1/tasks reads = 0 for time-accounting requests;
- unscoped tenant-wide scans = 0;
- only bounded per-task worklog source calls;
- no mutation tools called.

## Verdict
Use exactly one:
- `TASK_TIME_ACCOUNTING_GREEN_A215D`
- `TASK_TIME_ACCOUNTING_RED_A215D`

If GREEN:
- recommend immutable time-accounting checkpoint;
- recommend resuming A216 / Batch 3 QA;
- keep sprint/team time_spent as next source-bounded extension after Batch 3 unless the owner explicitly prioritizes it.

If RED:
- identify the first failing boundary and STOP.

Do not modify production code.
