# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_116_GARANIN_DIRECT_AS21_RETEST`

## Context
The branch has been rolled back to the last commit before 18:00 Moscow time on 2026-09-01: `0b3b3dc1f00618e0943360d8ec2c5454dad17a4a` (17:56:21 MSK). Do not reintroduce later product changes.

Assignment 116 is intentionally narrow. Reproduce the owner-observed mismatch for the canonical query `Задачи Гаранина` using REAL AS21 directly, with NO task synchronization and NO local task DB population.

The previous 110C report is not accepted as Agent A certification because its own counters show `Agent A requests = 0` despite a GREEN verdict.

## Role boundary
QA/test executor only. Do not modify production/backend/frontend code, prompts, skills, semantic logic, learning loop, Task API, MCP-SWTR, schemas, AS21 data, testing rules, or this file. Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`.

## Absolute prohibitions
DO NOT:
- run `sync_all_tasks.py`, `sync_sprint_tasks.py`, `sse_sync.py`, `swtr_sync.py` or any synchronization/population utility;
- create a synchronization script;
- populate or refresh a local task database;
- use local DB/cache as Oracle or authoritative task truth;
- change assignee extraction or source parsing;
- use fake/mock/frozen data;
- write to AS21.

If the normal production path itself routes to a local DB, prove that as a product routing defect. Do NOT populate that DB to make the test pass.

## Required paths
Agent A:
`actual Russian natural-language request -> exact Harness endpoint used by Browser UI -> normal Task API/source adapter -> MCP-SWTR -> REAL AS21`

Oracle B:
`independent direct MCP-SWTR read -> REAL AS21`

Browser UI control:
`Browser UI -> actual frontend route/proxy -> same Harness runtime`

## Phase 0 — rollback and runtime provenance
1. Fetch remote and align local branch with remote `feat/core8-real-query-hardening-v2`.
2. Record exact HEAD. Prove `0b3b3dc1f00618e0943360d8ec2c5454dad17a4a` is the rollback baseline; the only later commit should be this QA instruction.
3. Clean worktree before execution.
4. Restart only the services required for normal product query flow. Do not run any sync/population process.
5. Record PID, port, command and start time for Frontend, Harness, Task API and MCP-SWTR.
6. Prove direct MCP-SWTR -> REAL AS21 connectivity with a live read. If temporarily unavailable: timeout >=120 s, max 2 retries, 20–30 s backoff.

## Phase 1 — independent Oracle truth for Garanin
Using only direct MCP-SWTR/REAL AS21 reads, establish the current authoritative result for Rodion Garanin / `Garanin.R.V`:
- identity representation(s) used by source;
- exact current task-key set assigned to him;
- space/status for each task where available;
- exact count.

No local DB and no Harness output may be used to derive Oracle B.

## Phase 2 — exact three-way same-query test
Use the exact text:
`Задачи Гаранина`

Execute three paths:
A1. Browser UI with a fresh UI session.
A2. Direct request to the exact Harness endpoint that Browser UI calls, with a fresh session ID.
B. Independent Oracle B direct REAL AS21 request.

For A1/A2 record:
- browser page URL;
- actual network request URL/method/body;
- frontend proxy target if present;
- Harness endpoint and PID;
- session ID;
- downstream Task API endpoint/PID actually contacted;
- MCP-SWTR path actually contacted;
- response status;
- skill/version;
- semantic member/frame/slots;
- capability arguments;
- evidence/trace;
- exact returned task-key set;
- elapsed time.

For B record exact source request evidence and exact task-key set.

Primary assertion:
`Browser keys == Direct Harness keys == Oracle B keys`

Counts alone are insufficient.

## Phase 3 — repeatability and contamination check
Repeat the same exact `Задачи Гаранина` query:
1. fresh UI session with the PO Agent UI session/localStorage cleared;
2. another fresh session;
3. same persistent UI session after one unrelated harmless query.

Repeat corresponding direct-Harness controls with fresh session IDs.

The query contains no sprint. The Agent must not invent `SPRNT-2`, `DMS-SPRNT-2` or any other sprint.
All user-facing prose must be Russian.

## Phase 4 — one narrow member control
Select exactly one additional REAL team member for whom Oracle B independently proves a non-empty task set. Run the same Browser / Direct Harness / Oracle comparison.

Do not expand into a member matrix or full regression.

## Phase 5 — forensic only if mismatch exists
If Browser/Direct Harness differs from Oracle B, identify the earliest boundary without changing code.

Allowed classifications:
- `UI_PROXY_ROUTE_MISMATCH`
- `HARNESS_ENDPOINT_MISMATCH`
- `STALE_RUNTIME_PROCESS`
- `SESSION_CONTEXT_CONTAMINATION`
- `SEMANTIC_MEMBER_GROUNDING`
- `CAPABILITY_ARGUMENT_BUILDING`
- `TASK_API_SOURCE_ROUTING`
- `LOCAL_DB_ROUTE_USED_IN_PRODUCTION_PATH`
- `MCP_SWTR_SOURCE_CONTRACT`
- `RESPONSE_MAPPING`

If you discover local DB use in the normal Agent path, STOP the root-cause chain there after proving it. Do not synchronize/populate it.

## Mandatory execution counters
Report actual counts for:
- Browser UI natural-language requests;
- Direct Harness natural-language requests;
- Oracle B REAL AS21 reads;
- retries/timeouts;
- local DB authoritative reads;
- sync/population runs;
- fake/mock/frozen reads;
- AS21 writes.

A GREEN verdict is invalid if Browser requests = 0, Direct Harness requests = 0, or Oracle B reads = 0.
Required: sync/population runs = 0, fake/mock/frozen = 0, AS21 writes = 0.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/GARANIN_DIRECT_AS21_RETEST_116.md`

Optional evidence prefix:
`GARANIN_DIRECT_AS21_RETEST_116_`

Allowed verdicts:
- `GARANIN_THREE_WAY_PARITY_GREEN`
- `UI_HARNESS_ROUTE_MISMATCH_PROVEN`
- `SOURCE_ROUTING_DEFECT_PROVEN`
- `MEMBER_GROUNDING_DEFECT_PROVEN`
- `SESSION_CONTAMINATION_DEFECT_PROVEN`
- `MIXED_ROUTING_AND_MEMBER_DEFECTS`
- `BLOCKED_BY_ENVIRONMENT`

Commit/push only QA artifacts, report full SHA, then STOP.

## Start now
Execute Assignment 116 autonomously. Do not ask for permission between phases. Under no circumstances run synchronization or local task DB population.