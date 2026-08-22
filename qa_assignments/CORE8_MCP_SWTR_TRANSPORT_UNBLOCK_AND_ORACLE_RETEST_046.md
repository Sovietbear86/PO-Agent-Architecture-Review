# Assignment 046 — MCP-SWTR Transport Unblock and Bounded Oracle Retest

## Purpose

Assignment 045 proved that PO Agent and Task API are running from the expected repository/HEAD and that Task API exposes the current `/api/v1/swtr-read/*` contract. The remaining blocker is not general AS21 access and not the cached task-search path: owner smoke O1 returned AS21-backed tasks.

The blocker is only the live MCP-SWTR read transport required for independent oracle hydration:

`SWTR_TRANSPORT_CLASSIFICATION = MCP_SWTR_UNAVAILABLE`

Assignment 046 must connect the existing working MCP-SWTR SSE transport, prove `/api/v1/swtr-read/health`, and run a bounded oracle retest without syncing all tasks.

## Repository

`Sovietbear86/PO-Agent-Architecture-Review`

## Branch

`feat/core8-real-query-hardening-v2`

## Allowed output

Commit and push only:

`qa_reports/CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046.md`

Do not commit JSON, helper scripts, runner changes, config changes, logs, `.env`, credentials, historical reports, roadmap edits or production changes.

## Fixed role

You are QA/tester only.

- Do not modify production code, prompts, adapters, tests, fixtures, QA runners, acceptance runners, repository/local configuration, AS21/SWTR data, historical reports, roadmap files or learning state.
- Do not copy MCP-SWTR source into this repository.
- Do not run full tenant-wide task sync.
- Do not run bulk task synchronization as an oracle substitute.
- Do not weaken or tune the oracle.
- Do not change canonical query wording.
- Do not repair discovered production defects.
- Never commit `.env`, credentials or secrets.

## Autonomous execution

The repository owner pre-authorizes this QA batch. Do not ask for confirmation after each routine step, integration call, local service restart, read-only AS21/SWTR query, MCP-SWTR diagnostic, Task API diagnostic, HTTP diagnostic, test command, allowed report commit or allowed report push.

Ask only if continuing requires a missing credential, unavoidable platform approval, write outside the report allowlist, production/source-data/config mutation, destructive out-of-scope action or scope expansion.

If your IDE/tool asks for confirmation because of local safety settings, choose the non-destructive one-time approval for the exact allowed command. Do not ask the repository owner for routine approved QA steps.

## Mandatory preflight

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `START_HEAD = git rev-parse HEAD`.
4. Read this assignment and `GIGACODE_NEXT_ACTION.md` from `START_HEAD`.
5. Verify the active assignment is 046 and the allowed report path is exactly:
   `qa_reports/CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046.md`
6. Read:
   - `qa_reports/CORE8_RUNTIME_IDENTITY_AND_SWTR_READ_ROUTE_RETEST_045.md`
   - `qa_assignments/CORE8_RUNTIME_IDENTITY_AND_SWTR_READ_ROUTE_RETEST_045.md`
7. Verify no prohibited files are staged.

If preflight fails, write the allowed 046 report with `046_VERDICT = BLOCKED`, include exact mismatch evidence, commit only that report, push and stop.

## Important scope clarification

Do not synchronize all tasks.

Oracle testing does not require a tenant-wide task cache refresh. For sprint membership proof, hydrate only:

1. candidate task keys for the requested sprint;
2. the individual SWTR task units for those candidate keys;
3. the owner smoke result task keys returned by PO Agent.

Then compare exact key sets.

Full sync is slower, riskier, and does not prove source-backed sprint membership better than bounded live hydration.

## Phase 1 — MCP-SWTR transport discovery

Use the already working MCP-SWTR setup from the adjacent project if available, but do not copy its source into this repository and do not commit any local configuration.

Allowed discovery actions:

- inspect the adjacent project's documented MCP-SWTR launch command;
- start its MCP-SWTR server locally if it already has the working token/configuration;
- use its existing token/configuration without printing or committing secret values;
- set `SWTR_MCP_SSE_URL` for the current Task API process only.

Default candidate:

`http://127.0.0.1:3000/sse`

If the adjacent project uses a different SSE URL, record the URL without tokens and use:

```bash
export SWTR_MCP_SSE_URL="<working_sse_url>"
```

Required MCP tool names:

- `read_unit`
- `get_unit_files`
- `get_sprint_tasks`
- `search_versions`

If the transport cannot be started due to a missing credential or platform permission, do not mark production RED. Mark BLOCKED and include the exact manual action required.

## Phase 2 — Restart services from current HEAD

Stop stale local PO Agent and Task API processes.

Start Task API from the repository checkout with the discovered MCP-SWTR URL:

```bash
cd task-api
SWTR_MCP_SSE_URL="<working_sse_url>" \
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

Record PIDs, ports and process commands.

## Phase 3 — Runtime and transport proof

Call PO Agent diagnostics:

```bash
curl -s http://127.0.0.1:8004/api/v1/ops/as21-diagnostics
```

Required:

- `package_root = expected_package_root`;
- `git.loaded_package_root.head = START_HEAD`;
- `git.expected_package_root.head = START_HEAD`;
- module paths for `po_agent` and `po_agent.harness.sprint_intelligence` are `OK`;
- no secrets or token values in the response;
- `SUSPICIOUS_PYTHONPATH_COUNT = 0` or only explicitly justified known false positives under the expected current repository root.

Call Task API:

```bash
curl -s http://127.0.0.1:8003/health
curl -s http://127.0.0.1:8003/openapi.json
curl -s http://127.0.0.1:8003/api/v1/swtr-read/health
```

Required OpenAPI paths:

- `/api/v1/tasks` or `/api/v1/tasks/`;
- `/api/v1/swtr-read/health`;
- `/api/v1/swtr-read/tasks/{task_code}`;
- `/api/v1/swtr-read/sprints/{sprint_id}/tasks`.

Required `/api/v1/swtr-read/health` result:

- status connected;
- transport `sse`;
- required MCP tool names present.

## Phase 4 — Owner smoke regression check

Run these queries against PO Agent `/api/v1/query` with fresh session IDs:

| Case | Query | Expected |
|------|-------|----------|
| O1 | `Покажи задачи Безрукова` | COMPLETED with AS21-backed tasks if source has them; no fake adapter |
| O2 | `Покажи открытые задачи Гаранина из пространства DMS` | COMPLETED or source-backed clarification; no HTTP 500 |
| O3 | `Покажи задачи Гаранина в спринте DMS-SPRNT-2` | COMPLETED, source-backed clarification or fail-closed; no foreign-sprint false green |
| O4 | `Покажи здоровье спринта DMS-SPRNT-2` | COMPLETED or source-backed NEEDS_CLARIFICATION/FAILED; no internal `KeyError` |
| O5 | `Покажи список спринтов по DMS` | controlled response or clarification; no internal `KeyError`, no HTTP 500 |

Use `source_id` as canonical SWTR task key when `id` is an internal UUID.

## Phase 5 — Bounded oracle retest

Do not use the PO Agent result as oracle.

For `DMS-SPRNT-2`:

1. Call:
   `GET /api/v1/swtr-read/sprints/DMS-SPRNT-2/tasks?complete=true`
2. Extract candidate task keys from the live MCP-SWTR payload.
3. For each candidate key, call:
   `GET /api/v1/swtr-read/tasks/<TASK_KEY>`
4. From each authoritative unit extract:
   - task key;
   - assignee/login;
   - status;
   - space/product;
   - `scrum_board_plugin_sprint`.
5. Include a task in `ORACLE_KEYS_GARANIN_DMS_SPRNT_2` only when:
   - the authoritative per-task `scrum_board_plugin_sprint` exactly equals `DMS-SPRNT-2`;
   - the authoritative assignee/login matches Garanin.
6. Compare exact sets:
   - `AGENT_KEYS_O3`;
   - `ORACLE_KEYS_GARANIN_DMS_SPRNT_2`;
   - `MISSING_KEYS`;
   - `EXTRA_KEYS`.
7. Count and report any task whose authoritative sprint is not `DMS-SPRNT-2`.

If O3 correctly asks for source-backed clarification because Garanin is ambiguous, record that as clarification and run the same bounded oracle for the clarified login that the source evidence supports. Do not silently substitute people.

If the sprint endpoint returns paginated data, use its documented `complete=true` behavior and record `complete`, `completeness_source`, page count and any pagination limitation.

## Acceptance

046 is GREEN only if:

- runtime identity proof passes;
- Task API route contract is `SWTR_READ`;
- MCP-SWTR transport is connected through `/api/v1/swtr-read/health`;
- required MCP tool names are present;
- owner smoke tests produce no HTTP 500 and no internal `KeyError`;
- bounded oracle path is proven;
- no full tenant-wide sync was run;
- no production/source/config files are modified by QA;
- `FALSE_GREEN_COUNT = 0`;
- `FOREIGN_SPRINT_TASK_COUNT = 0`;
- `QUERY_HTTP_500_COUNT = 0`;
- `INTERNAL_KEYERROR_COUNT = 0`.

046 is BLOCKED if runtime identity and route contract pass, but the only remaining blocker is unavailable MCP-SWTR transport or missing local credential/platform permission.

046 is RED if there is a production regression, wrong runtime, missing `/api/v1/swtr-read/*` route contract, false green, silent slot drop, internal `KeyError`, HTTP 500, or if the agent returns tasks that the bounded oracle disproves.

## Required report sections

The report must contain:

- branch and `START_HEAD`;
- report commit SHA;
- PIDs/ports/process commands;
- MCP-SWTR SSE URL used, without tokens;
- runtime identity diagnostic evidence;
- Task API route and `/api/v1/swtr-read/health` evidence;
- owner smoke table O1-O5;
- bounded oracle method;
- per-task authoritative SWTR relation for every oracle/agent task key;
- exact key-set diffs;
- all mismatch traces;
- blocker/manual action if BLOCKED.

## Required footer

```text
ASSIGNMENT_ID = CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046
START_HEAD = <sha>
REPORT_COMMIT = <sha_after_commit_or_PENDING_BEFORE_COMMIT>
AS21_DIAGNOSTIC_ENDPOINT = PASS|FAIL|BLOCKED
DIAGNOSTIC_SECRET_LEAK = YES|NO
PO_AGENT_IMPORT_ROOT_OK = YES|NO
PO_AGENT_GIT_HEAD_OK = YES|NO
SPRINT_INTELLIGENCE_IMPORT_ROOT_OK = YES|NO
SUSPICIOUS_PYTHONPATH_COUNT = n
TASK_API_HEALTH = PASS|FAIL|BLOCKED
TASK_API_ENTRYPOINT_CURRENT = YES|NO
TASK_API_ROUTE_CONTRACT = SWTR_READ|LEGACY_SWTR_ONLY|MISSING|UNKNOWN
WRONG_TASK_API_PROCESS = YES|NO
SWTR_READ_ROUTES_PRESENT = YES|NO
MCP_SWTR_SSE_URL_USED = <url_without_tokens>|NONE
MCP_SWTR_TRANSPORT_CONNECTED = YES|NO
MCP_SWTR_TOOLS_PRESENT = YES|NO
SWTR_TRANSPORT_CLASSIFICATION = HEALTHY|MCP_SWTR_UNAVAILABLE|MCP_SWTR_MISSING_CREDENTIAL|WRONG_TASK_API_PROCESS|UNKNOWN
FULL_TASK_SYNC_RUN = YES|NO
BOUNDED_ORACLE_ONLY = YES|NO
ORACLE_PATH_PROVEN = YES|NO
OWNER_SMOKE_O1 = PASS|FAIL|BLOCKED
OWNER_SMOKE_O2 = PASS|FAIL|BLOCKED
OWNER_SMOKE_O3 = PASS|FAIL|BLOCKED
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
046_VERDICT = GREEN|RED|BLOCKED
READY_TO_RESUME_017_V2 = YES|NO
```

`READY_TO_RESUME_017_V2 = YES` only if 046 is GREEN and `ORACLE_PATH_PROVEN = YES`.

## Commit and stop

Before commit:

```bash
git status --short
git add -- qa_reports/CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046.md
git diff --cached --name-only
```

The staged file list must contain exactly:

```text
qa_reports/CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046.md
```

Commit subject:

`qa: CORE8_MCP_SWTR_TRANSPORT_UNBLOCK_AND_ORACLE_RETEST_046`

Push to the same branch. Return commit SHA, final verdict and complete report contents. Then stop.
