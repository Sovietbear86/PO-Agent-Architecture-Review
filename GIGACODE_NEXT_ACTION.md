# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_194_V4_TASK_WAVE_CONSOLIDATED_REGATE`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT implement, refactor, fix, improve, or rewrite production code, frontend code, plugin code, tests, prompts, adapters, config, or architecture docs. Do not start Wave S. The owner has implemented the A192/A193 remediation bundle independently; A194 must certify or reject it.

## Start state
1. Stop/restart only project services you own/reuse as needed; do not kill unrelated processes.
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `git rev-parse HEAD` as `START_HEAD` and `git status --short`.
4. If tracked production/test/config files contain local modifications not already committed by the owner, STOP and report. Do not overwrite them.
5. Read first:
   - `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_ATTACHMENT_ORACLE_193.md`
   - `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_CATALOG_TASK_WAVE_192.md`
   - `V4_DOD_LOCK.md`
   - `V4_54_SKILL_MIGRATION_PLAN.md`
6. Permanent rollback remains `0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`.

## Owner remediation to audit
The owner attempted one consolidated fix for the A192/A193 defects while preserving Hermes/plugin architecture. Inspect at minimum:
- `task-api/app/routers/swtr_query.py`
- `task-api/app/routers/swtr_assignee.py`
- `task-api/main.py`
- `po-agent-platform-v2/src/po_agent/adapters/production_task_api.py`
- `po-agent-platform-v2/src/po_agent/harness/v4_plugin_registry.py`
- `po-agent-platform-v2/src/po_agent/harness/v4_plugins/_task_live_handlers.py`
- `po-agent-platform-v2/src/po_agent/harness/v4_plugins/task_catalog.py`
- `po-agent-platform-v2/src/po_agent/harness/v4_plugins/core.py`
- `po-agent-platform-v2/src/po_agent/api/v1/__init__.py`
- `po-agent-platform-v2/frontend/src/api/client.ts`
- `po-agent-platform-v2/frontend/src/recovery/WorkspaceApp.tsx`
- `po-agent-platform-v2/tests/test_v4_owner_fix_contracts.py`

## Mission
Independently answer all of the following:
1. Are all factual Task Wave reads now live-only (`Task API live facade -> MCP-SWTR -> REAL AS21`) with **zero production fallback to `/api/v1/tasks` / SQLite/local task store**?
2. Are A192 RED #2 text search, #7 natural-language assignee search, and #8 status-only/space+status search fixed against fresh Oracle B exact key sets?
3. Are A193 attachment rows #3–#6 fixed against fresh live file metadata, including exact single-task attachments for `WMB-30000` if still present?
4. Does `task.lookup` expose live attachments without breaking the A188 task->assignee->tasks contract?
5. Does Browser C clarification continuation preserve the original request instead of treating an option such as `DMS` as a new query?
6. Did the owner preserve the Hermes/V4 extension invariant: no business-skill/source special cases added to Agent Core/planner/runtime trajectory/completion engine?
7. Did any A188/A190/A191 GREEN scenario regress?

## Phase 0 — architecture / Hermes / source-path audit
Compare the current owner diff with the A193 tested baseline and permanent A188 checkpoint.

Mandatory checks:
- no owner edit to `agent_core_v4.py`, `agent_core_v4_reliable.py`, `agent_core_v4_robust.py`, planner decision strategy/model, or completion-engine internals for these fixes;
- Task search/attachment behavior is attached through plugin/capability contracts, not `if skill_id == ...` branches in Agent Core;
- `CapabilityBindingV4.handler_builder` is a generic trusted registry extension seam, mutually exclusive with existing handler/legacy bindings and fail-closed when malformed;
- helper modules prefixed `_` are not discovered as standalone plugins;
- adding another source-backed task skill can use the same plugin seam without core edits;
- no surname/person/task/sprint/query phrase is hardcoded in production;
- natural-name matching is generic and source-backed, ambiguity still fails closed;
- no production factual task-search path reads `/api/v1/tasks`, local SQLite/cache/snapshot, or silently falls back to it;
- source outage cannot become `REAL_EMPTY`/0;
- browser still calls only `/api/v1/query`, never MCP/SWTR/direct capability routes.

Any violation of these invariants => RED. Do not fix it.

## Phase 1 — build / focused contract gates
Run at minimum:

```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_v4_owner_fix_contracts.py -v
python -m pytest tests/test_agent_core_v4_plugin_registry.py -v
python -m pytest tests/test_agent_core_v4_task_catalog.py -v
python -m pytest tests/test_agent_core_v4_completion_contract.py -v
python -m pytest tests/test_v4_browser_api_contract.py -v
python -m pytest tests/ -k "v4" -v

cd ../task-api
python -m pytest -q

cd ../po-agent-platform-v2/frontend
npm run build
```

If the task-api suite has unrelated pre-existing failures, classify them precisely and run focused imports/routes needed for `swtr_query`/`swtr_assignee`; do not edit tests or code.

## Phase 2 — fresh live stack / route provenance
Start a **fresh stack from START_HEAD** on free ports:
- Task API
- PO Agent backend with V4 enabled
- frontend Browser C

Use REAL AS21/SWTR only, concurrency 1.

Before agent cases, independently prove:
- `/api/v1/swtr-read/health` connected;
- new `/api/v1/swtr-read/task-query` returns REAL_AS21 provenance;
- direct live exact task/file routes work;
- local `/api/v1/tasks` may be empty or populated but its contents MUST NOT affect any V4 factual answer.

Instrument/log route usage for tested factual cases. A194 requires evidence that production requests do not touch local `/api/v1/tasks` as a truth source.

## Phase 3 — A192 RED re-gate
Discover fresh source examples immediately before each test.

### #2 `task.search_text`
- discover a distinctive phrase from a live task title/description;
- Oracle B from live source;
- natural Agent query through public `/api/v1/query`;
- require exact task-key parity, dedicated skill reachability, REAL source provenance, `semantic_prepass_used=false` and successful runtime completion.

### #7 `task.search_assignee`
At minimum:
- `Задачи Андрея Жданова` (or fresh equivalent if source identity changed);
- one second natural full-name case not used by the owner implementation;
- compare exact key set with fresh source-backed assignee query.

Do not accept a test that supplies a canonical login in place of the natural name.

### #8 `task.search_status`
At minimum:
- `Покажи открытые задачи в DMS`;
- independently calculate the exact open/non-terminal key set from live source workflow semantics/statusType;
- exact key parity required.

No assignee/sprint should be needed merely to make status+space executable.

## Phase 4 — A193 attachment re-gate
Re-discover attachment truth fresh; do not merely reuse A193 remembered counts.

At minimum test:
1. `Проверь на наличие вложений задачу WMB-30000`
2. `Задачи Калачанова с вложениями в пространстве WMB`
3. `Найди задачи с вложениями Excel в WMB`
4. `Найди задачи с PDF-вложениями в WMB`
5. `Найди задачи с MSG-вложениями в WMB`

For `WMB-30000`, if the same five Excel files still exist, require exact file-name/type/size parity with direct live `/tasks/WMB-30000/files`. If source changed, record current truth and compare to that.

For the Kalachanov/WMB collection, independently enumerate the fresh live assignee task set and each candidate's live files. Compare exact attachment-bearing task keys and attachment metadata.

Required checks:
- specialized Excel/PDF/MSG fixed argument remains deterministic;
- requested person/space/task constraints are preserved;
- no false REAL_EMPTY;
- `task.lookup` observation/result contains live attachment metadata and still exposes canonical `assignee_login`/`assignee_id` needed by retained A188 composition.

## Phase 5 — clarification continuation Browser C
Use a fresh browser session and execute exactly:

`задачи Гаранина в сентябрьском спринте`

If the runtime validly asks for space, click the actual `DMS` option button.

Require:
- first `NEEDS_CLARIFICATION` response has non-null `clarification_id`;
- second browser payload keeps the same `session_id` and sends `clarification_id` + selected option;
- backend restores the original request/clarification context before re-planning;
- second trajectory preserves person + September sprint + DMS constraints;
- no standalone parsing of bare `DMS`;
- no generic English incomplete-query fallback;
- source-backed continuation reaches a correct result or a new **relevant** typed clarification.

Also test controls:
- valid clarification id used from a different session => Russian fail-closed context-lost response;
- invalid option not in offered options => typed Russian clarification, not re-planned standalone;
- a normal new query without clarification metadata does not inherit stale pending state.

Clarification state is generic dialogue infrastructure; reject any implementation tied specifically to Garanin/DMS/September.

## Phase 6 — full Task Wave terminal classifications
Re-run the canonical 20-row Task Wave sufficiently to issue a fresh terminal classification for every row:
- `GREEN_SOURCE_SUPPORTED`
- `SOURCE_CONDITIONAL`
- `RED`

No silent skips.

Rows previously source-conditional (#10 release, #16 history, #17 time-in-status, #18 aging if timestamp surface absent, #20 similar if complete corpus unavailable) may remain SOURCE_CONDITIONAL only when the **fresh live source** proves the required contract unavailable. Do not convert implementation defects into SOURCE_CONDITIONAL.

## Phase 7 — retained regression
After all fixes are exercised, run at minimum:
- DMS-380 lookup -> assignee -> task search 3x, exact Oracle parity;
- current sprint tasks 2x exact;
- active sprint list 2x;
- person + space + not_completed exact parity;
- B2 open-status classification;
- invented person/sprint/task negatives fail closed;
- plugin/dummy-55 gate structurally GREEN;
- Browser C runtime/session/UIContract retained.

No new A188/A190/A191 regression allowed.

## Phase 8 — service keepalive
After QA, leave the freshly started current-HEAD project stack running for manual user testing.

Return:
- frontend URL / port / PID / health;
- backend URL / port / PID / `/api/v1/health` status;
- Task API URL / port / PID / `/api/v1/swtr-read/health` status;
- exact START_HEAD used by all three.

Do not leave an old pre-fix stack masquerading as current HEAD.

## Allowed output
Create/commit/push **only**:

`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_CATALOG_TASK_WAVE_REGATE_194.md`

Do not modify production/frontend/tests/config/plans/plugins.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_CATALOG_TASK_WAVE_GREEN`
- `AGENT_CORE_V4_CATALOG_TASK_WAVE_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires:
- Hermes/plugin architecture invariant GREEN;
- live-source-only invariant GREEN;
- every source-supported Task row #1–20 GREEN;
- source-conditional rows proven from live source and fail-closed;
- attachment Oracle exact where supported;
- clarification continuation GREEN;
- no A188/A190/A191 regression.

If GREEN, recommendation:
**Proceed to owner Wave S (#21–32 Sprint/flow) through the plugin surface.**

## STOP
After committing/pushing only the QA report, keep the fresh services running, return the service URLs/PIDs/health, then stop and wait for the owner.
