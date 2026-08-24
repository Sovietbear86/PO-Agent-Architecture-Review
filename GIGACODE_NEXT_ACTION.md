# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly this assignment:

`qa_assignments/CORE8_PENDING_CLARIFICATION_AND_NEW_TURN_RETEST_064.md`

## Report allowlist

Commit and push only:

`qa_reports/CORE8_PENDING_CLARIFICATION_AND_NEW_TURN_RETEST_064.md`

Do not commit JSON, helper scripts, runner changes, wrapper changes, `.env`, credentials, logs, screenshots, historical reports, roadmap edits, production changes, prompts, tests, fixtures, local configuration or AS21/SWTR data.

## Role

You are QA/tester only.

The owner/developer makes all production and test changes. Do not repair failures, weaken expectations or alter behavior during this assignment.

## Baseline under test

Production session-state fix:

`58ddbb7a12c4a527c906cd4ee9a5b21660ea2cb4`

Regression tests already present:

`po-agent-platform-v2/tests/test_semantic_session_isolation.py`

Your START_HEAD must contain the production fix and the tracked working tree must be clean.

## Purpose

Re-test the two concrete failures found by Assignment 063: pending clarification replay and stale semantic memory on a semantically NEW turn. Also prove A→B→A isolation, cross-session isolation and genuine correction behavior remain intact.

Assignments 060/062 remain paused until 064 is GREEN.

## Autonomous execution

Routine QA actions are pre-authorized. Do not ask for confirmation after branch fetch/pull, clean-tree verification, service restart, test execution, read-only AS21/SWTR queries, report creation, allowed report commit or allowed report push.

Ask only if continuing requires missing credentials, unavoidable platform approval, write outside the report allowlist, destructive out-of-scope action or scope expansion.

## Required final metrics

```text
START_HEAD = <sha>
CONTAINS_FIX_58DDBB7 = YES|NO
CLEAN_TREE_GUARD = PASS|FAIL
UNIT_SESSION_TESTS = x/2 PASS
CLARIFICATION_REPLAY_A1_A2_A3 = PASS|FAIL
A_B_A_ISOLATION = PASS|FAIL
NEW_TURN_ISOLATION = PASS|FAIL
CROSS_SESSION_ISOLATION = PASS|FAIL
GENUINE_CORRECTION = PASS|FAIL|BLOCKED
STALE_SLOT_CONTAMINATION_COUNT = n
REPLAY_CONSUMED_AS_CLARIFICATION_ANSWER_COUNT = n
UNRELATED_SPRINT_SLOT_COUNT = n
HTTP_500_COUNT = n
NEW_REGRESSIONS = n
READY_TO_RESUME_060_AND_062 = YES|NO
064_VERDICT = GREEN|RED|BLOCKED
```

## Completion

After completing Assignment 064, commit and push only the allowed report file, then stop and return report commit SHA, concise verdict and full report text.
