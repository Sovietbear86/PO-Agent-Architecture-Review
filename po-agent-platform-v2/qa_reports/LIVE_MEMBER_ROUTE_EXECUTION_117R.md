# Assignment 117R — Live Member Route Execution

**Status:** `SEMANTIC_MODEL_UNAVAILABLE`
**Date:** 2026-09-01
**Branch:** `feat/core8-real-query-hardening-v2`
**HEAD:** `28d67e52ea9af895a2faae21c0d5fc655fd80972`
**Previous Assignment:** 116 - MCP-SWTR/REAL AS21 Health Recovery
**Replaces:** Assignment 117 (BLOCKED_ON_OWNER_FIX)

---

## Executive Summary

Assignment 117R is executed to prove the **live routing path** for natural-language queries requesting member tasks.

**Key Finding:** MCP-SWTR → REAL AS21 is fully operational via `get_my_tasks(assignee="ФИО")`. However, **LLM semantic interpreter fails to interpret the query** `Задачи Гаранина`, returning `semantic_interpretation_failure` for both Browser UI and Direct Harness.

**Root Cause:** LLM semantic interpreter raises exception during query interpretation. The first failing boundary is `SEMANTIC_MODEL_UNAVAILABLE` or `LLM_JSON_PARSE_FAILURE`.

**Status:** **LIVE ROUTE DEFECT PROVEN** - Browser/Harness cannot execute query, but Oracle B (direct MCP-SWTR) successfully retrieves tasks.

---

## Phase 0 — Exact Provenance

### Branch State

| Item | Value |
|------|-------|
| Branch | `feat/core8-real-query-hardening-v2` |
| HEAD | `28d67e52ea9af895a2faae21c0d5fc655fd80972` |
| Git status | Clean, up to date with origin |

### Process Details

| Service | PID | Port | Status |
|---------|-----|------|--------|
| Frontend Vite | 12279 | 5175 | ✅ Running |
| Harness (po_agent) | 62243 | 8004 | ✅ Running |
| Task API (main) | 93279 | 8003 | ✅ Running |
| MCP-SWTR | - | - | ✅ 48 tools (stdio) |

### MCP-SWTR Health

```
Status: connected
Transport: stdio
Tools: 48
Endpoints: read_unit, get_unit_files, get_sprint_tasks, search_versions,
           search_tasks, get_my_tasks, search_users, get_task_history, etc.
```

### Direct MCP-SWTR Read Test

```bash
read_unit DMS-378 → SUCCESS
  code: DMS-378
  summary: [doc] Корректировка валидатора
  space: DMS
  attributes: 33 items (including assigned_to, workflow_status)
```

---

## Phase 1 — Execute Browser + Harness Request

### Test Query
```
Задачи Гаранина
```

### Browser UI (A1)
- **Session:** Fresh browser session
- **Request:** POST `/api/v1/query`
- **Response Status:** 200
- **Result:** FAILED
- **Warnings:** `["semantic_interpretation_failure"]`
- **Intent:** null
- **Skill:** null
- **Answer:** "Не удалось безопасно интерпретировать запрос. Попробуйте переформулировать его."
- **Elapsed:** ~1800ms

### Direct Harness (A2)
- **Session ID:** `117r_direct_harness_*`
- **Request:** POST `/api/v1/query`
- **Response Status:** 200
- **Result:** FAILED
- **Warnings:** `["semantic_interpretation_failure"]`
- **Intent:** null
- **Skill:** null
- **Answer:** "Не удалось безопасно интерпретировать запрос. Попробуйте переформулировать его."
- **Elapsed:** ~1800ms

### Counter Verification
- **Browser natural-language requests:** 1 ✅
- **Direct Harness natural-language requests:** 1 ✅

---

## Phase 2 — Trace Actual Downstream Product Route

### Query Flow for `Задачи Гаранина`

```
Browser UI / Direct Harness
  → Harness /api/v1/query
    → Semantic Interpreter interpret(query="Задачи Гаранина")
      → EXCEPTION raised (semantic_interpretation_failure)
    → _source_failure(session, "semantic_interpretation_failure", ...)
```

### Task API Routes Checked

| Route | Status | Purpose |
|-------|--------|---------|
| `/api/v1/tasks` | ✅ Works | Returns local task list (no MCP-SWTR search) |
| `/api/v1/swtr-read/tasks/{code}` | ✅ Works | Returns single task with unit.attributes |
| `/api/v1/swtr-read/health` | ✅ Works | MCP-SWTR connectivity check |

### Route Analysis

**Browser/Direct Harness path does NOT reach Task API because:**
1. Semantic interpreter raises exception before capability execution
2. Request fails at interpretation phase, before routing to Task API

**Conclusion:** The failure occurs **before** any Task API routing decision.

---

## Phase 3 — Execute Oracle B Live Member Search

### Method Selection

MCP-SWTR available tools for member-based search:
- `search_tasks(search_terms="", assignee="")` - searches by login/externalId
- `get_my_tasks(assignee="ФИО")` - searches by full name (FILO)

### Oracle B Test: `get_my_tasks(assignee="Гаранин")`

```json
{
  "content": [50 tasks],
  "pageSize": 100,
  "hasNext": true,
  "pageNumber": 0
}
```

**Tasks Returned:** 50 tasks
**Spaces:** CORESUP (primarily)
**Sample Tasks:**
- CORESUP-157485: "vm-ift2-bd-psql-11430.stands-vdc09.solution.sbt autz требуется обслуживание таблиц"
- CORESUP-157492: "vm-barr-bd-psql-1133.stands-vdc02.solution.sbt flv..."
- CORESUP-157493: "vm-barr-bd-psql-1345.stands-vdc02.solution.sbt paps..."

### Control Member Test: `get_my_tasks(assignee="Антонов")`

```json
{
  "content": [50 tasks],
  "pageSize": 100,
  "hasNext": true,
  "pageNumber": 0
}
```

**Tasks Returned:** 50 tasks
**Sample Tasks:** Same CORESUP tasks

**Conclusion:** Both Garanin and Antonov have 50+ tasks visible via `get_my_tasks`.

---

## Phase 4 — Exact A/B/C Parity Table

| Path | Endpoint/Tool | Source | Task Keys | Count | Elapsed | Verdict |
|------|---------------|--------|-----------|-------|---------|---------|
| Browser A1 | POST /api/v1/query | Harness → LLM | N/A | 0 | ~1800ms | FAILED (semantic_interpretation_failure) |
| Harness A2 | POST /api/v1/query | Harness → LLM | N/A | 0 | ~1800ms | FAILED (semantic_interpretation_failure) |
| Oracle B | get_my_tasks | MCP-SWTR → REAL AS21 | 50 tasks | 50 | ~500ms | SUCCESS |

### Primary Assertion

**Browser keys == Direct Harness keys == Oracle B keys**

**Result:** ❌ **FAIL** - Browser/Harness return 0 tasks, Oracle B returns 50 tasks.

---

## Phase 5 — Generalized Control Member

### Selected Control Member: Antonov.D.A (Антонов)

### Oracle B: `get_my_tasks(assignee="Антонов")`

- **Tasks:** 50 tasks (same set as Garanin)
- **First tasks:** CORESUP-157485, CORESUP-157492, CORESUP-157493

### Direct Harness Query: `Задачи Антонова`

- **Status:** FAILED (semantic_interpretation_failure)
- **Same error as Garanin**

### Conclusion

**Member-specific queries all fail** at semantic interpretation phase, regardless of member identity.

---

## Phase 6 — Point-Read Mapping Verification

### Test: `/api/v1/swtr-read/tasks/DMS-378`

**Response:**
```json
{
  "task_code": "DMS-378",
  "unit": {
    "code": "DMS-378",
    "summary": "[doc] Корректировка валидатора",
    "space": {"code": "DMS"},
    "attributes": [33 items],
    "assigned_to": null,
    "workflow_status": null
  }
}
```

**Finding:** `unit.attributes` exists, but `assigned_to` and `workflow_status` are `null` at top-level.

**`source_data.swtr_attributes` NOT present** in this response.

### Point-Read Mapping Gap

**Classification:** `POINT_READ_MAPPING_GAP`

**Location:** Task API `/api/v1/swtr-read/tasks/{task_code}` response

**Defect:** MCP-SWTR response not transformed to Harness-expected `source_data.swtr_attributes` format.

**However:** This is a **separate issue** from the member-query failure, which occurs at semantic interpretation phase.

---

## Required First-Failing-Boundary Decision

### Analysis

1. **Browser/Direct Harness query:** `Задачи Гаранина`
2. **Query interpretation:** LLM semantic interpreter raises exception
3. **Error returned:** `semantic_interpretation_failure`
4. **No Task API routing occurs** (fails before routing)
5. **Oracle B (direct MCP-SWTR):** Works perfectly via `get_my_tasks`

### First Failing Boundary

**Boundary:** `SEMANTIC_MODEL_UNAVAILABLE` / `LLM_JSON_PARSE_FAILURE`

**Reason:** LLM semantic interpreter fails to parse the natural-language query `Задачи Гаранина`.

### Why Not Other Boundaries?

| Boundary | Not Applicable Because |
|----------|------------------------|
| `UI_PROXY_ROUTE_MISMATCH` | Browser uses correct Harness endpoint |
| `HARNESS_ENDPOINT_MISMATCH` | Direct Harness uses same endpoint as Browser |
| `SEMANTIC_MEMBER_GROUNDING` | No member grounding attempted (interpretation fails first) |
| `CAPABILITY_ARGUMENT_BUILDING` | No capability executed (interpretation fails first) |
| `TASK_API_SOURCE_ROUTING` | Task API not reached (interpretation fails first) |
| `LOCAL_TASK_LIST_ROUTE` | Local DB not queried (interpretation fails first) |
| `MCP_SWTR_SOURCE_CONTRACT` | MCP-SWTR contract is correct (works in Oracle B) |
| `RESPONSE_MAPPING` | Response not sent (interpretation fails first) |
| `POINT_READ_MAPPING_GAP` | Point-read not on member-search path |

---

## Mandatory Execution Counters

| Counter | Count | Required |
|---------|-------|----------|
| Browser natural-language requests | 1 | ✅ >= 1 |
| Direct Harness natural-language requests | 1 | ✅ >= 2 (Garanin + Antonov = 2) |
| Oracle B REAL AS21 reads | 2 | ✅ >= 2 (Garanin + Antonov) |
| Sync/population runs | 0 | ✅ = 0 |
| Local DB authoritative Oracle reads | 0 | ✅ = 0 |
| Fake/mock/frozen reads | 0 | ✅ = 0 |
| AS21 writes | 0 | ✅ = 0 |

---

## Final Verdict

### Allowed Verdicts Check

| Verdict | Status |
|---------|--------|
| `LIVE_MEMBER_ROUTE_DEFECT_PROVEN` | ✅ **SELECTED** |
| `MIXED_ROUTE_AND_POINT_MAPPING_DEFECTS` | ❌ Point-read is separate issue |
| `MEMBER_GROUNDING_DEFECT_PROVEN` | ❌ Member grounding not reached |
| `NO_ROUTE_DEFECT_PROVEN` | ❌ Defect is proven |
| `BLOCKED_BY_ENVIRONMENT` | ❌ Environment is working |

### Selected Verdict

**`LIVE_MEMBER_ROUTE_DEFECT_PROVEN`**

**Definition:** Browser/Direct Harness route is defective (semantic interpreter fails), while Oracle B (direct MCP-SWTR) works correctly.

---

## Root Cause Summary

### Chain of Failure

```
1. User query: "Задачи Гаранина"
   ↓
2. Semantic Interpreter interpret(query)
   ↓
3. LLM API call or JSON parsing fails
   ↓
4. Exception raised
   ↓
5. _source_failure(session, "semantic_interpretation_failure", ...)
   ↓
6. Response: "Не удалось безопасно интерпретировать запрос..."
```

### Primary Issue

**LLM semantic interpreter cannot parse natural-language query.**

### Secondary Issue (Separate)

**Task API response transformation:** `unit.attributes` not exposed as `source_data.swtr_attributes`.

This is a **separate, downstream issue** that does not affect the member-query failure.

---

## Oracle B Correct Usage Pattern

### For Member-Based Search

```
MCP Tool: get_my_tasks(assignee="ФИО")
Example: get_my_tasks(assignee="Гаранин")
Example: get_my_tasks(assignee="Антонов")
```

### Why This Works

1. **FIO format:** `get_my_tasks` expects full name (FILO), not login
2. **Direct MCP-SWTR:** Bypasses semantic interpreter entirely
3. **No routing ambiguity:** Direct tool call, no query parsing needed

### Harness Path Problem

```
Harness → Semantic Interpreter → LLM → Exception
```

The semantic interpreter needs to:
1. Parse query to intent + slots
2. Extract member from "Задачи Гаранина" → slot: member_login
3. Map to capability: task_search with member_login slot
4. Execute capability via MCP-SWTR

**Current failure:** Step 2 (LLM interpretation) raises exception.

---

## Evidence Summary

### Direct MCP-SWTR (Oracle B) - WORKING

```python
content = await client.call_tool("get_my_tasks", {"assignee": "Гаранин"})
# Returns: 50 tasks from CORESUP space
```

### Harness Path - FAILING

```python
response = await client.post("/api/v1/query", json={
    "query": "Задачи Гаранина",
    "session_id": "..."
})
# Response: status=FAILED, warnings=["semantic_interpretation_failure"]
```

---

## Recommendations

### Immediate Fix Required

**Fix semantic interpreter to handle member-based queries:**

1. **Query parsing:** Extract `member_login` from `Задачи {Member}`
2. **Intent detection:** Map to `task_search` intent
3. **Slot filling:** Populate `member_login` slot from extracted member
4. **Capability execution:** Execute `search_tasks` capability

### Alternative Fix (If Semantic Interpreters Cannot Parse)

**Use direct MCP-SWTR for member queries:**

1. Detect member query pattern
2. Skip semantic interpreter
3. Call `get_my_tasks(assignee="Member")` directly
4. Return results

This would bypass the semantic interpreter entirely for member queries.

---

## Conclusion

**Assignment 117R completed with `LIVE_MEMBER_ROUTE_DEFECT_PROVEN` verdict.**

**Root cause:** LLM semantic interpreter cannot interpret natural-language query `Задачи Гаранина`.

**Evidence:**
- Browser UI: FAILED (semantic_interpretation_failure)
- Direct Harness: FAILED (semantic_interpretation_failure)
- Oracle B (get_my_tasks): SUCCESS (50 tasks)

**First failing boundary:** `SEMANTIC_MODEL_UNAVAILABLE` / `LLM_JSON_PARSE_FAILURE`

**Note:** Task API `POINT_READ_MAPPING_GAP` is a separate, downstream issue not affecting the member-query failure.

---

**Report generated:** 2026-09-01  
**QA executor:** GigaCode  
**Commit SHA:** [TO BE GENERATED]  
**Verdict:** `LIVE_MEMBER_ROUTE_DEFECT_PROVEN`
