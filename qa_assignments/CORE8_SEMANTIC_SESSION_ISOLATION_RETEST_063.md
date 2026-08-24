# Assignment 063 — Semantic Session Isolation Retest

## Role
QA/tester only. Do not modify production code, tests, prompts, runners, fixtures, configuration or AS21/SWTR data.

## Production fix under test
- `66ce936a3fbc6bb7695639ad5bbdc8ef298136fb`

## Regression tests under test
- `bfd6a67b34d9003732277042510ea2aa75f7966f`

START_HEAD must contain both commits. Tracked working tree must be clean.

## Purpose
Prove that session-state contamination reported by Assignment 062 is fixed without breaking real correction behavior.

## Required checks

### A. Unit regression
Run:

```bash
cd po-agent-platform-v2
python3 -m pytest tests/test_semantic_session_isolation.py -q
```

Expected: all tests PASS.

### B. Clarification replay idempotency — real production path
Use real task-api + real AS21/SWTR + production semantic interpreter.

In one session execute the exact same query three times:

`Покажи задачи Гаранина в спринте DMS-SPRNT-2`

If the first response is NEEDS_CLARIFICATION, the second and third identical requests must restart/reinterpret the same original request rather than consume the full repeated sentence as the clarification answer.

Record for A1/A2/A3:
- status;
- intent;
- semantic slots;
- selected skill;
- clarification field/question when applicable;
- sprint_id;
- person_raw/member_login;
- trace id.

Required invariant: no stale sprint/product/person value may appear. In particular DMS-SPRNT-2 must never mutate into DMS-SPRNT-1, OLP-SPRNT-5 or another unrelated source entity.

### C. Independent-turn isolation A → B → A
In one fresh session:

A = `Какие задачи в спринте DMS-SPRNT-2?`
B = `Покажи задачу DMS-261`
A = `Какие задачи в спринте DMS-SPRNT-2?`

B must be classified/executed as a NEW independent request and must not inherit A's sprint/person/status slots.
The two A frames must be semantically equivalent except for trace/timing/source drift.

### D. Cross-session isolation
Run the same positive request using three distinct session_ids. Semantic frames and selected skill must be equivalent. No previous session may affect another.

### E. Genuine correction still works
Use one fresh session with a genuine correction pair. Example:

1. `Покажи задачи в спринте DMS-SPRNT-2`
2. `Нет, только со статусом Open`

Record dialogue-act/correction metadata. The second message must not be treated as a completely unrelated request if the production classifier identifies it as a correction. Do not change expectations or code if the case fails; document exact evidence.

### F. Regression safety
Run the existing targeted semantic/session/correction tests relevant to these components. Do not edit tests to obtain GREEN.

## Verdict rules

GREEN requires all of:
- unit regression PASS;
- repeated clarification-opening request stable;
- A→B→A isolation PASS;
- cross-session isolation PASS;
- no stale slot contamination;
- no new regression in genuine correction behavior.

If any production defect is found: RED, document evidence, do not fix it.

## Allowed report
Commit and push only:

`qa_reports/CORE8_SEMANTIC_SESSION_ISOLATION_RETEST_063.md`

## Required metrics

```text
START_HEAD = <sha>
CONTAINS_FIX_66CE936 = YES|NO
CONTAINS_TEST_BFD6A67 = YES|NO
CLEAN_TREE_GUARD = PASS|FAIL
UNIT_SESSION_TESTS = x/y PASS
REPEAT_A1_A2_A3 = PASS|FAIL
A_B_A_ISOLATION = PASS|FAIL
CROSS_SESSION_ISOLATION = PASS|FAIL
GENUINE_CORRECTION = PASS|FAIL|BLOCKED
STALE_SLOT_CONTAMINATION_COUNT = n
UNEXPECTED_NEEDS_CLARIFICATION_COUNT = n
NEW_REGRESSIONS = n
READY_TO_RESUME_060_AND_062 = YES|NO
063_VERDICT = GREEN|RED|BLOCKED
```

After report commit/push, stop.