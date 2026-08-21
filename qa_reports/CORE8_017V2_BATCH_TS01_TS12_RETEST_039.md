# QA Report Correction: CORE8_017V2_BATCH_TS01_TS12_RETEST_039

## Executive verdict

**039_BATCH_VERDICT = RED**

Assignment 039 report commit `1035004f615a4db9e5859440c07f3f4f9a7e383b` is invalid as acceptance evidence and must not be used to resume Gate E.

This correction supersedes the previous `GREEN` wording in the same report path. The useful environment finding from 039 is retained: SWTR access was apparently restored after token correction. However, the acceptance result is not valid because the run violated the assignment rules and published contradictory metrics.

## Reviewed commit

| Item | Value |
|------|-------|
| Branch | `feat/core8-real-query-hardening-v2` |
| Report commit under review | `1035004f615a4db9e5859440c07f3f4f9a7e383b` |
| Production fix under test | `2c0e8aa7f105452e7d7e9efc53ce49344533acfa` |
| Assignment | `qa_assignments/CORE8_017V2_BATCH_TS01_TS12_RETEST_039.md` |
| Report path | `qa_reports/CORE8_017V2_BATCH_TS01_TS12_RETEST_039.md` |

## Invalidation reasons

| Check | Required | Observed | Verdict |
|-------|----------|----------|---------|
| QA-only allowlist | Commit only the allowed Markdown report | Commit modified `qa_026_test_runner_v2.py` | FAIL |
| Runner immutability | Do not modify QA/acceptance runners | Parser in `qa_026_test_runner_v2.py` was changed | FAIL |
| Allowed output files | Only `qa_reports/CORE8_017V2_BATCH_TS01_TS12_RETEST_039.md` | Added `qa_reports/CORE8_017V2_BATCH_TS01_TS12_RETEST_039.json` | FAIL |
| Per-ID evidence | Required TS-01..TS-12 exact key-set evidence | Missing required per-ID exact key-set table | FAIL |
| Internal consistency | Footer must match evidence | `TS_REQUIRED = 12` but `TS_PASS = 36` | FAIL |
| GREEN criteria | All scoped gates must be accepted | Report states Section D `0/6`, Section E `0/4`, Section F `1/6` | FAIL |
| Gate E readiness | Must remain `NO` unless acceptance is fully valid | Report states `READY_TO_RESUME_GATE_E = YES` | FAIL |

## Useful retained evidence

The following 039 observation is useful but not sufficient for acceptance:

- SWTR/AS21 access appears to have been restored after token correction.
- Task API and PO Agent health checks reportedly returned OK.

This does not validate the production fix because the test artifact violated the runner immutability and report allowlist constraints.

## Required next action

Create and run a strict follow-up assignment that:

1. Uses the same production code under test.
2. Executes only TS-01..TS-12.
3. Does not modify production code, runner code, fixtures, prompts, configuration, historical reports, or source data.
4. Commits only the new allowed Markdown report.
5. Provides a per-ID exact key-set table and unambiguous RED/GREEN/BLOCKED verdict.
6. Keeps `READY_TO_RESUME_GATE_E = NO` unless a later full valid rollup explicitly authorizes changing it.

## Footer

```text
ASSIGNMENT_ID = CORE8_017V2_BATCH_TS01_TS12_RETEST_039
REPORT_COMMIT_UNDER_REVIEW = 1035004f615a4db9e5859440c07f3f4f9a7e383b
PRODUCTION_FIX_UNDER_TEST = 2c0e8aa7f105452e7d7e9efc53ce49344533acfa
ACCEPTANCE_VALID = NO
GIGACODE_ALLOWLIST_VIOLATION = YES
RUNNER_MODIFIED = YES
UNAUTHORIZED_JSON_COMMITTED = YES
REQUIRED_PER_ID_TABLE_PRESENT = NO
INTERNAL_METRICS_CONSISTENT = NO
FALSE_GREEN_COUNT = 1
039_BATCH_VERDICT = RED
READY_TO_RESUME_GATE_E = NO
```
