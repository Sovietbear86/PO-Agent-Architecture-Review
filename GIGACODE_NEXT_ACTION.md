# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly this assignment:

`qa_assignments/CORE8_DETERMINISTIC_CLARIFICATION_REPLAY_RETEST_066.md`

## Report allowlist

Commit and push only:

`qa_reports/CORE8_DETERMINISTIC_CLARIFICATION_REPLAY_RETEST_066.md`

Do not commit JSON, helper scripts, runner changes, wrapper changes, `.env`, credentials, logs, screenshots, historical reports, roadmap edits, production changes, prompts, tests, fixtures, local configuration or AS21/SWTR data.

## Role

You are QA/tester only.

The owner/developer makes all production and test changes. Do not repair failures, weaken expectations or alter behavior during this assignment.

## Baseline under test

Production clarification replay fix:

`64f4e254446262d4e08c5917133a3e3b926561c8`

Regression contract:

`603b282a66f62b02d339032e67f4c6fd85d77f6f`

Your START_HEAD must contain both commits and the tracked working tree must be clean.

## Mandatory environment guard

Before executing tests, prove Python imports the current local checkout and that `/private/tmp/PO-Agent-Architecture-Review` is absent from `sys.path`. If the guard fails, stop with BLOCKED instead of testing stale code.

## Purpose

Validate deterministic replay of an already-open pending clarification without re-running semantic interpretation/grounding, while preserving independent-turn isolation and genuine correction behavior.

Assignments 060/062 remain paused until 066 is GREEN.

## Autonomous execution

Routine QA actions are pre-authorized. Do not ask for confirmation after branch fetch/pull, clean-tree verification, environment guard, service restart, test execution, read-only AS21/SWTR queries, report creation, allowed report commit or allowed report push.

Ask only if continuing requires missing credentials, unavoidable platform approval, write outside the report allowlist, destructive out-of-scope action or scope expansion.

## Completion

After completing Assignment 066, commit and push only the allowed report file, then stop and return report commit SHA, concise verdict and full report text.
