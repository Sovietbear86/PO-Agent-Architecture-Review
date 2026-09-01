# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_120_REPLAY_KNOWN_GOOD_GARANIN_ORACLE`

## Why Assignment 119 is not sufficient
Assignment 119 correctly refused GREEN, but it stopped too early and ignored a previously proven working Oracle pattern already present in repository evidence.

Historical authoritative anchor from `po-agent-platform-v2/qa_reports/AGENT_SEMANTIC_CONTEXT_LANGUAGE_FORENSIC_109.md`:
- REAL AS21 / MCP-SWTR Oracle for `DMS-SPRNT-1` returned 100 tasks;
- among them `Garanin.R.V` had exactly 10 tasks;
- exact historical task keys were:
  - `DMS-243`
  - `DMS-248`
  - `DMS-78`
  - `DMS-79`
  - `DMS-80`
  - `DMS-81`
  - `DMS-82`
  - `DMS-83`
  - `DMS-86`
  - `DMS-93`

This historical set is NOT automatically current truth. It is a known-good test recipe and regression anchor. You must re-read REAL AS21 now and prove the current task set independently.

Assignment 119 used `get_my_tasks(assignee=...)`, discovered that its assignee semantics were not trustworthy, and then gave up. Do NOT use `get_my_tasks` for this assignment.

## Role boundary
You are QA / forensic executor only.
Do NOT modify production/backend/frontend code, prompts, skills, adapters, Task API, MCP-SWTR, team data, AS21 data, testing rules, or this file.
Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`.

## Absolute prohibitions
- NO task synchronization/population utilities.
- NO local DB refresh/population.
- NO local DB/cache as Oracle.
- NO fake/mock/frozen data.
- NO AS21 writes.
- NO `get_my_tasks` as Oracle for Garanin.
- NO Harness/Agent/capability as Oracle.
- NO arbitrary users or spaces outside WMB/STS/OLP/DMS/CRPV.
- NO speculative production fix.
- NO GREEN from counts only.

## Goal
Reproduce the exact independent REAL-AS21 Oracle method that was effectively proven in Assignment 109: read the authoritative sprint membership for `DMS-SPRNT-1` directly from MCP-SWTR/REAL AS21, inspect raw assignee attributes on those rows, deterministically select only rows assigned to `Garanin.R.V`, and establish the current exact task-key set.

Only after Oracle B is proven, compare it with the Direct Harness natural-language query `Задачи Гаранина`.

This assignment intentionally does NOT require Browser automation. Browser parity will be a separate manual/user-visible step after Oracle truth is restored. Do not pretend a direct API call is Browser execution.

## Phase 0 — provenance and source health
1. Pull current `feat/core8-real-query-hardening-v2`; record exact HEAD and clean worktree.
2. Record PID/port/start time for Harness and Task API; record MCP-SWTR transport/tool count.
3. Verify one REAL point read in DMS via MCP-SWTR.
4. Verify the live schema for `get_sprint_tasks` / equivalent sprint-membership tool and use the exact documented parameter names. Do not guess.
5. If AS21 is temporarily unavailable, retry up to 2 times with 20–30 sec backoff; timeout >=120 sec.

## Phase 1 — reproduce the known-good Oracle recipe
Read `DMS-SPRNT-1` directly through MCP-SWTR → REAL AS21, not through Harness and not through local Task API list/cache.

Requirements:
- retrieve the complete sprint task collection, all pages if paginated;
- prove the sprint identity is exactly `DMS-SPRNT-1`;
- capture raw task code/key and raw `assigned_to` (or authoritative equivalent assignee attribute) for every row needed to determine Garanin membership;
- do not re-fetch through Harness/Agent;
- do not persist source rows.

Historical anchor: Assignment 109 observed 100 tasks in `DMS-SPRNT-1` and 10 assigned to `Garanin.R.V`. Current AS21 may differ; report both historical anchor and current live result.

## Phase 2 — current independent Garanin Oracle B
From the current live `DMS-SPRNT-1` source rows, deterministically filter in QA process memory for the exact authoritative identity `Garanin.R.V`.

Produce:
- complete current `DMS-SPRNT-1` task count;
- exact current Garanin task-key set;
- exact count;
- representative raw source evidence showing `assigned_to = Garanin.R.V` for at least 3 returned rows, if at least 3 exist;
- any historical keys from Assignment 109 that disappeared or changed assignee;
- any new Garanin keys not present in Assignment 109.

If current Oracle B returns zero, that zero is valid ONLY if you show the complete current sprint collection and prove no row has `assigned_to = Garanin.R.V`.

If you cannot retrieve complete sprint rows with assignee evidence, verdict is `ORACLE_RECIPE_BROKEN` — do not infer zero.

## Phase 3 — Direct Harness A2
With a fresh session execute exactly:
`Задачи Гаранина`

Capture:
- request URL/body/session;
- status;
- intent/skill;
- exact task-key set;
- count;
- elapsed;
- warnings.

Do NOT use Harness as Oracle.

## Phase 4 — exact comparison
Compare:
`Direct Harness A2 exact task-key set` vs `Independent Oracle B exact current task-key set`.

Allowed results:
- exact equality → `GARANIN_HARNESS_ORACLE_PARITY_GREEN`
- Oracle non-empty, Harness zero/different → `GARANIN_PRODUCT_MISMATCH_PROVEN`
- Oracle recipe cannot be reproduced → `ORACLE_RECIPE_BROKEN`
- environment unavailable after retries → `BLOCKED_BY_ENVIRONMENT`

If mismatch exists, trace only the first actual product boundary after semantic interpretation. Allowed labels:
- `ENTITY_GROUNDING`
- `CAPABILITY_ARGUMENT_BUILDING`
- `MEMBER_SEARCH_SOURCE_ROUTING`
- `TASK_API_LIVE_SOURCE_ROUTING`
- `MCP_TOOL_CONTRACT`
- `FILTER_APPLICATION`
- `RESPONSE_MAPPING`

## Phase 5 — explain why 119 failed while 109 worked
This is mandatory.
Compare the working Oracle approach/evidence from Assignment 109 with the failed approach from Assignment 119.
Determine whether 119:
- chose the wrong MCP tool;
- used wrong parameter semantics;
- failed to inspect sprint membership directly;
- encountered actual MCP tool/runtime drift;
- or whether AS21 data truly changed.

Do not attribute the difference to source data without raw current proof.

## Mandatory counters
- independent REAL AS21 sprint reads >= 1
- complete `DMS-SPRNT-1` enumeration = YES
- raw assignee evidence inspected = YES
- Direct Harness natural-language requests >= 1
- Harness/Agent used as Oracle = 0
- sync/population runs = 0
- local DB authoritative reads = 0
- fake/mock/frozen reads = 0
- AS21 writes = 0

## Output
Primary report:
`po-agent-platform-v2/qa_reports/REPLAY_KNOWN_GOOD_GARANIN_ORACLE_120.md`

Optional raw evidence prefix:
`REPLAY_KNOWN_GOOD_GARANIN_ORACLE_120_`

Allowed final verdicts only:
- `GARANIN_HARNESS_ORACLE_PARITY_GREEN`
- `GARANIN_PRODUCT_MISMATCH_PROVEN`
- `ORACLE_RECIPE_BROKEN`
- `BLOCKED_BY_ENVIRONMENT`

## Finish
Commit/push only QA artifacts, provide full SHA, then STOP.

## Start now
Execute Assignment 120 autonomously. Do not ask for confirmation. Do not modify production code. Do not synchronize or populate local task data.