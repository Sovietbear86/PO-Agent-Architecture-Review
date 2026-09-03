# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_140_ASSIGNEE_FULL_LIVE_ROUTE_AB`

## Mission
Assignment 139 proved the previous owner fix corrected `search_users`, but the same MCP-SWTR contract change also applies to `find_units_by_filter`. Owner commit `c832d442bb073f429fb82b09920be2850e721a72` now wraps the TQL request as `{"request": {...}}` in `task-api/app/routers/swtr_assignee.py`.

Certify the COMPLETE live assignee route end-to-end. QA/test executor only: do not modify production/backend/frontend code.

## Absolute rules
- Pull `feat/core8-real-query-hardening-v2`; record exact HEAD and prove it contains owner commits `5ce78840...` and `c832d442...`.
- Hard restart Task API and Harness from current HEAD.
- REAL AS21/MCP-SWTR only. No local DB, sync, fake, mock, frozen or historical task sets as truth.
- Oracle B must call MCP-SWTR directly and independently of Task API/Harness.
- Do NOT stop after proving the wrapper schema. Execute ALL phases including natural Agent A cases.
- Fresh session ID for every Agent A case.
- Concurrency=1. Timeout 180s; heavy paginated calls 300s. Retry only transient transport errors twice with 30s backoff.
- Do not run full 54-skill catalog.

# PHASE 0 — provenance and schema
1. Record HEAD/worktree and restart commands/PIDs.
2. Read live MCP tool schemas and prove BOTH calls require top-level `request`:
   - `search_users`
   - `find_units_by_filter`
3. Prove two direct `read_unit` source-health calls from different approved spaces.

# PHASE 1 — independent Oracle B FIRST
Resolve authoritative identities with direct MCP `search_users` using current schema:
- Garanin / `Garanin.R.V`
- Kalachanov: derive canonical code/login from repository config + live MCP; do not guess.

Then call direct MCP `find_units_by_filter` with current `request` wrapper and server-side `assigned_to = "<canonical>"`. Read ALL pages. Normalize exact task-key sets for approved spaces only: WMB, STS, OLP, DMS, CRPV.

Persist current live Oracle sets/counts for:
- Garanin all approved spaces
- Garanin DMS
- Kalachanov all approved spaces

# PHASE 2 — Task API parity
Call `/api/v1/swtr-read/assignee-tasks` for the same identities and Garanin+DMS.

Require:
- HTTP 200;
- correct `external_id`;
- source=`REAL_AS21`;
- route=`search_users->find_units_by_filter`;
- no request-wrapper ToolError;
- exact key-set equality with Oracle B, not just counts.

If any mismatch occurs, capture first differing keys and first failing boundary. Do not continue pretending GREEN.

# PHASE 3 — Agent A natural language
With fresh unique sessions execute ALL:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова`

Capture for each:
`INTERPRETER_CLASS`, `LLM_USED`, raw frame, grounded frame, resolved skill, capability args, source route, status, exact task keys, answer.

Acceptance:
- LLM-first path is active;
- no spurious clarification/correction state on first turn;
- exact Agent A task-key set equals Oracle B for the corresponding query;
- Russian query returns Russian answer.

# PHASE 4 — protected exact-task regression
Re-run:
- `DMS-380`: Task API point-read 200 and Agent exact key DMS-380;
- `DMS-999999999`: Task API 404 and Agent explicitly says task not found, never source unavailable.

# PHASE 5 — source integrity
Prove from traces/logs:
- no local task DB/sync used as authoritative truth;
- no AS21 writes;
- source route is direct live MCP-SWTR;
- pagination completed rather than silently truncating task sets.

# FINAL GATE
Write `po-agent-platform-v2/qa_reports/ASSIGNEE_FULL_LIVE_ROUTE_AB_140.md`.

Allowed verdicts:
- `ASSIGNEE_FULL_LIVE_ROUTE_GREEN`
- `ASSIGNEE_TASK_API_PARITY_RED`
- `ASSIGNEE_AGENT_PARITY_RED`
- `ASSIGNEE_IDENTITY_RED`
- `PROTECTED_EXACT_TASK_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN is forbidden unless every Phase 1-5 case was actually executed and exact key-set parity is proven for all three assignee scenarios.

Commit/push QA report only and STOP.

## Start now
Execute Assignment 140 completely.