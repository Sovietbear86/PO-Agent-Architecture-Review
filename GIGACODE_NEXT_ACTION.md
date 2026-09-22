# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_202_V4_POST_GREEN_HYGIENE_SMOKE`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT start Wave S.
Do NOT add new skills.

## Context
A201 is the certified clean zero-RED pre-Wave-S checkpoint:
- 27/27 existing V4 skills tested;
- 20 GREEN / 7 SOURCE_CONDITIONAL / 0 RED;
- Browser C 10/10;
- local-store factual reads 0;
- dummy-55 11/11;
- clarification-continuation defect D-A200-1 CLOSED.

After A201 the owner made a deliberately small hygiene-only change set:
1. `5410d00179d24f80671733dd697e0dda68477e10`
   - fixes 3 stale owner tests that still unpacked the pre-continuation 2-tuple API.
2. `ce5d74ed3f01ff79061b60453d96b82b94a3a724`
   - adds lightweight Task API source-health probe.
3. `10891bc56237ba40ddd7908ef7a708b05e27bc5c`
   - Agent `/health` no longer performs an unscoped task collection scan.
4. `3ce03af5c9f90dd2de3cc3ebc5e1a7be91aa9fbf`
   - regression test: health must call source-health and must not call `search_tasks("")`.
5. docs only after that.

No skill/plugin/Agent Core/planner/completion behavior was intentionally changed after A201.

## Mission
Certify the post-A201 hygiene changes without reopening the already-completed full catalog campaign.

A202 is a **compact smoke gate**, not a new full 27-skill certification. It may pass only if the hygiene changes are isolated and the high-risk A201 paths remain intact.

## Phase 0 — diff/static gate
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record exact START_HEAD; tracked worktree clean.
3. Diff A201 START_HEAD `ae5caeed503ebc3839a5957cd612fc1751cbada3` to START_HEAD.
4. Confirm:
   - no new skill/plugin business logic after A201;
   - no Agent Core/planner/completion behavior change after A201;
   - test-only clarification tuple update is compatible with the generic continuation contract;
   - health change is operational only and performs no task collection query;
   - no local-store fallback was introduced.

Any unexpected product-behavior change => RED.

## Phase 1 — focused automated tests
Run:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_v4_owner_fix_contracts.py -v
python -m pytest tests/test_v4_browser_api_contract.py -v
python -m pytest tests/test_agent_core_v4_completion_contract.py -v
python -m pytest tests/test_agent_core_v4_plugin_registry.py tests/test_agent_core_v4_task_catalog.py -v
```

Require:
- stale 3 clarification owner tests now GREEN;
- generic continuation state round-trip still GREEN;
- internal continuation state still hidden from public payload;
- all completion-frontier/pinned-goal tests GREEN;
- dummy-55/plugin tests GREEN;
- health test proves `search_tasks` is never called by readiness.

## Phase 2 — live health hygiene
With current services:
- GET Agent `/live`;
- GET Agent `/health`;
- GET Task API `/api/v1/swtr-read/health`.

Require:
- `/live` 200;
- Agent `/health` returns within a small operational budget (target <= 5s; record actual latency);
- Task API source-health 200;
- inspect logs and prove Agent `/health` caused **0** unscoped `task-query` or `GET /api/v1/tasks` reads.

If source-health itself is down, classify source outage separately; do not substitute a task scan.

## Phase 3 — retained live smoke
Fresh sessions, concurrency 1:
1. DMS-380 lookup -> assignee collection, 2x exact.
2. `Задачи Калачанова с вложениями в WMB`, 2x exact.
3. `Найди задачи Калачанова про 2027 в WMB`, 2x exact.
4. current-sprint multi-filter, 2x exact.
5. period-sprint clarification -> DMS continuation, at least 2 successful continuations if model emits typed options.
6. ambiguous person -> option-click continuation, 1 successful continuation.
7. one SOURCE_CONDITIONAL release/history path fail-closed.

Require no false completion, no all-space leak, no internal continuation-state leak, runtime_contract where contracted.

## Phase 4 — Browser C smoke
Browser:
- one ordinary factual task query;
- person attachments;
- one clarification + option click;
- one SOURCE_CONDITIONAL path.

Require no generic V4 error for supported cases and no continuation internals in UI response.

## Phase 5 — plugin extensibility
Run dummy-55 gate once.
Must remain GREEN with zero Agent Core/planner/runtime business edits.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_POST_GREEN_HYGIENE_SMOKE_GREEN`
- `AGENT_CORE_V4_POST_GREEN_HYGIENE_SMOKE_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires:
- focused tests GREEN;
- health no longer scans tasks;
- retained high-risk live paths exact/safe;
- Browser C smoke GREEN;
- dummy-55 GREEN;
- no new RED.

If RED:
STOP. Do not start Wave S.

If GREEN:
recommend:
**Create immutable/rollback checkpoint for the tested HEAD and wait for explicit owner/user approval before Wave S #23–32.**

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_POST_GREEN_HYGIENE_SMOKE_202.md`

## Service keepalive
Leave UI/backend/Task API/MCP running and return:
- verdict;
- exact START_HEAD;
- report commit;
- URLs/ports/PIDs/health;
- measured Agent /health latency.
Then stop.
