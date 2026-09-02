# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_128_CLEAN_RUNTIME_PRODUCTION_ADAPTER_PROOF`

## Why this assignment exists
Assignment 127 proved that the REAL AS21 live assignee boundary is healthy: `/api/v1/swtr-read/assignee-tasks` returned real tasks, while the running Harness returned zero. However, the current Git implementation of `ProductionTaskApiAS21Adapter.search_tasks()` already contains assignee routing to `/api/v1/swtr-read/assignee-tasks`. Therefore do NOT implement that routing again. First prove which adapter implementation the running Harness actually loaded.

## Role boundary
You are QA/test executor only. Do NOT modify production code, prompts, skills, adapters, Task API, MCP-SWTR, team configuration, AS21 data, testing rules, or this file. Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`.

## Absolute prohibitions
- NO production fixes in Assignment 128.
- NO merge/cherry-pick/revert of production code.
- NO local DB synchronization/population.
- NO local DB/cache as Agent source or Oracle.
- NO fake/mock/frozen/historical truth.
- NO AS21 writes.
- NO Harness/Agent as Oracle B.
- NO unrelated employees or spaces outside approved scope.
- NO 54-skill marathon yet.
- HTTP 200/COMPLETED alone is never PASS.

## Goal
Prove whether the current failure is caused by stale/wrong runtime adapter selection or by a later production boundary. Then perform TRUE live A/B equality for the assignee path.

A = freshly restarted production Harness from exact current HEAD.
B = independent REAL AS21 Oracle.

Globally approved spaces only:
`WMB, STS, OLP, DMS, CRPV`.

## Phase 0 — clean provenance
1. Pull latest `feat/core8-real-query-hardening-v2`.
2. Record exact HEAD and `git status`.
3. Production worktree must be CLEAN.
4. If any uncommitted production changes exist, STOP with verdict `BLOCKED_BY_DIRTY_PROVENANCE`; list them. Do not delete, stash, commit, or modify them.
5. Do not reuse old runtime results as current evidence.

## Phase 1 — hard runtime restart
1. Discover all currently running Task API and Harness processes and record old PIDs/start times.
2. Stop all old Task API/Harness processes.
3. Prove old PIDs no longer exist and required ports are free.
4. Start Task API and Harness again from the exact Phase-0 HEAD.
5. Record new PIDs/start times and working directories/commands.
6. Verify Task API health, Harness health, MCP-SWTR health and REAL AS21 availability.
7. If source is temporarily unavailable: retry up to 2 times, 20–30 sec backoff, timeout >=120 sec.

## Phase 2 — runtime adapter identity proof
Prove with runtime introspection/evidence, not assumption:
1. Which `runtime_factory/build_runtime_bundle` the running Harness uses.
2. Exact concrete adapter instance/class used for task search:
   - `ProductionTaskApiAS21Adapter`, or
   - `TaskApiAS21Adapter`, or
   - another class.
3. Capture:
   - class name;
   - module name;
   - loaded source file path;
   - loaded `search_tasks` implementation/source location;
   - runtime working directory/PYTHONPATH if relevant.
4. Compare the loaded production adapter file to current Git HEAD.

Do not edit production code to add diagnostics. Use existing logs, Python introspection, process information, or read-only debug execution.

Critical known fact to verify: current Git `ProductionTaskApiAS21Adapter.search_tasks()` is expected to detect an `assignee` filter and call `/api/v1/swtr-read/assignee-tasks` rather than `/api/v1/tasks`.

## Phase 3 — fresh independent Oracle B
Rebuild Oracle B from scratch from REAL AS21. Do not copy Assignment 127 counts as expected truth.

For Garanin:
`search_users -> exact Garanin.R.V externalId -> find_units_by_filter(query='assigned_to = "<externalId>"') -> complete pagination`

Filter results only to approved spaces `WMB, STS, OLP, DMS, CRPV`.

Capture exact:
- `B_GARANIN_ALL_APPROVED_KEYS`;
- `B_GARANIN_DMS_KEYS`;
- `B_GARANIN_OLP_KEYS`;
- all returned spaces/counts;
- excluded outside-scope keys if any;
- raw source/evidence references.

## Phase 4 — direct live Task API boundary
From the same fresh environment call:
`GET /api/v1/swtr-read/assignee-tasks?assignee=Garanin.R.V`

Capture source, route, external_id, count, exact keys, spaces, pages_read, elapsed.

Required invariant:
`TaskApiLiveKeys == B_GARANIN_ALL_APPROVED_KEYS`.

Also test `space=DMS` and `space=OLP` against the corresponding Oracle subsets.

If this boundary mismatches, identify it explicitly; do not blame Harness routing first.

## Phase 5 — actual fresh Harness A
Fresh session, natural query:
`Задачи Гаранина`

Capture:
- status;
- intent;
- skill/version;
- resolved member/externalId;
- capability args;
- concrete adapter class;
- ACTUAL downstream HTTP endpoint called by adapter;
- source/evidence;
- exact returned task keys;
- answer;
- elapsed.

Critical assert for assignee search:
actual downstream endpoint MUST be `/api/v1/swtr-read/assignee-tasks`, NOT `/api/v1/tasks`.

Required A/B invariant:
`A_GENERIC_KEYS == B_GARANIN_ALL_APPROVED_KEYS`.

A zero result is FAIL if independent Oracle B is non-zero.

## Phase 6 — explicit-space A/B controls
Fresh sessions:
1. `Задачи Гаранина в DMS`
2. `Задачи Гаранина в OLP`

For each capture exact A keys, exact B keys, selected skill/args, downstream endpoint and equality.

Do not ask needless clarification when member and explicit space are already unambiguous.

## Phase 7 — deterministic repeat
Only if generic + DMS + OLP pass once, repeat all three once more in fresh sessions.

Required:
- same exact key sets;
- same live source route;
- no local/cache fallback;
- no new clarification/regression.

## Phase 8 — first failing boundary
If mismatch remains, identify exactly the earliest incorrect boundary and show last-correct + first-incorrect artifacts.

Preferred classifications:

### `RUNTIME_FACTORY_ADAPTER_SELECTION`
Running Harness constructs `TaskApiAS21Adapter`/other adapter instead of `ProductionTaskApiAS21Adapter`.

### `LOADED_IMPLEMENTATION_MISMATCH`
Runtime claims production adapter but loaded module/file/search_tasks differs from current HEAD.

### `ADAPTER_ROUTING`
Current production adapter is loaded, but actual assignee execution still calls `/api/v1/tasks` instead of live assignee facade.

### `ADAPTER_MAPPING_OR_FILTERING`
Live endpoint returns correct tasks and adapter receives them, but mapping/filtering loses or changes them.

### `CAPABILITY_RESULT_PROPAGATION`
Adapter returns correct exact keys but capability/Harness loses or changes them above the adapter.

### `SEMANTIC_OR_ARGUMENT_BUILDING`
Natural query resolves wrong member/space/skill/capability arguments before adapter execution.

### `TASK_API_LIVE_ASSIGNEE_FACADE`
Direct Task API live result differs from independent REAL AS21 Oracle.

Do not infer a code change. Assignment 128 is diagnosis/certification only.

## Phase 9 — anti-surrogate gate
Every item must be YES for any GREEN:
- exact current HEAD recorded;
- clean production worktree;
- old processes killed;
- new PIDs/start times proven;
- runtime concrete adapter class proven;
- loaded module/file proven;
- independent Oracle B direct to REAL AS21;
- complete Oracle pagination;
- exact task-key sets captured;
- actual downstream endpoint captured;
- Task API live facade compared independently;
- Harness compared by exact-key equality;
- no local DB/sync/cache/fake/mock/frozen truth;
- approved spaces only;
- AS21 writes = 0.

## Allowed final verdicts ONLY
- `STALE_RUNTIME_PROVEN_AND_PARITY_GREEN`
- `RUNTIME_FACTORY_ADAPTER_SELECTION_DEFECT`
- `LOADED_IMPLEMENTATION_MISMATCH`
- `ADAPTER_ROUTING_DEFECT`
- `ADAPTER_MAPPING_OR_FILTERING_DEFECT`
- `CAPABILITY_RESULT_PROPAGATION_DEFECT`
- `SEMANTIC_OR_ARGUMENT_BUILDING_DEFECT`
- `TASK_API_LIVE_ASSIGNEE_FACADE_DEFECT`
- `REAL_SOURCE_CHANGED_OR_UNAVAILABLE`
- `BLOCKED_BY_DIRTY_PROVENANCE`

No other GREEN is allowed.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/CLEAN_RUNTIME_PRODUCTION_ADAPTER_PROOF_128.md`

Optional raw evidence prefix:
`CLEAN_RUNTIME_PRODUCTION_ADAPTER_PROOF_128_`

## Finish
Commit/push only QA report/raw QA evidence. Do not change production code. Provide report path, full SHA, verdict, then STOP.

## Start when instructed
Execute Assignment 128 autonomously and strictly as written.