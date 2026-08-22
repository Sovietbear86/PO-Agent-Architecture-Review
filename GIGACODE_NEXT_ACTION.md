# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly this assignment:

`qa_assignments/CORE8_052_VERDICT_INTEGRITY_AUDIT_053.md`

## Report allowlist

Commit and push only:

`qa_reports/CORE8_052_VERDICT_INTEGRITY_AUDIT_053.md`

Do not commit JSON, helper scripts, runner changes, wrapper changes, `.env`, credentials, logs, screenshots, historical reports, roadmap edits, production changes, prompts, tests, fixtures, local configuration or AS21/SWTR data.

## Role

You are QA/auditor only.

Do not repair production defects. Do not weaken acceptance rules. Do not run Gate E. Do not use implementation existence as execution evidence. Do not claim GREEN from aggregate counts without per-case evidence.

## Why Assignment 053 exists

Assignment 052 reported `052_VERDICT = GREEN` and `READY_TO_RESUME_GATE_E = YES`, but the report appears internally inconsistent:

- 052 footer reports `CORRECTION_LOOP_PASS = 2/15`, while 052 GREEN required 15/15;
- 052 body mentions test failures (`test_core8_real_query_hardening.py = 3/4`, all tests `1099/1108`) but footer claims `FUNCTIONAL_FAIL = 0`;
- 052 appears to use aggregate pytest/corpus summaries rather than complete per-ID 017 V2 matrix evidence;
- CL-03..CL-15 appear marked implemented rather than executed.

053 must audit whether the 052 GREEN verdict is valid before Gate E can resume.

## Autonomous execution

The repository owner pre-authorizes this QA audit. Do not ask for confirmation after routine read-only inspection, report creation, allowed report commit or allowed report push.

Ask only if continuing requires missing credentials, unavoidable platform approval, write outside the report allowlist, destructive out-of-scope action or scope expansion.

## Required final gate

```text
052_GREEN_VERDICT_VALID = YES|NO
052_READY_TO_RESUME_GATE_E_VALID = YES|NO
052_PER_ID_EVIDENCE_COMPLETE = YES|NO
052_CORRECTION_LOOP_15_OF_15_EXECUTED = YES|NO
READY_TO_RESUME_GATE_E = YES|NO
```

If 053 does not validate 052, do not start Gate E.

## Completion

After completing the assignment, commit and push only the allowed report file, then stop and return:

- report commit SHA;
- concise verdict;
- full report text.
