# QA Assignment — Core-8 Live Sprint Grounding Retest 023

## Goal
Verify the production fix for the RED blocker from Assignment 022: explicit sprint IDs must be validated against live SWTR and must never be deleted merely because cached `/api/v1/tasks` lacks `sprint_id`.

## Tester role
GigaCode is QA/adversarial reviewer only. Do not modify production code, tests, fixtures, configuration, AS21 data, or roadmap files. Only create the QA report.

## Branch
`feat/core8-real-query-hardening-v2`

## Required report
`qa_reports/CORE8_LIVE_SPRINT_GROUNDING_RETEST_023.md`

## A. Preflight
1. Pull current HEAD.
2. Restart Task API and PO Agent from current HEAD.
3. Record HEAD.
4. Confirm HTTP 500 count remains 0.

## B. Focused developer tests
Run:
`pytest -q tests/test_explicit_sprint_id_precision.py`

Required: 6/6 PASS.

## C. Prove live sprint validation contract
For `DMS-SPRNT-1`, `DMS-SPRNT-2` and one deliberately invalid sprint such as `DMS-SPRNT-999999`:
1. Call the direct SWTR sprint endpoint.
2. Record HTTP/source outcome.
3. Verify adapter `sprint_exists()` returns YES for the two real sprints and NO for the invalid sprint.
4. Verify cached `known_sprints` may be empty without affecting this decision.

Do not infer sprint non-existence from cached task fields.

## D. Production explicit-sprint queries
Run through `/api/v1/query`:
- `покажи задачи в DMS-SPRNT-1`
- `покажи задачи в DMS-SPRNT-2`
- `покажи задачи Гаранина в DMS-SPRNT-1`
- `покажи задачи Гаранина по DMS в спринте DMS-SPRNT-1`
- `покажи задачи в DMS-SPRNT-999999`

For every response record HTTP, status, intent, semantic frame/slots if available, warnings, result count and task keys.

Pass criteria:
- Real sprint IDs remain exact end-to-end (`DMS-SPRNT-*`), never become `SPRNT-*`, and never disappear.
- Invalid sprint fails closed or asks clarification; it must not silently execute without sprint filtering.
- The two unfiltered real-sprint queries must match the independent SWTR corpus by task key, not merely by count.

## E. Independent raw oracle
Obtain complete task-key corpus for:
- DMS-SPRNT-1
- DMS-SPRNT-2

Compare agent unfiltered sprint-query output with oracle.
Required:
`MISSING_KEYS=[]`, `EXTRA_KEYS=[]` for both.

If the API intentionally paginates user output, compare the complete underlying `data` corpus or documented pagination contract and state that explicitly.

## F. Garanin query truth
Do not assume whether Garanin has or has not tasks.
Independently inspect the complete live sprint corpus and raw assignee identity fields (`externalId`, login, display name) for DMS-SPRNT-1 and DMS-SPRNT-2.
State:
- exact matching task keys for Garanin, if any;
- identity field used for the match;
- agent result;
- MISSING_KEYS / EXTRA_KEYS.

No claim such as “Garanin has no tasks” is allowed without this complete source-backed proof.

## G. Correction smoke
Same session:
1. `Покажи открытые задачи Гаранина в последнем спринте по DMS`
2. `Ты не прав, проверь ещё раз`

Required:
- second turn is correction, not a new query;
- source recheck occurs;
- targeted clarification is allowed/expected for unresolved semantics;
- no persistent skill mutation.

## H. Task lookup non-regression
Run a known source-backed task lookup selected from the live DMS-SPRNT-1 corpus, not an arbitrary cached-missing key. Verify the ordinary task-key path still works and sprint suffix is never interpreted as a task key.

## I. Protected regression
Run the focused Core-8/protected suite used in 022. Classify every failure as one of:
- NEW_PRODUCTION_REGRESSION
- PRE_EXISTING_FAILURE
- STALE_TEST_EXPECTATION
- EXTERNAL_INTEGRATION_BLOCKED

Do not use contradictory classifications.

## Mandatory footer
```text
ASSIGNMENT_ID = CORE8_LIVE_SPRINT_GROUNDING_RETEST_023
CURRENT_HEAD = ...
FOCUSED_TESTS_PASS = x/6
QUERY_HTTP_500_COUNT = ...
LIVE_SPRINT_VALIDATION_DMS_1 = YES/NO
LIVE_SPRINT_VALIDATION_DMS_2 = YES/NO
INVALID_SPRINT_FAIL_CLOSED = YES/NO
DMS_SPRNT_1_PRESERVED = YES/NO
DMS_SPRNT_2_PRESERVED = YES/NO
SPRINT_SUFFIX_AS_TASK_KEY_COUNT = ...
RAW_ORACLE_DMS_1_MATCH = YES/NO
RAW_ORACLE_DMS_2_MATCH = YES/NO
GARANIN_SOURCE_PROOF = YES/NO
GARANIN_MISSING_KEYS = [...]
GARANIN_EXTRA_KEYS = [...]
CHALLENGE_TRIGGERS_FRESH_RECHECK = YES/NO
TARGETED_CLARIFICATION_PASS = YES/NO
SESSION_CONTEXT_RETENTION_PASS = YES/NO
PERSISTENT_SKILL_MUTATION_FROM_CORRECTION = ...
TASK_LOOKUP_NONREGRESSION = YES/NO
NEW_HIGH_PRODUCTION_REGRESSIONS = ...
AS21_MUTATIONS_DURING_TEST = 0
READY_TO_RERUN_017_V2 = YES/NO
```

`READY_TO_RERUN_017_V2 = YES` only if all real sprint grounding/oracle checks, correction smoke and protected regression gate are green.

After publishing and pushing the report, STOP.