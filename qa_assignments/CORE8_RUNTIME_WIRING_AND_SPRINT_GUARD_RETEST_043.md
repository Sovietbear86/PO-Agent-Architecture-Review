# Assignment 043 — Runtime Wiring and Sprint Guard Retest

## Purpose

Assignment 042 was BLOCKED by QA/runtime wiring, not by proof that PO Agent cannot return real tasks. Manual smoke tests after 042 show that PO Agent can return AS21-backed task-search results, while a separate sprint capability path can still fail with `KeyError: 'sprint_id'`.

Retest the production fix that:

1. accepts both runtime env naming styles: `AS21_MODE`/`TASK_API_BASE_URL` and `PO_AGENT_AS21_MODE`/`PO_AGENT_TASK_API_BASE_URL`;
2. prevents sprint capabilities from executing without required source slots, returning controlled clarification/fail-closed behavior instead of internal `KeyError`;
3. treats `/api/v1/tasks[*].source_id` as the canonical SWTR task key when `id` is an internal UUID.

## Repository

`Sovietbear86/PO-Agent-Architecture-Review`

## Branch

`feat/core8-real-query-hardening-v2`

## Allowed output

Commit and push only:

`qa_reports/CORE8_RUNTIME_WIRING_AND_SPRINT_GUARD_RETEST_043.md`

Do not commit JSON, temporary scripts, runner changes, config changes, logs, `.env`, credentials, historical reports, roadmap edits, or production changes.

## Fixed role

You are QA/tester only. Do not modify production code, prompts, adapters, tests, fixtures, QA runners, acceptance runners, repository/local configuration, AS21/SWTR data, historical reports, roadmap files or learning state.

Do not copy MCP-SWTR source into this repository. Do not run full tenant-wide task sync for this assignment. Do not weaken or tune the oracle.

## Autonomous execution

The repository owner pre-authorizes this QA batch. Do not ask for confirmation after each step, integration call, TS case, local service restart, read-only AS21/SWTR query, MCP-SWTR diagnostic, Task API diagnostic, HTTP diagnostic, test command, allowed report commit, or allowed report push.

Ask only if continuing requires a missing credential, unavoidable platform approval, write outside the report allowlist, production/source-data/config mutation, destructive out-of-scope action, or scope expansion.

## Mandatory preflight

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `START_HEAD = git rev-parse HEAD`.
4. Verify no prohibited files are staged.
5. Verify this assignment and allowed report path are active in `GIGACODE_NEXT_ACTION.md`.
6. Read `qa_reports/CORE8_017V2_READINESS_ORACLE_RETEST_042.md` and this assignment.

If preflight fails, write the allowed 043 report with `043_VERDICT = BLOCKED`, include exact evidence, commit only that report, push, and stop.

## Phase 1 — Service restart and runtime wiring

Restart from current `HEAD`:

- Task API on `127.0.0.1:8003`;
- PO Agent on `127.0.0.1:8004`;
- real AS21/SWTR source path;
- configured semantic LLM endpoint;
- production semantic interpreter;
- no FakeAS21Adapter for acceptance evidence.

Run two PO Agent startup variants, one at a time:

### Variant A — legacy env names

```bash
AS21_MODE=task-api \
TASK_API_BASE_URL=http://127.0.0.1:8003 \
python3 -m uvicorn po_agent.main:app --host 127.0.0.1 --port 8004
```

### Variant B — PO_AGENT-prefixed env names

```bash
PO_AGENT_AS21_MODE=task-api \
PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8003 \
python3 -m uvicorn po_agent.main:app --host 127.0.0.1 --port 8004
```

For each variant, capture `/live`, `/health`, and `/api/v1/health`.

Required:

- root `/health` is readiness-aware;
- `/health` and `/api/v1/health` agree;
- adapter/mode is task-api, not fake;
- `source_status` is healthy;
- `runtime_init_error` is null.

If either env variant starts in fake mode, mark RED with exact health payloads.

## Phase 2 — Task API entrypoint and SWTR-read diagnostics

Verify that port `8003` is the repository Task API started from current `HEAD`, not a stale/wrong process:

1. Capture process command for port `8003`.
2. Capture Task API `/health`.
3. Capture Task API `/openapi.json` and verify paths include `/api/v1/tasks`, `/api/v1/swtr-read/health`, `/api/v1/swtr-read/tasks/{task_code}`, and `/api/v1/swtr-read/sprints/{sprint_id}/tasks`.
4. Call `/api/v1/swtr-read/health`.

If `/api/v1/swtr-read/*` returns 404 while `/openapi.json` lacks those paths, the wrong Task API process is running. Record `WRONG_TASK_API_PROCESS = YES` and exact restart command. Do not claim production source defect from that 404.

If `/api/v1/swtr-read/*` returns 502/503, record MCP/SWTR transport evidence. Do not copy MCP source and do not run full sync.

## Phase 3 — Manual smoke cases from repository owner

Execute these smoke queries against PO Agent `/api/v1/query` with fresh sessions:

| Case | Query | Expected |
|------|-------|----------|
| M1 | `Покажи открытые задачи Гаранина из пространства DMS` | COMPLETED or source-backed clarification; no HTTP 500 |
| M2 | `Покажи задачи Безрукова` | COMPLETED with AS21-backed tasks if source has them; no fake adapter |
| M3 | `Покажи здоровье спринта DMS-SPRNT-2` | COMPLETED or source-backed NEEDS_CLARIFICATION; no HTTP 500 |
| M4 | `Покажи список спринтов по DMS` | controlled response or clarification; no `KeyError`, no HTTP 500 |

For all returned tasks, treat `source_id` as the SWTR task key when `id` is an internal UUID. Do not require an additional `key` field in `/api/v1/tasks` for this assignment.

## Phase 4 — Narrow source-backed oracle proof

Prove one independent source-backed oracle path for a bounded subset. Do not run the full 42-case matrix.

Allowed oracle paths:

1. Task API `/api/v1/swtr-read/*` current source hydration;
2. MCP-SWTR read-only calls through the existing local MCP transport;
3. direct SWTR/Jira REST if accessible.

For at least two task-search smoke cases, include endpoint/tool, non-secret request shape, sample hydrated task unit, exact `ORACLE_KEYS`, exact `AGENT_KEYS`, `MISSING_KEYS`, and `EXTRA_KEYS`.

`source_id` is acceptable as the canonical key when reading from Task API `/api/v1/tasks`.

## Acceptance

043 is GREEN only if:

- both env naming variants start PO Agent in task-api mode;
- root `/health` is readiness-aware and agrees with `/api/v1/health`;
- Task API entrypoint is proven current and not stale;
- M1-M4 execute without HTTP 500 or internal `KeyError`;
- at least two smoke cases have independent exact-set oracle evidence;
- `FALSE_GREEN_COUNT = 0`;
- `QUERY_HTTP_500_COUNT = 0`;
- `INTERNAL_KEYERROR_COUNT = 0`;
- no prohibited files are modified or committed.

If source transport is unavailable but process/env wiring is correct, mark BLOCKED with exact transport evidence. If wiring or sprint guard fails, mark RED.

## Required footer

```text
ASSIGNMENT_ID = CORE8_RUNTIME_WIRING_AND_SPRINT_GUARD_RETEST_043
START_HEAD = <sha>
REPORT_COMMIT = <sha_after_commit_or_PENDING_BEFORE_COMMIT>
ENV_ALIAS_LEGACY_MODE = PASS|FAIL|BLOCKED
ENV_ALIAS_PO_AGENT_MODE = PASS|FAIL|BLOCKED
ROOT_HEALTH_READINESS_AWARE = YES|NO
HEALTH_PAYLOADS_AGREE = YES|NO
TASK_API_ENTRYPOINT_CURRENT = YES|NO
WRONG_TASK_API_PROCESS = YES|NO
SWTR_READ_ROUTES_PRESENT = YES|NO
ORACLE_PATH_PROVEN = YES|NO
ORACLE_PATH_TYPE = TASK_API_SWTR_READ|MCP_SWTR|DIRECT_SWTR|NONE
MANUAL_SMOKE_M1 = PASS|FAIL|BLOCKED
MANUAL_SMOKE_M2 = PASS|FAIL|BLOCKED
MANUAL_SMOKE_M3 = PASS|FAIL|BLOCKED
MANUAL_SMOKE_M4 = PASS|FAIL|BLOCKED
INTERNAL_KEYERROR_COUNT = n
QUERY_HTTP_500_COUNT = n
FALSE_GREEN_COUNT = n
RUNNER_MODIFIED = NO
PRODUCTION_MODIFIED_BY_QA = NO
UNAUTHORIZED_FILES_COMMITTED = NO
043_VERDICT = GREEN|RED|BLOCKED
READY_TO_RESUME_017_V2 = YES|NO
```

`READY_TO_RESUME_017_V2 = YES` only if 043 is GREEN.

## Commit and stop

Before commit:

```bash
git status --short
git add -- qa_reports/CORE8_RUNTIME_WIRING_AND_SPRINT_GUARD_RETEST_043.md
git diff --cached --name-only
```

The staged file list must contain exactly:

```text
qa_reports/CORE8_RUNTIME_WIRING_AND_SPRINT_GUARD_RETEST_043.md
```

Commit subject:

`qa: CORE8_RUNTIME_WIRING_AND_SPRINT_GUARD_RETEST_043`

Push to the same branch. Return commit SHA, final verdict, and complete report contents. Then stop.
