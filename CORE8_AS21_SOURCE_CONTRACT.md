# Core-8 AS21 Source Contract Inventory

**Roadmap step:** A1 complete / A2 fix implemented / A2 retest pending  
**Status:** ASSIGNEE MAPPING PROVEN; FILTER TRANSPORT BUG FIXED; REAL RETEST REQUIRED

## Core eight
`task_search`, `task_summary`, `task_quality`, `sprint_health`, `velocity`, `team_workload`, `competency_match`, `release_health`.

## Proven real AS21 facts
From QA assignment `AS21-A2-REAL-CONTRACT-DISCOVERY-001`:

- local task-api is reachable and returns real SWTR-backed tasks;
- real WMB assignment identity is present in `source_data.swtr_attributes[code=assigned_to].value.externalId/login`;
- `WMB-30000` mapped `assignee_id = Kalachanov.V.V` and `assignee_login = kalachanov.v.v` correctly;
- authoritative project/space source is `source_data.swtr_space` (example `WMB`), not merely task-key prefix;
- sprint attribute code exists as `scrum_board_plugin_sprint`, but the inspected sample had `null` values;
- release attribute code exists as `fix_version_s`, but the inspected sample had empty lists;
- current task-api adapter boundary does not expose attachment metadata or task history;
- task-api `/api/v1/tasks` supports `status`, `assignee`, `source`, `limit`, `offset` and does **not** support `q`.

## QA blocker discovered
The previous production adapter sent `q=<query>` to task-api. FastAPI ignored the unsupported parameter and returned a broad corpus, so queries such as:

- `assignee = Kalachanov.V.V`
- `assignee = Ivanov.I.I`
- `assignee = nonexistent`

all returned the same 50-task set.

This was a deterministic source-contract blocker, not a learning-loop problem.

## A2 fixes now implemented

1. `TaskApiAS21Adapter` no longer sends `q` to task-api.
2. The adapter explicitly parses a bounded equality/`AND` grammar for Harness search fields.
3. Unknown search fields and malformed clauses fail closed.
4. Stable assignee matching is done against canonical `assignee_id`, `assignee_login` and display name after a bounded source read, because task-api's native `assignee` filter is based on display name and cannot safely resolve AS21 externalId/login.
5. `source` remains a proven source-side filter.
6. `project_space` is mapped from proven `source_data.swtr_space`.
7. task-api native statuses `todo`, `in_progress`, `done` are normalized respectively to canonical Open/In progress/Closed; truly unknown values remain `TaskStatus.UNKNOWN` with `status_raw` preserved.
8. sprint mapping uses the task-api derived `sprint` field when present, otherwise conservatively inspects `scrum_board_plugin_sprint`.
9. release mapping conservatively inspects `fix_version_s`; a real non-empty release sample is still required before declaring the release contract GREEN.
10. `get_sprint_tasks` / `get_release_tasks` now reuse the same deterministic canonical filter path instead of emulating JQL through an ignored source parameter.
11. exact-key lookup scans the documented bounded task-api read facade and matches canonical key exactly.
12. regression tests now explicitly prove that `q` is absent, nonexistent assignee cannot broaden results, and project/status/sprint/release canonical filtering is deterministic.

## Remaining blockers / gaps

### A. Real filter retest
The new implementation must be retested against real task-api. Gate A cannot rely on unit tests alone.

### B. Sprint real non-empty sample
Attribute code is known, but no populated sample was found in the first 50 tasks. We still need a real sprint-bearing task to prove identifier shape.

### C. Release real non-empty sample
`fix_version_s` exists but was empty in the sample. We still need a real release-bearing task to prove identifier shape.

### D. Attachments
Current task-api boundary exposes no attachment metadata through `TaskApiAS21Adapter`. We must inspect legacy SWTR/MCP read capabilities before attachment-dependent skill acceptance.

### E. History
Current task-api boundary exposes no status history. Sprint flow metrics that require transitions/cycle-time history remain blocked until a proven read-only source is wired.

## Gate

`GATE_A = YELLOW/RED UNTIL REAL RETEST`  
`ASSIGNEE_ID_MAPPING = PROVEN`  
`ASSIGNEE_FILTER_FIX = IMPLEMENTED, REAL RETEST PENDING`  
`PROJECT_SPACE_MAPPING = IMPLEMENTED FROM PROVEN SOURCE`  
`TASK_API_STATUS_NORMALIZATION = IMPLEMENTED`  
`SPRINT_NONEMPTY_CONTRACT = UNPROVEN`  
`RELEASE_NONEMPTY_CONTRACT = UNPROVEN`  
`ATTACHMENT_METADATA = NOT AVAILABLE VIA CURRENT TASK-API ADAPTER`  
`TASK_HISTORY = NOT AVAILABLE VIA CURRENT TASK-API ADAPTER`  
`READY_FOR_LEARNING_LOOP = NO`  
`NEXT = AS21-A2-FILTER-RETEST-002`
