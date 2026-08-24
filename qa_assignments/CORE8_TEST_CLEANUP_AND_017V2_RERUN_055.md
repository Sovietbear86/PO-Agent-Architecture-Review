# Assignment 055 — Test Cleanup Verification and 017 V2 Rerun

Repository:
`Sovietbear86/PO-Agent-Architecture-Review`

Branch:
`feat/core8-real-query-hardening-v2`

Start from current branch HEAD.

## Role

You are QA/tester only.

Do not modify production code, tests, prompts, fixtures, runners, `.env`, credentials, wrapper scripts, AS21/SWTR data, learning state, historical reports, or configuration.

Commit and push only:

`qa_reports/CORE8_TEST_CLEANUP_AND_017V2_RERUN_055.md`

## Autonomous Execution

The repository owner pre-authorizes this QA run.

Do not ask for confirmation after routine read-only inspection, service restart, targeted test execution, full acceptance execution, report creation, allowed report commit, or allowed report push.

Ask only if continuing requires missing credentials, unavoidable platform approval, destructive action, write outside the report allowlist, scope expansion, or changing production/test code.

## Background

Assignment 051 accepted the bounded SWTR oracle path.

Assignment 052 GREEN was rejected by Assignment 053.

Assignment 054 classified the remaining failures and found no confirmed production regression, but required cleanup of stale tests and incomplete mocks before another full 017 V2 run.

ChatGPT/developer then committed the test cleanup on this branch. This assignment verifies that cleanup and, only if it passes, reruns the full 017 V2 matrix correctly.

## Production Code Boundary

This assignment is not a production-fix validation. It validates test cleanup and real acceptance behavior.

If production code is dirty or modified locally, stop with `055_VERDICT = BLOCKED` and report the dirty files.

## Step 1 — Preflight

Record:

- branch;
- HEAD;
- clean tree status;
- latest commits since Assignment 054;
- service PIDs/ports after restart;
- `PO_AGENT_AS21_MODE=task-api`;
- Task API URL;
- semantic mode/LLM endpoint evidence;
- SWTR oracle transport evidence.

Restart Task API and PO Agent from current HEAD.

Use real AS21/SWTR and the production semantic interpreter.

Do not use FakeAS21Adapter for acceptance verdicts.

## Step 2 — Targeted Cleanup Retest

Run exactly this targeted pytest command from `po-agent-platform-v2`:

```bash
python3 -m pytest \
  tests/test_domain_models.py::TestNormalizeTaskStatus::test_normalize_unknown_status \
  tests/test_final_architecture_regressions.py::test_runtime_factory_runtime_records_production_execution_history \
  tests/test_final_architecture_regressions.py::test_portfolio_overview_never_labels_task_api_data_as_fake \
  tests/test_final_architecture_regressions.py::test_source_dependent_request_cannot_be_reinterpreted_when_fact_is_missing \
  tests/test_harness_dialogue_learning.py::test_conflicting_definition_never_silently_replaces_active_semantics \
  tests/test_harness_dialogue_runtime.py::test_dialogue_executes_with_extracted_task_key \
  -q
```

`055_TARGETED_CLEANUP_PASS = YES` only if all targeted tests pass.

If any targeted test fails:

- do not run full 017 V2;
- record exact failure output;
- classify each failure as production/test/env;
- commit the report and stop.

## Step 3 — Oracle Smoke Guard

If targeted cleanup passes, re-run the 051-style oracle smoke before full 017 V2:

- DMS-SPRNT-2 bounded source returns source-backed tasks;
- per-task hydration includes assignee/status/sprint attributes;
- Garanin + DMS-SPRNT-2 exact set is compared by exact task keys;
- invalid sprint `DMS-SPRNT-999999` fails closed or asks clarification;
- no foreign sprint tasks are accepted.

`055_ORACLE_SMOKE_PASS = YES` only if all checks pass.

If oracle smoke fails, do not run full 017 V2.

## Step 4 — Full 017 V2 Rerun

If targeted cleanup and oracle smoke both pass, run the canonical full assignment:

`qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`

Mandatory rules:

- execute through production semantic interpreter;
- use independent source-backed oracle, not agent output as oracle;
- compare exact key sets where task sets are involved;
- execute all CL-01..CL-15 correction-loop cases;
- record per-ID evidence for every case;
- classify every failure;
- do not mark implementation existence as execution evidence;
- do not claim GREEN from aggregate counts;
- do not mark `COMPLETED + 0` as PASS without an independent empty oracle;
- do not weaken acceptance criteria.

## Report Requirements

Create:

`qa_reports/CORE8_TEST_CLEANUP_AND_017V2_RERUN_055.md`

The report must include:

- branch and HEAD;
- clean tree evidence;
- test cleanup commit evidence;
- production wiring evidence;
- targeted cleanup retest output summary;
- oracle smoke evidence;
- full 017 V2 per-ID matrix if executed;
- exact key-set diffs for every task-set case;
- CL-01..CL-15 correction-loop evidence;
- all failure classifications;
- final decision.

## Required Footer

Include this footer exactly with filled values:

```text
ASSIGNMENT_ID = CORE8_TEST_CLEANUP_AND_017V2_RERUN_055
START_HEAD = <sha>
REPORT_COMMIT = <sha-or-PENDING>
CLEAN_TREE_GUARD = PASS|FAIL
PRODUCTION_CODE_MODIFIED_BY_QA = NO
055_TARGETED_CLEANUP_PASS = YES|NO|BLOCKED
055_ORACLE_SMOKE_PASS = YES|NO|BLOCKED
017V2_FULLY_EXECUTED = YES|NO
ORACLE_PREFLIGHT_PASS = YES|NO|BLOCKED
ORACLE_INDEPENDENCE_PASS = YES|NO|BLOCKED
FUNCTIONAL_TOTAL = n
FUNCTIONAL_PASS = n
FUNCTIONAL_FAIL = n
CORRECTION_LOOP_PASS = x/15
TARGETED_CLARIFICATION_PASS = YES|NO|BLOCKED
SESSION_CONTEXT_RETENTION_PASS = YES|NO|BLOCKED
NEGATIVE_FEEDBACK_TRACE_PASS = YES|NO|BLOCKED
FALSE_GREEN_COUNT = n
SILENT_SLOT_DROP_COUNT = n
QUERY_HTTP_500_COUNT = n
NEW_HIGH_PRODUCTION_REGRESSIONS = n
READY_TO_RESUME_GATE_E = YES|NO
READY_FOR_FRONTEND_FINALIZATION = YES|NO
055_VERDICT = GREEN|RED|BLOCKED
```

`READY_TO_RESUME_GATE_E = YES` is allowed only if full 017 V2 is fully executed, all acceptance gates are GREEN, `CORRECTION_LOOP_PASS = 15/15`, `FALSE_GREEN_COUNT = 0`, `SILENT_SLOT_DROP_COUNT = 0`, `QUERY_HTTP_500_COUNT = 0`, and `NEW_HIGH_PRODUCTION_REGRESSIONS = 0`.

## Completion

Commit and push only the allowed report file, then stop and return:

- report commit SHA;
- concise verdict;
- full report text.
