# Assignment 049 — Bounded SWTR Oracle Access Proof

## Purpose

Assignment 048 verified the production fix for schema-aware sprint reads and fail-closed SWTR error handling, but it did **not** prove the independent bounded oracle path:

```text
ORACLE_PATH_PROVEN = NO
READY_TO_RESUME_017_V2 = NO
```

The remaining question is not whether the PO Agent can return some tasks. Owner smoke tests show that normal task queries can return data. The remaining question is whether QA can independently obtain source-backed DMS sprint candidate task keys and hydrate each task unit from SWTR to verify `scrum_board_plugin_sprint`, assignee and status.

Do not run full tenant-wide task synchronization. Full sync is not required for this assignment and must not be used as an oracle substitute.

## Repository

`Sovietbear86/PO-Agent-Architecture-Review`

## Branch

`feat/core8-real-query-hardening-v2`

## Allowed output

Commit and push only:

`qa_reports/CORE8_BOUNDED_SWTR_ORACLE_ACCESS_PROOF_049.md`

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
5. Verify the active assignment is 049 and the allowed report path is exactly:
   `qa_reports/CORE8_BOUNDED_SWTR_ORACLE_ACCESS_PROOF_049.md`
6. Read:
   - `qa_reports/CORE8_SWTR_READ_SCHEMA_AWARE_SPRINT_ORACLE_RETEST_048.md`
   - `qa_assignments/CORE8_SWTR_READ_SCHEMA_AWARE_SPRINT_ORACLE_RETEST_048.md`
   - `qa_reports/CORE8_MCP_SWTR_STDIO_TRANSPORT_RETEST_047.md`
7. Verify no prohibited files are staged.

If preflight fails, write the allowed 049 report with `049_VERDICT = BLOCKED`, include exact mismatch evidence, commit only that report, push and stop.

## Phase 1 — Focused regression tests

Run:

```bash
cd task-api
python3 -m pytest tests/test_swtr_mcp_client.py tests/test_swtr_read_facade.py -q
```

Record exact result. If dependencies are missing, record the missing dependency and continue to integration phases if services can run.

## Phase 2 — Start bounded read-only runtime

Use the same adjacent working MCP-SWTR installation and wrapper proven in 048. Do not copy it into this repository.

Start Task API from `START_HEAD` with redacted stdio configuration:

```bash
cd task-api
SWTR_MCP_TRANSPORT=stdio \
SWTR_MCP_STDIO_COMMAND="<mcp-swtr-wrapper-or-python>" \
SWTR_MCP_STDIO_ARGS="mcp_server.py" \
SWTR_MCP_STDIO_CWD="<mcp-swtr>" \
SWTR_MCP_BASE_URL="https://portal.works.prod.sbt/swtr" \
SWTR_TOKEN="<redacted>" \
python3 -m uvicorn main:app --host 127.0.0.1 --port 8003
```

Start PO Agent from `START_HEAD`:

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

## Phase 3 — Health and access map

Call:

```bash
curl -s http://127.0.0.1:8003/api/v1/swtr-read/health
curl -s http://127.0.0.1:8004/api/v1/ops/as21-diagnostics
```

Required:

- `transport = stdio`;
- required tools present;
- Task API route contract remains `SWTR_READ`;
- runtime identity proof passes;
- no secrets in responses.

Then build a minimal source-access map using bounded calls only:

```bash
curl -i "http://127.0.0.1:8003/api/v1/swtr-read/tasks/DMS-261"
curl -i "http://127.0.0.1:8003/api/v1/swtr-read/tasks/DMS-248"
curl -i "http://127.0.0.1:8003/api/v1/swtr-read/spaces/DMS/current-sprint"
curl -i "http://127.0.0.1:8003/api/v1/swtr-read/sprints/DMS-SPRNT-2/tasks?space=DMS&complete=true"
```

If one of the historical task ids no longer exists or is inaccessible, record that fact and try one task key returned by the owner smoke query, but do not use the owner smoke query as the oracle.

For each call record:

- HTTP status;
- whether payload is real data or fail-closed error;
- redacted error type/message/exception id if present;
- whether `errorType` appears under a successful `tasks` object;
- whether HTTP 500 or internal traceback occurred.

## Phase 4 — No-full-sync proof

Explicitly verify and record:

- no `sync_all`, `sync_sprint_tasks`, full tenant task sync or equivalent bulk synchronization was run;
- no local AS21/SWTR cache was refreshed as an oracle substitute;
- only bounded read-only calls were used.

If you believe a full sync is necessary, stop and report `FULL_TASK_SYNC_REQUIRED_BY_QA = YES`. Do not run it.

## Phase 5 — Owner smoke observations

Run fresh-session owner smoke checks and compare them with the access map:

| Case | Query | Required classification |
|------|-------|-------------------------|
| O1 | `Покажи задачи Безрукова` | Data-bearing user-flow check |
| O2 | `Покажи открытые задачи Гаранина из пространства DMS` | Clarification or data-bearing check |
| O3 | `Покажи задачи Гаранина в спринте DMS-SPRNT-2` | Candidate for exact oracle if source access exists |
| O4 | `Покажи здоровье спринта DMS-SPRNT-2` | Controlled fail-closed or data-bearing check |
| O5 | `Покажи список спринтов по DMS` | Controlled fail-closed or data-bearing check |

Record exact response status, task keys when present, and whether the result uses fake adapter data. Do not mark O3 exact-set PASS without the independent hydrated oracle from Phase 6.

## Phase 6 — Bounded hydrated oracle, only if source access exists

Proceed only if a bounded SWTR source path returns candidate task keys for `DMS-SPRNT-2`.

Allowed candidate sources:

- `/api/v1/swtr-read/sprints/DMS-SPRNT-2/tasks?space=DMS&complete=true` returning real task content;
- a documented read-only MCP/SWTR bounded search/filter endpoint that directly constrains `space=DMS` and `scrum_board_plugin_sprint=DMS-SPRNT-2`.

Forbidden candidate sources:

- PO Agent answer text;
- PO Agent returned tasks;
- full tenant sync;
- arbitrary local cache scan without proving it is current and source-backed;
- historical hard-coded task lists.

For every candidate task key:

1. Call `GET /api/v1/swtr-read/tasks/<TASK_KEY>`.
2. Extract task key, assignee/login, status, space/product and `scrum_board_plugin_sprint`.
3. Keep only tasks where `scrum_board_plugin_sprint` exactly equals `DMS-SPRNT-2`.
4. Apply assignee filter for `Garanin.R.V` if source identity is available.
5. Compare exact key set with O3 agent result.

Agent result cannot be used as oracle.

## Verdict rules

049 is GREEN only if:

- focused tests pass or dependency skip is justified;
- stdio MCP transport is connected;
- bounded source candidate path for `DMS-SPRNT-2` is proven;
- every oracle task is individually hydrated via SWTR `read_unit`;
- O3 exact key set matches the hydrated oracle;
- `FALSE_GREEN_COUNT = 0`;
- `INTERNAL_KEYERROR_COUNT = 0`;
- `QUERY_HTTP_500_COUNT = 0`;
- `FULL_TASK_SYNC_RUN = NO`;
- `READY_TO_RERUN_017_V2 = YES`.

049 is BLOCKED if:

- transport/runtime is healthy;
- owner smoke shows user-flow data can work;
- but SWTR denies the bounded candidate source or task hydration due credential/tool permission;
- all denied paths fail closed without false green;
- no full sync was run.

049 is RED if:

- HTTP 200 wraps SWTR errors as task data;
- Task API/PO Agent returns HTTP 500 or internal traceback;
- sprint/user constraints are silently dropped;
- GigaCode modifies runner/production/config/source data;
- GigaCode runs full tenant-wide sync;
- bounded hydrated oracle disproves the agent result.

## Required footer

```text
ASSIGNMENT_ID = CORE8_BOUNDED_SWTR_ORACLE_ACCESS_PROOF_049
START_HEAD = <sha>
REPORT_COMMIT = <sha_after_commit_or_PENDING_BEFORE_COMMIT>
FOCUSED_TESTS = PASS|FAIL|BLOCKED
TASK_API_ROUTE_CONTRACT = SWTR_READ|LEGACY_SWTR_ONLY|MISSING|UNKNOWN
MCP_SWTR_TRANSPORT = stdio|sse|unknown
MCP_SWTR_TRANSPORT_CONNECTED = YES|NO
MCP_SWTR_TOOLS_PRESENT = YES|NO
TASK_READ_DMS_261 = PASS|FAIL|ACCESS_DENIED|NOT_FOUND|BLOCKED
TASK_READ_DMS_248 = PASS|FAIL|ACCESS_DENIED|NOT_FOUND|BLOCKED
DMS_CURRENT_SPRINT_READ = PASS|FAIL|ACCESS_DENIED|BLOCKED
DMS_SPRINT_TASKS_READ = PASS|FAIL|ACCESS_DENIED|BLOCKED
ERROR_PAYLOAD_WRAPPED_AS_TASKS = YES|NO
FULL_TASK_SYNC_RUN = YES|NO
FULL_TASK_SYNC_REQUIRED_BY_QA = YES|NO
BOUNDED_ORACLE_ONLY = YES|NO
ORACLE_CANDIDATE_SOURCE = swtr_sprint_tasks|bounded_swtr_search|NONE
ORACLE_PATH_PROVEN = YES|NO
OWNER_SMOKE_O1 = PASS|FAIL|BLOCKED
OWNER_SMOKE_O2 = PASS|FAIL|BLOCKED|CLARIFICATION
OWNER_SMOKE_O3 = PASS|FAIL|BLOCKED|CLARIFICATION
OWNER_SMOKE_O4 = PASS|FAIL|BLOCKED|CLARIFICATION
OWNER_SMOKE_O5 = PASS|FAIL|BLOCKED|CLARIFICATION
CASE_O3_EXACT_SET = PASS|FAIL|BLOCKED|CLARIFICATION
FOREIGN_SPRINT_TASK_COUNT = n
SILENT_SLOT_DROP_COUNT = n
INTERNAL_KEYERROR_COUNT = n
QUERY_HTTP_500_COUNT = n
FALSE_GREEN_COUNT = n
RUNNER_MODIFIED = NO
PRODUCTION_MODIFIED_BY_QA = NO
UNAUTHORIZED_FILES_COMMITTED = NO
049_VERDICT = GREEN|RED|BLOCKED
READY_TO_RERUN_017_V2 = YES|NO
READY_TO_RESUME_GATE_E = YES|NO
```

`READY_TO_RERUN_017_V2 = YES` only if `049_VERDICT = GREEN` and `ORACLE_PATH_PROVEN = YES`.

## Commit and stop

Before commit:

```bash
git status --short
git add -- qa_reports/CORE8_BOUNDED_SWTR_ORACLE_ACCESS_PROOF_049.md
git diff --cached --name-only
```

The staged file list must contain exactly:

```text
qa_reports/CORE8_BOUNDED_SWTR_ORACLE_ACCESS_PROOF_049.md
```

Commit subject:

`qa: CORE8_BOUNDED_SWTR_ORACLE_ACCESS_PROOF_049`

Push to the same branch. Return commit SHA, final verdict and complete report contents. Then stop.
