# Core-8 AS21 Source Contract Inventory

**Roadmap step:** A1 complete / A2 fixes implemented / A2 real retest pending  
**Status:** FILTER TRANSPORT FIXED; LONG-DESCRIPTION BLOCKER FIXED; REAL RETEST REQUIRED

## Core eight
`task_search`, `task_summary`, `task_quality`, `sprint_health`, `velocity`, `team_workload`, `competency_match`, `release_health`.

## Proven real AS21 facts
From QA assignments `AS21-A2-REAL-CONTRACT-DISCOVERY-001` and `AS21-A2-FILTER-RETEST-002`:

- local task-api is reachable and returns real SWTR-backed tasks;
- real WMB assignment identity is present in `source_data.swtr_attributes[code=assigned_to].value.externalId/login`;
- `WMB-30000` mapped `assignee_id = Kalachanov.V.V` and `assignee_login = kalachanov.v.v` correctly;
- authoritative project/space source is `source_data.swtr_space` (example `WMB`), not merely task-key prefix;
- sprint attribute code exists as `scrum_board_plugin_sprint`, but no populated real value has yet been captured;
- release attribute code exists as `fix_version_s`, but no populated real value has yet been captured;
- current task-api adapter boundary does not expose attachment metadata or task history;
- task-api `/api/v1/tasks` supports `status`, `assignee`, `source`, `limit`, `offset` and does **not** support `q`;
- real AS21 descriptions can exceed 10,000 characters, so a canonical 10k description cap is incompatible with the source contract.

## QA blockers discovered and resolved in code

### 1. Ignored `q` parameter caused broad false-positive search
The previous adapter sent `q=<query>` to task-api. FastAPI ignored the unsupported parameter and returned a broad corpus. This was fixed by removing `q`, parsing the bounded Harness query grammar and applying deterministic canonical filtering.

### 2. Canonical description limit blocked the entire real corpus
Retest `AS21-A2-FILTER-RETEST-002` showed that the adapter scans a bounded real corpus before local filtering, and at least one real AS21 task has a description longer than 10,000 characters. Pydantic therefore raised a validation error before any filter could be evaluated.

**Resolution:** canonical `Task.description` no longer imposes an arbitrary source-incompatible 10k limit. The full source description is preserved. We intentionally do **not** truncate and do **not** skip long tasks because `task_summary` and `task_quality` require complete grounded source text.

## A2 behavior now implemented

1. `TaskApiAS21Adapter` never sends ignored `q`.
2. Bounded equality/`AND` grammar is parsed deterministically.
3. Unknown fields/malformed clauses fail closed.
4. Stable assignee matching uses canonical `assignee_id`, `assignee_login` and display name.
5. `source` remains a proven task-api native filter.
6. `project_space` maps from proven `source_data.swtr_space`.
7. task-api `todo`, `in_progress`, `done` normalize to Open/In progress/Closed; truly unknown values remain `TaskStatus.UNKNOWN` with `status_raw` preserved.
8. sprint mapping uses task-api derived `sprint` when present, otherwise conservatively inspects `scrum_board_plugin_sprint`.
9. release mapping conservatively inspects `fix_version_s`; non-empty real evidence is still required.
10. exact-key, assignee, status, project, sprint and release selection all use deterministic canonical matching.
11. full AS21 task descriptions are preserved without truncation or silent task dropping.
12. regression coverage includes a 25,000-character real-shaped description.

## Remaining blockers / gaps

### A. Real filter retest after long-description fix
Must prove exact task, assignee, project and status behavior on the real task-api corpus. Unit/MockTransport tests are insufficient.

### B. Sprint real non-empty sample
Need at least one populated `scrum_board_plugin_sprint`/derived `sprint` example to freeze the identifier contract.

### C. Release real non-empty sample
Need a non-empty `fix_version_s` example to freeze the release identifier contract.

### D. Attachments
No proven attachment metadata path through current task-api adapter. Attachment-dependent skills remain blocked until a read-only source is discovered/wired.

### E. History
No proven status-history path through current task-api adapter. Flow metrics requiring transitions remain blocked until a read-only source is discovered/wired.

## Gate

`GATE_A = RED UNTIL REAL FILTER RETEST`  
`ASSIGNEE_ID_MAPPING = PROVEN`  
`Q_PARAMETER_BUG = FIXED`  
`LONG_DESCRIPTION_BLOCKER = FIXED IN CODE; REAL RETEST PENDING`  
`PROJECT_SPACE_MAPPING = IMPLEMENTED FROM PROVEN SOURCE`  
`TASK_API_STATUS_NORMALIZATION = IMPLEMENTED`  
`SPRINT_NONEMPTY_CONTRACT = UNPROVEN`  
`RELEASE_NONEMPTY_CONTRACT = UNPROVEN`  
`ATTACHMENT_METADATA = NOT AVAILABLE VIA CURRENT TASK-API ADAPTER`  
`TASK_HISTORY = NOT AVAILABLE VIA CURRENT TASK-API ADAPTER`  
`READY_FOR_LEARNING_LOOP = NO`  
`NEXT = AS21-A2-FILTER-RETEST-003`
