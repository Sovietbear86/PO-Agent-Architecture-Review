# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly:

`qa_assignments/CORE8_SEMANTIC_SLOT_RECOVERY_RETEST_069.md`

## Production fix under test

Owner/developer commit:

`88d602ff006bb5b3af4c3ca5c157a52055f43620`

The fix adds a bounded LLM-first flat-slot recovery pass when the primary semantic frame and audit both return empty task-search slots. Recovery values are accepted only when they are literal spans of the original query; no AS21 identifiers are guessed.

Assignment 068 already established that the empty-slot behavior predates the recently suspected slot-contract commit, so do not continue historical archaeology.

## Role

QA/tester only.

Do not modify production code, prompts, runtime factory, tests, fixtures, credentials, wrappers or AS21/SWTR configuration.

## Mandatory rules

1. Pull/fetch `feat/core8-real-query-hardening-v2` first and record `START_HEAD`.
2. Prove production fix `88d602ff006bb5b3af4c3ca5c157a52055f43620` is an ancestor of the tested HEAD.
3. Start fresh/current-checkout PO Agent and Task API processes; prove module/runtime provenance before testing.
4. Run the existing runtime freshness and SWTR health preflight first.
5. Execute Assignment 069 exactly as written.
6. Live certification uses REAL AS21/SWTR data only. No fake/mock positive data.
7. Run person/product/status/multi-filter/exact-task/sprint probes and repeat each required probe 3 times.
8. Run the genuine-correction control that was not certified by the latest 067 run.
9. Run the targeted automated regression suites specified by 069.
10. Do not repair failures. If a product defect remains, report the first proven failing boundary and STOP.
11. Do not start Assignment 062 or any later assignment.
12. Commit/push only `qa_reports/CORE8_SEMANTIC_SLOT_RECOVERY_RETEST_069.md`, then STOP.

## Required completion summary

Report at minimum:
- START_HEAD;
- production-fix ancestor proof;
- fresh-process/current-checkout proof;
- SWTR health verdict;
- focused semantic query matrix and 3x repeatability;
- semantic slot pass/fail counts;
- genuine-correction verdict;
- automated test counts;
- HTTP 500 count;
- fake/mock source call count;
- new product regressions count;
- Assignment 060 resume/retest verdict;
- READY_FOR_060_FULL_RERUN = YES/NO;
- QA report path;
- QA commit SHA;
- final 069 verdict.

STOP after Assignment 069.