# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_117R_LIVE_MEMBER_ROUTE_EXECUTION`

## Important
The previous Assignment 117 execution is NOT accepted. It produced `TASK_API_RESPONSE_PARSING_FIX_RETEST_117.md` with `BLOCKED_ON_OWNER_FIX`, but that is not the assignment currently required by the owner.

Do NOT wait for an owner fix. Do NOT propose a Task API parsing fix as the answer. First execute the live routing proof below.

The original user-visible defect is the natural-language query:
`Задачи Гаранина`

The key question is NOT whether `/api/v1/swtr-read/tasks/{code}` can map one point-read task. The key question is why the Browser/Harness path fails while direct GigaCode -> MCP-SWTR -> REAL AS21 reads work.

## Role boundary
You are QA / forensic executor only.
Do NOT modify production/backend/frontend code, prompts, skills, semantic logic, adapters, Task API, MCP-SWTR, schemas, testing rules, AS21 data, or this file.
Commit/push only QA evidence under `po-agent-platform-v2/qa_reports/`.

## Absolute prohibitions
- NO task synchronization/population utilities.
- NO local DB refresh/population.
- NO local DB/cache as Oracle.
- NO fake/mock/frozen data.
- NO AS21 writes.
- NO assignee extraction changes.
- NO speculative production fix.
- DO NOT stop merely because a possible parsing defect was found.
- DO NOT create a verification plan instead of executing tests.

## Phase 0 — exact provenance
1. `git fetch` and align with remote `feat/core8-real-query-hardening-v2` without discarding owner instruction.
2. Record exact HEAD and clean worktree.
3. Record PID/port/command/start time for Frontend, Harness and Task API.
4. Prove Task API `/api/v1/swtr-read/health` is connected to MCP-SWTR.
5. Prove a direct MCP-SWTR `read_unit` reaches REAL AS21.
6. Counters for sync/population must remain zero.

## Phase 1 — EXECUTE Browser + Harness request
Use the exact natural-language text:
`Задачи Гаранина`

Execute it, do not merely inspect code.

A1 Browser UI:
- use a fresh UI session;
- capture actual browser Network request URL, method, body, headers relevant to session;
- capture response;
- capture returned task keys/count/status/error;
- capture elapsed time.

A2 Direct Harness:
- send exactly the same natural-language request to the exact Harness endpoint used by the Browser;
- use a fresh session id;
- capture response, trace/evidence, task keys/count/status/error and elapsed time.

Mandatory: Browser natural-language requests >= 1 AND Direct Harness natural-language requests >= 1.
If either counter is zero, this assignment is incomplete.

## Phase 2 — trace the actual downstream product route
For the exact `Задачи Гаранина` request, prove the real call chain after Harness interpretation.

Determine exactly which Task API route is called:
- `/api/v1/tasks`, OR
- `/api/v1/swtr-read/...`, OR
- another route.

Capture exact URL/method/params and call order.

If the request uses `/api/v1/tasks`, classify it as `LOCAL_TASK_LIST_ROUTE` and prove whether any live MCP-SWTR search is made for the member query. Do NOT populate that local task list.

This phase must distinguish routing from point-read response mapping.

## Phase 3 — EXECUTE Oracle B live member search
Using the same mechanism that works when you query AS21 directly, execute an independent REAL AS21 search for Rodion Garanin / `Garanin.R.V`.

Capture:
- exact MCP tool name actually used (`find_units`, `find_units_by_filter`, or other);
- live input schema;
- exact request JSON;
- whether `assigned_to` filtering is server-side;
- response shape;
- where assignee lives in the response;
- pagination fields;
- every page required for a complete result;
- exact authoritative task-key set;
- exact count;
- elapsed time.

Timeout >=120s. Heavy reads may use 180s. Max 2 retries with 20–30s backoff.

Oracle B must not use Harness output or local DB.

## Phase 4 — exact A/B/C parity table
Create one explicit table for `Задачи Гаранина`:

| Path | Endpoint/tool | Source reached | Task keys | Count | Elapsed | Verdict |
|---|---|---|---|---:|---:|---|
| Browser A1 | ... | ... | ... | ... | ... | ... |
| Harness A2 | ... | ... | ... | ... | ... | ... |
| Oracle B | ... | REAL AS21 | ... | ... | ... | ... |

Primary assertion is exact task-key-set equality, not counts.

## Phase 5 — generalized control member
Choose exactly one other REAL team member for whom Oracle B proves a non-empty task set.
Execute Direct Harness + Oracle B for the equivalent Russian query and compare exact task-key sets.
No full member matrix in this assignment.

## Phase 6 — point-read mapping as separate finding
Only after Phases 1–5, verify one REAL task through `/api/v1/swtr-read/tasks/{task_code}`.
If `unit.attributes` exists but `source_data.swtr_attributes` does not, record:
`POINT_READ_MAPPING_GAP`.

Do NOT call this the root cause of `Задачи Гаранина` unless the actual traced member-search route uses that point-read endpoint.

## Required first-failing-boundary decision
For the original Browser query choose the earliest proven boundary from:
- `UI_PROXY_ROUTE_MISMATCH`
- `HARNESS_ENDPOINT_MISMATCH`
- `SEMANTIC_MEMBER_GROUNDING`
- `CAPABILITY_ARGUMENT_BUILDING`
- `MEMBER_SEARCH_SOURCE_ROUTING`
- `LOCAL_TASK_LIST_ROUTE`
- `MCP_SWTR_SOURCE_CONTRACT`
- `RESPONSE_MAPPING`
- `POINT_READ_MAPPING_GAP` (only if actually on the member-search call path)

If member search goes to `/api/v1/tasks` while Oracle B uses a live MCP search, then the first failing boundary must be reported as routing/local-task-list related, not the unrelated point-read mapping gap.

## Mandatory counters
Report actual numeric values:
- Browser natural-language requests >= 1
- Direct Harness natural-language requests >= 2 (Garanin + control member)
- Oracle B REAL AS21 reads >= 2
- sync/population runs = 0
- local DB authoritative Oracle reads = 0
- fake/mock/frozen reads = 0
- AS21 writes = 0

## Output
Primary report:
`po-agent-platform-v2/qa_reports/LIVE_MEMBER_ROUTE_EXECUTION_117R.md`

Optional raw evidence prefix:
`LIVE_MEMBER_ROUTE_EXECUTION_117R_`

Allowed final verdicts:
- `LIVE_MEMBER_ROUTE_DEFECT_PROVEN`
- `MIXED_ROUTE_AND_POINT_MAPPING_DEFECTS`
- `MEMBER_GROUNDING_DEFECT_PROVEN`
- `NO_ROUTE_DEFECT_PROVEN`
- `BLOCKED_BY_ENVIRONMENT`

A verdict `BLOCKED_ON_OWNER_FIX` is NOT allowed in 117R because no owner fix is prerequisite for this forensic execution.

## Finish
Commit/push only QA report/evidence, provide full SHA and STOP.

## Start now
Execute Assignment 117R autonomously. Do not ask for confirmation between phases. Do not synchronize or populate any task database.