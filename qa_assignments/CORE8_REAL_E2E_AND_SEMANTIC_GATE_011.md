# QA Assignment: CORE8-REAL-E2E-AND-SEMANTIC-GATE-011

## Purpose
Continue immediately after `AS21_A3_ATTACHMENT_CANONICAL_RETEST_010` (GREEN). We now validate the Core-8 on REAL AS21 data through the production PO Agent path, while fixing the semantic-query entrypoint revealed by the manual test.

## Important finding from manual test
The real natural-language query:

`Найди открытые задачи Гончарова в актуальном спринте по OLAP`

produced two different outcomes:
- `/api/v1/query` -> `semantic_interpretation_failure`
- direct adapter/Python path -> SUCCESS, 6 real OLP tasks found in `OLP-SPRNT-5`

This means AS21 retrieval is NOT the blocker. The blocker is the semantic interpretation / query orchestration path. Do NOT work around this by teaching tests to call the adapter directly. The production agent must understand this request through `/api/v1/query`.

Also: do NOT conclude that the only acceptable production fix is simply `llm_api_key` in `.env`. First inspect the original application/agent architecture and current code/config. Determine the intended semantic interpreter/provider contract. If an LLM provider is required, wire it through the existing configuration contract without hardcoding secrets, and fail explicitly when unavailable. If deterministic parsing already supports this query class, use it as a safe fallback where architecturally appropriate. Never silently convert semantic failure into an unfiltered AS21 query.

## Phase 0 — Promote proven source capabilities
A3 real QA proved attachment metadata. Update source capability advertisement only if the architecture uses `source_facts` as the capability gate:
- `tasks` remains proven
- `attachments` may now be marked proven

Do not advertise capabilities not proven on real AS21.

## Phase 1 — Pagination before analytics
The previous report returned 100 sprint tasks and explicitly indicated pagination. Implement/verify complete sprint traversal until the source indicates no next page (`hasNext=false` or equivalent source contract).

Requirements:
1. No hard-coded assumption that 100 == full sprint.
2. Deduplicate by canonical task/source id across pages.
3. Preserve sprint/project/status/assignee filtering.
4. Add loop-safety/max-page protection with explicit error, not silent truncation.
5. Report both page count and total unique tasks for DMS and OLP.

Run against real current sprint sources for DMS and OLP.

## Phase 2 — Semantic production-path gate
Reproduce the exact manual request through the real agent endpoint:

`Найди открытые задачи Гончарова в актуальном спринте по OLAP`

Expected semantic plan must resolve at least:
- domain/project/space: OLP/OLAP
- assignee: Гончаров (resolved to the real team member identity/login from the team roster/source data; do not hardcode a guessed login)
- sprint: current/active sprint
- status: open/non-done according to canonical status semantics

Acceptance:
- `/api/v1/query` succeeds.
- Result is grounded in AS21 through MCP-SWTR SSE, not fixtures/mocks.
- Result set equals the independently computed direct-adapter/source result for the same predicates.
- No broadening: removing any failed predicate is forbidden.
- Include keys and titles in report.
- If the six-task result seen in the manual test is still source-current, it should reconcile with those six; if source data changed, explain the delta using live evidence rather than forcing count=6.

Add adversarial variants:
1. `Покажи открытые задачи Гончарова в текущем спринте OLP`
2. `Какие незакрытые задачи у Гончарова в текущем спринте OLAP?`
3. `Найди задачи Гончарова в актуальном спринте по OLAP`
4. nonexistent assignee -> empty, never all sprint tasks
5. nonexistent space -> empty/error capability, never cross-space results

## Phase 3 — Core-8 REAL E2E
Run the previously defined Core-8 through the production Harness/agent boundary, not only unit-level Python calls:

1. `task_search`
2. `task_summary`
3. `task_quality`
4. `sprint_health`
5. `velocity`
6. `team_workload`
7. `competency_match`
8. `release_health`

For every skill report:
- exact natural-language input
- semantic interpretation / structured plan
- source calls used
- canonical entities/attributes used
- final answer/result
- independent oracle/reconciliation method
- PASS/FAIL and reason

Use real AS21 data. For sprint/team analytics use the repository team roster and the DMS/OLP spaces agreed for team discovery. Do not invent members or competencies.

### Core-8 acceptance principles
- Search predicates must be conjunctive when user asks A AND B AND C.
- Assignee identity must work via canonical id/login/name mapping.
- Current sprint must be resolved from source sprint metadata, not a hard-coded sprint id.
- Analytics must consume ALL paginated sprint tasks.
- Attachment-dependent behavior must use canonical attachment metadata proven in A3.
- Missing source evidence must produce explicit `unknown/unavailable`, never fabricated values.
- A direct adapter success does NOT count as production E2E success if `/api/v1/query` fails.

## Phase 4 — Regression / false-green attacks
Run existing regression plus targeted attacks:
- unknown semantic field
- nonexistent assignee
- nonexistent sprint
- nonexistent project/space
- conflicting predicates
- semantic interpreter unavailable
- MCP-SWTR unavailable
- pagination interrupted mid-stream

The system must fail closed or return explicit partial/unavailable status. It must never broaden the result silently.

## Learning-loop gate
DO NOT start or modify the learning loop in this assignment.

Set `READY_FOR_LEARNING_LOOP=YES` only when:
- semantic production path is GREEN
- pagination is GREEN
- Core-8 = 8/8 GREEN on real AS21
- no new code regressions vs current baseline
- no false-green path found

Otherwise keep it `NO` and identify blockers.

## Required report
Publish:
`qa_reports/CORE8_REAL_E2E_AND_SEMANTIC_GATE_011.md`

Machine-readable footer must include:

```text
ASSIGNMENT_ID = CORE8-REAL-E2E-AND-SEMANTIC-GATE-011
MCP_SWTR_CONNECTED = YES|NO
SEMANTIC_QUERY_PATH = GREEN|YELLOW|RED
SEMANTIC_PROVIDER_REQUIRED = YES|NO|UNKNOWN
SEMANTIC_PROVIDER_CONFIGURED = YES|NO|N/A
MANUAL_GONCHAROV_QUERY = PASS|FAIL
MANUAL_GONCHAROV_RESULT_COUNT = <n>
MANUAL_QUERY_DIRECT_ORACLE_MATCH = YES|NO
DMS_PAGINATION_COMPLETE = YES|NO
DMS_SPRINT_PAGE_COUNT = <n>
DMS_SPRINT_UNIQUE_TASK_COUNT = <n>
OLP_PAGINATION_COMPLETE = YES|NO
OLP_SPRINT_PAGE_COUNT = <n>
OLP_SPRINT_UNIQUE_TASK_COUNT = <n>
CORE8_TASK_SEARCH = PASS|FAIL
CORE8_TASK_SUMMARY = PASS|FAIL
CORE8_TASK_QUALITY = PASS|FAIL
CORE8_SPRINT_HEALTH = PASS|FAIL
CORE8_VELOCITY = PASS|FAIL
CORE8_TEAM_WORKLOAD = PASS|FAIL
CORE8_COMPETENCY_MATCH = PASS|FAIL
CORE8_RELEASE_HEALTH = PASS|FAIL
CORE8_GREEN_COUNT = <0..8>
FALSE_GREEN_PATH_FOUND = YES|NO
NEW_CODE_REGRESSIONS_VS_BASE = <n>
BLOCKER_COUNT = <n>
READY_FOR_LEARNING_LOOP = YES|NO
```

## Stop condition
If a real source/provider credential or endpoint is genuinely unavailable, do not fake the test and do not commit secrets. Document the exact missing configuration key/provider contract and continue every test that can still be run safely. Publish the report with the appropriate YELLOW/RED gate.