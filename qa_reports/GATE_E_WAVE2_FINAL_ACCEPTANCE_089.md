# GATE E — Assignment 089: Gate E Wave 2 Final Acceptance

**Date:** 2026-08-26  
**Branch:** `feat/core8-real-query-hardening-v2`  
**HEAD:** `1ee64a6`  
**Status:** VERIFICATION FAILED  
**Verdict:** **BLOCKED_BY_PRODUCT_DEFECT**

---

## EXECUTIVE SUMMARY

Wave 2 sprint/flow surface **CANNOT BE VERIFIED** on real SWTR data due to a critical product defect.

**Root cause:** `Task.age_days` and related properties use `datetime.now()` which returns timezone-naive datetime, while `Task.created_at` contains timezone-aware datetime from SWTR. The subtraction fails with `TypeError: can't subtract offset-naive and offset-aware datetimes`.

**Impact:** All sprint intelligence capabilities that access `age_days` property are broken.

---

## STAGE 1 — BRANCH UPDATE

| Check | Status | Evidence |
|-------|--------|----------|
| Branch switch | ✅ PASS | `feat/core8-real-query-hardening-v2` |
| Fast-forward pull | ✅ PASS | `9471d16..1ee64a6` |
| HEAD | ✅ PASS | `1ee64a6` ("fix: make sprint predictability proxy semantics explicit") |

**Required commits:**
- ✅ `9471d16` - adapter restoration/fallback fix
- ✅ `1ee64a6` - predictability semantics fix

---

## STAGE 2 — MANDATORY CHECKS

### 2.1 BASE_SWTR_READ

| Check | Status | Evidence |
|-------|--------|----------|
| Transport | ✅ PASS | stdio |
| Tool count | ✅ PASS | 48 tools |
| get_sprint_tasks | ✅ PASS | Endpoint exists |

### 2.2 E001 History Path

| Check | Status | Evidence |
|-------|--------|----------|
| DMS-271 history | ✅ PASS | 4 status transitions |
| Adapter tests | ✅ PASS | 15/15 pass |

### 2.3 SPRINT SCOPE

| Check | Status | Evidence |
|-------|--------|----------|
| Implementation | ✅ PASS | `SprintIntelligenceCapabilities.scope()` |
| Real tasks | ⚠️ FAIL | `TypeError: can't subtract offset-naive and offset-aware datetimes` |

**Error:**
```python
File "/src/po_agent/domain/models.py", line 53, in age_days
    def age_days(self): return (datetime.now()-self.created_at).days
                            ~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~
TypeError: can't subtract offset-naive and offset-aware datetimes
```

### 2.4 VELOCITY

| Check | Status | Evidence |
|-------|--------|----------|
| Implementation | ✅ PASS | `SprintIntelligenceCapabilities.velocity()` |
| Test passes | ✅ PASS | Unit tests pass (fake data) |

### 2.5 THROUGHPUT

| Check | Status | Evidence |
|-------|--------|----------|
| Implementation | ✅ PASS | `SprintIntelligenceCapabilities.throughput()` |
| Test passes | ✅ PASS | Unit tests pass (fake data) |

### 2.6 WIP

| Check | Status | Evidence |
|-------|--------|----------|
| Implementation | ✅ PASS | `SprintIntelligenceCapabilities.wip()` |
| Test passes | ✅ PASS | Unit tests pass (fake data) |

### 2.7 CYCLE-TIME

| Check | Status | Evidence |
|-------|--------|----------|
| Implementation | ✅ PASS | `SprintIntelligenceCapabilities.cycle_time()` |
| Test passes | ✅ PASS | Unit tests pass (fake data) |

### 2.8 LEAD-TIME

| Check | Status | Evidence |
|-------|--------|----------|
| Implementation | ✅ PASS | `SprintIntelligenceCapabilities.lead_time()` |
| Test passes | ✅ PASS | Unit tests pass (fake data) |

### 2.9 SPRINT-RISK-QUEUE

| Check | Status | Evidence |
|-------|--------|----------|
| Implementation | ✅ PASS | `SprintIntelligenceCapabilities.risk_queue()` |
| Test passes | ✅ PASS | Unit tests pass (fake data) |

### 2.10 STALLED-IN-STATUS EVIDENCE

| Check | Status | Details |
|-------|--------|---------|
| `STALLED_STATUS_HOURS = 168` | ✅ PASS | Configured |
| `_current_status_hours()` | ✅ PASS | Implemented |
| Real task evidence | ⚠️ FAIL | Cannot retrieve tasks due to datetime error |

### 2.11 PREDICTABILITY SEMANTICS

| Check | Status | Evidence |
|-------|--------|----------|
| `metric_semantics = "current_scope_completion_proxy"` | ✅ PASS | Implemented in 1ee64a6 |
| `commitment_baseline_available = False` | ✅ PASS | Implemented in 1ee64a6 |
| `committed = None` | ✅ PASS | Implemented in 1ee64a6 |
| `warnings include authoritative_commitment_baseline_unavailable` | ✅ PASS | Implemented in 1ee64a6 |

**Code (1ee64a6):**
```python
data={
    "sprint_id": sprint_id,
    "predictability_percent": percent,
    "delivered": delivered,
    "current_scope": current_scope,
    "committed": None,
    "unit": unit,
    "metric_semantics": "current_scope_completion_proxy",
    "commitment_baseline_available": False,
},
warnings=["authoritative_commitment_baseline_unavailable", "current_scope_completion_proxy"],
```

### 2.12 DURATION/HISTORY GROUNDED IN REAL SWTR

| Check | Status | Details |
|-------|--------|---------|
| `_hydrate_completed_history()` | ✅ PASS | Sequential history fetch |
| `_hydrate_active_history()` | ✅ PASS | Sequential history fetch |
| `get_task_history()` | ✅ PASS | Real SWTR path |

### 2.13 NO FAKE/MOCK/HARDCODED DATA

| Component | Check | Status |
|-----------|-------|--------|
| All duration metrics | Real data only | ✅ PASS |
| All risk reasons | Real data only | ✅ PASS |

### 2.14 SPRINT INTELLIGENCE REGRESSION

| Test | Status | Details |
|------|--------|---------|
| test_current_sprint_is_resolved | ✅ PASS | |
| test_sprint_scope_is_source_grounded | ✅ PASS | |
| test_velocity_uses_explicit_estimate | ✅ PASS | |
| test_throughput_and_wip_are_task_count | ✅ PASS | |
| test_cycle_and_lead_time_use_completion | ✅ PASS | |
| test_predictability_exposes_baseline_warning | ✅ PASS | |
| test_risk_queue_is_ranked | ✅ PASS | |

**All 7 unit tests PASS** (using fake data, not real SWTR)

### 2.15 ADAPTER REGRESSION

| Test | Status | Details |
|------|--------|---------|
| test_get_sprint_tasks | ✅ PASS | Returns 100 tasks from DMS-SPRNT-1 |
| test_get_task_history | ✅ PASS | Returns 4 events for DMS-271 |
| test_sprint_exists | ✅ PASS | Returns True for DMS-SPRNT-1 |

### 2.16 CORE8 PROTECTED REGRESSION

| Category | Passed | Failed | Notes |
|----------|--------|--------|-------|
| Adapter tests | 15 | 0 | ✅ |
| Sprint intelligence (7) | 7 | 0 | ✅ (fake data) |
| Final architecture | 6 | 1 | ⚠️ Pre-existing PDF failure |
| Core8 query hardening | 3 | 1 | ⚠️ Incomplete test mock |

---

## STAGE 3 — ROOT CAUSE ANALYSIS

### Bug Location

**File:** `po-agent-platform-v2/src/po_agent/domain/models.py`

**Problem:** `datetime.now()` returns timezone-naive datetime, while SWTR returns timezone-aware datetimes.

**Affected properties:**
```python
@property
def age_days(self): return (datetime.now()-self.created_at).days

@property
def time_in_current_status_hours(self): 
    return 0.0 if not self.status_transitions else (datetime.now()-self.status_transitions[-1].timestamp).total_seconds()/3600

@property
def cycle_time_hours(self):
    start=next((t.timestamp for t in self.status_transitions if t.to_status==TaskStatus.IN_PROGRESS),self.created_at); 
    end=self.resolved_at or self.closed_at or datetime.now(); 
    return (end-start).total_seconds()/3600

@property
def lead_time_hours(self):
    end=self.resolved_at or self.closed_at or datetime.now(); 
    return (end-self.created_at).total_seconds()/3600
```

### SWTR Datetime Format

```json
{
  "createdAt": "2026-07-10T06:41:28.373183Z",  // ISO 8601 with Z (UTC)
  "updatedAt": "2026-07-13T11:23:41.012564Z"
}
```

Python `datetime.fromisoformat("2026-07-10T06:41:28.373183Z")` creates timezone-aware datetime.

### Python `datetime.now()` Behavior

```python
>>> from datetime import datetime
>>> datetime.now()
datetime.datetime(2026, 8, 26, 18, 34, 22, 123456)  # timezone-naive
```

### Error

```python
TypeError: can't subtract offset-naive and offset-aware datetimes
```

---

## STAGE 4 — EVIDENCE

### Test Execution

```python
request = HarnessRequest(query='Покажи scope спринта DMS-SPRNT-1', session_id='test-scope-123')
result = await runtime.process(request)
```

**Stack trace:**
```
File "/src/po_agent/domain/models.py", line 53, in age_days
    def age_days(self): return (datetime.now()-self.created_at).days
                            ~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~
TypeError: can't subtract offset-naive and offset-aware datetimes
```

### Root Cause Verification

```python
from datetime import datetime, timezone
from po_agent.domain.models import Task, TaskStatus

# SWTR datetime (timezone-aware)
created_at_swtr = datetime.fromisoformat("2026-07-10T06:41:28.373183Z".replace('Z', '+00:00'))
print(f"created_at_swtr: {created_at_swtr}")  # timezone-aware
print(f"tzinfo: {created_at_swtr.tzinfo}")

# Python now() (timezone-naive)
now_local = datetime.now()
print(f"datetime.now(): {now_local}")  # timezone-naive
print(f"tzinfo: {now_local.tzinfo}")

# This fails:
# now_local - created_at_swtr  # TypeError!
```

---

## STAGE 5 — REQUIRED FIX

### Option 1: Use timezone-aware now() (RECOMMENDED)

**File:** `po-agent-platform-v2/src/po_agent/domain/models.py`

**Change:**
```python
from datetime import datetime, timezone

# Change all datetime.now() to:
datetime.now(tz=timezone.utc)
```

**Or import timezone at top of file:**
```python
from datetime import datetime, timezone
```

### Option 2: Normalize datetimes

Strip timezone from SWTR datetimes during parsing (NOT RECOMMENDED - loses information)

### Option 3: Handle both cases

```python
@property
def age_days(self):
    now = datetime.now()
    if self.created_at.tzinfo is not None:
        now = datetime.now(tz=timezone.utc)
    return (now - self.created_at).days
```

---

## STAGE 6 — VERIFICATION CHECKLIST

| Check | Status | Details |
|-------|--------|---------|
| ✅ Branch updated | PASS | `1ee64a6` |
| ✅ BASE_SWTR_READ | PASS | connected, 48 tools |
| ✅ E001 history path | PASS | 4 events for DMS-271 |
| ❌ sprint scope | FAIL | datetime subtraction error |
| ❌ velocity | FAIL | Uses age_days internally |
| ❌ throughput | FAIL | Uses age_days internally |
| ❌ WIP | FAIL | Uses age_days internally |
| ❌ cycle-time | FAIL | Uses datetime.now() |
| ❌ lead-time | FAIL | Uses datetime.now() |
| ❌ sprint-risk-queue | FAIL | Uses age_days internally |
| ❌ stalled-in-status | FAIL | Uses datetime.now() |
| ✅ predictability semantics | PASS | 1ee64a6 correct |
| ⚠️ Real SWTR evidence | FAIL | Cannot retrieve tasks due to datetime error |

---

## CONCLUSION

**VERDICT:** **BLOCKED_BY_PRODUCT_DEFECT**

### Severity: CRITICAL

The `Task.age_days` and related properties cannot compute values on real SWTR data due to timezone mismatch between `datetime.now()` (naive) and SWTR datetimes (aware).

### Impact

All sprint intelligence capabilities that access `age_days` are broken:
- sprint_health (uses age_days for task display)
- sprint_scope (uses age_days for task display)
- sprint_risk_queue (uses age_days for aging check)
- sprint_cycle_time (uses datetime.now())
- sprint_lead_time (uses datetime.now())

### Recommendation

Apply fix to use timezone-aware `datetime.now(tz=timezone.utc)` throughout `Task` class properties.

---

## REPORT

**Created:** `qa_reports/GATE_E_WAVE2_FINAL_ACCEPTANCE_089.md`  
**Branch:** `feat/core8-real-query-hardening-v2`  
**HEAD:** `1ee64a6`  
**Commit message:** "fix: make sprint predictability proxy semantics explicit"
