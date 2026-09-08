# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_166_H1B_TYPED_DECISION_PROTOCOL`

## Mission
Certify the H1B architectural change that removes the fragile free-form `action` enum as the control-flow decision. Assignment 165 proved the action-based JSON planner remained unreliable on Qwen 3.8 (2/5) even after bounded repair. The new protocol encodes the decision structurally as exactly one of two typed branches: CALL or FINAL.

This is QA ONLY. Do not modify production/backend/frontend/test source code, prompts, `.env`, registry contracts or committed Playwright tests.

## Required owner commits
Both MUST be ancestors before testing:
- `d3f0c6341864688c20224ca5433e9aa424019483` — H1B planner protocol replaced with typed `{call, final, rationale}` decision; execution no longer depends on an `action` field.
- `33f271b6eae8b04bbc913f1baae31946e2adbd4d` — typed CALL/FINAL safety/parser tests.

Important architecture note: production runtime still instantiates the same `AgentLoopPlannerV3` class. The class implementation itself is now typed-protocol. Do NOT expect or require a renamed planner class.

Accepted evidence from 162–165:
- H1B loop mechanics are real and previously executed two source-backed capabilities;
- `$obs` observation propagation works;
- REAL AS21 is authoritative;
- semantic grounding is advisory and raw human display names may not be sent as assignee identifiers;
- 165 demonstrated the OLD action-based planner was unreliable: 2/5 on `Покажи DMS-380`, with failed runs returning empty action/capability objects across all repair turns.

## Absolute rules
- Oracle B = fresh direct REAL AS21/MCP-SWTR only. No local DB/sync/fake/frozen/surrogate truth.
- Target model = current Qwen 3.8 runtime. Do not change model/config.
- Concurrency=1.
- Source-backed timeout=300s. A proven source failure gets exactly 2 retries with 30s backoff.
- Exact task-key-set equality mandatory for collections.
- No caveat GREEN.
- Commit/push only the final QA report.

## Phase 0 — pull and preflight
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
2. Print HEAD, git status and this Status line.
3. Verify both owner commits above are ancestors.
4. Start/restart REAL MCP-SWTR + Task API + PO Agent v3 + frontend so NEW code is loaded.
5. `/health` must prove v3=true, semantic LLM healthy and source healthy. Frontend must respond before Browser phases.
6. Static runtime proof: when v3=true, runtime uses `AgentLoopPlannerV3`, and the loaded class source contains typed `call/final` protocol and does NOT require `action` from model output.

If environment is not healthy, STOP as `BLOCKED_BY_PROVEN_ENVIRONMENT`; do not run expensive probes.

## Phase 1 — unit/static typed-protocol gate
Run:
`pytest -q tests/test_agent_core_v3_foundation.py tests/test_agent_core_v3_registry.py tests/test_agent_core_v3_loop.py tests/test_agent_core_v3_h1b_grounding.py`

Require all PASS.

Prove statically:
- planner control decision does NOT depend on a model-produced `action` field;
- CALL shape = non-null `call` object + `final=null`;
- FINAL shape = `call=null` + non-null `final.answer`;
- both-null and both-selected shapes are non-executable and repaired/fail-closed;
- legacy action-only object is non-executable;
- capability ID still must exist in H1A registry;
- unsupported constraints still fail closed;
- `$ground`/`$obs`, duplicate blocking, postconditions and max_steps=4 remain intact;
- there is NO deterministic regex/keyword fallback that maps `DMS-380` or person names directly to capabilities.

## Phase 2 — mandatory 10-run decision reliability gate
Do NOT proceed to multi-step until all ten runs pass. Use fresh sessions, concurrency=1.

### 2A — five point-read runs
Run exactly 5 fresh production `/api/v1/query` requests:
`Покажи DMS-380`

Each must:
- COMPLETED;
- use H1B typed planner;
- select CALL structurally with `task-lookup-v3`;
- return exact DMS-380 source identity;
- finalize after observation through FINAL typed branch;
- have no dependency on legacy `action`.

Record per run: status, latency, planner attempts, selected branches, capability, loop steps.

### 2B — five grounded human-name runs
Fresh Oracle B first for current `Garanin.R.V` DMS exact task-key set. Then run exactly 5 fresh production requests:
`Задачи Гаранина в DMS`

Each must:
- COMPLETED;
- resolve to authoritative canonical login before AS21 task-search;
- select CALL structurally with `task-search-v3`;
- exact task-key set == same-window fresh Oracle B (refresh Oracle if source data changed during the probe);
- never send raw `Гаранин/Гаранина` as AS21 assignee identifier.

Acceptance for Phase 2: **10/10 PASS**. No averaging and no caveat.
If ANY of the ten fails due to planner decision shape/reliability, STOP immediately with `H1B_TYPED_DECISION_RELIABILITY_RED`. Do not run later phases.
If a source error occurs, apply only the defined source retry policy and distinguish it from planner failure with raw evidence.

## Phase 3 — REAL multi-step Challenge A
Fresh Oracle B then Agent A:
`Проверь DMS-380 и затем покажи задачи его исполнителя`

Require:
- COMPLETED and `architecture_stage=H1B_AGENT_LOOP`;
- typed CALL `task-lookup-v3` -> authoritative observation -> typed CALL `task-search-v3` using `$obs`-derived assignee;
- >=2 and <=4 capability executions;
- every postcondition PASS;
- exact final task-key set == fresh Oracle B;
- typed FINAL only after requested outcomes are supported by observations.

## Phase 4 — REAL multi-step Challenge B / grounding
Fresh Oracle B then Agent A:
`Найди задачи Гаранина в DMS и затем покажи подробности DMS-380`

Require:
- canonical source-backed login for Garanin, never raw display name to AS21;
- one typed CALL to `task-search-v3` and one typed CALL to `task-lookup-v3` (order may vary);
- both outcomes preserved in observations/final response;
- exact search-key parity + exact DMS-380 identity parity;
- COMPLETED.

## Phase 5 — typed safety / no silent truncation
Prove all:
1. `{call:null, final:null}` is never executed as success.
2. Both CALL and FINAL selected simultaneously is never executed as success.
3. Legacy `action/capability_id`-only decision is never executed as typed success.
4. Unknown capability ID fails closed.
5. Unsupported constraint fails closed.
6. Invented `$ground` or `$obs` reference fails closed.
7. Duplicate capability+constraints is blocked and no run exceeds 4 calls.
8. `Проверь DMS-380 и затем покажи историю его статусов` must NOT silently succeed with only lookup; missing status-history capability must be explicit unsupported/fail-closed/clarification.

## Phase 6 — protected single-step exact parity
Fresh Oracle B then Agent A for:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`

Require COMPLETED + exact parity and typed planner behavior.

## Phase 7 — Browser C regression
Run:
`npm run e2e:h0`

Require 5/5 PASS. Start frontend if needed; do not skip.

## Phase 8 — Browser C multi-step
Use real Playwright Chromium in a fresh conversation for Challenge A. Persist screenshot, browser session id, correlated backend trace, CALL/CALL/FINAL behavior, rendered result and exact same-window Oracle parity.

## Phase 9 — final report
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_TYPED_DECISION_PROTOCOL_166.md`

Allowed verdicts ONLY:
- `AGENT_CORE_V3_H1B_TYPED_LOOP_GREEN`
- `H1B_TYPED_DECISION_RELIABILITY_RED`
- `H1B_TYPED_PROTOCOL_SAFETY_RED`
- `H1B_GROUNDING_RED`
- `H1B_OBSERVATION_PROPAGATION_RED`
- `H1B_AGENT_ORACLE_PARITY_RED`
- `H1B_SILENT_TRUNCATION_RED`
- `H1B_SINGLE_STEP_REGRESSION_RED`
- `H1B_BROWSER_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires ALL phases, including 10/10 reliability gate and Browser C. Commit/push only this report and STOP.

## Start now
Execute Assignment 166 completely. First pull, print HEAD + this Status line, verify owner commits, then preflight. Do not modify code.