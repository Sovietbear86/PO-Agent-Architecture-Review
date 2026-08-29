# SWTR Runtime Hardening Report

**Assignment:** 098-R2  
**Date:** 2026-08-29  
**Status:** COMPLETE  
**Branch:** feat/core8-real-query-hardening-v2

---

## EXECUTIVE SUMMARY

SWTR runtime has been **HARDENED**. All checks pass in real environment.

**VERDICT: SWTR_RUNTIME_HARDENED**

---

## HEALTH GUARD RESULTS

### HEALTH GUARD: PASS

```
SWTR_HEALTH: SWTR_HEALTHY
```

### Detailed Check Results

| Check | Status | Details |
|-------|--------|---------|
| Runtime freshness | PASS | PID 33151, HEAD 80e65e0 |
| MCP-SWTR health | PASS | HTTP 200 |
| MCP stdio transport | PASS | 48 tools, read_unit available |
| Real SWTR read | PASS | DMS-273, HTTP 200 |
| HTTP path | PASS | HTTP 200 |
| Bounded sync | PASS | HTTP 200 |
| PO Agent path | PASS | Verified |
| Status proof | PASS | workflow_status = Зарегистрирован |
| Repeatability | PASS | 3x consistent |

---

## RUNTIME FRESHNESS

### RUNTIME FRESHNESS: PASS

- **Running PID:** 33151
- **Expected HEAD:** 80e65e02b5bb203b4823ed65ab87dcc80930b4cd
- **Actual HEAD:** 80e65e02b5bb203b4823ed65ab87dcc80930b4cd
- **Task API CWD:** `task-api/`

---

## DIRECT MCP CANARY

### DIRECT MCP CANARY: PASS

- **Canary Task:** DMS-273
- **MCP Transport:** stdio
- **Response Type:** text
- **Response Code:** DMS-273
- **Workflow Status:** Зарегистрирован

---

## TASK API CANARY

### TASK API CANARY: PASS

- **HTTP Endpoint:** `GET /api/v1/swtr-read/tasks/DMS-273`
- **Response Code:** 200
- **Task Code:** DMS-273
- **Workflow Status:** Зарегистрирован

---

## 3x STABILITY

### 3x STABILITY: PASS

| Request | Status | Task Code | Workflow Status |
|---------|--------|-----------|-----------------|
| 1 | 200 | DMS-273 | Зарегистрирован |
| 2 | 200 | DMS-273 | Зарегистрирован |
| 3 | 200 | DMS-273 | Зарегистрирован |

---

## CONFIGURATION VERIFICATION

### TOKEN ENV REQUIRED: NO

- SWTR_TOKEN in Task API parent environment is NOT required
- MCP-SWTR wrapper loads credentials from `mcp-swtr/.env`
- Fallback to `~/.config/swtr/api_key` is supported

### SWTR:WMB REQUIRED: NOT PROVEN

- No evidence of `swtr:wmb` scope requirement in code
- No evidence in configuration
- No evidence in documentation
- Error messages do not indicate required scope

---

## FILES MODIFIED

| File | Action | Description |
|------|--------|-------------|
| `task-api/tests/test_swtr_health_guard.py` | MODIFIED | Added MCP stdio transport check, path fixes |
| `docs/SWTR_RUNTIME_HEALTH.md` | CREATED | Operational documentation |
| `qa_reports/SWTR_502_ROOT_CAUSE_098_R1.md` | CREATED | Root cause analysis |

---

## HEALTH GUARD ENHANCEMENTS

### New Check: MCP Stdio Transport

**Purpose:** Verify MCP stdio transport works and protocol is valid

**Checks:**
1. Transport is stdio
2. Tools list returns non-empty
3. read_unit tool exists
4. read_unit(DMS-273) returns valid response
5. Response type is "text"
6. Task code matches request
7. JSON is parseable

**Failure Status:** MCP_STDIO_FAILED or MCP_PROTOCOL_INVALID

### Path Resolution Fix

Fixed module import issue in health guard:
- Added `task-api` to sys.path
- Used relative path resolution

---

## TESTS IMPLEMENTED

### Unit Tests (via pytest)

Run from `task-api/`:

```bash
pytest tests/test_swtr_health_guard.py -v
```

### Manual Health Check

```bash
cd task-api
python3 tests/test_swtr_health_guard.py
```

### Expected Output

```
SWTR_HEALTH: SWTR_HEALTHY
```

---

## RECOVERY PROCEDURE

If SWTR health fails:

1. **Run health guard** to identify failing check
2. **Verify runtime freshness** - check HEAD mismatch
3. **Verify direct MCP canary** - test stdio transport
4. **Compare Task API path** - verify startup command
5. **Restart only if stale** - confirm HEAD mismatch
6. **Rerun canary** - verify recovery

---

## SECRETS EXPOSURE

### SECRETS EXPOSED: NO

- No token values printed
- No credential fingerprints in logs
- No secrets in git commits
- No secrets in health guard output

---

## GIT HISTORY

```
6ad9583 qa: SWTR_RUNTIME_HEALTH_098_R2
80e65e0 qa: SWTR_502_ROOT_CAUSE_098_R1
58f9c70 qa: REGRESSION_BASELINE_AND_SWTR_HEALTH_098
```

---

## VERIFICATION COMMANDS

### Check SWTR Health

```bash
cd task-api
python3 tests/test_swtr_health_guard.py
```

### Run DMS-273 Canary

```python
import httpx
r = httpx.get('http://127.0.0.1:8003/api/v1/swtr-read/tasks/DMS-273', timeout=30)
assert r.status_code == 200
assert r.json()['task_code'] == 'DMS-273'
```

### Check Process Freshness

```bash
# Get PID
lsof -i :8003 -t

# Check HEAD
cd task-api && git rev-parse HEAD
```

---

## NEXT STEPS

### STOP - Do NOT start 099 automatically

Assignment 098 is CLOSED. The SWTR runtime is hardened and ready for:

1. **Assignment 099 final certification** - if approved
2. **Real SWTR regression testing** - with health guard enabled
3. **Oracle testing** - with verified SWTR connectivity

---

## SIGN-OFF

| Item | Status |
|------|--------|
| Health guard enhanced | ✅ |
| Real read canary added | ✅ |
| Stale runtime protection | ✅ |
| Recovery procedure documented | ✅ |
| Tests implemented | ✅ |
| Real environment verified | ✅ |
| 3x stability confirmed | ✅ |
| No secrets exposed | ✅ |
| No temporary debug code | ✅ |

---

**FINAL VERDICT: SWTR_RUNTIME_HARDENED**

**Ready for Assignment 099 final certification.**
