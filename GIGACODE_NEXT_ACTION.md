# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly this assignment:

`qa_assignments/CORE8_TEST_CLEANUP_AND_017V2_RERUN_055.md`

## Report allowlist

Commit and push only:

`qa_reports/CORE8_TEST_CLEANUP_AND_017V2_RERUN_055.md`

Do not commit JSON, helper scripts, runner changes, wrapper changes, `.env`, credentials, logs, screenshots, historical reports, roadmap edits, production changes, prompts, tests, fixtures, local configuration or AS21/SWTR data.

## Role

You are QA/tester only.

Do not repair production defects. Do not weaken acceptance rules. Do not run Gate E directly. Do not use implementation existence as execution evidence. Do not claim GREEN from aggregate counts without per-case evidence.

## Why Assignment 055 Exists

Assignment 051 accepted the bounded SWTR oracle path.

Assignment 052 GREEN was rejected by Assignment 053.

Assignment 054 found no confirmed production regression, but required cleanup of stale test expectations and incomplete mocks before another full 017 V2 run.

ChatGPT/developer has now committed that test cleanup. Assignment 055 must verify the cleanup first, then run full 017 V2 only if targeted cleanup and oracle smoke both pass.

## Autonomous Execution

The repository owner pre-authorizes this QA run. Do not ask for confirmation after routine read-only inspection, service restart, targeted test execution, full acceptance execution, report creation, allowed report commit or allowed report push.

Ask only if continuing requires missing credentials, unavoidable platform approval, write outside the report allowlist, destructive out-of-scope action or scope expansion.

## Required Final Gate

```text
055_TARGETED_CLEANUP_PASS = YES|NO|BLOCKED
055_ORACLE_SMOKE_PASS = YES|NO|BLOCKED
017V2_FULLY_EXECUTED = YES|NO
CORRECTION_LOOP_PASS = x/15
FALSE_GREEN_COUNT = n
SILENT_SLOT_DROP_COUNT = n
NEW_HIGH_PRODUCTION_REGRESSIONS = n
READY_TO_RESUME_GATE_E = YES|NO
055_VERDICT = GREEN|RED|BLOCKED
```

Do not start Gate E.

## Completion

After completing the assignment, commit and push only the allowed report file, then stop and return:

- report commit SHA;
- concise verdict;
- full report text.