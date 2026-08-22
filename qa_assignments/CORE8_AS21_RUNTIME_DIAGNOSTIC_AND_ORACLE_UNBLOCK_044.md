# Assignment 044 — AS21 Runtime Diagnostic and Oracle Unblock

## Purpose

Assignment 043 proved that ordinary task search can return AS21-backed tasks, but acceptance remains blocked by runtime hygiene:

- PO Agent may import code from a conflicting adjacent checkout instead of this repository;
- Task API may be current while `/api/v1/swtr-read/*` is unavailable because MCP-SWTR transport is not running;
- full tenant-wide task sync is not required for the narrow oracle proof.

Assignment 044 validates the new operational AS21 diagnostic endpoint and uses it to unblock QA without mutating production code, runners, prompts, AS21/SWTR data or repository configuration.

## Repository

`Sovietbear86/PO-Agent-Architecture-Review`

## Branch

`feat/core8-real-query-hardening-v2`

## Allowed output

Commit and push only:

`qa_reports/CORE8_AS21_RUNTIME_DIAGNOSTIC_AND_ORACLE_UNBLOCK_044.md`

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
4. Verify `START_HEAD` contains the production diagnostic fix for `/api/v1/ops/as21-diagnostics`.
5. Verify no prohibited files are staged.
6. Verify this assignment and allowed report path are active in `GIGACODE_NEXT_ACTION.md`.
7. Read `qa_reports/CORE8_RUNTIME_WIRING_AND_SPRINT_GUARD_RETEST_043.md` and this assignment.

If preflight fails, write the allowed 044 report with `044_VERDICT = BLOCKED`, include exact evidence, commit only that report, push and stop.

## Phase 1 — Validate AS21 diagnostic endpoint

Start Task API and PO Agent from the current repository root, not from any adjacent checkout:

- Task API on `127.0.0.1:8003`;
- PO Agent on `127.0.0.1:8004`;
- `PO_AGENT_AS21_MODE=task-api`;
- `PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8003`;
- configured semantic LLM endpoint;
- no FakeAS21Adapter for acceptance evidence.

Call:

```bash
curl -s http://127.0.0.1:8004/api/v1/ops/as21-diagnostics
```

Required evidence:

- `settings.as21_mode = task-api`;
- `settings.task_api_base_url = http://127.0.0.1:8003`;
- `module_paths.po_agent.state = OK`;
- `module_paths.po_agent.harness.sprint_intelligence.state = OK`;
- no `suspicious_sys_path_entries` that point to adjacent `PO_Agent_Harness`;
- `task_api.required_paths_present = true`;
- `task_api.wrong_task_api_process = false`;
- diagnostic response contains no secrets or token values;
- `oracle_guidance.full_task_sync_required = false`;
- `repair_actions` include restart commands for PO Agent and Task API.

If module path is wrong, use only the diagnostic-provided safe repair command: restart PO Agent from this repository root with `unset PYTHONPATH`. Then repeat the diagnostic call and record before/after payloads.

## Phase 2 — Task API and SWTR-read classification

Using the diagnostic payload plus direct HTTP evidence, classify the source state:

- `TASK_API_HEALTH = PASS|FAIL`;
- `SWTR_READ_ROUTES_PRESENT = YES|NO`;
- `WRONG_TASK_API_PROCESS = YES|NO`;
- `SWTR_TRANSPORT_AVAILABLE = YES|NO`;
- `SWTR_TRANSPORT_CLASSIFICATION = HEALTHY|MCP_SWTR_UNAVAILABLE|DIRECT_SWTR_FORBIDDEN|WRONG_TASK_API_PROCESS|UNKNOWN`.

If `/api/v1/swtr-read/*` returns 502/503, record transport evidence and do not run full task sync. This is a transport blocker, not a proof that task-search is broken.

## Phase 3 — Owner smoke tests

Run these queries against PO Agent `/api/v1/query` with fresh sessions:

| Case | Query | Expected |
|------|-------|----------|
| O1 | `Покажи задачи Безрукова` | COMPLETED with AS21-backed tasks if source has them; no fake adapter |
| O2 | `Покажи открытые задачи Гаранина из пространства DMS` | COMPLETED or source-backed clarification; no HTTP 500 |
| O3 | `Покажи задачи Гаранина в спринте DMS-SPRNT-2` | COMPLETED, source-backed clarification or fail-closed; no foreign-sprint false green |
| O4 | `Покажи здоровье спринта DMS-SPRNT-2` | COMPLETED or source-backed NEEDS_CLARIFICATION/FAILED; no internal `KeyError` |
| O5 | `Покажи список спринтов по DMS` | controlled response or clarification; no internal `KeyError`, no HTTP 500 |

For any returned tasks, use `source_id` as canonical SWTR task key when `id` is an internal UUID.

## Phase 4 — Bounded oracle only

Do not sync all tasks. For oracle proof, use the narrowest available read-only source path:

1. If Task API `/api/v1/swtr-read/*` is healthy, hydrate only candidate keys required by O1/O3.
2. Else if MCP-SWTR transport is available from the existing local setup, read only candidate task units required by O1/O3.
3. Else if direct SWTR is accessible, read only candidate task units required by O1/O3.
4. Else mark `ORACLE_PATH_PROVEN = NO` with exact source transport evidence.

For every proven oracle case include:

- query;
- endpoint/tool used;
- non-secret request shape;
- exact `ORACLE_KEYS`;
- exact `AGENT_KEYS`;
- `MISSING_KEYS`;
- `EXTRA_KEYS`;
- authoritative per-task sprint relation when sprint filtering is involved.

## Acceptance

044 is GREEN only if:

- diagnostic endpoint is reachable and non-secret;
- runtime module paths point to this repository;
- Task API process is current and has `/api/v1/swtr-read/*` routes;
- owner smoke tests O1-O5 produce no HTTP 500 and no internal `KeyError`;
- no full tenant-wide task sync was run;
- if source transport is available, at least one bounded oracle exact-set proof is recorded;
- `FALSE_GREEN_COUNT = 0`;
- `QUERY_HTTP_500_COUNT = 0`;
- `INTERNAL_KEYERROR_COUNT = 0`;
- no prohibited files are modified or committed.

If the only blocker is external SWTR/MCP transport unavailability while runtime wiring and owner smokes are otherwise correct, mark BLOCKED rather than RED.

## Required footer

```text
ASSIGNMENT_ID = CORE8_AS21_RUNTIME_DIAGNOSTIC_AND_ORACLE_UNBLOCK_044
START_HEAD = <sha>
REPORT_COMMIT = <sha_after_commit_or_PENDING_BEFORE_COMMIT>
AS21_DIAGNOSTIC_ENDPOINT = PASS|FAIL|BLOCKED
DIAGNOSTIC_SECRET_LEAK = YES|NO
PO_AGENT_IMPORT_ROOT_OK = YES|NO
SPRINT_INTELLIGENCE_IMPORT_ROOT_OK = YES|NO
SUSPICIOUS_PYTHONPATH_COUNT = n
TASK_API_HEALTH = PASS|FAIL|BLOCKED
TASK_API_ENTRYPOINT_CURRENT = YES|NO
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
044_VERDICT = GREEN|RED|BLOCKED
READY_TO_RESUME_017_V2 = YES|NO
```

`READY_TO_RESUME_017_V2 = YES` only if 044 is GREEN and `ORACLE_PATH_PROVEN = YES`.

## Commit and stop

Before commit:

```bash
git status --short
git add -- qa_reports/CORE8_AS21_RUNTIME_DIAGNOSTIC_AND_ORACLE_UNBLOCK_044.md
git diff --cached --name-only
```

The staged file list must contain exactly:

```text
qa_reports/CORE8_AS21_RUNTIME_DIAGNOSTIC_AND_ORACLE_UNBLOCK_044.md
```

Commit subject:

`qa: CORE8_AS21_RUNTIME_DIAGNOSTIC_AND_ORACLE_UNBLOCK_044`

Push to the same branch. Return commit SHA, final verdict and complete report contents. Then stop.
