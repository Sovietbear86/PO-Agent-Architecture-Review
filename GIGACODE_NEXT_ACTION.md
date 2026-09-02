# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_124_ASSIGNEE_FILTER_ROUTE_FORENSIC`

## Context
Assignment 123 classified `MCP_ASSIGNEE_CAPABILITY_GAP_PROVEN`, but that conclusion is not yet accepted because two potentially relevant existing MCP-SWTR routes were not fully exercised:

1. `search_tasks(...)` exposes an `assignee` parameter but was left `PENDING`.
2. `find_units_by_filter(request=...)` was rejected after an invalid request missing required `calculatedAttributes`, rather than being tested with its correct schema.

Therefore Assignment 124 is a narrow forensic exercise. Do not inspect unrelated tools or jump to MCP redesign until these two routes are conclusively proven or rejected.

## Role boundary
You are QA / forensic executor only. Do NOT modify production/backend/frontend code, Task API, MCP-SWTR, Harness, prompts, skills, adapters, team data, AS21 data, testing rules, or this file. Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`.

## Absolute prohibitions
- NO local DB population/sync/cache as truth.
- NO `sync_all_tasks.py`, `sync_sprint_tasks.py`, `sse_sync.py`, `swtr_sync.py` or new sync scripts.
- NO fake/mock/frozen data.
- NO AS21 writes.
- NO arbitrary employees/spaces outside configured project scope.
- NO Agent/Harness answer as Oracle.
- NO 54-skill regression.
- NO production fixes.
- NO new MCP tool design until both target routes are fully tested.

## Approved scope
Use only authoritative configured project/team scope already present in repository. Expected spaces: WMB, STS, OLP, DMS, CRPV if confirmed by config. Target member: Rodion Garanin / `Garanin.R.V` only if confirmed by authoritative team config.

## Goal
Determine whether CURRENT MCP-SWTR already provides a complete REAL AS21 route for:

`assigned_to == Garanin.R.V`
AND approved space scope

using either:

A. `search_tasks`
B. `find_units_by_filter`

If either existing tool can do this correctly and completely, Assignment 123's MCP capability-gap verdict is rejected.

## Phase 0 — provenance and health
1. Pull current `feat/core8-real-query-hardening-v2`; record exact HEAD and clean worktree.
2. Record MCP-SWTR tool count/transport and REAL AS21 health.
3. Confirm exact target login and approved spaces from authoritative repo config.
4. Confirm local DB/sync/cache/fake/mock usage = 0; AS21 writes = 0.
5. Decode FastMCP envelopes using the contract proven in Assignment 121 before interpreting row counts/fields.
6. Retry temporary 5xx/timeouts up to 2 times with 20–30 sec backoff; timeout >=120 sec.

## Phase 1 — exact schema proof for `search_tasks`
Capture the live MCP tool schema for `search_tasks` verbatim enough to prove:
- exact argument names/types/defaults;
- whether `assignee` is supported;
- whether space/project/product/scope is supported directly;
- pagination fields/limits;
- returned fields/content structure.

Then inspect the implementation only read-only to determine the exact REAL AS21 request it builds. Record:
- AS21 endpoint used;
- payload/query/TQL/filter built;
- whether `assignee` is actually included in source request;
- whether space restriction can be included;
- pagination behavior.

Do not infer from Python signature alone.

## Phase 2 — live `search_tasks` experiments
Using only schema-valid arguments, execute controlled live REAL AS21 reads.

Required experiments:
1. assignee only = `Garanin.R.V`;
2. assignee + one approved space if tool supports it;
3. assignee + another approved space if supported;
4. if no explicit space argument exists, prove whether `search_terms` or another documented filter can safely constrain exact space without becoming fuzzy text search;
5. one negative control using another AUTHORITATIVE configured team member only, to prove assignee filtering changes the result.

For every experiment record:
- exact MCP arguments;
- exact AS21 endpoint/payload sent downstream;
- decoded task keys;
- decoded `space` values;
- decoded `assigned_to` values where available;
- pagination metadata;
- whether results actually satisfy requested assignee and scope.

A result is invalid if the tool accepts an `assignee` argument but source payload does not enforce it.

## Phase 3 — exact schema proof for `find_units_by_filter`
Capture its real MCP schema. Construct a VALID request including all required fields, especially `calculatedAttributes` if required.

Record exact supported request structure for:
- `attributes`;
- `calculatedAttributes`;
- `query` or TQL/filter;
- `page` / page number / page size;
- any space fields.

Inspect read-only implementation to determine the exact REAL AS21 endpoint and payload.

## Phase 4 — live `find_units_by_filter` experiments
Test whether source-side filtering can express BOTH:
- exact assignee `Garanin.R.V`;
- exact approved space, starting with DMS and OLP.

Prefer exact TQL/filter semantics, not fuzzy text search.

Required evidence:
1. exact valid request object;
2. exact downstream AS21 payload;
3. decoded returned task keys;
4. each task's space;
5. authoritative assignee field if bulk response exposes it;
6. if bulk response lacks assignee, point-read a sample plus all final candidate keys as necessary to prove the filter is genuinely correct;
7. pagination page 0 and page 1 if `hasNext=true`, proving whether page number can actually be changed through this tool.

Do not stop after a schema error. Fix the TEST REQUEST to conform to live schema; do not modify production code.

## Phase 5 — capability decision
Allowed verdicts only:

### `EXISTING_DIRECT_ROUTE_PROVEN`
At least one target tool provides a complete REAL AS21 route that enforces assignee + approved scope and supports complete pagination.

### `EXISTING_ROUTE_PARTIAL`
A target tool correctly enforces some required constraints but cannot provide complete scope/pagination/fields.

### `MCP_ASSIGNEE_GAP_RECONFIRMED`
Both `search_tasks` and correctly-invoked `find_units_by_filter` are conclusively unable to provide a complete assignee + approved-scope route.

### `BLOCKED_BY_ENVIRONMENT`
The schema supports a valid route, but live AS21 cannot be exercised after retries.

Do NOT certify Agent/Harness/UI in Assignment 124.

## Critical anti-shortcut rules
- `search_tasks` cannot be rejected without testing its `assignee` argument live and showing the downstream AS21 request.
- `find_units_by_filter` cannot be rejected because of a malformed QA request. It must be invoked with the exact required schema.
- Presence of unapproved spaces in results is not automatically a gap if exact post-source filtering is explicitly part of the tool contract; however, such filtering must remain independent of Harness and must allow COMPLETE pagination. Clearly distinguish source-side vs Oracle-side filtering.
- Counts alone are insufficient; capture exact task keys and space values.
- `hasNext=true` without exercising page 1 means completeness is NOT proven.

## Mandatory comparison table
For both tools include:
- tool name;
- exact schema;
- REAL AS21 endpoint;
- assignee source-side filter: YES/NO;
- exact-space source-side filter: YES/NO;
- returned task key: YES/NO;
- returned space: YES/NO;
- returned assigned_to: YES/NO;
- executable page 1+: YES/NO;
- complete Oracle usable: YES/NO;
- reason.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/ASSIGNEE_FILTER_ROUTE_FORENSIC_124.md`

Optional raw evidence prefix:
`ASSIGNEE_FILTER_ROUTE_FORENSIC_124_`

## Finish
Commit/push only QA report/evidence, provide full SHA, then STOP.

## Start when instructed
Execute Assignment 124 autonomously and narrowly. Do not modify production code. Do not synchronize/populate task data.