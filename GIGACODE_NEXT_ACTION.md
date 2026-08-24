# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly this assignment:

`qa_assignments/CORE8_FRESH_HEAD_057_RERUN_058.md`

## Report allowlist

Commit and push only:

`qa_reports/CORE8_FRESH_HEAD_057_RERUN_058.md`

Do not commit JSON, helper scripts, runner changes, wrapper changes, `.env`, credentials, logs, screenshots, historical reports, roadmap edits, production changes, prompts, tests, fixtures, local configuration or AS21/SWTR data.

## Role

You are QA/tester only.

Do not repair production defects. Do not weaken acceptance rules. Do not run Gate E directly. Do not use implementation existence as execution evidence. Do not claim GREEN from aggregate counts without per-case evidence.

## Why Assignment 058 Exists

Assignment 057 is stale and must not be used for release decisions.

Its report started from `af0ad146c7c6b5a493827160504e3c2b1a0f9e8d7c6b5a4`, before the cleanup fix `9f9e7407c4474f7fe9ea1ec4e6fc9ecc267661bf` was present in the working tree. The later merge did not make the already-collected evidence fresh.

Assignment 058 must first prove that execution starts from a fresh branch HEAD containing `9f9e7407c4474f7fe9ea1ec4e6fc9ecc267661bf`, then rerun the targeted cleanup gate, the bounded SWTR oracle smoke and full 017 V2 only if the earlier gates pass.

## Autonomous Execution

The repository owner pre-authorizes this QA run. Do not ask for confirmation after routine read-only inspection, branch fetch/pull, clean-tree verification, service restart, targeted test execution, oracle smoke, full acceptance execution, report creation, allowed report commit or allowed report push.

Ask only if continuing requires missing credentials, unavoidable platform approval, write outside the report allowlist, destructive out-of-scope action or scope expansion.

## Required Final Gate

```text
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
CORRECTION_LOOP_PASS = x/15
FALSE_GREEN_COUNT = n
SILENT_SLOT_DROP_COUNT = n
QUERY_HTTP_500_COUNT = n
NEW_HIGH_PRODUCTION_REGRESSIONS = n
READY_TO_RESUME_GATE_E = YES|NO
READY_FOR_FRONTEND_FINALIZATION = YES|NO
058_VERDICT = GREEN|RED|BLOCKED
```

Do not start Gate E.

## Completion

After completing the assignment, commit and push only the allowed report file, then stop and return:

- report commit SHA;
- concise verdict;
- full report text.
