# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_117_LIVE_MEMBER_ROUTE_CONTRACT_PROOF`

## Why this assignment exists
Owner review of Assignment 116 found that its proposed fix is not yet sufficient for the original defect `Задачи Гаранина`.

The current Harness `TaskApiAS21Adapter.search_tasks()` calls Task API `/api/v1/tasks`, i.e. the cached/local task-list facade. Adding `source_data` only to `/api/v1/swtr-read/tasks/{task_code}` would repair a point-read contract but would NOT by itself prove that member search uses REAL AS21.

Before the owner changes production routing, we need the exact live MCP-SWTR contract that already works when GigaCode queries AS21 directly.

## Role boundary
QA / forensic executor only. DO NOT modify production/backend/frontend code, prompts, skills, semantic logic, adapters, Task API, MCP-SWTR, schemas, testing rules, AS21 data, or this file. Commit/push only QA evidence under `po-agent-platform-v2/qa_reports/`.

## Absolute prohibitions
- NO task synchronization/population utilities.
- NO local DB refresh/population.
- NO local DB/cache as Oracle.
- NO fake/mock/frozen data.
- NO AS21 writes.
- NO assignee extraction changes.
- NO speculative fix.

## Goal
For the exact natural-language request `Задачи Гаранина`, prove the two real routing contracts side by side:

A. Current product path from Browser/Harness.
B. Direct GigaCode/MCP-SWTR path that successfully reaches REAL AS21.

The output must give the owner enough exact request/response contract information to implement a minimal live-read fix without synchronization.

## Phase 0 — provenance and health
1. Fetch/pull branch `feat/core8-real-query-hardening-v2` and record HEAD.
2. Clean worktree.
3. Restart only normal Frontend/Harness/Task API services if needed. Do not sync/populate anything.
4. Record PIDs/ports.
5. Call Task API `/api/v1/swtr-read/health` and prove MCP-SWTR -> REAL AS21 is connected.
6. Directly read one known REAL task and prove `unit.attributes` contains source attributes.

## Phase 1 — prove current Agent A route
Run exactly `Задачи Гаранина` through Browser UI and through the same Harness endpoint used by Browser UI.

Trace the downstream calls and prove whether member search invokes:
- `/api/v1/tasks`,
- `/api/v1/swtr-read/...`,
- another endpoint.

Record exact URL, method, params/body and call order. If `/api/v1/tasks` is used, explicitly classify it as `LOCAL_TASK_LIST_ROUTE` and prove that no live MCP-SWTR member-search call occurs for that request.

Do NOT populate the local task list.

## Phase 2 — prove working Oracle B live route
Using the exact direct mechanism by which GigaCode can successfully query REAL AS21 for Rodion Garanin / `Garanin.R.V`, capture:
- MCP tool name (`find_units`, `find_units_by_filter`, or other — do not guess);
- live tool input schema;
- exact request JSON actually sent;
- pagination semantics and page size;
- whether server-side filtering by `assigned_to` is supported;
- exact response shape;
- where `assigned_to` is represented (top-level vs `attributes[]`);
- exact task-key set returned for Garanin;
- count;
- elapsed time.

If more than one page is required, read all pages needed for a complete authoritative task-key set. Timeout >=120 s; heavy reads may use 180 s; max 2 retries with 20–30 s backoff.

## Phase 3 — one independent member control
Select exactly one other REAL team member with a non-empty Oracle result and repeat only the Oracle B live query contract. This is to prove the contract is generalized and not Garanin-specific.

## Phase 4 — point-read contract separately
Verify `/api/v1/swtr-read/tasks/{task_code}` for one Garanin task:
- `unit.attributes` contains `assigned_to` and `workflow_status` when present in REAL AS21;
- current response does or does not expose `source_data.swtr_attributes`.

Important: classify this as a separate `POINT_READ_MAPPING_GAP`. Do NOT claim it is the root cause of member search unless the traced Agent A route actually uses this endpoint for member search.

## Phase 5 — required final boundary
Report two independent findings if both are true:
1. `MEMBER_SEARCH_SOURCE_ROUTING`: current Harness member search uses local `/api/v1/tasks` instead of a live MCP-SWTR search path.
2. `POINT_READ_MAPPING_GAP`: live point-read returns `unit.attributes` but not the canonical `source_data` mapping expected by some Harness mapping code.

The report must state which finding is the FIRST failing boundary for the original UI request `Задачи Гаранина`.

## Required owner implementation contract
Without changing code, propose the smallest production contract for the owner:
- which Task API live read endpoint should expose member/task search;
- which MCP tool and exact schema it should call;
- how pagination/completeness must work;
- canonical task-row shape required by Harness;
- how `attributes[]` must be normalized exactly once;
- no local DB dependency for authoritative member search.

Do not write implementation code; provide contract/evidence only.

## Mandatory counters
- Browser natural-language requests >= 1
- Direct Harness natural-language requests >= 1
- Oracle B REAL AS21 reads >= 1
- sync/population runs = 0
- local DB authoritative reads = 0
- fake/mock/frozen reads = 0
- AS21 writes = 0

## Output
Primary report:
`po-agent-platform-v2/qa_reports/LIVE_MEMBER_ROUTE_CONTRACT_PROOF_117.md`

Optional evidence prefix:
`LIVE_MEMBER_ROUTE_CONTRACT_PROOF_117_`

Allowed verdicts:
- `LIVE_MEMBER_ROUTE_DEFECT_PROVEN`
- `POINT_READ_MAPPING_GAP_ONLY`
- `MIXED_ROUTE_AND_MAPPING_DEFECTS`
- `NO_ROUTE_DEFECT_PROVEN`
- `BLOCKED_BY_ENVIRONMENT`

Commit/push only QA artifacts, report full SHA, then STOP.

## Start now
Execute Assignment 117 autonomously. Do not ask for permission between phases. Do not modify production code and do not synchronize tasks.