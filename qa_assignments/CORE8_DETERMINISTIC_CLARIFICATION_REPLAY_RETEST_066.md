# Assignment 066 — Deterministic Clarification Replay Retest

## Role
QA/tester only. Do not modify production code, tests, prompts, runners, config, wrappers, `.env`, or AS21/SWTR data.

## Baseline under test
- Production fix: `64f4e254446262d4e08c5917133a3e3b926561c8`
- Regression contract: `603b282a66f62b02d339032e67f4c6fd85d77f6f`

## 0. Environment guard — mandatory
From the local `po-agent-platform-v2` checkout:

1. `git rev-parse HEAD`
2. `git status --short`
3. Print imported module path:
   `python3 -c "import po_agent.harness.semantic_correction_runtime_v2 as m; print(m.__file__)"`
4. Print `sys.path`.

The imported path MUST resolve under the current local checkout `PO_Agent_Harness/po-agent-platform-v2/src`.
`/private/tmp/PO-Agent-Architecture-Review/...` MUST NOT appear in `sys.path`.

If the guard fails, stop and report `066_VERDICT=BLOCKED`. Do not run tests against stale code.

## 1. Unit gate
Run only:

`python3 -m pytest tests/test_semantic_session_isolation.py -vv -s`

Expected: `2/2 PASS`.

Do not change a failing test. Return full assertion/traceback if it fails.

## 2. Live clarification replay
Using the real production runtime/config and real SWTR path, use a fresh session id and execute exactly three times:

`Покажи задачи Гаранина в спринте DMS-SPRNT-2`

Sequence: A1 → A2 → A3, same session.

If A1 opens a clarification, A2 and A3 must deterministically replay the same clarification state:
- same status `NEEDS_CLARIFICATION`;
- same question;
- same clarification_id;
- same intent and semantic constraints where exposed;
- warning `clarification_replay` on replays;
- no inner answer consumption;
- no `semantic-correction` clarification;
- no stale/unrelated sprint/person/product mutation.

Record per turn:
`status | intent | skill | clarification_id | question | warnings | semantic frame/slots`.

If A1 does not open clarification because current production grounding can fully prove the entity, do NOT force a clarification. Record that behavior and perform a second replay case using any naturally occurring real query that opens a legitimate clarification. Do not invent source data.

## 3. Control checks
Run a compact control only:
- A→B→A independent-turn isolation;
- one genuine correction flow.

No full QA026/062 in this assignment.

## Required report
Commit and push only:

`qa_reports/CORE8_DETERMINISTIC_CLARIFICATION_REPLAY_RETEST_066.md`

Required metrics:

```text
START_HEAD = <sha>
CONTAINS_FIX_64F4E25 = YES|NO
CONTAINS_TEST_603B282 = YES|NO
CLEAN_TREE_GUARD = PASS|FAIL
IMPORTED_MODULE_PATH = <path>
STALE_PRIVATE_TMP_PATH_PRESENT = YES|NO
UNIT_SESSION_TESTS = x/2 PASS
CLARIFICATION_REPLAY_A1_A2_A3 = PASS|FAIL|N/A
REPLAY_STATUS_STABLE = PASS|FAIL|N/A
REPLAY_QUESTION_STABLE = PASS|FAIL|N/A
REPLAY_CLARIFICATION_ID_STABLE = PASS|FAIL|N/A
CLARIFICATION_REPLAY_WARNING_COUNT = n
REPLAY_CONSUMED_AS_ANSWER_COUNT = n
STALE_SLOT_CONTAMINATION_COUNT = n
A_B_A_ISOLATION = PASS|FAIL
GENUINE_CORRECTION = PASS|FAIL|BLOCKED
HTTP_500_COUNT = n
NEW_REGRESSIONS = n
READY_TO_RESUME_060_AND_062 = YES|NO
066_VERDICT = GREEN|RED|BLOCKED
```

## Completion
Do not repair anything. After report push, stop and return report commit SHA, verdict, and full report text.
