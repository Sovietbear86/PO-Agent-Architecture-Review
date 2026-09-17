# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_196_V4_FULL_EXISTING_CATALOG_REGRESSION`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT implement, refactor, fix, improve or rewrite production code, frontend, plugins, tests, prompts, adapters, config or architecture docs. Do not start Wave S implementation. If a defect is found, classify it, report it and stop production changes.

## Why this gate exists
A195D restored universal person resolution and returned `AGENT_CORE_V4_TASK_WAVE_GREEN`. Before adding the next skill batch, the owner requires one **full regression of every skill currently exposed by the V4 plugin catalog**, not merely a retained sample.

This is the new clean checkpoint before Wave S #23–32.

Permanent rollback remains:
`0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`.

## Mission
Prove or reject the complete currently deployed V4 catalog on fresh REAL AS21 and Browser C, with no production edits.

The current plugin catalog contains **27 unique exposed skills** across `builtin.core.a188` and `builtin.catalog.tasks`.

### Core/helper skills (12)
1. `tasks.search`
2. `sprints.discover`
3. `sprints.list`
4. `tasks.lookup_then_assignee`
5. `task.lookup`
6. `task.summary`
7. `task.quality`
8. `task.acceptance`
9. `task.blockers`
10. `sprint.health`
11. `sprint.current`
12. `release.health`

### Task catalog additions (15)
13. `task.search_text`
14. `task.search_attachments`
15. `task.search_excel`
16. `task.search_pdf`
17. `task.search_msg`
18. `task.search_assignee`
19. `task.search_status`
20. `task.search_sprint`
21. `task.search_release`
22. `task.missing_requirements`
23. `task.dependencies`
24. `task.history`
25. `task.time_in_status`
26. `task.aging`
27. `task.similar`

No exposed skill may be silently omitted. If runtime discovery returns a different current set, record the exact set and classify the discrepancy before proceeding.

## Phase 0 — start, inventory and architecture audit
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record exact `START_HEAD`; tracked worktree must be clean.
3. Read:
   - `V4_54_SKILL_MIGRATION_PLAN.md`
   - `V4_DOD_LOCK.md`
   - A188, A190, A191 reports
   - A195D report `AGENT_CORE_V4_UNIVERSAL_IDENTITY_RESOLVER_REGATE_195D.md`
4. Programmatically enumerate the current plugin registry and capture:
   - plugin ids;
   - every skill id;
   - capability ids per skill;
   - completion contract;
   - UIContract if present.
5. Confirm the discovered unique skill set equals the expected 27 above, or explain the exact mismatch.
6. Static invariants:
   - Hermes/plugin architecture intact;
   - no person/surname/entity-specific production routing;
   - team directory is hint only, never searchable population;
   - no local `/api/v1/tasks`, SQLite/snapshot/fake/frozen source truth;
   - `semantic_prepass_used=false` production path remains available;
   - no new planner/completion business-skill branches since A195D owner fixes.

Any architecture violation => RED. Do not fix it.

## Phase 1 — build and automated regression suites
Run the relevant full V4 test surface, not only focused tests. At minimum:

```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4*.py -v
python -m pytest tests/test_v4*.py -v
```

Also run Task API tests relevant to current V4 live reads, identity, task query, sprint reads and attachments.

Record pass/fail/skip totals exactly. Pre-existing failures may be classified only with evidence that they predate START_HEAD and are unrelated; any newly introduced failure is RED.

## Phase 2 — fresh REAL AS21 Oracle pack
Build a fresh independent Oracle B immediately before agent runs. Agent output is never Oracle.

At minimum capture source-backed ground truth for:
- one exact task with rich data and known assignee (prefer DMS-380 if still present);
- one task with attachments (prefer WMB-30000 if still present);
- one known person in DMS (Garanin/Zhdanov or source-equivalent current person);
- one non-team person and one ambiguous person from REAL AS21;
- DMS current sprint;
- September-period DMS sprint(s);
- all active DMS sprints;
- complete task key set for one sprint;
- open-task set for DMS;
- one release with source-visible tasks if available;
- attachment metadata and file types available in the source;
- task history/dependency/timestamp source availability for rows that may be SOURCE_CONDITIONAL.

Record source drift rather than reusing old counts.

## Phase 3 — complete 27-skill API matrix
Use public `POST /api/v1/query`, fresh sessions, concurrency 1.

Every one of the 27 skills must be deliberately exercised by at least one natural-language request and its actual loaded skill must be recorded. Do not infer coverage from unit tests.

For each row record:
- natural-language query;
- expected skill id;
- actual loaded skill id(s);
- status;
- capability trajectory;
- completion mode/contract;
- source route provenance;
- Oracle parity when factual;
- evidence count/keys;
- `semantic_prepass_used`;
- UIContract metadata;
- classification: `GREEN_SOURCE_SUPPORTED`, `SOURCE_CONDITIONAL`, or `RED`.

### Mandatory canonical scenarios
Use these or source-equivalent current cases while still covering all 27 skills:

- exact task lookup;
- grounded task summary;
- task quality;
- acceptance/testability;
- blockers;
- multi-filter `tasks.search` person+sprint/space;
- lookup then assignee tasks;
- period sprint discovery;
- active sprint list;
- current sprint;
- sprint health;
- release health;
- text search with a phrase independently proven in source;
- all attachments for an exact task;
- Excel, PDF and MSG attachment searches (if source lacks a type, prove SOURCE_CONDITIONAL/REAL_EMPTY from live source, never local data);
- assignee search for team and non-team identity;
- status search;
- sprint task search;
- release task search;
- missing requirements;
- dependencies;
- history;
- time in status;
- aging;
- similar/duplicate discovery.

### Source-conditional semantics
A skill may remain `SOURCE_CONDITIONAL` only when:
1. the skill is actually reachable/loaded;
2. its handler follows the correct live route;
3. the authoritative source contract/data is proven unavailable or insufficient;
4. it fails closed or returns a source-proven empty state;
5. it does not fabricate success or silently use local data.

A timeout caused by an avoidable implementation defect is RED, not SOURCE_CONDITIONAL.

## Phase 4 — identity and clarification adversarial regression
Retain A195D behavior as a hard gate:
- inflected full-name team member -> exact factual completion;
- non-team unique canonical identity -> factual completion;
- ambiguous real surname -> `NEEDS_CLARIFICATION` with source candidates;
- choose one clarification candidate -> same-session successful continuation;
- invented person -> meaningful safe clarification/not-found;
- no `AS21 вернул некорректные данные` for ordinary ambiguity/not-found;
- no roster-only population restriction.

Also repeat sprint clarification continuation (`задачи Гаранина в сентябрьском спринте` -> choose DMS or current equivalent) to ensure generic session continuation still works.

## Phase 5 — stability / repeated representative cases
Because earlier POC gates exposed stochastic planner regressions, repeat at minimum:
- DMS-380 lookup -> assignee -> tasks: 5x;
- one full-name assignee query: 5x;
- one person+sprint multi-filter query: 5x;
- current sprint query: 3x;
- one attachment query: 3x.

Require factual parity on every completed run. Any recurrent planner misrouting must be quantified and classified; do not hide it behind a single passing run.

## Phase 6 — Browser C full result-shape regression
Use the real UI. Browser C must cover every **currently used distinct UI result shape/widget**, and all high-risk flows.

At minimum:
- task detail;
- task table/collection;
- attachment table;
- task analysis;
- task dependencies;
- task history/timeline if source-supported;
- similar-task list if source-supported;
- sprint summary;
- sprint list;
- sprint health;
- release health;
- clarification options + click continuation;
- safe zero/not-found/source-unavailable state.

For every browser case capture backend status, UI state/widget, evidence rendering and whether the UI preserves the factual count/key set from backend.

Also confirm no pre-query/runtime confusion causes the UI to silently execute Legacy Harness for the tested query. If the readiness-label issue remains cosmetic only, document it; if a query actually executes legacy path, RED.

## Phase 7 — plugin/extensibility regression
Re-run the A190 plugin gate/dummy-55 acceptance.

Require:
`plugin added -> discovery -> compact catalog -> load/select -> capability executes -> completion contract terminates -> UIContract propagated`

No Agent Core/planner/runtime business edit may be required.

## Phase 8 — final full-regression verdict
Create an explicit table with all 27 discovered skills and final classification.

Use exactly one overall verdict:
- `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_GREEN`
- `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires:
- all 27 exposed skills explicitly tested;
- zero `RED` rows;
- every factual GREEN exact against fresh Oracle B;
- every SOURCE_CONDITIONAL row proven live/fail-closed;
- identity + clarification + Browser C GREEN;
- repeated stability gate acceptable with no reproducible planner regression;
- A190 dummy-55/plugin extensibility GREEN;
- zero local-store source-of-truth reads;
- A188/A190/A191/A195D invariants preserved.

If any row is RED, stop and report the exact first bounded defect(s). Do **not** start Wave S.

If GREEN, recommendation must be exactly:
**Freeze A196 as the pre-Wave-S regression checkpoint and proceed to owner implementation of Wave S #23–32 through the existing plugin surface; #21 sprint.health and #22 sprint.current remain retained existing skills.**

## Allowed output
Commit/push **only**:

`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_FULL_EXISTING_CATALOG_REGRESSION_196.md`

No production/test/frontend/plugin/config/doc changes.

## Service keepalive
After committing/pushing only the QA report, leave the tested current-HEAD UI/backend/Task API/MCP stack running. Return URLs, ports, PIDs, health and exact START_HEAD. Then stop and wait for the owner.
