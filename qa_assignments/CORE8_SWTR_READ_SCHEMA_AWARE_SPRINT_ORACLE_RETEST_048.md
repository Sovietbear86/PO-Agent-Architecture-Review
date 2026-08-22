# Assignment 048 — Schema-Aware SWTR Sprint Oracle Retest

## Purpose

Assignment 047 proved that stdio MCP-SWTR transport works and required MCP tools are available. It also exposed two production issues in the read facade:

1. `get_sprint_tasks` could call MCP without explicit source space for `DMS-SPRNT-2`, allowing the MCP tool to fall back to an unexpected default project.
2. MCP error payloads such as `SWTR_ACCESS_DENIED_ERROR` were returned inside the `tasks` field with `complete=true` instead of failing closed.

The production fix under test makes `/api/v1/swtr-read/sprints/{sprint_id}/tasks` schema-aware, infers `space=DMS` from `DMS-SPRNT-2`, and converts MCP error payloads to HTTP errors.

## Repository

`Sovietbear86/PO-Agent-Architecture-Review`

## Branch

`feat/core8-real-query-hardening-v2`

## Allowed output

Commit and push only:

`qa_reports/CORE8_SWTR_READ_SCHEMA_AWARE_SPRINT_ORACLE_RETEST_048.md`

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
5. Verify the active assignment is 048 and the allowed report path is exactly:
   `qa_reports/CORE8_SWTR_READ_SCHEMA_AWARE_SPRINT_ORACLE_RETEST_048.md`
6. Read:
   - `qa_reports/CORE8_MCP_SWTR_STDIO_TRANSPORT_RETEST_047.md`
   - `qa_assignments/CORE8_MCP_SWTR_STDIO_TRANSPORT_RETEST_047.md`
7. Verify `START_HEAD` contains the schema-aware sprint read fix:
   - `_schema_aware_get_sprint_tasks_arguments`;
   - `_infer_space_from_sprint`;
   - `_raise_mcp_error_payload`;
   - `space: str | None = Query(...)` on sprint tasks endpoint.
8. Verify no prohibited files are staged.

If preflight fails, write the allowed 048 report with `048_VERDICT = BLOCKED`, include exact mismatch evidence, commit only that report, push and stop.

## Phase 1 — Local focused tests

Run, without modifying tests:

```bash
cd task-api
python3 -m pytest tests/test_swtr_mcp_client.py tests/test_swtr_read_facade.py -q
```

If local Python dependencies are missing, record the exact missing package and continue to integration phases if services can run in the normal QA environment.

## Phase 2 — Start stdio MCP-SWTR path

Use the same adjacent working MCP-SWTR installation as in 047. Do not copy it into this repository.

Start Task API from current `START_HEAD` with redacted stdio configuration:

```bash
cd task-api
SWTR_MCP_TRANSPORT=stdio \
SWTR_MCP_STDIO_COMMAND="<mcp-swtr>/.venv/bin/python_or_wrapper" \
SWTR_MCP_STDIO_ARGS="<mcp-swtr>/mcp_server.py" \
SWTR_MCP_STDIO_CWD="<mcp-swtr>" \
SWTR_MCP_BASE_URL="https://portal.works.prod.sbt/swtr" \
SWTR_TOKEN="<redacted>" \
python3 -m uvicorn main:app --host 127.0.0.1 --port 8003
```

Start PO Agent from current `START_HEAD`:

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

## Phase 3 — Transport and route proof

Call:

```bash
curl -s http://127.0.0.1:8003/api/v1/swtr-read/health
curl -s http://127.0.0.1:8003/openapi.json
curl -s http://127.0.0.1:8004/api/v1/ops/as21-diagnostics
```

Required:

- `/swtr-read/health` HTTP 200;
- `transport = stdio`;
- required MCP tools present;
- Task API route contract remains `SWTR_READ`;
- runtime identity proof passes;
- no secrets in responses.

## Phase 4 — Schema-aware sprint endpoint proof

Call both:

```bash
curl -i "http://127.0.0.1:8003/api/v1/swtr-read/sprints/DMS-SPRNT-2/tasks?complete=true"
curl -i "http://127.0.0.1:8003/api/v1/swtr-read/sprints/DMS-SPRNT-2/tasks?space=DMS&complete=true"
```

Required if the token has access:

- HTTP 200;
- `space = DMS`;
- MCP arguments or nested request include DMS space/project code;
- no `errorType`, `uiErrorMessage` or `exceptionUUID` under `tasks`;
- `complete` and `completeness_source` are truthful;
- bounded oracle can proceed.

Required if the token lacks access:

- HTTP 403, not HTTP 200;
- response detail contains redacted/non-secret access-denied evidence;
- no `tasks` object containing `errorType`;
- no `complete=true` false green;
- classify `ORACLE_PATH_PROVEN = NO` and `SWTR_ACCESS_DENIED_FAILCLOSED = YES`.

HTTP 200 with `tasks.errorType = SWTR_ACCESS_DENIED_ERROR` is a production FAIL.

## Phase 5 — Owner smoke check

Run these queries against PO Agent `/api/v1/query` with fresh session IDs:

| Case | Query | Expected |
|------|-------|----------|
| O1 | `Покажи задачи Безрукова` | COMPLETED or source-backed clarification; no fake adapter |
| O2 | `Покажи открытые задачи Гаранина из пространства DMS` | COMPLETED or source-backed clarification; no HTTP 500 |
| O3 | `Покажи задачи Гаранина в спринте DMS-SPRNT-2` | COMPLETED, source-backed clarification or fail-closed; no foreign-sprint false green |
| O4 | `Покажи здоровье спринта DMS-SPRNT-2` | COMPLETED or source-backed NEEDS_CLARIFICATION/FAILED; no internal `KeyError` |
| O5 | `Покажи список спринтов по DMS` | controlled response or clarification; no internal `KeyError`, no HTTP 500 |

## Phase 6 — Bounded oracle if accessible

If sprint tasks endpoint returns HTTP 200 with real tasks:

1. Extract candidate task keys.
2. For each key, call `GET /api/v1/swtr-read/tasks/<TASK_KEY>`.
3. Extract authoritative task key, assignee/login, status, space/product and `scrum_board_plugin_sprint`.
4. Build `ORACLE_KEYS_GARANIN_DMS_SPRNT_2`.
5. Compare exact sets with `AGENT_KEYS_O3`.

If sprint tasks endpoint fail-closes with HTTP 403 due credentials, do not run full sync and do not mark production RED solely for missing permissions.

## Acceptance

048 is GREEN if:

- focused tests pass or dependency skips are justified;
- stdio MCP transport remains connected;
- schema-aware endpoint sends/records DMS space;
- MCP access-denied payloads fail closed as HTTP 403;
- no false green `complete=true` error payload;
- no HTTP 500 or internal `KeyError`;
- no full tenant-wide sync was run;
- if source access exists, bounded oracle exact-set passes.

048 is BLOCKED if the only remaining blocker is credential access denied and the endpoint correctly fails closed.

048 is RED if access-denied payload is wrapped as successful tasks, if DMS space is not passed when schema allows it, if there is HTTP 500/internal `KeyError`, if QA runs full sync, or if oracle disproves returned tasks.

## Required footer

```text
ASSIGNMENT_ID = CORE8_SWTR_READ_SCHEMA_AWARE_SPRINT_ORACLE_RETEST_048
START_HEAD = <sha>
REPORT_COMMIT = <sha_after_commit_or_PENDING_BEFORE_COMMIT>
FOCUSED_TESTS = PASS|FAIL|BLOCKED
TASK_API_ROUTE_CONTRACT = SWTR_READ|LEGACY_SWTR_ONLY|MISSING|UNKNOWN
MCP_SWTR_TRANSPORT = stdio|sse|unknown
MCP_SWTR_TRANSPORT_CONNECTED = YES|NO
MCP_SWTR_TOOLS_PRESENT = YES|NO
DMS_SPACE_ARGUMENT_PASSED = YES|NO|UNPROVEN
SWTR_ACCESS_DENIED_FAILCLOSED = YES|NO|NOT_APPLICABLE
ACCESS_DENIED_HTTP_STATUS = 403|200|OTHER|NOT_APPLICABLE
ERROR_PAYLOAD_WRAPPED_AS_TASKS = YES|NO
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
048_VERDICT = GREEN|RED|BLOCKED
READY_TO_RESUME_017_V2 = YES|NO
```

`READY_TO_RESUME_017_V2 = YES` only if 048 is GREEN and `ORACLE_PATH_PROVEN = YES`.

## Commit and stop

Before commit:

```bash
git status --short
git add -- qa_reports/CORE8_SWTR_READ_SCHEMA_AWARE_SPRINT_ORACLE_RETEST_048.md
git diff --cached --name-only
```

The staged file list must contain exactly:

```text
qa_reports/CORE8_SWTR_READ_SCHEMA_AWARE_SPRINT_ORACLE_RETEST_048.md
```

Commit subject:

`qa: CORE8_SWTR_READ_SCHEMA_AWARE_SPRINT_ORACLE_RETEST_048`

Push to the same branch. Return commit SHA, final verdict and complete report contents. Then stop.
