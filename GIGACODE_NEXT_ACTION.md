# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_119_TRUE_GARANIN_ORACLE_PARITY`

## 118R is INVALID and must not be used as certification
Assignment 118R is rejected.

Reasons proven by its own report:
- Browser natural-language requests = 0 although Browser execution was mandatory.
- The candidate REAL AS21 Oracle tool was found not to apply the assignee filter correctly.
- Instead of obtaining an independent Oracle, the report substituted the Harness `task_search_assignee` skill as Oracle.
- Therefore Agent A and Oracle B were not independent.
- The report then declared `GARANIN_THREE_WAY_PARITY_GREEN` despite Browser being N/A and despite no independent Oracle proving the task-key set.
- A zero result from Agent/Harness must NEVER be treated as correct merely because the same Agent/Harness path also returns zero.

The owner states the real business fact that Garanin has tasks. Therefore a claimed authoritative zero result is a red flag that requires source proof, not a GREEN verdict.

## Non-negotiable testing law
A production GREEN is allowed only when ALL are true:
1. A1 = actual Browser UI natural-language execution.
2. A2 = actual Direct Harness execution of the same natural-language text.
3. B = independent REAL AS21 Oracle that does NOT use Harness, Agent skills, Agent capabilities, Agent filtering, local DB, cache, fake/mock/frozen data, or output from A1/A2.
4. Exact business facts match. For task collections, exact task-key sets must match.
5. All evidence is from the same exact HEAD/runtime provenance.

If independent Oracle B cannot be established, verdict MUST be `ORACLE_NOT_PROVEN` or `BLOCKED_BY_ENVIRONMENT`. GREEN is forbidden.

## Role boundary
You are QA / forensic executor only.
Do NOT modify production/backend/frontend code, prompts, skills, adapters, Task API, MCP-SWTR, schemas, team data, testing rules, AS21 data, or this file.
Commit/push only QA evidence under `po-agent-platform-v2/qa_reports/`.

## Absolute prohibitions
- NO task synchronization/population utilities.
- NO local DB refresh/population.
- NO local DB/cache as Oracle or truth source.
- NO fake/mock/frozen data.
- NO AS21 writes.
- NO Harness/Agent skill/capability as Oracle B.
- NO arbitrary users outside repository team data.
- NO positive task evidence outside WMB/STS/OLP/DMS/CRPV.
- NO invented sprint.
- NO replacement of Browser execution with a direct API statement such as "same contract applies".
- NO GREEN when any mandatory counter is below threshold.

If any sync/local-population action is attempted, STOP that action immediately and record it as prohibited; do not use its result.

## Goal
Establish the TRUE authoritative REAL AS21 task set for repository team member `Garanin.R.V` within owner-approved spaces WMB, STS, OLP, DMS, CRPV, then compare that exact set against the real Browser UI and Direct Harness result for the exact text:

`Задачи Гаранина`

This assignment is intentionally narrow. Do not run the 54-skill marathon yet.

## Phase 0 — exact provenance and health gate
1. Pull current remote `feat/core8-real-query-hardening-v2` and record exact HEAD.
2. Record clean worktree.
3. Record PID/port/command/start time for Frontend, Harness and Task API.
4. Verify MCP-SWTR live health.
5. Perform at least one direct REAL AS21 point read in DMS and one in OLP through MCP-SWTR.
6. For each point read capture raw source fields including task key, space, sprint when present, workflow status and `assigned_to`/member identity when present.
7. If AS21/MCP is temporarily unavailable or returns transport 5xx/timeout, retry up to 2 times with 20–30 sec backoff; timeout >=120 sec, heavy reads up to 180 sec.
8. Do not continue to parity if the source-health gate is not trustworthy.

## Phase 1 — discover the authoritative team identity
Read the repository authoritative team data file(s) only.
Record the exact entry for Rodion Garanin, including supported login/identifier, expected products/spaces and any aliases used by the product.

Subject for this assignment must remain `Garanin.R.V` / Rodion Garanin. Do not choose a different person because it is easier to query.

## Phase 2 — build a TRUE independent Oracle B
Do NOT assume any MCP member-search tool filters correctly.

### 2A. Inspect live MCP tools
Inspect the live schema/description of all plausible read/search tools that can retrieve tasks by:
- assignee/user/member,
- sprint,
- space/project,
- task collection/list/search.

Record exact tool names and relevant input fields.

### 2B. Prove filter semantics before trusting a tool
For every candidate assignee search tool:
- execute it for `Garanin.R.V`;
- inspect raw returned rows and their real `assigned_to` attributes;
- verify rows actually belong to Garanin;
- verify rows belong only to WMB/STS/OLP/DMS/CRPV or apply deterministic QA-only scope filtering after reading the source rows;
- verify pagination/completeness.

If a tool returns unrelated tasks, identical results for different assignees, ignores the assignee argument, or does not expose enough source data to validate identity, that tool is INVALID as Oracle.

### 2C. Fallback independent Oracle construction
If no single MCP tool supports a trustworthy server-side assignee filter, construct Oracle B independently by live READ-ONLY source enumeration:
- retrieve REAL AS21 task collections from the approved spaces only: WMB, STS, OLP, DMS, CRPV;
- use the live MCP-SWTR/AS21 path directly, never Harness/Task API local list;
- inspect the authoritative `assigned_to`/identity attributes in the REAL source response;
- deterministically filter in QA process memory only for `Garanin.R.V`;
- do not persist results and do not populate any database;
- read every page required for completeness.

For sprint-based evidence, explicitly inspect at least:
- `DMS-SPRNT-1`
- `DMS-SPRNT-2`
- `OLP-SPRNT-5`
where source access permits, because these are approved reference sprints for this project.

### 2D. Oracle proof output
Oracle B is valid only if the report contains:
- exact REAL MCP tool(s)/endpoint(s) used;
- exact identity value used for Garanin;
- pagination/completeness evidence;
- raw source evidence proving assignee identity for representative returned tasks;
- exact authoritative task-key set;
- exact count;
- per-space and, where available, per-sprint breakdown;
- zero use of Harness/Agent/local DB.

If Oracle B cannot prove a non-empty or empty set independently, STOP with `ORACLE_NOT_PROVEN`. Do not infer zero from Agent output.

## Phase 3 — actual Browser A1
Using a fresh Browser UI session, enter exactly:
`Задачи Гаранина`

Capture:
- Browser Network URL and method;
- request body;
- session ID/header;
- actual response;
- semantic intent/skill if exposed;
- task keys returned;
- count;
- user-facing text;
- elapsed time.

This must be an actual browser-generated request. A direct API call is not a substitute.

Browser request counter must be >=1.

## Phase 4 — Direct Harness A2
Using a different fresh session, send exactly:
`Задачи Гаранина`
through the exact Harness endpoint used by Browser.

Capture request/response, intent, skill, task keys, count, warnings and elapsed time.

Do not use A2 as Oracle.

## Phase 5 — exact three-way decision
Create an explicit table:

| Path | Independent? | Source reached | Exact task keys | Count | Elapsed | Verdict |
|---|---|---|---|---:|---:|---|
| Browser A1 | product path | ... | ... | ... | ... | ... |
| Harness A2 | product path | ... | ... | ... | ... | ... |
| Oracle B | YES | REAL AS21 | ... | ... | ... | ... |

Primary assertion:
`Browser A1 task-key set == Harness A2 task-key set == independent Oracle B task-key set`.

Counts are secondary and cannot establish parity by themselves.

If Oracle B proves tasks but Browser/Harness returns 0, verdict must be a product defect and the first failing boundary must be traced.

## Phase 6 — first failing boundary if mismatch exists
Only if A1/A2 differ from Oracle B, trace the earliest actual product boundary exercised by the request. Allowed labels:
- `UI_REQUEST_CONTRACT`
- `HARNESS_SEMANTIC_INTERPRETATION`
- `ENTITY_GROUNDING`
- `CAPABILITY_ARGUMENT_BUILDING`
- `MEMBER_SEARCH_SOURCE_ROUTING`
- `TASK_API_LIVE_SOURCE_ROUTING`
- `MCP_TOOL_CONTRACT`
- `RESPONSE_MAPPING`
- `FILTER_APPLICATION`

Do not jump to assignee extraction/local synchronization unless the actual live trace proves that is the exercised failing boundary.

## Phase 7 — anti-surrogate certification audit
Before final verdict mechanically verify:
- Browser requests >= 1
- Direct Harness requests >= 1
- independent REAL AS21 Oracle reads >= 1
- Oracle uses Harness/Agent = 0
- sync/population runs = 0
- local DB authoritative reads = 0
- fake/mock/frozen reads = 0
- AS21 writes = 0
- exact task-key-set comparison performed = YES

If any required condition fails, GREEN is structurally forbidden.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/TRUE_GARANIN_ORACLE_PARITY_119.md`

Optional raw evidence prefix:
`TRUE_GARANIN_ORACLE_PARITY_119_`

Allowed final verdicts only:
- `GARANIN_TRUE_THREE_WAY_PARITY_GREEN`
- `GARANIN_PRODUCT_MISMATCH_PROVEN`
- `ORACLE_NOT_PROVEN`
- `BLOCKED_BY_ENVIRONMENT`

Do NOT use `GREEN` in any other verdict.

## Finish
Commit/push only QA artifacts, provide full SHA and STOP.

## Start now
Execute Assignment 119 autonomously. Do not ask for confirmation between phases. Do not change production code. Do not synchronize or populate task data.