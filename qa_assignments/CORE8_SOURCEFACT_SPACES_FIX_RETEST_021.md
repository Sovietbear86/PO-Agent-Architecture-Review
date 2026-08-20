# QA Assignment 021 — SourceFact `spaces` Fix + Runtime Recovery

GigaCode is TESTER ONLY. Do not modify production code, tests, config values, AS21 data, or roadmap files. Publish only the QA report.

## Goal
Verify the root cause found in Assignment 020 is fixed and the Harness runtime can boot and answer queries without HTTP 500.

## A. SourceFact contract
1. Confirm `SourceFact.SPACES == "spaces"` exists.
2. Confirm `HardenedProductionTaskApiAS21Adapter.source_facts` is fully accepted by `source_facts(adapter)` with no ValueError.
3. Confirm `task-search-product` requires both `tasks` and `spaces` readiness facts.
4. Run `tests/test_source_readiness_spaces.py`.

## B. Runtime bootstrap
Restart Task API and PO Agent from CURRENT HEAD. Capture health response and visible logs.
Required:
- no `ValueError: 'spaces' is not a valid SourceFact`;
- `/api/v1/health` returns 200;
- runtime bundle initializes successfully;
- `/api/v1/query` produces structured responses, not HTTP 500.

## C. Five-query smoke
Run at least:
1. simple task lookup/search;
2. assignee task search;
3. explicit sprint task search using `DMS-SPRNT-1`;
4. product/space search for DMS;
5. golden composite query: `Покажи открытые задачи Гаранина в последнем спринте по DMS`.

For each record HTTP status, Harness status, intent, warnings and evidence/result keys. Do not declare semantic correctness if the result is merely non-500.

## D. Correction smoke
Using the same session as query #5, send `Ты не прав, проверь ещё раз` and verify it is treated as correction/recheck rather than an unrelated fresh task search. Record any clarification question.

## E. Protected regression
Run targeted source-readiness/runtime tests and a lightweight Core-8 smoke. AS21 mutations must remain 0.

## Required report
Publish `qa_reports/CORE8_SOURCEFACT_SPACES_FIX_RETEST_021.md` with footer:

```text
ASSIGNMENT_ID = CORE8_SOURCEFACT_SPACES_FIX_RETEST_021
CURRENT_HEAD = <sha>
SOURCEFACT_SPACES_VALID = YES|NO
PRODUCT_SEARCH_REQUIRES_SPACES = YES|NO
RUNTIME_BOOT_OK = YES|NO
QUERY_HTTP_500_COUNT = N
FIVE_QUERY_NON500 = x/5
GOLDEN_QUERY_EXECUTED = YES|NO
CORRECTION_RECHECK_EXECUTED = YES|NO
NEW_HIGH_PRODUCTION_REGRESSIONS = N
AS21_MUTATIONS_DURING_TEST = 0
READY_TO_RERUN_019 = YES|NO
```

GREEN requires SourceFact/readiness consistency and zero HTTP 500s. Do not attempt to certify full Core-8 correctness here; if GREEN, stop and authorize rerun of 019.