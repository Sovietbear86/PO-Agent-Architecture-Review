# Assignment 064 — Pending Clarification + NEW Turn Session Retest

## Role

QA/tester only. Do not modify production code, tests, prompts, runners, config, wrappers or AS21/SWTR data.

## Baseline

Production fix under test:

`58ddbb7a12c4a527c906cd4ee9a5b21660ea2cb4`

Existing regression tests:

`po-agent-platform-v2/tests/test_semantic_session_isolation.py`

START_HEAD must contain the production fix and tracked tree must be clean.

## Goal

Verify the two concrete defects found by Assignment 063 are closed:

1. exact replay of a request that opened a clarification must restart the original request instead of consuming the replay as a clarification answer;
2. a semantically NEW independent turn in the same user session must not inherit the prior semantic frame.

Also prove genuine correction behavior still works.

## Stage A — Unit gate

Run:

```bash
cd po-agent-platform-v2
python3 -m pytest tests/test_semantic_session_isolation.py -q
```

Expected: `2 passed`.

If either test fails, do not modify anything. Record exact assertion/actual values and continue to the live diagnostic stages if possible.

## Stage B — Clarification replay live test

Use production task-api / real SWTR path.

Query A:

`Покажи задачи Гаранина в спринте DMS-SPRNT-2`

Use one session_id. Execute A three times unchanged: `A1 -> A2 -> A3`.

Capture for every run:
- status;
- clarification_id;
- intent;
- selected skill;
- semantic frame slots (`person_raw`, `member_login`, `product`, `sprint_id`, `status_raw` when present);
- warnings.

Required invariant:
- exact replay must not be consumed as the answer to the pending clarification;
- A2/A3 must not become a broadened COMPLETED request with lost filters;
- the extracted explicit sprint must remain `DMS-SPRNT-2` whenever a semantic frame is present;
- no stale `DMS-SPRNT-1` / `OLP-SPRNT-5` or other unrelated slot may appear.

## Stage C — A -> B -> A same-session isolation

In one session:

A = `Какие задачи в спринте DMS-SPRNT-2?`
B = `Покажи задачу DMS-261`
A again.

Required:
- B must not inherit A filters;
- final A must semantically match first A;
- no stale task/sprint/product/person slot contamination.

## Stage D — NEW independent turn semantic memory

Use two standalone queries in one session that the dialogue-act classifier identifies as `new`.

Record semantic frames for both. The second request must contain only values justified by its own text, not previous-turn values.

## Stage E — Cross-session isolation

Run the same standalone sprint query in three distinct session_ids. Results must be semantically consistent and independent.

## Stage F — Genuine correction control

In one session:

1. `Покажи задачи в спринте DMS-SPRNT-2`
2. `Нет, только со статусом Open`

The correction mechanism must remain functional. Do not mark the fix GREEN if genuine correction is broken.

## Required metrics

```text
START_HEAD = <sha>
CONTAINS_FIX_58DDBB7 = YES|NO
CLEAN_TREE_GUARD = PASS|FAIL
UNIT_SESSION_TESTS = x/2 PASS
CLARIFICATION_REPLAY_A1_A2_A3 = PASS|FAIL
A_B_A_ISOLATION = PASS|FAIL
NEW_TURN_ISOLATION = PASS|FAIL
CROSS_SESSION_ISOLATION = PASS|FAIL
GENUINE_CORRECTION = PASS|FAIL|BLOCKED
STALE_SLOT_CONTAMINATION_COUNT = n
REPLAY_CONSUMED_AS_CLARIFICATION_ANSWER_COUNT = n
UNRELATED_SPRINT_SLOT_COUNT = n
HTTP_500_COUNT = n
NEW_REGRESSIONS = n
READY_TO_RESUME_060_AND_062 = YES|NO
064_VERDICT = GREEN|RED|BLOCKED
```

## Report allowlist

Commit and push only:

`qa_reports/CORE8_PENDING_CLARIFICATION_AND_NEW_TURN_RETEST_064.md`

No production/test/runner changes are allowed.
