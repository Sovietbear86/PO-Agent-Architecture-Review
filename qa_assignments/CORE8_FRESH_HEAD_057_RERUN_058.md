# Assignment 058 — Fresh-HEAD 057 Rerun

Repository:
`Sovietbear86/PO-Agent-Architecture-Review`

Branch:
`feat/core8-real-query-hardening-v2`

## Role

You are QA/tester only.

Do not modify production code, tests, prompts, fixtures, runners, `.env`, credentials, wrapper scripts, AS21/SWTR data, learning state, historical reports, or configuration.

Commit and push only:

`qa_reports/CORE8_FRESH_HEAD_057_RERUN_058.md`

## Why This Assignment Exists

Assignment 057 was executed from stale start HEAD `af0ad14...` and did not actually test the fix commit:

`9f9e7407c4474f7fe9ea1ec4e6fc9ecc267661bf`

The report was then merged with newer branch state, but its test evidence remained stale. Therefore the 057 report is not valid evidence for the current branch.

## Mandatory Fresh-HEAD Guard

Before any test execution:

1. Fetch remote branch.
2. Ensure local working tree is clean.
3. Update to current `origin/feat/core8-real-query-hardening-v2`.
4. Record actual `START_HEAD`.
5. Verify `START_HEAD` contains commit:

   `9f9e7407c4474f7fe9ea1ec4e6fc9ecc267661bf`

6. Verify `po-agent-platform-v2/tests/test_final_architecture_regressions.py` contains `ScriptedConversationInterpreter` and still uses:

   - `build_runtime_bundle("task-api", semantic_interpreter=interpreter)` in both architecture tests;
   - `response.data["adapter"] == "task-api"` in the portfolio test.

If any fresh-head guard fails, do not run tests. Set `058_FRESH_HEAD_GUARD = FAIL`, commit the report, and stop.

## Autonomous Execution

The repository owner pre-authorizes this QA run. Do not ask for confirmation after routine read-only inspection, branch update, service restart, targeted test execution, oracle smoke, full acceptance execution, report creation, allowed report commit, or allowed report push.

Ask only if continuing requires missing credentials, unavoidable platform approval, write outside the report allowlist, destructive action beyond ordinary branch synchronization, scope expansion, or changing production/test code.

## Step 1 — Re-run 057 Targeted Cleanup on Fresh HEAD

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

If any targeted test fails, stop. Record exact failure output and classification.

## Step 2 — Oracle Smoke

If targeted cleanup passes:

- restart Task API and PO Agent from fresh HEAD;
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

`qa_reports/CORE8_FRESH_HEAD_057_RERUN_058.md`

Include:

- branch and actual START_HEAD;
- proof that START_HEAD contains `9f9e7407c4474f7fe9ea1ec4e6fc9ecc267661bf`;
- stale-report explanation for 057;
- fresh-head guard evidence;
- targeted pytest output;
- oracle smoke evidence or timeout evidence;
- full 017 V2 evidence if executed.

## Required Footer

```text
ASSIGNMENT_ID = CORE8_FRESH_HEAD_057_RERUN_058
START_HEAD = <sha>
REPORT_COMMIT = <sha-or-PENDING>
CLEAN_TREE_GUARD = PASS|FAIL
PRODUCTION_CODE_MODIFIED_BY_QA = NO
058_FRESH_HEAD_GUARD = PASS|FAIL
CONTAINS_FIX_9F9E740 = YES|NO
057_REPORT_STALE = YES
058_TARGETED_CLEANUP_PASS = YES|NO|BLOCKED
058_ORACLE_SMOKE_PASS = YES|NO|BLOCKED
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
058_VERDICT = GREEN|RED|BLOCKED
```

`READY_TO_RESUME_GATE_E = YES` is allowed only if full 017 V2 is fully executed with complete evidence and all gates are GREEN.

## Completion

Commit and push only the allowed report file, then stop and return:

- report commit SHA;
- concise verdict;
- full report text.
