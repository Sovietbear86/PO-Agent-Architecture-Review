# QA Report: CORE8_017V2_BATCH_TS01_TS12_RETEST_038

## Executive Verdict

**038_BATCH_VERDICT = RED**

This report records the actual Assignment 038 retest evidence collected after production fix `6cb0ad7fa175863f8c8d0807a1504fe1e35bd6aa`.

Report hygiene note: GigaCode first wrote this retest into historical `CORE8_017V2_BATCH_TS01_TS12_037.md`. The historical 037 report was later restored. This 038 file preserves the actual rerun evidence from commit `01ace96683a7e8fad88dbc1590450af1fd2bb356` with corrected 038 identifiers.

## Environment / HEAD

| Item | Value |
|------|-------|
| Branch | `feat/core8-real-query-hardening-v2` |
| START_HEAD / CURRENT_HEAD | `941e5f1aa1d99199bd79ccbf0c171043836f9dd6` |
| Production fix under test | `6cb0ad7fa175863f8c8d0807a1504fe1e35bd6aa` |
| Previous 037 report commit | `0a604d956418ebec2941aadec0511a70ac9d1478` |
| Canonical spec | `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md` |
| Batch scope | TS-01..TS-12 |

## QA runner corrections made before final rerun

The local QA helper initially produced unreliable evidence. GigaCode corrected the helper locally and reran the batch:

1. Fresh `session_id` per TS case to avoid session-state contamination.
2. Correct PO Agent endpoint on port 8004 instead of Task API port 8003.
3. Correct top-level `response.status` extraction.
4. Expanded task-key extraction from `data.tasks`, `answer`, and `evidence` paths.

These runner/helper changes were not part of the committed production changes and must not be treated as acceptance-runner changes.

## Service restart evidence

| Service | Port | Status |
|---------|------|--------|
| Task API | 8003 | 200 OK |
| PO Agent | 8004 | 200 OK |

`FRESH_RUNTIME_PROVEN = YES`

## Oracle / source-contract preflight

- Person grounding evidence: `assigned_to.externalId` for `Garanin.R.V` and `Kalachanov.V.V`.
- Product grounding evidence: `unit.space.code` for DMS/OLP/WMB.
- Sprint grounding evidence: `scrum_board_plugin_sprint.code`; DMS current sprint evidence includes `DMS-SPRNT-1`.
- Status evidence uses SWTR workflow status fields.
- Oracle path is independent from agent path: agent uses `/api/v1/query`; oracle uses direct SWTR reads/search.

`ORACLE_PREFLIGHT_PASS = YES`
`ORACLE_INDEPENDENCE_PASS = YES`

## Per-ID evidence table

| ID | Query | Executed | Response | Agent Keys | Oracle Keys | Missing | Extra | Verdict | Evidence |
|----|-------|----------|----------|------------|-------------|---------|-------|---------|----------|
| TS-01 | `Покажи задачи Гаранина.` | YES | COMPLETED | 17 keys incl. DMS and OLP | 8 DMS keys | 0 shown | OLP-3037, OLP-3110, OLP-3145... | FAIL | Agent returned foreign OLP tasks beyond expected DMS set. |
| TS-02 | `Покажи задачи Калачанова.` | YES | COMPLETED | 50 CRPV keys | empty | 0 | CRPV-117199, CRPV-117200, CRPV-117201... | FAIL | Agent produced tasks while oracle for canonical scope was empty. |
| TS-03 | `Покажи задачи по DMS.` | YES | FAILED | empty | DMS-243, DMS-248, DMS-262... | DMS keys | 0 | FAIL | Agent failed with no tasks while oracle had DMS tasks. |
| TS-04 | `Покажи задачи по OLP.` | YES | FAILED | empty | empty | 0 | 0 | PASS | Empty result matched independent empty oracle. |
| TS-05 | `Покажи задачи текущего спринта DMS.` | YES | FAILED | empty | DMS-243, DMS-248, DMS-36... | DMS current sprint keys | 0 | FAIL | Current DMS sprint oracle had tasks; agent returned none. |
| TS-06 | `Покажи задачи текущего спринта OLP.` | YES | FAILED | empty | empty | 0 | 0 | PASS | Empty result matched independent empty oracle. |
| TS-07 | `Покажи задачи со статусом Open в DMS.` | YES | NEEDS_CLARIFICATION | empty | empty | 0 | 0 | CLARIFICATION_PASS | Agent requested clarification for Open status. |
| TS-08 | `Покажи закрытые задачи Гаранина.` | YES | NEEDS_CLARIFICATION | empty | empty | 0 | 0 | CLARIFICATION_PASS | Agent requested clarification for closed/completed status semantics. |
| TS-09 | `Покажи задачи Гаранина по DMS.` | YES | FAILED | empty | DMS-243, DMS-248, DMS-262... | DMS Garanin keys | 0 | FAIL | Agent failed with no tasks while oracle had exact person+product tasks. |
| TS-10 | `Покажи задачи Гаранина по OLP.` | YES | NEEDS_CLARIFICATION | empty | empty | 0 | 0 | CLARIFICATION_PASS | Agent requested clarification for person+product query. |
| TS-11 | `Покажи задачи Калачанова по WMB.` | YES | NEEDS_CLARIFICATION | empty | empty | 0 | 0 | CLARIFICATION_PASS | Agent requested clarification for person+product query. |
| TS-12 | `Покажи открытые задачи Гаранина.` | YES | NEEDS_CLARIFICATION | empty | DMS-243, DMS-248, DMS-262... | DMS Garanin keys | 0 | CLARIFICATION_PASS | Clarification despite non-empty oracle; counted as false-empty high risk. |

## Key findings

1. TS-01 still leaks tasks outside the expected source-backed scope.
2. TS-02 returns tasks when the oracle is empty for the canonical scope.
3. TS-03, TS-05, TS-09 return `FAILED` with no tasks despite non-empty oracle sets.
4. TS-12 clarification hides a non-empty oracle set and is a false-empty risk.
5. The production fix under test did not close the TS-01..TS-12 batch.

## Footer

```text
ASSIGNMENT_ID = CORE8_017V2_BATCH_TS01_TS12_RETEST_038
CURRENT_HEAD = 941e5f1aa1d99199bd79ccbf0c171043836f9dd6
PRODUCTION_FIX_UNDER_TEST = 6cb0ad7fa175863f8c8d0807a1504fe1e35bd6aa
PREVIOUS_037_REPORT_COMMIT = 0a604d956418ebec2941aadec0511a70ac9d1478
BATCH_SCOPE = TS-01..TS-12
TS_REQUIRED = 12
TS_EXECUTED = 12/12
TS_PASS = 2
TS_FAIL = 5
TS_NOT_EXECUTED = 0
TS_CLARIFICATION_PASS = 5
CURRENT_SPRINT_RESOLUTION = FAIL
STATUS_OPEN_GROUNDING = BLOCKED
STATUS_CLOSED_COMPLETED_GROUNDING = BLOCKED
PERSON_PRODUCT_GROUNDING = FAIL
ORACLE_PREFLIGHT_PASS = YES
ORACLE_INDEPENDENCE_PASS = YES
FALSE_EMPTY_HIGH_COUNT = 4
FALSE_GREEN_HIGH_COUNT = 0
SOURCE_CONTRACT_OR_GROUNDING_DEFECTS = 1
NEW_HIGH_PRODUCTION_REGRESSIONS = 0
AS21_MUTATIONS_DURING_TEST = 0
038_BATCH_VERDICT = RED
READY_TO_RESUME_GATE_E = NO
```

## Conclusion

Assignment 038 is RED. Do not resume Gate E and do not start later 017 V2 batches until the TS-01..TS-12 production defects are fixed and retested.
