# DIRECT REAL TASK LOOKUP RESTORATION - Assignment 094A

**Date:** 2026-08-26  
**Branch:** `feat/core8-real-query-hardening-v2`  
**Target HEAD:** `ea39619`  
**QA Role:** TESTER ONLY  
**Action:** Verify direct real task lookup restoration

---

## EXECUTIVE SUMMARY

**VERDICT:** **CERTIFIED**

**Key Finding:** Commit `ea39619` restores authoritative point lookup against real SWTR, bypassing the empty `/api/v1/tasks` cache.

**Forensic Conclusion:** `TaskApiAS21Adapter.get_task()` was broken by commit `0c2c153` which made it depend on `/api/v1/tasks` cache. Commit `ea39619` overrides `get_task()` to perform direct SWTR lookup, restoring functionality.

---

## 1. TEST EXECUTION

### 1.1 Branch Update

| Check | Status | Evidence |
|-------|--------|----------|
| Branch | ✅ PASS | `feat/core8-real-query-hardening-v2` |
| HEAD | ✅ PASS | `ea39619ed7287651b405bdb6f02193fbeb4757e6` |
| Fast-forward | ✅ PASS | `1902e41..ea39619` |

### 1.2 PO Agent Restart

| Check | Status | Evidence |
|-------|--------|----------|
| Restart | ✅ PASS | Service restarted from HEAD `ea39619` |
| Health | ✅ PASS | `/health` returns 200 |
| Runtime mode | ✅ PASS | `harness-dialogue-v2` |

---

## 2. DIRECT TASK LOOKUP TESTS

### 2.1 Test Queries

| Query | Expected Key | Status | Answer Contains Key | Not Found? |
|-------|--------------|--------|---------------------|------------|
| `Покажи DMS-271` | DMS-271 | ✅ COMPLETED | ✅ YES | ❌ NO |
| `Что с задачей DMS-338?` | DMS-338 | ✅ COMPLETED | ✅ YES | ❌ NO |
| `Найди задачу DMS-343` | DMS-343 | ✅ COMPLETED | ✅ YES | ❌ NO |
| `Какой статус у DMS-371?` | DMS-371 | ✅ COMPLETED | ✅ YES | ❌ NO |

### 2.2 Detailed Results

**Query:** `Покажи DMS-271`
```
Status: COMPLETED
Intent: task_lookup
Answer: DMS-271 — [DMS] Решить уязвимости релиза 2.4.0. Статус: Unknown. Исполнитель: Агатаева Айна Жумагалиевна.
Clarifications: None
Warnings: []
```

**Query:** `Что с задачей DMS-338?`
```
Status: COMPLETED
Intent: task_lookup
Answer: DMS-338 — [Naumen] Дефекты реализации API SafeGuard (SDP Beholder). Статус: QA. Исполнитель: Семавин Михаил Михайлович.
Clarifications: None
Warnings: []
```

**Query:** `Найди задачу DMS-343`
```
Status: COMPLETED
Intent: task_lookup
Answer: DMS-343 — [DMS] Собрать единый дистрибутив для 2.5.0. Статус: Unknown. Исполнитель: Долговской Евгений Николаевич.
Clarifications: None
Warnings: []
```

**Query:** `Какой статус у DMS-371?`
```
Status: COMPLETED
Intent: task_lookup
Answer: DMS-371 — Отказ от проверки права SELECT при выполнении EXPLAIN. Статус: Unknown. Исполнитель: Жданов Александр Николаевич.
Clarifications: None
Warnings: []
```

---

## 3. MANDATORY VERIFICATION

### 3.1 No Sprint/Project Clarification

| Test | Result |
|------|--------|
| All 4 queries | ✅ PASS - No clarification ID returned |
| Clarification required | ✅ PASS - All queries completed directly |

### 3.2 Response Returns Real Task

| Test | Result |
|------|--------|
| DMS-271 found | ✅ PASS |
| DMS-338 found | ✅ PASS |
| DMS-343 found | ✅ PASS |
| DMS-371 found | ✅ PASS |

### 3.3 /api/v1/tasks Remains Empty

**Test:**
```python
r = httpx.get('http://127.0.0.1:8003/api/v1/tasks?limit=1000')
print(r.json())  # []
```

**Result:** ✅ PASS - `/api/v1/tasks` returns empty array

**Evidence:**
```
/api/v1/tasks response type: list
/api/v1/tasks length: 0
✅ /api/v1/tasks is EMPTY (cache not populated)
```

### 3.4 Direct SWTR Lookup Works

**Test:**
```python
swtr_url = 'http://127.0.0.1:8003/api/v1/swtr-read'
r = httpx.get(f'{swtr_url}/tasks/DMS-271')
# Returns: {"task_code":"DMS-271",...}
```

**Result:** ✅ PASS - All 4 keys found via SWTR

### 3.5 No Sync Prerequisite

**Test:**
```
POST /api/v1/tasks/sync returns 405 (method not allowed)
GET /api/v1/tasks returns [] (empty, not synced)
```

**Result:** ✅ PASS - No sync required, lookup works immediately

### 3.6 Mapped Fields Match SWTR

| Task | SWTR Summary | Agent Answer | Status Match |
|------|--------------|--------------|--------------|
| DMS-271 | [DMS] Решить уязвимости... | ✅ Same | ✅ Unknown |
| DMS-338 | [Naumen] Дефекты... | ✅ Same | ✅ QA |
| DMS-343 | [DMS] Собрать единый... | ✅ Same | ✅ Unknown |
| DMS-371 | Отказ от проверки... | ✅ Same | ✅ Unknown |

### 3.7 Cold Restart Works

**Test:**
- Service restarted from HEAD `ea39619`
- Health check passed
- All 4 queries executed successfully after restart

**Result:** ✅ PASS - Lookup works after cold restart

---

## 4. FORENSIC CONCLUSION

### 4.1 Historical Context

**Commit 0c2c153 (TaskApiAS21Adapter introduced):**
```python
async def get_task(self, task_key: str) -> Optional[Task]:
    normalized = task_key.upper().strip()
    tasks = await self._fetch_tasks(limit=self._scan_limit, source="swtr")
    task = next((item for item in tasks if item.key.upper() == normalized), None)
    # ❌ Depends on /api/v1/tasks cache
```

**Problem:**
- `_fetch_tasks()` calls `/api/v1/tasks` endpoint
- `/api/v1/tasks` returns empty array (cache not populated)
- All exact-key lookups fail even though tasks exist in SWTR

### 4.2 Fix Applied (Commit ea39619)

```python
async def get_task(self, task_key: str) -> Task | None:
    """Resolve a full task key directly against live SWTR, never the cache.

    Exact-key lookup is an authoritative point read. Requiring the bounded
    `/api/v1/tasks` cache to be populated made a valid DMS-271 lookup fail
    even while `/api/v1/swtr-read/tasks/DMS-271` was healthy. Preserve the
    rich-read contract by attaching live attachment metadata after mapping.
    """
    normalized = _canonical_task_code(task_key)
    if not normalized:
        return None
    unit = await self._read_raw_unit(normalized)  # ✅ Direct SWTR call
    if unit is None:
        return None
    task = self._map_raw_unit(unit)
    if task is None:
        raise AS21SourceError(...)
    attachments = await self.get_attachment_metadata(normalized)
    return task.model_copy(update={"attachments": attachments})
```

**Key Change:**
- `_read_raw_unit()` → `/api/v1/swtr-read/tasks/{KEY}` (direct)
- No dependency on `/api/v1/tasks` cache
- Preserves rich-read contract with live attachment metadata

### 4.3 Boundary Analysis

| Component | Status | Notes |
|-----------|--------|-------|
| SWTR backend | ✅ WORKING | `/api/v1/swtr-read/tasks/{KEY}` returns task |
| Adapter `_read_raw_unit()` | ✅ WORKING | Direct SWTR call |
| `get_task()` override | ✅ WORKING | Bypasses cache |
| Mapping `_map_raw_unit()` | ✅ WORKING | Correctly extracts fields |
| PO Agent runtime | ✅ WORKING | Routes to correct capability |

---

## 5. VERIFICATION CHECKLIST

| Requirement | Status | Evidence |
|-------------|--------|----------|
| ✅ HEAD = ea39619 | PASS | Fast-forward verified |
| ✅ PO Agent restarted | PASS | Service restarted from HEAD |
| ✅ DMS-271 lookup works | PASS | COMPLETED, key in answer |
| ✅ DMS-338 lookup works | PASS | COMPLETED, key in answer |
| ✅ DMS-343 lookup works | PASS | COMPLETED, key in answer |
| ✅ DMS-371 lookup works | PASS | COMPLETED, key in answer |
| ✅ No sprint clarification | PASS | All clarification_id = None |
| ✅ No project clarification | PASS | All clarification_id = None |
| ✅ Response returns real task | PASS | All 4 tasks found |
| ✅ /api/v1/tasks empty | PASS | Returns [] |
| ✅ SWTR direct lookup works | PASS | All 4 keys exist in SWTR |
| ✅ No sync prerequisite | PASS | 405 on /sync endpoint |
| ✅ Mapped fields match SWTR | PASS | key/title/status/assignee verified |
| ✅ Cold restart works | PASS | All tests passed after restart |

---

## 6. VERDICT

**VERDICT:** **CERTIFIED**

**Rationale:**
1. ✅ All 4 direct task lookups work via PO Agent
2. ✅ No sprint/project clarification required
3. ✅ All tasks found with correct details
4. ✅ `/api/v1/tasks` remains empty (cache not populated)
5. ✅ Lookup works through `/api/v1/swtr-read/tasks/{KEY}`
6. ✅ No sync prerequisite
7. ✅ Mapped fields match SWTR data
8. ✅ Cold restart preserves functionality

### Forensic Summary

| Issue | Root Cause | Fix | Status |
|-------|------------|-----|--------|
| Task lookup failed | `get_task()` depended on empty cache | Override `get_task()` to call `_read_raw_unit()` | ✅ RESOLVED |
| DMS-271 not found | Cache never populated | Direct SWTR lookup | ✅ RESOLVED |
| All task lookups broken | Cache dependency | Bypass cache entirely | ✅ RESOLVED |

### Recommendations

1. **Long-term:** Consider implementing `/api/v1/tasks/sync` endpoint to populate cache
2. **Monitoring:** Add health check for `/api/v1/tasks` endpoint responsiveness
3. **Documentation:** Document that exact-key lookup uses direct SWTR, not cache

---

## APPENDIX A: TEST COMMANDS

```bash
# Verify HEAD
cd /path/to/PO_Agent_Harness
git log --oneline -5

# Test task lookup
python3 -c "
import httpx
r = httpx.post('http://127.0.0.1:8004/api/v1/query', 
    json={'query': 'Покажи DMS-271'}, timeout=60)
print(r.json())
"

# Verify /api/v1/tasks empty
python3 -c "
import httpx
r = httpx.get('http://127.0.0.1:8003/api/v1/tasks?limit=1000')
print(r.json())
"
```

---

**Report Generated:** 2026-08-26  
**QA Tested By:** GigaCode  
**Branch:** `feat/core8-real-query-hardening-v2`  
**Commit:** `ea39619ed7287651b405bdb6f02193fbeb4757e6`
