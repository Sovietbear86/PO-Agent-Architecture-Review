# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly this assignment:

`qa_assignments/CORE8_017V2_FULL_CLEAN_ORACLE_RERUN_052.md`

## Report allowlist

Commit and push only:

`qa_reports/CORE8_017V2_FULL_CLEAN_ORACLE_RERUN_052.md`

Do not commit JSON, helper scripts, runner changes, wrapper changes, `.env`, credentials, logs, screenshots, historical reports, roadmap edits, production changes, prompts, tests, fixtures, local configuration or AS21/SWTR data.

## Role

You are QA/tester only.

Do not repair production defects. Do not weaken oracle rules. Do not run full tenant-wide task sync. Do not use PO Agent output as oracle. Do not compare counts only. Do not claim GREEN from aggregate counts without per-case evidence.

## Why Assignment 052 exists

Assignment 051 is accepted as the bounded oracle unblock gate:

```text
CLEAN_TREE_GUARD = PASS
ORACLE_PATH_PROVEN = YES
CASE_GARANIN_DMS_SPRINT2_EXACT_SET = PASS
LLM_TIMEOUT_COUNT = 0
READY_TO_RERUN_017_V2 = YES
```

052 resumes the full 017 V2/Core-8 real-query hardening rerun. It must avoid the historical 033/035 evidence problems: no partial matrix, no inconsistent totals, no GREEN while any required case is FAIL/BLOCKED/NOT_EXECUTED.

## Mandatory clean-tree guard

Before starting services or matrix execution, run:

```bash
git status --short
git diff --name-only
git diff --cached --name-only
```

If there are unstaged or staged tracked changes in production code, tests, prompts, runners, wrappers, config or roadmap files, do not continue the full rerun. Write the allowed 052 report with `052_VERDICT = BLOCKED`, include the exact changed file list, commit only the report and stop.

Ignored/untracked local secret files such as `.env` may exist but must not be committed, printed or pasted. External MCP-SWTR runtime files outside this repository may be used as environment setup evidence only if their secret values are redacted. Untracked repo-local helper scripts/wrappers must not be runtime dependencies.

## Autonomous execution

The repository owner pre-authorizes this QA batch. Do not ask for confirmation after each routine step, integration call, local service restart, read-only AS21/SWTR query, MCP-SWTR diagnostic, Task API diagnostic, HTTP diagnostic, test command, allowed report commit or allowed report push.

Ask only if continuing requires a missing credential, unavoidable platform approval, write outside the report allowlist, production/source-data/config mutation, destructive out-of-scope action or scope expansion.

## Required final gate

```text
017V2_FULLY_EXECUTED = YES
FUNCTIONAL_FAIL = 0
FUNCTIONAL_NOT_EXECUTED = 0
CORRECTION_LOOP_PASS = 15/15
FALSE_GREEN_COUNT = 0
SILENT_SLOT_DROP_COUNT = 0
QUERY_HTTP_500_COUNT = 0
EVIDENCE_CONSISTENCY_AUDIT = PASS
READY_TO_RESUME_GATE_E = YES
```

If 052 is not GREEN, do not start Gate E.

## Completion

After completing the assignment, commit and push only the allowed report file, then stop and return:

- report commit SHA;
- concise verdict;
- full report text.
