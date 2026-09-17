# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_195_V4_TASK_ASSIGNEE_FINAL_REGATE`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT implement, refactor, fix, improve, or rewrite production code, frontend code, plugin code, tests, prompts, adapters, config, or architecture docs. Do not start Wave S before this focused gate is GREEN.

## Start state
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record `git rev-parse HEAD` as `START_HEAD` and verify tracked worktree is clean.
3. Read:
   - `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_CATALOG_TASK_WAVE_REGATE_194.md`
   - `V4_DOD_LOCK.md`
   - `V4_54_SKILL_MIGRATION_PLAN.md`
4. Permanent rollback remains `0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`.

## Context
A194 left exactly one bounded RED in the Task Wave: canonical row #7 `task.search_assignee`.

The live AS21 `search_users` surface does not reliably translate a Russian full name (for example `Андрей Жданов`) to the canonical Latin login. The owner has now implemented a generic two-stage solution **outside Agent Core**:

1. the task plugin may use the configured authorized team directory only as a deterministic identity **hint** when a natural reference resolves to exactly one configured team member;
2. the hinted canonical login is still sent through the live AS21 assignee route and must be confirmed by REAL AS21 before any task result is accepted;
3. ambiguous/unknown references are not guessed and remain source-resolved/fail-closed;
4. pure assignee queries reuse the previously proven `/api/v1/swtr-read/assignee-tasks` live route rather than performing a separate five-space corpus scan.

Owner production changes for this gate are limited to plugin/source-boundary files and focused tests. Agent Core/planner/runtime trajectory/completion engine must remain unchanged.

## Mission
Prove or reject the final fix for row #7 without reopening already-green areas unnecessarily.

A195 must answer:
1. Can natural Russian full names resolve to the correct canonical AS21 identity without hardcoded people/surnames?
2. Does the team directory remain only a hint, with REAL AS21 still authoritative?
3. Do ambiguous/unknown people fail closed rather than guess?
4. Does the pure assignee path avoid local storage and avoid the A194 `max_pages` failure caused by the generic multi-space scan?
5. Did the fix preserve A188/A190/A191 and the A194-green Task Wave behavior?
6. Is Hermes/plugin extensibility still intact: no new skill-specific logic in Agent Core/planner/runtime?

## Phase 0 — architecture/static audit
Compare current HEAD with A194 START_HEAD `4425e27c5de556301758562ed5cfd4a8b8416134`.

Require:
- no edits to `agent_core_v4.py`, `agent_core_v4_reliable.py`, `agent_core_v4_robust.py`, planner strategy/model, or completion engine for this fix;
- natural-name bridge implemented at plugin/source boundary, not as person-specific routing;
- no literal production reference to `Жданов`, `Андрей`, or any other individual identity;
- configured team directory is not accepted as factual task truth: the downstream live AS21 route must confirm the canonical identity;
- no `/api/v1/tasks`, SQLite, local task store, snapshot or fake fallback in factual path;
- assignee ambiguity/not-found remains fail-closed;
- generic plugin handler seam remains reusable by future skills.

Any violation => RED. Do not fix it.

## Phase 1 — focused build/tests
Run at minimum:

```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_v4_owner_fix_contracts.py -v
python -m pytest tests/test_agent_core_v4_plugin_registry.py -v
python -m pytest tests/test_agent_core_v4_task_catalog.py -v
python -m pytest tests/test_agent_core_v4_completion_contract.py -v
```

Task API focused import/tests for `swtr_query` + `swtr_assignee` must also pass. Do not modify tests/code.

## Phase 2 — fresh REAL AS21 Oracle B
Start/reuse a fresh current-HEAD live stack, concurrency 1.

For each tested person, derive Oracle B independently from REAL AS21. Do not use Agent output as Oracle.

Required cases:

### A. Natural full name — primary A194 defect
Execute through public `/api/v1/query`:

`Задачи Андрея Жданова`

Requirements:
- dedicated `task.search_assignee` skill loaded;
- natural reference remains user-grounded;
- plugin may produce a canonical source hint, but route provenance must show live AS21 confirmation;
- exact task-key parity with independent live assignee Oracle;
- no `max_pages` failure from generic five-space scan;
- `semantic_prepass_used=false`;
- successful contracted completion.

If source/team data changed and this exact identity is no longer available, document it and use another configured Russian full-name case while still attempting this case first.

### B. Unseen second natural full name
Choose a second configured team member not used by the owner tests. Use a natural Russian full name, not canonical login. Exact Oracle parity required.

### C. Canonical login control
Query a canonical login directly. It must produce the same source-backed identity/task collection as Oracle B and must not require the team hint.

### D. Ambiguous/unknown controls
At minimum:
- one ambiguous surname/reference;
- one invented person.

Neither may silently choose a person. Accept typed clarification/fail-closed only.

## Phase 3 — route provenance / pagination
For the successful assignee cases prove:

`task.search_assignee plugin -> production adapter -> /api/v1/swtr-read/task-query -> delegated /assignee-tasks -> MCP-SWTR -> REAL AS21`

or an equivalent certified live path.

Confirm:
- no `/api/v1/tasks` read;
- no five-space full-corpus scan for a pure assignee query;
- collection is complete/exact for Oracle B;
- if source pagination itself cannot prove completeness, fail closed rather than return partial data as complete.

## Phase 4 — retained bounded regression
Do not repeat all of A194. Run only enough to prove the focused fix did not regress adjacent behavior:
- `DMS-380` lookup -> assignee -> tasks, exact Oracle parity, 2x;
- `Покажи открытые задачи в DMS`, exact parity;
- `Проверь на наличие вложений задачу WMB-30000`, exact live attachment parity;
- clarification continuation `задачи Гаранина в сентябрьском спринте` -> choose `DMS` once;
- plugin/dummy-55 structural gate;
- Browser C still uses V4 and `/api/v1/query`.

## Phase 5 — Task Wave final decision
Use A194 classifications for rows unaffected by this owner fix, but recheck row #7 live and confirm no adjacent regression.

If row #7 is GREEN and all retained checks are GREEN, Task Wave #1-20 is closed for current source capabilities even though explicitly proven `SOURCE_CONDITIONAL` rows remain tracked as such.

## Allowed output
Create/commit/push **only**:

`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_TASK_ASSIGNEE_FINAL_REGATE_195.md`

No production/test/config/frontend/plugin/doc changes.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_CATALOG_TASK_WAVE_GREEN`
- `AGENT_CORE_V4_CATALOG_TASK_WAVE_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires:
- row #7 natural-name assignee search exact against REAL AS21;
- no hardcoded identity routing;
- live-source-only invariant GREEN;
- ambiguity/unknown fail closed;
- no A188/A190/A191/A194-green regression.

If GREEN, recommendation must be:
**Close Wave T (#1-20) and proceed immediately to owner Wave S (#21-32 Sprint/flow) through the existing plugin surface.**

## Service keepalive
After committing/pushing only the QA report, leave the current-HEAD UI/backend/Task API stack running and return frontend/backend/Task API URLs, ports, PIDs, health and START_HEAD. Then stop and wait for the owner.
