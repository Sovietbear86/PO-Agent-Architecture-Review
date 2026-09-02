# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_123_AUTHORITATIVE_ASSIGNEE_ROUTE_DISCOVERY`

## Why Assignment 122 is NOT accepted as GREEN
Assignment 122 reported `TRUE_AS21_PARITY_GREEN`, but its own evidence proves Oracle B was incomplete:
- `get_sprint_tasks(DMS-SPRNT-1)` returned `hasNext=true`, while only page 0 / 100 tasks was inspected;
- 100 point reads were attempted, but only 98 succeeded;
- the natural-language question `Задачи Гаранина` was reduced to one sprint although the question itself contains no sprint constraint.

Therefore Assignment 122 must be treated as `ORACLE_INCOMPLETE`, not as certification of the Agent.

## Role boundary
You are QA / forensic executor only. Do NOT modify production/backend/frontend code, prompts, skills, adapters, Task API, MCP-SWTR, team data, AS21 data, testing rules, or this file. Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`.

## Absolute prohibitions
- NO synchronization/population of tasks into a local DB.
- NO local DB/cache as source of truth or Oracle.
- NO fake/mock/frozen/historical data as current truth.
- NO AS21 writes.
- NO production fixes.
- NO 54-skill marathon.
- NO arbitrary sprint selection as a substitute for the user question.
- NO unrelated employees or spaces outside the configured project/team scope.
- Do NOT declare GREEN from a partial page, partial point-read set, counts alone, or absence of evidence.

## Goal
Discover and prove the authoritative REAL AS21/MCP-SWTR read route capable of answering the business question:

`Задачи Гаранина`

without silently adding a sprint constraint and without local synchronization.

This assignment is SOURCE/CONTRACT DISCOVERY first. Do not test Agent correctness until a complete independent Oracle route is proven.

## Phase 0 — provenance and health
1. Pull current `feat/core8-real-query-hardening-v2`; record exact HEAD and clean worktree.
2. Record service PIDs, MCP-SWTR transport/tool count and REAL AS21 health.
3. Confirm exact Garanin identity from authoritative repository team config; expected `Garanin.R.V` only if confirmed.
4. Record approved project spaces from authoritative project configuration. Do not invent or broaden scope.
5. Confirm local DB/sync/cache/fake/mock usage = 0 and AS21 writes = 0.

## Phase 1 — inventory the REAL MCP-SWTR read contract
Inspect the actual currently exposed MCP-SWTR tool schemas, not assumptions from old reports.

Find every READ-ONLY tool that can potentially retrieve/filter tasks/units by any of:
- `assigned_to` / assignee / user login;
- member/user;
- space/project/product;
- query/filter expression;
- task search;
- sprint/release only if needed as a bounded fallback.

For each relevant tool record:
- exact tool name;
- exact input schema/arguments;
- pagination arguments;
- filters supported server-side;
- fields returned;
- whether task key/code is returned;
- whether `assigned_to` is returned;
- whether response is complete/paginated;
- whether the tool is a true REAL AS21 read.

Do not infer capabilities from names. Prove them from schema plus one safe live read where necessary.

## Phase 2 — prove or reject a DIRECT assignee Oracle route
Priority is a direct authoritative source query equivalent to:
`assigned_to == Garanin.R.V`
within the approved project scope.

Try only schema-supported READ operations.

A route is `DIRECT_ASSIGNEE_ROUTE_PROVEN` only if all are true:
1. REAL AS21 is the source;
2. assignee constraint is actually applied by the source request, not post-hoc guessed;
3. all pages can be traversed to completion;
4. exact task keys are returned or can be authoritatively point-read;
5. approved scope can be enforced;
6. no local DB/cache/sync/Harness answer participates.

Capture exact requests, decoded response contract, pagination evidence and resulting task-key set.

## Phase 3 — if no direct assignee route exists, find a COMPLETE bounded enumeration route
Only if Phase 2 proves no direct route is available, determine whether current MCP-SWTR exposes a complete authoritative enumeration of all tasks in the approved scope.

Requirements:
- every approved scope segment must be enumerable;
- pagination must be executable to completion, not merely expose `hasNext=true`;
- each enumerated task must have an authoritative way to obtain `assigned_to` (for example `read_unit`);
- failed point reads must be retried; any unresolved point read makes the Oracle incomplete unless the failed key is authoritatively proven irrelevant by another source read;
- no arbitrary single sprint may stand in for the entire query scope.

If complete enumeration is impossible because the MCP tool contract cannot request page 1+, explicitly prove that contract limitation.

## Phase 4 — classify the source capability
Exactly one primary outcome:

### `DIRECT_ASSIGNEE_ROUTE_PROVEN`
A complete live REAL AS21 assignee-filtered Oracle route exists.

### `BOUNDED_ENUMERATION_ROUTE_PROVEN`
No direct assignee route exists, but complete live enumeration + authoritative assignee point reads can answer the question.

### `MCP_ASSIGNEE_CAPABILITY_GAP_PROVEN`
Current MCP-SWTR contract cannot completely answer the question because required assignee filtering and/or complete pagination/enumeration is unavailable.

### `BLOCKED_BY_ENVIRONMENT`
A route appears contractually possible but cannot be exercised due current REAL AS21/environment failure after retries.

Do NOT use `GREEN`, `PARITY_GREEN`, or any Agent certification verdict in Assignment 123.

## Phase 5 — only if a complete Oracle route is proven
If and only if Phase 2 or Phase 3 proves a complete Oracle route, execute that route once for `Garanin.R.V` and record:
- exact authoritative task-key set;
- exact count;
- scope searched;
- pagination completion proof;
- number of source reads;
- failed reads = 0 for a complete Oracle.

Do NOT compare to Harness/UI yet. That is the next assignment.

If Oracle cannot be completed, STOP after proving the MCP capability gap. Do not compensate with local synchronization.

## Important correction to Assignment 122
The following is structurally forbidden:
`get_sprint_tasks(DMS-SPRNT-1) -> first 100 rows -> 98 successful read_unit -> zero Garanin -> GREEN`

Reasons:
1. `hasNext=true` means the sprint set was incomplete;
2. failed point reads mean assignee truth was incomplete;
3. one sprint is not equivalent to unconstrained `Задачи Гаранина`.

## Mandatory evidence table
Report must contain:
- HEAD/worktree;
- MCP-SWTR health and tool count;
- confirmed Garanin identity;
- authoritative approved scope;
- candidate read tools and exact schemas;
- direct assignee filter available: YES/NO + proof;
- executable pagination available: YES/NO + proof;
- complete approved-scope enumeration available: YES/NO + proof;
- authoritative assignee field available: YES/NO + where;
- Oracle completeness: COMPLETE/INCOMPLETE;
- exact task-key set only if COMPLETE;
- local DB/sync/cache/fake/mock/historical usage = 0;
- AS21 writes = 0.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/AUTHORITATIVE_ASSIGNEE_ROUTE_DISCOVERY_123.md`

Optional raw evidence prefix:
`AUTHORITATIVE_ASSIGNEE_ROUTE_DISCOVERY_123_`

## Finish
Commit/push only QA report/evidence, provide full SHA, then STOP.

## Start when instructed
Execute Assignment 123 autonomously. Do not modify production code and do not synchronize/populate task data.