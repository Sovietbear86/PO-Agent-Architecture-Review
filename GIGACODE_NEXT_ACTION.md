# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly this assignment:

`qa_assignments/CORE8_SEMANTIC_SESSION_ISOLATION_RETEST_063.md`

## Report allowlist

Commit and push only:

`qa_reports/CORE8_SEMANTIC_SESSION_ISOLATION_RETEST_063.md`

Do not commit JSON, helper scripts, runner changes, wrapper changes, `.env`, credentials, logs, screenshots, historical reports, roadmap edits, production changes, prompts, tests, fixtures, local configuration or AS21/SWTR data.

## Role

You are QA/tester only.

The owner/developer makes all production and test changes. Do not repair failures, weaken expectations or alter behavior during this assignment.

## Baseline under test

Production session-isolation fix:

`66ce936a3fbc6bb7695639ad5bbdc8ef298136fb`

Regression tests:

`bfd6a67b34d9003732277042510ea2aa75f7966f`

Your START_HEAD must contain both commits and the tracked working tree must be clean.

## Purpose

Validate the session-state corruption fix discovered by Assignment 062. Prove clarification replay idempotency, independent-turn A→B→A isolation, cross-session isolation and preservation of genuine correction behavior.

Assignments 060/062 remain paused until 063 is GREEN.

## Autonomous execution

Routine QA actions are pre-authorized. Do not ask for confirmation after branch fetch/pull, clean-tree verification, service restart, test execution, read-only AS21/SWTR queries, report creation, allowed report commit or allowed report push.

Ask only if continuing requires missing credentials, unavoidable platform approval, write outside the report allowlist, destructive out-of-scope action or scope expansion.

## Required final metrics

```text
START_HEAD = <sha>
CONTAINS_FIX_66CE936 = YES|NO
CONTAINS_TEST_BFD6A67 = YES|NO
CLEAN_TREE_GUARD = PASS|FAIL
UNIT_SESSION_TESTS = x/y PASS
REPEAT_A1_A2_A3 = PASS|FAIL
A_B_A_ISOLATION = PASS|FAIL
CROSS_SESSION_ISOLATION = PASS|FAIL
GENUINE_CORRECTION = PASS|FAIL|BLOCKED
STALE_SLOT_CONTAMINATION_COUNT = n
UNEXPECTED_NEEDS_CLARIFICATION_COUNT = n
NEW_REGRESSIONS = n
READY_TO_RESUME_060_AND_062 = YES|NO
063_VERDICT = GREEN|RED|BLOCKED
```

## Completion

After completing Assignment 063, commit and push only the allowed report file, then stop and return report commit SHA, concise verdict and full report text.
