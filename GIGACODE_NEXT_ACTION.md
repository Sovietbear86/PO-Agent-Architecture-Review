# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_125_EXTERNAL_ID_TQL_ROUTE_PROOF`

## Context
Assignment 124 did NOT conclusively prove an MCP assignee capability gap.

It established:
- `search_tasks` is not a valid assignee Oracle route;
- `find_units_by_filter` supports source-side TQL filtering by `assigned_to` and exact space;
- the TQL `assigned_to` property uses the user's `externalId`, not login;
- Assignment 124 stopped because it did not complete the existing two-step lookup `login -> externalId -> find_units_by_filter`.

Therefore the MCP gap verdict remains UNPROVEN until the existing `search_users`/user lookup capabilities are exhausted and a schema-valid TQL query is executed with the real externalId.

## Role boundary
You are QA / forensic executor only. Do NOT modify production/backend/frontend code, Task API, MCP-SWTR, Harness, prompts, skills, adapters, team data, AS21 data, testing rules, or this file. Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`.

## Absolute prohibitions
- NO local DB/sync/cache as truth.
- NO sync scripts or DB population.
- NO fake/mock/frozen/historical data as current truth.
- NO AS21 writes.
- NO Agent/Harness answer as Oracle.
- NO unrelated employees.
- NO 54-skill regression.
- NO production fixes.
- Do NOT declare MCP gap merely because user externalId requires a second existing read step.

## Approved scope
Target member: Rodion Garanin / `Garanin.R.V` only if confirmed by authoritative repository config.
Approved spaces: WMB, STS, OLP, DMS, CRPV if confirmed by authoritative config.

## Goal
Prove or reject this existing REAL AS21 route using only current MCP-SWTR tools:

`Garanin.R.V login -> authoritative AS21 user externalId -> find_units_by_filter(TQL assigned_to = externalId AND exact space) -> complete pagination -> exact task keys`

No new MCP tool may be proposed until this route is conclusively exercised.

## Phase 0 — provenance and health
1. Pull current branch and record exact HEAD/worktree.
2. Record MCP-SWTR health/tool count/transport.
3. Confirm Garanin login and approved scope from authoritative repo config.
4. Confirm prohibited usage = 0 and AS21 writes = 0.
5. Decode all FastMCP envelopes using the Assignment 121 contract.
6. Retry transient 5xx/timeouts up to 2 times with 20–30 sec backoff; timeout >=120 sec.

## Phase 1 — authoritative user externalId discovery
Inspect CURRENT existing MCP-SWTR user-related tools, especially `search_users` and any read-user/find-user equivalent.

Capture exact live schemas and implementation routes.

Using only READ operations, resolve `Garanin.R.V` to the authoritative REAL AS21 user record.

Required proof:
- exact MCP tool and arguments;
- exact REAL AS21 endpoint/payload sent downstream;
- decoded user result(s);
- login/full name;
- authoritative `externalId` or exact field required by TQL `assigned_to.searchField`;
- ambiguity count.

The externalId is accepted only if exactly one authoritative user record matches Garanin's configured identity. If multiple users match, disambiguate using available authoritative fields; do not guess.

If existing tools cannot expose externalId after all relevant schemas are tested, classify `USER_EXTERNAL_ID_LOOKUP_GAP_PROVEN` and STOP. Do not redesign MCP in this assignment.

## Phase 2 — prove exact TQL grammar
Using read-only source/schema/property metadata and existing working TQL examples in repo/MCP implementation, determine the exact syntax for:
- `assigned_to = <externalId>`;
- exact space restriction for DMS;
- exact space restriction for OLP;
- conjunction/AND syntax;
- quoted values/parentheses as required.

Do not guess TQL syntax repeatedly. Capture evidence supporting the constructed grammar.

## Phase 3 — execute DMS direct route
Call `find_units_by_filter` with a schema-valid request using the confirmed Garanin externalId and exact DMS scope.

Required request fields:
- `calculatedAttributes` explicitly supplied as schema requires;
- `attributes` includes at least code/summary/assigned_to and space if supported;
- exact TQL query;
- flat integer `page`;
- explicit `size`;
- timezone if schema supports it.

Capture:
- exact MCP args;
- exact downstream AS21 endpoint/payload;
- decoded response;
- exact task keys;
- returned assignee values;
- returned spaces;
- pageNumber/pageSize/hasNext/total if present.

Validate every returned row belongs to DMS and to the resolved Garanin externalId/identity. If assigned_to is represented as object/reference, normalize only from raw Oracle evidence.

## Phase 4 — pagination proof
If `hasNext=true`, execute page 1 by changing the FLAT integer `page` field to 1. Continue pages sequentially until `hasNext=false` or source metadata proves completion.

Capture each page number, count, task-key set and pagination metadata.

No completeness verdict is permitted if any required page is unexecuted.

## Phase 5 — repeat for OLP
Execute the same authoritative route for exact OLP space using the same resolved externalId.

Traverse all pages to completion.

Capture exact task keys and source evidence.

## Phase 6 — optional remaining approved spaces
Only after DMS and OLP work, determine from authoritative team/product configuration whether Garanin should be searched in any of WMB/STS/CRPV.

Do not broaden scope merely because those spaces are globally approved. Use member/product ownership rules from authoritative project config.

If config says only DMS/OLP for Garanin, state that explicitly and do not search irrelevant spaces.

## Phase 7 — route verdict
Allowed verdicts only:

### `EXISTING_TQL_ASSIGNEE_ROUTE_PROVEN`
Existing MCP-SWTR tools successfully resolve login -> externalId and provide exact assignee + exact-space REAL AS21 filtering with complete pagination.

### `USER_EXTERNAL_ID_LOOKUP_GAP_PROVEN`
`find_units_by_filter` route is otherwise viable but current existing MCP tools cannot authoritatively resolve login to required externalId.

### `TQL_ASSIGNEE_ROUTE_BROKEN`
ExternalId is authoritatively resolved, but a schema-valid/proven TQL query fails or does not enforce assignee+space correctly.

### `PAGINATION_ROUTE_BROKEN`
Assignee+space filtering works, but complete pagination cannot be executed through the current tool schema.

### `BLOCKED_BY_ENVIRONMENT`
Contractually valid route cannot be exercised due transient/current AS21 environment after retries.

Do NOT use generic `MCP_ASSIGNEE_GAP_RECONFIRMED` unless a more precise allowed verdict above is impossible; explain why.

## Mandatory evidence
Report must include:
- exact HEAD;
- exact Garanin configured identity;
- user lookup tool/schema/endpoint;
- resolved externalId (mask only if it is a secret; ordinary AS21 entity IDs are evidence, not credentials);
- ambiguity count;
- exact TQL grammar evidence;
- exact DMS request/payload and all pages;
- exact OLP request/payload and all pages;
- exact task-key sets per space if route works;
- page completion proof;
- `assigned_to` evidence from returned rows;
- local DB/sync/cache/fake/mock/historical Oracle usage = 0;
- AS21 writes = 0.

## Critical anti-shortcut rules
- Needing two READ calls (`search_users` then `find_units_by_filter`) is NOT an MCP capability gap.
- Do not reject the route just because the TQL property uses `externalId` instead of login.
- Do not stop after malformed TQL. Determine exact grammar from source/schema/examples first.
- Do not declare pagination broken without actually attempting `page=1` when `hasNext=true`.
- Do not use fuzzy `query` search as evidence of assignee filtering.
- Do not compare to Agent/Harness/UI in this assignment.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/EXTERNAL_ID_TQL_ROUTE_PROOF_125.md`

Optional raw evidence prefix:
`EXTERNAL_ID_TQL_ROUTE_PROOF_125_`

## Finish
Commit/push only QA report/evidence, provide full SHA, then STOP.

## Start when instructed
Execute Assignment 125 autonomously and narrowly. Do not modify production code and do not synchronize/populate task data.