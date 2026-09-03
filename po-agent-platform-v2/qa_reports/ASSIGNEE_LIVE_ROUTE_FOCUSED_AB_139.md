# Assignment 139 — ASSIGNEE_LIVE_ROUTE_FOCUSED_AB

**Date:** 2026-09-03  
**Branch:** `feat/core8-real-query-hardening-v2`  
**HEAD:** `875248e137b71868c8119cdebe655126745afbc4`  
**Owner commit verified:** `5ce78840ecc9553c0f1f062922a8a0d26fe9ae58`  
**QA role:** Tester/executor only (no production code modifications)

---

## Mission

Certify owner fix `5ce7884` to `task-api/app/routers/swtr_assignee.py::_resolve_external_id()` which wraps `search_users` arguments in `{"request": {...}}`.

**Status:** ROOT CAUSE IDENTIFIED (FIX REQUIRED)

---

## Phase 0 — Source and Schema Health

| Item | Status |
|------|--------|
| Branch `feat/core8-real-query-hardening-v2` | ✅ Verified (HEAD `875248e`) |
| Owner commit `5ce7884` | ✅ Verified |
| Task API PID | 60006 |
| Harness PID | 60142 |
| MCP-SWTR tools | 48 tools |
| DMS-380 read | ✅ Works |
| STS-184686 read | ✅ Works |

**MCP-SWTR Tool Schemas:**

| Tool | Required Arguments |
|------|-------------------|
| `search_users` | `{"request": {"text_search": str, "page": int, "size": int}}` |
| `find_units_by_filter` | `{"request": TqlSearchRequest(...)} ` |

---

## Phase 1 — Direct Task API Assignee Route

**Fix Applied (line 102-105 in `swtr_assignee.py`):**
```python
content = await client.call_tool(
    "search_users",
    {"request": {"text_search": needle, "page": 0, "size": 100}},
)
```

**Problem Identified:** `find_units_by_filter` also requires `request` wrapper.

**Current (Broken) Code:**
```python
arguments = {
    "calculatedAttributes": [],
    "attributes": ["code", "summary", "assigned_to", "space", "workflow_status"],
    "query": f'assigned_to = "{external_id}"',
    "timeZone": "Europe/Moscow",
    "page": 0,
    "size": 100,
}
content = await client.call_tool("find_units_by_filter", arguments)
```

**Error:**
```
Invalid arguments for tool 'find_units_by_filter':
  - Missing required argument: 'request'
  - Unexpected keyword argument: 'calculatedAttributes', 'attributes', 'query', 'timeZone', 'page', 'size'
```

**Expected Fix:**
```python
arguments = {
    "request": {
        "calculatedAttributes": [],
        "attributes": ["code", "summary", "assigned_to", "space", "workflow_status"],
        "query": f'assigned_to = "{external_id}"',
        "timeZone": "Europe/Moscow",
        "page": 0,
        "size": 100,
    }
}
```

---

## Phase 2 — Independent Oracle B

**Direct MCP `find_units_by_filter` test:**

```python
arguments = {
    "request": {
        "calculatedAttributes": [],
        "attributes": ["code", "summary", "assigned_to", "space", "workflow_status"],
        "query": f'assigned_to = "Garanin.R.V"',
        "timeZone": "Europe/Moscow",
        "page": 0,
        "size": 100,
    }
}
```

**MCP-SWTR returns:** Valid `content` array with task rows.

---

## Phase 3 — Agent A Natural-Language Path

**Not Tested:** Requires fix to `find_units_by_filter` first.

**Expected Behavior (after fix):**
- `Задачи Гаранина` → HTTP 200, tasks returned
- `Задачи Гаранина в DMS` → HTTP 200, tasks filtered by space
- `Задачи Калачанова` → HTTP 200, tasks returned

---

## Phase 4 — Protected Exact-Task Cluster

| Test | Expected | Actual | Result |
|------|----------|--------|--------|
| DMS-380 → Task API | HTTP 200 | HTTP 200 | ✅ PASS |
| DMS-380 → Agent A | COMPLETED, key=DMS-380 | COMPLETED, key=DMS-380 | ✅ PASS |
| DMS-999999999 → Task API | HTTP 404 | HTTP 404 | ✅ PASS |
| DMS-999999999 → Agent A | "не найдена" | "не найдена" | ✅ PASS |

**Exact-task cluster remains GREEN.**

---

## Phase 5 — Regression Semantics

**Requires fix.** Not testable until `find_units_by_filter` is corrected.

---

## Root Cause Analysis

**MCP-SWTR Tool Schemas:**

Both `search_users` and `find_units_by_filter` are FastMCP tools defined with Pydantic request models that require a single top-level `request` argument.

**`search_users` (line 400 in mcp_server.py):**
```python
@mcp.tool()
async def search_users(request: BaseSearchRequest) -> str:
    payload = {
        "searchString": request.text_search,
        "paging": {
            "page": request.page,
            "size": request.size
        }
    }
```

**`find_units_by_filter` (line 198 in mcp_server.py):**
```python
@mcp.tool()
async def find_units_by_filter(request: TqlSearchRequest) -> str:
    payload = {
        "calculatedAttributes": request.calculatedAttributes or [],
        "attributes": request.attributes or [],
        "query": request.query,
        "timeZone": request.timeZone,
        "page": {
            "page": request.page,
            "size": request.size
        }
    }
```

---

## Fix Scope

**Files to Modify:**
1. `task-api/app/routers/swtr_assignee.py` line 102-105: ✅ Already fixed
2. `task-api/app/routers/swtr_assignee.py` line 150-165: **MISSING FIX**

**Line 150-165 (Current Broken):**
```python
arguments = {
    "calculatedAttributes": [],
    "attributes": [
        "code",
        "summary",
        "assigned_to",
        "space",
        "workflow_status",
        "scrum_board_plugin_sprint",
        "fix_version_s",
    ],
    "query": f'assigned_to = "{external_id}"',
    "timeZone": "Europe/Moscow",
    "page": page,
    "size": limit,
}
content = await client.call_tool("find_units_by_filter", arguments)
```

**Line 150-165 (Expected Fixed):**
```python
arguments = {
    "request": {
        "calculatedAttributes": [],
        "attributes": [
            "code",
            "summary",
            "assigned_to",
            "space",
            "workflow_status",
            "scrum_board_plugin_sprint",
            "fix_version_s",
        ],
        "query": f'assigned_to = "{external_id}"',
        "timeZone": "Europe/Moscow",
        "page": page,
        "size": limit,
    }
}
content = await client.call_tool("find_units_by_filter", arguments)
```

---

## Verdicts

| Verdict | Status | Details |
|---------|--------|---------|
| `ASSIGNEE_LIVE_ROUTE_GREEN` | ❌ Partial fix (search_users fixed, find_units_by_filter missing) |
| `ASSIGNEE_IDENTITY_STILL_RED` | ❌ Identity resolution works after fix |
| `ASSIGNEE_TASK_PARITY_RED` | ⚠️ Can't test due to missing find_units_by_filter fix |
| `PROTECTED_EXACT_TASK_REGRESSION_RED` | ❌ Not affected |
| `BLOCKED_BY_ENVIRONMENT` | ❌ MCP-SWTR schema known, fix required |

---

## Overall Verdict

**`ASSIGNEE_LIVE_ROUTE_FIX_REQUIRED`**

**First Failing Boundary:**
- **File:** `task-api/app/routers/swtr_assignee.py`
- **Function:** `get_assignee_tasks()` → `find_units_by_filter` call
- **Line:** ~150-165
- **Issue:** Missing `request` wrapper for `find_units_by_filter` tool arguments

**Minimal Owner Fix Scope:**
Wrap `find_units_by_filter` arguments in `{"request": {...}}` (single line change).

---

## Head SHA

`875248e137b71868c8119cdebe655126745afbc4`

---

## Report Commit SHA

Pending commit after this report.

---

## GigaCode Actions

- [x] Verified HEAD `875248e` and owner commit `5ce7884` in branch
- [x] Phase 0: Source health proven, MCP schemas identified
- [x] Phase 1: Fix partially applied (search_users fixed, find_units_by_filter missing)
- [x] Phase 2: Direct MCP calls require `request` wrapper
- [x] Phase 3: Agent A path blocked by find_units_by_filter fix
- [x] Phase 4: Protected exact-task cluster GREEN
- [x] Phase 5: Regression semantics blocked by missing fix
- [x] Root cause identified with exact line number and fix
- [x] Created report at `po-agent-platform-v2/qa_reports/ASSIGNEE_LIVE_ROUTE_FOCUSED_AB_139.md`
- [ ] Commit/push QA artifacts only (report only)
