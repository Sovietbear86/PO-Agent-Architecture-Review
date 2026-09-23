# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_206_HISTORY_STATUS_POST_FIX_REGATE`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT start Wave S.
Do NOT add new skills.
Any RED blocks progression.

## Context
A206 diagnostic returned:
`AGENT_CORE_V4_HISTORY_STATUS_SOURCE_FIXABLE_RED`

It proved three independent owner-side defects:
1. Task API called nonexistent MCP tool `get_unit_change_history`; live MCP exposes `get_task_history({"task_code": ...})`.
2. History parser used wrong fields and would silently corrupt real source data:
   - real field identity = `entity.code`;
   - timestamp = `createdAt`;
   - actor = `user.externalId`;
   - old/new values are structured objects.
3. Person+status queries could drop `not_completed` when planner selected `task.search_assignee`, causing false “open tasks” answers.

Owner fixes now in branch:
- history route/tool/schema + live payload parser corrected;
- authoritative timestamp parsing is fail-closed, never replaced with `now`;
- structured status/user values normalized;
- task history page completeness is checked;
- terminal time-in-status final interval ends at terminal transition instead of extending to current time;
- `task.search_assignee` can now carry optional `status` and filters the result exactly;
- planner contract explicitly forbids dropping an expressible collection constraint;
- task catalog test covers status argument;
- task-api history schema tests updated to the real MCP contract.

Key owner commits after diagnostic:
- `acbc4f620d551c5dc934229060b3747d44b8b4b4`
- `111cadfced3f048b3642fd591dce324dcb0a2675`
- `ba038299772560b9e43cfe911203d465e5a0a96a`
- `da7b17cfe2cac62e3128dcd93c18e294d3e3c72d`
- `a5bb7a0e28b97f3474920ada669808868d6140c9`
- `c9938dc306d3c1a6ee042d732958213f24d0c85b`
- `a5e08a977af8d8e75afc8d77d3432330d05f2c31`

A205 rollback checkpoint remains:
`checkpoint/v4-a205-green@1fd519105ba6612f535ad98a55cb1302f387ca43`.

## Mission
Re-gate only the A206 affected surface plus retained A205 safety controls.

GREEN means:
- live history is actually usable from REAL AS21;
- parsed timelines match raw MCP events;
- time-in-status calculations are exact;
- person+status query no longer drops status;
- ordinary status search remains exact;
- no regression to Harness/plugin architecture.

## Phase 0 — pull / diff
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record exact START_HEAD; tracked worktree clean.
3. Diff A206 diagnostic START `7d505dc2e3204ae66942af83117f80b3fe62447a` to START_HEAD.
4. Confirm changes are bounded to:
   - Task API history route/parser/tests;
   - task time-in-status calculation;
   - task.search_assignee status constraint support;
   - generic planner constraint-preservation wording;
   - docs/spec.
5. No new skill ids, no Agent Core entity hardcode, no local history fallback.

Any architecture drift => RED.

## Phase 1 — focused automated tests
Run at minimum:
```bash
cd task-api
python -m pytest tests/test_swtr_read_facade.py -v

cd ../po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4_task_catalog.py -v
python -m pytest tests/test_agent_core_v4*.py -v
python -m pytest tests/test_harness_task_intelligence.py -v
```

Zero unexplained failures.

## Phase 2 — live MCP + Task API history parity
For:
- DMS-380
- DMS-399
- WMB-30000

Call live MCP `get_task_history` directly and Task API:
`GET /api/v1/swtr-read/tasks/{task}/history`

Require:
- Task API 200;
- exact event count parity;
- exact event ordering parity by source timestamp;
- `field_code` exactly from `entity.code`;
- `changed_at` exactly from `createdAt`, offset-aware;
- actor from `user.externalId` when present;
- status values normalize to meaningful source names, not Python dict strings;
- no `datetime.now()` substitution;
- no local fallback.

If source returns `hasNext=true` but tool exposes no page selector, typed fail-closed is correct.

## Phase 3 — task.history E2E
Run at least 5x each:
- `покажи историю статусов задачи DMS-380`
- `покажи историю статусов задачи DMS-399`
- `покажи историю статусов задачи WMB-30000`

Require:
- actual `task.history` execution;
- COMPLETED when source is healthy;
- exact status-transition timeline vs raw MCP oracle;
- no assignee-change event misclassified as status transition;
- no fabricated transitions;
- source/evidence provenance preserved.

## Phase 4 — task.time_in_status E2E
Use raw MCP timestamps as the Oracle.

### DMS-399 — open
Verify:
- Open -> next transition duration exact;
- current open status extends only to current time;
- offset-aware timestamps;
- no negative intervals.

### DMS-380 — terminal
Verify:
- historical intervals exact;
- final terminal status **does not extend to current time**;
- closure timestamp is authoritative.

### WMB-30000 — status revisit
Verify:
- repeated Escalated visits are not lost;
- intervals are kept separately or explicitly aggregated without changing total duration;
- terminal final interval does not extend to current time.

Run at least 5x per representative query where practical.

Any duration corruption => RED.

## Phase 5 — person + status regression
Fresh Oracle immediately before testing.

Run at least 10 fresh sessions:
`Открытые задачи Родиона Гаранина в DMS`

Require every successful run:
- planner may choose `task.search` or `task.search_assignee`;
- whichever capability executes must carry/cover `status=not_completed`;
- exact active key parity;
- terminal DMS-248, DMS-262, DMS-36 must not appear if still terminal in fresh source;
- no answer may label an unconstrained 11-task collection as “open”.

Also run:
- `Активные задачи Родиона Гаранина в DMS`
- `Все задачи Родиона Гаранина в DMS`

The first must be open-only; the second must remain unfiltered by status.

Any stochastic constraint drop => RED.

## Phase 6 — ordinary status controls
Fresh parity:
- open tasks in DMS;
- completed/closed tasks in DMS;
- current sprint tasks + statuses;
- encoded terminal statuses.

Require retained A205/A206 exact behavior.

## Phase 7 — capability honesty
Query:
- `Ты умеешь показывать историю задачи?`
- `Ты умеешь определять время задачи в статусах?`

If live history is healthy now, agent may state it is available.
If source is intermittently unavailable, it must distinguish capability definition from current source availability.
No unconditional fabrication.

## Phase 8 — retained architecture/source safety
Check:
- local `/api/v1/tasks` factual reads = 0;
- history comes only from live REAL AS21/MCP;
- no fake/frozen/cache timeline;
- dummy-55/plugin gate still GREEN;
- no production skill hardcode in Agent Core.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_HISTORY_STATUS_REGATE_GREEN`
- `AGENT_CORE_V4_HISTORY_STATUS_REGATE_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires:
- history route/source working;
- parser exact;
- time-in-status exact;
- person+status deterministic 10/10;
- status controls GREEN;
- no local fallback;
- plugin invariant GREEN.

If RED:
STOP. Do not start Wave S. Return exact root cause.

If GREEN:
recommend:
`PROCEED_TO_WAVE_S_APPROVAL_WITH_RELEASE_SEARCH_HELPER`

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_HISTORY_STATUS_REGATE_206.md`

Leave UI/backend/Task API/MCP running.
Return verdict, START_HEAD, report commit, source/event parity, person+status 10x result, service health.
Then stop.
