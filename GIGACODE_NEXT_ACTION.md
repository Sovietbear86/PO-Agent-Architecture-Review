# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_129_OWNER_FIX_TRUE_AB_REGRESSION`

## Owner fix under test
Owner commit: `54f7f01e967f03bd62b0e6592059c898505ef4b9`

Defect fixed: `HardenedProductionTaskApiAS21Adapter.search_tasks()` previously bypassed the live production assignee route whenever `project_space` was present and called the empty legacy `/api/v1/tasks` facade. The owner fix gives assignee queries precedence (unless a sprint-specific path is required), so generic and `assignee + space` searches must route through `ProductionTaskApiAS21Adapter.search_tasks()` -> `/api/v1/swtr-read/assignee-tasks` -> REAL AS21.

## Role boundary
You are QA/test executor only. Do NOT modify production code, prompts, skills, adapters, Task API, MCP-SWTR, tests, fixtures, team configuration, AS21 data, testing rules, or this file. Commit/push only QA reports/evidence under `po-agent-platform-v2/qa_reports/`.

## Absolute anti-surrogate rules
- NO local DB synchronization/population.
- NO local DB/cache as Agent truth or Oracle truth.
- NO fake/mock/frozen/historical expected answers.
- NO Harness/Agent as Oracle B.
- NO copying expected task counts/keys from Assignment 128 as current truth.
- NO AS21 writes.
- HTTP 200 / COMPLETED is never sufficient for PASS.
- Exact business facts must be compared A vs independent B.
- For task collections, exact task-key-set equality is mandatory.
- If Oracle B cannot be independently established for a case, mark it `ORACLE_NOT_PROVEN`; never convert that case to PASS.

## Goal
First certify the owner routing fix with TRUE live A/B. Only if the focused gate is GREEN, run regression. If focused gate fails, STOP and report the first failing boundary; do not waste time on the 54-skill marathon.

A = freshly restarted production Harness/Agent.
B = independently queried REAL AS21/MCP-SWTR source facts.

Approved task spaces: `WMB, STS, OLP, DMS, CRPV`.

## Phase 0 — provenance and runtime reset
1. `git switch feat/core8-real-query-hardening-v2`.
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
3. Record exact HEAD; it MUST contain owner commit `54f7f01e...`.
4. Record `git status --porcelain` and full diffs of any pre-existing dirty files. Do not modify/stash/delete them.
5. Important: Assignment 128 observed pre-existing local changes in `po-agent-platform-v2/src/po_agent/adapters/task_api.py` and `task-api/app/routers/swtr_assignee.py`. Treat them as owner-fix-under-test state only if still present; hash/diff them explicitly. Do not silently normalize them.
6. Kill all old Task API/Harness processes; prove ports free.
7. Start Task API and Harness fresh from the current working tree; record PID/start time/CWD/command and loaded Git HEAD.
8. Verify Task API, Harness and MCP-SWTR health.
9. Timeout >=120s; heavy source reads may use 180s; retry transient timeout/502 up to 2 times with 20–30s backoff. Concurrency=1 for source-heavy tests.

## Phase 1 — focused independent Oracle B for Garanin
Build current truth from REAL AS21, independently of Harness:

`search_users -> exact externalId Garanin.R.V -> find_units_by_filter(assigned_to = "Garanin.R.V") -> complete pagination -> approved-space filter`

Capture exact sets:
- `B_GARANIN_ALL_KEYS`
- `B_GARANIN_DMS_KEYS`
- `B_GARANIN_OLP_KEYS`
- per-space counts/keys for all approved spaces
- source request/evidence and pagination proof.

Do not assume the previous count of 16 remains current.

## Phase 2 — direct Task API boundary
Call fresh:
1. `/api/v1/swtr-read/assignee-tasks?assignee=Garanin.R.V`
2. same with `space=DMS`
3. same with `space=OLP`

Required exact invariants:
- TaskApi generic keys == `B_GARANIN_ALL_KEYS`
- TaskApi DMS keys == `B_GARANIN_DMS_KEYS`
- TaskApi OLP keys == `B_GARANIN_OLP_KEYS`

Capture actual route/source/external_id/pages_read.

## Phase 3 — focused Harness A certification
Fresh session for every query:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Гаранина в OLP`

For every query capture:
- status, intent, skill/version;
- semantic member and space;
- capability args;
- concrete adapter class;
- ACTUAL downstream endpoint;
- evidence/source;
- exact returned task keys;
- elapsed.

Mandatory routing invariant for 1-3 when no sprint is requested:
`/api/v1/swtr-read/assignee-tasks` must be used and `/api/v1/tasks` must NOT be used as authoritative source.

Mandatory equality:
- A generic == B generic
- A DMS == B DMS
- A OLP == B OLP

Repeat all three once in fresh sessions if first pass is GREEN.

## Phase 4 — independent second-member control
Use `Kalachanov.V.V` only as an anti-hardcoding control, not as a zero-task expectation.

Build B independently from REAL AS21 across ALL approved spaces `WMB, STS, OLP, DMS, CRPV`; capture exact keys and per-space distribution. Then run fresh A query `Задачи Калачанова` and compare exact key sets.

Known owner context must NOT be used as Oracle: Kalachanov may have tasks in WMB/CRPV/STS. Current source decides the answer.

## Focused Gate
Proceed to Phase 5 only if ALL of Phases 1-4 have independently proven Oracle B and exact A/B equality.

If any mismatch exists, STOP with `FOCUSED_AB_REGRESSION_FAILED` and identify FIRST_FAILING_BOUNDARY.

## Phase 5 — targeted semantic/source regression
Run TRUE A/B controls for the historically fragile paths using fresh real entities discovered from current AS21:
- exact task ID: existing;
- exact task ID: nonexistent;
- sprint ID only;
- sprint + person;
- sprint + status;
- person only;
- person + explicit space/product;
- person + status where supported;
- correction turn: new status replaces old while unaffected slots survive.

For task-returning cases compare exact key sets against independent REAL AS21 filtering. For non-task semantic cases compare grounded identifiers/constraints and independently verifiable source facts.

## Phase 6 — 54-skill regression
Only after Focused Gate GREEN.

Run all 54 registered skills sequentially against the fresh production runtime. Use realistic Russian business queries and valid current REAL entities. Do not manufacture PASS from HTTP status.

For every skill classify:
- `AB_PASS` — independently proven business facts equal;
- `EXPECTED_CLARIFICATION` — clarification is required by contract and input is genuinely ambiguous/incomplete;
- `SOURCE_CAPABILITY_UNAVAILABLE_BY_DESIGN` — required source fact is genuinely unavailable and product returns the correct typed state;
- `ENVIRONMENT_BLOCKED` — transient source/environment prevented proof after retries;
- `AB_MISMATCH` — independently proven business facts differ;
- `ORACLE_NOT_PROVEN` — independent B could not be established.

For task collections exact key-set equality is primary. For metrics, independently reconstruct the input task set/source facts and calculation where source contract permits. Never use Harness output as expected value.

Record total counts; they must sum exactly to 54.

## Phase 7 — learning-loop guardrail regression
Do NOT teach/promote anything merely because an answer is zero.

If A returns zero and independent B is non-zero, classify `AB_MISMATCH`, trace the boundary, and only then assess whether a generalized learning candidate is appropriate. No hardcoded member/task/count facts. No rule such as “zero is impossible”.

If both A and B are zero for the same current scope, it is valid zero and no learning event is justified.

## Phase 8 — FIRST_FAILING_BOUNDARY
Allowed labels include:
- `SEMANTIC_INTERPRETATION`
- `MEMBER_IDENTITY_RESOLUTION`
- `SPACE_SCOPE_RESOLUTION`
- `SKILL_RESOLUTION`
- `CAPABILITY_ARGUMENT_BUILDING`
- `PRODUCTION_ADAPTER_ROUTING`
- `TASK_API_LIVE_ASSIGNEE_FACADE`
- `MCP_USER_RESOLUTION`
- `MCP_TQL_QUERY`
- `SOURCE_RESPONSE_DECODING`
- `GLOBAL_SPACE_FILTERING`
- `DETERMINISTIC_CALCULATION`
- `CAPABILITY_RESULT_PROPAGATION`
- `RESPONSE_STATUS_MAPPING`
- `RESPONSE_RENDERING`
- `QA_HARNESS_ORACLE_DEFECT`

Always show last-correct and first-incorrect artifacts.

## Phase 9 — final anti-surrogate audit
Report explicitly:
- exact HEAD and whether owner commit is contained;
- dirty-file hashes/diffs if any;
- fresh PIDs/start times;
- REAL AS21 reads count/evidence;
- local DB/cache authoritative reads = 0;
- fake/mock/frozen truth = 0;
- AS21 writes = 0;
- Oracle independence method;
- exact-key comparison method;
- `/api/v1/tasks` authoritative use for assignee tests = 0;
- all 54 classification counts sum to 54 if marathon executed.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/OWNER_FIX_TRUE_AB_REGRESSION_129.md`

Optional raw evidence prefix:
`OWNER_FIX_TRUE_AB_REGRESSION_129_`

## Allowed final verdicts
- `OWNER_FIX_FOCUSED_AB_GREEN_REGRESSION_GREEN`
- `OWNER_FIX_FOCUSED_AB_GREEN_REGRESSION_DEFECTS_FOUND`
- `FOCUSED_AB_REGRESSION_FAILED`
- `BLOCKED_BY_ENVIRONMENT`
- `BLOCKED_BY_PROVENANCE`

No other GREEN verdict is allowed.

## Finish
Commit/push ONLY QA report/evidence. Do not modify production code. Return full SHA, report path, focused A/B result, 54-skill totals if executed, final verdict, then STOP.

## Start when instructed
Execute Assignment 129 autonomously and strictly as written.