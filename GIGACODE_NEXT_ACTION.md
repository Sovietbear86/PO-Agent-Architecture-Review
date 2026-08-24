# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly this assignment:

`qa_assignments/CORE8_SAME_SESSION_IDEMPOTENCY_RETEST_061.md`

## Report allowlist

Commit and push only:

`qa_reports/CORE8_SAME_SESSION_IDEMPOTENCY_RETEST_061.md`

Do not commit JSON, helper scripts, runner changes, wrapper changes, `.env`, credentials, logs, screenshots, historical reports, roadmap edits, production changes, prompts, tests, fixtures, local configuration or AS21/SWTR data.

## Role

You are QA/tester only.

The owner/developer makes all production and test changes. Do not repair failures or alter behavior during this assignment.

## Baseline under test

Production fix:

`76ed1ada782118bd10567cc19fa40e9a2857d4e5`

Unit coverage:

`e5444c7d2b5ad8ef0def8a53fb2e3fc230b69182`

Your START_HEAD must contain both commits and the tracked working tree must be clean.

## Purpose

Validate that exact repeated standalone requests in one session are idempotent reruns and never become semantic correction clarifications, while genuine correction behavior remains intact.

Assignment 060 is paused until 061 is GREEN.

## Autonomous execution

Routine QA actions are pre-authorized. Do not ask for confirmation after branch fetch/pull, clean-tree verification, service restart, test execution, read-only AS21/SWTR queries, report creation, allowed report commit or allowed report push.

Ask only if continuing requires missing credentials, unavoidable platform approval, write outside the report allowlist, destructive out-of-scope action or scope expansion.

## Required final metrics

```text
START_HEAD = <sha>
CONTAINS_FIX_76ED1AD = YES|NO
CONTAINS_TEST_E5444C7 = YES|NO
CLEAN_TREE_GUARD = PASS|FAIL
UNIT_GATE = x/y PASS
SAME_SESSION_REPEAT = x/3 PASS
NORMALIZED_REPEAT = x/2 PASS
FRESH_SESSION_CONTROL = x/3 PASS
SEMANTIC_CORRECTION_CLARIFICATION_ON_REPEAT_COUNT = n
INTENT_LOSS_ON_REPEAT_COUNT = n
SKILL_LOSS_ON_REPEAT_COUNT = n
HTTP_500_COUNT = n
GENUINE_CORRECTION_REGRESSION = PASS|FAIL|BLOCKED
READY_TO_RESUME_ASSIGNMENT_060 = YES|NO
061_VERDICT = GREEN|RED|BLOCKED
```

## Completion

After completing Assignment 061, commit and push only the allowed report file, then stop and return report commit SHA, concise verdict and full report text.
