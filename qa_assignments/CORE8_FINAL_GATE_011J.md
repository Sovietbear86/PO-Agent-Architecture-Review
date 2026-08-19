# QA Assignment: CORE8 FINAL GATE 011J

## Mission
Close Core-8 honestly and authorize Learning Loop 012 only on proven production behavior.

GigaCode is **tester only**. Do not edit production code, tests, configuration, fixtures, expected results, or AS21 data. Developer fixes are supplied separately. If a test fails, capture evidence and classify it; do not patch it.

## Mandatory startup
1. Pull `feat/real-baseline-candidate-eval-v1` and record exact HEAD.
2. Restart Task API and PO Agent from that HEAD; record PIDs/ports.
3. Verify MCP-SWTR connectivity.
4. Confirm AS21 read-only behavior; mutations must remain zero.

## A. Core-8 acceptance matrix
Execute all queries through the real production endpoint `/api/v1/query`.

1. `task_search`: `Найди задачи Гончарова в актуальном спринте по OLAP`
2. `task_summary`: `Суммаризируй задачу WMB-30000`
3. `task_quality`: `Оцени качество постановки WMB-30000`
4. `sprint_health`: `Покажи здоровье текущего спринта OLP`
5. `velocity`: `Покажи velocity текущего спринта OLP`
6. `team_workload`: `Какая нагрузка у Калачанова?`
7. `competency_match`: `Подбери исполнителя для WMB-30000`
8. `release_health`: revalidate a real release from canonical AS21 `fix_version_s`; preferred current anchor `743559fc-f632`, then execute `Покажи здоровье релиза <REAL_RELEASE_ID>`.

Required: all 8 return correct source-grounded production behavior. `CORE8_AGENT_E2E_PASS = 8/8`. For release_health the response must contain the exact release ID and evidence tasks belonging to it.

## B. Release semantic extraction proof
Specifically prove that a release identifier embedded in natural Russian text is extracted into the semantic `release_id` slot and reaches `release_health` without unnecessary clarification.

Test at minimum:
- `Покажи здоровье релиза 743559fc-f632`
- the same query using whatever current real release is selected if live data drifted.

Required: `COMPLETED`, exact release ID preserved, source-backed task evidence present. No hardcoded special case for `743559fc-f632` is acceptable.

## C. Stale live-anchor test handling
Re-run `tests/test_harness_dialogue_runtime.py::test_dialogue_executes_with_extracted_task_key`.

If its configured task (historically `OLP-3134`) does not exist in current AS21, first prove nonexistence using the canonical exact-task/read path. Classify this as `STALE_LIVE_ANCHOR`, not `PRODUCTION_REGRESSION`, provided:
- exact lookup correctly returns not-found;
- an equivalent currently existing task key is correctly extracted from natural language and executes successfully;
- no production code is changed to fabricate the missing task.

Report both the stale anchor and the live replacement evidence. Do not make production behavior less strict merely to satisfy an obsolete live-data fixture.

## D. Previously suspicious regressions
Re-run and evidence these individually:
- `test_runtime_factory_runtime_records_production_execution_history`
- `test_portfolio_overview_never_labels_task_api_data_as_fake`

Classify as `PRODUCTION_REGRESSION` only if current production behavior itself violates the intended contract. Include actual vs expected evidence.

Historical known non-production categories must remain correctly classified when evidence still supports them:
- PDF discovery expectation after proven PDF support -> `STALE_EXPECTATION_PROVEN_IMPROVEMENT`;
- repository `.gigacode` hygiene/local artifact -> `ENVIRONMENT`;
- unknown-status expectation -> stale if canonical contract intentionally preserves unknown values;
- external MCP `search_versions` ToolError -> `EXTERNAL_DEPENDENCY_ISSUE` when canonical `fix_version_s` fallback works.

## E. False-green gate
Repeat the 10-control false-green matrix from 011I. All contradictory/nonexistent/unsupported requests must fail closed or request clarification as semantically appropriate. No silently discarded selector is allowed.

Required: `FALSE_GREEN_ATTACKS_PASS = YES`.

## F. Source completeness and attachments
Reprove:
- current OLP sprint complete-mode set, including pagination and no duplicate task IDs;
- WMB-30000 attachment visibility and Office classification;
- expected current evidence is 5 XLSX attachments unless live AS21 itself changed.

Required: `SPRINT_COMPLETENESS_PASS = YES`; `ATTACHMENT_REGRESSION_PASS = YES` or explicitly `LIVE_DATA_DRIFT` with source evidence.

## G. Full regression
Run full pytest after targeted checks. Triage every failure/error into exactly one of:
- `PRODUCTION_REGRESSION`
- `STALE_LIVE_ANCHOR`
- `STALE_EXPECTATION_PROVEN_IMPROVEMENT`
- `ENVIRONMENT`
- `EXTERNAL_DEPENDENCY_ISSUE`

Do not count stale/environment/external cases as HIGH production regressions.

## H. Final authorization rule
Set `READY_FOR_LEARNING_LOOP_012 = YES` iff all are true:
- `CORE8_AGENT_E2E_PASS = 8/8`
- `REAL_RELEASE_HEALTH_E2E_PASS = YES`
- `FALSE_GREEN_ATTACKS_PASS = YES`
- `SPRINT_COMPLETENESS_PASS = YES`
- attachment regression is green or proven live-data drift
- `TARGETED_HIGH_PRODUCTION_REGRESSIONS = 0`
- `NEW_HIGH_PRODUCTION_REGRESSIONS = 0`
- `AS21_MUTATIONS_DURING_TEST = 0`

A stale `OLP-3134` anchor, stale PDF expectation, repository-local hygiene issue, or external `search_versions` outage must **not** veto the gate when production behavior is independently proven correct.

## Required report
Publish and push:
`qa_reports/CORE8_FINAL_GATE_011J.md`

Include exact evidence for every section above and this footer:

```text
ASSIGNMENT_ID = CORE8_FINAL_GATE_011J
CURRENT_HEAD = <sha>
CORE8_AGENT_E2E_PASS = x/8
REAL_RELEASE_ID = <id>
REAL_RELEASE_HEALTH_E2E_PASS = YES|NO
RELEASE_ID_SEMANTIC_EXTRACTION_PASS = YES|NO
STALE_LIVE_ANCHORS = N
FALSE_GREEN_ATTACKS_PASS = YES|NO
SPRINT_COMPLETENESS_PASS = YES|NO
ATTACHMENT_REGRESSION_PASS = YES|NO|LIVE_DATA_DRIFT
TARGETED_HIGH_PRODUCTION_REGRESSIONS = N
FULL_REGRESSION_PASSED = N
FULL_REGRESSION_FAILED = N
FULL_REGRESSION_ERRORS = N
EXTERNAL_SEARCH_VERSIONS_TOOL_HEALTH = PASS|FAIL
NEW_HIGH_PRODUCTION_REGRESSIONS = N
AS21_MUTATIONS_DURING_TEST = N
READY_FOR_LEARNING_LOOP_012 = YES|NO
```

## Stop rule
After publishing `011J`, STOP. Do not start Learning Loop 012 and do not expand to 48 skills. The report is the authorization evidence for the next phase.