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
Diagnose the existing **health + dialogue-context surface** before any new Wave S skills are introduced.

Primary questions:
1. `sprint.health` routing/completion may stop after sprint discovery/identity instead of executing the actual `sprint.health` capability.
2. Same-session ordinary conversational reference (`этом спринте`) may not preserve enough completed-turn context outside the special clarification-continuation path.
3. `release.health` may be incorrectly routed/completed or may be genuinely blocked by an unavailable REAL AS21 release-task source path. The user observed `здоровье релиза по DMS` returning an AS21-unavailable error.
4. Same-session release follow-ups (`этот релиз`) may have the same completed-turn context problem as sprint follow-ups.

Do not fix any defect. Produce exact trajectory/source evidence and bounded root-cause classification.

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

## Phase 1 — inspect declared sprint + release contracts
Without editing code, document:

### Sprint
- `sprint.health` SkillSpec;
- its declared capabilities;
- its CompletionContract;
- its UIContract;
- whether `sprint.health` is still bound to a legacy capability or a V4 plugin handler;
- `sprints.discover`, `sprint.current`, `task.search_sprint` contracts that could compete for the same natural-language query.

Classify whether current declarations make the manual sprint-health request eligible to complete without an actual `sprint.health` observation.

### Release
- `release.health` SkillSpec;
- its declared capabilities;
- its CompletionContract;
- its UIContract;
- whether `release.health` is still bound to a legacy capability or a V4 plugin handler;
- `release.resolve` and the underlying release-task collection/source path;
- whether REAL AS21 currently exposes enough certified release-task data to compute health;
- whether the existing project+release path intentionally fails closed because live release-task collection is unavailable.

Classify whether `здоровье релиза по DMS` should:
A. resolve a concrete release and execute `release.health`;
B. ask a typed clarification for which release;
C. fail SOURCE_CONDITIONAL because the required REAL AS21 source surface is genuinely unavailable;
D. or is currently failing for the wrong architectural reason.

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

## Phase 5 — release-health live diagnostic
Use fresh sessions, concurrency 1.

Run at least 10x:
`здоровье релиза по DMS`

Because the query does not name a release, capture whether the correct behavior is:
- typed clarification asking which release;
- source-backed discovery/resolve of an unambiguous active/current release if such semantics are actually declared and supported;
- SOURCE_CONDITIONAL/fail-closed because REAL AS21 release-task collection is unavailable.

For every run capture:
- loaded skills;
- `release.resolve` calls and arguments;
- whether a concrete release_id is established;
- whether `release.health` capability executes;
- source route used by `release.health`;
- whether any local `/api/v1/tasks` path is attempted;
- status / completion mode;
- evidence count;
- UI widget;
- exact error/source-unavailable classification.

Hard requirements:
- never fabricate a release id;
- never substitute local-store rows for REAL AS21;
- an AS21-unavailable result is acceptable only if logs prove the required certified release source surface is genuinely unavailable;
- if the only missing input is which release, the agent should prefer typed clarification over a generic source error;
- if a concrete release can be source-resolved but `release.health` still uses an unavailable/legacy source path, classify that as a capability/source integration defect.

Then run explicit controls with at least one REAL release id discovered from source/Oracle:
1. `здоровье релиза <REAL_RELEASE_ID> по DMS`
2. `покажи задачи релиза <REAL_RELEASE_ID> по DMS`

Compare `release.resolve`, `release.health`, and release-task collection behavior.

## Phase 6 — same-session release follow-up
If Turn 1 can establish a concrete release identity (even if health is SOURCE_CONDITIONAL), in the same session send:
`Покажи список задач в этом релизе и их статусы`

Compare against explicit:
`Покажи список задач релиза <REAL_RELEASE_ID> по DMS и их статусы`

Capture:
- whether completed-turn context contains/reuses the prior release_id;
- whether `этом релизе` resolves correctly;
- whether the failure class matches the sprint `этом спринте` problem;
- whether the explicit release-id query behaves differently.

If no concrete release can be established because the source surface is unavailable, state that this phase is source-blocked rather than inventing a result.

## Phase 7 — regression safety
Re-run small retained controls:
- current sprint identity;
- sprint discovery by September+DMS;
- current-sprint multi-filter;
- clarification continuation;
- dummy-55/plugin registry.

Confirm no new architecture drift.

## Required report
Produce:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_SPRINT_RELEASE_HEALTH_DIALOG_CONTEXT_204.md`

Report must contain:
- sprint-health Turn 1 root cause;
- sprint same-session Turn 2 root cause;
- release-health root cause;
- release same-session follow-up result/root cause if testable;
- whether sprint/release findings are one shared defect class or independent defects;
- whether any release failure is a genuine SOURCE_CONDITIONAL limitation versus an implementation/routing defect;
- exact files/functions implicated;
- exact recommended owner fix boundaries;
- explicit statement whether each fix can remain generic Harness/plugin architecture with zero skill hardcode;
- no production changes.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_SPRINT_HEALTH_DIALOG_CONTEXT_GREEN`
- `AGENT_CORE_V4_SPRINT_HEALTH_DIALOG_CONTEXT_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN is allowed only if:
- sprint Turn 1 truly executes the health capability correctly;
- sprint Turn 2 same-session follow-up resolves the prior sprint and returns exact task/status data;
- release-health behavior is semantically correct: typed clarification when release identity is missing, or exact health when source-supported, or proven SOURCE_CONDITIONAL when the certified release source surface is unavailable;
- no local-store factual fallback for release;
- same-session release follow-up resolves prior release when a concrete release was established and the source supports task collection;
- no generic V4 error on supported paths;
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
