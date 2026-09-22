# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_204_V4_SPRINT_HEALTH_AND_DIALOG_CONTEXT_DIAGNOSTIC`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT start Wave S.
Do NOT add new skills.

## Context
A203 is RED only because of one stale owner test tuple-unpack bug. Owner fixed that separately in commit:
`0c57346666ca4a5d42509bdae34704759343727a`.

However, manual Browser testing exposed a potentially real product defect in an already-existing skill/session path:

Turn 1:
`здоровье сентябрьского спринта по DMS`

Observed UI result:
- sprint identity DMS-SPRNT-3 returned;
- answer says detailed sprint-health metrics are unavailable and suggests asking for task list/statuses;
- UI surface appears as `sprint_summary`, not an actual health result.

Turn 2 in the same Browser session:
`Покажи список задач в этом спринте и их статусы`

Observed:
- generic V4 trajectory failure.

This must be resolved before any new Wave S skills are introduced.

## Mission
Diagnose exactly whether there are one or two defects:
1. `sprint.health` routing/completion may stop after sprint discovery/identity instead of executing the actual `sprint.health` capability.
2. Same-session ordinary conversational reference (`этом спринте`) may not preserve enough completed-turn context outside the special clarification-continuation path.

Do not fix either defect. Produce exact trajectory/source evidence and bounded root-cause classification.

## Phase 0 — start / test cleanup
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record START_HEAD; tracked worktree clean.
3. Run:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_v4_owner_fix_contracts.py -v
```
Require 11/11 after owner commit `0c573466...`.
If not, report RED test-compat finding separately.

## Phase 1 — inspect declared sprint contracts
Without editing code, document:
- `sprint.health` SkillSpec;
- its declared capabilities;
- its CompletionContract;
- its UIContract;
- whether `sprint.health` is still bound to a legacy capability or a V4 plugin handler;
- `sprints.discover`, `sprint.current`, `task.search_sprint` contracts that could compete for the same natural-language query.

Classify whether current declarations make the manual Turn 1 eligible to complete without an actual `sprint.health` observation.

## Phase 2 — Turn 1 live reproduction
Fresh sessions, concurrency 1, run at least 10x:
`здоровье сентябрьского спринта по DMS`

For every run capture:
- loaded skills in order;
- capability trajectory;
- whether `space.resolve` executes;
- whether `sprint.search` executes;
- resolved sprint_id;
- whether **`sprint.health` capability actually executes**;
- completion mode;
- final UI contract/widget;
- source provenance;
- final answer.

Build a fresh REAL AS21 Oracle for DMS-SPRNT-3 tasks/statuses if possible.

Classification:
- If request completes without a `sprint.health` observation, RED.
- If `sprint.health` executes but returns identity-only data, RED and localize its handler/source path.
- If source truly lacks required fields and capability fails closed/source-conditional, record that separately; do not treat identity-only answer as health.
- `sprint_summary` for a health request is acceptable only if UIContract explicitly maps health to that widget; otherwise flag UI mismatch.

## Phase 3 — same-session follow-up
In the **same session**, after a successful Turn 1, send:
`Покажи список задач в этом спринте и их статусы`

Run at least 10 session pairs.

Capture:
- exact request payload for turn 2;
- session_id;
- whether any prior completed-turn state is supplied to Harness;
- loaded skills/observations on turn 2;
- whether `этом спринте` resolves to the prior sprint_id;
- whether `task.search_sprint` / `task.search` executes;
- completion/error;
- Browser C rendering.

Classify:
A. Product supports only clarification continuation, not general completed-turn dialogue context.
B. General session context exists but is lost/miswired.
C. Planner has enough context but routes incorrectly.
D. Source/capability error.

Do not guess; prove from payload/runtime trajectory.

## Phase 4 — explicit-control comparisons
Compare the failing follow-up with:
1. `Покажи список задач в DMS-SPRNT-3 и их статусы`
2. `Покажи список задач сентябрьского спринта DMS и их статусы`
3. new-session version of the same explicit queries.

If explicit queries succeed while `этом спринте` fails, that strongly isolates the issue to conversational/session reference resolution rather than task/sprint source capability.

## Phase 5 — regression safety
Re-run small retained controls:
- current sprint identity;
- sprint discovery by September+DMS;
- current-sprint multi-filter;
- clarification continuation;
- dummy-55/plugin registry.

Confirm no new architecture drift.

## Required report
Produce:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_SPRINT_HEALTH_DIALOG_CONTEXT_204.md`

Report must contain:
- Turn 1 root cause;
- Turn 2 root cause;
- whether they are one defect or two;
- exact files/functions implicated;
- exact recommended owner fix boundaries;
- explicit statement whether fix can remain generic Harness/plugin architecture with zero skill hardcode;
- no production changes.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_SPRINT_HEALTH_DIALOG_CONTEXT_GREEN`
- `AGENT_CORE_V4_SPRINT_HEALTH_DIALOG_CONTEXT_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN is allowed only if:
- Turn 1 truly executes the health capability correctly;
- Turn 2 same-session follow-up resolves the prior sprint and returns exact task/status data;
- no generic V4 error;
- existing plugin/Harness invariants remain.

Any failure => RED and Wave S remains blocked.

## Service keepalive
Leave UI/backend/Task API/MCP running. Return:
- verdict;
- START_HEAD;
- report commit;
- URLs/PIDs/health;
- key trajectory evidence for both turns.
Then stop.
