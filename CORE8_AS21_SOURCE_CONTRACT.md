# Core-8 AS21 Source Contract Inventory

**Roadmap step:** A1 complete / A2 in progress  
**Status:** DETERMINISTIC IDENTITY + STATUS FIX IMPLEMENTED; REAL CONTRACT DISCOVERY STILL REQUIRED

## Core eight
`task_search`, `task_summary`, `task_quality`, `sprint_health`, `velocity`, `team_workload`, `competency_match`, `release_health`.

## A1 findings
The production path is `AS21/SWTR -> task-api -> TaskApiAS21Adapter -> canonical Task -> Harness`. The old implementation delegated mapping to `LegacyAS21Bridge`; that lost identity and relationship facts and silently mapped unknown statuses to OPEN.

Observed real assignment structure for WMB data:
`source_data.swtr_attributes[code=assigned_to].value.externalId/login/name`.

## A2 implemented
- `Task` now has `assignee_login`, `project_space`, `status_raw` and diagnostic `source_data` in addition to existing `assignee_id`, `sprint_id`, `release_id`.
- `TaskStatus.UNKNOWN` is explicit. Unknown raw AS21 status no longer becomes OPEN.
- `TaskApiAS21Adapter` owns its mapping rather than calling the permissive legacy mapper.
- observed `assigned_to.value.externalId` maps to `assignee_id` and `value.login` to `assignee_login`.
- sanitized raw `source_data` is retained at the canonical boundary for evidence/schema discovery; skills must not parse it ad hoc.
- adapter no longer advertises sprint/release facts as proven merely because it can construct a query-like string.
- `get_sprint_tasks`, `get_release_tasks`, history and attachment access fail explicitly until their actual read contracts are proven.
- regression tests cover the observed real-shaped assignee payload, unknown status, exact-key behavior, transport/protocol failure and unproven capability boundaries.

## Deliberately NOT guessed
We have not invented mappings for:
- sprint (`scrum_board_plugin_sprint` remains a hypothesis until a real payload is inspected);
- release (`fix_version_s` remains a hypothesis until a real payload is inspected);
- project/space;
- attachments;
- history.

This is intentional: source schema truth comes from real read-only AS21 evidence, not naming conventions or prompts.

## Remaining A2 work
1. Run the updated adapter tests in the actual repository environment.
2. Read bounded real task-api samples containing sprint/release/project fields.
3. Record sanitized shapes/codes and then add typed central extractors.
4. Prove attachment/history read paths or keep dependent checks BLOCKED/NOT_APPLICABLE.
5. Run production regression.
6. Proceed to A3 only after these are evidenced.

## Gate
`GATE_A = YELLOW`  
`ASSIGNEE_MAPPING = IMPLEMENTED, TEST EXECUTION PENDING`  
`UNKNOWN_STATUS_SAFETY = IMPLEMENTED, TEST EXECUTION PENDING`  
`SPRINT/RELEASE/PROJECT = UNPROVEN`  
`ATTACHMENT/HISTORY = UNPROVEN`  
`READY_FOR_LEARNING_LOOP = NO`  
`NEXT = GigaCode test/review of A2 + bounded real contract discovery`
