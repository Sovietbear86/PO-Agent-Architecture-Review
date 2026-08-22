# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly this assignment:

`qa_assignments/CORE8_BOUNDED_SWTR_ORACLE_ACCESS_UNBLOCK_RETEST_050.md`

## Report allowlist

Commit and push only:

`qa_reports/CORE8_BOUNDED_SWTR_ORACLE_ACCESS_UNBLOCK_RETEST_050.md`

Do not commit JSON, helper scripts, runner changes, wrapper changes, `.env`, credentials, logs, screenshots, historical reports, roadmap edits, production changes, prompts, tests, fixtures, local configuration or AS21/SWTR data.

## Role

You are QA/tester only.

Do not repair production defects. Do not weaken oracle rules. Do not run full tenant-wide task sync. Do not use PO Agent output as oracle. Do not compare counts only.

## Autonomous execution

The repository owner pre-authorizes this QA batch. Do not ask for confirmation after each routine step, integration call, local service restart, read-only AS21/SWTR query, MCP-SWTR diagnostic, Task API diagnostic, HTTP diagnostic, test command, allowed report commit or allowed report push.

Ask only if continuing requires a missing credential, unavoidable platform approval, write outside the report allowlist, production/source-data/config mutation, destructive out-of-scope action or scope expansion.

## Current purpose

Assignment 049 was blocked because both the Harness path and the adjacent known-good `MyTestProject_1` MCP-SWTR path returned `SWTR_ACCESS_DENIED_ERROR`.

The owner now reports the MCP-SWTR token passthrough problem is fixed and the direct filter for `DMS-SPRNT-2` returns task keys. Assignment 050 must prove the bounded hydrated oracle path before any full 017 V2 rerun.

Required final gate:

```text
ORACLE_PATH_PROVEN = YES
CASE_GARANIN_DMS_SPRINT2_EXACT_SET = PASS
READY_TO_RERUN_017_V2 = YES
```

If 050 is not GREEN, do not run 017 V2 and do not start Gate E.

## Completion

After completing the assignment, commit and push only the allowed report file, then stop and return:

- report commit SHA;
- concise verdict;
- full report text.
