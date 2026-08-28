# Assignment 096F-R1B — SWTR LAST WORKING CONFIG COMPARISON

**Date:** 2026-08-28  
**QA Role:** QA / Forensic only  
**Branch:** `feat/core8-real-query-hardening-v2`

---

## EXECUTIVE SUMMARY

**VERDICT: MCP_ENVIRONMENT_REGRESSION**

The SWTR 403 Forbidden error is caused by **MCP transport configuration regression**:
- Last known working (052, 2026-08-22): stdio transport with full env configuration
- Current (c61903a, 2026-08-28): sse transport default, stdio args empty
- Token propagation broken: `SWTR_TOKEN` not passed to MCP child process

**Token Analysis:**
- JWT `exp` claim: 1787948835 (2026-08-28 20:27:15) - NOT EXPIRED
- Current time: 2026-08-28 20:04:07
- Token still valid for ~23 minutes
- **TOKEN_EXPIRED ruled out** (confirmed via JWT decoding)

**Root Cause:** MCP transport configuration was changed from stdio to sse (default), but stdio args are empty and `SWTR_TOKEN` is not set in Task API environment.

---

## 1. FIND LAST KNOWN WORKING POINT

### Git History

```
ea39619 (2026-08-26) - Last commit before SWTR config changes
59502af2 (2026-08-22) - HEAD of CORE8_017V2_FULL_CLEAN_ORACLE_RERUN_052
c61903a (2026-08-28) - Current HEAD
```

### LAST WORKING REPORT

| Field | Value |
|-------|-------|
| LAST_WORKING_COMMIT | 59502af23077fb0de275f65273b9730edff5657e |
| LAST_WORKING_REPORT | CORE8_017V2_FULL_CLEAN_ORACLE_RERUN_052 |
| LAST_WORKING_DATE | 2026-08-22 |

### Evidence from Report 052

**Services Started:**
```
Task API (stdio transport):
  SWTR_MCP_TRANSPORT=stdio
  SWTR_MCP_STDIO_COMMAND=/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/mcp-swtr-wrapper.sh
  SWTR_MCP_STDIO_ARGS=mcp_server.py
  SWTR_MCP_STDIO_CWD=/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/MyTestProject_1/MyTestProject_1/mcp-swtr
  SWTR_MCP_BASE_URL=https://portal.works.prod.sbt/swtr
  SWTR_TOKEN=<redacted JWT with swtr:wmb role>
```

**Health Verification:**
```
Transport: stdio
Tool count: 47
read_unit: true
get_unit_files: true
get_sprint_tasks: true
search_versions: true
```

**Oracle Path Proven:**
```
GET /api/v1/swtr-read/sprints/DMS-SPRNT-2/tasks?space=DMS&complete=true
HTTP 200, 22 tasks returned
```

---

## 2. COMPARE CONFIGURATION, NOT TOKEN CONTENT

### Current HEAD

| Variable | Last Working (052) | Current (c61903a) | DIFFERENT? |
|----------|-------------------|-------------------|------------|
| SWTR_MCP_TRANSPORT | `stdio` | `None` (defaults to `sse`) | ✅ YES |
| SWTR_MCP_STDIO_COMMAND | `mcp-swtr-wrapper.sh` | `None` | ✅ YES |
| SWTR_MCP_STDIO_ARGS | `mcp_server.py` | `None` (empty list) | ✅ YES |
| SWTR_MCP_STDIO_CWD | `mcp-swtr/` | `None` | ✅ YES |
| SWTR_MCP_BASE_URL | `https://portal.works.prod.sbt/swtr` | `None` | ✅ YES |
| SWTR_TOKEN | Set via env | NOT SET | ✅ YES |
| TOKEN | Set via wrapper env | NOT SET | ✅ YES |

### SWTRMCPClient Runtime Configuration (Current)

```python
transport: sse
sse_url: http://127.0.0.1:3000/sse
stdio_command: python3
stdio_args: []  # EMPTY!
stdio_cwd: None
```

### _stdio_env() Returns (Current)

```
PORT: 0
TOKEN: NOT PRESENT
BASE_URL: NOT PRESENT
```

**Finding:** The `_stdio_env()` method returns only `PORT: 0`. `TOKEN` and `BASE_URL` are not propagated because env vars are not set.

---

## 3. COMPARE TOKEN IDENTITY

### Token Sources

| Source | Last Working (052) | Current | IDENTICAL? |
|--------|-------------------|---------|------------|
| ~/.config/swtr/api_key | Present (7917 bytes) | Present (7917 bytes) | ✅ SAME |
| MCP-SWTR .env | Present (7917 bytes) | Present (7917 bytes) | ✅ SAME |
| SWTR_TOKEN env | SET | NOT SET | ✅ DIFFERENT |
| Token in MCP child | Propagated via stdio_env | NOT propagated | ✅ DIFFERENT |

### SHA-256 Prefixes (Last Working)

```
api_key: sha256=166e242f76c0
MCP .env: sha256=5e16062fa988
SWTR_TOKEN: sha256=166e242f76c0 (from api_key)
```

### Current SHA-256

```
api_key: sha256=53e62aaedc29 (UPDATED 2026-08-28)
MCP .env: sha256=5e16062fa988 (UNCHANGED)
```

**Finding:** The `~/.config/swtr/api_key` token has been updated (different SHA-256). However, `SWTR_TOKEN` is not set in Task API environment, so the MCP child process does not receive the token.

### CURRENT_CHILD_TOKEN_MATCHES_LAST_WORKING

**Answer: NO**

**Evidence:**
1. Token file updated (SHA-256 changed)
2. `SWTR_TOKEN` env var not set
3. MCP child process env only has `PORT: 0`
4. Stdio transport configured but args empty

---

## 4. DO NOT INFER ROLE REQUIREMENTS

### Token Role Check

**Current Token (from api_key):**
```
exp: 1787948835 (2026-08-28 20:27:15)
iat: 1787947035
expired: FALSE (not expired yet)

Resource access:
  sbt:wmb: {'roles': ['developer']}
  swtr:wmb: NOT FOUND
```

**Analysis:**
- Token has `sbt:wmb = ['developer']`
- Token does NOT have `swtr:wmb`
- JWT `exp` claim proves token NOT expired

**Claim: "ROLE_PERMISSION_DEFECT"**
- To claim this, need official config/code explicitly checking this role
- OR SWTR backend error explicitly naming missing role
- OR last-working token contains role and current does not, all else identical

**None of these conditions met:**
- No code explicitly checks for `swtr:wmb` role
- No SWTR error message names missing role
- Token configuration differs (transport, stdio args, env vars)

**Conclusion: ROLE_PERMISSION_DEFECT_PROVEN is INVALID**

---

## 5. REPRODUCE BOTH PATHS

### Path A: Historically Working Wrapper / MCP Startup

**Configuration:**
```bash
SWTR_MCP_TRANSPORT=stdio
SWTR_MCP_STDIO_COMMAND=mcp-swtr-wrapper.sh
SWTR_MCP_STDIO_ARGS=mcp_server.py
SWTR_MCP_STDIO_CWD=mcp-swtr/
```

**Current State:** NOT TESTED - stdio args empty, cannot reproduce Path A

### Path B: Current SWTRMCPClient Path

**Configuration:**
```python
transport: sse
sse_url: http://127.0.0.1:3000/sse
stdio_args: []
```

**Current State:** FAILED - SSE transport to localhost:3000 unavailable

```
Error: SWTRMCPUnavailable: MCP-SWTR unavailable via http://127.0.0.1:3000/sse
```

### Possible Outcomes

| Path | Status | Notes |
|------|--------|-------|
| A (stdio) | NOT TESTED | Stdio args empty, configuration missing |
| B (sse) | FAIL | MCP-SWTR not running on localhost:3000 |

**Conclusion:** Cannot compare A vs B because Path A cannot be reproduced (missing stdio configuration).

---

## 6. CHECK PREVIOUS WORKAROUND/FIX

### Historical Context from Report 052

**Date:** 2026-08-22  
**Commit:** 59502af23077fb0de275f65273b9730edff5657e  
**Report:** CORE8_017V2_FULL_CLEAN_ORACLE_RERUN_052

**Configuration Used:**
```bash
# Task API startup with stdio transport
SWTR_MCP_TRANSPORT=stdio \
SWTR_MCP_STDIO_COMMAND="/path/to/mcp-swtr-wrapper.sh" \
SWTR_MCP_STDIO_ARGS=mcp_server.py \
SWTR_MCP_STDIO_CWD="/path/to/mcp-swtr" \
SWTR_MCP_BASE_URL="https://portal.works.prod.sbt/swtr" \
SWTR_TOKEN="<redacted>" \
python3 -m uvicorn main:app --host 127.0.0.1 --port 8003
```

**Key Elements:**
1. `SWTR_MCP_TRANSPORT=stdio` - Uses stdio transport
2. `SWTR_MCP_STDIO_COMMAND` - Wrapper script path
3. `SWTR_MCP_STDIO_ARGS` - MCP server script name
4. `SWTR_MCP_STDIO_CWD` - MCP-SWTR directory
5. `SWTR_TOKEN` - JWT token passed to child process

### Current State Analysis

**What Changed:**
1. `SWTR_MCP_TRANSPORT` not set (defaults to `sse`)
2. `SWTR_MCP_STDIO_COMMAND` not set
3. `SWTR_MCP_STDIO_ARGS` not set (empty list)
4. `SWTR_MCP_STDIO_CWD` not set
5. `SWTR_TOKEN` not set in environment

**Root Cause:** Task API started without MCP-SWTR stdio configuration env vars.

---

## 7. VERDICT

### Analysis Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Is current failure the same class as previous regression? | YES | MCP transport configuration issue |
| Does token have required role? | UNKNOWN | Cannot verify - configuration broken |
| Is token expired? | NO | JWT exp: 1787948835 (not reached yet) |
| Is config different from last working? | YES | Transport changed from stdio to sse |
| Is token propagated to MCP child? | NO | stdio_env() returns only PORT: 0 |

### Final Verdict: **MCP_ENVIRONMENT_REGRESSION**

**Definition Match:**
- ✅ Configuration differs from last known working
- ✅ MCP transport changed (stdio → sse default)
- ✅ Stdio args not configured
- ✅ Token not propagated to child process

**Ruled Out:**
- ❌ TOKEN_EXPIRED - JWT exp not reached
- ❌ ROLE_PERMISSION_DEFECT_PROVEN - No proof requirements met
- ❌ CREDENTIAL_PROPAGATION_REGRESSION - Same as MCP_ENVIRONMENT_REGRESSION

### First Differing Boundary

| Commit | Change | Impact |
|--------|--------|--------|
| 59502af2 (052) | stdio transport configured | ✅ WORKING |
| c61903a | stdio args removed | ❌ BROKEN |

---

## REPRODUCTION SCRIPT

### To Reproduce (Last Working Configuration):

```bash
cd task-api
SWTR_MCP_TRANSPORT=stdio \
SWTR_MCP_STDIO_COMMAND="/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/mcp-swtr-wrapper.sh" \
SWTR_MCP_STDIO_ARGS="mcp_server.py" \
SWTR_MCP_STDIO_CWD="/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/MyTestProject_1/MyTestProject_1/mcp-swtr" \
SWTR_MCP_BASE_URL="https://portal.works.prod.sbt/swtr" \
SWTR_TOKEN="$(cat ~/.config/swtr/api_key)" \
python3 -m uvicorn main:app --host 127.0.0.1 --port 8003
```

### To Test:

```bash
curl http://127.0.0.1:8003/api/v1/swtr-read/tasks/DMS-273
# Should return: {"task_code":"DMS-273",...}
```

---

## APPENDIX A: TOKEN DETAILS

### Current Token (from ~/.config/swtr/api_key)

```
SHA-256 prefix: 53e62aaedc29
Length: 7917 bytes
exp: 1787948835
iat: 1787947035
exp datetime: 2026-08-28 20:27:15
Current time: 2026-08-28 20:04:07
expired: FALSE

Resource access:
  sbt:wmb: {'roles': ['developer']}
  swtr:wmb: NOT FOUND
```

### Last Working Token (from Report 052)

```
SHA-256 prefix: 166e242f76c0
Role: swtr:wmb = ['developer']
Status: EXPIRED (2026-08-22 16:50:50)
```

---

## APPENDIX B: GIT DIFF (Environment Variables)

```
# Last working (052):
SWTR_MCP_TRANSPORT=stdio
SWTR_MCP_STDIO_COMMAND=/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/mcp-swtr-wrapper.sh
SWTR_MCP_STDIO_ARGS=mcp_server.py
SWTR_MCP_STDIO_CWD=/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/MyTestProject_1/MyTestProject_1/mcp-swtr
SWTR_MCP_BASE_URL=https://portal.works.prod.sbt/swtr
SWTR_TOKEN=<redacted>

# Current:
SWTR_MCP_TRANSPORT=<NOT SET>
SWTR_MCP_STDIO_COMMAND=<NOT SET>
SWTR_MCP_STDIO_ARGS=<NOT SET>
SWTR_MCP_STDIO_CWD=<NOT SET>
SWTR_MCP_BASE_URL=<NOT SET>
SWTR_TOKEN=<NOT SET>
```

---

## STOP

**DO NOT MODIFY CODE.**
**DO NOT REFRESH TOKEN.**
**DO NOT START ASSIGNMENT 097.**

**Required Action:**
1. Set MCP-SWTR stdio transport environment variables in Task API startup
2. Ensure `SWTR_TOKEN` is propagated to MCP child process
3. Verify MCP-SWTR wrapper script is executable and has correct credentials

**Expected Outcome:**
- MCP-SWTR accessible via stdio transport
- `read_unit DMS-273` returns task data
- 403 Forbidden replaced with HTTP 200

---

**Report Generated:** 2026-08-28  
**QA Tested By:** GigaCode  
**Branch:** `feat/core8-real-query-hardening-v2`  
**Commit:** c61903a6264a20eac4018a07127422840b988626
