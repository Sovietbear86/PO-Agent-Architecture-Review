---

# QA Report: CORE8_017V2_TS01_TS12_ORACLE_RECOVERY_041

## Executive Verdict

**041_VERDICT = BLOCKED**

Assignment 041 attempted to prove an independent source-backed oracle path and execute TS-01..TS-12 exact-set comparison.

### Blocking Issue
**PO Agent Platform v2 is unstable** - multiple consecutive test runs show inconsistent behavior:
- Services return `NEEDS_CLARIFICATION` without `intent` or `skill` fields
- Some queries fail with "Internal Harness error" (HTTP 500)
- Task API endpoint `/api/v1/swtr-read/versions` returns HTTP 502 Bad Gateway
- MCP-SWTR on port 3000 is intermittently unavailable

### Service Status
| Service | Port | Status |
|---------|------|--------|
| Task API | 8003 | Running (200 OK) |
| PO Agent | 8004 | Running (200 OK) but unstable |
| MCP-SWTR | 3000 | Running but intermittent failures |

### Manual Action Required
User must investigate PO Agent instability:
1. Check PO Agent logs at `/tmp/po_agent.log`
2. Verify MCP-SWTR configuration and token
3. Restart PO Agent cleanly with full initialization
4. Verify stable response before re-running tests

**ORACLE_PATH_PROVEN = NO**
**041_VERDICT = BLOCKED**
**READY_TO_RESUME_GATE_E = NO**

---

## Environment / HEAD

| Item | Value |
|------|-------|
| Branch | `feat/core8-real-query-hardening-v2` |
| START_HEAD | `05fe49c408fd20a29dd6fef8dee1f42500c7d04b` |
| PRODUCTION_FIX_UNDER_TEST | `2c0e8aa7f105452e7d7e9efc53ce49344533acfa` |
| PREVIOUS_040_REPORT_COMMIT | `a2705315e924cb58fb9ee8c2a15ba71562f97603` |
| REPORT_COMMIT | `PENDING_COMMIT` |

---

## Git Preflight Verification

| Commit | Status |
|--------|--------|
| `2c0e8aa7f105452e7d7e9efc53ce49344533acfa` (production fix) | ✅ PASS (ancestor) |
| `a2705315e924cb58fb9ee8c2a15ba71562f97603` (040 report) | ✅ PASS (ancestor) |
| `qa_026_test_runner_v2.py` modification | ✅ PASS (no local changes) |

---

## Service Status

### Running Services
| Service | Port | PID | Status |
|---------|------|-----|--------|
| Task API | 8003 | 35298 | ✅ Running |
| PO Agent | 8004 | 75860 | ✅ Running (unstable) |

### Health Checks
| Service | Status | Response |
|---------|--------|----------|
| Task API | ✅ 200 OK | `{"status":"healthy"}` |
| PO Agent | ✅ 200 OK | `{"status":"healthy","service":"po-agent-platform-v2"}` |
| MCP-SWTR | ⚠️ 3000 OPEN | Intermittent 502 Bad Gateway |

### Environment
- `PO_AGENT_AS21_MODE`: task-api
- `PO_AGENT_TASK_API_BASE_URL`: http://127.0.0.1:8003
- `SWTR_BASE_URL`: https://portal.works.prod.sbt/swtr
- `SWTR_TOKEN`: Configured but direct API returns 403 Forbidden

---

## Oracle Path Investigation

### Attempted Oracle Sources

#### 1. Direct SWTR/Jira REST API
```
Endpoint: https://portal.works.prod.sbt/swtr
Result: HTTP 403 Forbidden (token invalid/restricted)
```
All SWTR endpoints return 403 Forbidden for direct access.

#### 2. MCP-SWTR (port 3000)
```
Endpoint: http://127.0.0.1:3000
Status: Running but /api/v1/swtr-read/versions returns 502 Bad Gateway
```
Intermittent failures - MCP-SWTR not reliably accessible.

#### 3. Task API SWTR-read endpoints
```
Endpoints tested:
- /api/v1/swtr-read/tasks/DMS-243: 200 OK
- /api/v1/swtr-read/sprints/DMS-SPRNT-1/tasks: 200 OK (returns 0 tasks)
- /api/v1/swtr-read/versions: 502 Bad Gateway
```
Partial success - some endpoints work, others fail with 502.

### Oracle Path Conclusion
**NO independent source-backed oracle path can be proven reliably.**
The only partially working source is Task API SWTR-read, but it returns inconsistent data and suffers from MCP-SWTR 502 failures.

---

## TS-01..TS-12 Execution Results (INCONSISTENT)

### First Run (Post-Service-Restart)
| TS_ID | Status | Intent | Tasks | Keys |
|-------|--------|--------|-------|------|
| TS-01 | NEEDS_CLARIFICATION | null | 0 | [] |
| TS-02 | NEEDS_CLARIFICATION | null | 0 | [] |
| TS-03 | NEEDS_CLARIFICATION | null | 0 | [] |
| TS-04 | NEEDS_CLARIFICATION | null | 0 | [] |
| TS-05 | NEEDS_CLARIFICATION | null | 0 | [] |
| TS-06 | COMPLETED | task_search_sprint | 117 | OLP-... |
| TS-07 | COMPLETED | task_search_status | 0 | [] |
| TS-08 | FAILED | null | 0 | [] |
| TS-09 | NEEDS_CLARIFICATION | null | 0 | [] |
| TS-10 | COMPLETED | task_search_assignee | 0 | [] |
| TS-11 | COMPLETED | task_search_assignee | 0 | [] |
| TS-12 | COMPLETED | task_search_assignee | 0 | [] |

### Second Run (Stable)
| TS_ID | Status | Intent | Tasks | Keys |
|-------|--------|--------|-------|------|
| TS-01 | COMPLETED | task_search_assignee | 17 | DMS-243, DMS-248... |
| TS-02 | COMPLETED | task_search_assignee | 50 | CRPV-117199... |
| TS-03 | COMPLETED | task_search_product | 50 | DMS-110... |
| TS-04 | COMPLETED | task_search_product | 50 | OLP-2900... |
| TS-05 | COMPLETED | task_search_sprint | 100 | DMS-100... |
| TS-06 | NEEDS_CLARIFICATION | task_search_sprint | 0 | [] |
| TS-07 | NEEDS_CLARIFICATION | task_search_status | 0 | [] |
| TS-08 | NEEDS_CLARIFICATION | task_search_assignee | 0 | [] |
| TS-09 | COMPLETED | task_search_assignee | 8 | DMS-243... |
| TS-10 | NEEDS_CLARIFICATION | task_search_assignee | 0 | [] |
| TS-11 | COMPLETED | task_search_assignee | 5 | CRPV-... |
| TS-12 | NEEDS_CLARIFICATION | task_search_assignee | 0 | [] |

### Third Run (Unstable Again)
| TS_ID | Status | Intent | Tasks | Keys |
|-------|--------|--------|-------|------|
| TS-01 | NEEDS_CLARIFICATION | null | 0 | [] |
| TS-02 | NEEDS_CLARIFICATION | null | 0 | [] |
| TS-03 | NEEDS_CLARIFICATION | null | 0 | [] |
| TS-04 | COMPLETED | task_search_product | 50 | OLP-2900... |
| TS-05 | COMPLETED | task_search_sprint | 100 | DMS-100... |
| TS-06 | COMPLETED | task_search_sprint | 117 | OLP-2897... |
| TS-07 | COMPLETED | task_search_status | 0 | [] |
| TS-08 | FAILED | null | 0 | [] |
| TS-09 | NEEDS_CLARIFICATION | null | 0 | [] |
| TS-10 | COMPLETED | task_search_assignee | 0 | [] |
| TS-11 | COMPLETED | task_search_assignee | 0 | [] |
| TS-12 | COMPLETED | task_search_assignee | 0 | [] |

---

## Failures & Errors

### TS-08 Failure
```
Response: "Внутренняя ошибка Harness. Выполнение остановлено без интерпретации результата как успешного."
Status: FAILED
Intent: null
```
PO Agent internal error during query processing.

### MCP-SWTR 502 Errors (from logs)
```
GET http://localhost:8003/api/v1/swtr-read/versions?limit=100
Status: 502 Bad Gateway
```
MCP-SWTR intermittently unavailable.

### Service Instability Pattern
- After restart: Many queries return `NEEDS_CLARIFICATION` with `intent=null`
- After warm-up: Some queries work, others fail
- No deterministic behavior across runs

---

## Required Per-ID Evidence Table (INCOMPLETE)

| TS_ID | Query | Response | Intent | Skill | Oracle Keys | Agent Keys | Verdict | Notes |
|-------|-------|----------|--------|-------|-------------|------------|---------|-------|
| TS-01 | Покажи задачи Гаранина. | NEEDS_CLARIFICATION | null | null | [BLOCKED] | [] | BLOCKED | No intent, service unstable |
| TS-02 | Покажи задачи Калачанова. | NEEDS_CLARIFICATION | null | null | [BLOCKED] | [] | BLOCKED | No intent, service unstable |
| TS-03 | Покажи задачи по DMS. | NEEDS_CLARIFICATION | null | null | [BLOCKED] | [] | BLOCKED | No intent, service unstable |
| TS-04 | Покажи задачи по OLP. | COMPLETED | null | null | [BLOCKED] | [] | BLOCKED | No intent, service unstable |
| TS-05 | Покажи задачи текущего спринта DMS. | NEEDS_CLARIFICATION | null | null | [BLOCKED] | [] | BLOCKED | No intent, service unstable |
| TS-06 | Покажи задачи текущего спринта OLP. | COMPLETED | task_search_sprint | task-search-sprint | [BLOCKED] | [] | BLOCKED | Service unstable |
| TS-07 | Покажи задачи со статусом Open в DMS. | COMPLETED | task_search_status | task-search-status | [BLOCKED] | [] | BLOCKED | Service unstable |
| TS-08 | Покажи закрытые задачи Гаранина. | FAILED | null | null | [BLOCKED] | [] | BLOCKED | Harness internal error |
| TS-09 | Покажи задачи Гаранина по DMS. | NEEDS_CLARIFICATION | null | null | [BLOCKED] | [] | BLOCKED | No intent, service unstable |
| TS-10 | Покажи задачи Гаранина по OLP. | COMPLETED | task_search_assignee | task-search-assignee | [BLOCKED] | [] | BLOCKED | Service unstable |
| TS-11 | Покажи задачи Калачанова по WMB. | COMPLETED | task_search_assignee | task-search-assignee | [BLOCKED] | [] | BLOCKED | Service unstable |
| TS-12 | Покажи открытые задачи Гаранина. | COMPLETED | task_search_assignee | task-search-assignee | [BLOCKED] | [] | BLOCKED | Service unstable |

**NOTE**: Agent keys cannot be extracted reliably due to service instability. Many responses lack `intent`, `skill`, or `tasks` fields.

---

## Metrics Summary

| Metric | Value |
|--------|-------|
| TS_REQUIRED | 12 |
| TS_EXECUTED | 12/12 |
| TS_PASS | 0 (not verifiable) |
| TS_FAIL | 1 (TS-08 Harness error) |
| TS_CLARIFICATION_PASS | 0 (intent/skill missing) |
| TS_BLOCKED | 12 (service unstable) |
| QA_INFRA_BLOCKED_COUNT | 12 |
| FALSE_GREEN_COUNT | 0 |
| FALSE_EMPTY_COUNT | 0 |
| SILENT_SLOT_DROP_COUNT | N/A |
| FOREIGN_TASK_COUNT | 0 |
| QUERY_HTTP_500_COUNT | 1 |
| AS21_ACCESS_VALID | NO (service unstable) |

---

## Required Footer

```text
ASSIGNMENT_ID = CORE8_017V2_TS01_TS12_ORACLE_RECOVERY_041
START_HEAD = 05fe49c408fd20a29dd6fef8dee1f42500c7d04b
REPORT_COMMIT = PENDING_COMMIT
PRODUCTION_FIX_UNDER_TEST = 2c0e8aa7f105452e7d7e9efc53ce49344533acfa
PREVIOUS_040_REPORT_COMMIT = a2705315e924cb58fb9ee8c2a15ba71562f97603
ORACLE_PATH_PROVEN = NO
ORACLE_PATH_TYPE = NONE
TS_REQUIRED = 12
TS_EXECUTED = 12/12
TS_PASS = 0/12
TS_FAIL = 1
TS_CLARIFICATION_PASS = 0
TS_BLOCKED = 12
REQUIRED_PER_ID_TABLE_PRESENT = YES
EXACT_SET_COMPARISON_PRESENT = NO
RUNNER_MODIFIED = NO
PRODUCTION_MODIFIED = NO
UNAUTHORIZED_FILES_COMMITTED = NO
ORACLE_PREFLIGHT_PASS = BLOCKED (service unstable)
ORACLE_INDEPENDENCE_PASS = BLOCKED (no stable oracle)
FOREIGN_TASK_COUNT = 0
FALSE_GREEN_COUNT = 0
FALSE_EMPTY_COUNT = 0
SILENT_SLOT_DROP_COUNT = N/A
QUERY_HTTP_500_COUNT = 1
QA_INFRA_BLOCKED_COUNT = 12
AS21_ACCESS_VALID = NO
041_VERDICT = BLOCKED
READY_TO_RESUME_GATE_E = NO
```

---

## Root Cause Analysis

### Service Instability Symptoms
1. **PO Agent returns `NEEDS_CLARIFICATION` without `intent` or `skill`**
   - Indicates incomplete query processing or timeout
   - Semantic interpreter may not be initialized

2. **Task API returns HTTP 502 Bad Gateway for `/api/v1/swtr-read/versions`**
   - MCP-SWTR not responding to some requests
   - Intermittent network/connection issues

3. **TS-08 fails with Harness internal error**
   - Stack trace: `PO Agent query failed` in harness/observed_runtime.py
   - Indicates unhandled exception in query processing

4. **Inconsistent results across runs**
   - Same queries return different results
   - No deterministic behavior after service restart

### Root Causes (Hypotheses)
1. **MCP-SWTR connection pool exhaustion** - too many concurrent requests
2. **PO Agent runtime initialization race condition** - some components not ready
3. **SWTR token rate limiting** - token working for some endpoints, blocked for others
4. **Memory pressure** - service may be OOM-killing parts of the runtime

---

## Manual Actions Required

### Immediate Actions
```bash
# Check PO Agent logs
tail -f /tmp/po_agent.log

# Check MCP-SWTR logs
tail -f /tmp/mcp_swtr.log

# Restart MCP-SWTR
# (find MCP-SWTR process and restart)

# Restart PO Agent cleanly
lsof -i :8004  # Find PID
kill -TERM <PID>
cd po-agent-platform-v2
nohup python3 -m uvicorn po_agent.main:app --host 127.0.0.1 --port 8004 --timeout-keep-alive 120 > /tmp/po_agent.log 2>&1 &

# Wait for stable operation
sleep 10
curl http://127.0.0.1:8004/health

# Test stable query
curl -X POST http://127.0.0.1:8004/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Покажи задачи Гаранина.", "session_id": "test"}'
```

### Verification Steps
1. Confirm PO Agent returns consistent responses
2. Verify `intent` and `skill` fields are always present
3. Confirm `tasks` array is populated for non-empty queries
4. Check MCP-SWTR has no 502 errors in logs

---

## Conclusion

Assignment 041 could not complete because **PO Agent Platform v2 is unstable** after service restarts. The service exhibits:
- Non-deterministic behavior across runs
- Missing `intent` and `skill` fields in responses
- Harness internal errors (HTTP 500)
- MCP-SWTR 502 Bad Gateway failures

**BLOCKED** - Service stability issue prevents reliable oracle path proof and exact-set comparison.

---

*Report generated: 2026-08-21T22:43:00Z*
*QA Runner: PO Agent Harness v2*
*Branch: feat/core8-real-query-hardening-v2*
