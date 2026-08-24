# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly this assignment:

`qa_assignments/CORE8_FRESH_PROCESS_CLARIFICATION_REPLAY_RETEST_067.md`

## Report allowlist

Commit and push only:

`qa_reports/CORE8_FRESH_PROCESS_CLARIFICATION_REPLAY_RETEST_067.md`

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

## Mandatory process provenance guard

QA 066 proved current CLI imports and unit tests were correct, but did not prove the already-running FastAPI/uvicorn service had been restarted after the fix. Assignment 067 MUST stop the old service, prove it is down, and launch a fresh PO Agent process from the current checkout before any live query.

If fresh-process provenance cannot be proven, stop with BLOCKED instead of producing a product RED.

## Purpose

Distinguish a genuine production clarification-replay defect from a stale in-memory service process. Validate the live `/api/v1/query` path only after a proven fresh restart.

Assignments 060/062 remain paused until 067 is GREEN.

## Autonomous execution

Routine QA actions are pre-authorized. Do not ask for confirmation after branch fetch/pull, clean-tree verification, environment/import guard, stopping/restarting the local PO Agent service, health verification, read-only AS21/SWTR queries, test execution, report creation, allowed report commit or allowed report push.

Ask only if continuing requires missing credentials, unavoidable platform approval, write outside the report allowlist, destructive out-of-scope action or scope expansion.

## Completion

After completing Assignment 067, commit and push only the allowed report file, then stop and return report commit SHA, concise verdict and full report text.
