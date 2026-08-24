# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly this assignment:

`qa_assignments/CORE8_SEMANTIC_CONTRACT_REPAIR_TARGETED_RETEST_060.md`

## Report allowlist

Commit and push only:

`qa_reports/CORE8_SEMANTIC_CONTRACT_REPAIR_TARGETED_RETEST_060.md`

Do not commit JSON, helper scripts, runner changes, wrapper changes, `.env`, credentials, logs, screenshots, historical reports, roadmap edits, production changes, prompts, tests, fixtures, local configuration or AS21/SWTR data.

## Role

You are QA/tester only.

The owner/developer makes all production and test changes. You must not repair failures, change semantic prompts, weaken acceptance rules or edit QA infrastructure during this assignment.

## Baseline under test

Production semantic fix:

`9ba842e49ed5406e8f456893f2e533edf0a7f258`

Contract tests:

`81fce0e218edbf08cdaf5d571a8b145ce407480d`

Your START_HEAD must contain both commits and the tracked working tree must be clean.

## Purpose

Validate the new semantic slot-contract repair against the exact 19 PRODUCT_FAIL cases from QA026 V3/V4, plus semantic unit tests, independent SWTR oracle anchors and a representative regression sample.

Do not run the full 42-case QA026 in this assignment. Do not fix any failure.

## Autonomous Execution

Routine QA actions are pre-authorized. Do not ask for confirmation after read-only inspection, branch fetch/pull, clean-tree verification, service restart, test execution, direct read-only SWTR oracle checks, report creation, allowed report commit or allowed report push.

Ask only if continuing requires missing credentials, unavoidable platform approval, write outside the report allowlist, destructive out-of-scope action or scope expansion.

## Required final metrics

```text
START_HEAD = <sha>
CONTAINS_PRODUCTION_FIX_9BA842E = YES|NO
CONTAINS_CONTRACT_TESTS_81FCE0E = YES|NO
CLEAN_TREE_GUARD = PASS|FAIL
SEMANTIC_UNIT_TESTS = x/y PASS
PERSON_CLUSTER = x/12 PASS
STATUS_CLUSTER = x/4 PASS
PRODUCT_CLUSTER = x/3 PASS
TOTAL_RECOVERED = x/19
PRODUCT_FAIL_REMAINING = n
NEW_REGRESSIONS = n
SOURCE_ORACLE = PASS|FAIL|BLOCKED
SILENT_SLOT_DROP_COUNT = n
UNSAFE_FULL_QUERY_SLOT_COUNT = n
DERIVED_LOGIN_WITHOUT_PERSON_RAW_COUNT = n
READY_FOR_FULL_QA026 = YES|NO
060_VERDICT = GREEN|RED|BLOCKED
```

## Completion

After completing Assignment 060, commit and push only the allowed report file, then stop and return:

- report commit SHA;
- concise verdict;
- full report text.