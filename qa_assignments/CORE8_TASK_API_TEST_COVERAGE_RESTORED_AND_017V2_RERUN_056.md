# Assignment 056 — Task-API Test Coverage Restored and 017 V2 Rerun

Repository:
`Sovietbear86/PO-Agent-Architecture-Review`

Branch:
`feat/core8-real-query-hardening-v2`

Start from current branch HEAD.

## Role

You are QA/tester only.

Do not modify production code, tests, prompts, fixtures, runners, `.env`, credentials, wrapper scripts, AS21/SWTR data, learning state, historical reports, or configuration.

Commit and push only:

`qa_reports/CORE8_TASK_API_TEST_COVERAGE_RESTORED_AND_017V2_RERUN_056.md`

## Autonomous Execution

The repository owner pre-authorizes this QA run.

Do not ask for confirmation after routine read-only inspection, service restart, targeted test execution, oracle smoke, full acceptance execution, report creation, allowed report commit, or allowed report push.

Ask only if continuing requires missing credentials, unavoidable platform approval, write outside the report allowlist, destructive action, scope expansion, or changing production/test code.

## Background

Assignment 055 initially proved the targeted cleanup still failed. A later 055 rerun reported targeted cleanup pass, but the cleanup had incorrectly weakened architecture regression tests by switching task-api coverage to fake mode.

ChatGPT/developer restored task-api coverage in:

`c413e6c8a81d596da1f83172c23afe1342338f66`

This assignment verifies that restoration and then reruns the 017 V2 acceptance path only if guards pass.

## Hard Guard — No Fake-Mode Coverage Weakening

Before running tests, inspect:

`po-agent-platform-v2/tests/test_final_architecture_regressions.py`

Required:

1. `test_runtime_factory_runtime_records_production_execution_history` must use `build_runtime_bundle("task-api")`.
2. `test_portfolio_overview_never_labels_task_api_data_as_fake` must use `build_runtime_bundle("task-api")`.
3. The portfolio test must assert `response.data["adapter"] == "task-api"`.
4. The task-api mock handlers may include `/api/v1/tasks` and `/api/v1/swtr-read/versions`; they must not replace task-api mode with fake mode.

If any guard fails:

- set `056_TASK_API_COVERAGE_GUARD = FAIL`;
- do not run full 017 V2;
- commit the report and stop.

## Step 1 — Targeted Cleanup Retest

Run exactly:

```bash
cd po-agent-platform-v2
python3 -m pytest \
  tests/test_domain_models.py::TestNormalizeTaskStatus::test_normalize_unknown_status \
  tests/test_final_architecture_regressions.py::test_runtime_factory_runtime_records_production_execution_history \
  tests/test_final_architecture_regressions.py::test_portfolio_overview_never_labels_task_api_data_as_fake \
  tests/test_final_architecture_regressions.py::test_source_dependent_request_cannot_be_reinterpreted_when_fact_is_missing \
  tests/test_harness_dialogue_learning.py::test_conflicting_definition_never_silently_replaces_active_semantics \
  tests/test_harness_dialogue_runtime.py::test_dialogue_executes_with_extracted_task_key \
  -q
```

`056_TARGETED_CLEANUP_PASS = YES` only if all targeted tests pass.

If any targeted test fails:

- do not run full 017 V2;
- record exact failure output;
- classify each failure;
- commit the report and stop.

## Step 2 — Production Service and Oracle Smoke

If targeted cleanup passes:

1. Restart Task API and PO Agent from current HEAD.
2. Verify PO Agent health reports:
   - adapter/task mode is `task-api`;
   - semantic mode is production LLM, not fake;
   - source status is healthy.
3. Re-run 051-style bounded SWTR oracle smoke:
   - DMS-SPRNT-2 bounded source returns source-backed tasks;
   - per-task hydration includes assignee/status/sprint attributes;
   - Garanin + DMS-SPRNT-2 exact set is compared by exact task keys;
   - invalid sprint `DMS-SPRNT-999999` fails closed or asks clarification;
   - no foreign sprint tasks are accepted.

If real AS21/SWTR oracle smoke times out:

- record exact endpoint, request, timeout value, elapsed time, and service logs;
- classify as `ENVIRONMENT_TIMEOUT` only if health is otherwise good and no code exception is present;
- do not claim production RED without evidence of production defect;
- do not run full 017 V2.

## Step 3 — Full 017 V2 Rerun

If targeted cleanup and oracle smoke both pass, run:

`qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`

Mandatory:

- production semantic interpreter;
- independent source-backed oracle;
- exact key-set comparisons for task-set cases;
- complete per-ID evidence table;
- CL-01..CL-15 all executed, not just implementation-checked;
- every failure classified;
- no fake adapter for acceptance verdicts;
- no GREEN from aggregate counts only;
- no `COMPLETED + 0` PASS without independent empty oracle.

## Report Requirements

Create:

`qa_reports/CORE8_TASK_API_TEST_COVERAGE_RESTORED_AND_017V2_RERUN_056.md`

Include:

- branch and HEAD;
- changed-files guard evidence;
- task-api coverage guard evidence;
- targeted pytest output;
- production service wiring evidence;
- oracle smoke evidence or exact timeout evidence;
- full 017 V2 per-ID evidence if executed;
- final decision.

## Required Footer

```text
ASSIGNMENT_ID = CORE8_TASK_API_TEST_COVERAGE_RESTORED_AND_017V2_RERUN_056
START_HEAD = <sha>
REPORT_COMMIT = <sha-or-PENDING>
CLEAN_TREE_GUARD = PASS|FAIL
PRODUCTION_CODE_MODIFIED_BY_QA = NO
056_TASK_API_COVERAGE_GUARD = PASS|FAIL
056_TARGETED_CLEANUP_PASS = YES|NO|BLOCKED
056_ORACLE_SMOKE_PASS = YES|NO|BLOCKED
ENVIRONMENT_TIMEOUT_COUNT = n
017V2_FULLY_EXECUTED = YES|NO
ORACLE_PREFLIGHT_PASS = YES|NO|BLOCKED
ORACLE_INDEPENDENCE_PASS = YES|NO|BLOCKED
FUNCTIONAL_TOTAL = n
FUNCTIONAL_PASS = n
FUNCTIONAL_FAIL = n
CORRECTION_LOOP_PASS = x/15
FALSE_GREEN_COUNT = n
SILENT_SLOT_DROP_COUNT = n
QUERY_HTTP_500_COUNT = n
NEW_HIGH_PRODUCTION_REGRESSIONS = n
READY_TO_RESUME_GATE_E = YES|NO
READY_FOR_FRONTEND_FINALIZATION = YES|NO
056_VERDICT = GREEN|RED|BLOCKED
```

`READY_TO_RESUME_GATE_E = YES` is allowed only if full 017 V2 is fully executed with complete evidence and all acceptance gates are GREEN.

## Completion

Commit and push only the allowed report file, then stop and return:

- report commit SHA;
- concise verdict;
- full report text.
