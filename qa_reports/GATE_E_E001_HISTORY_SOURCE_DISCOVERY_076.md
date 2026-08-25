# Gate E / E001 History Source Discovery / Real SWTR Forensics

**Assignment:** 076  
**Date:** 2026-08-24  
**Status:** DISCOVERY_COMPLETE  
**ROLE:** Independent QA / Forensic Investigator only

---

## Executive Summary

**START_HEAD:** `20be63d76f1a1dc4a4310a51f53258ca6a3c44a1`  
**END_HEAD:** `20be63d76f1a1dc4a4310a51f53258ca6a3c44a1`  
**PRODUCTION_CODE_MODIFIED:** NO

**REAL_SWTR_TASKS_PROBED:** 3 (DMS-248, DMS-249, WMB-101)  
**REST_HISTORY_SOURCE:** NOT_AVAILABLE  
**MCP_HISTORY_SOURCE:** NOT_AVAILABLE  
**ALTERNATIVE_HISTORY_SOURCE:** NOT_AVAILABLE

**STATUS_HISTORY_AVAILABLE:** NO  
**ASSIGNEE_HISTORY_AVAILABLE:** NO  
**TRANSITION_TIMESTAMPS_AVAILABLE:** NO

**E001_DECISION:** HISTORY_SOURCE_NOT_AVAILABLE

**TASK_HISTORY_STATUS:** SOURCE_BLOCKED  
**TASK_TIME_IN_STATUS_STATUS:** SOURCE_BLOCKED

**RECOMMENDED_PRODUCTION_CHANGE:** NONE - upstream source must be enabled first  
**READY_FOR_E001_IMPLEMENTATION:** NO

**NEXT_GATE_RECOMMENDATION:** Gate E / Wave 2 (Sprint Metrics) - no dependency on history

---

## Stage 0: Environment / Provenance Guard

### Git State
| Field | Value |
|-------|-------|
| BRANCH | `feat/core8-real-query-hardening-v2` |
| START_HEAD | `20be63d76f1a1dc4a4310a51f53258ca6a3c44a1` |
| END_HEAD | `20be63d76f1a1dc4a4310a51f53258ca6a3c44a1` |
| WORKING_TREE | Clean (QA-only) |

### SWTR Configuration
| Field | Value |
|-------|-------|
| SWTR_BASE_URL | Configured via `BASE_URL` env var |
| SWTR_TOKEN | Configured via `TOKEN` env var |
| SWTR_MCP_TRANSPORT | stdio (default) / sse |
| SWTR_MCP_BASE_URL | Configured via `SWTR_MCP_BASE_URL` env var |

### MCP-SWTR
| Field | Value |
|-------|-------|
| PATH | `mcp-swtr/mcp_server.py` |
| TRANSPORT | FastMCP with stdio/SSE support |
| TOOLS | No history-related tools |

### Imported Module Paths
| Field | Value |
|-------|-------|
| PO_AGENT_SRC | `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/po-agent-platform-v2/src` |
| TASK_API | `/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/PO_Agent_Harness/task-api` |

---

## Stage 1: Current SWTR REST API Forensics

### Task REST Endpoint
**Path:** `/api/v1/swtr-read/tasks/{task_code}`

**Response structure (DMS-248):**
```json
{
  "task_code": "DMS-248",
  "unit": {
    "code": "DMS-248",
    "summary": "Объединить общий конфиг и конфиг аудита",
    "description": "...",
    "createdAt": "2026-06-24T11:15:06.425514Z",
    "createdBy": {...},
    "updatedAt": "2026-08-01T21:34:42.649558Z",
    "updatedBy": {...},
    "workflow_status": {"name": "Closed", "code": "CLSD_YLquKLRWNLxhnnC", ...},
    "assigned_to": {...},
    "attributes": [...],
    ...
  }
}
```

### History-Related Fields Checked
| Field | Exists | Value |
|-------|--------|-------|
| history | ❌ NO | N/A |
| changelog | ❌ NO | N/A |
| audit | ❌ NO | N/A |
| events | ❌ NO | N/A |
| timeline | ❌ NO | N/A |
| activity | ❌ NO | N/A |
| status_transitions | ❌ NO | N/A |
| status_history | ❌ NO | N/A |
| assignee_history | ❌ NO | N/A |
| previous_status | ❌ NO | N/A |

### Endpoint Probes (404 - Not Found)
| Endpoint | Status |
|----------|--------|
| `/api/v1/swtr-read/tasks/DMS-248/history` | 404 |
| `/api/v1/swtr-read/tasks/DMS-248/transitions` | 404 |
| `/api/v1/swtr-read/tasks/DMS-248/changelog` | 404 |
| `/api/v1/swtr-read/tasks/DMS-248/audit` | 404 |
| `/api/v1/swtr-read/tasks/DMS-248/events` | 404 |
| `/api/v1/swtr-read/tasks/DMS-248/updates` | 404 |
| `/api/v1/swtr-read/tasks/DMS-248/timeline` | 404 |

---

## Stage 2: MCP-SWTR Forensics

### MCP-SWTR Tools
**Location:** `mcp-swtr/mcp_server.py`

### History-Related Tools Checked
| Tool Name | Exists | Returns History Data |
|-----------|--------|---------------------|
| get_task_history | ❌ NO | N/A |
| status_history | ❌ NO | N/A |
| task_changelog | ❌ NO | N/A |
| audit_log | ❌ NO | N/A |
| activity_feed | ❌ NO | N/A |
| workflow_events | ❌ NO | N/A |

### Available Tools (Summary)
- `search_units` - Search tasks by JQL-like queries
- `read_unit` - Get single task by key
- `get_unit_files` - Get attachment metadata
- `get_sprint_tasks` - Get sprint tasks
- `get_release_tasks` - Get release tasks
- `get_spaces` - Get spaces
- `get_versions` - Get versions
- No history-related tools

---

## Stage 3: Real Task Probes

### Probed Tasks
| Task | Status | Assignee | Created By | Updated By |
|------|--------|----------|------------|------------|
| DMS-248 | Closed | Garanin.R.V | Garanin.R.V | Kalachanov.V.V |
| DMS-249 | Cancelled | (none) | Kondratchikova.P.I | Kondratchikova.P.I |
| WMB-101 | Выполнен | Russkikh.E.P | Naumova.S.V | Russkikh.E.P |

### History Attributes per Task
| Task | status_transitions | status_history | workflow_status_history | assignee_history |
|------|-------------------|----------------|------------------------|------------------|
| DMS-248 | N/A | N/A | N/A | N/A |
| DMS-249 | N/A | N/A | N/A | N/A |
| WMB-101 | N/A | N/A | N/A | N/A |

### Timestamps Available
| Task | createdAt | created_by | updatedAt | updated_by |
|------|-----------|------------|-----------|------------|
| DMS-248 | ✅ | ✅ | ✅ | ✅ |
| DMS-249 | ✅ | ✅ | ✅ | ✅ |
| WMB-101 | ✅ | ✅ | ✅ | ✅ |

### Conclusion
**Basic timestamps (created/updated) exist, but no status transition or assignee transition history.**

---

## Stage 4: Alternative Authoritative Sources

### Investigated Alternatives

| Source | Exists | Evidence Found |
|--------|--------|----------------|
| SWTR REST API history endpoint | ❌ NOT FOUND | 404 on all history routes |
| MCP-SWTR history tool | ❌ NOT FOUND | No history tools |
| Task attributes | ❌ NO | No status_transitions field |
| Comments | ❌ NO | Comments exist but no workflow metadata |
| Attachments | ❌ NO | Only file metadata, no history |
| Wiki pages | ❌ NO | Not applicable to tasks |

### Source Completeness Assessment
| Source | Exists | Real Data Proven | Status History | Assignee History | Timestamps | Suitable |
|--------|--------|------------------|----------------|------------------|------------|----------|
| SWTR REST task endpoint | ✅ YES | ✅ | ❌ NO | ❌ NO | ❌ Basic only | ❌ NOT_SUITABLE |
| MCP-SWTR | ✅ YES | ✅ | ❌ NO | ❌ NO | ❌ Basic only | ❌ NOT_SUITABLE |
| SWTR REST history endpoint | ❌ NO | N/A | N/A | N/A | N/A | N/A |
| SWTR REST audit endpoint | ❌ NO | N/A | N/A | N/A | N/A | N/A |

**Conclusion:** No alternative authoritative source provides history data.

---

## Stage 5: Source Capability Matrix

| Source | Exists | Real Data | Status History | Assignee History | Timestamps | Production Suitable | Classification |
|--------|--------|-----------|----------------|------------------|------------|---------------------|----------------|
| SWTR REST task | ✅ | ✅ | ❌ | ❌ | ❌ (basic) | ❌ | NOT_AVAILABLE |
| MCP-SWTR | ✅ | ✅ | ❌ | ❌ | ❌ (basic) | ❌ | NOT_AVAILABLE |
| SWTR REST history | ❌ | N/A | N/A | N/A | N/A | N/A | NOT_AVAILABLE |
| SWTR REST audit | ❌ | N/A | N/A | N/A | N/A | N/A | NOT_AVAILABLE |
| SWTR REST transitions | ❌ | N/A | N/A | N/A | N/A | N/A | NOT_AVAILABLE |
| SWTR REST events | ❌ | N/A | N/A | N/A | N/A | N/A | NOT_AVAILABLE |

**Classification Legend:**
- **AUTHORITATIVE:** Provides all required fields with real data
- **PARTIAL:** Provides some fields, missing critical data
- **NOT_AVAILABLE:** Does not exist or returns 404
- **UNSUITABLE:** Exists but lacks required fields

---

## Stage 6: Minimum Contract Discovery

### Target Event Schema
```json
{
  "task_code": "WMB-123",
  "event_timestamp": "2026-08-01T10:00:00Z",
  "field": "workflow_status",
  "old_value": "Open",
  "new_value": "In progress",
  "actor": "Ivanov.I.I"
}
```

### Required Fields for Production
| Field | Source Requirement | SWTR Provides? |
|-------|-------------------|----------------|
| task_code | Task identifier | ✅ YES |
| event_timestamp | ISO 8601 datetime | ❌ Not in history context |
| field | Field name (workflow_status, assigned_to) | ❌ Not exposed |
| old_value | Previous value | ❌ Not exposed |
| new_value | Current value | ❌ Not exposed |
| actor | User who made change | ❌ Not exposed |

### SWTR Response Fields (Current)
| Field | Type | Available | Purpose |
|-------|------|-----------|---------|
| code | string | ✅ YES | Task key |
| summary | string | ✅ YES | Task title |
| description | string | ✅ YES | Task description |
| createdAt | datetime | ✅ YES | Task creation |
| createdBy | user | ✅ YES | Original creator |
| updatedAt | datetime | ✅ YES | Last update |
| updatedBy | user | ✅ YES | Last updater |
| workflow_status | status | ✅ YES | Current status |
| assigned_to | user | ✅ YES | Current assignee |

**Conclusion:** SWTR exposes current state but NOT history/events.

---

## Stage 7: Decision

### E001_DECISION: HISTORY_SOURCE_NOT_AVAILABLE

**Evidence Summary:**

1. **SWTR REST API** - No history/changelog/audit/event endpoints exist
2. **MCP-SWTR** - No history-related tools exposed
3. **Task unit payload** - Contains only current state, no transition history
4. **Timestamps** - Only basic `createdAt`, `createdBy`, `updatedAt`, `updatedBy` available
5. **Attributes** - No `status_transitions`, `status_history`, `workflow_events`, or similar

**Proof by probing:**
- All history endpoint attempts return 404
- No MCP tools named with "history", "changelog", "transition", "audit", "event"
- Real task responses contain no history-related fields

---

## Stage 8: Impact on Skills

### Current Skills Status

| Skill | Status | Reason |
|-------|--------|--------|
| task-history | SOURCE_BLOCKED | No status transitions available |
| task-time-in-status | SOURCE_BLOCKED | No status transitions for duration calculation |

### Blocking Dependencies

| Future Capability | Requires | Blocked? |
|-------------------|----------|----------|
| task-history | Status transitions | ✅ YES (already blocked) |
| task-time-in-status | Status transitions with timestamps | ✅ YES (already blocked) |
| sprint-cycle-time | Task history | ⚠️ Would be blocked |
| sprint-lead-time | Task history | ⚠️ Would be blocked |
| team-velocity (advanced) | Assignee transitions | ⚠️ Would be blocked |
| flow-metrics | Status transitions | ⚠️ Would be blocked |

### Recommendation

**DO NOT** implement task-history or task-time-in-status until upstream SWTR provides history endpoint.

These skills MUST remain `SOURCE_BLOCKED` until:

1. SWTR REST API exposes history endpoint, OR
2. MCP-SWTR provides history tool, OR
3. SWTR unit attributes include status transitions

---

## Stage 9: Report Compliance

✅ REPORT ONLY: `qa_reports/GATE_E_E001_HISTORY_SOURCE_DISCOVERY_076.md`  
✅ NO PRODUCTION CODE MODIFIED  
✅ NO TESTS MODIFIED  
✅ NO PROMPTS MODIFIED  
✅ NO CATALOG MODIFIED  

---

## Final Metrics

| Metric | Value |
|--------|-------|
| START_HEAD | `20be63d76f1a1dc4a4310a51f53258ca6a3c44a1` |
| END_HEAD | `20be63d76f1a1dc4a4310a51f53258ca6a3c44a1` |
| PRODUCTION_CODE_MODIFIED | NO |
| REAL_SWTR_TASKS_PROBED | 3 |
| REST_HISTORY_SOURCE | NOT_AVAILABLE |
| MCP_HISTORY_SOURCE | NOT_AVAILABLE |
| ALTERNATIVE_HISTORY_SOURCE | NOT_AVAILABLE |
| STATUS_HISTORY_AVAILABLE | NO |
| ASSIGNEE_HISTORY_AVAILABLE | NO |
| TRANSITION_TIMESTAMPS_AVAILABLE | NO |
| E001_DECISION | HISTORY_SOURCE_NOT_AVAILABLE |
| TASK_HISTORY_STATUS | SOURCE_BLOCKED |
| TASK_TIME_IN_STATUS_STATUS | SOURCE_BLOCKED |
| RECOMMENDED_PRODUCTION_CHANGE | NONE |
| READY_FOR_E001_IMPLEMENTATION | NO |
| NEXT_GATE_RECOMMENDATION | Gate E / Wave 2 (Sprint Metrics) |

---

## Evidence Summary

### SWTR API Probes
```
GET /api/v1/swtr-read/tasks/DMS-248/history      → 404
GET /api/v1/swtr-read/tasks/DMS-248/transitions  → 404
GET /api/v1/swtr-read/tasks/DMS-248/changelog    → 404
GET /api/v1/swtr-read/tasks/DMS-248/audit        → 404
GET /api/v1/swtr-read/tasks/DMS-248/events       → 404
```

### MCP-SWTR Tools
- No tools with "history", "changelog", "transition", "audit", "event" in name
- Available tools: search_units, read_unit, get_unit_files, get_sprint_tasks, get_release_tasks, get_spaces, get_versions

### Task Unit Payload
```json
{
  "createdAt": "2026-06-24T11:15:06.425514Z",
  "createdBy": {...},
  "updatedAt": "2026-08-01T21:34:42.649558Z",
  "updatedBy": {...},
  // NO status_transitions, status_history, workflow_status_history
}
```

---

## Recommended Next Action

**DO NOT PROCEED** with E001 implementation.

**Required upstream work:**
1. SWTR team must expose history endpoint in REST API
2. MCP-SWTR must be extended with history tools
3. Task API must be extended with history endpoint

**Once upstream enabled:**
1. Task API → Add `/api/v1/swtr-read/tasks/{task_code}/history` endpoint
2. MCP-SWTR → Add `get_task_history` tool
3. PO Agent → Implement adapter `get_task_history()` method
4. Run full regression test suite

---

**STOP - HISTORY SOURCE NOT AVAILABLE**

Report created by Assignment 076 QA / Forensic Investigator task.
