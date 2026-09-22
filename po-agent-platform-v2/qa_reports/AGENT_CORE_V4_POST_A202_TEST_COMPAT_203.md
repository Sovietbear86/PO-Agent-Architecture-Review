# A203 — Post-A202 Test Compatibility Check

**Date:** 2026-09-22
**Verdict:** `AGENT_CORE_V4_POST_A202_TEST_COMPAT_RED`
**START_HEAD:** `2e359d46c1cd5f6fc876ec3c779375355374367e`
**A202 checkpoint:** `e580489950e5a149a6a740cb8779dfdb0351d471` / `checkpoint/v4-pre-wave-s-a202`

## Executive summary

Diff `e580489..2e359d4` is **test/docs only** (zero source/frontend/plugin changes). Runtime sanity is fully GREEN. The sole blocker: **1 owner test still fails** — `test_invalid_clarification_option_does_not_replan_as_standalone_query` (line 213 of `test_v4_owner_fix_contracts.py`) was missed in commit `a914977` (which fixed line 187 but not 213). The fix is a one-line change: `effective, early =` → `effective, early, continuation =`.

## Phase 0 — diff audit (PASS)

| Category | Files changed | Verdict |
|---|---|---|
| Production source (`src/`) | **0** | ✅ No runtime changes |
| Frontend (`frontend/src/`) | **0** | ✅ No UI changes |
| Plugins (`v4_plugins/`) | **0** | ✅ No plugin changes |
| Tests | `test_v4_browser_api_contract.py` (+`available_facts`), `test_v4_owner_fix_contracts.py` (line 187 tuple fix) | Test-only ✅ |
| Docs/specs | `GIGACODE_NEXT_ACTION.md`, `V4_54_SKILL_MIGRATION_PLAN.md`, `V4_DOD_LOCK.md` | Docs ✅ |
| QA report | `AGENT_CORE_V4_POST_GREEN_HYGIENE_SMOKE_202.md` (A202) | Report ✅ |

**Zero product/runtime changes after A202 checkpoint.**

## Phase 1 — focused tests (64 passed, 1 FAILED)

| Suite | Result |
|---|---|
| `test_v4_owner_fix_contracts.py` | 10 pass, **1 FAIL** (`test_invalid_clarification_option_does_not_replan_as_standalone_query`: line 213 `effective, early = _prepare_query(` — 2-tuple unpack on 3-tuple return) |
| `test_v4_browser_api_contract.py` | **11/11** (health mock fix verified: `available_facts` present) |
| `test_agent_core_v4_completion_contract.py` | **23/23** |
| `test_agent_core_v4_plugin_registry.py` + `test_agent_core_v4_task_catalog.py` | **20/20** |
| **Total** | **64 passed, 1 failed** |

### Root cause of the 1 failure

Commit `a914977` fixed line 187 (`test_clarification_is_session_bound_and_fails_closed_in_russian`) but **missed line 213** (`test_invalid_clarification_option_does_not_replan_as_standalone_query`), which still unpacks `_prepare_query` as a 2-tuple:

```python
# line 213 (current, BROKEN):
effective, early = _prepare_query(...)

# required fix:
effective, early, continuation = _prepare_query(...)
```

This is an owner test-only bug, not a production defect.

## Phase 2 — minimal runtime sanity (PASS)

| Check | Result |
|---|---|
| UI (localhost:5175) | 200 |
| Agent `/live` | 200 / 27ms |
| **Agent `/health`** | **200 / 81ms** (A202 fix retained) |
| Task API `swtr-read/health` | 200 |
| MCP-SWTR (port 3000) | OPEN |
| Factual query (DMS-380) | **COMPLETED** `runtime_contract`, source-accurate, 39.2s |
| Clarification continuation (turn1) | **NEEDS_CLARIFICATION** (typed, cid present, 36.0s); empty options = LLM non-determinism (same A199–A201 F3 class); safe, no false completion |

## Verdict

`AGENT_CORE_V4_POST_A202_TEST_COMPAT_RED` — single owner test bug (1 line, line 213 of `test_v4_owner_fix_contracts.py`).

**Owner fix needed:** change `effective, early = _prepare_query(` to `effective, early, continuation = _prepare_query(` on line 213. Then re-run `pytest tests/test_v4_owner_fix_contracts.py` — expect 11/11. No production change required.

**Wave S may begin only after this 1-line fix + re-run + explicit owner/user approval.**

## Services left running (HEAD 2e359d4)

| Service | URL | PID | Health |
|---|---|---|---|
| UI | http://localhost:5175 | 55206 | 200 |
| Agent | http://127.0.0.1:8212 | 63078 | `/live` 200, `/health` 200 / 81ms, EXPECTED_HEAD=`e580489` (runtime) |
| Task API | http://127.0.0.1:8241 | 55200 | 200 |
| MCP-SWTR | http://127.0.0.1:3000/sse | 55196 | OPEN |
