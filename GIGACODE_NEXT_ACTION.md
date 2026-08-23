# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly this assignment:

`qa_assignments/CORE8_TASK_API_SEMANTIC_STUB_AND_017V2_RERUN_057.md`

## Report allowlist

Commit and push only:

`qa_reports/CORE8_TASK_API_SEMANTIC_STUB_AND_017V2_RERUN_057.md`

Do not commit JSON, helper scripts, runner changes, wrapper changes, `.env`, credentials, logs, screenshots, historical reports, roadmap edits, production changes, prompts, tests, fixtures, local configuration or AS21/SWTR data.

## Role

You are QA/tester only.

Do not repair production defects. Do not weaken acceptance rules. Do not run Gate E directly. Do not use implementation existence as execution evidence. Do not claim GREEN from aggregate counts without per-case evidence.

## Why Assignment 057 Exists

Assignment 056 passed the task-api coverage guard but targeted tests still failed because pytest had no real LLM semantic model.

ChatGPT/developer fixed this in commit `9f9e7407c4474f7fe9ea1ec4e6fc9ecc267661bf` by keeping `build_runtime_bundle("task-api")` while injecting deterministic conversation-aware semantic frames for unit regression tests only.

Assignment 057 must verify this targeted cleanup, then run oracle smoke and full 017 V2 only if the earlier gates pass.

## Autonomous Execution

The repository owner pre-authorizes this QA run. Do not ask for confirmation after routine read-only inspection, service restart, targeted test execution, oracle smoke, full acceptance execution, report creation, allowed report commit or allowed report push.

Ask only if continuing requires missing credentials, unavoidable platform approval, write outside the report allowlist, destructive out-of-scope action or scope expansion.

## Required Final Gate

```text
057_TASK_API_COVERAGE_GUARD = PASS|FAIL
057_TARGETED_CLEANUP_PASS = YES|NO|BLOCKED
057_ORACLE_SMOKE_PASS = YES|NO|BLOCKED
ENVIRONMENT_TIMEOUT_COUNT = n
017V2_FULLY_EXECUTED = YES|NO
CORRECTION_LOOP_PASS = x/15
FALSE_GREEN_COUNT = n
SILENT_SLOT_DROP_COUNT = n
NEW_HIGH_PRODUCTION_REGRESSIONS = n
READY_TO_RESUME_GATE_E = YES|NO
057_VERDICT = GREEN|RED|BLOCKED
```

Do not start Gate E.

## Completion

After completing the assignment, commit and push only the allowed report file, then stop and return:

- report commit SHA;
- concise verdict;
- full report text.