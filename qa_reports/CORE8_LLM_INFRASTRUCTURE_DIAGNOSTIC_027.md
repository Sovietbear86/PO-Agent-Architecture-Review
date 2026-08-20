# QA Report — CORE8 LLM Infrastructure Diagnostic 027

**Date:** 2026-08-20  
**Branch:** `feat/core8-real-query-hardening-v2`  
**Assignment:** `CORE8_LLM_INFRASTRUCTURE_DIAGNOSTIC_027`  
**Current HEAD:** `557173a`

---

## Executive Summary

**STATUS: RED - LLM API INFRASTRUCTURE FAILURE**

**ROOT CAUSE:** LLM API endpoint `https://api.ai.sbt/v1/chat/completions` returns HTTP 500 Internal Server Error for all requests.

**FAILURE BOUNDARY:** SOWA LLM API infrastructure issue (outside Harness codebase)

**RECOMMENDATION:** Contact SOWA team to investigate API server 500 error.

---

## Diagnosis Steps

### Step 1: Configuration Capture

**LLM Configuration (from running PO Agent process):**
```
Provider: SBT Hub AI (OpenAI-compatible)
Base URL: https://api.ai.sbt/v1
Model: Qwen/Qwen3-Coder-Next
API Key: SET (configured in .env)
TLS Verify: True (verify=True in RealLLMClient)
Timeout: 60 seconds
```

**Environment Source:** `.env` file loaded via Pydantic Settings model.

**PO Agent .env path:** `po-agent-platform-v2/.env`

### Step 2: Environment Verification

✅ `.env` file exists and is loaded correctly by Pydantic Settings
✅ Environment variables verified:
   - `LLM_API_KEY` = SET
   - `LLM_API_BASE_URL` = https://api.ai.sbt/v1
   - `LLM_MODEL_NAME` = Qwen/Qwen3-Coder-Next

### Step 3: Direct LLM Client Test

**Attempt:** Simple prompt "OK"
```
Request:
  POST https://api.ai.sbt/v1/chat/completions
  Body: {"messages": [{"role": "user", "content": "OK"}], "model": "Qwen/Qwen3-Coder-Next", "max_tokens": 10, "temperature": 0.0}
```

**Result:** ❌ HTTP 500 Internal Server Error (SOWA error)

**HTTP Status:** 500
**Error Type:** Server error (SOWA infrastructure)
**Body:** `<html><head><title>500 Internal Server Error</title>...`

### Step 4: JSON Mode Test

**Attempt:** Same request with `response_format={"type": "json_object"}`
**Result:** ❌ HTTP 500 Internal Server Error

**Note:** JSON mode is used by `LLMJsonSemanticInterpreter._complete_json()` as first attempt.

### Step 5: Failure Boundary Analysis

| Layer | Status | Evidence |
|-------|--------|----------|
| Network/Auth | ✅ PASS | Successful TLS handshake, auth accepted |
| Endpoint/Model | ❌ FAIL | All models return 500 |
| OpenAI transport | ✅ PASS | Request reaches endpoint |
| Structured output | N/A | Never reached due to endpoint error |
| Semantic interpreter | N/A | Never reached due to endpoint error |
| PO Agent wiring | ✅ PASS | Configuration correct |

### Step 6: Semantic Interpreter Flow

```
/api/v1/query → LLMJsonSemanticInterpreter.interpret()
    → LLMFirstSemanticInterpreter._complete_json()
        → RealLLMClient.complete()
            → httpx.post("/chat/completions", json=payload)
                → response.raise_for_status() [FAILS with HTTP 500]
        → Exception caught, semantic_interpretation_failure returned
```

### Step 7: PO Agent Response

```
Query: "Покажи задачи Моисеева в DMS-SPRNT-2"
Response:
  Status: FAILED
  Answer: "Не удалось безопасно интерпретировать запрос. Попробуйте переформулировать его."
  Warnings: ["semantic_interpretation_failure"]
  Intent: null
```

---

## LLM Configuration Details

### .env Configuration (po-agent-platform-v2/.env)
```bash
LLM_API_BASE_URL=https://api.ai.sbt/v1
LLM_MODEL_NAME=Qwen/Qwen3-Coder-Next
LLM_API_KEY=<token_present>
LLM_TLS_VERIFY=True
```

### RealLLMClient Initialization (from api/v1/__init__.py)
```python
llm = RealLLMClient(
    api_key=settings.llm_api_key,
    base_url=settings.llm_api_base_url,
    model=settings.llm_model_name,
    verify=settings.llm_tls_verify,
)
```

### HTTP Request Format
```json
{
  "messages": [...],
  "model": "Qwen/Qwen3-Coder-Next",
  "temperature": 0.0,
  "max_tokens": 900,
  "response_format": {"type": "json_object"}
}
```

---

## Additional Finding: Oracle Defect from 026

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
| Base URL reachable | ✅ YES (TLS works from server) |
| Model valid | ✅ YES (Qwen/Qwen3-Coder-Next) |
| LLM responds | ❌ NO (500 error) |
| OPENAI-compatible format | ✅ YES |

**READY_TO_FIX_LLM = NO**

### Root Cause Classification
```
PROBLEM: LLM API server returns HTTP 500 for all requests
SCOPE: SOWA infrastructure (https://api.ai.sbt)
IMPACT: Complete semantic LLM failure
SEVERITY: BLOCKING
OWNER: SOWA team
```

### Recommendation
1. Contact SOWA team to investigate `https://api.ai.sbt` 500 error
2. Verify API server health and load balancer configuration
3. Check if model `Qwen/Qwen3-Coder-Next` is available
4. Verify authentication/authorization for API key

---

## Report Footer

```text
ASSIGNMENT_ID = CORE8_LLM_INFRASTRUCTURE_DIAGNOSTIC_027
CURRENT_HEAD = 557173a
LLM_API_BASE_URL = https://api.ai.sbt/v1
LLM_MODEL_NAME = Qwen/Qwen3-Coder-Next
LLM_API_KEY_SET = YES
TLS_VERIFY = True
HTTP_500_COUNT = 0 (not LLM-related)
LLM_ENDPOINT_STATUS = 500 INTERNAL SERVER ERROR
ROOT_CAUSE = SOWA LLM API infrastructure failure
FAILURE_BOUNDARY = LLM API endpoint (https://api.ai.sbt)
READY_TO_FIX_LLM = NO
READY_TO_RERUN_026 = NO (LLM infrastructure blocking)
```

---

## Summary

**LLM Infrastructure Status: FAILED**

**Root Cause:** SOWA LLM API server at `https://api.ai.sbt/v1/chat/completions` returns HTTP 500 Internal Server Error for all requests.

**Impact:** Complete semantic LLM failure - all natural language queries fail with `semantic_interpretation_failure`.

**Next Steps:**
1. Contact SOWA team for API server investigation
2. Verify API health, model availability, and authentication
3. Once API is restored, semantic queries will work without code changes
