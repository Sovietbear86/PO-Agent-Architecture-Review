# Assignment 034 — 017 V2 Verdict Integrity and Complete Matrix Retest

## Purpose

Assignment 033 produced a report at:

`qa_reports/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2_RERUN_033.md`

Report commit:

`7a46762fd02cf43633e4fb5c18af2582941d5366`

That report declares:

```text
CORE8_REAL_QUERY_HARDENING_GREEN = YES
READY_TO_RESUME_GATE_E = YES
```

But the same report also states:

```text
TOTAL_FUNCTIONAL_TESTS = 36
FUNCTIONAL_PASS = 28
FUNCTIONAL_FAIL = 8
CORRECTION_LOOP_PASS = 8/15
```

This is self-contradictory against the canonical 017 V2 GREEN rule. Assignment 034 must perform a strict verdict-integrity review and, if required, a complete rerun of 017 V2. GigaCode is QA/tester only.

## Repository

Repository:

`Sovietbear86/PO-Agent-Architecture-Review`

Branch:

`feat/core8-real-query-hardening-v2`

Expected report:

`qa_reports/CORE8_017V2_VERDICT_INTEGRITY_RETEST_034.md`

Do not overwrite historical reports:

- `qa_reports/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
- `qa_reports/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2_RERUN_033.md`

## Mandatory Git preflight

Before starting services or tests:

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `git rev-parse HEAD` as `START_HEAD`.
4. Re-read `GIGACODE_NEXT_ACTION.md` and this assignment from `START_HEAD`.
5. Read all files below completely:
   - `qa_assignments/CORE8_017V2_VERDICT_INTEGRITY_RETEST_034.md`
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017.md`
   - `qa_assignments/CORE8_CORRECTION_LOOP_ADDENDUM_017A.md`
   - `qa_reports/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2_RERUN_033.md`

Verify required ancestor commits:

```bash
git merge-base --is-ancestor 319ae1e85311f3123c44c2dd0118b843172aef4d "$START_HEAD"
git merge-base --is-ancestor 940ee44939dcbca14a7583e167b096525f0e509f "$START_HEAD"
git merge-base --is-ancestor cc780219c4b29f5d0dd37e929c16ff528f1508f0 "$START_HEAD"
git merge-base --is-ancestor 7a46762fd02cf43633e4fb5c18af2582941d5366 "$START_HEAD"
```

If any check fails, write the 034 report with `034_VERDICT = BLOCKED`, exact mismatch evidence, and stop.

## Autonomous execution — no step-by-step confirmation

The repository owner has pre-authorized the complete QA workflow defined by this entrypoint and the active assignment. Execute it end to end without asking for confirmation after each step or before each integration call.

No additional conversational confirmation is required for read-only AS21/SWTR calls, the configured semantic LLM, local service restart/health checks, HTTP diagnostics, test runs, `git switch`, `git pull --ff-only`, Git inspection, or commit/push of the explicitly allowed QA report.

Do not pause with questions such as “continue?”, “run the integration?”, “restart the service?” or “commit the report?”. Ask only if continuing requires an unconfigured credential/permission, an unavoidable platform approval, a write outside the report allowlist, a production/source-data/configuration mutation, a destructive out-of-scope action, or a material scope expansion. Consolidate unavoidable prompts to the minimum number possible.

## Fixed role and prohibitions

GigaCode is QA/tester only.

Do not modify:

- production code;
- prompts;
- adapters;
- tests;
- fixtures;
- acceptance runners;
- configuration;
- AS21/SWTR data;
- learning state;
- historical reports;
- roadmap files.

Do not repair discovered defects. Do not weaken or reinterpret the oracle to make the gate GREEN.

## Part 1 — Mandatory verdict-integrity review of 033

Review the 033 report against the canonical 017 V2 final GREEN rule.

At minimum, answer with evidence:

1. Can `CORE8_REAL_QUERY_HARDENING_GREEN = YES` be valid when `FUNCTIONAL_FAIL = 8`?
2. Can `CORE8_REAL_QUERY_HARDENING_GREEN = YES` be valid when `CORRECTION_LOOP_PASS = 8/15`?
3. Can `READY_TO_RESUME_GATE_E = YES` be valid if any required functional tests failed or were not executed?
4. Did 033 execute all required functional categories, or only the 36 `task_search` cases?
5. Did 033 execute all CL-01..CL-15, or only a subset?
6. Did 033 provide an explicitly approved live-data-drift exception for every non-pass? If not, do not count the case as GREEN.

If the 033 GREEN verdict is invalid, state:

```text
033_GREEN_VERDICT_VALID = NO
033_READY_TO_RESUME_GATE_E_VALID = NO
```

## Part 2 — Complete 017 V2 scope accounting

The canonical functional matrix contains at least 107 functional scenarios:

```text
task_search TS-01..TS-36 = 36
task_summary SUM-01..SUM-08 = 8
task_quality Q-01..Q-08 = 8
sprint_health SH-01..SH-10 = 10
velocity V-01..V-08 = 8
team_workload TW-01..TW-10 = 10
competency_match CM-01..CM-09 = 9
release_health RH-01..RH-10 = 10
cross-skill X-01..X-08 = 8
TOTAL_FUNCTIONAL_REQUIRED_MIN = 107
```

The correction/recheck addendum contains:

```text
CL-01..CL-15 = 15
```

For the 034 report, produce a complete scope-accounting table with every required ID:

- EXECUTED;
- PASS;
- FAIL;
- BLOCKED;
- NOT_EXECUTED;
- CLARIFICATION_PASS, only when clarification is the expected safe behavior and the question is targeted;
- LIVE_DATA_DRIFT_EXCEPTION, only with explicit source evidence and justification.

Clarification is not automatically a fail. But if the report footer counts a case as `FUNCTIONAL_FAIL`, the overall GREEN verdict must be `NO`.

## Part 3 — Complete rerun if 033 is incomplete or invalid

If 033 did not execute the complete canonical matrix, rerun 017 V2 completely and unchanged from `START_HEAD`.

Use:

- real AS21/SWTR;
- `PO_AGENT_AS21_MODE=task-api`;
- working semantic LLM endpoint with `/openai/v1`;
- production semantic interpreter;
- production entity resolver;
- production correction runtime.

Restart Task API and PO Agent from `START_HEAD`. Include old/new PIDs, ports, commands and health evidence.

Do not use `FakeAS21Adapter` for acceptance evidence.

If services cannot be restarted because of environment limits, do not report production FAIL. Report `034_VERDICT = BLOCKED`, exact manual restart commands, and stop.

## Part 4 — Hard GREEN rule for 034

`034_VERDICT = GREEN`, `CORE8_REAL_QUERY_HARDENING_GREEN = YES` and `READY_TO_RESUME_GATE_E = YES` are allowed only if all are true:

- 033 verdict-integrity review passes, or a complete 034 rerun supersedes 033;
- all required functional IDs are accounted for;
- `TOTAL_FUNCTIONAL_TESTS >= 107`;
- `FUNCTIONAL_FAIL = 0`;
- `FUNCTIONAL_NOT_EXECUTED = 0`;
- every CL-01..CL-15 is accounted for;
- `CORRECTION_LOOP_PASS = 15/15`;
- `ORACLE_PREFLIGHT_PASS = YES`;
- `KNOWN_POSITIVE_DMS_GARANIN_ANCHORS_VERIFIED = YES`;
- `ORACLE_INDEPENDENCE_PASS = YES`;
- `FALSE_EMPTY_HIGH_COUNT = 0`;
- `FALSE_GREEN_HIGH_COUNT = 0`;
- `SOURCE_CONTRACT_OR_GROUNDING_DEFECTS = 0`;
- `NEW_HIGH_PRODUCTION_REGRESSIONS = 0`;
- `AS21_MUTATIONS_DURING_TEST = 0`.

If any condition is not satisfied, the correct verdict is RED or BLOCKED, not GREEN.

## Required report

Create:

`qa_reports/CORE8_017V2_VERDICT_INTEGRITY_RETEST_034.md`

The report must contain:

- branch and `START_HEAD`;
- ancestor verification;
- verdict-integrity review of 033;
- explicit statement whether 033 GREEN is accepted or rejected;
- service restart evidence if a rerun was performed;
- complete scope-accounting table for all 107+ functional scenarios;
- complete CL-01..CL-15 accounting;
- oracle/source-contract evidence;
- exact set diffs for factual task-set queries;
- defect/blocker ledger;
- final decision for Gate E.

Footer:

```text
ASSIGNMENT_ID = CORE8_017V2_VERDICT_INTEGRITY_RETEST_034
CURRENT_HEAD = <sha>
033_REPORT_COMMIT = 7a46762fd02cf43633e4fb5c18af2582941d5366
033_GREEN_VERDICT_VALID = YES|NO
033_READY_TO_RESUME_GATE_E_VALID = YES|NO
034_RERUN_EXECUTED = YES|NO
TOTAL_FUNCTIONAL_REQUIRED_MIN = 107
TOTAL_FUNCTIONAL_TESTS = N
FUNCTIONAL_PASS = N
FUNCTIONAL_FAIL = N
FUNCTIONAL_NOT_EXECUTED = N
CORRECTION_LOOP_PASS = x/15
ORACLE_PREFLIGHT_PASS = YES|NO
KNOWN_POSITIVE_DMS_GARANIN_ANCHORS_VERIFIED = YES|NO
ORACLE_INDEPENDENCE_PASS = YES|NO
FALSE_EMPTY_HIGH_COUNT = N
FALSE_GREEN_HIGH_COUNT = N
SOURCE_CONTRACT_OR_GROUNDING_DEFECTS = N
NEW_HIGH_PRODUCTION_REGRESSIONS = N
AS21_MUTATIONS_DURING_TEST = 0
CORE8_REAL_QUERY_HARDENING_GREEN = YES|NO
READY_TO_RESUME_GATE_E = YES|NO
034_VERDICT = GREEN|RED|BLOCKED
```

## Commit and push

Commit and push only:

`qa_reports/CORE8_017V2_VERDICT_INTEGRITY_RETEST_034.md`

Before commit:

```bash
git add -- qa_reports/CORE8_017V2_VERDICT_INTEGRITY_RETEST_034.md
git diff --cached --name-only
```

The staged file list must contain exactly the allowed 034 report.

Commit subject must start with:

`qa: CORE8_017V2_VERDICT_INTEGRITY_RETEST_034`

After push, stop and return:

1. report commit SHA;
2. final verdict;
3. complete report contents.
