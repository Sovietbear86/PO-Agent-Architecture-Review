# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_195B_V4_ASSIGNEE_MORPHOLOGY_UI_REGATE`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT implement, refactor, fix, improve, or rewrite production code, frontend code, plugin code, tests, prompts, adapters, config, or architecture docs. Do not start Wave S until this focused live UI regression is classified.

## Why this gate was reopened
A195 returned `AGENT_CORE_V4_CATALOG_TASK_WAVE_GREEN`, but immediately afterward manual Browser-C testing on the same live product exposed a user-visible failure:

`Задачи Александра Жданова в DMS`

Browser C returned:
- `Agent Core v4 не смог безопасно завершить траекторию.`
- status `FAILED`
- evidence `0`

A195 itself mentioned a known pre-existing morphology limitation: the V4 grounding guard may reject nominative identity forms when the literal user query contains an inflected/genitive form. Because this now reproduces on a normal production-like user query, it is no longer acceptable to leave it only as a non-blocking note. We must prove exactly where the trajectory fails before Wave S proceeds.

## Start state
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record `git rev-parse HEAD` as `START_HEAD` and verify tracked worktree is clean.
3. Read:
   - `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_TASK_ASSIGNEE_FINAL_REGATE_195.md`
   - `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_CATALOG_TASK_WAVE_REGATE_194.md`
   - `V4_DOD_LOCK.md`
   - `V4_54_SKILL_MIGRATION_PLAN.md`
4. Permanent rollback remains `0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`.

## Mission
Reproduce and localize the **Russian morphology / grounding** regression for natural assignee search without modifying code.

A195B must answer:
1. Does the exact Browser-C query `Задачи Александра Жданова в DMS` still fail on current HEAD?
2. Is identity resolution itself correct (team hint + live AS21 confirmation), with failure occurring later in query-grounding / literal validation?
3. Which exact guard rejects the canonical/nominative identity and why?
4. Does the failure affect only one grammatical case, or a broader family of Russian case forms?
5. Can the same source-backed person succeed when queried as `Александр Жданов`, `Александра Жданова`, surname-only, and canonical login?
6. Is this a generic morphology defect rather than a person-specific issue?
7. Does Browser C surface a generic FAILED because an internal typed grounding failure is not propagated as clarification/error detail?

## Phase 0 — keep architecture assumptions locked
No production changes. Confirm current HEAD still preserves:
- Hermes/plugin architecture;
- no person-specific hardcode;
- REAL AS21 live authority;
- no local `/api/v1/tasks` fallback;
- no new edits to Agent Core/planner/runtime since A195 owner fix.

## Phase 1 — fresh REAL AS21 identity oracle
Before agent testing, independently resolve the target identity against REAL AS21 and record the canonical login/id.

Use source-backed paths only. Confirm whether the configured team directory maps the natural Russian full name to the same canonical identity and whether live AS21 confirms it.

The agent result is NOT Oracle B.

## Phase 2 — morphology matrix through public `/api/v1/query`
Use fresh sessions, concurrency 1, same space `DMS` where applicable.

Test at minimum:
1. `Задачи Александр Жданов в DMS`
2. `Задачи Александра Жданова в DMS`
3. `Покажи задачи Александру Жданову в DMS`
4. `Что делает Александр Жданов в DMS`
5. `Задачи Жданова в DMS`
6. canonical-login control for the same person

For each capture:
- response status;
- loaded skill;
- capability calls and arguments;
- identity result;
- exact planner/runtime failure point;
- warnings/exception type;
- whether the canonical identity was already source-confirmed before the failure;
- exact key-set parity where execution succeeds.

Do not accept a canonical-login-only success as proof that natural Russian morphology works.

## Phase 3 — grounding-guard forensic trace
Inspect, without editing, the production path that validates capability arguments against user-grounded text/observations.

Determine exactly whether the failure is caused by:
- `_literal_is_query_derived` or equivalent literal substring grounding;
- `_reference_is_query_derived_person` / morphology helper;
- trusted-observation reuse guard;
- planner emitting a normalized/nominative form not literally present in the inflected query;
- another bounded guard.

Provide exact file/function and the rejected value vs original query text.

The desired architecture is generic: a source-confirmed identity from a trusted resolver observation may be reused downstream even when its canonical/nominative spelling is not a literal substring of the inflected Russian user query. Do NOT implement this in QA; just prove whether this is the missing rule.

## Phase 4 — Browser C exact reproduction
Use the actual running UI and execute exactly:

`Задачи Александра Жданова в DMS`

Capture:
- frontend request payload;
- backend response payload;
- trace/runtime details;
- whether the UI hides a more specific typed failure behind generic `V4 ERROR`.

Repeat one successful control in the same UI session family to prove the service stack itself is healthy.

## Phase 5 — regression controls
Run a very small retained sample only:
- one A195-green natural-name query that previously passed;
- `DMS-380` lookup -> assignee -> tasks once;
- `Покажи открытые задачи в DMS` once;
- clarification flow once.

This gate is not a full Task Wave rerun.

## Classification
Use exactly one morphology finding:
- `GREEN_MORPHOLOGY_SUPPORTED`
- `RED_MORPHOLOGY_GROUNDING_GUARD`
- `RED_IDENTITY_RESOLUTION`
- `RED_PLANNER_NORMALIZATION`
- `RED_OTHER` (explain precisely)

## Allowed output
Create/commit/push **only**:

`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_ASSIGNEE_MORPHOLOGY_UI_REGATE_195B.md`

Do not modify production/frontend/tests/config/plugins/plans.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_TASK_WAVE_GREEN`
- `AGENT_CORE_V4_TASK_WAVE_REOPENED_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

If the exact natural UI query fails due to a generic morphology/grounding defect, verdict MUST be `AGENT_CORE_V4_TASK_WAVE_REOPENED_RED`; do not keep GREEN merely because A195 canonical cases passed.

## Service keepalive
After committing/pushing only the QA report, leave the current-HEAD UI/backend/Task API stack running and return frontend/backend/Task API URLs, ports, PIDs, health and START_HEAD. Then stop and wait for the owner.
