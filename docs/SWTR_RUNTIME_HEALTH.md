# SWTR Runtime Health Guard

**Last updated:** 2026-08-29  
**Assignment:** 098-R2  
**Status:** IMPLEMENTED

---

## OVERVIEW

This document describes the SWTR runtime health guard used to validate that the SWTR integration is functioning correctly before starting real-environment regression or Oracle testing.

---

## CRITICAL BEHAVIOR

### 1. SWTR Uses Stdio Transport

The SWTR integration uses **stdio transport** for MCP-SWTR communication. This is the default and required transport.

- DO NOT assume SSE transport is being used
- DO NOT check for SSE-specific configuration
- DO verify stdio transport via `SWTRMCPClient.transport_kind()`

### 2. Credentials Are Loaded by Wrapper

Credentials are loaded by the MCP-SWTR wrapper from its configured `.env` file:

- **Wrapper location:** `mcp-swtr-wrapper.sh`
- **Config file:** `mcp-swtr/.env`
- **Fallback:** `~/.config/swtr/api_key`

The wrapper reads credentials and passes them to MCP-SWTR.

### 3. Missing SWTR_TOKEN in Parent Environment Is NOT an Error

The Task API process does not require `SWTR_TOKEN` in its environment. The MCP-SWTR wrapper loads credentials from its own configuration.

**DO NOT classify absence of `SWTR_TOKEN` in Task API parent environment as a failure.**

### 4. swtr:wmb Scope Is NOT Required (Without Evidence)

The `swtr:wmb` scope is NOT automatically required for SWTR operations. Do not assume this scope is needed without explicit evidence from:

- Code review
- Configuration
- Documentation
- Error messages

### 5. Run Health Guard Before Real SWTR Testing

Always run the SWTR health guard before:

- Oracle testing
- Real SWTR regression
- any test using `read_unit` or other SWTR tools

---

## HEALTH GUARD CHECKS

The health guard runs the following checks in order:

1. **Runtime Freshness** - Verify Task API is running and matches expected HEAD
2. **MCP-SWTR Health** - Verify health endpoint responds
3. **MCP Stdio Transport** - Verify stdio transport works and protocol is valid
4. **Real SWTR Read** - Verify real task read via HTTP
5. **HTTP Path** - Verify HTTP path to SWTR
6. **Bounded Sync** - Verify sync endpoint (optional)
7. **PO Agent Path** - Verify PO Agent can access SWTR
8. **Status Proof** - Verify workflow_status is correct
9. **Repeatability** - Verify consistent results over multiple requests

---

## FAILURE CLASSIFICATIONS

### PASS

All checks passed. Ready for real SWTR testing.

### TASK_API_NOT_RUNNING

Task API is not reachable on port 8003.

**Recovery:**
1. Start Task API
2. Verify PID is running: `lsof -i :8003 -t`
3. Retry health guard

### STALE_OR_WRONG_RUNTIME

Task API process is running with stale/wrong code.

**Check:**
- Running HEAD does not match expected HEAD
- Task API started from wrong directory

**Recovery:**
1. Identify running PID: `lsof -i :8003 -t`
2. Check git HEAD in task API directory
3. Restart Task API if HEAD mismatch is confirmed
4. Verify process started from correct path

### MCP_SWTR_UNAVAILABLE

MCP-SWTR service is unavailable or misconfigured.

**Check:**
- Health endpoint returns non-200
- Transport is not stdio
- Tools list is empty

**Recovery:**
1. Verify MCP-SWTR wrapper exists: `ls mcp-swtr-wrapper.sh`
2. Verify wrapper has execute permission
3. Check MCP-SWTR `.env` has valid credentials
4. Restart MCP-SWTR if needed

### MCP_PROTOCOL_INVALID

MCP stdio response is not valid JSON or protocol is corrupted.

**Check:**
- Stdout contains non-MCP text
- Response is not parseable JSON
- Task code in response does not match request

**Recovery:**
1. Check wrapper stderr for errors
2. Verify MCP-SWTR server is running correctly
3. Check for log output in stdout
4. Restart MCP-SWTR

### SWTR_READ_FAILED

Real SWTR read failed unexpectedly.

**Check:**
- Task read returns non-200
- Workflow status is missing or incorrect
- Response structure is invalid

**Recovery:**
1. Verify SWTR token has correct scope
2. Check network connectivity
3. Verify task code exists in SWTR
4. Check SWTR service status

### MCP_STDIO_FAILED

MCP stdio transport failed (wrapper or protocol).

**Check:**
- Wrapper process failed to start
- Stdio transport configuration is incorrect
- Connection lost during transfer

**Recovery:**
1. Verify wrapper path is correct
2. Check wrapper has execute permission
3. Verify MCP-SWTR `.env` has valid credentials
4. Restart MCP-SWTR

### SWTR_HTTP_PATH_FAILED

HTTP path to SWTR failed.

**Check:**
- GET `/api/v1/swtr-read/tasks/{code}` returns non-200

**Recovery:**
1. Run full health guard
2. Check MCP-SWTR health
3. Verify Task API logs

### SWTR_SYNC_FAILED

Bounded sync endpoint failed.

**Check:**
- POST `/api/v1/swtr/sync` returns non-200

**Note:** This check may be skipped if sync is not required for the test.

### PO_AGENT_SWTR_PATH_FAILED

PO Agent SWTR path failed.

**Check:**
- PO Agent cannot access SWTR via Task API

**Recovery:**
1. Run full health guard
2. Verify all previous checks passed
3. Check PO Agent configuration

---

## RECOVERY PROCEDURE

If 403/502 occurs:

1. **Run health guard**
   ```bash
   python3 task-api/tests/test_swtr_health_guard.py
   ```

2. **Verify runtime freshness**
   - Check running PID: `lsof -i :8003 -t`
   - Check git HEAD: `cd task-api && git rev-parse HEAD`
   - Compare to expected HEAD

3. **Verify direct MCP canary**
   - Run health guard's MCP stdio transport check
   - Verify DMS-273 canary returns correct status

4. **Compare Task API path**
   - Check task-api startup command
   - Verify working directory
   - Verify environment variables

5. **Restart only if stale runtime is proven/suspected**
   ```bash
   # Kill and restart Task API
   lsof -i :8003 -t | xargs kill
   cd task-api
   python3 -m uvicorn main:app --host 127.0.0.1 --port 8003
   ```

6. **Rerun canary**
   ```bash
   python3 task-api/tests/test_swtr_health_guard.py
   ```

7. **Verify recovery**
   - All checks should pass
   - DMS-273 canary should return HTTP 200

---

## CREDENTIALS AND SECRETS

### Never Print or Commit Credentials

The health guard NEVER:

- Prints token values
- Logs token fingerprints (except for debugging)
- Exposes credentials in error messages
- Writes credentials to logs

### Credential Sources

The wrapper loads credentials from:

1. `mcp-swtr/.env` (primary)
2. `~/.config/swtr/api_key` (fallback)

The wrapper script reads `TOKEN`, `BASE_URL`, and `PORT` from its environment and exports them to MCP-SWTR.

---

## TESTING

### Before Running Assignments

1. Run health guard:
   ```bash
   python3 task-api/tests/test_swtr_health_guard.py
   ```

2. Verify PASS:
   ```
   SWTR_HEALTH: SWTR_HEALTHY
   ```

3. If FAIL, follow recovery procedure above

### After Fixing Issues

1. Re-run health guard
2. Verify all checks pass
3. Run DMS-273 canary:
   ```bash
   curl http://127.0.0.1:8003/api/v1/swtr-read/tasks/DMS-273
   ```

4. Verify HTTP 200 with correct data

---

## REFERENCE

- **Assignment 098-R1:** Root cause analysis of HTTP 502
- **Assignment 098-R2:** Runtime health hardening
- **SWTR Health Guard:** `task-api/tests/test_swtr_health_guard.py`

---

## CONTACT

For questions or issues, refer to:
- `GIGACODE.md` in repository root
- `qa_assignments/` for active assignments
- `qa_reports/` for past reports
