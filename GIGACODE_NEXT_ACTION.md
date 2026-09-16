# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_192_V4_CATALOG_TASK_WAVE`

## Role lock
GigaCode is **QA/adversarial tester only**.

Do NOT implement, refactor, fix, improve, or rewrite production code, frontend code, plugin code, tests, prompts, adapters, config, or architecture docs. The owner has implemented the first V4-CATALOG wave independently.

## Start state
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record `git rev-parse HEAD` as `START_HEAD`.
3. Run `git status --short` and record it. Pre-existing local QA-only/untracked artifacts may remain if they are clearly not production/test/source changes and were already present before A192; do not delete them. If any tracked production/test/config file is locally modified, or ownership is unclear, STOP and report.
4. Permanent rollback remains `0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`.
5. A188, A190 and A191 are already GREEN. A192 must prove the Task Wave does not regress them.

## Authoritative scope
Read first:
- `V4_54_SKILL_MIGRATION_PLAN.md`
- `PO_AGENT_48_SKILL_MATRIX.md`
- `V4_DOD_LOCK.md`
- `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_BROWSER_UI_REGATE_191.md`

The canonical production denominator is **54 = frozen 48 + six reconciled additions**. A192 covers canonical Task rows **#1–20** only. Helper/composition skills do not alter that denominator.

## Owner changes to audit
At minimum inspect:
- `po-agent-platform-v2/src/po_agent/harness/v4_plugins/task_catalog.py`
- `po-agent-platform-v2/src/po_agent/harness/v4_plugins/core.py`
- `po-agent-platform-v2/src/po_agent/harness/v4_plugin_registry.py`
- `po-agent-platform-v2/tests/test_agent_core_v4_task_catalog.py`
- `po-agent-platform-v2/tests/test_agent_core_v4_plugin_registry.py`
- `po-agent-platform-v2/frontend/src/components/V4ResultPanel.tsx`
- `V4_54_SKILL_MIGRATION_PLAN.md`

## Mission
Independently certify the first progressive V4-CATALOG wave and answer all of the following:

1. Are all canonical Task skills #1–20 explicitly represented in the V4 progressive catalog?
2. Can the planner select/use the dedicated canonical skill for natural-language requests rather than relying on legacy phrase routing?
3. Are new skills implemented through the plugin surface with zero Agent Core/planner/runtime-trajectory business hardcode?
4. Do reused deterministic/source-backed legacy handlers preserve fresh REAL AS21 truth?
5. Do CompletionContract and UIContract metadata match actual result shapes?
6. Did any A188/A190/A191 GREEN scenario regress?

## Canonical Task denominator #1–20
The exact rows are:

1. `task.lookup`
2. `task.search_text`
3. `task.search_attachments`
4. `task.search_excel`
5. `task.search_pdf`
6. `task.search_msg`
7. `task.search_assignee`
8. `task.search_status`
9. `task.search_sprint`
10. `task.search_release`
11. `task.summary`
12. `task.quality`
13. `task.missing_requirements`
14. `task.acceptance`
15. `task.dependencies`
16. `task.history`
17. `task.time_in_status`
18. `task.aging`
19. `task.blockers`
20. `task.similar`

The exact V4 ids may share reusable capabilities, but every row above must be an explicit `SkillSpec` and terminally classified in the report.

## Phase 0 — architecture/static audit
Compare `START_HEAD` with A191 QA commit `dca5a3d31419841b3d5d36aa56869ca531569a7d` and with permanent checkpoint `0f03fca...`.

Verify:
- no edit to `agent_core_v4.py`, `agent_core_v4_reliable.py`, `agent_core_v4_robust.py`, planner strategy/model, or runtime trajectory/completion engine;
- catalog additions are trusted plugin artifacts discovered by the registry;
- no surname/person/task/sprint/release/query-phrase hardcode was added to production;
- new fixed binding arguments are generic extension-surface behavior, not task/entity routing;
- specialized Excel/PDF/MSG capabilities deterministically force their declared attachment type even if planner arguments conflict;
- registry ordering/duplicate/malformed contracts still fail closed;
- the 20 canonical Task ids are all present, while helper skills are not counted as extra denominator rows;
- Browser UI remains presentation-only and does not choose capabilities/source routes.

Any architectural invariant violation => RED. Do not fix it.

## Phase 1 — build/contract gates
Run at minimum:

```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4_task_catalog.py -v
python -m pytest tests/test_agent_core_v4_plugin_registry.py -v
python -m pytest tests/test_agent_core_v4_completion_contract.py -v
python -m pytest tests/test_v4_browser_api_contract.py -v
python -m pytest tests/ -k "v4" -v

cd frontend
npm run build
```

Known A191 hygiene: `npm ci` may still fail because of the pre-existing package-lock desync. Record it separately; do not modify package files in QA.

Acceptance:
- new Task Wave focused tests GREEN;
- A190 plugin/dummy-55 tests GREEN;
- completion tests GREEN;
- V4-focused suite has no new failure;
- frontend TypeScript/Vite build GREEN.

## Phase 2 — fresh REAL AS21 Oracle discovery
Start fresh Task API + PO Agent on fresh ports with V4 enabled. Concurrency 1.

Immediately before Task Wave cases, independently discover fresh source examples rather than relying on remembered IDs/counts:
- at least one existing task suitable for lookup/summary/quality;
- a phrase from a live task title/description suitable for text search;
- a live assignee identity;
- a live sprint with tasks;
- a live release/fix-version with tasks if source exposes one;
- attachment-bearing tasks and attachment types if present;
- a task with dependencies if present; otherwise source-prove a real zero-dependency task;
- a task/history case if task history is supported;
- aging/open tasks for an independently computed threshold case.

If a source surface needed by one skill is genuinely unavailable, prove the unavailability and classify that individual skill `SOURCE_CONDITIONAL`; do not fabricate a GREEN result and do not fail the entire wave solely because the authoritative optional source does not exist.

## Phase 3 — Agent A / Oracle B Task #1–20 certification
Exercise natural-language requests for **every one of the 20 canonical Task skills**. For each row record:
- natural-language query;
- loaded/selected canonical skill id;
- called capabilities and arguments;
- status/completion marker;
- source evidence;
- Oracle B comparison;
- terminal classification.

Mandatory factual comparisons:
- #1 lookup: exact source task identity/status/assignee;
- #2 text search: exact task-key set for the discovered phrase;
- #3 any attachments: exact task-key set + attachment metadata parity;
- #4 Excel, #5 PDF, #6 MSG: exact type-constrained key sets; verify the executed handler received the correct fixed type regardless of planner formatting;
- #7 assignee: exact key set vs fresh source identity query;
- #8 status: exact key set for a source-valid status/open-state query;
- #9 sprint: exact complete key set, including >100 if a current source sprint provides such a case;
- #10 release: exact release task key set when release source is available;
- #18 aging: independently calculate keys/ages from fresh source data for the same threshold.

Mandatory analytical/source-input checks:
- #11 summary uses only source task fields/evidence;
- #12 quality deterministic score/rules are reproducible from the same task input;
- #13 missing requirements matches deterministic quality inputs;
- #14 acceptance criteria/testability is reproducible from source description;
- #15 dependency rows match source links;
- #16 history matches source status transitions or is explicitly SOURCE_CONDITIONAL;
- #17 time-in-status uses source timestamps only or is explicitly SOURCE_CONDITIONAL;
- #19 blocker result matches task/blocking/dependency facts;
- #20 similar candidates and scores reproduce the declared deterministic similarity method over fresh source tasks.

For collections, compare **exact key sets, not counts only**.

For successful contracted runs require:
- `semantic_prepass_used=false`;
- REAL AS21 authoritative;
- `completion=runtime_contract` unless the skill is intentionally uncontracted (none of the new Wave-T canonical skills should be);
- zero fabricated source facts.

### Dedicated skill reachability
A correct result through a generic helper alone does not automatically certify the canonical row. The report must show the dedicated canonical SkillSpec is actually loadable/reachable by the planner for a natural request appropriate to that row. If a canonical skill is systematically shadowed by an overlapping helper, classify that row RED and report the exact overlap; do not add a phrase router.

## Phase 4 — Browser C / UIContract
Use the real Browser C through public `/api/v1/query` for a representative set covering every **new result shape**, at minimum:
- task table/text search;
- attachment table (one specialized type if source has it, otherwise proven real-empty);
- task analysis (`missing_requirements` or `dependencies`);
- history/timeline when supported;
- similar-task list;
- one real-empty case;
- one negative/not-found/source-unavailable case.

Verify:
- runtime is Agent Core v4;
- same browser session id reaches backend and response;
- `ui.result_kind` / `preferred_widget` comes from registry UIContract;
- structured rows correspond to the same backend response/evidence;
- no local `/tasks`, MCP/SWTR, fake route, or client-side capability selection renders the result;
- `REAL_EMPTY`, `SOURCE_UNAVAILABLE`/`ERROR`, and success are not conflated.

## Phase 5 — retained A191/A190 regression
After Task Wave testing, rerun a bounded retained sample unrelated to the new single-task skills:
- 3x DMS-380 task→assignee→tasks exact Oracle parity;
- 2x current-sprint task collection;
- 2x active-sprint list;
- 2x person+space+not_completed exact parity;
- B2 open-status classification;
- invented person/sprint negative controls;
- dummy-55/plugin registry gate remains structurally GREEN.

No new regression is allowed. If a new Task skill works but an A191 scenario breaks, A192 is RED.

## Phase 6 — report classifications
Create a 20-row table with exactly one terminal classification per canonical Task skill:
- `GREEN_SOURCE_SUPPORTED`
- `SOURCE_CONDITIONAL`
- `RED`

No `SKIPPED`, `NOT_TESTED`, or silent omission.

Keep the known generic unscoped Cyrillic identity mutation (`Задачи Семавина`) tracked separately unless it appears as the first failing boundary of a tested canonical skill. Do not hardcode a surname fix.

## Allowed output
Create/commit/push **only**:

`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_CATALOG_TASK_WAVE_192.md`

Do not modify production code, frontend, tests, config, plans, or plugin artifacts.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_CATALOG_TASK_WAVE_GREEN`
- `AGENT_CORE_V4_CATALOG_TASK_WAVE_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires:
- architecture/plugin gate GREEN;
- all source-supported canonical Task rows #1–20 GREEN;
- any source-conditional rows explicitly proven and fail-closed;
- Browser C representative shapes GREEN;
- no A188/A190/A191 regression.

If GREEN, recommendation:
**Proceed to owner Wave S (#21–32 Sprint/flow) through the plugin surface.**

## STOP
After committing/pushing only the QA report, stop. Do not implement Wave S and do not change production code.