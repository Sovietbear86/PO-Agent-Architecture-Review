# Core-8 AS21 Source Contract Inventory

**Roadmap step:** A1 DONE / A2 DONE / A3 CURRENT  
**Status:** BASE TASK FILTER CONTRACT GREEN; ATTACHMENT SOURCE DISCOVERED AND WIRED FOR REAL RETEST; SPRINT/RELEASE/HISTORY STILL PARTIAL

## Core eight
`task_search`, `task_summary`, `task_quality`, `sprint_health`, `velocity`, `team_workload`, `competency_match`, `release_health`.

## Real AS21 facts proven through A2
- local task-api returns real SWTR-backed tasks;
- assignment identity lives in `source_data.swtr_attributes[code=assigned_to].value.externalId/login`;
- `WMB-30000` maps `assignee_id = Kalachanov.V.V`, `assignee_login = kalachanov.v.v`;
- authoritative project/space is `source_data.swtr_space`;
- `/api/v1/tasks` does not support `q`;
- exact key, assignee, project, status and free-text filtering are real-tested and fail closed;
- long descriptions are preserved without arbitrary truncation;
- unknown statuses remain UNKNOWN rather than becoming Open.

## A3 extended-source discovery — proven facts
QA assignment `AS21-A3-EXTENDED-SOURCE-DISCOVERY-004` proved that MCP-SWTR exposes richer READ-ONLY tools beyond the cached `/api/v1/tasks` facade:

- `read_unit` — full unit payload;
- `find_units` / `find_units_by_filter` — task search/TQL;
- `get_unit_files` — attachment metadata;
- `download_unit_file` — attachment content (not enabled for normal metadata reads);
- `get_unit_comments` — comments;
- `search_versions` — release/version discovery;
- `get_current_sprint`, `get_sprint_tasks`, `get_current_sprint_tasks` — sprint tools, although current-sprint call currently returns an AS21 invalid-parameters error in the tested environment.

### Attachments — PROVEN REAL SOURCE
`WMB-30000` is a real WMB task assigned to `Kalachanov.V.V` and has attachments.

Proven metadata source:
`MCP get_unit_files(unit_code)`.

Observed metadata family includes:
`id`, `name`, `size`, `contentType`, `created`, `createdBy`, `version`, `hash`, `storageType`.

The Harness should not spawn MCP directly. A read-only task-api facade has now been added:

`GET /api/v1/swtr-read/tasks/{task_code}/files`

It calls only MCP `get_unit_files` with `safe=True`; it does not download content and exposes no write tools. `TaskApiAS21Adapter.get_attachment_metadata()` now maps this response into canonical `Attachment` objects. Source readiness is intentionally NOT yet upgraded to advertise `attachments` until the new path passes real QA.

### Comments/history — PARTIAL
`MCP get_unit_comments` is real and read-only, but comments are not status-transition history. We must not map comments into `StatusTransition` or claim cycle-time history from them.

`TASK_HISTORY_AVAILABLE = PARTIAL_COMMENTS_ONLY`.

### Sprint — PARTIAL
Task-to-sprint relation uses `scrum_board_plugin_sprint` when populated. MCP sprint tools exist, but `get_current_sprint` currently fails with `Invalid request parameters`, so the current-sprint contract is not yet green.

### Release — PARTIAL
`fix_version_s` is the task-side relation family. MCP `search_versions` exists and is the candidate release catalog source. A populated real release example is still required before release-health acceptance.

## Current implementation boundary

```text
Harness
  -> TaskApiAS21Adapter
       -> /api/v1/tasks                 # base task facts/filtering
       -> /api/v1/swtr-read/.../files   # rich attachment metadata, read-only
             -> SWTRSyncService
                  -> MCP get_unit_files
```

This composition is preferred to launching MCP subprocesses inside Harness. task-api owns SWTR/MCP transport and credentials; Harness receives deterministic read-only facts.

## Closed defects
1. ignored `q` broadening search — FIXED + real-tested;
2. missing externalId/login identity — FIXED + real-tested;
3. missing project_space — FIXED + real-tested;
4. unknown status -> Open false mapping — FIXED;
5. artificial 10k description limit — FIXED + real-tested.

## Remaining A3 work
1. Real-test `/api/v1/swtr-read/tasks/WMB-30000/files` and canonical attachment mapping.
2. Only after real proof, add `attachments` to `TaskApiAS21Adapter.source_facts`.
3. Determine safe canonical use of comments for task-quality evidence without mislabeling them as status history.
4. Fix/discover correct current-sprint MCP request contract or explicitly approve a task-attribute-based sprint policy.
5. Capture a populated release/version example through `search_versions` / `fix_version_s`.
6. Decide metric policy for `sprint_health`/`velocity` if no status-transition history exists.

## Gate state

`BASE_TASK_FILTER_CONTRACT = GREEN`  
`A2 = DONE`  
`ATTACHMENT_SOURCE_DISCOVERY = PROVEN_REAL`  
`ATTACHMENT_HARNESS_WIRING = IMPLEMENTED, REAL RETEST PENDING`  
`COMMENTS_SOURCE = PROVEN_REAL`  
`STATUS_TRANSITION_HISTORY = UNPROVEN`  
`SPRINT_SOURCE_CONTRACT = PARTIAL`  
`RELEASE_SOURCE_CONTRACT = PARTIAL`  
`GATE_A = YELLOW`  
`READY_FOR_LEARNING_LOOP = NO`  
`NEXT = AS21-A3-ATTACHMENT-WIRING-RETEST-005`
