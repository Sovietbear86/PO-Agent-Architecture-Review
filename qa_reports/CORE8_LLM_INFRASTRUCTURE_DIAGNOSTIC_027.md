# QA Report — CORE8 LLM Infrastructure Diagnostic 027

**Date:** 2026-08-20  
**Branch:** `feat/core8-real-query-hardening-v2`  
**Assignment:** `CORE8_LLM_INFRASTRUCTURE_DIAGNOSTIC_027`  
**Current HEAD:** `e20be31`

---

## Executive Summary

**STATUS: RED - CONFIGURATION ERROR (NOT INFRASTRUCTURE)**

**ROOT CAUSE:** `.env` file has `LLM_API_BASE_URL=https://api.ai.sbt/v1` but the API requires the path `/openai/v1`.

**FIRST_BAD_COMMIT:** 90ce3d5 (2026-08-13) - LLM API key configuration changes
**LAST_KNOWN_GOOD_COMMIT:** 3626202 (2026-08-13) - Qwen LLM client hardening

**FIX:** Update `.env` to use `LLM_API_BASE_URL=https://api.ai.sbt/openai/v1`

---

## Investigation Methodology

### Step 1: Find LAST_KNOWN_GOOD LLM Commit

**Search strategy:** Query test results and commit messages for successful LLM usage.

**Evidence:**
- `QWENCODER_TEST_RESULTS.md` (2026-08-13) shows "LLM Integration: PASS (4 passed)"
- Commit `6caf181` (2026-08-13 14:03:20) documents "GigaCode bootstrap using active local credentials"
- Real Qwen integration tests passed on 2026-08-13
- No LLM code changes after `3626202` (2026-08-13 12:33:06)

**LAST_KNOWN_GOOD_COMMIT:** `3626202665ce43c7fc3c0aa953a28b81df727264`
**Date:** 2026-08-13 12:33:06
**Log:** "fix: harden real Qwen LLM client configuration"

### Step 2: Compare LLM Client Code

**LLM client (real.py) is IDENTICAL between commits:**

```bash
# Hash comparison
3626202: 6e34051ff2694e62b4ef9aa46739159a
HEAD:     6e34051ff2694e62b4ef9aa46739159a
```

**No code changes in real.py since 2026-08-13!**

### Step 3: Compare Configuration

**Settings.py changes (since 3626202):**

| Setting | OLD | NEW | Status |
|---------|-----|-----|--------|
| `.env` path | `.env` (current dir) | `_PROJECT_ROOT / ".env"` (absolute) | ✅ Safe |
| `semantic_llm_enabled` | `default=True` | `default=True` | ✅ Same |
| `llm_api_base_url` | `https://api.ai.sbt/openai/v1` | `https://api.ai.sbt/openai/v1` | ✅ Same default |

**BUT** the `.env` file was modified to use:
```bash
# OLD (working):
LLM_API_BASE_URL=https://api.ai.sbt/openai/v1

# NEW (broken):
LLM_API_BASE_URL=https://api.ai.sbt/v1  # Missing /openai/v1!
```

### Step 4: Test Both Endpoints

**Test request:**
```json
{
  "messages": [{"role": "user", "content": "OK"}],
  "model": "Qwen/Qwen3-Coder-Next",
  "max_tokens": 10,
  "temperature": 0.0
}
```

| Endpoint | HTTP Status | Result |
|----------|-------------|--------|
| `https://api.ai.sbt/openai/v1/chat/completions` | **200 OK** | ✅ Working |
| `https://api.ai.sbt/v1/chat/completions` | **500** | ❌ SOWA error |

**CONCLUSION:** The `/openai/v1` path is REQUIRED by the SBT Hub AI API.

---

## Full Configuration Comparison

### LAST_KNOWN_GOOD (3626202)

| Parameter | Value |
|-----------|-------|
| **base_url** | `https://api.ai.sbt/openai/v1` |
| **endpoint** | `/chat/completions` |
| **model** | `Qwen/Qwen3-Coder-Next` |
| **Authorization** | `Bearer <api_key>` |
| **Content-Type** | `application/json` |
| **verify** | `True` |
| **timeout** | `60` |
| **request JSON** | OpenAI-compatible |
| **response_format** | `{type: "json_object"}` (conditional) |

### CURRENT (HEAD)

| Parameter | Value | Status |
|-----------|-------|--------|
| **base_url** | `https://api.ai.sbt/v1` | ❌ WRONG (missing `/openai/v1`) |
| **endpoint** | `/chat/completions` | ✅ |
| **model** | `Qwen/Qwen3-Coder-Next` | ✅ |
| **Authorization** | `Bearer <api_key>` | ✅ |
| **Content-Type** | `application/json` | ✅ |
| **verify** | `True` | ✅ |
| **timeout** | `60` | ✅ |
| **request JSON** | OpenAI-compatible | ✅ |
| **response_format** | `{type: "json_object"}` | ✅ |

---

## Diff Summary: LAST_KNOWN_GOOD → CURRENT

### LLM Client Code (`po-agent-platform-v2/src/po_agent/llm/real.py`)
```
NO CHANGES (identical SHA-256: 6e34051ff2694e62b4ef9aa46739159a)
```

### Settings (`po-agent-platform-v2/src/po_agent/config/settings.py`)
```
+ Added absolute .env path resolution
- Removed semantic_llm_enabled comment
= Same defaults
```

### Configuration (`.env`)
```
- LLM_API_BASE_URL=https://api.ai.sbt/openai/v1
+ LLM_API_BASE_URL=https://api.ai.sbt/v1
```

---

## Root Cause Delta Analysis

| Layer | LAST_KNOWN_GOOD | CURRENT | Status |
|-------|-----------------|---------|--------|
| Code: real.py | 3626202 | HEAD | ✅ Same |
| Code: settings.py | 3626202 | HEAD | ⚠️ Path only |
| Config: `.env` base_url | `.../openai/v1` | `.../v1` | ❌ BROKEN |
| API: endpoint path | `/openai/v1` | `/v1` | ❌ BROKEN |

**ROOT CAUSE:** User-modified `.env` file removed `/openai/v1` from base URL.

**NOT A CODE BUG:** The default in `settings.py` is correct. The `.env` override is wrong.

---

## Fix Recommendation

**Minimal Change (5 seconds):**
```bash
# Edit po-agent-platform-v2/.env
LLM_API_BASE_URL=https://api.ai.sbt/v1
# Change to:
LLM_API_BASE_URL=https://api.ai.sbt/openai/v1
```

**After fix:**
1. Restart PO Agent service
2. Query should succeed with HTTP 200

**Verification:**
```bash
# After fix, this should return 200:
curl -X POST https://api.ai.sbt/openai/v1/chat/completions \
  -H "Authorization: Bearer <your_key>" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"OK"}],"model":"Qwen/Qwen3-Coder-Next","max_tokens":10}'
```

---

## Oracle Defect from Assignment 026

**Issue:** Sprint listing endpoint does not contain full `assigned_to` attribute.

**Evidence:**
- `/sprints/DMS-SPRNT-1/tasks` returns tasks with incomplete attributes
- Individual task read (`/tasks/DMS-XXX`) contains full `assigned_to` with `externalId`, `login`, `display`
- Assignee cannot be determined from sprint listing alone

**Recommendation for 026 Rerun:**
1. First query sprint for task keys only
2. For assignee verification, hydrate each task via individual read
3. This ensures complete `assigned_to` data for oracle comparison

---

## Hard Acceptance Gates

### LLM Infrastructure
| Check | Status |
|-------|--------|
| API key configured | ✅ YES |
| Base URL correct | ❌ NO (missing `/openai/v1`) |
| Model valid | ✅ YES |
| LLM responds | ❌ NO (500 error - wrong path) |
| OPENAI-compatible format | ✅ YES |

### LLM Infrastructure Fix Status
| Check | Status |
|-------|--------|
| `.env` can be edited | ✅ YES |
| Service can be restarted | ✅ YES |
| Fix is minimal (1 line) | ✅ YES |
| Production code modified | ❌ NO (no code changes) |

**READY_TO_FIX_LLM = YES** (configuration-only fix)
**READY_TO_RERUN_026 = YES** (after fix)

---

## Summary

**LLM Infrastructure Status: CONFIGURATION ERROR**

**Root Cause:** `.env` file has `LLM_API_BASE_URL=https://api.ai.sbt/v1` but SBT Hub AI API requires `https://api.ai.sbt/openai/v1`.

**Impact:** All semantic LLM queries fail with HTTP 500 error.

**Fix:** Add `/openai/v1` to `LLM_API_BASE_URL` in `.env`.

**Files Changed Since Last Good State:**
- `po-agent-platform-v2/src/po_agent/llm/real.py` → NO CHANGES
- `po-agent-platform-v2/src/po_agent/config/settings.py` → PATH RESOLUTION ONLY
- `po-agent-platform-v2/.env` → REMOVED `/openai/v1` FROM BASE_URL

**Test Results:**
- `https://api.ai.sbt/openai/v1/chat/completions` → 200 OK ✅
- `https://api.ai.sbt/v1/chat/completions` → 500 ❌

---

## Report Footer

```text
ASSIGNMENT_ID = CORE8_LLM_INFRASTRUCTURE_DIAGNOSTIC_027
CURRENT_HEAD = e20be31
LAST_KNOWN_GOOD_COMMIT = 3626202 (2026-08-13 12:33:06)
FIRST_BAD_COMMIT = 90ce3d5 (2026-08-13) - LLM_API_KEY changes
ROOT_CAUSE = .env base_url missing /openai/v1 path
ROOT_CAUSE_DELTA = LLM_API_BASE_URL=https://api.ai.sbt/v1 (should be .../openai/v1)
FIX_REQUIRED = Edit .env: add /openai/v1 to LLM_API_BASE_URL
PRODUCTION_CODE_MODIFIED = NO (configuration only)
READY_TO_FIX_LLM = YES
READY_TO_RERUN_026 = YES (after .env fix)
TESTED_ENDPOINTS = 2 (1 working, 1 failing)
WORKING_ENDPOINT = https://api.ai.sbt/openai/v1/chat/completions
FAILING_ENDPOINT = https://api.ai.sbt/v1/chat/completions
```
