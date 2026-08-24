# Assignment 067 — Fresh Process Clarification Replay Retest

## Role
QA/tester only. Do not modify production code, tests, prompts, runners, config, AS21/SWTR data or environment files.

## Purpose
Determine whether QA 066 was executed against a stale already-running PO Agent process. Unit tests imported the current checkout and passed 2/2, while the live HTTP path behaved exactly like the pre-fix runtime and emitted no `clarification_replay` warning. This assignment must prove the live service process is freshly started from the current checkout before replay is tested.

## Baseline
Branch: `feat/core8-real-query-hardening-v2`

The START_HEAD must contain:
- production clarification replay fix `64f4e254446262d4e08c5917133a3e3b926561c8`
- regression contract `603b282a66f62b02d339032e67f4c6fd85d77f6f`

## Stage A — Checkout / import guard
1. Fetch/pull the branch.
2. Record `git rev-parse HEAD` and `git status --short`.
3. From `po-agent-platform-v2`, set PYTHONPATH to the current checkout `src` directory and verify:
   - `semantic_correction_runtime_v2.__file__` resolves inside the current local checkout;
   - `/private/tmp/PO-Agent-Architecture-Review` is absent from `sys.path`.
4. Run `python3 -m pytest tests/test_semantic_session_isolation.py -q`.
5. If unit tests are not 2/2 PASS, STOP and report RED without changing code.

## Stage B — Force a fresh PO Agent service process
This stage is mandatory before any live query.

1. Stop every running uvicorn/PO Agent process that serves the local PO Agent API used by QA.
2. Prove the old service is down before restart (health/query endpoint must not respond successfully).
3. Start PO Agent again from the CURRENT local checkout and CURRENT environment used for real task-api/AS21 testing.
4. Do not start it from `/private/tmp`, another clone, another venv checkout, or another shell with stale PYTHONPATH.
5. Record:
   - process PID after restart;
   - working directory / launch command;
   - resolved current checkout path;
   - health result after restart;
   - adapter mode and semantic mode from health.

If a fresh process cannot be proven, verdict = BLOCKED. Do not continue.

## Stage C — Live exact clarification replay only
Use one new unique session_id and this same exact query for all three turns:

`Покажи задачи Гаранина в спринте DMS-SPRNT-2`

Execute A1 -> A2 -> A3 through the normal production `/api/v1/query` path.

For every turn record:
- status
- intent
- skill
- question
- clarification_id
- warnings
- session_id

Required invariant after fix `64f4e25`:
- A1 = NEEDS_CLARIFICATION
- A2 = NEEDS_CLARIFICATION
- A3 = NEEDS_CLARIFICATION
- A2/A3 warnings contain `clarification_replay`
- A2/A3 must NOT be consumed as clarification answers
- clarification question and clarification_id remain semantically the same as A1 (trace_id may differ)

If A1 does not open a clarification because source data now unambiguously resolves the person, classify the case as NOT_APPLICABLE and use another source-backed ambiguous person query that reliably opens member_login clarification. Do not invent test data and do not alter AS21.

## Stage D — Minimal controls
Only if Stage C PASS:
1. A -> B -> A same-session independent-turn isolation.
2. One genuine correction case (`Нет, только со статусом Open`) to prove correction behavior remains functional.

Do not run full QA026/060/062 in this assignment.

## Required report
Create and commit only:
`qa_reports/CORE8_FRESH_PROCESS_CLARIFICATION_REPLAY_RETEST_067.md`

Required metrics:
```text
START_HEAD = <sha>
CURRENT_CHECKOUT_IMPORT = PASS|FAIL
STALE_PRIVATE_TMP_PATH_PRESENT = YES|NO
UNIT_SESSION_TESTS = x/2 PASS
OLD_SERVICE_PROVEN_STOPPED = YES|NO
FRESH_SERVICE_PID = <pid>
FRESH_SERVICE_CURRENT_CHECKOUT_PROVEN = YES|NO
HEALTH_AFTER_RESTART = PASS|FAIL
CLARIFICATION_REPLAY_A1_A2_A3 = PASS|FAIL|NOT_APPLICABLE
CLARIFICATION_REPLAY_WARNING_COUNT = n
REPLAY_CONSUMED_AS_ANSWER_COUNT = n
A_B_A_ISOLATION = PASS|FAIL|NOT_TESTED
GENUINE_CORRECTION = PASS|FAIL|NOT_TESTED
HTTP_500_COUNT = n
NEW_REGRESSIONS = n
READY_TO_RESUME_060_AND_062 = YES|NO
067_VERDICT = GREEN|RED|BLOCKED
```

## Rules
- No production/test/prompt/config modifications.
- No automatic repair.
- No weakening expectations.
- Commit/push only the report.
- If live behavior remains RED after a proven fresh process, return raw evidence and stop.
