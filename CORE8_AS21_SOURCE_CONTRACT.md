# Core-8 AS21 Source Contract Inventory

**Roadmap step:** A1  
**Status:** COMPLETE WITH BLOCKERS FOUND  
**Scope:** fields/contracts required before real-AS21 acceptance of the eight core domain skills.

## 1. Core eight

`task_search`, `task_summary`, `task_quality`, `sprint_health`, `velocity`, `team_workload`, `competency_match`, `release_health`.

## 2. Current architecture path

```text
AS21/SWTR
 -> existing task-api on localhost:8003
 -> TaskApiAS21Adapter
 -> LegacyAS21Bridge._map_fastapi_task()
 -> canonical Task
 -> Harness capabilities/skills
```

`TaskApiAS21Adapter` is fail-closed for transport/protocol errors, but currently delegates canonical mapping to `LegacyAS21Bridge._map_fastapi_task()`.

## 3. Current canonical Task fields relevant to Core-8

Present in `domain/models.py`:
- key / id
- title / description
- status / status_category / status_transitions
- assignee / assignee_id
- created_at / updated_at / due_date / resolved_at / closed_at
- priority
- estimate_hours / time_spent_hours
- sprint_id / release_id / parent_key / depends_on
- labels / components
- attachments
- source / source_url

### Missing/insufficient for diagnostics and filtering
- raw/sanitized `source_data` is not retained in canonical Task;
- no explicit project/space field exists on Task;
- current mapper does not populate `assignee_id`, `sprint_id`, `release_id`, effort, components, attachments or dependencies from task-api `source_data`;
- task history and attachment metadata are explicitly unsupported by TaskApiAS21Adapter.

## 4. Real AS21 evidence already observed

For real task `WMB-30000`, the task-api payload contains user assignment metadata in:

```text
source_data.swtr_attributes[]
  code = "assigned_to"
  value.externalId = "Kalachanov.V.V"
  value.firstName = "Виктор"
  value.lastName = "Калачанов"
  value.middleName = "Вячеславович"
  value.login = "kalachanov.v.v"
```

The visible display assignee can be populated while canonical `assignee_id` remains empty. Therefore filtering by canonical assignee id/login fails even though the task exists.

Known AS21 attribute families that must be verified from real payloads rather than guessed:
- assignee/user: observed `assigned_to`;
- sprint: expected/previously referenced `scrum_board_plugin_sprint`, structure still must be verified against real payload;
- release: expected/previously referenced `fix_version_s`, structure still must be verified against real payload;
- workflow status: task-api exposes top-level status and/or `source_data.workflow_status`;
- project/space: must be verified from real task-api payload/source identity;
- attachment metadata: current task-api contract does not yet expose it through this adapter.

## 5. Source contract per skill

| Skill | Required contract before GREEN |
|---|---|
| task_search | key, title/description, assignee_id/login, status, sprint_id, release_id, project/space, bounded search/filter semantics |
| task_summary | title, description and any referenced acceptance/attachment/link facts; source evidence |
| task_quality | description and deterministic requirement/acceptance fields used by scoring policy |
| sprint_health | sprint_id, normalized status, dates/history needed by formulas, assignee, effort/scope fields |
| velocity | sprint_id, completed-state semantics, estimate/task-count policy, sprint dates |
| team_workload | assignee_id/login, active/WIP/blocked status, sprint/project, effort when used |
| competency_match | task text/type/components/labels plus approved competency config |
| release_health | release_id, status, scope/project, dependencies/blocked indicators, dates |

## 6. Blockers found in A1

### BLOCKER A1-1 — assignee identity is not mapped
`LegacyAS21Bridge._map_fastapi_task()` sets `assignee=data.get("assignee")` but never sets canonical `assignee_id` from real `swtr_attributes[].value.externalId/login`.

Impact:
- real assignee filter can return zero for existing tasks;
- `task_search` and `team_workload` cannot pass real-data acceptance;
- learning loop must not attempt to learn around this deterministic mapper bug.

### BLOCKER A1-2 — sprint/release are present in canonical model but mapper does not populate them
The mapper currently leaves `sprint_id` and `release_id` at defaults. Real attribute codes/structures must be confirmed and then mapped centrally.

Impact:
- sprint/release filters can false-empty;
- `sprint_health`, `velocity`, `release_health` cannot be trusted.

### BLOCKER A1-3 — project/space is not represented canonically
Core search and analytics require a stable project/space identity. Determine actual source field and either add a canonical field or a dedicated typed context entity; do not infer solely from prose.

### BLOCKER A1-4 — attachments/history contract incomplete
`TaskApiAS21Adapter.get_attachment_metadata()` and `get_task_history()` intentionally fail with `AS21CapabilityUnavailable`. This is correct fail-closed behavior, but attachment-dependent and history-dependent skills cannot be marked GREEN until a proven read-only source is wired.

### HIGH A1-5 — unknown status defaults to OPEN in legacy parser
`_parse_swtr_status()` currently uses `TaskStatus.OPEN` as fallback. Unknown real status therefore risks false-green interpretation as backlog/open rather than explicit unknown/failure.

## 7. Required A2 implementation order

1. Add centralized helpers to extract typed values from real `swtr_attributes`.
2. Fix assignee display + id/login mapping from observed `assigned_to` structure.
3. Change unknown status handling so unmapped real statuses cannot silently become OPEN.
4. Verify and map real sprint attribute structure.
5. Verify and map real release attribute structure.
6. Verify project/space source and represent it canonically.
7. Retain sanitized source_data (or equivalent diagnostic evidence) without spreading raw parsing into skills.
8. Add tests using sanitized shapes copied from real task-api responses.
9. Run adapter + production regression before real filter matrix.
10. Only then proceed to STEP A3 real key/assignee/status/sprint/project/release combinations.

## 8. Gate decision

`GATE_A = RED/YELLOW — deterministic source-contract fixes required.`

`READY_FOR_LEARNING_LOOP = NO`  
`READY_FOR_CORE8_REAL_AS21 = NO`  
`NEXT = STEP A2`
