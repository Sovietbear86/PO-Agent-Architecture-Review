# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_127_POST_FIX_LIVE_ASSIGNEE_AB`

## Owner fix under test
Current branch now contains an owner production fix that restores live assignee search without local synchronization:

1. Task API route: `GET /api/v1/swtr-read/assignee-tasks`
2. Route implementation: `search_users -> externalId -> find_units_by_filter(assigned_to = externalId) -> complete pagination`
3. Only globally approved spaces are allowed: `WMB, STS, OLP, DMS, CRPV`
4. Harness `ProductionTaskApiAS21Adapter.search_tasks()` routes assignee filters to this live REAL AS21 facade instead of `/api/v1/tasks` local/cache scan.

Important scope correction: do NOT use a team member's `products:` field as the authoritative task-search scope for the generic query `Задачи <сотрудника>`. We have owner evidence that team members may have valid tasks in other approved spaces. Generic assignee search must compare against ALL globally approved spaces. Explicit `... в DMS` / `... в OLP` queries are separately scoped.

## Role boundary
You are QA/test executor only. Do NOT modify production code, prompts, skills, adapters, Task API, MCP-SWTR, team configuration, AS21 data, or this file. Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`.

## Absolute prohibitions
- NO local DB synchronization/population.
- NO local DB/cache as Oracle or Agent source.
- NO fake/mock/frozen/historical truth.
- NO AS21 writes.
- NO Agent/Harness as Oracle B.
- NO product/member hardcoding in test logic.
- NO 54-skill marathon yet.
- HTTP 200/COMPLETED alone is never PASS.

## Goal
Certify the owner fix with TRUE live A/B equality for assignee search and determine whether the agent is usable again for this core path.

A = current production Harness/Agent after full service restart from current HEAD.
B = independent REAL AS21 Oracle using direct MCP-SWTR reads only.

## Phase 0 — exact provenance and fresh runtime
1. Pull latest `feat/core8-real-query-hardening-v2`.
2. Record exact HEAD and clean worktree.
3. Restart Task API and Harness from that exact HEAD. Do not reuse stale processes.
4. Record PIDs/start times.
5. Verify Task API health and `/api/v1/swtr-read/health`.
6. Verify new `/api/v1/swtr-read/assignee-tasks` route is registered.
7. Local DB/sync/cache/fake/mock usage for this assignment = 0. AS21 writes = 0.

If AS21/MCP is temporarily unavailable, retry up to 2 times with 20–30 sec backoff; timeout >=120 sec. Environment failure is not a product FAIL without retest.

## Phase 1 — independent Oracle B for Garanin
Rebuild from scratch via direct MCP-SWTR, NOT through Task API/Harness:

`search_users -> exact Garanin.R.V externalId -> find_units_by_filter(query='assigned_to = "<externalId>"') -> all pages`

Capture every returned task key and space.

Generic Oracle scope = only globally approved spaces:
`WMB, STS, OLP, DMS, CRPV`

Produce exact sets:
- `B_GARANIN_ALL_APPROVED_KEYS`
- `B_GARANIN_DMS_KEYS`
- `B_GARANIN_OLP_KEYS`
- other approved-space subsets if present (including STS/WMB/CRPV)
- excluded keys outside the five approved spaces

Do NOT discard STS/WMB/CRPV merely because `team_members.yaml products` omits them.

## Phase 2 — Task API live facade proof
Call the new owner route directly:
`GET /api/v1/swtr-read/assignee-tasks?assignee=Garanin.R.V`

Capture:
- source/route fields;
- exact task-key set;
- spaces;
- external_id;
- pages_read;
- elapsed time.

Required invariant:
`TaskApiLiveKeys == B_GARANIN_ALL_APPROVED_KEYS`

Then call with `space=DMS` and `space=OLP` and compare exact keys to Oracle subsets.

If this boundary mismatches, STOP functional Harness analysis and identify `TASK_API_LIVE_ASSIGNEE_FACADE` as first failing boundary.

## Phase 3 — Harness A generic query
Fresh session, exact natural query:
`Задачи Гаранина`

Capture:
- status;
- intent/skill/version;
- semantic member identity;
- capability arguments;
- source/evidence;
- exact returned task keys;
- answer text;
- elapsed time.

Required invariant:
`A_GENERIC_KEYS == B_GARANIN_ALL_APPROVED_KEYS`

No silent narrowing to DMS/OLP is allowed for this generic query.

## Phase 4 — explicit space queries
Fresh sessions:

1. `Задачи Гаранина в DMS`
   - expected exact set = `B_GARANIN_DMS_KEYS`
   - must not ask needless clarification if `DMS` and Garanin are already unambiguous.

2. `Задачи Гаранина в OLP`
   - expected exact set = `B_GARANIN_OLP_KEYS`
   - must not ask needless clarification if `OLP` and Garanin are already unambiguous.

Capture exact parity and dialogue behavior.

## Phase 5 — mandatory real negative/control member: Kalachanov
Use `Kalachanov.V.V` as the control because owner evidence confirms he has real tasks in approved spaces including WMB/CRPV/STS.

Build Oracle B independently from REAL AS21:
`search_users -> Kalachanov externalId -> find_units_by_filter assigned_to -> all pages`

Filter ONLY to globally approved spaces WMB/STS/OLP/DMS/CRPV. Do not filter using `products: [DMS, OLP]` from current team YAML; that field is not authoritative for task-search scope.

Capture exact:
- `B_KALACHANOV_ALL_APPROVED_KEYS`
- per-space counts/keys (especially WMB, CRPV, STS)

Then fresh Harness session:
`Задачи Калачанова`

Required invariant:
`A_KALACHANOV_KEYS == B_KALACHANOV_ALL_APPROVED_KEYS`

A zero result is a FAIL if Oracle is non-zero.

## Phase 6 — exact first failing boundary
If any mismatch occurs, trace the earliest incorrect artifact. Allowed labels:
- `SEMANTIC_INTERPRETATION`
- `MEMBER_IDENTITY_RESOLUTION`
- `SPACE_SCOPE_RESOLUTION`
- `SKILL_RESOLUTION`
- `CAPABILITY_ARGUMENT_BUILDING`
- `PRODUCTION_ADAPTER_ROUTING`
- `TASK_API_LIVE_ASSIGNEE_FACADE`
- `MCP_USER_RESOLUTION`
- `MCP_TQL_QUERY`
- `SOURCE_RESPONSE_DECODING`
- `GLOBAL_SPACE_FILTERING`
- `RESPONSE_MAPPING`
- `RESPONSE_RENDERING`

Show last correct and first incorrect artifact. Do not infer root cause from count alone.

## Phase 7 — anti-surrogate gate
All must be YES for any GREEN:
- fresh current runtime from exact HEAD;
- independent Oracle B direct to REAL AS21;
- complete pagination;
- exact task-key sets captured;
- Task API live facade compared independently;
- Harness result compared by exact key equality;
- no local DB/sync/cache/fake/mock/frozen truth;
- Garanin + Kalachanov both tested;
- generic query uses all five approved spaces, not member `products` narrowing;
- AS21 writes = 0.

## Allowed verdicts
### `ASSIGNEE_CORE_PATH_RESTORED_GREEN`
All Garanin generic/DMS/OLP and Kalachanov generic exact-key invariants pass.

### `OWNER_FIX_PARTIAL_REGRESSION_REMAINS`
At least one real A/B mismatch remains; identify first failing boundary.

### `OWNER_FIX_TASK_API_BOUNDARY_FAILED`
The new Task API live facade itself differs from independent Oracle B.

### `BLOCKED_BY_ENVIRONMENT`
REAL AS21/MCP could not complete after required retries.

No other GREEN is allowed.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/POST_FIX_LIVE_ASSIGNEE_AB_127.md`

Optional raw evidence prefix:
`POST_FIX_LIVE_ASSIGNEE_AB_127_`

## Finish
Commit/push only QA report/evidence, provide full SHA, then STOP.

## Start when instructed
Execute Assignment 127 autonomously. Do not modify production code and do not synchronize/populate local task data.