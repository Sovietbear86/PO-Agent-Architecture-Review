# Assignment 047 — MCP-SWTR Stdio Transport Retest

## Purpose

Assignment 046 proved that the available working MCP-SWTR server is stdio-based, while Task API previously tried to use only SSE. The production fix under test adds read-only stdio transport support to `SWTRMCPClient` without using bulk sync.

Assignment 047 must start Task API with `SWTR_MCP_TRANSPORT=stdio`, prove `/api/v1/swtr-read/health`, and rerun the bounded oracle path.

## Repository

`Sovietbear86/PO-Agent-Architecture-Review`

## Branch

`feat/core8-real-query-hardening-v2`

## Allowed output

Commit and push only:

`qa_reports/CORE8_MCP_SWTR_STDIO_TRANSPORT_RETEST_047.md`

Do not commit JSON, helper scripts, runner changes, config changes, logs, `.env`, credentials, historical reports, roadmap edits or production changes.

## Fixed role

You are QA/tester only.

- Do not modify production code, prompts, adapters, tests, fixtures, QA runners, acceptance runners, repository/local configuration, AS21/SWTR data, historical reports, roadmap files or learning state.
- Do not copy MCP-SWTR source into this repository.
- Do not run full tenant-wide task sync.
- Do not run bulk task synchronization as an oracle substitute.
- Do not repair discovered production defects.
- Never print, commit or paste token values.

## Autonomous execution

The repository owner pre-authorizes this QA batch. Do not ask for confirmation after each routine step, integration call, local service restart, read-only AS21/SWTR query, MCP-SWTR diagnostic, Task API diagnostic, HTTP diagnostic, test command, allowed report commit or allowed report push.

Ask only if continuing requires a missing credential, unavoidable platform approval, write outside the report allowlist, production/source-data/config mutation, destructive out-of-scope action or scope expansion.

## Mandatory preflight

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `START_HEAD = git rev-parse HEAD`.
4. Read this assignment and `GIGACODE_NEXT_ACTION.md` from `START_HEAD`.
5. Verify the active assignment is 047 and the allowed report path is exactly:
   `qa_reports/CORE8_MCP_SWTR_STDIO_TRANSPORT_RETEST_047.md`
6. Read:
   - `qa_reports/CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046.md`
   - `qa_assignments/CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046.md`
7. Verify `START_HEAD` contains stdio support in `task-api/app/services/swtr_mcp_client.py`:
   - `SWTR_MCP_TRANSPORT`;
   - `SWTR_MCP_STDIO_COMMAND`;
   - `SWTR_MCP_STDIO_ARGS` or `SWTR_MCP_STDIO_SCRIPT`;
   - `StdioTransport`.
8. Verify no prohibited files are staged.

If preflight fails, write the allowed 047 report with `047_VERDICT = BLOCKED`, include exact mismatch evidence, commit only that report, push and stop.

## Phase 1 — Configure stdio MCP-SWTR

Use the adjacent working MCP-SWTR installation identified in 046. Do not copy it into this repository.

Expected local MCP-SWTR shape:

- Python executable: `<mcp-swtr>/.venv/bin/python`
- Server script: `<mcp-swtr>/mcp_server.py`
- Working directory: `<mcp-swtr>`
- Token/configuration already available locally.

Set Task API environment without printing secret values:

```bash
export SWTR_MCP_TRANSPORT=stdio
export SWTR_MCP_STDIO_COMMAND="<mcp-swtr>/.venv/bin/python"
export SWTR_MCP_STDIO_ARGS="<mcp-swtr>/mcp_server.py"
export SWTR_MCP_STDIO_CWD="<mcp-swtr>"
export SWTR_MCP_BASE_URL="https://portal.works.prod.sbt/swtr"
export SWTR_TOKEN="$(cat ~/.config/swtr/api_key)"
```

If the adjacent project `.env` uses `TOKEN` and `BASE_URL`, you may export those names instead. Do not include token values in the report.

## Phase 2 — Restart services from current HEAD

Start Task API from the repository checkout:

```bash
cd task-api
SWTR_MCP_TRANSPORT=stdio \
SWTR_MCP_STDIO_COMMAND="<mcp-swtr>/.venv/bin/python" \
SWTR_MCP_STDIO_ARGS="<mcp-swtr>/mcp_server.py" \
SWTR_MCP_STDIO_CWD="<mcp-swtr>" \
SWTR_MCP_BASE_URL="https://portal.works.prod.sbt/swtr" \
SWTR_TOKEN="<redacted>" \
python3 -m uvicorn main:app --host 127.0.0.1 --port 8003
```

Start PO Agent from the repository checkout:

```bash
cd po-agent-platform-v2
unset PYTHONPATH
PO_AGENT_AS21_MODE=task-api \
PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8003 \
PO_AGENT_EXPECTED_PACKAGE_ROOT="$(pwd)" \
PO_AGENT_EXPECTED_HEAD="<START_HEAD>" \
python3 -m uvicorn po_agent.main:app --host 127.0.0.1 --port 8004
```

Record PIDs, ports and redacted process commands.

## Phase 3 — Transport proof

Call:

```bash
curl -s http://127.0.0.1:8003/api/v1/swtr-read/health
```

Required:

- HTTP 200;
- `status = connected`;
- `transport = stdio`;
- `read_unit = true`;
- `get_unit_files = true`;
- `get_sprint_tasks = true`;
- `search_versions = true`;
- no secrets in response.

Also call PO Agent diagnostics:

```bash
curl -s http://127.0.0.1:8004/api/v1/ops/as21-diagnostics
```

Required:

- current repository runtime identity passes;
- Task API route contract remains `SWTR_READ`;
- no HTTP 500;
- no internal `KeyError`.

Known diagnostic note: `SUSPICIOUS_PYTHONPATH_COUNT` may report current checkout paths containing `PO_Agent_Harness`; treat these as false positives only if `package_root`, `expected_package_root` and git heads all match `START_HEAD`.

## Phase 4 — Owner smoke check

Run these queries against PO Agent `/api/v1/query` with fresh session IDs:

| Case | Query | Expected |
|------|-------|----------|
| O1 | `Покажи задачи Безрукова` | COMPLETED or source-backed clarification; no fake adapter |
| O2 | `Покажи открытые задачи Гаранина из пространства DMS` | COMPLETED or source-backed clarification; no HTTP 500 |
| O3 | `Покажи задачи Гаранина в спринте DMS-SPRNT-2` | COMPLETED, source-backed clarification or fail-closed; no foreign-sprint false green |
| O4 | `Покажи здоровье спринта DMS-SPRNT-2` | COMPLETED or source-backed NEEDS_CLARIFICATION/FAILED; no internal `KeyError` |
| O5 | `Покажи список спринтов по DMS` | controlled response or clarification; no internal `KeyError`, no HTTP 500 |

Use `source_id` as canonical SWTR task key when `id` is an internal UUID.

## Phase 5 — Bounded oracle retest

Do not use the PO Agent result as oracle. Do not sync all tasks.

For `DMS-SPRNT-2`:

1. Call `GET /api/v1/swtr-read/sprints/DMS-SPRNT-2/tasks?complete=true`.
2. Extract candidate task keys from the live MCP-SWTR payload.
3. For each candidate key, call `GET /api/v1/swtr-read/tasks/<TASK_KEY>`.
4. From each authoritative unit extract:
   - task key;
   - assignee/login;
   - status;
   - space/product;
   - `scrum_board_plugin_sprint`.
5. Include a task in `ORACLE_KEYS_GARANIN_DMS_SPRNT_2` only when:
   - authoritative sprint exactly equals `DMS-SPRNT-2`;
   - authoritative assignee/login matches Garanin.
6. Compare exact sets with `AGENT_KEYS_O3`.

If O3 asks for source-backed clarification because Garanin is ambiguous, record it and run bounded oracle for the clarified login only if the source evidence supports that login. Do not silently substitute people.

## Acceptance

047 is GREEN only if:

- stdio MCP-SWTR transport is connected;
- required MCP tools are present;
- Task API route contract is `SWTR_READ`;
- runtime identity proof passes;
- owner smoke tests produce no HTTP 500 and no internal `KeyError`;
- bounded oracle path is proven, or O3 is a source-backed clarification with documented oracle evidence for the clarified login;
- no full tenant-wide sync was run;
- no production/source/config files are modified by QA;
- `FALSE_GREEN_COUNT = 0`;
- `QUERY_HTTP_500_COUNT = 0`;
- `INTERNAL_KEYERROR_COUNT = 0`.

047 is BLOCKED only if credentials/platform permissions prevent starting the known stdio MCP-SWTR transport.

047 is RED if stdio transport support is present but fails due to production code, if `/swtr-read/*` returns HTTP 500, if there is an internal `KeyError`, if the oracle disproves returned tasks, or if QA runs full sync as a substitute for bounded hydration.

## Required footer

```text
ASSIGNMENT_ID = CORE8_MCP_SWTR_STDIO_TRANSPORT_RETEST_047
START_HEAD = <sha>
REPORT_COMMIT = <sha_after_commit_or_PENDING_BEFORE_COMMIT>
TASK_API_ROUTE_CONTRACT = SWTR_READ|LEGACY_SWTR_ONLY|MISSING|UNKNOWN
SWTR_READ_ROUTES_PRESENT = YES|NO
MCP_SWTR_TRANSPORT = stdio|sse|unknown
MCP_SWTR_TRANSPORT_CONNECTED = YES|NO
MCP_SWTR_TOOLS_PRESENT = YES|NO
STDIO_COMMAND_REDACTED = YES|NO
MCP_SECRET_LEAK = YES|NO
FULL_TASK_SYNC_RUN = YES|NO
BOUNDED_ORACLE_ONLY = YES|NO
ORACLE_PATH_PROVEN = YES|NO
OWNER_SMOKE_O1 = PASS|FAIL|BLOCKED
OWNER_SMOKE_O2 = PASS|FAIL|BLOCKED
OWNER_SMOKE_O3 = PASS|FAIL|BLOCKED|CLARIFICATION
OWNER_SMOKE_O4 = PASS|FAIL|BLOCKED
OWNER_SMOKE_O5 = PASS|FAIL|BLOCKED
CASE_O3_EXACT_SET = PASS|FAIL|BLOCKED|CLARIFICATION
FOREIGN_SPRINT_TASK_COUNT = n
SILENT_SLOT_DROP_COUNT = n
INTERNAL_KEYERROR_COUNT = n
QUERY_HTTP_500_COUNT = n
FALSE_GREEN_COUNT = n
RUNNER_MODIFIED = NO
PRODUCTION_MODIFIED_BY_QA = NO
UNAUTHORIZED_FILES_COMMITTED = NO
047_VERDICT = GREEN|RED|BLOCKED
READY_TO_RESUME_017_V2 = YES|NO
```

`READY_TO_RESUME_017_V2 = YES` only if 047 is GREEN and `ORACLE_PATH_PROVEN = YES`.

## Commit and stop

Before commit:

```bash
git status --short
git add -- qa_reports/CORE8_MCP_SWTR_STDIO_TRANSPORT_RETEST_047.md
git diff --cached --name-only
```

The staged file list must contain exactly:

```text
qa_reports/CORE8_MCP_SWTR_STDIO_TRANSPORT_RETEST_047.md
```

Commit subject:

`qa: CORE8_MCP_SWTR_STDIO_TRANSPORT_RETEST_047`

Push to the same branch. Return commit SHA, final verdict and complete report contents. Then stop.
