# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_126_TRUE_ORACLE_ASSIGNEE_PARITY`

## Context
Assignment 125 materially changes the situation. A REAL AS21 independent assignee Oracle route now exists using current MCP-SWTR tools:

`search_users -> externalId -> find_units_by_filter(assigned_to = externalId) -> complete pagination -> Oracle-side exact product/space filtering`

Assignment 125 proved for `Garanin.R.V`:
- 15 REAL AS21 tasks assigned to Garanin across returned spaces;
- DMS = 7 exact tasks;
- OLP = 3 exact tasks;
- STS = 5 tasks outside the configured Garanin product scope;
- configured Garanin scope = DMS + OLP;
- therefore authoritative expected in-scope result for generic `Задачи Гаранина` is 10 tasks if the Agent contract means configured product scope.

Previous GREEN conclusions based on zero tasks are invalid and must not be reused as truth.

## Role boundary
You are QA / forensic executor only. Do NOT modify production/backend/frontend code, Task API, MCP-SWTR, Harness, prompts, skills, adapters, team data, AS21 data, testing rules, or this file. Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`.

## Absolute prohibitions
- NO local DB/sync/cache as truth.
- NO sync scripts or DB population.
- NO fake/mock/frozen/historical data as current truth.
- NO AS21 writes.
- NO Harness/Agent answer as Oracle.
- NO zero-result acceptance without independent Oracle equality.
- NO production fixes.
- NO 54-skill regression yet.
- Do not invent source limitations already disproven by Assignment 125.

## Goal
Use the newly proven REAL AS21 Oracle route to perform the first trustworthy A/B parity test for assignee search and identify the exact first failing boundary if the Agent disagrees.

A = production Agent/Harness under test.
B = independent REAL AS21 Oracle built only from the Assignment 125 route.

## Phase 0 — provenance and health
1. Pull current branch; record exact HEAD and clean worktree.
2. Restart Harness/Task API from current HEAD if needed so A is definitely current code.
3. Record PIDs/start times and REAL AS21/MCP health.
4. Confirm local DB/sync/cache/fake/mock/frozen Oracle usage = 0; AS21 writes = 0.
5. Confirm configured identity and product scope for Garanin from authoritative repo config.

## Phase 1 — rebuild Oracle B from scratch
Do NOT copy counts from Assignment 125 as test output. Re-execute the route live:
1. `search_users` -> uniquely resolve Garanin -> externalId.
2. `find_units_by_filter(query='assigned_to = "<externalId>"')`.
3. Traverse every page until `hasNext=false`.
4. Capture every returned task key, space and assigned_to.
5. Apply configured product/space scope independently in QA logic only after the REAL AS21 result is complete.

Produce exact normalized sets:
- `B_ALL_ASSIGNED_KEYS`
- `B_DMS_KEYS`
- `B_OLP_KEYS`
- `B_IN_SCOPE_KEYS = DMS ∪ OLP`
- `B_OUT_OF_SCOPE_KEYS`

Counts alone are insufficient.

## Phase 2 — Agent A generic assignee query
In a NEW session execute exactly the natural user query:
`Задачи Гаранина`

Capture:
- status;
- intent/skill/version;
- semantic frame/slots;
- resolved member identity;
- configured scope passed downstream;
- capability/tool arguments;
- source/evidence IDs;
- exact returned task keys;
- answer text;
- elapsed time.

Normalize to `A_GENERIC_KEYS`.

Primary parity criterion:
`A_GENERIC_KEYS == B_IN_SCOPE_KEYS`

If the Agent contract explicitly proves a different intended scope, document the contract and compare against that exact independently derived Oracle subset. Do not silently redefine scope to make A pass.

## Phase 3 — explicit DMS and OLP A/B tests
Use NEW independent sessions.

A-DMS query:
`Задачи Гаранина в DMS`
Expected Oracle:
`B_DMS_KEYS`

A-OLP query:
`Задачи Гаранина в OLP`
Expected Oracle:
`B_OLP_KEYS`

For each capture exact task-key equality, not counts only.

## Phase 4 — negative control
Choose one OTHER authoritative configured team member from repo config.
Rebuild Oracle B for that member using the same REAL route:
`search_users -> externalId -> find_units_by_filter -> complete pagination -> configured scope filter`

Then query Agent A naturally for that member.

Purpose: prove there is no Garanin-specific hardcoding and that identity resolution/filtering changes the result.

Do not use arbitrary/non-team employees.

## Phase 5 — exact first failing boundary
For every mismatch, trace evidence and assign the earliest applicable label only:
- `SEMANTIC_INTERPRETATION`
- `MEMBER_IDENTITY_RESOLUTION`
- `SCOPE_RESOLUTION`
- `SKILL_RESOLUTION`
- `CAPABILITY_ARGUMENT_BUILDING`
- `TASK_API_ADAPTER`
- `MCP_TOOL_SELECTION`
- `SOURCE_QUERY_CONSTRUCTION`
- `SOURCE_RESPONSE_DECODING`
- `POST_SOURCE_SCOPE_FILTERING`
- `RESPONSE_STATUS_MAPPING`
- `RESPONSE_RENDERING`

Show the last correct artifact and first incorrect artifact. Do not guess root cause from final count.

## Phase 6 — old surrogate verdict invalidation
Explicitly identify earlier QA reports that certified `0 tasks` for Garanin as GREEN or used an unproven Oracle route.

Do not edit/delete old reports. Mark them in Assignment 126 as superseded by the REAL Oracle proof from 125/126.

At minimum review Assignments 118R, 119, 120, 122 and any later report that reused their zero-task conclusion.

## Phase 7 — anti-surrogate certification
The report must answer YES/NO with evidence:
- Oracle B is independent of Agent/Harness: YES required.
- Oracle B uses live REAL AS21 reads: YES required.
- Exact task keys captured: YES required.
- Complete pagination proven: YES required.
- No local DB/sync/cache/fake/mock/frozen truth: YES required.
- No historical count copied as current Oracle: YES required.
- Agent result compared by exact set equality: YES required.

If any required answer is NO, GREEN is structurally forbidden.

## Allowed verdicts
### `TRUE_AB_PARITY_GREEN`
Generic + DMS + OLP + negative-control Agent results exactly equal independently rebuilt REAL AS21 Oracle sets.

### `AGENT_ASSIGNEE_REGRESSION_PROVEN`
Oracle is complete and independent, and at least one Agent result differs. Include first failing boundary.

### `MIXED_AGENT_AND_QA_DEFECTS`
A product mismatch exists and additional QA methodology/report defects are proven.

### `BLOCKED_BY_ENVIRONMENT`
A contractually valid live route cannot complete after retries.

No other GREEN verdict is allowed.

## Critical rules
- HTTP 200 / COMPLETED is NOT success without exact key parity.
- `0 tasks` is NOT success unless Oracle B independently returns the same empty set.
- Do not use `get_my_tasks` as Oracle for another assignee.
- Do not use `search_tasks` as assignee Oracle; Assignment 124 proved its assignee argument is not enforced.
- Do not use `get_sprint_tasks` alone as assignee Oracle.
- Space filtering in Oracle B may be QA-side ONLY after complete server-side assignee retrieval; record this explicitly.
- Do not fix anything in this assignment.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/TRUE_ORACLE_ASSIGNEE_PARITY_126.md`

Optional raw evidence prefix:
`TRUE_ORACLE_ASSIGNEE_PARITY_126_`

## Finish
Commit/push only QA report/evidence, provide full SHA, then STOP.

## Start when instructed
Execute Assignment 126 autonomously. No production changes and no synchronization/population.