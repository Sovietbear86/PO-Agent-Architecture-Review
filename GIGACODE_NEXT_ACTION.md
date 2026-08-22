# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly this assignment:

`qa_assignments/CORE8_053_REGRESSION_CLASSIFICATION_AND_017V2_RERUN_DECISION_054.md`

## Report allowlist

Commit and push only:

`qa_reports/CORE8_053_REGRESSION_CLASSIFICATION_AND_017V2_RERUN_DECISION_054.md`

Do not commit JSON, helper scripts, runner changes, wrapper changes, `.env`, credentials, logs, screenshots, historical reports, roadmap edits, production changes, prompts, tests, fixtures, local configuration or AS21/SWTR data.

## Role

You are QA/auditor only.

Do not repair production defects. Do not weaken acceptance rules. Do not run Gate E. Do not use implementation existence as execution evidence. Do not claim GREEN from aggregate counts without per-case evidence.

## Why Assignment 054 exists

Assignment 053 correctly rejected the Assignment 052 GREEN verdict:

- correction loop evidence was only `2/15`, not `15/15`;
- per-ID 017 V2 evidence was incomplete;
- test failures were not classified;
- the full matrix was not proven through production semantic execution.

054 must classify the six behavior-change items listed by 053 and decide whether the next step is a production fix, test expectation update, or a proper full 017 V2 rerun.

## Autonomous execution

The repository owner pre-authorizes this QA audit. Do not ask for confirmation after routine read-only inspection, service restart, targeted test execution, report creation, allowed report commit or allowed report push.

Ask only if continuing requires missing credentials, unavoidable platform approval, write outside the report allowlist, destructive out-of-scope action or scope expansion.

## Required final gate

```text
PRODUCTION_REGRESSION_COUNT = n
STALE_TEST_EXPECTATION_COUNT = n
054_READY_FOR_PRODUCTION_FIX = YES|NO
054_READY_FOR_TEST_EXPECTATION_UPDATE = YES|NO
054_READY_FOR_FULL_017V2_RERUN = YES|NO
READY_TO_RESUME_GATE_E = YES|NO
```

Do not start Gate E.

## Completion

After completing the assignment, commit and push only the allowed report file, then stop and return:

- report commit SHA;
- concise verdict;
- full report text.