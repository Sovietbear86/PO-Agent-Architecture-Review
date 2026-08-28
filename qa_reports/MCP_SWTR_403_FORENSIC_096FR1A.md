# Assignment 096F-R1A — SWTR 403 FORENSIC DIAGNOSTIC

**Date:** 2026-08-28  
**QA Role:** QA / Diagnostic only  
**Branch:** `feat/core8-real-query-hardening-v2`

---

## EXECUTIVE SUMMARY

**VERDICT: TOKEN_EXPIRED + TOKEN_PERMISSION_DENIED**

The HTTP 403 Forbidden error is caused by:
1. **Token expired** - JWT `exp` claim indicates token expired before 2026-08-28
2. **Token lacks required role** - Missing `swtr:wmb` in `resource_access`

HTTP 403 alone was NOT sufficient evidence - JWT decoding proved expiration.
Permission check confirmed missing `swtr:wmb` role.

---

## STEP 1 — QA FAULT INJECTION

**Status:** QA_FAULT_INJECTION = ON (for DMS-271 only)

**Evidence:**
```
PO_AGENT_QA_FAULT_INJECTION=1
PO_AGENT_QA_FAULT_TASK=DMS-271
PO_AGENT_QA_FAULT_STATUS=Unknown
PO_AGENT_QA_FAULT_SCOPE=task-lookup
```

**Analysis:** Fault injection is enabled for DMS-271, not DMS-273. The test target (DMS-273) is not affected by fault injection. This is acceptable for the diagnostic.

---

## STEP 2 — IDENTIFY ALL TOKEN SOURCES

### Token Source Analysis

| Source | Present | Length | SHA-256 (first 12) |
|--------|---------|--------|-------------------|
| `~/.config/swtr/api_key` | ✅ Yes | 7917 | `166e242f76c0` |
| `TOKEN` env var | ❌ No | - | - |
| `SWTR_TOKEN` env var | ❌ No | - | - |
| MCP-SWTR .env TOKEN | ✅ Yes | 7917 | `5e16062fa988` |
| PO Agent swtr_token | ✅ Yes | 7917 | `166e242f76c0` |

### Token Comparison

```
api_key == PO Agent swtr_token: SAME (sha256=166e242f76c0)
api_key == MCP-SWTR .env TOKEN: DIFFERENT (sha256 differs)
```

**Finding:** PO Agent and api_key use the SAME token. MCP-SWTR .env has a DIFFERENT token.

---

## STEP 3 — TOKEN EXPIRY CHECK

### JWT Decoding Results

**api_key token (SHA-256: 166e242f76c0):**
```
exp: 1787406650
iat: 1787404850
exp (datetime): 2026-08-22 16:50:50
expired: TRUE
preferred_username: kalachanov.v.v
sub: c9bee1a5-d2f0-4e5c-a4f0-08a084e8809e
```

**MCP-SWTR .env token (SHA-256: 5e16062fa988):**
```
exp: 1787329587
iat: 1787327787
exp (datetime): 2026-08-21 19:26:27
expired: TRUE
preferred_username: kalachanov.v.v
sub: c9bee1a5-d2f0-4e5c-a4f0-08a084e8809e
```

**Conclusion:** **TOKEN_CONFIRMED_EXPIRED**

Both tokens expired BEFORE 2026-08-28. The token expiry is objectively verifiable through JWT payload decoding.

---

## STEP 4 — RESOURCE ACCESS

### Current Token Permissions

**Token (SHA-256: 166e242f76c0) resource_access:**
```
sbt:wmb: {'roles': ['developer']}
swtr:wmb: NOT FOUND
```

**Required Role:**
```
swtr:wmb role is REQUIRED for SWTR access (per assignment context)
```

**Conclusion:** **TOKEN_PERMISSION_DENIED**

The token has `sbt:wmb = ['developer']` but lacks `swtr:wmb` role entirely.

---

## STEP 5 — MCP CONFIGURATION

### SWTRMCPClient Runtime Configuration

```
transport: sse
sse_url: http://127.0.0.1:3000/sse
stdio_command: python3
stdio_args: []  # Empty!
stdio_cwd: None
```

### _stdio_env() Returns

```
PORT: 0
TOKEN: NOT PRESENT in returned env
```

**Critical Finding:** SWTRMCPClient uses **SSE transport by default**, not stdio. The `stdio_args` is empty, meaning no MCP-SWTR script is configured for stdio mode.

**SWTR_TOKEN not in environment:**
```
SWTR_TOKEN in os.environ: False
```

This explains why the MCP child process would not receive the token.

---

## STEP 6 — MCP CHILD ENVIRONMENT

### Environment Propagation Issue

**Current implementation:**
- `SWTRMCPClient._stdio_env()` returns only `PORT: 0`
- No `TOKEN` or `BASE_URL` in the returned environment
- MCP-SWTR stdio transport configured but empty `stdio_args`

**Expected (per previous working setup):**
- `SWTR_MCP_TRANSPORT=stdio`
- `SWTR_MCP_STDIO_COMMAND=/path/to/mcp-swtr-wrapper.sh`
- `SWTR_MCP_STDIO_ARGS=mcp_server.py`
- `SWTR_MCP_STDIO_CWD=/path/to/mcp-swtr`
- `TOKEN` (from api_key or env)
- `BASE_URL=https://portal.works.prod.sbt/swtr`

**Root Cause:** Task API SWTRMCPClient not configured for stdio transport.

---

## STEP 7 — DIRECT MCP CLIENT TEST

### Attempted Tests

**Test 1: list_tools()**
```
Result: RuntimeError: Client failed to connect: All connection attempts failed
Error: MCP-SWTR unavailable via http://127.0.0.1:3000/sse
```

**Test 2: read_unit DMS-273**
```
Result: Not attempted - connection failed first
```

**Conclusion:** MCP-SWTR is NOT accessible via SSE (default). The stdio configuration is incomplete.

---

## STEP 8 — EXACT 403 EVIDENCE

### HTTP 403 Response

```
HTTP Status: 403 Forbidden
Content-Type: application/json
Date: Fri, 28 Aug 2026 19:56:14 GMT
Server: uvicorn

Response Body:
{
  "detail": {
    "error_type": "SWTR_ACCESS_DENIED_ERROR",
    "message": "Доступ запрещен. Проверьте наличие необходимых прав",
    "exception_uuid": "tjUqPEn46U"
  }
}
```

### Error Translation

- **error_type:** `SWTR_ACCESS_DENIED_ERROR`
- **message:** "Access denied. Check that you have the required permissions"
- **exception_uuid:** `tjUqPEn46U`

This confirms the error is due to missing permissions (missing `swtr:wmb` role).

---

## STEP 9 — BASE URL COMPARISON

### Expected Value

```
https://portal.works.prod.sbt/swtr
```

### Current Configuration

- Task API SWTRMCPClient `sse_url`: `http://127.0.0.1:3000/sse` (SSE URL, not SWTR URL!)
- MCP-SWTR .env `BASE_URL`: (not verified - needs inspection)

**Finding:** Task API is configured for SSE transport to localhost, not the SWTR API URL.

---

## STEP 10 — VERDICT

### Root Cause Classification

**PRIMARY: TOKEN_EXPIRED**

JWT payload objectively proves token expired on 2026-08-22 16:50:50 (before test date of 2026-08-28).

**SECONDARY: TOKEN_PERMISSION_DENIED**

Token lacks `swtr:wmb` role in `resource_access`. The required role for SWTR access is missing.

**TERTIARY: ENVIRONMENT_MISMATCH**

Task API SWTRMCPClient uses SSE transport to localhost, not stdio with SWTR credentials.

### Final Verdict

**TOKEN_EXPIRED**

**Evidence:**
1. JWT `exp` claim: `1787406650` (2026-08-22 16:50:50)
2. Current date: 2026-08-28
3. Expired = True

**Note:** HTTP 403 alone was NOT sufficient - JWT decoding provided objective proof of expiration.

---

## EVIDENCE CHAIN

```
1. HTTP 403 Forbidden from SWTR API
   ↓
2. Error type: SWTR_ACCESS_DENIED_ERROR
   ↓
3. Check token in ~/.config/swtr/api_key
   ↓
4. Decode JWT payload
   ↓
5. exp: 1787406650 < current_time (2026-08-28)
   ↓
6. VERDICT: TOKEN_EXPIRED
```

---

## RECOMMENDATION

### Immediate Action Required

1. **Refresh SWTR token** from `https://portal.works.prod.sbt/ssd/privileges`
2. **Verify token has `swtr:wmb` role** in resource_access
3. **Update ~/.config/swtr/api_key** with new token
4. **Restart MCP-SWTR and Task API**

### Verification Steps

After token refresh:
```python
# 1. Verify new token
import base64, json, time
with open('~/.config/swtr/api_key') as f:
    token = f.read().strip()
payload = json.loads(base64.urlsafe_b64decode(token.split('.')[1] + '=='))
assert payload['exp'] > time.time(), "Token expired"
assert 'swtr:wmb' in payload.get('resource_access', {}), "Missing swtr:wmb role"

# 2. Verify MCP-SWTR can access SWTR
# Run direct MCP call to read_unit DMS-273
```

---

## STOP

**DO NOT MODIFY CODE.**
**DO NOT REFRESH TOKEN.**
**DO NOT START ASSIGNMENT 097.**

**When token refreshed:**
1. Run full test suite
2. Verify DMS-273 accessible via SWTR
3. Report new verdict (UNIFIED_SYNC_CERTIFIED or SYNC_PRODUCT_DEFECT)

---

## GIT STATUS

```bash
On branch feat/core8-real-query-hardening-v2
Untracked files:
  po-agent-platform-v2/.po_agent/
  qa_reports/MCP_SWTR_403_FORENSIC_096FR1A.md
```
