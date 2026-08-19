# QA Assignment: CORE8 E2E RETEST 011G

## Role boundary
GigaCode is TESTER ONLY for this assignment. Do not edit production code, tests, configuration, or fixtures. Do not auto-fix failures. Record findings in the report and stop.

## Objective
Retest developer remediation after 011F and determine whether Core-8 is ready for Learning Loop 012.

Developer changes to validate include:
- precise high-confidence Core-8 sprint intent normalization;
- live current-sprint grounding after canonical validation;
- fail-closed negative exact-task lookup;
- production runtime wiring for these boundaries;
- release grounding fallback from canonical real AS21 task `fix_version_s` when MCP `search_versions` is externally broken;
- source-readiness tests aligned to proven source facts.

## Environment reset
1. Pull `origin/feat/real-baseline-candidate-eval-v1`.
2. Record exact HEAD.
3. Restart Task API on 8003 and PO Agent on 8004 from that HEAD.
4. Confirm MCP-SWTR SSE connectivity.
5. Do not print or persist secrets.

## Test A — canonical task/attachment regression
Reconfirm:
- `/api/v1/tasks` direct 200, no redirect;
- trailing-slash route does not become alternate contract;
- WMB-30000 exact read;
- all 5 XLSX attachments remain visible;
- no AS21 mutations.

## Test B — current-sprint semantic precision and live grounding
Run all through `/api/v1/query`:
1. `Какой текущий спринт OLP?`
2. `Покажи здоровье текущего спринта OLP`
3. `Покажи velocity текущего спринта OLP`
4. `Найди задачи Гончарова в актуальном спринте по OLAP`
5. `Найди открытые задачи Гончарова в актуальном спринте по OLAP`

Expected:
- query 1 intent = `sprint_current` and uses live `OLP-SPRNT-5` (or whatever current live AS21 returns at test time);
- query 2 intent = `sprint_health`, not `sprint_current`;
- query 3 intent = `sprint_velocity`, not `sprint_current`;
- queries 2/3 must receive a source-backed sprint_id automatically and execute, not ask for sprint_id;
- query 4 must resolve `Goncharov.A.O`, OLP product alias, and live current sprint, then execute task search;
- query 5 may ask ONLY for business-semantic clarification of what `open` means if no learned rule exists. It must NOT ask for sprint_id, assignee, or product if those are source-groundable.

Capture returned intent, skill, slots, status, answer and evidence.

## Test C — nonexistent exact task must fail closed
Through `/api/v1/query` execute:
`Покажи задачу NONEXISTENT-99999`

Required:
- response status = FAILED;
- warning includes `entity_not_found` (or equivalent explicit negative-source marker);
- data preserves `found=false` and not-found evidence;
- must never return COMPLETED.

Also verify a real exact task WMB-30000 still returns COMPLETED.

## Test D — invalid JSON must fail closed at HTTP boundary
Send syntactically invalid JSON and structurally invalid request bodies to `/api/v1/query`.

Judge fail-closed by HTTP contract, NOT by trying to read a Harness `status` field from a validation-error response.
Expected: HTTP 4xx (normally FastAPI/Pydantic 422) and no capability execution/evidence.

Do not report `status=None` as false-green if the HTTP request itself was rejected before Harness execution.

## Test E — release/version resilience
Separate TWO facts in the report:

### E1 External MCP tool health
Call `/api/v1/swtr-read/versions?space=WMB`, OLP and DMS and record whether the external MCP `search_versions` ToolError still exists. If it remains 502, label it `EXTERNAL_MCP_TOOL_BLOCKER`, not an invented internal success.

### E2 Production Harness release grounding
Independently verify that real canonical AS21 tasks expose `fix_version_s`/canonical `release_id` values. Use the production `ProductionTaskApiAS21Adapter.search_versions()` path and prove that, when the external tool fails, it returns only release identifiers grounded in those real canonical tasks with explicit `source=canonical_as21_task.fix_version_s` and evidence task keys.

Choose one real release found from WMB/OLP/DMS and run a real `release_health` natural-language query through `/api/v1/query` using that release ID. Required: no fabricated release, exact release ID grounded, capability executes with AS21 task evidence.

A broken external `search_versions` tool may remain a separately tracked integration issue, but it must no longer make the agent unable to use release facts already present on real AS21 tasks.

## Test F — full Core-8 production E2E
Run and report exactly these eight capability classes through the user-facing `/api/v1/query` path:
1. task_search
2. task_summary
3. task_quality
4. sprint_health
5. velocity
6. team_workload
7. competency_match / team assignee recommendation according to authoritative Core-8 mapping
8. release_health

For every row provide:
`query | status | intent | skill | source evidence | PASS/FAIL`.

A PASS requires actual execution (`COMPLETED`) except a deliberately ambiguous business semantic such as undefined `open`, which must be tested with a second unambiguous query so the underlying Core-8 skill is still proven operational.

## Test G — sprint completeness
Reconfirm live first page and complete canonical result. Ensure no duplicate IDs and complete count >= first-page count. Record `completeness_source`.

## Test H — false-green matrix
At minimum:
- nonexistent exact task -> FAILED;
- nonexistent assignee -> fail closed/clarify;
- nonexistent sprint -> fail closed/clarify;
- nonexistent release -> fail closed/clarify;
- contradictory filters -> fail closed/empty, never broad all-task result;
- unsupported weather/arithmetic/code requests -> fail closed;
- invalid JSON -> HTTP 4xx before execution;
- no task/attachment leakage;
- no AS21 mutations.

## Test I — targeted regression cleanup
Run the seven failures from 011F individually and classify each as:
- FIXED,
- REAL_PRODUCTION_REGRESSION,
- STALE_EXPECTATION_AFTER_PROVEN_IMPROVEMENT,
- LOCAL_ENVIRONMENT_ARTIFACT.

Important:
- PDF attachment discovery is a proven functionality improvement; do not call it a production regression merely because an old test expected absence.
- source readiness must distinguish base `TaskApiAS21Adapter` (tasks + proven attachments only) from `ProductionTaskApiAS21Adapter` (tasks + attachments + proven sprint/release production paths).
- do not alter tests during QA.

## Test J — full regression
Run full project regression and compare to 011F:
- previous: 1164 passed, 7 failed, 11 errors, 12 skipped.
- report current counts;
- enumerate every remaining failure/error;
- `NEW_CODE_REGRESSIONS_VS_011F` must be explicit.

## Gate
Set `READY_FOR_LEARNING_LOOP_012 = YES` only if:
- Core-8 user-facing E2E = 8/8;
- current-sprint intent/grounding tests pass;
- nonexistent task false-green is eliminated;
- invalid JSON is HTTP fail-closed;
- real release_health executes using real AS21 release evidence;
- sprint completeness passes;
- false-green matrix passes;
- no new production regressions;
- AS21 mutations = 0.

The external MCP `search_versions` ToolError must be reported separately as `EXTERNAL_SEARCH_VERSIONS_TOOL_HEALTH`. It is a gate blocker only if the production Harness cannot safely ground/use releases from real AS21 source facts without inventing data.

## Required report
Publish and push:
`qa_reports/CORE8_E2E_RETEST_011G.md`

Machine-readable footer:
```text
ASSIGNMENT_ID = CORE8_E2E_RETEST_011G
CURRENT_HEAD = <sha>
CURRENT_SPRINT_SEMANTIC_PRECISION_PASS = YES|NO
CURRENT_SPRINT_LIVE_GROUNDING_PASS = YES|NO
NONEXISTENT_TASK_FAIL_CLOSED = YES|NO
INVALID_JSON_HTTP_FAIL_CLOSED = YES|NO
EXTERNAL_SEARCH_VERSIONS_TOOL_HEALTH = PASS|FAIL
CANONICAL_TASK_RELEASE_FALLBACK_PASS = YES|NO
REAL_RELEASE_HEALTH_E2E_PASS = YES|NO
SPRINT_COMPLETENESS_PASS = YES|NO
CORE8_AGENT_E2E_PASS = x/8
FALSE_GREEN_ATTACKS_PASS = YES|NO
TARGETED_011F_FAILURES_REMAINING = n
FULL_REGRESSION_PASSED = n
FULL_REGRESSION_FAILED = n
FULL_REGRESSION_ERRORS = n
NEW_CODE_REGRESSIONS_VS_011F = n
AS21_MUTATIONS_DURING_TEST = n
READY_FOR_LEARNING_LOOP_012 = YES|NO
```

## Stop rule
After publishing the report, STOP. Do not start Learning Loop 012 and do not edit code/tests.
