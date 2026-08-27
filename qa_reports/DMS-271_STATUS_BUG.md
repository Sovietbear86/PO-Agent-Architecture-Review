# DMS-271 STATUS BUG

**Date:** 2026-08-27  
**Agent version:** HEAD 8c7d3a2f40f7aa9165ef37c0f9f63afdbbf3f9a4

---

## PROBLEM

Agent returns `Unknown` status for task DMS-271, but actual SWTR status is `Resolved`.

### Actual SWTR Data

```json
{
  "code": "workflow_status",
  "name": "Статус",
  "value": {
    "name": "Resolved",
    "code": "RSLVD_iDxZrfBaaZfOTL",
    "statusType": "done"
  }
}
```

### Agent Response

```
Query: "Покажи задачу DMS-271"
Status: Unknown
```

---

## ROOT CAUSE

**File:** `po-agent-platform-v2/src/po_agent/adapters/hardened_production_task_api.py`  
**Line:** 184

```python
status_raw = status_value.get("code") or status_value.get("name") or ""
```

**Problem:** Uses `code` (random hash `RSLVD_iDxZrfBaaZfOTL`) instead of `name` (`Resolved`).

**Result:** 
- `status_raw = "RSLVD_iDxZrfBaaZfOTL"` (invalid)
- `normalize_task_status("RSLVD_iDxZrfBaaZfOTL")` → `TaskStatus.UNKNOWN` (fallback)

---

## FIX REQUIRED

**Change line 184 to:**
```python
status_raw = status_value.get("name") or status_value.get("code") or ""
```

This prioritizes human-readable `name` field over machine-readable `code` field.

---

## VERIFICATION

After fix:
- `status_raw = "Resolved"` (valid)
- `normalize_task_status("Resolved")` → `TaskStatus.RESOLVED` ✅

---

## AFFECTED FILES

1. `po-agent-platform-v2/src/po_agent/adapters/hardened_production_task_api.py` (line 184)

**Priority:** HIGH  
**Impact:** All tasks with non-standard status codes will show as `Unknown`

---

**Status:** BUG IDENTIFIED  
**QA Recommendation:** Fix line 184 in hardened_production_task_api.py
