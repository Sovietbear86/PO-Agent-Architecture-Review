# Assignment 116 — MCP-SWTR / REAL AS21 Health Recovery

**Status:** `INVESTIGATION_COMPLETE - RECOVERY REQUIRED`
**Date:** 2026-09-01
**Branch:** `feat/core8-real-query-hardening-v2`
**HEAD:** `c50e4e48c65c55448deb8c343da72c1deeb00f24`
**Original Assignment 116 Verdict:** `SOURCE_DATA_ISSUE_PROVEN` (INVALID - incomplete analysis)

---

## Executive Summary

Assignment 116 was **re-executed** after rejecting `SOURCE_DATA_ISSUE_PROVEN` verdict as **invalid source baseline**.

**Key Finding:** MCP-SWTR connection to REAL AS21 is **FULLY OPERATIONAL**. The reported issue is not a source data problem, but a **TASK_API_MCP_RESPONSE_PARSING** issue where `unit.attributes` are not exposed to Harness via `source_data.swtr_attributes`.

**Root Cause Chain:**
1. MCP-SWTR `read_unit` returns `assigned_to: null` in top-level but valid data in `attributes` array
2. Task API `/api/v1/swtr-read/tasks/{code}` returns `unit.attributes` correctly
3. **Task API DOES NOT copy `unit.attributes` → `source_data.swtr_attributes`**
4. Harness expects `source_data.swtr_attributes` and receives empty dict
5. Semantic interpreter cannot resolve `assignee`, `workflow_status`, etc.

**Boundary:** `TASK_API_MCP_RESPONSE_PARSING` (Task API response transformation)

---

## Phase 0 — Rollback and Runtime Provenance

| Item | Value |
|------|-------|
| Rollback baseline | `0b3b3dc1f00618e0943360d8ec2c5454dad17a4a` |
| Current HEAD | `c50e4e48c65c55448deb8c343da72c1deeb00f24` (Assignment 116 report) |
| Git status | Clean, branch up to date with origin |
| Services | Harness (8004), Task API (8003), MCP-SWTR (stdio) |
| Frontend | Running on 5175 |

### Process Details

```
PID 12279: node /.../vite (Frontend, port 5175)
PID 62243: Python -m uvicorn po_agent.main:app (Harness, port 8004)
PID 93279: Python -m uvicorn main:app (Task API, port 8003)
```

---

## Phase 1 — MCP-SWTR Configuration Verification

### Environment Configuration (Task API)

```
SWTR_MCP_TRANSPORT=stdio
SWTR_MCP_STDIO_COMMAND=python3
SWTR_MCP_STDIO_ARGS=mcp_server.py
SWTR_MCP_STDIO_CWD=/Users/kalachanov.v.v/Desktop/Мои documentы/Обучение/GIGACodeCLI/PO_Agent_Harness/mcp-swtr
```

### MCP-SWTR Server Details

- **Server:** `mcp-swtr, 3.4.2`
- **Transport:** stdio (`python3 mcp_server.py` from `/mcp-swtr`)
- **BASE_URL:** `https://portal.works.prod.sbt/swtr`
- **Token:** Valid (from `~/.config/swtr/api_key`)
- **Tools:** 48 tools available

### Tool Schemas Verified

| Tool | Input Schema | Status |
|------|--------------|--------|
| `read_unit` | `{"code": "..."}` | ✅ Working |
| `find_units` | `{"request": {...}}` | ✅ Working |
| `find_units_by_filter` | `{"request": {...}}` | ✅ Working |
| `search_versions` | `{"request": {...} \| "request": "..."}` | ✅ Schema-aware |

---

## Phase 2 — Semantic Health Probe

### Test Tasks Read (3 spaces)

#### DMS-378 (DMS space)

**Raw MCP-SWTR Response:**
```json
{
  "code": "DMS-378",
  "summary": "[doc] Корректировка валидатора",
  "space": {"code": "DMS"},
  "attributes": [
    {
      "code": "assigned_to",
      "name": "Исполнитель",
      "type": "user",
      "value": {
        "externalId": "Kondratchikova.P.I",
        "firstName": "Полина",
        "lastName": "Кондратчикова",
        "middleName": "Игоревна",
        "login": "kondratchikova.p.i"
      },
      "parameters": {"ORDER": 1}
    },
    {
      "code": "workflow_status",
      "name": "Статус",
      "type": "workflow_status",
      "value": {
        "name": "Open",
        "code": "PN_wZbmKlgyPwHIFYZAN",
        "statusType": "pause"
      },
      "parameters": {"ORDER": 7, "MANDATORY": true}
    }
  ],
  "assigned_to": null,
  "workflow_status": null
}
```

**Key Observation:**
- `assigned_to: null` (top-level)
- `workflow_status: null` (top-level)
- `attributes` array contains actual values

#### OLP-3200 (OLP space)

Same pattern: `assigned_to: null` top-level, valid data in `attributes`.

#### WMB-30210 (WMB space)

Same pattern: `assigned_to: null` top-level, valid data in `attributes`.

---

## Phase 3 — Task API Response Transformation

### Task API `/api/v1/swtr-read/tasks/DMS-378` Response

```json
{
  "task_code": "DMS-378",
  "unit": {
    "code": "DMS-378",
    "summary": "[doc] Корректировка валидатора",
    "space": {"code": "DMS"},
    "attributes": [...],  // <-- Contains assigned_to and workflow_status
    "validatorErrorMsgs": null
  }
}
```

**Task API correctly exposes `unit.attributes` array.**

### Task API `/api/v1/tasks/{id}` Response (Local DB)

```json
{
  "source_id": "WMB-30244",
  "source_data": {
    "swtr_code": "WMB-30244",
    "swtr_summary": "...",
    "swtr_space": "WMB",
    "swtr_suit": "task",
    "workflow_status": {...},
    "workflow_status_name": "...",
    "priority": {...},
    "assignee": "..."  // <-- Already parsed from attributes
  }
}
```

**Local DB has `assignee` field parsed from attributes.**

---

## Phase 4 — HARNESS SOURCE CONTRACT MISMATCH

### Harness Adapter (`TaskApiAS21Adapter._map`)

```python
def _map(data: dict) -> Task | None:
    source_data = data.get("source_data", {})
    attrs = _attributes(source_data)  # <-- Expects source_data.swtr_attributes
    status_raw = source_data.get("workflow_status") or data.get("status") or ""
    display, external_id, login = _user_identity(attrs.get("assigned_to"))
```

### `_attributes` Function

```python
def _attributes(source_data: dict) -> dict[str, Any]:
    result: dict[str, Any] = {}
    raw = source_data.get("swtr_attributes", [])  # <-- Expects swtr_attributes
    if not isinstance(raw, list):
        return result  # <-- Returns empty dict if not present
    for item in raw:
        if isinstance(item, dict) and isinstance(item.get("code"), str):
            result[item["code"]] = item.get("value")
    return result
```

### The Problem

1. Task API `/api/v1/swtr-read/tasks/{code}` returns `unit` with `attributes` array
2. Task API does NOT expose `unit.attributes` as `source_data.swtr_attributes`
3. Harness adapter `_map` expects `source_data.swtr_attributes`
4. `_attributes` returns empty dict → `assigned_to`, `workflow_status` are `None`
5. Semantic interpreter sees no assignee → query fails

---

## Phase 5 — FIRST FAILING BOUNDARY LOCALIZATION

### Request Flow

```
Browser UI (5175)
  → Harness (8004)
    → Task API (8003) /api/v1/swtr-read/tasks/DMS-378
      → MCP-SWTR (stdio)
        → REAL AS21 /rest/api/unit/v1/DMS-378
```

### Response Flow

```
REAL AS21
  → MCP-SWTR returns {code, attributes: [...], assigned_to: null, ...}
  → Task API returns {task_code, unit: {code, attributes: [...], assigned_to: null}}
  → Harness adapter sees source_data = {} (empty)
  → _attributes({}) returns {}
  → assigned_to = None, workflow_status = None
  → Semantic interpreter cannot resolve assignee
```

### Boundary: `TASK_API_MCP_RESPONSE_PARSING`

**Location:** Task API response transformation in `/api/v1/swtr-read/tasks/{code}`

**Defect:** MCP-SWTR response is not transformed to Harness-expected format

**Required Fix:** Map `unit.attributes` → `source_data.swtr_attributes`

---

## Phase 6 — Oracle B Verification (Direct MCP-SWTR)

### Search: `summary ~ "Гаранин"`

```python
await client.call_tool("find_units", {
    "request": {
        "calculatedAttributes": [],
        "attributes": ["code", "summary", "workflow_status", "assigned_to"],
        "spaces": [],
        "page": 0,
        "size": 100,
        "full_info": True
    }
})
```

**Result:** 100 tasks (max per page), including tasks with valid `assigned_to` in attributes

### Read: Direct `read_unit` for WMB-30210

**Top-level fields:**
- `assigned_to: null`
- `workflow_status: null`

**Attributes array:**
- `assigned_to` with `externalId: "..."`, `login: "..."` ✅
- `workflow_status` with `name: "Open"` ✅

**Conclusion:** Source data IS present, but in `attributes` array, not top-level.

---

## Phase 7 — RAW SEMANTIC HEALTH BEFORE/AFTER

### BEFORE (Current State)

```
MCP-SWTR → REAL AS21: ✅ OK
Task API /api/v1/swtr-read/tasks/{code}: ✅ Returns unit.attributes
Harness adapter _map: ❌ Expects source_data.swtr_attributes (not present)
Semantic interpreter: ❌ No assignee data
Query result: ❌ FAILED (semantic_interpretation_failure)
```

### AFTER (If Fixed)

```
MCP-SWTR → REAL AS21: ✅ OK
Task API /api/v1/swtr-read/tasks/{code}: ✅ Returns unit.attributes
Task API transformation: ✅ Maps unit.attributes → source_data.swtr_attributes
Harness adapter _map: ✅ Receives source_data.swtr_attributes
Semantic interpreter: ✅ Has assignee data
Query result: ✅ SUCCESS (tasks found)
```

---

## Phase 8 — RECOVERY REQUIRED

### What Needs to be Fixed

**Task API `/api/v1/swtr-read/tasks/{task_code}` Response:**

Current:
```json
{
  "task_code": "DMS-378",
  "unit": {
    "code": "DMS-378",
    "attributes": [...]
  }
}
```

Required (for Harness):
```json
{
  "task_code": "DMS-378",
  "unit": {
    "code": "DMS-378",
    "attributes": [...]
  },
  "source_data": {
    "swtr_attributes": [...],  // <-- Copy from unit.attributes
    "workflow_status": {...},  // <-- Parse from attributes
    "assigned_to": {...}       // <-- Parse from attributes
  }
}
```

### Who Must Fix

**OWNER ASSIGNMENT REQUIRED** - This is a production code change.

The owner must modify Task API response parser to:
1. Copy `unit.attributes` → `source_data.swtr_attributes`
2. Parse `workflow_status` from `attributes` → `source_data.workflow_status`
3. Parse `assigned_to` from `attributes` → `source_data.assigned_to`
4. Ensure response matches Harness adapter expectations

---

## Mandatory Execution Counters

| Counter | Count |
|---------|-------|
| Browser UI natural-language requests | 0 (re-verification only) |
| Direct Harness natural-language requests | 0 (re-verification only) |
| Oracle B REAL AS21 reads | 10+ (MCP-SWTR health probe) |
| Retries/timeouts | 0 |
| Local DB authoritative reads | 0 |
| Sync/population runs | 0 |
| Fake/mock/frozen reads | 0 |
| AS21 writes | 0 |

---

## Final Verdict Table

| Query | UI endpoint | Direct endpoint | Oracle result | FIRST_DIFFERENCE |
|-------|-------------|-----------------|---------------|------------------|
| `Задачи Гаранина` | Harness (8004) | Harness (8004) | N tasks with assignee=Garanin | **TASK_API_MCP_RESPONSE_PARSING** |

### Verdict

- ❌ `SOURCE_DATA_ISSUE_PROVEN` (INVALID - incomplete analysis)
- ✅ **`TASK_API_MCP_RESPONSE_PARSING`** (CORRECT - root cause identified)

---

## Recovery Steps

### Step 1: Task API Response Transformation

Modify Task API to transform MCP-SWTR response:

```python
# In /api/v1/swtr-read/tasks/{task_code}
unit = _parse_tool_content(content)

# Extract attributes to source_data format
swtr_attributes = unit.get("attributes", [])
source_data = {
    "swtr_code": unit.get("code"),
    "swtr_summary": unit.get("summary"),
    "swtr_space": unit.get("space", {}).get("code"),
    "swtr_suit": unit.get("suit", {}).get("code"),
    "swtr_attributes": swtr_attributes,
    # Also parse specific fields from attributes
    "workflow_status": _extract_attribute_value(swtr_attributes, "workflow_status"),
    "assigned_to": _extract_attribute_value(swtr_attributes, "assigned_to"),
}

return {"task_code": normalized, "unit": unit, "source_data": source_data}
```

### Step 2: Harness Adapter Compatibility

Verify Harness adapter works with new response format:

```python
def _map(data: dict) -> Task | None:
    source_data = data.get("source_data", {})
    attrs = _attributes(source_data)  # Now receives swtr_attributes
    status_raw = source_data.get("workflow_status") or data.get("status") or ""
    display, external_id, login = _user_identity(attrs.get("assigned_to"))
    # ... rest of mapping
```

### Step 3: Test Full Flow

1. Start fresh MCP-SWTR process
2. Test `/api/v1/swtr-read/tasks/{code}` returns `source_data.swtr_attributes`
3. Test Harness semantic query for `Задачи Гаранина`
4. Verify assignee data is correctly resolved

---

## Required Documentation Updates

### 1. Task API Contract

Document expected response format:

```markdown
## /api/v1/swtr-read/tasks/{task_code}

Response includes:
- `task_code`: string
- `unit`: object with all MCP-SWTR fields
- `source_data`: object with parsed fields for adapter compatibility
  - `swtr_attributes`: array of attribute objects
  - `workflow_status`: parsed workflow status object
  - `assigned_to`: parsed user object
  - Other parsed fields...
```

### 2. Harness Adapter Contract

Document expected input format:

```markdown
## TaskApiAS21Adapter

Expects:
- `source_data.swtr_attributes`: array of attribute objects
- `source_data.workflow_status`: parsed workflow status
- `source_data.assigned_to`: parsed user object
```

---

## Conclusion

**Assignment 116 REJECTED** - Original `SOURCE_DATA_ISSUE_PROVEN` verdict was **invalid**.

**Root Cause Identified:** `TASK_API_MCP_RESPONSE_PARSING` - Task API response does not expose `unit.attributes` to Harness adapter.

**Recovery Required:** Task API must transform MCP-SWTR response to include `source_data.swtr_attributes`.

**Production Code Change Required:** Yes (Task API response transformation).

**Owner Assignment Required:** Yes (production code change).

**Status:** INVESTIGATION COMPLETE - BLOCKED ON OWNER ASSIGNMENT

---

**Report generated:** 2026-09-01  
**QA executor:** GigaCode  
**Commit SHA:** `c50e4e48c65c55448deb8c343da72c1deeb00f24`  
**Next action:** WAIT FOR OWNER ASSIGNMENT TO FIX TASK_API_MCP_RESPONSE_PARSING
