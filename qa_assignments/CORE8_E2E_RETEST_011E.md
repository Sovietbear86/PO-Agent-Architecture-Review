# QA Assignment: CORE8 E2E RETEST 011E

## Role
GigaCode is **tester/reviewer only**. Do not modify production code, tests, config, prompts, or fixtures. Report defects with evidence; developer fixes are done separately.

## Goal
Retest the remaining 011D blockers after the developer fixes and establish whether the production PO Agent can now execute Core-8 against real AS21 data.

## Required developer commits to validate
At minimum verify the branch contains these changes:
- `5edca17` resilient Qwen/OpenAI-compatible JSON extraction and blind semantic fallback
- `d27fd36` resilient semantic wrappers wired into runtime
- `3add096` deterministic MCP alias selection and safer MCP error classification
- `6c563c2` complete sprint-read semantics + deterministic version arguments
- `8b05b2e` real team identities/competencies restored in canonical YAML
- `057b592` production Task API AS21 adapter with sprint/release source facts
- `9a7c64b` current-sprint wording guard
- `096c394` production runtime uses live adapter + live grounder

Also retain previously validated fixes for slashless Task API routes and attachments.

## Mandatory environment reset
1. Pull/fetch current branch and record HEAD.
2. Stop old Task API and PO Agent processes.
3. Start Task API from current HEAD on `:8003`.
4. Start PO Agent from current HEAD on `:8004` using the existing real/task-api mode and existing LLM configuration. Never print secrets.
5. Prove both OpenAPI/health endpoints belong to current HEAD before testing.

A stale process invalidates the report.

## Test A — Canonical route regression
Verify:
- `GET /api/v1/tasks?limit=1` -> 200, no redirect
- `GET /api/v1/tasks/?limit=1` -> 404, no redirect
- `WMB-30000` remains readable
- exactly 5 real XLSX attachments remain visible

## Test B — Real team grounding
The production runtime must use the restored real team directory, not anonymized identities.

Prove at least:
- `Гончаров Александр Олегович` -> `Goncharov.A.O`
- `Калачанов Виктор Вячеславович` -> `Kalachanov.V.V`
- Goncharov product includes OLP
- competency source for Goncharov includes Java and OLAP

Do not count reading YAML alone as E2E success; this test only proves grounding/config input.

## Test C — Current sprint grounding
Use live AS21:
- OLP current sprint must resolve from `/api/v1/swtr-read/spaces/OLP/current-sprint`
- DMS current sprint must resolve likewise
- relative wording `текущий/актуальный спринт` must resolve to the live source ID when the product is explicit

Primary user query:
`Найди открытые задачи Гончарова в актуальном спринте по OLAP`

Required structured predicates after interpretation/grounding:
- product/space = OLP
- assignee = Goncharov.A.O
- sprint = current live OLP sprint
- open/non-completed status semantics must be explicit and must not silently broaden

If the learned/open-status rule is not configured, a clarification for what counts as open is acceptable; `semantic_interpretation_failure` is not.

## Test D — Sprint completeness
Call:
`GET /api/v1/swtr-read/sprints/<OLP_CURRENT_SPRINT>/tasks?complete=true`

Two valid completeness modes exist:
1. MCP supports page/offset: all pages are traversed to `hasNext=false`; OR
2. MCP schema exposes only `sprint_id` despite `hasNext=true`: response explicitly uses `completeness_source=task-api-canonical-cache`, returns `complete_tasks`, and reconciles live first-page IDs against the canonical SWTR cache.

For mode 2 require:
- `complete=true`
- `live_first_page_reconciled=true`
- every returned canonical row has the requested sprint ID
- no duplicate task/source IDs
- complete count >= live first-page count

Do not mark pagination incomplete merely because the upstream MCP tool itself has no page input; judge the explicit completeness contract above.

## Test E — Release/version source
Call real endpoint with one argument at a time first:
- `/api/v1/swtr-read/versions?space=WMB`
- `/api/v1/swtr-read/versions?space=DMS`
- `/api/v1/swtr-read/versions?space=OLP`

The facade must send at most one alias for each semantic argument (not query+q+search+text simultaneously).

If 200 is returned, identify at least one real version/release and then find real tasks with matching `fix_version_s` where available. Record exact version ID/name/space and task IDs.

If an endpoint fails, report:
- HTTP status
- safe error detail (exception class only, no credentials/payload secrets)
- live MCP `search_versions` input schema
- exact argument names the facade sent

## Test F — Semantic layer, exact production `/api/v1/query`
Run all of these through the real PO Agent API, not direct adapter calls:
1. `Покажи задачу WMB-30000`
2. `Оцени качество постановки WMB-30000`
3. `Какой текущий спринт OLP?`
4. `Найди открытые задачи Гончарова в актуальном спринте по OLAP`
5. `Какая нагрузка у Калачанова?`
6. `Подбери исполнителя для WMB-30000 по компетенциям`
7. one release-health query using the real release discovered in Test E
8. one task-summary query for WMB-30000

Expected semantic behavior:
- no blanket `semantic_interpretation_failure`
- JSON wrapped in markdown, Qwen reasoning text, or `<think>...</think>` must still be safely parsed if a valid JSON object is present
- unsupported requests still fail closed
- provider rejection of `json_schema` must fall back without disabling closed-set validation

If any semantic query still fails, run a diagnostic script against the existing interpreter/client **without changing code** and report only:
- which stage failed: `initial_completion`, `initial_json_parse`, `catalog_resolution`, `entailment`, `blind_domain`, `blind_capability`, `grounding`, or `execution`
- whether the model returned parseable JSON
- returned intent label if non-secret
Do not publish full prompts, tokens, credentials, or sensitive source payloads.

## Test G — Core-8 production E2E
Evaluate exactly these eight authoritative skills through the production user-facing path:
1. task_search
2. task_summary
3. task_quality
4. sprint_health
5. velocity
6. team_workload
7. competency_match
8. release_health

Important: **No dedicated REST endpoint per skill is required.** The intended architecture is:
`/api/v1/query -> semantic interpretation -> Harness -> Skill/Capability -> canonical sources`.
Do not fail a skill simply because there is no `/velocity` or `/team-workload` HTTP route.

For each skill include:
- exact user query
- interpreted intent
- grounded slots
- skill id/capability id
- source evidence
- final answer/result
- PASS/FAIL

## Test H — False-green attacks
At minimum:
- nonexistent task
- nonexistent assignee
- nonexistent sprint
- nonexistent release
- contradictory filters
- unsupported/random non-PO request
- semantic parser receives prose around JSON but only accepts the embedded valid object
- invalid JSON does not execute anything
- no cross-task attachment leakage
- no AS21 mutations

## Test I — Regression
Run targeted AS21/semantic/runtime tests and the full regression suite.
Compare against 011D. Any new failure introduced by developer commits must be identified precisely.

## Gate
Set `READY_FOR_LEARNING_LOOP_012 = YES` only if:
- semantic production path is operational
- Core-8 agent E2E = 8/8
- current sprint grounding works on real OLP/DMS
- sprint completeness contract passes
- release/version source produces a real usable anchor
- real team grounding + competency source pass
- attachment regression passes
- false-green attacks pass
- no unexplained new regressions
- AS21 mutations = 0

Otherwise set NO.

## Required report
Publish only:
`qa_reports/CORE8_E2E_RETEST_011E.md`

Machine-readable footer:
```text
ASSIGNMENT_ID = CORE8_E2E_RETEST_011E
CURRENT_HEAD = <sha>
TASK_API_CANONICAL_ROUTE_PASS = YES|NO
ATTACHMENT_REGRESSION_PASS = YES|NO
REAL_TEAM_GROUNDING_PASS = YES|NO
CURRENT_SPRINT_GROUNDING_PASS = YES|NO
SPRINT_COMPLETENESS_PASS = YES|NO
SPRINT_COMPLETENESS_SOURCE = mcp-all-pages|task-api-canonical-cache|NONE
RELEASE_VERSION_ENDPOINT_PASS = YES|NO
REAL_RELEASE_ANCHOR_PASS = YES|NO
SEMANTIC_LAYER_OPERATIONAL = YES|NO
MANUAL_GONCHAROV_QUERY = PASS|CLARIFICATION|FAIL
CORE8_TASK_SEARCH = PASS|FAIL
CORE8_TASK_SUMMARY = PASS|FAIL
CORE8_TASK_QUALITY = PASS|FAIL
CORE8_SPRINT_HEALTH = PASS|FAIL
CORE8_VELOCITY = PASS|FAIL
CORE8_TEAM_WORKLOAD = PASS|FAIL
CORE8_COMPETENCY_MATCH = PASS|FAIL
CORE8_RELEASE_HEALTH = PASS|FAIL
CORE8_AGENT_E2E_PASS = <n>/8
FALSE_GREEN_ATTACKS_PASS = YES|NO
NEW_CODE_REGRESSIONS_VS_011D = <n>
AS21_MUTATIONS_DURING_TEST = 0|<n>
HIGH_BLOCKER_COUNT = <n>
READY_FOR_LEARNING_LOOP_012 = YES|NO
```

## Stop rule
After publishing the report, STOP. Do not modify code and do not begin Learning Loop 012.