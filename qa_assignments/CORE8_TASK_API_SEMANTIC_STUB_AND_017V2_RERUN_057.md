# Assignment 057 — Task-API Semantic Stub Retest and 017 V2 Rerun

Repository:
`Sovietbear86/PO-Agent-Architecture-Review`

Branch:
`feat/core8-real-query-hardening-v2`

Start from current branch HEAD.

## Role

You are QA/tester only.

Do not modify production code, tests, prompts, fixtures, runners, `.env`, credentials, wrapper scripts, AS21/SWTR data, learning state, historical reports, or configuration.

Commit and push only:

`qa_reports/CORE8_TASK_API_SEMANTIC_STUB_AND_017V2_RERUN_057.md`

## Autonomous Execution

The repository owner pre-authorizes this QA run. Do not ask for confirmation after routine read-only inspection, service restart, targeted test execution, oracle smoke, full acceptance execution, report creation, allowed report commit, or allowed report push.

Ask only if continuing requires missing credentials, unavoidable platform approval, write outside the report allowlist, destructive action, scope expansion, or changing production/test code.

## Background

Assignment 056 verified that task-api architecture coverage was restored, but targeted tests still failed because pytest had no real LLM semantic model.

ChatGPT/developer fixed this in:

`9f9e7407c4474f7fe9ea1ec4e6fc9ecc267661bf`

The fix keeps `build_runtime_bundle("task-api")` and task-api adapter coverage, but injects a deterministic `ConversationAwareSemanticInterpreter`-compatible semantic frame provider for the two unit regression tests. This is allowed for unit tests only. It is not allowed for acceptance/oracle/full 017 V2.

## Guard — Task-API Coverage and No Fake Acceptance

Before tests, verify:

1. `test_runtime_factory_runtime_records_production_execution_history` uses `build_runtime_bundle("task-api", semantic_interpreter=...)`.
2. `test_portfolio_overview_never_labels_task_api_data_as_fake` uses `build_runtime_bundle("task-api", semantic_interpreter=...)`.
3. The portfolio test asserts `response.data["adapter"] == "task-api"`.
4. These two unit tests may use deterministic semantic frames, but must not use fake adapter mode.
5. Acceptance/oracle/full 017 V2 must use production semantic interpreter and real AS21/SWTR, not deterministic stubs.

If guard fails, stop and report `057_TASK_API_COVERAGE_GUARD = FAIL`.

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

If any targeted test fails, do not run full 017 V2. Record exact failure and stop.

## Step 2 — Production Oracle Smoke

If targeted cleanup passes:

- restart Task API and PO Agent from current HEAD;
- verify health says adapter `task-api`, semantic mode production/Qwen LLM, source healthy;
- run 051-style bounded SWTR oracle smoke with real AS21/SWTR;
- prove DMS-SPRNT-2 bounded source, per-task hydration, Garanin exact-set, invalid sprint fail-closed.

If service query times out, record exact request, timeout seconds, elapsed time, logs, and classify as environment timeout only if health is otherwise good and no code exception exists.

## Step 3 — Full 017 V2

If targeted cleanup and oracle smoke pass, run:

`qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`

Mandatory:

- production semantic interpreter;
- real AS21/SWTR;
- independent oracle;
- exact key-set comparisons;
- complete per-ID evidence;
- all CL-01..CL-15 executed;
- all failures classified;
- no fake adapter/stub for acceptance verdicts;
- no GREEN from aggregate counts only.

## Report Requirements

Create:

`qa_reports/CORE8_TASK_API_SEMANTIC_STUB_AND_017V2_RERUN_057.md`

## Required Footer

```text
ASSIGNMENT_ID = CORE8_TASK_API_SEMANTIC_STUB_AND_017V2_RERUN_057
START_HEAD = <sha>
REPORT_COMMIT = <sha-or-PENDING>
CLEAN_TREE_GUARD = PASS|FAIL
PRODUCTION_CODE_MODIFIED_BY_QA = NO
057_TASK_API_COVERAGE_GUARD = PASS|FAIL
057_TARGETED_CLEANUP_PASS = YES|NO|BLOCKED
057_ORACLE_SMOKE_PASS = YES|NO|BLOCKED
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
057_VERDICT = GREEN|RED|BLOCKED
```

`READY_TO_RESUME_GATE_E = YES` is allowed only if full 017 V2 is fully executed with complete evidence and all gates are GREEN.

## Completion

Commit and push only the allowed report file, then stop and return:

- report commit SHA;
- concise verdict;
- full report text.
