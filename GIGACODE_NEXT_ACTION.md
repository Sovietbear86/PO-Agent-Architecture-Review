# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_122_TRUE_AS21_ASSIGNEE_ORACLE`

## Context
Assignment 121 proved that Assignment 120 misparsed the FastMCP outer envelope. Current live `get_sprint_tasks(DMS-SPRNT-1)` decodes to 100 business rows, but sprint rows currently expose empty `unit.attributes`. A live point read via `read_unit` returns full attributes including `assigned_to`.

Therefore this assignment must establish current authoritative assignee truth directly from REAL AS21 without any local DB, synchronization, cache, Harness answer, historical answer, or surrogate Oracle.

## Role boundary
You are QA / forensic executor only. Do NOT modify production/backend/frontend code, prompts, skills, adapters, Task API, MCP-SWTR, team data, AS21 data, testing rules, or this file. Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`.

## Absolute prohibitions
- NO task synchronization/population utilities.
- NO local DB refresh/population.
- NO local DB/cache as truth or Oracle.
- NO fake/mock/frozen data.
- NO AS21 writes.
- NO historical task list/count as current Oracle.
- NO Harness/Agent as Oracle.
- NO invented team members or spaces outside the approved project scope.
- NO 54-skill marathon.
- NO production fixes.

## Goal
Build a TRUE current Oracle for the natural-language query `Задачи Гаранина` from live REAL AS21, then compare the exact same business question across:
A1 = Browser/UI path if executable without manual GUI automation; otherwise record `NOT_EXECUTED` and do not fake it.
A2 = Direct Harness API.
B = Independent REAL AS21 Oracle.

Primary truth is B.

## Phase 0 — provenance and health
1. Pull current `feat/core8-real-query-hardening-v2`; record exact HEAD and clean worktree.
2. Record MCP-SWTR tool count/transport and service PIDs for provenance.
3. Verify REAL AS21 point read using an existing DMS task.
4. Decode MCP envelopes exactly as proven in Assignment 121.
5. Retry temporary 5xx/timeouts up to 2 times with 20–30 sec backoff; timeout >=120 sec.

## Phase 1 — establish exact Garanin identity
Use only authoritative team/project configuration already present in the repository plus live AS21 user/task fields. Establish the exact allowed team identity for Rodion Garanin, expected login `Garanin.R.V` if confirmed by authoritative data/config.

Do not search for unrelated employees. Do not substitute Antonov or any other non-team member as control.

## Phase 2 — TRUE independent Oracle B
1. Call live MCP-SWTR `get_sprint_tasks` for `DMS-SPRNT-1`.
2. Correctly decode the FastMCP envelope and inner JSON.
3. Follow pagination until the complete current sprint task-key set is obtained. Do not assume the first 100 rows are complete when `hasNext=true`.
4. For EVERY task key returned for this sprint, call authoritative live `read_unit` (or exact current point-read equivalent if schema proves another name).
5. Decode each point-read response.
6. Extract current `assigned_to` from the returned attributes.
7. Select only tasks whose authoritative current assignee exactly matches Garanin's confirmed identity/login.
8. Record the exact resulting task-key set, count, sprint membership and assignee values.
9. No local DB or Task API data may participate in Oracle B.

This may be slow. Run sequentially/conservatively. Do not optimize by replacing point reads with historical or local data.

## Phase 3 — Direct Harness A2
After Oracle B is complete, submit exactly:
`Задачи Гаранина`
to the current Direct Harness API through the same production route used by the application backend.

Capture:
- status;
- resolved intent/skill;
- semantic assignee slot/identity;
- returned task count;
- exact returned task-key set;
- warnings/errors;
- elapsed time.

Do not teach, correct, seed, synchronize, or populate anything before this call.

## Phase 4 — Browser/UI A1
If the existing test environment provides a real executable Browser/UI request path, execute exactly `Задачи Гаранина` once and capture the response and task keys.

If CLI cannot truly execute the Browser/UI path, mark `A1_NOT_EXECUTED`. Do not simulate Browser UI with another Harness call and do not call it Browser evidence.

## Phase 5 — exact parity decision
Compare Oracle B vs A2, and A1 only if genuinely executed.

Primary invariant:
`exact set(task_keys_A) == exact set(task_keys_B)`

Counts alone are insufficient.

Allowed outcomes:
- `TRUE_AS21_PARITY_GREEN` only if current independent Oracle B is fully proven and A2 exact task-key set equals B; A1 may be separately NOT_EXECUTED if unavailable.
- `AGENT_ORACLE_MISMATCH_PROVEN` if B is proven and A2 differs.
- `ORACLE_INCOMPLETE` if pagination or any required point reads prevent proving the complete B set.
- `BLOCKED_BY_ENVIRONMENT` if REAL AS21 cannot be read after retries.

ZERO TASKS IS NEVER ACCEPTABLE merely because Harness returned zero. Zero is valid only if the complete independent point-read Oracle B also proves zero current Garanin tasks.

## Phase 6 — first failing boundary if mismatch
If A2 != B, trace only enough to identify the first failing boundary. Allowed labels:
- `SEMANTIC_INTERPRETATION`
- `ASSIGNEE_IDENTITY_GROUNDING`
- `SKILL_RESOLUTION`
- `CAPABILITY_ARGUMENT_BUILDING`
- `SOURCE_ROUTE`
- `SOURCE_RESPONSE_PARSING`
- `FILTERING`
- `RESPONSE_MAPPING`

Do not fix the defect in this assignment.

## Mandatory evidence
Report must include:
- exact current HEAD;
- complete sprint pagination evidence;
- number of sprint task keys point-read;
- number of successful/failed point reads;
- confirmed Garanin login/identity source;
- Oracle B exact Garanin task-key set;
- A2 exact task-key set;
- A1 exact task-key set or explicit NOT_EXECUTED;
- set differences `B-A2` and `A2-B`;
- statement confirming local DB/sync/cache/fake/mock/historical Oracle usage = 0;
- AS21 writes = 0.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/TRUE_AS21_ASSIGNEE_ORACLE_122.md`

Optional raw evidence prefix:
`TRUE_AS21_ASSIGNEE_ORACLE_122_`

## Finish
Commit/push only QA artifacts, provide full SHA, then STOP.

## Start when instructed
Execute Assignment 122 autonomously. Do not modify production code. Do not synchronize/populate local task data.