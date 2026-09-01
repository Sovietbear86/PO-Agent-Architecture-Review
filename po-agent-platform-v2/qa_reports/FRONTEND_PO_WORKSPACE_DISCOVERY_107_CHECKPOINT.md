# Assignment 107 - Frontend/PO Workspace Discovery

**Status:** IN_PROGRESS
**Started:** 2026-09-01
**Last Update:** 2026-09-01

## Phase 0 - Provenance and Baseline Integrity

### Git Status
- **Branch:** feat/core8-real-query-hardening-v2
- **HEAD:** eda68c9c0d3a8315256050e1dccf460053164943
- **Remote HEAD:** eda68c9c0d3a8315256050e1dccf460053164943
- **Status:** CLEAN (no uncommitted changes)

### Assignment 106 Baseline
- **Status:** COMPLETED and PUSHED
- **HEAD:** 0a471d7
- **Verdict:** FULL_REGRESSION_GREEN_READY_FOR_NEXT_PLAN_STEP
- **Skills Tested:** 54/54
- **PASS:** 23
- **EXPECTED_CLARIFICATION:** 25
- **EXPECTED_SOURCE_CAPABILITY_UNAVAILABLE:** 6
- **FAIL:** 0
- **BLOCKED:** 0

### Frontend Packages Identified

| Package | Path | Framework | Start Command | Port |
|---------|------|-----------|---------------|------|
| po-agent-frontend | po-agent-platform-v2/frontend | React 18 + Vite 5 | `npm run dev` | 5175 |
| task-api (backend) | task-api | FastAPI | `uvicorn main:app` | 8003 |

### Frontend Startup Configuration

**vite.config.ts:**
```typescript
server: {
  port: 5175,
  proxy: {
    '/api': {
      target: 'http://localhost:8004',
      changeOrigin: true,
    },
  },
}
```

**API Proxy Target:** `http://localhost:8004` (PO Agent Harness Dialogue Runtime)

### Backend API Endpoints Used by Frontend

| API Module | Endpoints | Status |
|------------|-----------|--------|
| agent.query | POST /api/v1/query | Active |
| agent.feedback | POST /api/v1/feedback/{trace_id} | Active |
| agent.learnSemantic | POST /api/v1/learning/semantic | Active |
| tasks.getAll | GET /api/v1/tasks | Active |
| quality.getEvalResults | GET /api/v1/evaluations/results | Active |
| team.getMembers | GET /api/v1/team/members | Active |
| releases.getAll | GET /api/v1/releases | Active |

### Backend Health Check
- **PO Agent Harness (port 8004):** HEALTHY
- **Task API (port 8003):** HEALTHY
- **MCP-SWTR:** Connected via stdio

## Progress

- Phase 0: IN PROGRESS
- Phase 1: PENDING
- Phase 2: PENDING
- Phase 3: PENDING
- Phase 4: PENDING
- Phase 5: PENDING
- Phase 6: PENDING
- Phase 7: PENDING
- Phase 8: PENDING

## Notes

- Backend is healthy and ready for live smoke testing
- Frontend uses certified Harness API path (PO Agent Harness on port 8004)
- No immediate startup blockers identified
