# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_195B_V4_ASSIGNEE_MORPHOLOGY_UI_REGATE`

## Role lock
GigaCode is QA/adversarial tester + service operator only. Do not modify production/frontend/tests/plugins/config/docs. Do not start Wave S.

## Context
A195 was GREEN, but real Browser C still fails on natural full-name requests while surname-only requests succeed. Reproduce and localize this before Wave S.

Known user cases:
- `Задачи Александра Жданова в DMS` -> FAILED in UI;
- same class reported for Родион Гаранин;
- `Задачи Жданова ...` and `Задачи Гаранина ...` work.

A195 already documented a pre-existing morphology/grounding limitation: planner normalization to nominative may be rejected by the anti-invention grounding guard when the normalized multi-token name is not a literal substring of the inflected query.

## Start
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record START_HEAD; tracked worktree must be clean.
3. Read A195, A194, `V4_DOD_LOCK.md`, `V4_54_SKILL_MIGRATION_PLAN.md`.
4. Permanent rollback: `0f03fca14fe078c86dca961362915e10cc985401`.

## Phase 1 — REAL AS21 oracle
Independently establish canonical identities and task key sets for both target people using live AS21 only. Agent output is not Oracle B.

## Phase 2 — API morphology matrix
Fresh sessions, concurrency 1. Run through public `/api/v1/query`:
- `Задачи Александра Жданова в DMS`
- `Задачи Жданова в DMS`
- `Покажи задачи Александру Жданову в DMS`
- `Что делает Александр Жданов в DMS`
- canonical-login control for same person
- `Задачи Родиона Гаранина в DMS`
- `Задачи Гаранина в DMS`
- `Покажи задачи Родиону Гаранину в DMS`
- `Что делает Родион Гаранин в DMS`
- canonical-login control for same person

For each record status, loaded skill, capability args, identity result, rejected value, failure point, warnings/exception, source confirmation, and exact key parity when successful.

## Phase 3 — grounding forensic
Inspect without editing `_literal_is_query_derived` and related person-grounding checks. For each failure record:
- original query;
- planner-emitted person value;
- whether it was normalized to nominative/canonical form;
- exact guard/branch that rejected it;
- whether trusted source identity was already confirmed.

Determine whether this is generic morphology grounding, identity resolution, planner normalization, or another issue. Also determine from existing reports/commits whether the defect predates A195.

## Phase 4 — Browser C
In the actual UI run:
- `Задачи Александра Жданова в DMS`
- `Задачи Родиона Гаранина в DMS`
- surname-only control for each.

Capture frontend request, backend response, trace, and whether UI hides a specific backend cause behind generic `V4 ERROR`.

## Phase 5 — tiny regression
Run once each: DMS-380 lookup->assignee->tasks, open tasks DMS, clarification continuation. No full Task Wave rerun.

## Classification
Exactly one:
- `GREEN_MORPHOLOGY_SUPPORTED`
- `RED_MORPHOLOGY_GROUNDING_GUARD`
- `RED_IDENTITY_RESOLUTION`
- `RED_PLANNER_NORMALIZATION`
- `RED_OTHER`

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_ASSIGNEE_MORPHOLOGY_UI_REGATE_195B.md`

## Verdict
Exactly one:
- `AGENT_CORE_V4_TASK_WAVE_GREEN`
- `AGENT_CORE_V4_TASK_WAVE_REOPENED_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

If either full-name Browser-C case fails due to generic morphology/grounding, verdict must be `AGENT_CORE_V4_TASK_WAVE_REOPENED_RED`.

Leave current-HEAD UI/backend/Task API running after QA and return URLs, ports, PIDs, health and START_HEAD.