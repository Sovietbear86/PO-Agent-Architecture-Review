# QA Assignment: CORE8 FALSE-GREEN & RELEASE CLOSURE 011H

## Mission
Close the remaining Core-8 gate after 011G. GigaCode is TESTER ONLY: do not edit production code or tests.

Developer fixes to validate:
- `2aba4db` — contradictory sprint selectors fail closed before execution.
- `a6e9710` — production subclasses of TaskApiAS21Adapter are labelled `task-api`, not `fake-as21`.

## Mandatory startup
1. Pull `feat/real-baseline-candidate-eval-v1` and record exact HEAD.
2. Restart Task API and PO Agent from that HEAD.
3. Verify health endpoints and real task `WMB-30000` before E2E.
4. Do not modify code/tests. Report defects only.

## A — Contradictory-filter closure
Through `/api/v1/query`, test at least:
- `Найди задачи Гончарова в текущем спринте OLP и в OLP-SPRNT-4`
- a query containing two distinct explicit sprint IDs, using real/known sprint IDs when available.

Expected: NEVER `COMPLETED`. Must be `NEEDS_CLARIFICATION` (preferred) or safe `FAILED`, with explicit indication that one sprint selector must be chosen. No source execution may silently discard one selector.

Control: `Найди задачи Гончарова в текущем спринте OLP` must remain COMPLETED.

## B — Real release discovery from canonical AS21 tasks
External MCP `search_versions` is known unhealthy; test it and report its status separately, but do not make its failure erase proven canonical `fix_version_s` facts.

Using read-only Task API/canonical AS21 tasks:
1. Scan enough real tasks to discover actual non-empty `release_id`/`fix_version_s` values.
2. Record at least 3 examples if available, including evidence task keys.
3. Select ONE real release with at least one real task. Prefer CRPV because 011G proved 24 unique CRPV releases exist.
4. Do not invent a release name and do not infer a naming convention.

## C — release_health production E2E
Using the exact real release discovered in B, call `/api/v1/query` with natural Russian wording, e.g. `Покажи здоровье релиза <REAL_RELEASE_ID>`.

PASS requires:
- intent `release_health`;
- skill `release-health`;
- status `COMPLETED`;
- returned release ID equals the real source-backed release;
- task/evidence set is source-backed and non-empty;
- no fabricated WMB/OLP/DMS release is substituted.

Also attack `Покажи здоровье релиза NONEXISTENT_RELEASE_99999`: it must not be COMPLETED.

## D — Full Core-8 matrix
Re-run all eight through `/api/v1/query`:
1. task_search
2. task_summary
3. task_quality
4. sprint_health
5. velocity
6. team_workload
7. competency_match / assignee recommendation (use the authoritative Core-8 mapping from prior reports)
8. release_health using the real release from B

Gate metric must be `x/8`, never `7/7`. A skill not tested is not PASS.

## E — False-green matrix
Re-run:
- nonexistent exact task;
- nonexistent assignee;
- nonexistent sprint;
- nonexistent release;
- contradictory sprint selectors;
- unsupported request;
- weather/arithmetic;
- invalid JSON.

`FALSE_GREEN_ATTACKS_PASS=YES` only if none silently completes with invented/ignored source constraints.

## F — Targeted regression triage
Re-run the failures from 011G individually and capture exact assertion/stack trace. Classify each as:
- `PRODUCTION_REGRESSION`
- `STALE_EXPECTATION`
- `PROVEN_IMPROVEMENT`
- `ENVIRONMENT`

Pay special attention to:
- `test_portfolio_overview_never_labels_task_api_data_as_fake` — expected fixed by `a6e9710`;
- `test_task_api_end_to_end_query_maps_source_to_harness_contract`;
- `test_dialogue_clarifies_multiple_ambiguous_slots_before_execution`;
- `test_dialogue_executes_with_extracted_task_key`.

For the PDF test, do not call successful real PDF discovery a production regression merely because an old assertion expected absence.
For unknown-status normalization, report whether preserving the raw unknown status is the current intended canonical contract; do not change code.
For `.gigacode/settings.json`, classify missing local environment files separately from product behavior.

## G — Full regression
Run the complete suite. Report passed/failed/errors/skipped and exact delta vs 011G. Distinguish collection/environment errors from assertion failures.

## H — Architecture assertions
Confirm:
- production `/api/v1/query` uses `ProductionTaskApiAS21Adapter`/Task API path and never labels it `fake-as21`;
- release fallback is based only on canonical AS21 task `fix_version_s` values;
- external MCP `search_versions` failure remains observable separately;
- AS21 mutations = 0.

## Gate
`READY_FOR_LEARNING_LOOP_012=YES` only if:
- Core-8 E2E = 8/8;
- real release_health E2E PASS;
- false-green matrix PASS;
- contradictory filters fail closed;
- no HIGH production regression remains in targeted tests;
- no new production regression vs 011G;
- AS21 mutations = 0.

External MCP `search_versions` ToolError may be recorded as an external degraded dependency if and only if release_health is proven through canonical source-backed task release facts and no data is fabricated.

## Report
Publish `qa_reports/CORE8_FALSE_GREEN_RELEASE_CLOSURE_011H.md` and push it.

Required footer:
```text
ASSIGNMENT_ID = CORE8_FALSE_GREEN_RELEASE_CLOSURE_011H
CURRENT_HEAD = <sha>
CONTRADICTORY_FILTER_FAIL_CLOSED = YES|NO
REAL_RELEASE_DISCOVERED = YES|NO
REAL_RELEASE_ID = <id|NONE>
REAL_RELEASE_HEALTH_E2E_PASS = YES|NO
EXTERNAL_SEARCH_VERSIONS_TOOL_HEALTH = PASS|FAIL
CORE8_AGENT_E2E_PASS = x/8
FALSE_GREEN_ATTACKS_PASS = YES|NO
PORTFOLIO_PRODUCTION_SOURCE_LABEL_PASS = YES|NO
TARGETED_HIGH_PRODUCTION_REGRESSIONS = N
FULL_REGRESSION_PASSED = N
FULL_REGRESSION_FAILED = N
FULL_REGRESSION_ERRORS = N
NEW_PRODUCTION_REGRESSIONS_VS_011G = N
AS21_MUTATIONS_DURING_TEST = N
READY_FOR_LEARNING_LOOP_012 = YES|NO
```

## Stop rule
After publishing the report, STOP. Do not start Learning Loop 012 and do not edit code/tests.