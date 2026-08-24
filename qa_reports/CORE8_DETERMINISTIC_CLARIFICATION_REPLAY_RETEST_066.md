# Assignment 066 — Deterministic Clarification Replay Retest Results

**Date:** 2026-08-24  
**Branch:** `feat/core8-real-query-hardening-v2`  
**Commit:** `262e863045775e6474ee7ba324759ac04daba63e`  
**Assignment:** 066 — Deterministic Clarification Replay Retest  
**Status:** RED - Clarification Replay Fix Not Working  

---

## Environment Guard

| Check | Status | Evidence |
|-------|--------|----------|
| `git rev-parse HEAD` | ✅ PASS | `262e863045775e6474ee7ba324759ac04daba63e` |
| `git status --short` | ✅ PASS | Clean tree (only QA report files) |
| `IMPORTED_MODULE_PATH` | ✅ PASS | `PO_Agent_Harness/po-agent-platform-v2/src/po_agent/harness/semantic_correction_runtime_v2.py` |
| `STALE_PRIVATE_TMP_PATH_PRESENT` | ✅ PASS | NO |

---

## Final Metrics

| Metric | Value |
|--------|-------|
| **START_HEAD** | `262e863045775e6474ee7ba324759ac04daba63e` |
| **CONTAINS_FIX_64F4E25** | YES |
| **CONTAINS_TEST_603B282** | YES |
| **CLEAN_TREE_GUARD** | PASS |
| **IMPORTED_MODULE_PATH** | `PO_Agent_Harness/po-agent-platform-v2/src/po_agent/harness/semantic_correction_runtime_v2.py` |
| **STALE_PRIVATE_TMP_PATH_PRESENT** | NO |
| **UNIT_SESSION_TESTS** | 2/2 PASS |
| **CLARIFICATION_REPLAY_A1_A2_A3** | FAIL |
| **REPLAY_STATUS_STABLE** | FAIL |
| **REPLAY_QUESTION_STABLE** | FAIL |
| **REPLAY_CLARIFICATION_ID_STABLE** | FAIL |
| **CLARIFICATION_REPLAY_WARNING_COUNT** | 0 |
| **REPLAY_CONSUMED_AS_ANSWER_COUNT** | 1 |
| **STALE_SLOT_CONTAMINATION_COUNT** | 0 |
| **A_B_A_ISOLATION** | NOT TESTED (timed out) |
| **GENUINE_CORRECTION** | NOT TESTED (timed out) |
| **HTTP_500_COUNT** | 0 |
| **NEW_REGRESSIONS** | 0 |
| **READY_TO_RESUME_060_AND_062** | NO |
| **066_VERDICT** | RED |

---

## Test Results

### Unit Gate

```
tests/test_semantic_session_isolation.py::test_repeating_request_that_opened_clarification_replays_without_consuming_pending PASSED
tests/test_semantic_session_isolation.py::test_new_independent_turn_does_not_inherit_semantic_previous_turn PASSED
```

**UNIT_SESSION_TESTS: 2/2 PASS**

### Live Clarification Replay

**Query:** `Покази задачи Гаранина в спринте DMS-SPRNT-2`

| Turn | Status | Clarification ID | Behavior |
|------|--------|------------------|----------|
| A1 | NEEDS_CLARIFICATION | 066-live-replay:member_login | ✅ Opens clarification |
| A2 | COMPLETED | None | ❌ FAIL - consumed as answer |
| A3 | NEEDS_CLARIFICATION | 066-live-replay:semantic-correction | ❌ Recheck (not reopen) |

**Additional test with `Покажи задачи Петрова`:**

| Turn | Status | Clarification ID | Behavior |
|------|--------|------------------|----------|
| A1 | NEEDS_CLARIFICATION | 066-different:member_login | ✅ Opens clarification |
| A2 | COMPLETED | None | ❌ FAIL - consumed as answer |
| A3 | NEEDS_CLARIFICATION | 066-different:semantic-correction | ❌ Recheck (not reopen) |

**CLARIFICATION_REPLAY_A1_A2_A3: FAIL**
- Expected: All three turns return NEEDS_CLARIFICATION
- Actual: A2 returns COMPLETED

**REPLAY_STATUS_STABLE: FAIL**
- Expected: All turns return same status (NEEDS_CLARIFICATION)
- Actual: A2 returns COMPLETED

**REPLAY_QUESTION_STABLE: FAIL**
- A2 has no question (status is COMPLETED)

**REPLAY_CLARIFICATION_ID_STABLE: FAIL**
- A2 has no clarification_id

**CLARIFICATION_REPLAY_WARNING_COUNT: 0**
- Expected: `clarification_replay` warning on replays
- Actual: No such warnings observed

**REPLAY_CONSUMED_AS_ANSWER_COUNT: 1**
- A2 consumed as clarification answer instead of restarting clarification

**STALE_SLOT_CONTAMINATION_COUNT: 0**
- All semantic frames correctly contain `sprint_id: DMS-SPRNT-2`

---

## Root Cause Analysis

**Fix under test:** `64f4e254446262d4e08c5917133a3e3b926561c8`

**Finding:** The fix does not resolve the issue. Production runtime still consumes repeat queries as clarification answers.

**Evidence:**
- Unit tests pass (mock `_ClarifyingInner` returns NEEDS_CLARIFICATION for repeats)
- Live tests fail (`dialogue_runtime.process` returns COMPLETED for repeats)
- This is the same issue identified in Assignment 064

**Root cause:** `DialogueHarnessRuntime.process()` in `dialogue_runtime.py` treats repeat queries as clarification answers when `session in self._pending`. The fix in `64f4e25` clears pending before `inner.process()`, but `inner.process()` (which is `dialogue_runtime.process()`) still interprets the query as a new request without re-opening clarification.

---

## Conclusion

**066_VERDICT: RED** - The deterministic clarification replay fix is not working in production. A2 consumes the replay as a clarification answer instead of restarting the clarification flow.

**READY_TO_RESUME_060_AND_062: NO** - Assignment 066 failed.

---

## Git Status

```
cd po-agent-platform-v2
git status --short
```

**Result:** Clean tree (only QA report file added)

**Report File:** `qa_reports/CORE8_DETERMINISTIC_CLARIFICATION_REPLAY_RETEST_066.md`
