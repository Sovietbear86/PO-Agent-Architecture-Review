# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_139_ASSIGNEE_LIVE_ROUTE_FOCUSED_AB`

## Mission
Assignment 138 proved the assignee failure is a product integration defect, not an AS21 outage: `search_users` now requires its search DTO under a top-level `request` argument. Owner commit `5ce78840ecc9553c0f1f062922a8a0d26fe9ae58` fixes `task-api/app/routers/swtr_assignee.py::_resolve_external_id()` to call:

```python
{"request": {"text_search": needle, "page": 0, "size": 100}}
```

Your job is to certify this fix end-to-end against independent REAL AS21 Oracle B. QA only: do not modify production code.

## Absolute rules
- Pull `feat/core8-real-query-hardening-v2` and prove HEAD contains owner commit `5ce78840ecc9553c0f1f062922a8a0d26fe9ae58`.
- Hard restart Task API and Harness from current HEAD.
- REAL MCP-SWTR only; no local DB/sync/fake/mock/frozen truth.
- Oracle B must independently call MCP `search_users` and `find_units_by_filter` directly.
- Fresh unique session ID per Agent A case.
- Concurrency=1; normal timeout 180s; retry transient transport failures twice with 30s backoff.
- Do not run the full skill catalog.

# PHASE 0 — source and schema health
1. Record HEAD, worktree status, Task API/Harness PIDs and restart commands.
2. Prove `search_users` current schema still requires `request` wrapper.
3. Prove two known-good REAL `read_unit` calls from different approved spaces.

# PHASE 1 — direct Task API assignee route
For each canonical person identity below, first resolve the actual canonical identifier using direct MCP `search_users` with the live schema, then call Task API `/api/v1/swtr-read/assignee-tasks`:
- Garanin (`Garanin.R.V` / repository-configured identity)
- Kalachanov (derive exact repository-configured identity; do not guess spelling/login)

For Garanin additionally test `space=DMS`.

Capture Task API HTTP status, `external_id`, count, pages_read and exact returned task-key set.

Acceptance: no 409/502 caused by `search_users` DTO shape.

# PHASE 2 — independent Oracle B exact parity
For the same authoritative IDs, bypass Task API and execute direct REAL MCP `find_units_by_filter` using server-side `assigned_to` filter. Read all pages and normalize only approved spaces WMB/STS/OLP/DMS/CRPV.

Compare:
```text
set(TaskAPI_Garanin.keys) == set(OracleB_Garanin.keys)
set(TaskAPI_Garanin_DMS.keys) == set(OracleB_Garanin_DMS.keys)
set(TaskAPI_Kalachanov.keys) == set(OracleB_Kalachanov.keys)
```

Count-only equality is insufficient.

# PHASE 3 — Agent A natural-language path
Fresh sessions:
- `Задачи Гаранина`
- `Задачи Гаранина в DMS`
- `Задачи Калачанова`

For each capture:
```text
INTERPRETER_CLASS
LLM_USED
RAW_SEMANTIC_FRAME
GROUNDED_FRAME
RESOLVED_SKILL
CAPABILITY_ARGS
SOURCE_ROUTE
AGENT_STATUS
TASK_KEYS
ANSWER
```

Require exact key-set equality Agent A vs Oracle B where task collection is returned.

# PHASE 4 — protected exact-task cluster
Ensure previous fixes remain GREEN:
- existing `DMS-380` -> Task API 200 and Agent exact key;
- nonexistent `DMS-999999999` -> Task API 404 and Agent says task not found, not source unavailable.

# PHASE 5 — regression semantics
Verify:
- Russian query -> Russian answer;
- first turn is not correction/recheck;
- no local DB/sync used as authoritative source;
- no AS21 writes;
- exact `search_users -> find_units_by_filter` live source route is visible for assignee search.

# Final report
Write:
`po-agent-platform-v2/qa_reports/ASSIGNEE_LIVE_ROUTE_FOCUSED_AB_139.md`

Allowed verdicts:
- `ASSIGNEE_LIVE_ROUTE_GREEN`
- `ASSIGNEE_IDENTITY_STILL_RED`
- `ASSIGNEE_TASK_PARITY_RED`
- `PROTECTED_EXACT_TASK_REGRESSION_RED`
- `BLOCKED_BY_ENVIRONMENT`

`ASSIGNEE_LIVE_ROUTE_GREEN` requires all three Agent A queries to match independent Oracle B exact key sets and no request-wrapper error.

Commit/push QA artifacts only and STOP.

## Start now
Execute Assignment 139 autonomously.