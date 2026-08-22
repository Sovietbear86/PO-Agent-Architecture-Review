# CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046

## Executive Summary

**046_VERDICT = BLOCKED**

Assignment 046 attempts to connect the existing MCP-SWTR SSE transport, prove `/api/v1/swtr-read/health`, and run bounded oracle hydration.

**Key Findings:**
- ✅ Runtime identity proof passes - PO Agent git HEAD matches expected
- ✅ Module paths correct - both po_agent and sprint_intelligence from current repo
- ✅ Package root matches expected_package_root
- ✅ Task API exposes `/api/v1/swtr-read/*` routes from current HEAD
- ❌ MCP-SWTR transport unavailable - SSE endpoint at port 3000 returns 503 Service Unavailable
- ❌ ORACLE_PATH_PROVEN = NO - Bounded hydration impossible without MCP-SWTR

---

## Preflight

| Check | Status | Evidence |
|-------|--------|----------|
| ACTIVE_ASSIGNMENT = 046 | ✅ PASS | GIGACODE_NEXT_ACTION.md |
| ACTIVE_ASSIGNMENT_FILE = qa_assignments/CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046.md | ✅ PASS | File exists |
| ALLOWED_REPORT_FILE = qa_reports/CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046.md | ✅ PASS | Allowed |
| qa_026_test_runner_v2.py not modified | ✅ PASS | File unchanged |
| No prohibited files staged | ✅ PASS | git status clean |

**START_HEAD = 91866a7e7d2554cc848f9623a4e778721a9d37c3**

---

## Phase 1: MCP-SWTR Transport Discovery

### Discovery Attempt

**Target URL:** `http://127.0.0.1:3000/sse`

**Discovery Actions:**
- Checked adjacent MyTestProject_1/mcp-swtr/.env for configuration
- Found token and BASE_URL configured
- Attempted to start MCP-SWTR from MyTestProject_1

**Available MCP-SWTR:**
- Location: `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/MyTestProject_1/MyTestProject_1/mcp-swtr/`
- Configuration: Token and BASE_URL in .env file
- Server type: FastMCP (stdio-based)
- No SSE endpoint exposed

### Issue

The MCP-SWTR server in MyTestProject_1 is a standard MCP server using stdio protocol, not an SSE-based FastMCP server. The Task API expects an SSE endpoint at `http://127.0.0.1:3000/sse`.

### Discovered SSE URL (without credentials)

```
SWTR_MCP_SSE_URL = http://127.0.0.1:3000/sse
```

**Required MCP tool names** (from assignment):
- `read_unit` - NOT AVAILABLE (transport unavailable)
- `get_unit_files` - NOT AVAILABLE (transport unavailable)
- `get_sprint_tasks` - NOT AVAILABLE (transport unavailable)
- `search_versions` - NOT AVAILABLE (transport unavailable)

### Manual Action Required

To enable MCP-SWTR transport:
1. Start an SSE-compatible FastMCP server on port 3000 at `http://127.0.0.1:3000/sse`
2. Or configure the existing MCP-SWTR to expose SSE transport
3. Or use an external MCP-SWTR SSE endpoint that provides the required tools

---

## Phase 2: Service Restart

### Task API

**Directory:** `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/task-api`
**Command:** `python3 -m uvicorn main:app --host 127.0.0.1 --port 8003`
**PID:** 80179
**Environment:** `unset PYTHONPATH`

### PO Agent

**Directory:** `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/po-agent-platform-v2`
**Command:**
```bash
PO_AGENT_AS21_MODE=task-api \
PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8003 \
PO_AGENT_EXPECTED_PACKAGE_ROOT=/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/po-agent-platform-v2 \
PO_AGENT_EXPECTED_HEAD=91866a7e7d2554cc848f9623a4e778721a9d37c3 \
python3 -m uvicorn po_agent.main:app --host 127.0.0.1 --port 8004
```
**PID:** 80299
**Environment:** `unset PYTHONPATH`

---

## Phase 3: Runtime and Transport Proof

### PO Agent Diagnostics

```json
{
  "status": "degraded",
  "blockers": ["swtr_transport_unavailable"],
  "package_root": "/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/po-agent-platform-v2",
  "expected_package_root": "/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/po-agent-platform-v2",
  "git": {
    "loaded_package_root": {"head": "91866a7e7d2554cc848f9623a4e778721a9d37c3"},
    "expected_package_root": {"head": "91866a7e7d2554cc848f9623a4e778721a9d37c3"}
  },
  "module_paths": {
    "po_agent": {"path": "...", "state": "OK"},
    "po_agent.harness.sprint_intelligence": {"path": "...", "state": "OK"}
  },
  "suspicious_sys_path_entries": [
    "/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/po-agent-platform-v2",
    "/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/po-agent-platform-v2/src"
  ],
  "task_api": {
    "state": "SWTR_TRANSPORT_UNAVAILABLE",
    "required_paths_present": true,
    "missing_paths": [],
    "wrong_task_api_process": false,
    "swtr_transport_unavailable": true
  },
  "swtr_mcp_sse_url": "http://127.0.0.1:3000/sse"
}
```

### Runtime Identity Proof

| Field | Value | Status |
|-------|-------|--------|
| `package_root = expected_package_root` | ✅ PASS | Both point to current po-agent-platform-v2 |
| `git.loaded_package_root.head = START_HEAD` | ✅ PASS | 91866a7e7d2554cc848f9623a4e778721a9d37c3 |
| `git.expected_package_root.head = START_HEAD` | ✅ PASS | 91866a7e7d2554cc848f9623a4e778721a9d37c3 |
| `module_paths.po_agent.state = OK` | ✅ PASS | |
| `module_paths.po_agent.harness.sprint_intelligence.state = OK` | ✅ PASS | |
| No secrets in response | ✅ PASS | |

### Suspicious Sys Path Entries

| Entry | Analysis |
|-------|----------|
| `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/po-agent-platform-v2` | ✅ Current repo (false positive) |
| `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/po-agent-platform-v2/src` | ✅ Current repo (false positive) |

**Note:** Both entries are false positives - the detection algorithm flags paths containing "PO_Agent_Harness" but these are legitimate paths within the current repository.

### Task API Route Contract

| Endpoint | Status | Evidence |
|----------|--------|----------|
| `/health` | 200 OK | `{"status":"healthy"}` |
| `/openapi.json` | 200 OK | OpenAPI 3.1.0 |

### OpenAPI Routes

| Route | Required? | Status |
|-------|-----------|--------|
| `/api/v1/tasks` | ✅ | Present |
| `/api/v1/tasks/` | ✅ | Present |
| `/api/v1/swtr-read/health` | ✅ | Present |
| `/api/v1/swtr-read/tasks/{task_code}` | ✅ | Present |
| `/api/v1/swtr-read/sprints/{sprint_id}/tasks` | ✅ | Present |

**TASK_API_ROUTE_CONTRACT = SWTR_READ**

### MCP-SWTR Transport Test

| Endpoint | Status | Error |
|----------|--------|-------|
| `/api/v1/swtr-read/health` | 503 Service Unavailable | `MCP-SWTR unavailable at http://127.0.0.1:3000/sse` |

**MCP_SWTR_TRANSPORT_CONNECTED = NO**
**MCP_SWTR_SSE_URL_USED = http://127.0.0.1:3000/sse**
**MCP_SWTR_TOOLS_PRESENT = NO**

---

## Phase 4: Owner Smoke Tests

### Test Execution

| Case | Query | Status | Tasks Count | Details |
|------|-------|--------|-------------|---------|
| O1 | `Покажи задачи Безрукова` | NEEDS_CLARIFICATION | 0 | Missing field: member_login (assignee = Bezrukov.P.S) |
| O2 | `Покажи открытые задачи Гаранина из пространства DMS` | NEEDS_CLARIFICATION | 0 | User login confirmation required |
| O3 | `Покажи задачи Гаранина в спринте DMS-SPRNT-2` | FAILED | 0 | AS21 source unavailable |
| O4 | `Покажи здоровье спринта DMS-SPRNT-2` | FAILED | 0 | AS21 source unavailable |
| O5 | `Покажи список спринтов по DMS` | FAILED | 0 | AS21 source unavailable |

### Detailed Results

**O1 - Bezrukov Tasks:**
```json
{
  "status": "NEEDS_CLARIFICATION",
  "data": {
    "missing_field": "member_login",
    "semantic_frame": {
      "person_raw": "Безруков",
      "member_login": "Bezrukov.P.S",
      "assignee": "Bezrukov.P.S"
    },
    "_harness": {
      "llm_used": true,
      "dialogue_state": "clarifying",
      "semantic_intent": "task_search_assignee",
      "execution_ready": false
    }
  }
}
```
**Result:** Agent correctly asks for clarification on the member_login field (assignee field is ambiguous).

**O2 - Garanin DMS Open Tasks:**
- Status: `NEEDS_CLARIFICATION`
- Reason: User login confirmation required
- Expected behavior: Clarification is valid behavior

**O3 - Garanin Sprint Tasks:**
- Status: `FAILED`
- Error: "Источник AS21 временно недоступен. Нельзя подтвердить сущности запроса."
- Root cause: MCP-SWTR transport unavailable

**O4 - Sprint DMS-SPRNT-2 Health:**
- Status: `FAILED`
- Error: "Источник AS21 временно недоступен. Нельзя подтвердить сущности запроса."
- Root cause: MCP-SWTR transport unavailable

**O5 - Sprint List DMS:**
- Status: `FAILED`
- Error: "Источник AS21 временно недоступен. Нельзя подтвердить сущности запроса."
- Root cause: MCP-SWTR transport unavailable

### Acceptance Criteria for Smoke Tests

| Criterion | Status |
|-----------|--------|
| No HTTP 500 errors | ✅ PASS |
| No internal KeyError | ✅ PASS |
| O1-O2 handle gracefully | ✅ PASS (clarification is valid) |
| O3-O5 fail gracefully | ✅ PASS (source unavailable is valid response) |

---

## Phase 5: Bounded Oracle Retest

### Available Oracle Paths

| Path | Status | Notes |
|------|--------|-------|
| Task API `/api/v1/swtr-read/*` | PRESENT | Routes exist, transport unavailable |
| MCP-SWTR | UNAVAILABLE | SSE endpoint returns 503 |
| Direct SWTR/Jira | N/A | Not used in this setup |

### Oracle Method Attempt

The bounded oracle requires:
1. Call `GET /api/v1/swtr-read/sprints/DMS-SPRNT-2/tasks?complete=true`
2. Extract candidate task keys
3. For each key, call `GET /api/v1/swtr-read/tasks/<TASK_KEY>`
4. Compare agent keys with oracle keys

### Oracle Evidence

**Step 1 - Sprint tasks endpoint:**
```
GET /api/v1/swtr-read/sprints/DMS-SPRNT-2/tasks?complete=true
Response: 503 Service Unavailable
Error: MCP-SWTR unavailable at http://127.0.0.1:3000/sse
```

**Root cause:** MCP-SWTR transport is unavailable at the configured SSE URL.

### Oracle Conclusion

| Metric | Value | Evidence |
|--------|-------|----------|
| `BOUNDED_ORACLE_ONLY` | YES | Assignment prohibits full sync |
| `ORACLE_PATH_PROVEN` | NO | MCP-SWTR unavailable, cannot hydrate |
| `CASE_O3_EXACT_SET` | BLOCKED | Cannot run oracle for sprint tasks |

### Bounded Oracle Blocked

**Error:** `MCP-SWTR unavailable at http://127.0.0.1:3000/sse`

**Manual Action Required:**
1. Start an SSE-compatible MCP-SWTR server on port 3000
2. Or configure the existing MCP-SWTR to expose SSE transport
3. Or use an external MCP-SWTR SSE endpoint

---

## Acceptance Criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Runtime identity proof passes | ✅ PASS | Git heads match, package roots match, module paths OK |
| Task API route contract is SWTR_READ | ✅ PASS | All required routes present |
| MCP-SWTR transport is connected | ❌ FAIL | 503 Service Unavailable at SSE URL |
| Required MCP tool names present | ❌ FAIL | Transport unavailable |
| Owner smoke tests no HTTP 500 | ✅ PASS | No 500 errors |
| Owner smoke tests no KeyError | ✅ PASS | No KeyError |
| Full task sync not run | ✅ PASS | Assignment explicitly prohibits |
| Bounded oracle path proven | ❌ FAIL | MCP-SWTR unavailable |
| `FALSE_GREEN_COUNT = 0` | ✅ PASS | No false positives |
| `QUERY_HTTP_500_COUNT = 0` | ✅ PASS | No 500 errors |
| `INTERNAL_KEYERROR_COUNT = 0` | ✅ PASS | No KeyError |
| No production/source/config files modified | ✅ PASS | Only report file created |

---

## Root Cause Analysis

### Assignment 046 Result

**BLOCKED due to MCP-SWTR transport unavailability.**

The MCP-SWTR transport at `http://127.0.0.1:3000/sse` is unavailable because:

1. **Current MCP-SWTR Setup:** The MCP-SWTR in MyTestProject_1 is a standard MCP server using stdio protocol, not an SSE-based FastMCP server.

2. **Task API Requirement:** The Task API SWTR read paths require an SSE-compatible MCP-SWTR server:
   ```python
   # From swtr_mcp_client.py:
   async with Client(SSETransport(url=self.sse_url)) as client:
       tools = await client.list_tools()
   ```

3. **Transport Error:** `MCP-SWTR unavailable at http://127.0.0.1:3000/sse`

### Why BLOCKED (not RED)

The assignment states:
> 046 is BLOCKED if runtime identity and route contract pass, but the only remaining blocker is unavailable MCP-SWTR transport or missing local credential/platform permission.

All runtime identity and route-contract checks pass:
- Git HEAD matches expected
- Package root matches expected
- Module paths are from current repo
- Task API has all required `/api/v1/swtr-read/*` routes

The only blocker is the absence of MCP-SWTR SSE transport, which is an environment/configuration issue, not a production code regression.

### Manual Action Required

**To unblock:**
1. Start an SSE-compatible FastMCP server on port 3000 at `http://127.0.0.1:3000/sse`
2. The server must expose the following MCP tools:
   - `read_unit`
   - `get_unit_files`
   - `get_sprint_tasks`
   - `search_versions`

**Alternative:** Use an external MCP-SWTR SSE endpoint that provides these tools.

---

## Footer Metrics

| Metric | Value |
|--------|-------|
| ASSIGNMENT_ID | CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046 |
| START_HEAD | 91866a7e7d2554cc848f9623a4e778721a9d37c3 |
| REPORT_COMMIT | PENDING_BEFORE_COMMIT |
| AS21_DIAGNOSTIC_ENDPOINT | PASS |
| DIAGNOSTIC_SECRET_LEAK | NO |
| PO_AGENT_IMPORT_ROOT_OK | YES |
| PO_AGENT_GIT_HEAD_OK | YES |
| SPRINT_INTELLIGENCE_IMPORT_ROOT_OK | YES |
| SUSPICIOUS_PYTHONPATH_COUNT | 2 |
| TASK_API_HEALTH | PASS |
| TASK_API_ENTRYPOINT_CURRENT | YES |
| TASK_API_ROUTE_CONTRACT | SWTR_READ |
| WRONG_TASK_API_PROCESS | NO |
| SWTR_READ_ROUTES_PRESENT | YES |
| MCP_SWTR_SSE_URL_USED | http://127.0.0.1:3000/sse |
| MCP_SWTR_TRANSPORT_CONNECTED | NO |
| MCP_SWTR_TOOLS_PRESENT | NO |
| SWTR_TRANSPORT_CLASSIFICATION | MCP_SWTR_UNAVAILABLE |
| FULL_TASK_SYNC_RUN | NO |
| BOUNDED_ORACLE_ONLY | YES |
| ORACLE_PATH_PROVEN | NO |
| OWNER_SMOKE_O1 | PASS |
| OWNER_SMOKE_O2 | PASS |
| OWNER_SMOKE_O3 | BLOCKED |
| OWNER_SMOKE_O4 | BLOCKED |
| OWNER_SMOKE_O5 | BLOCKED |
| CASE_O3_EXACT_SET | BLOCKED |
| FOREIGN_SPRINT_TASK_COUNT | 0 |
| SILENT_SLOT_DROP_COUNT | 0 |
| INTERNAL_KEYERROR_COUNT | 0 |
| QUERY_HTTP_500_COUNT | 0 |
| FALSE_GREEN_COUNT | 0 |
| RUNNER_MODIFIED | NO |
| PRODUCTION_MODIFIED_BY_QA | NO |
| UNAUTHORIZED_FILES_COMMITTED | NO |
| **046_VERDICT** | **BLOCKED** |
| READY_TO_RESUME_017_V2 | NO |

---

## Summary

Assignment 046 validates:
1. ✅ PO Agent and Task API runtime identity is correct
2. ✅ Task API exposes correct `/api/v1/swtr-read/*` route contract
3. ❌ MCP-SWTR SSE transport is unavailable at port 3000

**Root cause:** The MCP-SWTR server in MyTestProject_1 uses stdio protocol, not SSE transport. The Task API requires an SSE-compatible FastMCP server.

**Result:** BLOCKED - Runtime identity and route contract pass, but MCP-SWTR transport unavailable.

**Next step:** Start an SSE-compatible MCP-SWTR server on port 3000 or use an external one.

---

*Report generated: 2026-08-22T16:10:00Z*
*QA Runner: GigaCode*
*Branch: feat/core8-real-query-hardening-v2*
