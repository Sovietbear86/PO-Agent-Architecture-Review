# QA Assignment — Core-8 Assignee + Sprint Fail-Closed Retest 024

## Goal
Verify the two remaining production defects from QA 023 are fixed before the exhaustive 017_V2 rerun:
1. natural Russian assignee wording such as `задачи Гаранина` must survive semantic interpretation and ground to the real AS21 assignee;
2. an invented explicit sprint must fail closed even though MCP echoes the requested sprint ID.

## Tester role
GigaCode is QA/adversarial reviewer only. Do not modify production code, tests, fixtures, configuration, AS21 data, roadmap files, or skill definitions. Only create/update the assigned QA report.

## Branch
`feat/core8-real-query-hardening-v2`

## Required report
`qa_reports/CORE8_ASSIGNEE_AND_SPRINT_FAILCLOSED_RETEST_024.md`

## A. Preflight
1. Pull current HEAD.
2. Restart Task API and PO Agent from current HEAD.
3. Record HEAD.
4. Confirm Task API and PO Agent health.
5. Confirm `QUERY_HTTP_500_COUNT = 0` during the entire run.

## B. Focused developer tests
Run:

`pytest -q tests/test_explicit_sprint_id_precision.py`

Required: all focused tests PASS. Record exact count.

Pay special attention to tests proving:
- `задачи Гаранина` -> `person_raw=Гаранина`;
- `задачи Родиона Гаранина` preserves the full raw person mention;
- `что у Гаранина в работе` preserves the person;
- an echoed but source-empty sprint fails closed;
- a source-backed real sprint is preserved.

## C. Independent source oracle
Using direct AS21/SWTR read capabilities, independently prove:
- `DMS-SPRNT-1` complete corpus = expected live corpus;
- `DMS-SPRNT-2` complete corpus = expected live corpus;
- `DMS-SPRNT-999999` has no positive source evidence;
- Garanin identity fields (`externalId`, login, display/full name) and exact task keys in `DMS-SPRNT-1` and `DMS-SPRNT-2`.

Known acceptance anchor from QA 023: Garanin had exactly **4 source-backed tasks in DMS-SPRNT-1 and 0 in DMS-SPRNT-2**. Re-prove this from the live source; do not blindly trust the previous report if source data changed.

## D. Semantic frame checks
Run through the production semantic/runtime path and capture slots/intent where available:
- `Покажи задачи Гаранина в DMS-SPRNT-1`
- `Покажи задачи Родиона Гаранина в DMS-SPRNT-1`
- `Что у Гаранина в работе`

Required:
- person/assignee mention is present after interpretation/grounding;
- it is not silently dropped;
- the explicit sprint remains exactly `DMS-SPRNT-1` where supplied;
- no `SPRNT-1` task key hallucination.

## E. Production acceptance queries
Run through `/api/v1/query` and compare with independent oracle by task key, not count only:
1. `Покажи задачи в DMS-SPRNT-1`
2. `Покажи задачи в DMS-SPRNT-2`
3. `Покажи задачи Гаранина в DMS-SPRNT-1`
4. `Покажи задачи Родиона Гаранина в DMS-SPRNT-1`
5. `Покажи задачи Гаранина в DMS-SPRNT-2`
6. `Покажи задачи Гаранина по DMS в спринте DMS-SPRNT-1`
7. `Покажи задачи в DMS-SPRNT-999999`

Required:
- queries 1 and 2 match complete sprint oracle by task key;
- queries 3, 4 and 6 match the Garanin oracle exactly; if live source still contains 4 tasks, agent result must be exactly those 4 keys;
- query 5 matches source truth (previously 0);
- query 7 must be `NEEDS_CLARIFICATION`/`FAILED` fail-closed or equivalent safe non-execution. `COMPLETED + 0` is FAIL;
- no query silently drops an explicit assignee or sprint filter.

Mandatory comparison for every filtered query:
`MISSING_KEYS=[...]`
`EXTRA_KEYS=[...]`

## F. Natural wording robustness
Test at least these variants against source truth:
- `Какие задачи у Гаранина в DMS-SPRNT-1?`
- `Что у Гаранина в DMS-SPRNT-1?`
- `Покажи, что делает Гаранин в DMS-SPRNT-1`
- `Покажи задачи Гаранина по DMS`

If a wording is genuinely ambiguous, targeted clarification is acceptable. Silently ignoring the person filter is not.

## G. Correction loop smoke
Same session:
1. `Покажи открытые задачи Гаранина в последнем спринте по DMS`
2. `Ты не прав, проверь ещё раз`

Required:
- turn 2 is recognized as correction of turn 1;
- fresh source recheck occurs;
- session context retained;
- targeted clarification appears when semantics remain unresolved;
- no persistent skill mutation from one correction.

## H. Negative/false-green controls
1. An invented sprint may not be accepted only because the source facade echoes the input ID.
2. `COMPLETED + 0` is not PASS unless independent oracle proves empty result.
3. Agent and oracle may not share the same cached relation source as the only evidence.
4. Assignee filter may not disappear between semantic frame and adapter execution.

## I. Protected regression
Run the protected/Core-8 regression suite used in QA 023. Classify every failure as exactly one of:
- `NEW_PRODUCTION_REGRESSION`
- `PRE_EXISTING_FAILURE`
- `STALE_TEST_EXPECTATION`
- `EXTERNAL_INTEGRATION_BLOCKED`

No contradictory classifications.

## Mandatory footer
```text
ASSIGNMENT_ID = CORE8_ASSIGNEE_AND_SPRINT_FAILCLOSED_RETEST_024
CURRENT_HEAD = ...
FOCUSED_TESTS_PASS = x/x
QUERY_HTTP_500_COUNT = ...
RAW_ORACLE_DMS_1_MATCH = YES/NO
RAW_ORACLE_DMS_2_MATCH = YES/NO
GARANIN_SOURCE_PROOF = YES/NO
GARANIN_DMS1_SOURCE_COUNT = ...
GARANIN_DMS2_SOURCE_COUNT = ...
NATURAL_ASSIGNEE_SLOT_PRESERVED = YES/NO
GARANIN_DMS1_AGENT_COUNT = ...
GARANIN_DMS1_MISSING_KEYS = [...]
GARANIN_DMS1_EXTRA_KEYS = [...]
GARANIN_FULLNAME_QUERY_MATCH = YES/NO
GARANIN_DMS2_QUERY_MATCH = YES/NO
INVALID_SPRINT_FAIL_CLOSED = YES/NO
INVALID_SPRINT_COMPLETED_ZERO_COUNT = ...
SPRINT_SUFFIX_AS_TASK_KEY_COUNT = ...
NATURAL_WORDING_ROBUSTNESS_PASS = x/4
CHALLENGE_TRIGGERS_FRESH_RECHECK = YES/NO
TARGETED_CLARIFICATION_PASS = YES/NO
SESSION_CONTEXT_RETENTION_PASS = YES/NO
PERSISTENT_SKILL_MUTATION_FROM_CORRECTION = ...
NEW_HIGH_PRODUCTION_REGRESSIONS = ...
AS21_MUTATIONS_DURING_TEST = 0
READY_TO_RERUN_017_V2 = YES/NO
```

`READY_TO_RERUN_017_V2 = YES` only if:
- real sprint corpus checks match the independent oracle;
- natural assignee wording is preserved end-to-end;
- Garanin filtered queries match source keys exactly;
- invalid sprint fails closed;
- correction loop remains green;
- HTTP 500 count is zero;
- there are zero new HIGH production regressions.

After publishing and pushing the report, STOP. Do not launch 017_V2 yourself.
