# Assignment 096F — MCP-SWTR → TASK API SYNC GAP DIAGNOSTIC

**Date:** 2026-08-28  
**QA Role:** QA / Diagnostic only  
**Branch:** `feat/core8-real-query-hardening-v2`

---

## TESTED HEAD

| Item | Value |
|------|-------|
| HEAD | `52fb044` (commit of 096E report) |
| Branch | `feat/core8-real-query-hardening-v2` |

---

## SERVICE/CONFIG STATE

| Service | Status | Configuration |
|---------|--------|---------------|
| MCP-SWTR | Connected (stdio) | `mcp-swtr-wrapper.sh` sources `.env` |
| Task API | Healthy | `http://127.0.0.1:8003` |
| PO Agent | Degraded | `task-api` adapter, no MCP-SWTR env vars |
| Environment | Missing | `SWTR_MCP_STDIO_*` env vars not set by PO Agent |

---

## COMPLETE BOUNDARY TRACE

### A. REAL SWTR Response

**Endpoint:** `https://portal.works.prod.sbt/swtr/unit/DMS-273` (via MCP-SWTR stdio)

**Evidence:**
```
Unit code: DMS-273
workflow_status: {
  "name": "Зарегистрирован",
  "code": "ZRGSTR_JEPgizwlJWGww",
  "statusType": "pause"
}
```

**Result:** ✅ DMS-273 available with workflow_status

---

### B. /api/v1/swtr-read/tasks/DMS-273

**Endpoint:** `http://127.0.0.1:8003/api/v1/swtr-read/tasks/DMS-273`

**Evidence:**
```json
{
  "task_code": "DMS-273",
  "unit": {
    "code": "DMS-273",
    "summary": "[doc] Поправить документацию по ручной установке Safeguard",
    "attributes": [
      {
        "code": "workflow_status",
        "value": {
          "name": "Зарегистрирован",
          "code": "ZRGSTR_JEPgizwlJWGww",
          "statusType": "pause"
        }
      }
    ]
  }
}
```

**Result:** ✅ DMS-273 available, workflow_status present

---

### C. SYNCHRONIZATION/IMPORT INPUT

**Attempted endpoint:** `http://127.0.0.1:8003/api/v1/swtr/tasks/DMS-273`

**Evidence:**
```json
{
  "task": null,
  "error": "Task not found or sync failed"
}
```

**SWTRSyncService.sync_single_task() behavior:**
- Calls `read_unit` via stdio subprocess
- Returns `None` because MCP-SWTR stdio transport fails

**Root cause in `_run_mcp_command()`:**
- Uses subprocess to run MCP-SWTR
- Sets `TOKEN`, `BASE_URL`, `PORT` in env
- Calls `read_unit` with `{"code": "DMS-273"}`
- MCP-SWTR returns: `{"error": {"code": -32602, "message": "Invalid request parameters"}}`

**Result:** ❌ MCP-SWTR stdio subprocess transport fails

---

### D. SYNCHRONIZATION/IMPORT OUTPUT

**Attempted endpoint:** Same as C

**Evidence:** Same as C - returns error

**Result:** ❌ No data synchronized

---

### E. TASK API INTERNAL REPRESENTATION/STORAGE

**Storage:** `~/.task-tracker/tasks.json` (in-memory + file)

**Evidence:**
```json
{
  "id": "...",
  "source": null,
  "source_data": {}
}
```

**Result:** ❌ Empty `source_data` - no SWTR attributes stored

**Reason:** No synchronization ever succeeded, so no `swtr_attributes` populated.

---

### F. /api/v1/tasks RESULT

**Endpoint:** `http://127.0.0.1:8003/api/v1/tasks`

**Evidence:**
```
[]  // Empty list - no tasks available
```

**Result:** ❌ Empty list - MCP-SWTR not providing data

**Why:** SWTRMCPClient for Task API uses SSE transport (default), but MCP-SWTR not available via SSE.

---

### G. PO AGENT LOOKUP

**Adapter:** `task-api`

**Behavior:** Calls `/api/v1/tasks` → empty list

**Result:** ❌ Cannot find tasks

---

## FIRST FAILING BOUNDARY

**Boundary C → D (SYNCHRONIZATION/IMPORT INPUT)**

**Evidence:**
1. MCP-SWTR is reachable via stdio subprocess (used by PO Agent's `mcp-swtr-wrapper.sh`)
2. But `SWTRSyncService._run_mcp_command()` fails when calling `read_unit`
3. MCP-SWTR returns: `{"error": {"code": -32602, "message": "Invalid request parameters"}}`

**Root cause:** MCP-SWTR stdio protocol expects specific JSON-RPC format. Current implementation sends:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "read_unit",
    "arguments": {"code": "DMS-273"}
  },
  "id": 1
}
```

MCP-SWTR returns "Invalid request parameters" - likely expects different format.

**However, this is NOT the PRIMARY problem.**

---

## PRIMARY ROOT CAUSE: ENVIRONMENT VARIABLE PROBLEM

**Boundary F → G (Task API → PO Agent adapter)**

**Evidence:**
```python
# PO Agent does NOT set MCP-SWTR transport env vars:
SWTR_MCP_TRANSPORT = None  # ❌ Not set by PO Agent
SWTR_MCP_STDIO_COMMAND = None
SWTR_MCP_STDIO_ARGS = None
SWTR_MCP_STDIO_CWD = None
SWTR_TOKEN = None
BASE_URL = None
```

**Task API SWTRMCPClient defaults:**
```python
transport = "sse"  # Default, not stdio
sse_url = "http://127.0.0.1:3000/sse"  # Default
```

**But MCP-SWTR is NOT available via SSE:**
```
SWTRMCPUnavailable: MCP-SWTR unavailable via http://127.0.0.1:3000/sse
```

**MCP-SWTR is ONLY available via stdio subprocess.**

---

## SYNCHRONIZATION MECHANISM

### Current State

| Component | Mechanism | Status |
|-----------|-----------|--------|
| MCP-SWTR transport | stdio subprocess | ✅ Works (mcp-swtr-wrapper.sh) |
| SWTRSyncService | stdio subprocess | ❌ Fails (wrong protocol) |
| SWTRMCPClient | SSE (default) | ❌ Fails (not available) |
| PO Agent → Task API | No MCP-SWTR env vars | ❌ Not set |

### Expected State

```
PO Agent startup
  → Sets SWTR_MCP_TRANSPORT=stdio
  → Sets SWTR_MCP_STDIO_COMMAND=/path/to/mcp-swtr-wrapper.sh
  → Sets SWTR_MCP_STDIO_ARGS=mcp_server.py
  → Sets SWTR_MCP_STDIO_CWD=/path/to/mcp-swtr
  → Sets SWTR_TOKEN and BASE_URL from .env

Task API initialization
  → Reads SWTR_MCP_STDIO_* env vars
  → Uses stdio transport for MCP-SWTR
  → Can call read_unit and other MCP tools

Data flow
  MCP-SWTR (stdio) 
    → SWTRMCPClient.call_tool("read_unit", ...)
      → Task API swtr-sync endpoints
        → TaskRepository.save()
          → /api/v1/tasks returns tasks with source_data.swtr_attributes
```

---

## RELEVANT MODULES/FUNCTIONS

### Task API

| Module | Function | Issue |
|--------|----------|-------|
| `app/services/swtr_mcp_client.py` | `SWTRMCPClient.__init__()` | Uses SSE by default, stdio not configured |
| `app/services/swtr_sync_service.py` | `SWTRSyncService._run_mcp_command()` | Wrong MCP protocol format |
| `app/services/swtr_sync_service.py` | `SWTRSyncService.sync_single_task()` | Returns None on MCP error |
| `app/routers/swtr_read.py` | `get_task_raw()` | Direct MCP read works (separate client) |
| `app/routers/swtr_read.py` | `_source_workflow_status()` | Looks in `source_data.swtr_attributes` |

### PO Agent

| Module | Function | Issue |
|--------|----------|-------|
| `po_agent/main.py` | (none) | Does NOT set MCP-SWTR env vars |
| `po_agent/config/settings.py` | `Settings.swtr_token` | Reads token but doesn't propagate |
| `po_agent/adapters/task_api.py` | `TaskApiAS21Adapter._map()` | Expects `source_data.swtr_attributes` |

---

## COMMANDS/ENDPOINTS EXECUTED

### Working (via MCP-SWTR stdio subprocess):

```bash
# mcp-swtr-wrapper.sh (from PO Agent)
# Sources .env, runs MCP-SWTR with stdio
# Successfully serves MCP protocol
```

### Not Working (Task API):

```bash
# Task API attempts SSE:
curl http://127.0.0.1:3000/sse
# Connection refused - MCP-SWTR not listening on SSE

# Task API attempts stdio with wrong format:
python3 -c "
import subprocess, json, os
env = os.environ.copy()
env['TOKEN'] = open(os.path.expanduser('~/.config/swtr/api_key')).read().strip()
env['BASE_URL'] = 'https://portal.works.prod.sbt/swtr'
env['PORT'] = '0'
cmd = ['.venv/bin/python', 'mcp_server.py']
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env)
proc.stdin.write(json.dumps({'jsonrpc':'2.0','method':'tools/call','params':{'name':'read_unit','arguments':{'code':'DMS-273'}},'id':1}) + '\n')
proc.stdin.flush()
print(proc.stdout.readline())
# Returns: {'error': {'code': -32602, 'message': 'Invalid request parameters'}}
"
```

### Partially Working (Direct MCP-SWTR read):

```bash
# PO Agent uses this directly for swtr-read endpoints:
curl http://127.0.0.1:8003/api/v1/swtr-read/tasks/DMS-273
# Returns: DMS-273 with workflow_status = "Зарегистрирован"
```

---

## ROOT CAUSE CLASSIFICATION

**PRIMARY: ARCHITECTURAL_GAP**

**Secondary: SYNC_CONFIGURATION_ERROR**

### Primary Classification: ARCHITECTURAL_GAP

**Evidence:**
1. PO Agent does not configure MCP-SWTR transport for Task API
2. Task API SWTRMCPClient defaults to SSE, but MCP-SWTR only available via stdio
3. SWTRSyncService uses wrong MCP protocol format for stdio subprocess
4. No mechanism to propagate `SWTR_TOKEN` and MCP-SWTR transport config from PO Agent to Task API

**Why not SYNC_CONFIGURATION_ERROR:**
- MCP-SWTR stdio transport is correctly configured for PO Agent
- But Task API has no way to access this configuration
- Configuration gap between components

**Why not SYNC_RUNTIME_FAILURE:**
- MCP-SWTR stdio subprocess works (used by PO Agent)
- Issue is not runtime failure, but missing integration configuration

### Secondary Classification: SYNC_CONFIGURATION_ERROR

**Evidence:**
- Task API SWTRMCPClient uses `transport=sse` by default
- `SWTR_MCP_TRANSPORT` env var is not set by PO Agent
- `SWTR_MCP_STDIO_*` env vars are not set by PO Agent

---

## MINIMAL DEVELOPER REMEDIATION RECOMMENDATION

### Step 1: PO Agent must configure MCP-SWTR transport for Task API

**File:** `po-agent-platform-v2/src/po_agent/main.py`

**Action:** Add MCP-SWTR transport configuration to PO Agent startup:

```python
def configure_mcp_swtr_transport() -> None:
    """Configure MCP-SWTR stdio transport for Task API."""
    settings = get_settings()
    
    # Set environment variables that Task API expects
    os.environ["SWTR_MCP_TRANSPORT"] = "stdio"
    os.environ["SWTR_MCP_STDIO_COMMAND"] = "/path/to/mcp-swtr-wrapper.sh"
    os.environ["SWTR_MCP_STDIO_ARGS"] = "mcp_server.py"
    os.environ["SWTR_MCP_STDIO_CWD"] = "/path/to/mcp-swtr"
    
    # Propagate SWTR token
    if settings.swtr_token:
        os.environ["SWTR_TOKEN"] = settings.swtr_token
    if settings.swtr_base_url:
        os.environ["BASE_URL"] = settings.swtr_base_url
```

### Step 2: Fix SWTRSyncService MCP protocol for stdio

**File:** `task-api/app/services/swtr_sync_service.py`

**Action:** Update `_run_mcp_command()` to use correct stdio MCP protocol:

```python
def _run_mcp_command(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Run MCP command via stdio subprocess."""
    # ... existing token setup ...
    
    # Build correct MCP request for stdio
    request = {
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': 1
    }
    
    # For tools/call, params should be {'name': 'tool_name', 'arguments': {...}}
    if method == 'tools/call':
        request['params'] = {
            'name': params.get('name'),
            'arguments': params.get('arguments', {})
        }
    
    # ... rest of subprocess logic ...
```

### Step 3: Configure PO Agent startup

**File:** `po-agent-platform-v2/src/po_agent/main.py`

**Action:** Call `configure_mcp_swtr_transport()` at startup:

```python
@app.on_event("startup")
async def startup_event():
    configure_mcp_swtr_transport()
    # ... other startup logic ...
```

---

## VERDICT

**ARCHITECTURAL_GAP**

**Reason:** PO Agent and Task API are not properly integrated for MCP-SWTR transport. The configuration is incomplete:

1. PO Agent reads `swtr_token` but doesn't propagate it to Task API
2. PO Agent doesn't configure MCP-SWTR stdio transport for Task API
3. Task API defaults to SSE, but MCP-SWTR only available via stdio
4. SWTRSyncService uses wrong MCP protocol format for stdio subprocess

---

## SYNC WORKING?

**NO**

**Evidence:**
- `/api/v1/swtr-read/tasks/DMS-273` works (direct MCP read)
- `/api/v1/swtr/tasks/DMS-273` fails (synchronization)
- `/api/v1/tasks` returns empty (no data synchronized)
- PO Agent adapter cannot find tasks (no source_data.swtr_attributes)

---

## STOP

DO NOT implement remediation.

DO NOT modify code.

DO NOT start Assignment 097.

---

## GIT STATUS

```bash
On branch feat/core8-real-query-hardening-v2
Your branch is ahead of 'origin/feat/core8-real-query-hardening-v2' by 1 commit.

Untracked files:
  po-agent-platform-v2/.po_agent/
  qa_reports/MCP_SWTR_TASK_API_SYNC_DIAGNOSTIC_096F.md
```
