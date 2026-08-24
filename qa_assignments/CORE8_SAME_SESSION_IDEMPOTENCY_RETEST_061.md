# Assignment 061 — Same-Session Idempotency Stability Retest

## Role

QA/tester only. Do not modify production code, tests, prompts, runners, config, `.env`, wrappers or AS21/SWTR data.

## Baseline under test

Production fix:

`76ed1ada782118bd10567cc19fa40e9a2857d4e5`

Unit coverage:

`e5444c7d2b5ad8ef0def8a53fb2e3fc230b69182`

START_HEAD must contain both commits and tracked working tree must be clean.

## Purpose

Verify that an identical standalone query repeated in the SAME session is an idempotent rerun, not a correction/recheck clarification, while preserving genuine correction behavior.

This assignment precedes Assignment 060. Do not run the 19-case semantic targeted matrix yet.

## A. Unit gate

Run:

```bash
cd po-agent-platform-v2
python3 -m pytest \
  tests/test_semantic_correction_repeat.py \
  tests/test_semantic_core_v2.py \
  tests/test_harness_dialogue_learning.py \
  -q
```

Record exact pass/fail counts. Do not edit tests on failure.

## B. Live same-session repeat

Use production `task-api` + configured production LLM + real AS21/SWTR.

Query:

`У кого наибольшая загрузка в спринте DMS-SPRNT-2?`

Use ONE fresh session id, e.g. `qa061-repeat`.

Execute the exact same query three times sequentially in that same session.

For each run capture:

- status;
- intent;
- skill_id;
- answer/result summary;
- clarification_id;
- warnings;
- `_harness.dialogue_state`;
- latency_ms.

Required:

- all 3 runs complete normally;
- no `semantic-correction` clarification;
- same intent/skill across runs;
- no `correction_clarification` state;
- no restart between runs.

## C. Normalized repeat guard

In one fresh session execute sequentially:

1. `У кого наибольшая загрузка в спринте DMS-SPRNT-2?`
2. `  У КОГО   НАИБОЛЬШАЯ загрузка в спринте DMS-SPRNT-2?  `

Both must execute as the same standalone operation and must not enter correction flow.

## D. Fresh-session control

Run the baseline query once in each of three fresh sessions.

All three must return the same status/intent/skill class. Capture differences in source result only if AS21 data changed during the test.

## E. Genuine correction regression

Use a new session.

Turn 1: execute one supported request containing a person or sprint constraint.

Turn 2: send an explicit correction that replaces exactly one constraint, e.g. `Нет, я имел в виду DMS-SPRNT-1` when appropriate for the selected request.

Required:

- genuine correction path remains active;
- correction is not treated as an independent duplicate rerun;
- no persistent skill mutation;
- response metadata/evidence shows correction/recheck behavior as designed.

Do not change the production query contract to make this pass.

## Fail-fast conditions

Stop and report RED if any exact repeat:

- becomes `NEEDS_CLARIFICATION` with `:semantic-correction`;
- loses intent or skill after a previous successful identical turn;
- requires service restart to work again;
- causes HTTP 500/unhandled exception.

Do not repair anything.

## Report

Commit and push only:

`qa_reports/CORE8_SAME_SESSION_IDEMPOTENCY_RETEST_061.md`

Required final metrics:

```text
START_HEAD = <sha>
CONTAINS_FIX_76ED1AD = YES|NO
CONTAINS_TEST_E5444C7 = YES|NO
CLEAN_TREE_GUARD = PASS|FAIL
UNIT_GATE = x/y PASS
SAME_SESSION_REPEAT = x/3 PASS
NORMALIZED_REPEAT = x/2 PASS
FRESH_SESSION_CONTROL = x/3 PASS
SEMANTIC_CORRECTION_CLARIFICATION_ON_REPEAT_COUNT = n
INTENT_LOSS_ON_REPEAT_COUNT = n
SKILL_LOSS_ON_REPEAT_COUNT = n
HTTP_500_COUNT = n
GENUINE_CORRECTION_REGRESSION = PASS|FAIL|BLOCKED
READY_TO_RESUME_ASSIGNMENT_060 = YES|NO
061_VERDICT = GREEN|RED|BLOCKED
```

After push, return report SHA, concise verdict and full report text, then stop.
