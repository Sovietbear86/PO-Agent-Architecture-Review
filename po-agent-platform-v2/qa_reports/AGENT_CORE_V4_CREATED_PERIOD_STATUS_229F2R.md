# A229F2R — Created-Period + Status Re-Gate

**Verdict:** `AGENT_CORE_V4_CREATED_PERIOD_STATUS_RED_A229F2R`

**Classification:** `RED_P0_TEST_LOGIC_TASKSTATUS_DONE`

**START_HEAD:** `79f5191`
**Checkpoint:** `9d71a79` (A229F1R2 GREEN)
**Date:** 2026-10-04
**STOP at:** P0 (test regression)

---

## P0 — Integrity

### P0.1 Core files byte-identical to checkpoint 9d71a79

| File | Blob @ 79f5191 | Blob @ 9d71a79 | Match |
|------|---------------|----------------|-------|
| `contracts.py` | `20d93d5d` | `20d93d5d` | ✅ |
| `agent_core_v4.py` | `52100ca1` | `52100ca1` | ✅ |
| `agent_core_v4_robust.py` | `3bdb4d09` | `3bdb4d09` | ✅ |
| `api/v1/__init__.py` | `8f4b1663` | `8f4b1663` | ✅ |

**4/4 byte-identical.** No Core/planner/runtime/session modifications.

### P0.2 Owner diff audit

Plugin-only diff (2 files + 1 test):
- `_task_live_handlers.py` (+12): optional `status` param in `build_task_search_created`, reuses existing `_matches_requested_status`; adds `status` to result data.
- `task_catalog.py` (+6): adds `status` arg to capability spec; updates skill procedure text (single-capability guidance + no-invented-status rule).
- `test_agent_core_v4_task_created_period.py` (+92): extends `_task` helper with `status` param; adds 2 new status-constraint tests.

No phrase router, no surname/STS/5-days special branch, no local date/status cache. Design is clean.

### P0.3 Focused created-period tests

**Result: 4 FAILED / 2 PASSED**

| Test | Result | Root cause |
|------|--------|------------|
| `test_created_period_parses_explicit_inclusive_dates` | ✅ PASSED | — |
| `test_created_period_parses_last_two_calendar_days` | ✅ PASSED | — |
| `test_created_period_search_filters_only_source_created_timestamps` | ❌ FAILED | `TaskStatus.DONE` AttributeError |
| `test_created_period_search_fails_closed_if_created_at_is_not_source_backed` | ❌ FAILED | `TaskStatus.DONE` AttributeError |
| `test_created_period_search_preserves_open_status_constraint` | ❌ FAILED | `TaskStatus.DONE` AttributeError |
| `test_created_period_search_preserves_in_progress_status_constraint` | ❌ FAILED | `TaskStatus.DONE` AttributeError |

### P0.4 Full V4 blast

**Result: 236 passed / 4 failed** (A229F1R2 was 238/238)

All 4 failures share the same root cause. No other regressions.

### P0.5 Root cause

`tests/test_agent_core_v4_task_created_period.py:28` in the `_task` helper:

```python
is_completed = status in {TaskStatus.CLOSED, TaskStatus.DONE}
```

`TaskStatus` enum (`src/po_agent/domain/models.py:31`) has no `DONE` member. Available terminal values: `CLOSED`, `CANCELLED`, `RESOLVED`.

Because Python evaluates the set literal `{TaskStatus.CLOSED, TaskStatus.DONE}` eagerly, **every call to `_task()`** raises `AttributeError: type object 'TaskStatus' has no attribute 'DONE'`, regardless of the actual `status` argument.

**Impact:**
- 2 previously-passing tests from A229F1R2 regression (`test_created_period_search_filters_only_source_created_timestamps`, `test_created_period_search_fails_closed_if_created_at_is_not_source_backed`).
- 2 newly-added tests also fail for the same reason.

### P0.6 Owner fix

Replace `TaskStatus.DONE` with a valid terminal enum member. The intent appears to be "any terminal status", so the most correct fix is:

```python
is_completed = status in {TaskStatus.CLOSED, TaskStatus.CANCELLED, TaskStatus.RESOLVED}
```

Alternatively, if only `CLOSED` is used in the fixtures, simply:

```python
is_completed = status == TaskStatus.CLOSED
```

Then re-gate from P0.3.

---

## P1–P5 — SKIPPED

Not executed per first-RED STOP rule.

---

## Services

| Service | Port | PID | Status |
|---------|------|-----|--------|
| MCP-SWTR | 3000 | 88403 | ✅ UP |
| Task API | 8241 | 88843 | ✅ UP |
| Agent V4 | 8004 | 95481 | ✅ UP @ 79f5191 |
| Vite UI | 5175 | 89595 | ✅ UP |

---

## Recommendation

Owner fix (one line in test file): replace `TaskStatus.DONE` with the correct terminal enum set, then re-gate from P0.3 onward. The production plugin diff is architecturally sound and clean.
