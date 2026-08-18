# QA Assignment: AS21-A3-UNIFIED-SSE-RETEST-008

## Purpose
Validate the developer-authored transport fix that removes the legacy stdio bridge from all **new Harness rich-read paths** and routes them through one live MCP-SWTR SSE client.

GigaCode is tester/reviewer only. Do not modify production code.

## Context
Previous QA proved:
- real MCP-SWTR is alive at `http://127.0.0.1:3000/sse`;
- FastMCP can list 47 tools;
- direct SSE `get_unit_files` returned a real attachment for `WMB-30000`;
- Task API rich-read failed only because it called legacy `SWTRSyncService._run_mcp_command()` over subprocess/stdin.

Developer fix now present:
- `task-api/app/services/swtr_mcp_client.py` — unified async SSE client;
- `task-api/app/routers/swtr_read.py` — rich read facade now uses only `SWTRMCPClient`;
- `task-api/requirements.txt` includes `fastmcp>=2.0`;
- new read-only endpoints include health, full `read_unit`, attachment metadata, current sprint, and sprint tasks.

Important: legacy `SWTRSyncService` remains for historical sync/import code but MUST NOT be invoked by `swtr_read` or Harness rich-read capabilities.

## Pre-check
```bash
git fetch --all --prune
git checkout feat/real-baseline-candidate-eval-v1
git pull --ff-only
git status --short
git log --oneline -12
```

Inspect:
- `task-api/app/services/swtr_mcp_client.py`
- `task-api/app/routers/swtr_read.py`
- `task-api/app/services/swtr_sync_service.py`

Confirm no `SWTRSyncService` import/use remains in `swtr_read.py`.

## Environment
Use the real MCP-SWTR service already discovered in RETEST-007:

```bash
cd task-api/mcp-swtr
python3 mcp_server.py
```

If that directory exists only in the local checked-out working tree and is not tracked by Git, that is acceptable for runtime QA; do not commit it.

The expected endpoint is:

`http://127.0.0.1:3000/sse`

Set explicitly before Task API startup:

```bash
export SWTR_MCP_SSE_URL='http://127.0.0.1:3000/sse'
```

Install/update Task API dependencies if needed:

```bash
cd task-api
python3 -m pip install -r requirements.txt
```

Start current Task API:

```bash
python3 -m uvicorn main:app --host 127.0.0.1 --port 8003
```

## Test 1 — SSE health through Task API
Call:

```bash
curl -sS http://127.0.0.1:8003/api/v1/swtr-read/health
```

Required:
- HTTP 200;
- `status=connected`;
- `transport=sse`;
- tool count > 0;
- `read_unit=true`;
- `get_unit_files=true`.

This proves Task API itself reaches MCP-SWTR through the new client.

## Test 2 — real full task read
Call:

```bash
curl -sS http://127.0.0.1:8003/api/v1/swtr-read/tasks/WMB-30000
```

Required:
- HTTP 200;
- payload originates from real `read_unit`;
- real task code/summary/attributes present;
- no secrets/tokens returned.

Compare enough fields with the already working `/api/v1/tasks` representation to prove both refer to the same source task.

## Test 3 — real attachment metadata
Call:

```bash
curl -sS http://127.0.0.1:8003/api/v1/swtr-read/tasks/WMB-30000/files
```

Required:
- HTTP 200;
- at least one attachment if the source has not changed;
- expected real file metadata discovered in RETEST-007;
- no content download;
- no token leakage.

Then call the real `TaskApiAS21Adapter.get_attachment_metadata('WMB-30000')` and prove canonical mapping succeeds.

If source data changed and WMB-30000 no longer has files, locate another real WMB task assigned to `Kalachanov.V.V` with files and record the key. Do not fabricate.

## Test 4 — preserve existing task retrieval
Critical regression check: prove that normal task search still works exactly as before.

Use production adapter / task-api for:
- exact `WMB-30000`;
- `assignee = Kalachanov.V.V`;
- `project = WMB AND assignee = Kalachanov.V.V`;
- nonexistent assignee => 0;
- free-text search from previous A2 suite.

The transport change MUST NOT break `/api/v1/tasks` or canonical task mapping.

## Test 5 — sprint discovery in DMS and OLP
Read:
- `CORE8_TEAM_SPRINT_DISCOVERY_CONTRACT.md`
- `task-api/knowledge/team/team.md`
- `task-api/knowledge/team/competencies.md`

Do not use anonymized `task-api/config/team_members.yaml` as identity truth.

First test the new same-transport endpoint:

```bash
curl -sS http://127.0.0.1:8003/api/v1/swtr-read/spaces/DMS/current-sprint
curl -sS http://127.0.0.1:8003/api/v1/swtr-read/spaces/OLP/current-sprint
```

If current sprint is returned, call:

```text
GET /api/v1/swtr-read/sprints/<REAL_SPRINT_ID>/tasks
```

Then cross-check returned tasks against real team members/logins in `team.md`.

If `get_current_sprint` is not the correct tool contract for DMS/OLP, inspect actual tool schema and report exact mismatch. Do not alter production code.

Also use read-only `find_units_by_filter` directly through MCP if necessary to discover sprint-bearing tasks for real team members in spaces DMS and OLP, following `CORE8_TEAM_SPRINT_DISCOVERY_CONTRACT.md`.

Report:
- real DMS sprint id / status;
- real OLP sprint id / status;
- team members found in each;
- task count;
- source shape that associates task with sprint.

## Test 6 — transport isolation
Adversarially prove:
- `swtr_read.py` does not instantiate `SWTRSyncService`;
- no hardcoded `/MyTestProject_1/.../mcp-swtr` path is reachable from new rich-read routes;
- no subprocess/stdin transport is used for new rich reads;
- `SWTR_MCP_SSE_URL` override works;
- MCP outage returns 503/explicit source unavailable, not fake empty success;
- malformed MCP payload fails closed.

Legacy sync/import code may still contain the historical path; classify it as `LEGACY_NOT_HARNESS_READ_PATH`, not as a regression of this assignment.

## Test 7 — regressions
Run targeted adapter tests and relevant Task API tests, then full regression.

Baseline from RETEST-007:
- `test_task_api_as21_adapter.py`: 15/15 PASS
- full regression: 1166 passed, 5 pre-existing failures

Compute:
`NEW_CODE_REGRESSIONS_VS_RETEST_007`

## Gate
GREEN requires all of:
- Task API -> MCP-SWTR SSE health succeeds;
- `read_unit(WMB-30000)` succeeds through Task API;
- real attachment metadata succeeds through Task API and canonical adapter;
- base task retrieval/filtering remains GREEN;
- no new regressions;
- new rich read routes do not use legacy stdio bridge.

Sprint DMS/OLP may remain YELLOW if the tool contract itself is not yet wired, but must be classified with exact evidence.

Do NOT return to learning loop in this assignment.

## Report
Publish:

`qa_reports/AS21_A3_UNIFIED_SSE_RETEST_008.md`

End with:

```text
ASSIGNMENT_ID = AS21-A3-UNIFIED-SSE-RETEST-008
MCP_SWTR_CONNECTED =
TASK_API_SSE_HEALTH =
REAL_WMB_30000_READ =
REAL_ATTACHMENT_FACADE =
REAL_ATTACHMENT_COUNT =
CANONICAL_ATTACHMENT_MAPPING =
BASE_TASK_SEARCH_REGRESSION =
LEGACY_STDIO_USED_BY_RICH_READ =
DMS_CURRENT_SPRINT_READ =
DMS_REAL_SPRINT_ID =
DMS_TEAM_TASKS_FOUND =
OLP_CURRENT_SPRINT_READ =
OLP_REAL_SPRINT_ID =
OLP_TEAM_TASKS_FOUND =
NEW_CODE_REGRESSIONS_VS_RETEST_007 =
BLOCKER_COUNT =
HIGH_COUNT =
ATTACHMENT_WIRING_READY_FOR_PROMOTION =
GATE_A =
READY_FOR_LEARNING_LOOP = NO
```
