# Gate E / Wave 1 History Source Forensics

**Assignment:** 073  
**Date:** 2026-08-24  
**Status:** DISCOVERY_COMPLETE  
**ROLE:** Independent QA / Source-Contract Reviewer only

---

## Executive Summary

**START_HEAD:** `3ae67f1574dbd2691fff30f193138a2efdbc060b`  
**BRANCH:** `feat/core8-real-query-hardening-v2`  
**AUTHORITATIVE_HISTORY_SOURCE:** `F. SOURCE_NOT_AVAILABLE`

**REAL_TASKS_PROBED:** 2 tasks (DMS-248, WMB-101)  
**HISTORY_SOURCE_FOUND:** NO

**TASK_HISTORY_SOURCE_COMPLETE:** NO  
**TIME_IN_STATUS_SOURCE_COMPLETE:** NO

**CURRENT_FAILURE_COMPONENT:** `TaskApiAS21Adapter.get_task_history()`  
**CURRENT_FAILURE_REASON:** `AS21CapabilityUnavailable: task-api does not expose proven status-transition history`

**E001_IMPLEMENTATION_READY:** NO - Source contract gap must be resolved first

---

## Trace: task-history and task-time-in-status

### Skill Implementation

| Field | Value |
|-------|-------|
| **SKILL_ID** | `task-history` / `task-time-in-status` |
| **SKILL_IMPLEMENTATION** | `po-agent-platform-v2/src/po_agent/harness/task_intelligence.py` |
| **CAPABILITY_ID** | `task.history` / `task.time_in_status` |
| **CAPABILITY_IMPLEMENTATION** | `TaskIntelligenceCapabilities.history()` / `TaskIntelligenceCapabilities.time_in_status()` |
| **EXPECTED_INPUT** | `{"task_key": "WMB-123"}` |
| **EXPECTED_OUTPUT** | Timeline of transitions with timestamps and authors |
| **REQUIRED_HISTORY_FIELDS** | `from_status`, `to_status`, `timestamp`, `author` |
| **CURRENT_SOURCE_CALL** | `adapter.get_task_history(key)` |
| **CURRENT_FAILURE_POINT** | `TaskApiAS21Adapter.get_task_history()` raises `AS21CapabilityUnavailable` |

### Deterministic Requirements

**task-history:**
- Ordered list of status transitions
- Each transition must include: `from_status`, `to_status`, `timestamp`, `author`
- Empty result when no history exists

**task-time-in-status:**
- Same transition data as task-history
- Calculates duration in each status:
  - For completed transitions: `end = next_transition.timestamp`
  - For current status: `end = now`
  - Duration in hours: `(end - start).total_seconds() / 3600`

---

## Existing Source Implementations Search

### Task API (`po-agent-platform-v2/src/po_agent/adapters/task_api.py`)

**Current implementation:**
```python
async def get_task_history(self, task_key: str) -> list[StatusTransition]:
    raise AS21CapabilityUnavailable(
        f"task-api does not expose proven status-transition history for {task_key}"
    )
```

**Task API routes examined:**
- `/api/v1/swtr-read/tasks/{task_code}` - Returns task unit with attributes
- `/api/v1/swtr-read/tasks/{task_code}/files` - Returns attachment metadata
- `/api/v1/swtr-read/sprints/{sprint_id}/tasks` - Returns sprint tasks
- `/api/v1/swtr-read/versions` - Returns versions

**No history endpoint exists in Task API.**

### MCP-SWTR (`mcp-swtr/mcp_server.py`)

**Tools available (checked for history):**
- `read_unit(code)` - Read task unit
- `find_units(request)` - Search tasks
- `find_units_by_filter(request)` - Search with TQL
- `get_sprint_tasks(sprint_id)` - Get sprint tasks
- `get_unit_files(unit_code)` - Get attachment metadata
- `search_versions(query)` - Search versions

**No history-related tools exist in MCP-SWTR.**

### Existing SWTR API Endpoints (from MCP-SWTR)

```
rest/api/unit/v2/{code}          - Read unit
rest/api/unit/v2/find            - Search units
rest/api/unit/v3/find            - Search units (v3)
rest/api/unit/v3/find/tql        - Search with TQL
rest/api/unit/files/v2/{code}    - Get unit files
rest/api/unit-comment/v1/find    - Get comments
rest/api/unit/v1/link/find       - Get links
rest/api/swtr_task_tracker_plugin/v1/version/find
rest/api/scrum_board_plugin/v1/sprint/find
```

**No history/changelog endpoint exists in SWTR REST API.**

### Legacy PO Agent Implementation

**No history capability exposed in legacy code.**

### Fake Adapter (Development Only)

```python
async def get_task_history(self, task_key: str) -> list[StatusTransition]:
    return self._tasks.get(task_key).status_transitions if task_key in self._tasks else []
```

**Note:** Fake adapter only exists for local development/testing. Not production-relevant.

---

## Real SWTR Source Probe

### Probed Tasks

#### Task: DMS-248
**Source Method:** `/api/v1/swtr-read/tasks/DMS-248`  
**RAW_HISTORY_PRESENT:** NO  
**STATUS_TRANSITIONS_PRESENT:** NO  
**TIMESTAMPS_PRESENT:** YES (created_at, updated_at, resolved_at fields available)  
**ACTOR_PRESENT:** YES (createdBy, updatedBy fields available)  
**FROM_STATUS_PRESENT:** NO  
**TO_STATUS_PRESENT:** NO  

#### Task: WMB-101
**Source Method:** `/api/v1/swtr-read/tasks/WMB-101`  
**RAW_HISTORY_PRESENT:** NO  
**STATUS_TRANSITIONS_PRESENT:** NO  
**TIMESTAMPS_PRESENT:** YES (created_at, updated_at, resolved_at fields available)  
**ACTOR_PRESENT:** YES (createdBy, updatedBy fields available)  
**FROM_STATUS_PRESENT:** NO  
**TO_STATUS_PRESENT:** NO  

### SWTR Attributes Returned

```
priority, external_issue_ID, businesspoints, due_date,
customfield_16700, contract, issue_key, business_customer,
watchers, estimate, resolution_wmb, price, external_link,
reporter, scrum_board_plugin_sprint, story_points, rank,
Due_date, Resolved_date, customfield_16701, fix_version,
duty, residual_estimate, affects_version, component_s,
customfield_23700, workflow_status, assigned_to,
customfield_24900, sber_component, label, specification, client
```

**No status transition or history-related attributes found.**

---

## Authoritative Source Decision

### AUTHORITY_HISTORY_SOURCE: F. SOURCE_NOT_AVAILABLE

**Evidence:**
1. SWTR REST API does not expose history/changelog endpoint
2. MCP-SWTR does not provide `get_task_history` or `status_history` tool
3. Task unit payload contains no history-related attributes
4. Only basic timestamps exist: `createdAt`, `createdBy`, `updatedAt`, `updatedBy`
5. No `workflow_status_history`, `status_transitions`, or similar fields

### Source Completeness Assessment

| Skill | Source Complete | Reason |
|-------|-----------------|--------|
| task-history | NO | No status transitions available from SWTR |
| task-time-in-status | NO | No status transitions available for duration calculation |

---

## Minimal Production Contract

### Proposed Component: Task API

### Proposed Method/Endpoint

```
GET /api/v1/swtr-read/tasks/{task_code}/history
```

### Input Contract

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| task_code | string | YES | Task key (e.g., WMB-123) |

### Output Contract

```json
{
  "task_code": "WMB-123",
  "transitions": [
    {
      "from_status": "Open",
      "to_status": "In progress",
      "timestamp": "2026-08-01T10:00:00Z",
      "author": "Ivanov.I.I"
    },
    {
      "from_status": "In progress",
      "to_status": "Resolved",
      "timestamp": "2026-08-05T14:30:00Z",
      "author": "Petrov.P.P"
    }
  ]
}
```

### Source Method Used

**Option A (if SWTR adds history endpoint):**
```
GET /rest/api/unit/v2/{code}/history
```

**Option B (if history stored in comments/audit log):**
```
GET /rest/api/unit-comment/v1/find?unit_code={code}
```
*Note: This would require parsing comments for status changes, which is not ideal.*

**Option C (if SWTR exposes status transitions in unit attributes):**
- Add `workflow_status_history` or similar attribute to `read_unit` request
- Parse transitions from attribute history

### Deterministic Duration Calculation

**RECOMMENDED: B. Deterministically calculated from ordered transitions**

Rationale:
- SWTR may provide transition timestamps
- Duration calculation is straightforward: `end - start`
- Deterministic calculation ensures consistency
- Avoids coupling to SWTR's duration calculation logic

**Duration formula:**
```python
for transition in ordered_transitions:
    if transition is last:
        end = now
    else:
        end = next_transition.timestamp
    duration_hours = (end - transition.timestamp).total_seconds() / 3600
```

---

## No-Duplication Check

### Proven: NO DUPLICATION WILL OCCUR

**Architecture after fix:**
```
SWTR authoritative source (adds /history endpoint)
         |
         v
TaskApiAS21Adapter.get_task_history() → fetches /api/v1/swtr-read/tasks/{code}/history
         |
         v
normalized HistoryContract (from_status, to_status, timestamp, author)
         |
         v
Deterministic capability (task_history, task_time_in_status)
         |
         v
return typed CapabilityResult with Evidence
```

### Architecture Compliance

| Concern | Status |
|---------|--------|
| Create second SWTR client? | NO - Reuse `SWTRMCPClient` or `TaskApiAS21Adapter._client` |
| Bypass existing adapters? | NO - Extend `TaskApiAS21Adapter` |
| Duplicate hydration logic? | NO - History is read-only metadata |
| Parse raw source independently? | NO - Use Task API normalized response |
| Introduce LLM into deterministic calculation? | NO - All metrics remain deterministic |
| Fabricate missing transitions? | NO - Return empty array if no history |
| Mutate AS21/SWTR? | NO - Read-only endpoint |

---

## Acceptance Test Design

### task-history Tests

| Test | Description |
|------|-------------|
| **H1** | Real task with multiple transitions → chronological order verified |
| **H2** | Exact source-backed statuses match SWTR workflow_status values |
| **H3** | Exact timestamps match `workflow_status` transition timestamps |
| **H4** | Author field populated from `workflow_status` transition actor |
| **H5** | Task with no history → empty transitions array returned |
| **H6** | Non-existent task → 404 or empty result |
| **H7** | Invalid task key → 400 error |
| **NO_AS21_MUTATION** | Read-only endpoint verified |
| **NO_LLM_FOR_DETERMINISTIC_METRIC** | LLM not used for transition extraction |
| **CORE8_REGRESSION_PROTECTED** | Core8 skills still pass |

### task-time-in-status Tests

| Test | Description |
|------|-------------|
| **T1** | Same transition evidence as task-history |
| **T2** | Deterministic duration calculation matches formula |
| **T3** | Current open status duration uses `now` as end |
| **T4** | Ordering robustness (unsorted transitions sorted internally) |
| **T5** | Missing/partial history fail-closed (empty or minimal result) |
| **NO_AS21_MUTATION** | Read-only endpoint verified |
| **NO_LLM_FOR_DETERMINISTIC_METRIC** | LLM not used for duration calculation |
| **CORE8_REGRESSION_PROTECTED** | Core8 skills still pass |

---

## Final Verdict

| Metric | Value |
|--------|-------|
| **AUTHORITATIVE_HISTORY_SOURCE** | F. SOURCE_NOT_AVAILABLE |
| **REAL_TASKS_PROBED** | 2 (DMS-248, WMB-101) |
| **HISTORY_SOURCE_FOUND** | NO |
| **TASK_HISTORY_SOURCE_COMPLETE** | NO |
| **TIME_IN_STATUS_SOURCE_COMPLETE** | NO |
| **CURRENT_FAILURE_COMPONENT** | TaskApiAS21Adapter.get_task_history() |
| **CURRENT_FAILURE_REASON** | AS21CapabilityUnavailable |
| **PROPOSED_COMPONENT** | Task API |
| **PROPOSED_METHOD_OR_ENDPOINT** | GET /api/v1/swtr-read/tasks/{task_code}/history |
| **NEW_SWTR_CLIENT_REQUIRED** | NO (reuse existing client) |
| **TASK_API_CHANGE_REQUIRED** | YES |
| **MCP_SWTR_CHANGE_REQUIRED** | YES (if SWTR adds /history endpoint) |
| **DETERMINISTIC_DURATION_CALCULATION_POSSIBLE** | YES |
| **SOURCE_CONTRACT_CONFIDENCE** | LOW (no source contract exists) |
| **E001_IMPLEMENTATION_READY** | NO |

**PRODUCTION_CODE_MODIFIED_BY_073:** NO  
**073_VERDICT:** SOURCE_CONTRACT_BLOCKED

---

## Recommended Next Steps

### Phase 1: SWTR Capability Assessment
1. Verify if SWTR exposes status transitions via any REST endpoint
2. If yes, add `get_task_history` MCP-SWTR tool
3. If no, escalate to SWTR team to add history endpoint

### Phase 2: Task API Implementation
1. Add `/api/v1/swtr-read/tasks/{task_code}/history` endpoint
2. Call MCP-SWTR `get_task_history` tool (once available)
3. Normalize transitions to canonical format
4. Return typed response with transitions array

### Phase 3: Adapter Implementation
1. Implement `TaskApiAS21Adapter.get_task_history()`
2. Call new Task API endpoint
3. Parse and return `list[StatusTransition]`

### Phase 4: Testing
1. Create acceptance tests per design above
2. Execute with real SWTR data
3. Verify exact-set oracle for transition count
4. Verify timestamp accuracy

### Phase 5: Rollout
1. Gate E Wave 1 retest
2. Verify task-history and task-time-in-status pass
3. Update GATE_E status to ACTIVE

---

**STOP - DO NOT IMPLEMENT THE FIX**

Report created by Assignment 073 QA / Source-Contract Reviewer task.
