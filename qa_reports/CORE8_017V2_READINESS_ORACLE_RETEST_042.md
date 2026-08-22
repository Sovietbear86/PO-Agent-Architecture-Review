# CORE8_017V2_READINESS_ORACLE_RETEST_042

## Executive Summary

**042_VERDICT = BLOCKED**

Assignment 042 is BLOCKED because the independent oracle path required for exact-set comparison cannot be proven. Multiple infrastructure issues prevent source-backed oracle evidence collection:

1. **MCP-SWTR is not running** in this repository - only present in the adjacent MyTestProject_1 project
2. **Task API swtr-read endpoints return 404** - router not properly registered or server not restarted
3. **PO Agent running in FAKE mode** instead of task-api mode as required for real AS21 data access
4. **Task API tasks endpoint lacks `key` field** - returns internal UUID instead of SWTR task key (e.g., DMS-243)

---

## Preflight

| Check | Status | Evidence |
|-------|--------|----------|
| ACTIVE_ASSIGNMENT = 042 | ✅ PASS | GIGACODE_NEXT_ACTION.md |
| ACTIVE_ASSIGNMENT_FILE = qa_assignments/CORE8_017V2_READINESS_ORACLE_RETEST_042.md | ✅ PASS | File exists |
| ALLOWED_REPORT_FILE = qa_reports/CORE8_017V2_READINESS_ORACLE_RETEST_042.md | ✅ PASS | Allowed |
| 041 report ancestor | ✅ PASS | 4ce7e59 is ancestor of HEAD |
| qa_026_test_runner_v2.py not modified | ✅ PASS | git diff empty |
| No prohibited files staged | ✅ PASS | git status clean |

**START_HEAD = 4669df594b3719c9b73fb816530830ccca5f784d**

---

## Phase 1: Readiness Validation

### Service Status

| Service | Port | PID | Status |
|---------|------|-----|--------|
| Task API | 8003 | 29199 | Running (404 errors on swtr-read) |
| PO Agent | 8004 | 32111 | Running (in FAKE mode) |
| MCP-SWTR | 3000 | NOT RUNNING | Not installed in this repo |

**Note**: MCP-SWTR exists in `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/MyTestProject_1/MyTestProject_1/mcp-swtr/` but is not part of PO-Agent-Architecture-Review.

### Service Health Check Results

**Task API `/health`:**
```json
{
  "status": "healthy"
}
```

**Task API `/api/v1/swtr-read/health` returns HTTP 404 Not Found**

**Task API `/api/v1/swtr-read/versions` returns HTTP 404 Not Found**

**Task API `/api/v1/tasks` returns 200 OK** but contains no `key` field:
- Tasks use internal UUIDs (e.g., "30670021-50fa-47ec-bc0b-11d78bf17118")
- SWTR task keys (e.g., "DMS-243") are stored in `source_id` field
- This prevents exact-set comparison with PO Agent responses

**PO Agent `/health`:**
```json
{
  "status": "healthy",
  "service": "po-agent-platform-v2",
  "runtime": "harness-dialogue-v2",
  "adapter": "fake",
  "semantic_mode": "qwen-llm",
  "source_status": "healthy",
  "source_error": null,
  "runtime_init_error": null,
  "source_facts": ["attachments", "releases", "spaces", "sprints", "tasks", "team_competencies"],
  "skill_readiness": {"ready": 47, "degraded": 0, "unavailable": 7, "planned": 0},
  "correlation_id": "6366d53c-3dae-492e-b685-e96abfa677ee",
  "timestamp": "2026-08-22T14:48:12Z"
}
```

**PO Agent `/api/v1/health`:**
```json
{
  "status": "healthy",
  "service": "po-agent-platform-v2",
  "runtime": "harness-dialogue-v2",
  "adapter": "fake",
  "semantic_mode": "qwen-llm",
  "source_status": "healthy",
  "source_error": null,
  "runtime_init_error": null,
  "source_facts": ["attachments", "releases", "spaces", "sprints", "tasks", "team_competencies"],
  "skill_readiness": {"ready": 47, "degraded": 0, "unavailable": 7, "planned": 0},
  "correlation_id": "6366d53c-3dae-492e-b685-e96abfa677ee",
  "timestamp": "2026-08-22T14:48:12Z"
}
```

### Readiness Check Results

| Check | Status |
|-------|--------|
| Root `/health` returns readiness fields | ✅ PASS |
| `/api/v1/health` returns readiness fields | ✅ PASS |
| `status` = "healthy" | ✅ PASS |
| `source_status` = "healthy" | ✅ PASS |
| `runtime_init_error` = null | ✅ PASS |
| Health payloads agree | ✅ PASS |

**ROOT_HEALTH_READINESS_AWARE = YES**
**ROOT_HEALTH_STATUS = healthy**
**API_V1_HEALTH_STATUS = healthy**
**HEALTH_PAYLOADS_AGREE = YES**

### Critical Findings

| Issue | Severity | Impact |
|-------|----------|--------|
| PO Agent running in FAKE mode | HIGH | No real AS21 data access |
| MCP-SWTR not running | CRITICAL | No SWTR source data via MCP |
| swtr-read endpoints return 404 | CRITICAL | No SWTR source data via Task API |
| Tasks lack `key` field | CRITICAL | Cannot build oracle key sets |

---

## Phase 2: Independent Oracle Path Investigation

### Oracle Sources Evaluated

| Source | Endpoint | Status | Reason |
|--------|----------|--------|--------|
| Direct SWTR/Jira REST | https://portal.works.prod.sbt/swtr | ❌ FAIL | No credentials in environment |
| MCP-SWTR | http://127.0.0.1:3000/sse | ❌ FAIL | Service not installed in repo |
| Task API SWTR-read | http://127.0.0.1:8003/api/v1/swtr-read/* | ❌ FAIL | All endpoints return 404 |
| Task API tasks | http://127.0.0.1:8003/api/v1/tasks | ⚠️ PARTIAL | Returns data but no `key` field |

### Task API Response Analysis

**Task API `/api/v1/tasks` returns:**
```json
{
  "id": "30670021-50fa-47ec-bc0b-11d78bf17118",
  "title": "[OLP] OLAP Analytics подготовка к БП2027",
  "source_id": "OLP-123",
  "project_space": "OLP",
  "sprint": "OLP-SPRNT-2027-1",
  "status": "In Progress",
  ...
}
```

**Critical Issue**: The `id` field contains an internal UUID, NOT the SWTR task key (e.g., DMS-243). The actual task key is stored in `source_id`.

For exact-set comparison with PO Agent responses (which return task keys), I would need to:
1. Map PO Agent keys to Task API `source_id` values
2. OR expose `key` field in Task API task responses

Neither approach is currently available.

### SWTR MCP Client Configuration

The SWTR MCP client in `task-api/app/services/swtr_mcp_client.py` uses:
- Default URL: `http://127.0.0.1:3000/sse`
- Environment variable: `SWTR_MCP_SSE_URL`

**MCP-SWTR is not installed in this repository.** It exists only in the adjacent MyTestProject_1 project at:
- `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/MyTestProject_1/MyTestProject_1/mcp-swtr/mcp_server.py`

### Oracle Path Conclusion

**NO INDEPENDENT ORACLE PATH PROVEN**

All source-backed oracle paths are unavailable:
- MCP-SWTR not installed in this repo (only in MyTestProject_1)
- Task API swtr-read endpoints return 404 (router issue)
- Task API tasks endpoint lacks `key` field for comparison
- No SWTR credentials available in environment

**ORACLE_PATH_PROVEN = NO**
**ORACLE_PATH_TYPE = NONE**

---

## Phase 3: TS Cases Execution

All TS cases are BLOCKED due to:

1. **No oracle path** - Cannot build `ORACLE_KEYS` for comparison
2. **Adapter = FAKE** - PO Agent uses FakeAS21Adapter, not real SWTR data
3. **Task API issues** - swtr-read endpoints not working, tasks lack `key` field

### Blocked TS Cases

| TS_ID | Query | Verdict | Evidence |
|-------|-------|---------|----------|
| TS-01 | Покажи задачи Гаранина. | BLOCKED | Oracle path not proven, FAKE adapter |
| TS-02 | Покажи задачи Калачанова. | BLOCKED | Oracle path not proven, FAKE adapter |
| TS-03 | Покажи задачи по DMS. | BLOCKED | Oracle path not proven, FAKE adapter |
| TS-04 | Покажи задачи по OLP. | BLOCKED | Oracle path not proven, FAKE adapter |
| TS-05 | Покажи задачи текущего спринта DMS. | BLOCKED | Oracle path not proven, FAKE adapter |
| TS-06 | Покажи задачи текущего спринта OLP. | BLOCKED | Oracle path not proven, FAKE adapter |
| TS-07 | Покажи задачи со статусом Open в DMS. | BLOCKED | Oracle path not proven, FAKE adapter |
| TS-08 | Покажи закрытые задачи Гаранина. | BLOCKED | Oracle path not proven, FAKE adapter |
| TS-09 | Покажи задачи Гаранина по DMS. | BLOCKED | Oracle path not proven, FAKE adapter |
| TS-10 | Покажи задачи Гаранина по OLP. | BLOCKED | Oracle path not proven, FAKE adapter |
| TS-11 | Покажи задачи Калачанова по WMB. | BLOCKED | Oracle path not proven, FAKE adapter |
| TS-12 | Покажи открытые задачи Гаранина. | BLOCKED | Oracle path not proven, FAKE adapter |

**TS_EXECUTED = 0/12**
**TS_PASS = 0**
**TS_FAIL = 0**
**TS_CLARIFICATION_PASS = 0**
**TS_BLOCKED = 12**

**REQUIRED_PER_ID_TABLE_PRESENT = NO** (all rows blocked)
**EXACT_SET_COMPARISON_PRESENT = NO**

---

## PO Agent Service Configuration

### Current Configuration (FAKE MODE)

**Environment:**
```
AS21_MODE=fake
TASK_API_BASE_URL=http://localhost:8003
```

**Adapter:** `FakeAS21Adapter` - Uses canned/test data, not real SWTR

### Required Configuration (TASK-API MODE)

**Environment:**
```
AS21_MODE=task-api
TASK_API_BASE_URL=http://127.0.0.1:8003
```

**Adapter:** `EvidenceValidatedProductionTaskApiAS21Adapter` - Connects to real SWTR

### Required Actions to Unblock

1. **Install MCP-SWTR** in PO-Agent-Architecture-Review:
   - Copy or symlink from MyTestProject_1/mcp-swtr
   - Configure token with swtr:wmb role
   - Start server on port 3000

2. **Fix swtr-read endpoints**:
   - Verify router registration in task-api/main.py
   - Restart Task API server after changes

3. **Restart PO Agent with task-api mode**:
   ```bash
   cd po-agent-platform-v2
   AS21_MODE=task-api TASK_API_BASE_URL=http://127.0.0.1:8003 \
     python3 -m uvicorn src.po_agent.main:app --host 127.0.0.1 --port 8004
   ```

4. **Add `key` field to Task API tasks**:
   - Modify `/api/v1/tasks` response to include SWTR task key
   - Or expose `source_id` as `key` in task responses

---

## Manual Action Required

To unblock Assignment 042, the following infrastructure issues must be resolved:

1. **MCP-SWTR Installation**
   - Copy MCP-SWTR source code from MyTestProject_1/mcp-swtr
   - Configure SWTR credentials with swtr:wmb role
   - Start MCP-SWTR server on port 3000

2. **Task API swtr-read Endpoints**
   - Investigate why `/api/v1/swtr-read/*` returns 404
   - Verify router registration and restart Task API

3. **PO Agent task-api Mode**
   - Set `AS21_MODE=task-api`
   - Restart PO Agent with new configuration

4. **Task Key Field**
   - Ensure Task API tasks include SWTR task key
   - Current `source_id` field must be exposed or mapped

Once infrastructure is resolved, re-run Assignment 042 with:
- Real AS21 data access
- Working MCP-SWTR transport
- Task API swtr-read endpoints operational
- Tasks include `key` field for exact-set comparison

---

## Footer Metrics

| Metric | Value |
|--------|-------|
| ASSIGNMENT_ID | CORE8_017V2_READINESS_ORACLE_RETEST_042 |
| START_HEAD | 4669df594b3719c9b73fb816530830ccca5f784d |
| REPORT_COMMIT | PENDING_BEFORE_COMMIT |
| PREVIOUS_041_REPORT_COMMIT | 4ce7e595e0a6112f45cc4f3162030e0c9f065809 |
| ROOT_HEALTH_READINESS_AWARE | YES |
| ROOT_HEALTH_STATUS | healthy |
| API_V1_HEALTH_STATUS | healthy |
| HEALTH_PAYLOADS_AGREE | YES |
| ORACLE_PATH_PROVEN | NO |
| ORACLE_PATH_TYPE | NONE |
| TS_REQUIRED | 12 |
| TS_EXECUTED | 0/12 |
| TS_PASS | 0 |
| TS_FAIL | 0 |
| TS_CLARIFICATION_PASS | 0 |
| TS_BLOCKED | 12 |
| REQUIRED_PER_ID_TABLE_PRESENT | NO |
| EXACT_SET_COMPARISON_PRESENT | NO |
| RUNNER_MODIFIED | NO |
| PRODUCTION_MODIFIED | NO |
| UNAUTHORIZED_FILES_COMMITTED | NO |
| ORACLE_PREFLIGHT_PASS | NO |
| ORACLE_INDEPENDENCE_PASS | NO |
| FOREIGN_TASK_COUNT | 0 |
| FALSE_GREEN_COUNT | 0 |
| FALSE_EMPTY_COUNT | 0 |
| SILENT_SLOT_DROP_COUNT | 0 |
| QUERY_HTTP_500_COUNT | 0 |
| QA_INFRA_BLOCKED_COUNT | 12 |
| AS21_ACCESS_VALID | NO (FAKE adapter, no MCP-SWTR) |
| **042_VERDICT** | **BLOCKED** |
| READY_TO_RESUME_GATE_E | NO |

---

*Report generated: 2026-08-22T14:48:00Z*
*QA Runner: PO Agent Harness v2*
*Branch: feat/core8-real-query-hardening-v2*
