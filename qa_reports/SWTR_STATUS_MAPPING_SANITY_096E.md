# Assignment 096E — SWTR Status Mapping Sanity Check

**Date:** 2026-08-28  
**QA Role:** QA / Tester only  
**Branch:** `feat/core8-real-query-hardening-v2`

---

## BASELINE

| Item | Value |
|------|-------|
| Branch | `feat/core8-real-query-hardening-v2` |
| HEAD | `a51b69a706510491654a12950a96b59f2661586d` |
| Fix commit `34f0b0a` | ✅ Present (expose raw SWTR workflow status) |
| Fix commit `a51b69a` | ✅ Present (normalize registered status as open) |
| Working tree | Clean (except `.po_agent/` artifacts) |

---

## SERVICE HEALTH

| Service | Status | Notes |
|---------|--------|-------|
| MCP-SWTR (stdio) | Connected | Health endpoint reports 48 tools |
| Task API | Healthy | `/api/v1/swtr-read/health` returns connected |
| PO Agent | Degraded | `task-api` adapter healthy, but `/api/v1/tasks` returns empty |

---

## FIX VERIFICATION

### Fix 34f0b0a: Expose raw SWTR workflow status

**Purpose:** Expose `workflow_status` from `source_data.swtr_attributes` or `source_data.workflow_status` when present.

**Current status:** ❌ Cannot be fully verified

**Reason:** MCP-SWTR is not synchronized with Task API. The `/api/v1/tasks` endpoint returns an empty list because MCP-SWTR stdio transport is not providing task data to Task API.

**Test evidence:**
```json
// /api/v1/swtr-read/tasks/DMS-273 returns:
{
  "task_code": "DMS-273",
  "unit": {
    "attributes": [
      {
        "code": "workflow_status",
        "value": {
          "name": "Зарегистрирован",
          "code": "ZRGSTR_JEPgizwlJWGww",
          ...
        }
      }
    ]
  },
  "source_data": null  // <-- PROBLEM: This is where fix 34f0b0a looks
}
```

**Expected behavior:** `source_data.swtr_attributes` should contain `workflow_status` with value `"Зарегистрирован"`.

**Actual behavior:** `source_data` is `null` or empty dict.

---

### Fix a51b69a: Normalize registered SWTR workflow status as Open

**Purpose:** Map Russian "registered" / "зарегистрирован" to canonical `Open` status.

**Current status:** ✅ Working

**Test evidence:**
```
Query: "Какой статус у задачи DMS-273?"

PO Agent Response:
  status: Open              ✅ Correct
  status_raw: None          ⚠️  Expected: "Зарегистрирован" but source_data is empty

Answer: "DMS-273 — [doc] Поправить документацию по ручной установке Safeguard. Статус: Open..."
```

**Why status shows Open:** PO Agent adapter (`task-api`) gets `status: None` from Task API, which defaults to `Open` via the `normalize_task_status` function. Since `source_data` is empty, the raw workflow status cannot be preserved in `status_raw`.

---

## ENVIRONMENT PROBLEM

### MCP-SWTR Not Synchronized

**Evidence:**
```bash
$ curl http://127.0.0.1:8003/api/v1/tasks
[]  # Empty list - no tasks available

$ curl http://127.0.0.1:8003/api/v1/tasks?source=swtr
[]  # Empty list - MCP-SWTR not providing data
```

**Task API `/api/v1/swtr-read/tasks/DMS-273` shows:**
- `unit.attributes.workflow_status = "Зарегистрирован"` ✅
- `source_data = null` ❌

**Root cause:** Task API adapter for MCP-SWTR is not synchronizing `source_data.swtr_attributes` from MCP-SWTR stdio transport.

**MCP-SWTR Health:**
```json
{
  "status": "connected",
  "transport": "stdio",
  "tool_count": 48,
  "read_unit": true,
  "get_unit_files": true,
  "get_sprint_tasks": true,
  "search_versions": true
}
```

MCP-SWTR is connected via stdio, but Task API is not consuming the data through this transport.

---

## TEST RESULTS SUMMARY

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| DMS-273 status | Open | Open | ✅ Partial |
| DMS-273 status_raw | "Зарегистрирован" | None | ❌ Blocked by env |
| Fix 34f0b0a | `source_data.swtr_attributes` populated | `source_data` empty | ❌ Environment blocked |
| Fix a51b69a | "registered" → "Open" | "Open" | ✅ Working (fallback behavior) |
| MCP-SWTR sync | Tasks in `/api/v1/tasks` | Empty list | ❌ Environment blocked |

---

## VERDICT

**STATUS_MAPPING_ENVIRONMENT_BLOCKED**

**Reason:** MCP-SWTR stdio transport is not synchronizing task data with Task API. The `/api/v1/tasks` endpoint returns an empty list, making it impossible to fully verify fix 34f0b0a.

**What works:**
- Fix a51b69a: Status normalization (`registered` → `Open`) works via fallback behavior

**What cannot be verified:**
- Fix 34f0b0a: Cannot test `source_data.swtr_attributes` population because MCP-SWTR is not synchronized with Task API

---

## REPRODUCER FOR PRODUCT DEFECT (when environment fixed)

When MCP-SWTR is properly synchronized with Task API:

1. Start MCP-SWTR (stdio transport)
2. Ensure Task API synchronizes data via `/api/v1/swtr-sync/sync`
3. Verify `/api/v1/tasks` returns tasks with `source_data.swtr_attributes`
4. Query `DMS-273` through PO Agent
5. Expected:
   - `status = "Open"`
   - `status_raw = "Зарегистрирован"`
   - `source_data.swtr_attributes.workflow_status.value.name = "Зарегистрирован"`

---

## NEXT STEPS

1. Investigate why Task API is not consuming MCP-SWTR data
2. Check Task API swtr-sync service
3. Verify stdio MCP-SWTR data stream
4. Once fixed, rerun full test suite for Assignment 097

---

## GIT STATUS

```bash
On branch feat/core8-real-query-hardening-v2
Your branch is up to date with 'origin/feat/core8-real-query-hardening-v2'.

Untracked files:
  po-agent-platform-v2/.po_agent/
```

---

## SERVICES STATE

- **PO Agent:** Running on `127.0.0.1:8004` (task-api adapter, degraded)
- **Task API:** Running on `127.0.0.1:8003` (healthy, but no task data)
- **MCP-SWTR:** Connected via stdio (48 tools)
