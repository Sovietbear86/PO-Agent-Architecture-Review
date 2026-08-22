# CORE8_RUNTIME_WIRING_AND_SPRINT_GUARD_RETEST_043

## Executive Summary

**043_VERDICT = RED**

Assignment 043 tests the production fix that:
1. Accepts both runtime env naming styles (`AS21_MODE`/`TASK_API_BASE_URL` and `PO_AGENT_AS21_MODE`/`PO_AGENT_TASK_API_BASE_URL`)
2. Prevents sprint capabilities from executing without required source slots
3. Treats `/api/v1/tasks[*].source_id` as canonical SWTR task key

**Findings:**
- ✅ Both env naming variants work correctly (task-api mode confirmed)
- ✅ Task API routes are registered and accessible
- ✅ M1 and M2 smoke tests pass
- ❌ M3 and M4 fail with sprint intelligence capability issues
- ❌ Sprint guard fix (line 125 sprint_intelligence.py) is IN THE CODE but Python environment loads OLD cached code from conflicting path

---

## Preflight

| Check | Status | Evidence |
|-------|--------|----------|
| ACTIVE_ASSIGNMENT = 043 | ✅ PASS | GIGACODE_NEXT_ACTION.md |
| ACTIVE_ASSIGNMENT_FILE = qa_assignments/CORE8_RUNTIME_WIRING_AND_SPRINT_GUARD_RETEST_043.md | ✅ PASS | File exists |
| ALLOWED_REPORT_FILE = qa_reports/CORE8_RUNTIME_WIRING_AND_SPRINT_GUARD_RETEST_043.md | ✅ PASS | Allowed |
| qa_026_test_runner_v2.py not modified | ✅ PASS | git diff empty |
| No prohibited files staged | ✅ PASS | git status clean |

**START_HEAD = 3750d09fd6194549f4c4cae349b5ed834494d90d**

---

## Phase 1: Service Restart and Runtime Wiring

### Variant A - Legacy Env Names

```bash
AS21_MODE=task-api TASK_API_BASE_URL=http://127.0.0.1:8003 \
  python3 -m uvicorn po_agent.main:app --host 127.0.0.1 --port 8004
```

**Health Check Results:**
```json
{
  "status": "healthy",
  "service": "po-agent-platform-v2",
  "runtime": "harness-dialogue-v2",
  "adapter": "task-api",
  "semantic_mode": "qwen-llm",
  "source_status": "healthy",
  "source_error": null,
  "runtime_init_error": null,
  "source_facts": ["attachments", "releases", "spaces", "sprints", "tasks", "team_competencies"],
  "skill_readiness": {"ready": 47, "degraded": 0, "unavailable": 7, "planned": 0}
}
```

**Result:** ✅ PASS - `adapter: task-api`, `source_status: healthy`

### Variant B - PO_AGENT-Prefixed Env Names

```bash
PO_AGENT_AS21_MODE=task-api PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8003 \
  python3 -m uvicorn po_agent.main:app --host 127.0.0.1 --port 8004
```

**Health Check Results:**
```json
{
  "status": "healthy",
  "service": "po-agent-platform-v2",
  "runtime": "harness-dialogue-v2",
  "adapter": "task-api",
  "semantic_mode": "qwen-llm",
  "source_status": "healthy",
  "source_error": null,
  "runtime_init_error": null,
  "source_facts": ["attachments", "releases", "spaces", "sprints", "tasks", "team_competencies"],
  "skill_readiness": {"ready": 47, "degraded": 0, "unavailable": 7, "planned": 0}
}
```

**Result:** ✅ PASS - `adapter: task-api`, `source_status: healthy`

### Runtime Wiring Conclusion

| Check | Status |
|-------|--------|
| Variant A starts in task-api mode | ✅ PASS |
| Variant B starts in task-api mode | ✅ PASS |
| Root `/health` readiness-aware | ✅ PASS |
| `/health` and `/api/v1/health` agree | ✅ PASS |
| `runtime_init_error` is null | ✅ PASS |

**ENV_ALIAS_LEGACY_MODE = PASS**
**ENV_ALIAS_PO_AGENT_MODE = PASS**

---

## Phase 2: Task API Entrypoint and SWTR-Read Diagnostics

### Process Verification

```
Task API PID: 29199 (original)
Restarted Task API: new process on port 8003
```

### Task API /health

```json
{
  "status": "healthy"
}
```

### Task API OpenAPI Routes

| Route | Status |
|-------|--------|
| `/api/v1/tasks` | ✅ Registered (GET) |
| `/api/v1/swtr-read/health` | ✅ Registered (GET) |
| `/api/v1/swtr-read/tasks/{task_code}` | ✅ Registered (GET) |
| `/api/v1/swtr-read/sprints/{sprint_id}/tasks` | ✅ Registered (GET) |
| `/api/v1/swtr-read/versions` | ✅ Registered (GET) |

### SWTR-Read Endpoint Tests

| Endpoint | Result | Reason |
|----------|--------|--------|
| `/api/v1/swtr-read/health` | 503 Service Unavailable | MCP-SWTR transport unavailable |
| `/api/v1/swtr-read/versions?limit=5` | 503 Service Unavailable | MCP-SWTR transport unavailable |

**Task API entrypoint is current (correct code). MCP-SWTR unavailable is expected as it's not installed in this repository.**

**TASK_API_ENTRYPOINT_CURRENT = YES**
**WRONG_TASK_API_PROCESS = NO**
**SWTR_READ_ROUTES_PRESENT = YES**

---

## Phase 3: Manual Smoke Cases

### Test Execution

| Case | Query | Status | Result |
|------|-------|--------|--------|
| M1 | `Покажи открытые задачи Гаранина из пространства DMS` | NEEDS_CLARIFICATION | Asks for user login confirmation |
| M2 | `Покажи задачи Безрукова` | COMPLETED | 8 tasks found (CRPV-109286, CRPV-109285, etc.) |
| M3 | `Покажи здоровье спринта DMS-SPRNT-2` | FAILED | AS21 temporarily unavailable |
| M4 | `Покажи список спринтов по DMS` | FAILED | KeyError: 'sprint_id' |

### Detailed Results

**M1 - Garanin DMS Open Tasks:**
- Status: NEEDS_CLARIFICATION
- Reason: User login confirmation required
- Expected: Clarification is valid behavior

**M2 - Bezrukov Tasks:**
- Status: COMPLETED
- Tasks found: 8
- Keys: CRPV-109286, CRPV-109285, CRPV-102735, CRPV-156030, CRPV-156031, CRPV-25486, CRPV-52318, CRPV-36098
- Expected: ✅ PASS

**M3 - DMS-SPRNT-2 Health:**
- Status: FAILED
- Response: "Источник AS21 временно недоступен. Нельзя подтвердить сущности запроса."
- Root cause: MCP-SWTR unavailable (not installed in this repo)

**M4 - Sprint List DMS:**
- Status: FAILED
- Response: "Внутренняя ошибка Harness"
- **Root cause: Sprint guard fix NOT APPLIED due to Python path conflict**

### Sprint Guard Fix Verification

The fix at `po-agent-platform-v2/src/po_agent/harness/sprint_intelligence.py` line 124-125:

```python
async def _tasks(self, args: dict[str, str]) -> tuple[str, list[Task]]:
    sprint_id = (args.get("sprint_id") or "").strip().upper()  # FIX: uses .get() not direct access
    if not sprint_id:
        raise AS21CapabilityUnavailable("sprint_id is required for sprint intelligence")
    return sprint_id, await self.adapter.get_sprint_tasks(sprint_id)
```

**PROBLEM:** Python environment loads module from conflicting path:
- Repository code: `/Users/kalachanov.v.v/Desktop/Мои.../PO-Agent-Architecture-Review/po-agent-platform-v2/src/...`
- Environment code: `/Users/kalachanov.v.v/Desktop/Мои.../PO_Agent_Harness/po-agent-platform-v2/src/...`

The environment path (PO_Agent_Harness) has OLD code with `args["sprint_id"].upper()` causing KeyError.

**FIX IS IN REPOSITORY** but Python import system loads from conflicting path.

---

## Phase 4: Narrow Source-Backed Oracle Proof

### Available Oracle Paths

| Path | Status | Notes |
|------|--------|-------|
| Task API `/api/v1/swtr-read/*` | 503 | MCP-SWTR unavailable |
| MCP-SWTR | Not installed | Only in adjacent MyTestProject_1 |
| Direct SWTR/Jira | 403 | Token lacks swtr:wmb role |

### Test Case M2 Oracle Evidence

**Task API `/api/v1/tasks` query results for Bezrukov:**

| Task Key | Title | Status |
|----------|-------|--------|
| CRPV-109286 | DMS \| Реализовать требование HCK-502... | Unknown |
| CRPV-109285 | DMS \| Реализовать требование HCK-501... | Unknown |
| CRPV-102735 | Пройти ручную проверку на соответствие... | Unknown |
| CRPV-156030 | Обезличивание данных категории К-2... | Unknown |
| CRPV-156031 | Отказ от проверки права SELECT... | Unknown |
| CRPV-25486 | Platform V OLAP Analytics Выпуск сертификатов... | Unknown |
| CRPV-52318 | OLAP Analytics 229 Возможность делиться... | Unknown |
| CRPV-36098 | OLAP 68. Возможность сохранять отчет... | Unknown |

**AGENT_KEYS:** CRPV-109286, CRPV-109285, CRPV-102735, CRPV-156030, CRPV-156031, CRPV-25486, CRPV-52318, CRPV-36098

**ORACLE_KEYS:** N/A - No independent oracle path available due to MCP-SWTR unavailability

**MISSING_KEYS:** N/A
**EXTRA_KEYS:** N/A

---

## Acceptance Criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Both env naming variants work | ✅ PASS | AS21_MODE and PO_AGENT_AS21_MODE both accepted |
| Root `/health` readiness-aware | ✅ PASS | Returns runtime, adapter, source_status |
| Task API entrypoint current | ✅ PASS | All routes registered correctly |
| M1-M4 execute without HTTP 500 | ❌ FAIL | M3, M4 fail with internal errors |
| Sprint guard fix applied | ❌ FAIL | KeyError due to Python path conflict |
| Independent oracle path proven | ❌ FAIL | MCP-SWTR unavailable |
| `KEYERROR_COUNT = 0` | ❌ FAIL | M4 shows KeyError |

---

## Footer Metrics

| Metric | Value |
|--------|-------|
| ASSIGNMENT_ID | CORE8_RUNTIME_WIRING_AND_SPRINT_GUARD_RETEST_043 |
| START_HEAD | 3750d09fd6194549f4c4cae349b5ed834494d90d |
| REPORT_COMMIT | PENDING_BEFORE_COMMIT |
| ENV_ALIAS_LEGACY_MODE | PASS |
| ENV_ALIAS_PO_AGENT_MODE | PASS |
| ROOT_HEALTH_READINESS_AWARE | YES |
| HEALTH_PAYLOADS_AGREE | YES |
| TASK_API_ENTRYPOINT_CURRENT | YES |
| WRONG_TASK_API_PROCESS | NO |
| SWTR_READ_ROUTES_PRESENT | YES |
| ORACLE_PATH_PROVEN | NO |
| ORACLE_PATH_TYPE | NONE |
| MANUAL_SMOKE_M1 | PASS (clarification) |
| MANUAL_SMOKE_M2 | PASS |
| MANUAL_SMOKE_M3 | BLOCKED (AS21 unavailable) |
| MANUAL_SMOKE_M4 | BLOCKED (KeyError) |
| INTERNAL_KEYERROR_COUNT | 1 |
| QUERY_HTTP_500_COUNT | 0 |
| FALSE_GREEN_COUNT | 0 |
| RUNNER_MODIFIED | NO |
| PRODUCTION_MODIFIED_BY_QA | NO |
| UNAUTHORIZED_FILES_COMMITTED | NO |
| **043_VERDICT** | **RED** |
| READY_TO_RESUME_017_V2 | NO |

---

## Root Cause Analysis

### Sprint Guard Fix Not Applied

The sprint guard fix at line 125 of `sprint_intelligence.py` changes:
```python
# BEFORE (BUG):
sprint_id = args["sprint_id"].upper()  # KeyError when args["sprint_id"] missing

# AFTER (FIX):
sprint_id = (args.get("sprint_id") or "").strip().upper()  # Safe default
if not sprint_id:
    raise AS21CapabilityUnavailable("sprint_id is required...")
```

**Why fix not applied:**
- Python import system loads module from `/Users/kalachanov.v.v/Desktop/Мои.../PO_Agent_Harness/po-agent-platform-v2/src/`
- Repository code at `/Users/kalachanov.v.v/Desktop/Мои.../PO-Agent-Architecture-Review/po-agent-platform-v2/src/` not loaded
- Path conflict caused by `po-agent-platform-v2/src` in PYTHONPATH from adjacent project

### Manual Action Required

1. **Fix Python path conflict** - Remove conflicting path from PYTHONPATH or virtual environment
2. **Restart PO Agent** - Ensure new code is loaded after path fix
3. **Re-test M4** - Verify `sprint_id` is handled gracefully

**OR**

Update the sprint intelligence capability to handle missing `sprint_id` gracefully even if using direct access pattern:

```python
# Alternative fix (if .get() pattern cannot be used):
sprint_id = args.get("sprint_id")
if sprint_id is None:
    raise AS21CapabilityUnavailable("sprint_id is required...")
sprint_id = sprint_id.strip().upper()
```

---

*Report generated: 2026-08-22T18:18:00Z*
*QA Runner: PO Agent Harness v2*
*Branch: feat/core8-real-query-hardening-v2*
