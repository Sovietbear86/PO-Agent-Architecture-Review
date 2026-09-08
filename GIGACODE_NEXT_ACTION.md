# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_165_H1B_PLANNER_DECISION_REPAIR`

## Mission
Retest H1B after Assignment 164 proved that the remaining blocker is not loop mechanics or observation propagation, but planner decision reliability: Qwen 3.8 often returns an empty/non-executable planner object, and the semantic pre-pass sometimes blocks compound requests before the loop starts.

Owner fixes are now present. This is QA ONLY. Do not modify production/backend/frontend/test source code, prompts, `.env`, registry contracts or committed Playwright tests.

## Required owner commits
All MUST be ancestors before testing:
- `97081ac2cb8d1d38d6d61f2dd78d4eb82ddddee1` — planner no longer accepts the first parseable-but-non-executable object; invalid decisions trigger bounded explicit LLM repair turns. Empty action + selected capability is normalized to `call_capability`; empty action without a decision remains fail-closed.
- `ffe218c679c56380624fec11c6c81b0558a50116` — semantic pre-pass is advisory for H1B and may no longer suppress a compound loop with an incidental clarification; raw human display names cannot be sent to AS21 as assignee identifiers.
- `f2bced2cde44b8f8320ec0a94546e0370766c871` — planner decision-shape safety tests.

Accepted evidence from 162–164:
- real H1B plan/execute/observe mechanics already executed two source-backed capabilities;
- `$obs` propagation from DMS-380 assignee to task-search has been proven;
- REAL AS21 remains authoritative;
- 164 RED root cause was planner empty/non-executable action plus pre-pass clarification flakiness;
- H0 baseline was 5/5 before the H1B planner regression.

## Absolute rules
- Oracle B = fresh direct REAL AS21/MCP-SWTR only. No local DB/sync/fake/frozen/surrogate truth.
- Target model remains Qwen 3.8.
- Concurrency=1.
- Source-backed timeout=300s.
- A proven source error receives exactly 2 retries with 30s backoff before being called transient.
- Exact task-key-set equality is mandatory for collections.
- No caveat GREEN.
- Commit/push only the final QA report.

## Phase 0 — preflight
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
2. Record HEAD and git status.
3. Verify all 3 owner commits above are ancestors.
4. Restart/reuse REAL MCP-SWTR + Task API + PO Agent v3 with Qwen 3.8 and frontend used by Playwright.
5. `/health` must prove v3=true, semantic LLM healthy, source healthy; frontend must answer before Browser phases.

STOP as `BLOCKED_BY_PROVEN_ENVIRONMENT` if this is not true.

## Phase 1 — unit/static safety gate
Run:
`pytest -q tests/test_agent_core_v3_foundation.py tests/test_agent_core_v3_registry.py tests/test_agent_core_v3_loop.py tests/test_agent_core_v3_h1b_grounding.py`

Require all PASS.

Static proof:
- parseable but non-executable planner JSON does NOT end the retry loop;
- subsequent attempts are explicit repair turns, not identical retries of the same prompt;
- empty action + valid capability_id becomes `call_capability` without inventing capability/constraints;
- empty action with no capability and no final answer remains non-executable/fail-closed;
- semantic pre-pass clarification is advisory in H1B and cannot itself stop a compound request;
- a human display name cannot reach the task-search executor unless converted to a source-grounded login or provided explicitly as a login-like identifier;
- max_steps=4, duplicate blocking and `$obs` safety remain intact.

## Phase 2 — planner repair focused probe
Before full A/B, exercise the production planner through `/api/v1/query` in fresh sessions at least 5 times using:
`Покажи DMS-380`

Record for each run:
- status;
- number of planner LLM attempts used for the first decision;
- whether first raw candidate had empty action;
- whether a repair turn was required;
- selected capability;
- final planner decision after observation.

Acceptance: 5/5 must complete correctly. A run may use bounded repair, but MUST NOT fail merely because the first candidate had empty action. No run may exceed the configured bounded attempts/loop budget.

If 5/5 does not pass, STOP with `H1B_PLANNER_DECISION_REPAIR_RED`; do not waste time on later phases.

## Phase 3 — REAL multi-step Challenge A
Fresh Oracle B, then Agent A:
`Проверь DMS-380 и затем покажи задачи его исполнителя`

Oracle B independently:
1. point-read DMS-380;
2. capture current authoritative assignee login;
3. live search all tasks for that exact assignee;
4. persist exact normalized key set.

Agent A requires:
- COMPLETED;
- `architecture_stage=H1B_AGENT_LOOP`;
- lookup DMS-380 -> authoritative observation -> later task-search;
- second-step assignee equals the source-backed observation login;
- >=2 and <=4 capability executions;
- every postcondition PASS;
- exact final task-key-set parity with Oracle B;
- planner repair metadata, if used, is visible in evidence/logs and bounded.

## Phase 4 — REAL multi-step Challenge B / grounding
Fresh Oracle B, then Agent A:
`Найди задачи Гаранина в DMS и затем покажи подробности DMS-380`

Require:
- compound request reaches H1B loop even if semantic pre-pass emits a clarification advisory;
- source-grounded canonical login is used for Garanin; raw `Гаранин/Гаранина` MUST NOT be sent to AS21;
- one `task-search-v3` with DMS + canonical assignee and one `task-lookup-v3` for DMS-380;
- both requested outcomes preserved;
- exact search key parity and exact point-read parity;
- COMPLETED.

Any HTTP 409 caused by raw human name is RED.

## Phase 5 — safety / no silent truncation
Fresh sessions prove:
1. `Проверь DMS-380 и затем покажи историю его статусов` must NOT silently return only lookup as success. Unsupported second operation must fail closed/clarify explicitly.
2. Empty action with no capability/final answer after all bounded repair attempts fails closed.
3. Invented `$ground.member_login` fails closed.
4. Invented `$obs` path fails closed.
5. Duplicate same capability+constraints blocked.
6. No run exceeds 4 capability executions.

## Phase 6 — protected single-step exact parity
Fresh Oracle B then Agent A:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`

Require COMPLETED + exact parity. Human-name cases must use canonical source-backed logins.

## Phase 7 — Browser C regression
Run:
`npm run e2e:h0`

Require 5/5 PASS. Start frontend if needed; do not skip.

## Phase 8 — Browser C multi-step
Use real Playwright Chromium in a fresh conversation for Challenge A. Persist screenshot, browser session id, correlated backend trace, H1B loop metadata, rendered result and exact Oracle parity from the same time window.

## Phase 9 — final report
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_PLANNER_DECISION_REPAIR_165.md`

Allowed verdicts ONLY:
- `AGENT_CORE_V3_H1B_LOOP_GREEN`
- `H1B_PLANNER_DECISION_REPAIR_RED`
- `H1B_GROUNDING_RED`
- `H1B_OBSERVATION_PROPAGATION_RED`
- `H1B_AGENT_ORACLE_PARITY_RED`
- `H1B_SILENT_TRUNCATION_RED`
- `H1B_SINGLE_STEP_REGRESSION_RED`
- `H1B_BROWSER_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires all phases including Browser C. Commit/push only this QA report and STOP.

## Start now
Execute Assignment 165 completely. First pull, print HEAD + this Status line, then preflight. Do not modify code.