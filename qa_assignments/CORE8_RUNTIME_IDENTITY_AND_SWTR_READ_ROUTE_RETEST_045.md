# Assignment 045 — Runtime Identity and SWTR-Read Route Retest

## Purpose

Assignment 044 showed that owner smoke queries can run without HTTP 500 or internal `KeyError`, but oracle proof is still blocked because the running Task API did not expose `/api/v1/swtr-read/*` routes. It also revealed a diagnostic weakness: a PO Agent process imported from a wrong checkout could still report module paths as `OK` when the diagnostic compared paths against its own loaded location.

Assignment 045 validates the hardened AS21 diagnostic and proves that both PO Agent and Task API are running from the current repository/HEAD before attempting any oracle hydration.

## Repository

`Sovietbear86/PO-Agent-Architecture-Review`

## Branch

`feat/core8-real-query-hardening-v2`

## Allowed output

Commit and push only:

`qa_reports/CORE8_RUNTIME_IDENTITY_AND_SWTR_READ_ROUTE_RETEST_045.md`

Do not commit JSON, helper scripts, runner changes, config changes, logs, `.env`, credentials, historical reports, roadmap edits or production changes.

## Fixed role

You are QA/tester only. Do not modify production code, prompts, adapters, tests, fixtures, QA runners, acceptance runners, repository/local configuration, AS21/SWTR data, historical reports, roadmap files or learning state.

Do not copy MCP-SWTR source into this repository. Do not run full tenant-wide task sync. Do not weaken or tune the oracle.

## Autonomous execution

The repository owner pre-authorizes this QA batch. Do not ask for confirmation after each routine step, integration call, local service restart, read-only AS21/SWTR query, MCP-SWTR diagnostic, Task API diagnostic, HTTP diagnostic, test command, allowed report commit or allowed report push.

Ask only if continuing requires a missing credential, unavoidable platform approval, write outside the report allowlist, production/source-data/config mutation, destructive out-of-scope action or scope expansion.

## Mandatory preflight

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `START_HEAD = git rev-parse HEAD`.
4. Verify `START_HEAD` contains the hardened diagnostic fields:
   - `expected_package_root`;
   - `git.loaded_package_root.head`;
   - `git.expected_package_root.head`;
   - `task_api.legacy_swtr_paths_present`.
5. Verify no prohibited files are staged.
6. Verify this assignment and allowed report path are active in `GIGACODE_NEXT_ACTION.md`.
7. Read `qa_reports/CORE8_AS21_RUNTIME_DIAGNOSTIC_AND_ORACLE_UNBLOCK_044.md` and this assignment.

If preflight fails, write the allowed 045 report with `045_VERDICT = BLOCKED`, include exact evidence, commit only that report, push and stop.

## Phase 1 — Restart from current repository identity

Stop stale local PO Agent and Task API processes.

Start Task API from the repository checkout:

```bash
cd task-api
python3 -m uvicorn main:app --host 127.0.0.1 --port 8003
```

Start PO Agent from the repository checkout and bind expected runtime identity:

```bash
cd po-agent-platform-v2
unset PYTHONPATH
PO_AGENT_AS21_MODE=task-api \
PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8003 \
PO_AGENT_EXPECTED_PACKAGE_ROOT="$(pwd)" \
PO_AGENT_EXPECTED_HEAD="<START_HEAD>" \
python3 -m uvicorn po_agent.main:app --host 127.0.0.1 --port 8004
```

Do not start either service from adjacent `PO_Agent_Harness`, `MyTestProject_1`, old virtualenv source paths or any other checkout.

## Phase 2 — Diagnostic identity proof

Call:

```bash
curl -s http://127.0.0.1:8004/api/v1/ops/as21-diagnostics
```

Required:

- `status` is not degraded by `po_agent_import_root_mismatch`;
- `status` is not degraded by `po_agent_git_head_mismatch`;
- `expected_package_root` points to the current `po-agent-platform-v2`;
- `package_root` equals `expected_package_root`;
- `git.loaded_package_root.head = START_HEAD`;
- `git.expected_package_root.head = START_HEAD`;
- `module_paths.po_agent.state = OK`;
- `module_paths.po_agent.harness.sprint_intelligence.state = OK`;
- `SUSPICIOUS_PYTHONPATH_COUNT = 0`;
- diagnostic response contains no secrets or token values.

If this phase fails, do not continue to oracle. Report RED or BLOCKED with exact diagnostic payload and stop.

## Phase 3 — Task API route contract proof

Capture Task API:

- process command for port `8003`;
- `/health`;
- `/openapi.json`.

Required OpenAPI paths:

- `/api/v1/tasks` or `/api/v1/tasks/`;
- `/api/v1/swtr-read/health`;
- `/api/v1/swtr-read/tasks/{task_code}`;
- `/api/v1/swtr-read/sprints/{sprint_id}/tasks`.

If only `/api/v1/swtr/*` paths are present and `/api/v1/swtr-read/*` paths are absent:

- record `TASK_API_ROUTE_CONTRACT = LEGACY_SWTR_ONLY`;
- record `WRONG_TASK_API_PROCESS = YES`;
- do not run full sync;
- write report and stop.

If `/api/v1/swtr-read/*` paths are present but return 502/503, classify as `MCP_SWTR_UNAVAILABLE`, not as a route-contract defect.

## Phase 4 — Owner smoke tests

Run these queries against PO Agent `/api/v1/query` with fresh sessions:

| Case | Query | Expected |
|------|-------|----------|
| O1 | `Покажи задачи Безрукова` | COMPLETED with AS21-backed tasks if source has them; no fake adapter |
| O2 | `Покажи открытые задачи Гаранина из пространства DMS` | COMPLETED or source-backed clarification; no HTTP 500 |
| O3 | `Покажи задачи Гаранина в спринте DMS-SPRNT-2` | COMPLETED, source-backed clarification or fail-closed; no foreign-sprint false green |
| O4 | `Покажи здоровье спринта DMS-SPRNT-2` | COMPLETED or source-backed NEEDS_CLARIFICATION/FAILED; no internal `KeyError` |
| O5 | `Покажи список спринтов по DMS` | controlled response or clarification; no internal `KeyError`, no HTTP 500 |

For any returned tasks, use `source_id` as canonical SWTR task key when `id` is an internal UUID.

## Phase 5 — Bounded oracle only

Do not sync all tasks.

If `/api/v1/swtr-read/*` is available, hydrate only the candidate keys required by O1/O3 and compare exact sets.

If `/api/v1/swtr-read/*` routes are present but MCP-SWTR transport is unavailable, mark `ORACLE_PATH_PROVEN = NO` with exact 502/503 evidence and classify the assignment as BLOCKED if all runtime identity and route-contract checks passed.

## Acceptance

045 is GREEN only if:

- diagnostic identity proof passes;
- Task API exposes `/api/v1/swtr-read/*` routes from current `START_HEAD`;
- owner smoke tests O1-O5 produce no HTTP 500 and no internal `KeyError`;
- no full tenant-wide task sync was run;
- if source transport is available, at least one bounded oracle exact-set proof is recorded;
- `FALSE_GREEN_COUNT = 0`;
- `QUERY_HTTP_500_COUNT = 0`;
- `INTERNAL_KEYERROR_COUNT = 0`;
- no prohibited files are modified or committed.

If runtime identity and route-contract checks pass but only MCP-SWTR transport is unavailable, mark BLOCKED rather than RED.

## Required footer

```text
ASSIGNMENT_ID = CORE8_RUNTIME_IDENTITY_AND_SWTR_READ_ROUTE_RETEST_045
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
SWTR_TRANSPORT_AVAILABLE = YES|NO
SWTR_TRANSPORT_CLASSIFICATION = HEALTHY|MCP_SWTR_UNAVAILABLE|DIRECT_SWTR_FORBIDDEN|WRONG_TASK_API_PROCESS|UNKNOWN
FULL_TASK_SYNC_RUN = YES|NO
ORACLE_PATH_PROVEN = YES|NO
OWNER_SMOKE_O1 = PASS|FAIL|BLOCKED
OWNER_SMOKE_O2 = PASS|FAIL|BLOCKED
OWNER_SMOKE_O3 = PASS|FAIL|BLOCKED
OWNER_SMOKE_O4 = PASS|FAIL|BLOCKED
OWNER_SMOKE_O5 = PASS|FAIL|BLOCKED
INTERNAL_KEYERROR_COUNT = n
QUERY_HTTP_500_COUNT = n
FALSE_GREEN_COUNT = n
RUNNER_MODIFIED = NO
PRODUCTION_MODIFIED_BY_QA = NO
UNAUTHORIZED_FILES_COMMITTED = NO
045_VERDICT = GREEN|RED|BLOCKED
READY_TO_RESUME_017_V2 = YES|NO
```

`READY_TO_RESUME_017_V2 = YES` only if 045 is GREEN and `ORACLE_PATH_PROVEN = YES`.

## Commit and stop

Before commit:

```bash
git status --short
git add -- qa_reports/CORE8_RUNTIME_IDENTITY_AND_SWTR_READ_ROUTE_RETEST_045.md
git diff --cached --name-only
```

The staged file list must contain exactly:

```text
qa_reports/CORE8_RUNTIME_IDENTITY_AND_SWTR_READ_ROUTE_RETEST_045.md
```

Commit subject:

`qa: CORE8_RUNTIME_IDENTITY_AND_SWTR_READ_ROUTE_RETEST_045`

Push to the same branch. Return commit SHA, final verdict and complete report contents. Then stop.
