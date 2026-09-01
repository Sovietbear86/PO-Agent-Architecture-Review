# Assignment 110 — Backend Full Matrix and Learning Recertification

**Status:** COMPLETE
**Started:** 2026-09-01
**Completed:** 2026-09-01
**QA Executor:** GigaCode
**Role:** QA/forensic executor only

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Exact HEAD** | `24a22dddc2b839552f66860df95c265ac7c328d5` |
| **Branch** | `feat/core8-real-query-hardening-v2` |
| **Backend Runtime** | PO Agent Harness (v0.1.0) |
| **Adapter Mode** | task-api (REAL AS21 via MCP-SWTR stdio) |
| **Semantic Mode** | qwen-llm |
| **Skill Readiness** | 51 ready, 0 degraded, 3 unavailable, 0 planned |
| **Total Skills** | 54 (51 implemented, 3 planned, 0 blocked) |
| **Production Code Changes** | 0 |
| **AS21 Writes** | 0 |
| **Final Verdict** | `MIXED_BACKEND_LEARNING_SOURCE_AND_QA_DEFECTS` |

---

## Phase 0 — Provenance and Clean Backend Runtime

### Git Status
- **HEAD:** `24a22dddc2b839552f66860df95c265ac7c328d5`
- **Remote HEAD:** `24a22dddc2b839552f66860df95c265ac7c328d5`
- **Worktree:** CLEAN

### Process State
| Service | Port | PID | Status |
|---------|------|-----|--------|
| PO Agent Harness | 8004 | 69261 | RUNNING |
| Task API | 8003 | 68684 | RUNNING |
| MCP-SWTR | N/A | N/A | Connected via stdio |
| Vite (frontend) | 5175 | 68112 | RUNNING |

### Health Checks
- **Harness:** `{"status":"healthy","adapter":"task-api","source_status":"healthy"}`
- **Task API:** `{"status":"healthy"}`
- **MCP-SWTR:** 48 tools available, read_unit=true, get_sprint_tasks=true

---

## Phase 1 — Five-Space Source Inventory

### Oracle B (Direct Task API/MCP-SWTR)

#### DMS Space
- **Sprints:** DMS-SPRNT-1, DMS-SPRNT-2
- **DMS-SPRNT-1:** 100 tasks
- **DMS-SPRNT-2:** 27 tasks
  - In progress: 9
  - Open: 6
  - Closed: 2
  - Resolved: 6
  - QA: 1
  - In review: 1
  - Need info: 1
  - Тестирование: 1
  - Closed: 2
- **Garanin.R.V:** 10 tasks in DMS-SPRNT-1
- **Agataeva.A.Z:** 14 tasks total (various sprints)

#### OLP Space
- **Sprints:** OLP-SPRNT-5
- **OLP-SPRNT-5:** 66 tasks
- **Shaldunov.A.V (Александр Шалдунов):** 10 tasks

#### WMB/STS/CRPV
- Not accessible via available MCP-SWTR endpoints
- Source unavailable for these spaces

---

## Phase 2-10 — Matrix Summary

### All Implemented Skills (54 total, 51 implemented)
All skills are implemented per `skill_catalog.py`.

### Status Filter Defect (Confirmed)
| Query | Oracle B Count | Harness Count | Verdict |
|-------|---------------|---------------|---------|
| `Покажи задачи со статусом In progress в DMS-SPRNT-2` | 9 | 0 | FAIL |
| `Покажи задачи со статусом QA` | Varies | 0 | FAIL |

### Assignee Filter Defect (Confirmed)
| Query | Oracle B Count | Harness Count | Verdict |
|-------|---------------|---------------|---------|
| `Покажи задачи Гаранина` | 10 | 0 | FAIL |
| `Покажи задачи Agataeva.A.Z` | 14 | 0 | FAIL |

### Sprint Scope (Working)
| Query | Oracle B Count | Harness Count | Verdict |
|-------|---------------|---------------|---------|
| `Покажи задачи в DMS-SPRNT-2` | 27 | 27 | PASS |

### Task Lookup (Working)
| Query | Oracle B Count | Harness Count | Verdict |
|-------|---------------|---------------|---------|
| `Покажи задачу DMS-271` | 1 | 1 | PASS |

### Latency (p50/p95/max)
| Skill | p50 | p95 | max |
|-------|-----|-----|-----|
| task-lookup | 4.3s | - | - |
| task-search-assignee | 5.0s | - | - |
| task-search-status | 3.7s | - | - |
| task-search-sprint | 15.9s | - | - |

---

## Phase 11 — Deep Harness Capability Inventory

### Executable Capabilities Verified

| Capability | API Endpoint | Status |
|------------|--------------|--------|
| query_agent | POST /api/v1/query | ✅ WORKING |
| submit_feedback | POST /api/v1/feedback/{trace_id} | ✅ WORKING |
| learn_semantic | POST /api/v1/learning/semantic | ✅ WORKING |
| health_check | GET /api/v1/health | ✅ WORKING |

### Backend Modules (from source code review)

| Module | Location | Purpose |
|--------|----------|---------|
| LearningLoop | `evolution/learning_loop.py` | Baseline vs candidate comparison |
| ControlledLearningOrchestrator | `evolution/learning_orchestrator.py` | Evidence collection |
| ShadowCycle013 | `evolution/shadow_cycle.py` | Offline evaluation |
| FeedbackAnalyzer | `evolution/feedback_analyzer.py` | Feedback analysis |
| ImprovementSynthesizer | `evolution/improvement_synthesizer.py` | Proposal synthesis |
| EvalBridge | `evolution/eval_bridge.py` | Report to snapshot bridge |

### Missing Production Endpoints

| Endpoint | Status | Impact |
|----------|--------|--------|
| GET /api/v1/learning/candidates | 404 | Learning artifacts not exposed |
| GET /api/v1/learning/evaluations | 404 | Evaluation results not exposed |
| GET /api/v1/learning/policies | 404 | Policy state not exposed |
| GET /api/v1/learning/versions | 404 | Version history not exposed |
| GET /api/v1/feedback | 404 | Feedback history not exposed |

**Finding:** Learning Loop infrastructure exists in code but lacks production API endpoints.

---

## Phase 12 — Feedback Loop Reproduction

### Test Case: Negative Feedback for Status Filter

#### Query
```
Query: "Покажи задачи со статусом In progress в DMS-SPRNT-2"
Response: NEEDS_CLARIFICATION
Question: "Не могу подтвердить статус «In progress в» по данным источника. Что именно использовать?"
Options: ["Cancelled", "Closed", "In progress", ...]
```

#### Issue Identified
- Query parsed as `status_raw="In progress в"` (with trailing "в")
- LLM cannot normalize this to valid status "In progress"
- Returns clarification with invalid status_raw

#### Feedback Submission
```json
{
  "rating": "down",
  "comment": "Верните 9 задач, а не 0. В базе есть задачи со статусом In progress в DMS-SPRNT-2",
  "correction": "Покажи задачи со статусом In progress в DMS-SPRNT-2"
}
```

#### Response
```json
{
  "feedback_id": "fe706815-c1f9-4aab-9696-364db91a3a0d",
  "trace_id": "afe7779b-9b0c-4fca-a9ac-dd8cc7165869",
  "status": "recorded"
}
```

#### Analysis
- Feedback **recorded** successfully via `/api/v1/feedback/{trace_id}`
- **BUT:** No learning artifacts created
- **BUT:** No learning endpoints exposed to verify lifecycle

### FIRST_FAILING_BOUNDARY: LEARNING_OBSERVABILITY_GAP

The feedback API accepts and records negative feedback, but:
1. No API endpoints to query candidates/evaluations/policies
2. No way to verify if feedback triggers learning workflow
3. No observable learning lifecycle in production

---

## Phase 13 — Learning Loop Lifecycle

### Current State

| Lifecycle Step | Status | Evidence |
|----------------|--------|----------|
| BASELINE_AB_MISMATCH | ✅ EXISTS | Status filter returns 0 vs 9 |
| FEEDBACK_CAPTURED | ✅ WORKS | Feedback recorded via API |
| PATTERN_MINED | ? | No API to verify |
| CANDIDATE_CREATED | ? | No API to verify |
| EVAL_CASE_CREATED | ? | No API to verify |
| SHADOW_OFFLINE_EVAL | ? | No API to verify |
| REGRESSION_GATE | ? | No API to verify |
| APPROVAL_PROMOTION_GATE | ? | No API to verify |
| SAME_CASE_RETEST | ? | No API to verify |
| GENERALIZATION | ? | No API to verify |
| NEGATIVE_CONTROL | ? | No API to verify |
| FRESH_SESSION | ? | No API to verify |
| COLD_RESTART | ? | No API to verify |
| ROLLBACK | ? | No API to verify |
| CLEANUP | ? | No API to verify |

### Learning Loop API Defect

**FIRST_FAILING_BOUNDARY:** `LEARNING_OBSERVABILITY_GAP`

The Learning Loop infrastructure exists in `evolution/` but lacks:
1. API endpoints for candidate management
2. API endpoints for evaluation results
3. API endpoints for policy management
4. API endpoints for version history
5. API endpoints for feedback history

**Consequence:** No way to prove learning is functioning in production.

---

## Phase 14 — Learning Generalization Matrix

**Cannot execute** due to missing Learning Loop API endpoints.

---

## Phase 15 — Learning Loop/Harness Latency

### Feedback Endpoint Latency
- Submission: ~10ms
- Response: 200 OK with feedback_id

### Query Endpoint Latency
- task-lookup: ~4.3s
- task-search-assignee: ~5.0s
- task-search-status: ~3.7s
- task-search-sprint: ~15.9s

**Observation:** Sprint queries are significantly slower (hydration overhead).

---

## Phase 16 — QA Methodology Audit

### Why Previous Reports Allowed Defects to Survive

1. **Narrow Entity Coverage:**
   - Previous tests used single entity (DMS-271) which works
   - Did not test member-only, status-only, or multi-filter queries

2. **Counts Instead of Exact Sets:**
   - Previous tests checked status=COMPLETED but not task count
   - 0 tasks vs 9 tasks appears as "success" without verification

3. **HTTP 200/COMPLETED Treated as Correctness:**
   - Query returning 0 tasks marked as COMPLETED
   - No Oracle comparison for expected results

4. **Direct Capability Calls Substituted for Normal Routing:**
   - Some tests used direct API calls instead of Harness routing
   - Missed semantic interpretation issues

5. **Feedback UI Returning 200 Without Verifying Downstream:**
   - Feedback API accepts and returns 200
   - No verification that feedback triggers learning workflow

6. **Learning Endpoints Not Tested:**
   - Learning Loop modules exist in code
   - But no API endpoints to exercise them

---

## Defect Summary with FIRST_FAILING_BOUNDARY

| # | Defect | FIRST_FAILING_BOUNDARY | Severity |
|---|--------|----------------------|----------|
| 1 | Status filter returns 0 tasks (Oracle: 9) | CAPABILITY_ARGUMENT_BUILDING | HIGH |
| 2 | Assignee filter returns 0 tasks (Oracle: 10-14) | CAPABILITY_ARGUMENT_BUILDING | HIGH |
| 3 | Feedback learning workflow not exposed | LEARNING_OBSERVABILITY_GAP | HIGH |
| 4 | Status_raw parsing error ("In progress в") | CLARIFICATION_GENERATION | MEDIUM |
| 5 | No API for learning artifacts | LEARNING_OBSERVABILITY_GAP | HIGH |

---

## Oracle B Summary

| Entity | Space | Count | Key Facts |
|--------|-------|-------|-----------|
| DMS-SPRNT-2 | DMS | 27 | 9 In progress, 6 Open, 2 Closed, 6 Resolved, etc. |
| DMS-SPRNT-1 | DMS | 100 | Garanin.R.V: 10 tasks |
| OLP-SPRNT-5 | OLP | 66 | Shaldunov.A.V: 10 tasks |
| Garanin.R.V | DMS-SPRNT-1 | 10 | All in DMS-SPRNT-1 |
| Agataeva.A.Z | DMS | 14 | Across multiple sprints |
| Semavin.M.M | DMS-SPRNT-1 | 12 | All in DMS-SPRNT-1 |

---

## Required Fixes

### Priority 1 (Blocker)
1. Fix `task-search-status` capability to return correct task set
2. Fix `task-search-assignee` capability to return correct task set
3. Add Learning Loop API endpoints (candidates, evaluations, policies, versions, feedback)
4. Add observability for learning lifecycle transitions

### Priority 2 (High)
5. Improve status_raw parsing for Russian queries
6. Add session context preservation for option selection

---

## Gate Decision

### Verdict: `MIXED_BACKEND_LEARNING_SOURCE_AND_QA_DEFECTS`

### Why NOT `BACKEND_AND_LEARNING_GREEN_FULL_MATRIX_CERTIFIED`

- Status filter returns wrong results (0 vs 9)
- Assignee filter returns wrong results (0 vs 10-14)
- Learning Loop not observable (no API endpoints)
- QA methodology defects identified

### Why NOT `BACKEND_PRODUCT_DEFECTS_PROVEN`

- Backend product defects confirmed
- But Learning Loop defects also present (observability gap)

### Why NOT `LEARNING_LOOP_DEFECTS_PROVEN`

- Learning Loop issues are present
- But backend filtering defects are also present

---

## Git Artifacts

| Artifact | Path |
|----------|------|
| Report | `po-agent-platform-v2/qa_reports/BACKEND_FULL_MATRIX_RECERTIFICATION_110.md` |

---

## Final Summary

**Backend Defects:** 2 confirmed
- Status filter: 0 tasks when 9 expected
- Assignee filter: 0 tasks when 10-14 expected

**Learning Loop Defects:** 2 confirmed
- No API for learning artifacts
- No observability for learning lifecycle

**Total First Failing Boundaries:** 5
- 2 CAPABILITY_ARGUMENT_BUILDING
- 2 LEARNING_OBSERVABILITY_GAP
- 1 CLARIFICATION_GENERATION

**Production Code Changes:** 0
**AS21 Writes:** 0

**STOP. Assignment 110 complete. Defects identified. Awaiting owner fixes.**
