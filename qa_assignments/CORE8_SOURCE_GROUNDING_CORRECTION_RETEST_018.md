# QA Assignment 018 — Core-8 Source Grounding + Correction Retest

## Mission
Verify the developer fixes prompted by 017_V2 before rerunning the full 122-case matrix. GigaCode is tester only: do not modify production code, tests, fixtures, AS21/SWTR data, or roadmap files.

## Developer changes under test
- production runtime now uses `HardenedProductionTaskApiAS21Adapter`;
- sprint membership is joined from the **complete live SWTR sprint corpus by task key** instead of trusting missing cached `sprintId`;
- missing cached project/space is rehydrated from raw SWTR unit evidence instead of being interpreted as `NO`;
- composite task search preserves `product` and intersects by task keys;
- assignee filtering accepts canonical externalId/login/display-name identity;
- explicit negative feedback (`ты не прав`, `проверь ещё раз`, etc.) forces a fresh source recheck and then targeted clarification/correction handling;
- a single correction cannot mutate/promote a production skill.

## A. Unit/developer tests
Run at minimum:
- `tests/test_core8_real_query_hardening.py`
- existing task-api adapter/source-contract tests
- existing dialogue/feedback/learning-loop tests

Record exact pass/fail counts. No test modifications.

## B. Oracle repair — complete sprint corpus
The 017_V2 oracle incorrectly used `DMS-SPRNT-1: 100 (page 1)` as if it were complete. This is forbidden.

For both `DMS-SPRNT-1` and `DMS-SPRNT-2`:
1. call the read-only sprint endpoint with `complete=true`, `limit=100`, sufficient `max_pages`;
2. prove `complete=true` or otherwise classify oracle BLOCKED;
3. extract every unique task key from the complete corpus;
4. join those keys to canonical `/api/v1/tasks` records and/or raw `/swtr-read/tasks/{key}` evidence;
5. resolve Garanin using canonical identity aliases: externalId, login and display name — never display-name-only;
6. report all matching task keys and the raw identity evidence.

Known user-provided positive anchors are a hypothesis to verify, not a hardcoded answer:
- Garanin has tasks in `DMS-SPRNT-1`;
- Garanin has tasks in `DMS-SPRNT-2`.

If complete SWTR evidence still contradicts either assertion, provide the full task-key corpus size, every Garanin identity used, and exact source evidence. Do not write “user assertion false” from a partial page.

## C. Project/space grounding
Take at least 5 known Garanin tasks and prove their project/space using raw `/swtr-read/tasks/{key}` evidence. Compare:
- cached project relation;
- raw SWTR space relation;
- hardened adapter canonical `project_space`.

Required: missing cached relation must be repaired when raw source proves it. Missing relation must never mean “not in DMS”.

## D. Sprint grounding through production adapter
Call `HardenedProductionTaskApiAS21Adapter.get_sprint_tasks` for `DMS-SPRNT-1` and `DMS-SPRNT-2` with `space="DMS"`.

Required:
- same unique key set as complete SWTR oracle (subject only to tasks that can be canonically mapped; any unmappable rows are HIGH and must be listed);
- no first-page truncation;
- returned tasks carry `sprint_id` and source-backed DMS relation.

## E. GOLDEN production query
Through the real `/api/v1/query` path execute:
`Покажи открытые задачи Гаранина в последнем спринте по DMS`

Do not pre-decide the semantics of `открытые` or `последний`. If no approved rule exists, targeted clarification is correct. If an approved rule exists, record it exactly.

After semantics are resolved, compare exact task-key result to the independent complete oracle:
- `MISSING_KEYS`
- `EXTRA_KEYS`

`COMPLETED + 0` is FAIL if any matching source task exists.

## F. Two-filter and four-filter regression
Execute and independently verify:
1. `Покажи задачи Гаранина по DMS.`
2. `Покажи задачи Гаранина в DMS-SPRNT-1.`
3. `Покажи задачи Гаранина в DMS-SPRNT-2.`
4. `Покажи только Open-задачи Гаранина в DMS-SPRNT-2.`
5. `Покажи незавершенные задачи Гаранина в DMS-SPRNT-2.`

Required: exact sets after semantic clarification; product selector must not be silently ignored.

## G. Correction loop
Use the same session.

Turn 1:
`Покажи открытые задачи Гаранина в последнем спринте по DMS`

After its answer, Turn 2:
`Ты не прав, проверь ещё раз.`

Required:
- previous execution is recognized;
- a fresh source recheck occurs;
- response exposes correction metadata with previous/recheck trace IDs;
- if ambiguity remains, ask a targeted clarification about `открытые` and/or `последний спринт`;
- do not simply return the cached answer;
- do not mutate a skill.

Then test explicit correction:
`Ты не прав. У Гаранина точно есть задачи в DMS-SPRNT-1 и DMS-SPRNT-2. Проверь через спринты.`

Required: supplied sprint IDs are hypotheses verified against SWTR, original assignee/product context is retained, and negative feedback trace is captured.

## H. Protected Core-8 smoke
Re-run one known-good real-AS21 query for each Core-8 skill. This is not the final exhaustive matrix; it only proves fixes did not break unrelated capabilities.

## I. Authorization
Only if this targeted retest is green, rerun `CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md` unchanged as the final hardening gate.

## Report
Publish `qa_reports/CORE8_SOURCE_GROUNDING_CORRECTION_RETEST_018.md` with footer:

```text
ASSIGNMENT_ID = CORE8_SOURCE_GROUNDING_CORRECTION_RETEST_018
CURRENT_HEAD = <sha>
HARDENING_UNIT_TESTS_PASS = YES|NO
DMS_SPRNT_1_COMPLETE = YES|NO
DMS_SPRNT_1_GARANIN_TASKS = N
DMS_SPRNT_2_COMPLETE = YES|NO
DMS_SPRNT_2_GARANIN_TASKS = N
RAW_SPACE_GROUNDING_PASS = YES|NO
PRODUCTION_SPRINT_JOIN_PASS = YES|NO
GOLDEN_QUERY_PASS = YES|NO
MISSING_KEYS = [...]
EXTRA_KEYS = [...]
MULTIFILTER_REGRESSION_PASS = x/5
CHALLENGE_TRIGGERS_FRESH_RECHECK = YES|NO
TARGETED_CORRECTION_CLARIFICATION_PASS = YES|NO
PERSISTENT_SKILL_MUTATION_FROM_CORRECTION = N
CORE8_SMOKE_PASS = x/8
NEW_HIGH_PRODUCTION_REGRESSIONS = N
AS21_MUTATIONS_DURING_TEST = 0
READY_TO_RERUN_017_V2 = YES|NO
```

After publishing, STOP. Do not modify code and do not resume Gate E.