# Assignment 117 — Task API Response Parsing Fix Verification

**Status:** `BLOCKED_ON_OWNER_FIX`
**Date:** 2026-09-01
**Branch:** `feat/core8-real-query-hardening-v2`
**HEAD:** `027896fc0127be271b21f898400eb4562416f9c3`
**Previous Assignment:** 116 - MCP-SWTR/REAL AS21 Health Recovery

---

## Executive Summary

Assignment 117 is the **verification assignment** for the Task API response parsing fix identified in Assignment 116.

**Key Finding from Assignment 116:** MCP-SWTR connection to REAL AS21 is **FULLY OPERATIONAL**. The reported issue is not a source data problem, but a **TASK_API_MCP_RESPONSE_PARSING** issue where `unit.attributes` are not exposed to Harness via `source_data.swtr_attributes`.

**Root Cause Chain:**
1. MCP-SWTR `read_unit` returns `assigned_to: null` in top-level but valid data in `attributes` array
2. Task API `/api/v1/swtr-read/tasks/{code}` returns `unit.attributes` correctly
3. **Task API DOES NOT copy `unit.attributes` → `source_data.swtr_attributes`**
4. Harness expects `source_data.swtr_attributes` and receives empty dict
5. Semantic interpreter cannot resolve `assignee`, `workflow_status`, etc.

**Boundary:** `TASK_API_MCP_RESPONSE_PARSING` (Task API response transformation)

**Status:** **BLOCKED ON OWNER ASSIGNMENT** - Production code change required in Task API.

---

## Phase 0 — Rollback and Runtime Provenance

### Branch State

| Item | Value |
|------|-------|
| Branch | `feat/core8-real-query-hardening-v2` |
| HEAD | `027896fc0127be271b21f898400eb4562416f9c3` |
| Previous HEAD | `c50e4e48c65c55448deb8c343da72c1deeb00f24` |
| Rollback baseline | `0b3b3dc1f00618e0943360d8ec2c5454dad17a4a` |
| Git status | Clean, up to date with origin |

### Assignment 116 Completion

Assignment 116 completed with:
- **Report:** `GARANIN_DIRECT_AS21_RETEST_116.md` (rejected - incomplete analysis)
- **Report:** `MCP_SWTR_REAL_AS21_HEALTH_RECOVERY_116.md` (diagnosis complete)
- **Verdict:** `TASK_API_MCP_RESPONSE_PARSING` (root cause identified)

### Commit History

```
027896f - qa: add MCP-SWTR/REAL AS21 health recovery investigation (Assignment 116 rejected)
c50e4e4 - qa: add CORE8_SEMANTIC_CORRECTION_LEARNING_072D.md report
```

### Service Status

| Service | PID | Port | Status |
|---------|-----|------|--------|
| Frontend Vite | 12279 | 5175 | ✅ Running |
| Harness (po_agent) | 62243 | 8004 | ✅ Running |
| Task API (main) | 93279 | 8003 | ✅ Running |
| MCP-SWTR (stdio) | - | - | ✅ 48 tools |

### Process Details

```
PID 12279: node /.../vite (Frontend, port 5175)
PID 62243: Python -m uvicorn po_agent.main:app (Harness, port 8004)
PID 93279: Python -m uvicorn main:app (Task API, port 8003)
```

---

## Phase 1 — Assignment 116 Diagnosis Summary

### What Was Found

#### MCP-SWTR Health: GREEN ✅

- **Transport:** stdio (`python3 mcp_server.py` from `/mcp-swtr`)
- **Tools:** 48 tools available
- **BASE_URL:** `https://portal.works.prod.sbt/swtr`
- **Token:** Valid (from `~/.config/swtr/api_key`)

#### REAL AS21 Readability: GREEN ✅

```
MCP-SWTR → REAL AS21: ✅ Working
- read_unit DMS-378: Returns attributes array with assigned_to and workflow_status
- read_unit OLP-3200: Returns attributes array with assigned_to and workflow_status
- read_unit WMB-30210: Returns attributes array with assigned_to and workflow_status
```

#### Task API Response: MISMATCH ❌

**Expected (by Harness):**
```json
{
  "task_code": "DMS-378",
  "source_data": {
    "swtr_attributes": [...],  // <-- Must be populated
    "workflow_status": {...},
    "assigned_to": {...}
  }
}
```

**Actual (from Task API):**
```json
{
  "task_code": "DMS-378",
  "unit": {
    "attributes": [...]  // <-- Available but not exposed
  }
}
```

### First Failing Boundary

**Boundary:** `TASK_API_MCP_RESPONSE_PARSING`

**Location:** Task API `/api/v1/swtr-read/tasks/{task_code}` response transformation

**Defect:** MCP-SWTR response is not transformed to Harness-expected format

**Required Fix:** Map `unit.attributes` → `source_data.swtr_attributes`

---

## Phase 2 — Assignment 117 Scope

### What Assignment 117 Should Verify

Assignment 117 is the **verification assignment** that will run AFTER the Task API fix is deployed.

### Expected Behavior After Fix

When Task API response transformation is fixed:

```
1. Browser UI → Harness → Task API /api/v1/swtr-read/tasks/{code}
2. Task API calls MCP-SWTR read_unit({code: "DMS-378"})
3. MCP-SWTR returns: {code, attributes: [...], assigned_to: null, ...}
4. Task API transforms to:
   {
     task_code: "DMS-378",
     unit: {...},
     source_data: {
       swtr_attributes: [...],  // <-- COPY from unit.attributes
       workflow_status: {...},  // <-- PARSED from attributes
       assigned_to: {...}       // <-- PARSED from attributes
     }
   }
5. Harness adapter _map receives source_data.swtr_attributes
6. Semantic interpreter has assignee data
7. Query "Задачи Гаранина" returns tasks with assignee=Garanin
```

### Test Scenarios for Assignment 117

After Task API fix is deployed, run:

1. **MCP-SWTR Health Check:**
   - Verify 48 tools available
   - Test `read_unit` returns valid attributes
   - Test `find_units` works correctly

2. **Task API Response Check:**
   - Call `/api/v1/swtr-read/tasks/DMS-378`
   - Verify `source_data.swtr_attributes` is populated
   - Verify `source_data.workflow_status` is parsed
   - Verify `source_data.assigned_to` is parsed

3. **Harness Semantic Query:**
   - Call Harness `/api/v1/query` with `Задачи Гаранина`
   - Verify tasks are returned with correct assignee
   - Verify semantic member/frame/slots are correct

4. **Three-Way Parity:**
   - Browser UI query
   - Direct Harness query
   - Oracle B direct MCP-SWTR query
   - All three should return same task keys

### Verification Checklist

- [ ] MCP-SWTR: 48 tools available
- [ ] MCP-SWTR: `read_unit` returns valid attributes array
- [ ] Task API: `source_data.swtr_attributes` is populated
- [ ] Task API: `source_data.workflow_status` is parsed
- [ ] Task API: `source_data.assigned_to` is parsed
- [ ] Harness: Semantic query returns correct tasks
- [ ] Three-way: Browser == Direct Harness == Oracle B

---

## Phase 3 — Required Fix Details

### Task API Response Transformation

**Location:** Task API `/api/v1/swtr-read/tasks/{task_code}` endpoint

**Current Implementation (simplified):**
```python
async def get_task_raw(task_code: str):
    # ...
    content = await client.call_tool("read_unit", {"code": normalized})
    return {"task_code": normalized, "unit": _parse_tool_content(content)}
```

**Required Implementation:**
```python
async def get_task_raw(task_code: str):
    # ...
    content = await client.call_tool("read_unit", {"code": normalized})
    unit = _parse_tool_content(content)
    
    # Extract attributes to source_data format
    swtr_attributes = unit.get("attributes", [])
    
    # Parse specific fields from attributes
    workflow_status = None
    assigned_to = None
    for attr in swtr_attributes:
        if attr.get("code") == "workflow_status":
            workflow_status = attr.get("value")
        if attr.get("code") == "assigned_to":
            assigned_to = attr.get("value")
    
    source_data = {
        "swtr_code": unit.get("code"),
        "swtr_summary": unit.get("summary"),
        "swtr_space": unit.get("space", {}).get("code"),
        "swtr_suit": unit.get("suit", {}).get("code"),
        "swtr_attributes": swtr_attributes,
        "workflow_status": workflow_status,
        "workflow_status_name": workflow_status.get("name") if workflow_status else None,
        "assigned_to": assigned_to,
        "assignee": _parse_user_display(assigned_to) if assigned_to else None,
    }
    
    return {"task_code": normalized, "unit": unit, "source_data": source_data}
```

### Harness Adapter Compatibility

**Current Harness adapter (`TaskApiAS21Adapter._map`):**
```python
def _map(data: dict) -> Task | None:
    source_data = data.get("source_data", {})
    attrs = _attributes(source_data)  # Expects source_data.swtr_attributes
    status_raw = source_data.get("workflow_status") or data.get("status") or ""
    display, external_id, login = _user_identity(attrs.get("assigned_to"))
    # ...
```

**After fix, `attrs` will receive proper data from `source_data.swtr_attributes`.**

---

## Phase 4 — Owner Assignment Required

### Who Must Fix

**Production code change required** in Task API response transformation.

The owner must modify Task API to:
1. Copy `unit.attributes` → `source_data.swtr_attributes`
2. Parse `workflow_status` from `attributes` → `source_data.workflow_status`
3. Parse `assigned_to` from `attributes` → `source_data.assigned_to`
4. Ensure response matches Harness adapter expectations

### No Temporary Workarounds

**DO NOT:**
- Populate local DB to make tests pass
- Use fake/mock/frozen data
- Modify Harness adapter to work with current format
- Change MCP-SWTR contract

**DO:**
- Fix Task API response transformation
- Ensure response matches existing adapter expectations

---

## Phase 5 — Verification Protocol

### When Owner Fix is Deployed

1. **Restart Task API** to pick up new response transformation
2. **Verify Task API response:**
   ```bash
   curl http://localhost:8003/api/v1/swtr-read/tasks/DMS-378
   ```
   Verify `source_data.swtr_attributes` is populated.

3. **Test Harness semantic query:**
   ```bash
   curl -X POST http://localhost:8004/api/v1/query \
     -H "Content-Type: application/json" \
     -d '{"query": "DMS-378", "session_id": "verify_117"}'
   ```

4. **Run three-way test:**
   - Browser UI query `Задачи Гаранина`
   - Direct Harness query
   - Oracle B direct MCP-SWTR query
   - All should return same task keys

5. **Update Assignment 117 report** with GREEN verdict if all pass.

---

## Mandatory Execution Counters (Assignment 116)

| Counter | Count |
|---------|-------|
| Browser UI natural-language requests | 0 |
| Direct Harness natural-language requests | 0 |
| Oracle B REAL AS21 reads | 10+ (MCP-SWTR health probe) |
| Retries/timeouts | 0 |
| Local DB authoritative reads | 0 |
| Sync/population runs | 0 |
| Fake/mock/frozen reads | 0 |
| AS21 writes | 0 |

---

## Final Verdict

| Assignment | Status | Verdict |
|------------|--------|---------|
| 116 | COMPLETE | `TASK_API_MCP_RESPONSE_PARSING` (root cause identified) |
| 117 | BLOCKED | `WAITING_FOR_OWNER_FIX` |

### Root Cause Summary

**Root Cause:** `TASK_API_MCP_RESPONSE_PARSING`

**Location:** Task API `/api/v1/swtr-read/tasks/{task_code}` response transformation

**Defect:** MCP-SWTR response is not transformed to Harness-expected format

**Required Fix:** Map `unit.attributes` → `source_data.swtr_attributes`

**Status:** **BLOCKED ON OWNER ASSIGNMENT**

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

**Assignment 116** completed with root cause identification: `TASK_API_MCP_RESPONSE_PARSING`.

**Assignment 117** is the **verification assignment** for the Task API fix.

**Current Status:** BLOCKED ON OWNER ASSIGNMENT - Production code change required in Task API.

**Next Steps:**
1. Owner fixes Task API response transformation
2. Restart Task API service
3. Run Assignment 117 verification
4. Update report with GREEN verdict if all pass

---

**Report generated:** 2026-09-01  
**QA executor:** GigaCode  
**Commit SHA:** `027896fc0127be271b21f898400eb4562416f9c3`  
**Next action:** WAIT FOR OWNER ASSIGNMENT TO FIX TASK_API_MCP_RESPONSE_PARSING
