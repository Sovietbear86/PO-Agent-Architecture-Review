# QA Assignment: CORE8 E2E RETEST 011D

## Role

You are TESTER ONLY. Do not edit production code or tests. Do not weaken assertions. If anything fails, capture evidence and report it; the developer will fix it.

## Purpose

Retest all blockers from `CORE8_E2E_REMEDIATION_011C.md` after developer fixes.

Developer commits to validate include:

- `9b49aa9584862539a92bddfc584482e1846502b9` — FastAPI slash redirects disabled globally.
- `8aa42d847296b9024afd0f1c3b3d9e51664fad33` — MCP tool-schema introspection for safe argument negotiation.
- `33ef1356fe2a96c253b26d202e5e3b7294e27c40` — schema-aware sprint pagination + real `search_versions` read facade.
- `1565b747005f6e83a601dde83a1b1c0fc159a6ff` — semantic authorization compatibility fallback when the enterprise OpenAI-compatible gateway rejects `response_format=json_schema`.

## Mandatory precondition: restart services

The previous 011C report tested stale processes after Git changes. Before testing, restart the Task API and PO Agent API using the repository's documented launch commands so both processes load current HEAD.

Verify process health using HTTP endpoints, not process enumeration.

Record current branch and HEAD. The branch must contain all developer commits above.

## Test 1 — canonical Task API route

Call with redirects disabled in the client:

- `GET http://localhost:8003/api/v1/tasks?limit=1`
- `GET http://localhost:8003/api/v1/tasks/?limit=1`

Expected:

- slashless route returns a direct non-redirect response (normally 200), never 307/308;
- trailing-slash route is not silently normalized into the production contract;
- `TaskApiAS21Adapter.search_tasks()` works through `/api/v1/tasks`.

Also verify `POST /api/v1/tasks` route registration without performing a real mutation. Use OpenAPI/router introspection only. AS21 mutations remain forbidden.

## Test 2 — exact task and attachment regression

Use `WMB-30000`.

Verify:

- exact canonical task can still be obtained through the production adapter;
- title/description/status/assignee/sprint/release attributes remain mapped;
- all known attachments remain visible;
- XLS/XLSX files remain classified as Excel;
- no first-search-hit substitution;
- no AS21 write/mutation.

## Test 3 — live MCP schema inspection

Call `/api/v1/swtr-read/health` and inspect live MCP tool descriptors using the Task API client implementation.

Report whether these tools exist:

- `get_sprint_tasks`
- `search_versions`

For each, record only input property NAMES from the MCP schema. Do not print credentials or sensitive values.

## Test 4 — sprint pagination completeness

Use real `OLP-SPRNT-5` if still current/available; otherwise use another real OLP/DMS sprint with `hasNext=true`.

Call:

`GET /api/v1/swtr-read/sprints/{sprint_id}/tasks?page=0&limit=100`

Then continue page-by-page while the returned source metadata says `has_next=true`.

Requirements:

- each requested page must cause the facade to pass only pagination parameter names declared by the live MCP tool schema;
- page 1+ must actually differ from page 0 when source has additional data;
- traverse until source termination;
- concatenate all task IDs;
- prove no duplicates;
- report total unique task count and page count;
- fail if the facade returns page 0 repeatedly while claiming pagination support.

Set `PAGINATION_COMPLETENESS_PASS=YES` only with real multi-page proof.

## Test 5 — release/version source

Call:

`GET /api/v1/swtr-read/versions`

Then test supported query/space parameters based on the live `search_versions` schema. Prefer WMB, DMS or OLP.

Find at least one real version/release and record:

- source space/project if available;
- release/version ID;
- display name;
- relevant dates/status if source provides them;
- raw source envelope type/keys (do not dump sensitive payloads unnecessarily).

Then find real tasks linked to that release via the existing canonical task model / release attribute and use it as the `release_health` E2E anchor.

Set `RELEASE_REAL_ANCHOR_PASS=YES` only when a real version AND real linked task evidence are proven.

## Test 6 — semantic-layer compatibility fix

The previous run returned `semantic_interpretation_failure` for every natural-language query. Retest after restarting PO Agent on current HEAD.

Use at least these queries:

1. `Найди открытые задачи Гончарова в актуальном спринте по OLAP`
2. `Покажи задачи WMB-30000`
3. `Оцени качество постановки WMB-30000`
4. a real sprint-health request for OLP/DMS
5. a real release-health request using Test 5 anchor
6. a team-workload request using a real team member
7. a competency-match request using the authoritative team competency source

For each query record:

- HTTP status;
- Harness status;
- semantic intent;
- selected skill;
- grounded slots;
- answer summary;
- evidence IDs;
- warnings.

The compatibility fallback is valid only if it preserves the same fail-closed authorization rules. Also test one clearly unsupported request and prove it does NOT get routed to a Core-8 skill.

## Test 7 — Core-8 full production E2E matrix

Retest all eight:

1. `task_search`
2. `task_summary`
3. `task_quality`
4. `sprint_health`
5. `velocity`
6. `team_workload`
7. `competency_match`
8. `release_health`

A skill is GREEN only through:

`natural language -> semantic interpretation -> Harness runtime -> selected skill -> Task API -> MCP/SWTR or approved knowledge source -> canonical data -> answer + evidence`

Adapter-only/config-only success does not count.

## Test 8 — false-green attacks

At minimum:

- nonexistent task;
- nonexistent assignee;
- nonexistent sprint;
- nonexistent release;
- contradictory filters;
- unsupported natural-language request;
- malformed semantic-provider response if test harness supports injection;
- provider that rejects `response_format` but accepts ordinary JSON: must still authorize only a valid closed-set candidate;
- provider failure in both schema and plain-JSON modes: must fail closed;
- pagination page repetition attack;
- attachment leakage across tasks.

## Test 9 — regression

Run targeted suites for:

- task API router;
- AS21 adapter;
- SWTR rich-read facade/client;
- semantic authorization/dialogue runtime;
- Core-8 Harness capabilities.

Then run the full repository regression baseline.

Report baseline/current counts and `NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN`.

## Final gate

Set `READY_FOR_LEARNING_LOOP_012 = YES` only when:

```text
CORE8_RECOVERED = 8/8
CORE8_ADAPTER_CONTRACT_PASS = 8/8
CORE8_REAL_DATA_PASS = 8/8
CORE8_AGENT_E2E_PASS = 8/8
SEMANTIC_LAYER_OPERATIONAL = YES
TASK_API_CANONICAL_ROUTE_PASS = YES
PAGINATION_COMPLETENESS_PASS = YES
RELEASE_REAL_ANCHOR_PASS = YES
ATTACHMENT_REGRESSION_PASS = YES
FALSE_GREEN_ATTACKS_PASS = YES
NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN = 0
AS21_MUTATIONS_DURING_TEST = 0
HIGH_BLOCKER_COUNT = 0
```

If anything fails, `READY_FOR_LEARNING_LOOP_012 = NO`.

## Report

Publish exactly:

`qa_reports/CORE8_E2E_RETEST_011D.md`

Include root-cause evidence for every remaining failure. Do not edit code. STOP after publishing the report.
