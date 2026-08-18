# Core-8 AS21 Source Contract Inventory

**Roadmap step:** A1 DONE / A2 DONE / A3 CURRENT  
**Status:** BASE TASK FILTER CONTRACT VERIFIED ON REAL AS21; EXTENDED SPRINT/ATTACHMENT/HISTORY/RELEASE SOURCES UNDER DISCOVERY

## Core eight
`task_search`, `task_summary`, `task_quality`, `sprint_health`, `velocity`, `team_workload`, `competency_match`, `release_health`.

## Real AS21 facts now proven
From QA assignments `AS21-A2-REAL-CONTRACT-DISCOVERY-001`, `AS21-A2-FILTER-RETEST-002`, `AS21-A2-FILTER-RETEST-003`:

- local task-api is reachable and returns real SWTR-backed tasks;
- assignment identity is in `source_data.swtr_attributes[code=assigned_to].value.externalId/login`;
- `WMB-30000` maps `assignee_id = Kalachanov.V.V`, `assignee_login = kalachanov.v.v`;
- authoritative project/space is `source_data.swtr_space`;
- `/api/v1/tasks` does **not** support `q`;
- exact-key lookup is correct;
- assignee filtering by externalId/login is correct and nonexistent users return 0;
- project filtering and project+assignee intersections are correct;
- status and free-text filtering work on real data;
- unknown query fields/malformed clauses fail closed;
- long descriptions no longer break or truncate canonical mapping;
- no new regressions from A2;
- current cached task sample did not contain populated sprint/release values;
- current `TaskApiAS21Adapter` does not expose attachment metadata or history.

## Historical/source architecture facts
The early PO Agent `SWTRAdapter` used the local task-api but its `Task` model already had `comments` and `attachments`; however the early mapper initialized them as empty lists. Therefore the old adapter itself is **not** proof that attachment data was available through `/api/v1/tasks`.

More importantly, the current repository contains a richer real SWTR read path in `task-api/app/services/swtr_sync_service.py`:

- MCP `find_units`;
- MCP `find_units_by_filter` using TQL;
- MCP `read_unit` for a full real task;
- MCP `get_current_sprint`;
- sprint task retrieval;
- raw `attributes` preserved into `swtr_attributes`;
- historical sync code already extracted `scrum_board_plugin_sprint` from full `read_unit` payloads.

The current router also exposes read-oriented endpoints under `/api/v1/swtr`, including `/sprints` and `/sprint-tasks`. These must be validated rather than assuming sprint data must exist in the cached `/api/v1/tasks` sample.

## A2 defects that are closed

1. Unsupported `q` caused broad false-positive search — FIXED and real-tested.
2. `assigned_to.externalId/login` was not canonicalized — FIXED and real-tested.
3. `project_space` missing — FIXED from `source_data.swtr_space` and real-tested.
4. unknown source status silently became Open — FIXED; unknown remains UNKNOWN.
5. artificial 10k description cap broke real corpus — FIXED; description preserved.

## A3 questions to answer

### Sprint
Use the proven MCP/SWTR sprint path (`get_current_sprint`, `/api/v1/swtr/sprints`, sprint-task source) to capture a real sprint identifier and real tasks from that sprint. Do not rely only on scanning cached tasks.

### Attachments
Owner has confirmed that at least one task assigned to `Kalachanov.V.V` in space `WMB` contains attachments. QA must discover that task from real data, then inspect the full `read_unit` payload and MCP tool catalog to determine whether attachments are:
- top-level task fields;
- attributes;
- dedicated attachment resources/tools;
- or another read endpoint.

Do not ask the owner to manually provide the key unless deterministic discovery is genuinely impossible.

### History
Inspect MCP tool catalog/source for read-only changelog/activity/status-history capability. If no proven source exists, record the gap explicitly; do not infer transitions from current state.

### Release
Inspect full `read_unit`/filtered real source for `fix_version_s` and any dedicated release/version tool. Do not infer the contract from an empty cached list.

## Gate state

`BASE_TASK_FILTER_CONTRACT = GREEN`  
`A2 = DONE`  
`SPRINT_SOURCE_CONTRACT = UNPROVEN`  
`ATTACHMENT_SOURCE_CONTRACT = UNPROVEN`  
`HISTORY_SOURCE_CONTRACT = UNPROVEN`  
`RELEASE_SOURCE_CONTRACT = UNPROVEN`  
`GATE_A = YELLOW`  
`READY_FOR_LEARNING_LOOP = NO`  
`CURRENT = A3 EXTENDED REAL SWTR SOURCE DISCOVERY`
