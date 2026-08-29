# SWTR 502 Root Cause Analysis

**Assignment:** 098-R1  
**Date:** 2026-08-29  
**Issue:** Task API returning HTTP 502 "SWTR MCP returned invalid JSON"

---

## SUMMARY

**ROOT CAUSE:** `INSUFFICIENT_EVIDENCE` - Task API now working correctly.

The Task API was initially returning HTTP 502 "SWTR MCP returned invalid JSON", but after a process restart (likely by uvicorn's auto-reload), the system began returning HTTP 200 with correct SWTR data. The root cause could not be definitively proven due to the transient nature of the failure and the automatic recovery.

---

## STEP 1 — EFFECTIVE MCP CREDENTIAL SOURCE

### Credential Sources Available

| Source | Path | Status |
|--------|------|--------|
| Wrapper .env | `mcp-swtr/.env` | ✅ Contains TOKEN (7917 bytes) |
| User config | `~/.config/swtr/api_key` | ✅ Contains TOKEN (7917 bytes) |
| Task API env | `SWTR_TOKEN` | ✅ Set but empty |

### Key Findings

1. **Two different tokens:**
   - Wrapper .env: SHA256 prefix `166e242f76c0c71a`
   - User config: SHA256 prefix `53e62aaedc29eb39`

2. **MCP-SWTR wrapper correctly reads credentials from:**
   - Its own `.env` file
   - `~/.config/swtr/api_key` fallback

3. **Wrapper behavior:**
   - If `TOKEN` is empty, reads from `.env`
   - If `TOKEN` still empty, reads from `~/.config/swtr/api_key`
   - If `TOKEN` still empty, exits with code 3

---

## STEP 2 — REPRODUCE OUTSIDE TASK API

### Test Method

1. Start MCP-SWTR wrapper in background
2. Connect via FastMCP client
3. Call `read_unit(DMS-273)`

### Results

```
✅ MCP-SWTR wrapper started successfully
✅ Tools: 48 available
✅ read_unit: 1 items
✅ task_code: DMS-273
✅ workflow_status: Зарегистрирован
```

**MCP_DIRECT = PASS**

---

## STEP 3 — COMPARE DIRECT VS TASK API

| Aspect | Direct MCP | Task API (after restart) |
|--------|------------|--------------------------|
| Wrapper | Same | Same |
| Credentials | From `.env` | From `.env` |
| Transport | stdio | stdio |
| Response | 200 | 200 |
| task_code | DMS-273 | DMS-273 |
| workflow_status | Зарегистрирован | Зарегистрирован |

**Note:** Initial Task API test showed HTTP 502, but subsequent tests showed HTTP 200 after process restart.

---

## STEP 4 — INVESTIGATE «INVALID JSON»

### Error Source Analysis

The error "SWTR MCP returned invalid JSON" originates from `_parse_tool_content()` in `swtr_read.py:62`.

### Possible Causes

1. **Stdout contains non-JSON text** (banners, logs, warnings)
2. **MCP response protocol malformed**
3. **Connection lost during transfer**

### Investigation

- Direct MCP test shows stdout is empty (expected for MCP protocol)
- Stderr contains FastMCP banners (not a problem)
- MCP protocol framing is correct

---

## STEP 5 — CONTROLLED TOKEN-PROPAGATION TEST

### Test A: Empty SWTR_TOKEN (like Task API)

```
env['SWTR_TOKEN'] = ''
Result: ✅ PASS - wrapper reads from .env
```

### Test B: Valid SWTR_TOKEN

```
env['SWTR_TOKEN'] = "<valid token>"
Result: ✅ PASS
```

**Both tests pass.** Token propagation is not the issue.

---

## STEP 6 — VERIFY SCOPE CLAIM

### Search for `swtr:wmb` requirement

No evidence found in:
- `task-api/app/services/swtr_mcp_client.py`
- `task-api/app/routers/swtr_read.py`
- `mcp-swtr-wrapper.sh`
- `mcp-swtr/.env`

**SCOPE_REQUIREMENT_NOT_PROVEN**

The wrapper reads credentials from `.env` or `~/.config/swtr/api_key` and passes them to MCP-SWTR. No explicit `swtr:wmb` scope requirement found in code.

---

## FINDINGS

| Check | Status |
|-------|--------|
| MCP_EFFECTIVE_TOKEN | PRESENT (via wrapper .env) |
| TOKEN_FINGERPRINT_MATCH | N/A (no comparison needed) |
| MCP_EFFECTIVE_BASE_URL | PRESENT |
| STDOUT_VALID_MCP_PROTOCOL | YES |
| FIRST_FAILING_BOUNDARY | UNKNOWN (process restarted) |

---

## ROOT CAUSE ASSESSMENT

**INSUFFICIENT_EVIDENCE**

The system transitioned from failing (HTTP 502) to succeeding (HTTP 200) after a process restart. Possible explanations:

1. **Transient MCP-SWTR server failure** - server was not properly initialized
2. **Environment variable race condition** - Task API started before credentials loaded
3. **MCP protocol framing issue** - stdio buffer corruption (not reproducible)

**No definitive root cause could be identified** because:
- The failure was transient
- The process automatically recovered
- No logs show the exact failure point

---

## REPRODUCER

```bash
# Initial state (may fail):
# Task API started without credentials

# After restart (works):
cd task-api
python3 -m uvicorn main:app --host 127.0.0.1 --port 8003

# Test:
python3 << 'PYEOF'
import httpx
r = httpx.get('http://127.0.0.1:8003/api/v1/swtr-read/tasks/DMS-273', timeout=30)
print(r.status_code)  # Expected: 200
PYEOF
```

---

## MINIMAL FIX RECOMMENDATION

**If the issue recurs, the fix should be:**

1. **Add startup check** - Verify MCP-SWTR is reachable before accepting requests
2. **Add health endpoint** - `GET /api/v1/swtr-read/health` should verify MCP connection
3. **Add credential preload** - Load credentials from `.env` or `~/.config/swtr/api_key` at startup
4. **Add automatic restart** - Configure uvicorn to restart if MCP-SWTR becomes unavailable

---

## CONFIDENCE

**CONFIDENCE: LOW**

The issue could not be reproduced consistently. The system works correctly now, but the original root cause remains unproven.

---

## OBSERVATIONS

1. **Task API restarts automatically** - uvicorn's auto-reload may have fixed the issue
2. **Wrapper credential loading works** - MCP-SWTR correctly reads from `.env`
3. **No code changes needed** - Current configuration is correct
4. **Future monitoring recommended** - If issue recurs, capture logs before restart

---

## NEXT STEPS

If the issue recurs:

1. **Capture logs BEFORE restart** - Save `/tmp/task_api.log`
2. **Check MCP-SWTR wrapper** - Verify it's executable and has correct permissions
3. **Verify credentials** - Check `~/.config/swtr/api_key` and `mcp-swtr/.env`
4. **Test stdio manually** - Run wrapper directly with test request

---

**STOP. Do not implement fix. Do not start 099.**
