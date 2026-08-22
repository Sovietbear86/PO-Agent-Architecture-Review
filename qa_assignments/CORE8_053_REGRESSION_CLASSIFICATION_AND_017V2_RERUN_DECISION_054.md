# Assignment 054 — Regression Classification and 017 V2 Rerun Decision

Repository:
`Sovietbear86/PO-Agent-Architecture-Review`

Branch:
`feat/core8-real-query-hardening-v2`

Start from current branch HEAD.

## Role

You are QA/auditor only.

Do not modify production code, tests, prompts, fixtures, runners, `.env`, credentials, wrapper scripts, AS21/SWTR data, learning state, historical reports, or configuration.

Commit and push only:

`qa_reports/CORE8_053_REGRESSION_CLASSIFICATION_AND_017V2_RERUN_DECISION_054.md`

## Autonomous Execution

The repository owner pre-authorizes this QA audit.

Do not ask for confirmation after routine read-only inspection, service restart, test execution, report creation, allowed report commit, or allowed report push.

Ask only if continuing requires missing credentials, unavoidable platform approval, destructive action, write outside the report allowlist, scope expansion, or changing production/test code.

## Background

Assignment 051 proved the bounded SWTR oracle path:

- clean tree guard passed;
- stdio MCP-SWTR transport works through Task API environment;
- DMS-SPRNT-2 bounded source returned 22 tasks;
- per-task hydration worked;
- Garanin + DMS-SPRNT-2 exact set passed;
- `READY_TO_RERUN_017_V2 = YES`.

Assignment 052 then incorrectly reported GREEN for the full 017 V2 rerun.

Assignment 053 correctly rejected 052 because:

- `CORRECTION_LOOP_PASS = 2/15`, not 15/15;
- per-ID evidence was incomplete;
- test failures were not fully classified;
- the matrix was not proven to have been executed through the production semantic interpreter.

This assignment does **not** rerun the full 017 V2 matrix yet. It classifies the unresolved failures and decides whether the next step should be:

1. a production fix;
2. a test/expectation update by ChatGPT/developer;
3. a proper full 017 V2 rerun with per-ID evidence.

## Required Inputs

Read these files from the current branch:

- `qa_reports/CORE8_052_VERDICT_INTEGRITY_AUDIT_053.md`
- `qa_reports/CORE8_017V2_FULL_CLEAN_ORACLE_RERUN_052.md`
- `qa_reports/CORE8_ORACLE_CLEAN_TREE_EXACT_SET_RETEST_051.md`
- `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
- relevant tests and implementation files for each failure listed below.

## Scope

Classify exactly these six behavior-change items from Assignment 053:

1. `test_domain_models.py::TestNormalizeTaskStatus::test_normalize_unknown_status`
2. `test_final_architecture_regressions.py::test_runtime_factory_runtime_records_production_execution_history`
3. `test_final_architecture_regressions.py::test_portfolio_overview_never_labels_task_api_data_as_fake`
4. `test_final_architecture_regressions.py::test_source_dependent_request_cannot_be_reinterpreted_when_fact_is_missing`
5. `test_harness_dialogue_learning.py::test_conflicting_definition_never_silently_replaces_active_semantics`
6. `test_harness_dialogue_runtime.py::test_dialogue_executes_with_extracted_task_key`

Also restate, but do not re-litigate, the two non-production failures already classified by 053:

- incomplete mock for live sprint membership;
- missing LLM env for `test_conversation_context_is_supplied_to_next_semantic_turn`.

## Classification Rules

For each of the six scoped items, assign exactly one classification:

- `PRODUCTION_REGRESSION`
- `INTENTIONAL_FAIL_CLOSED_HARDENING`
- `STALE_TEST_EXPECTATION`
- `TEST_INFRA_OR_MOCK_BUG`
- `ENVIRONMENT_ONLY`
- `NEEDS_OWNER_DECISION`

Do not mark `PRODUCTION_REGRESSION` unless current production behavior violates the active source-backed/fail-closed contract.

Do not mark `GREEN` or `READY_TO_RESUME_GATE_E=YES` unless all high production regressions are zero and the next full 017 V2 rerun is explicitly ready.

## Required Evidence Per Item

For each scoped item record:

- test name;
- exact old assertion or expected behavior;
- observed/current behavior from 052/053;
- relevant production code path;
- relevant active contract from assignments/reports;
- classification;
- whether ChatGPT/developer must fix production code, update tests, or only rerun acceptance;
- concise rationale.

Use source snippets sparingly; cite file paths and function/test names.

## Targeted Execution

Run the smallest useful targeted checks available in the environment.

At minimum attempt:

```bash
cd po-agent-platform-v2
python -m pytest \
  tests/test_domain_models.py::TestNormalizeTaskStatus::test_normalize_unknown_status \
  tests/test_final_architecture_regressions.py \
  tests/test_harness_dialogue_learning.py::test_conflicting_definition_never_silently_replaces_active_semantics \
  tests/test_harness_dialogue_runtime.py::test_dialogue_executes_with_extracted_task_key \
  -q
```

If pytest or dependencies are unavailable, do not invent results. Record `TARGETED_PYTEST_EXECUTED = NO` with the exact blocker and classify by static source evidence only.

## Decision Gate

Set:

- `054_READY_FOR_PRODUCTION_FIX = YES` only if at least one scoped item is a confirmed production regression.
- `054_READY_FOR_TEST_EXPECTATION_UPDATE = YES` only if one or more scoped items are stale tests or test infra issues and no production fix is needed first.
- `054_READY_FOR_FULL_017V2_RERUN = YES` only if:
  - 051 oracle path remains accepted;
  - 052 GREEN remains rejected;
  - no unresolved HIGH production regression remains;
  - the report explicitly says the next run must execute full 017 V2 with per-ID evidence and CL-01..CL-15.

## Report Requirements

Create:

`qa_reports/CORE8_053_REGRESSION_CLASSIFICATION_AND_017V2_RERUN_DECISION_054.md`

The report must include:

- branch and HEAD;
- clean tree status before execution;
- summary of 051 oracle status;
- summary of why 052 GREEN remains invalid;
- classification table for all six scoped items;
- restatement of two already-known non-production failures;
- targeted pytest attempt and output summary;
- final recommended next action.

## Required Footer

Include this footer exactly with filled values:

```text
ASSIGNMENT_ID = CORE8_053_REGRESSION_CLASSIFICATION_AND_017V2_RERUN_DECISION_054
START_HEAD = <sha>
REPORT_COMMIT = <sha-or-PENDING>
051_ORACLE_PATH_ACCEPTED = YES|NO
052_GREEN_VERDICT_VALID = NO
053_AUDIT_ACCEPTED = YES|NO
TARGETED_PYTEST_EXECUTED = YES|NO
SCOPED_ITEMS_TOTAL = 6
PRODUCTION_REGRESSION_COUNT = n
INTENTIONAL_FAIL_CLOSED_HARDENING_COUNT = n
STALE_TEST_EXPECTATION_COUNT = n
TEST_INFRA_OR_MOCK_BUG_COUNT = n
ENVIRONMENT_ONLY_COUNT = n
NEEDS_OWNER_DECISION_COUNT = n
054_READY_FOR_PRODUCTION_FIX = YES|NO
054_READY_FOR_TEST_EXPECTATION_UPDATE = YES|NO
054_READY_FOR_FULL_017V2_RERUN = YES|NO
READY_TO_RESUME_GATE_E = NO
READY_FOR_FRONTEND_FINALIZATION = NO
054_VERDICT = GREEN|RED|BLOCKED
```

`READY_TO_RESUME_GATE_E` must remain `NO` in this assignment. This assignment can only authorize the next 017 V2 rerun, not Gate E itself.

## Completion

Commit and push only the allowed report file, then stop and return:

- report commit SHA;
- concise verdict;
- full report text.
