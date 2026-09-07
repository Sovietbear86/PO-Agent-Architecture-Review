# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_162_H1B_HERMES_AGENT_LOOP_CERTIFICATION`

## Mission
Certify the first real H1B Hermes-style Agent Core v3 loop after Assignment 161 proved the previous runtime was single-shot.

Owner implementation is now present. The target behavior is a bounded LLM-driven cycle:
`plan -> capability -> execute -> authoritative observation -> re-plan -> next capability/final`.

This is QA ONLY. Do not modify production/backend/frontend/test source code, prompts, registry contracts, `.env`, or committed Playwright tests. If a defect exists, localize the first failing boundary and STOP for owner repair.

## Required owner commits
All MUST be ancestors of HEAD before testing:
- `9da9b051716fea7592e731fbe28e9fe53a176f03` — bounded H1B LLM planner + observation-reference contract.
- `1c68d05c1864983f5680c98c4900881b64b81ad2` — Agent Core v3 executes bounded multi-step capability loop.
- `c315c87c3d4752857c5200e6662a9282c6fe4504` — production runtime wires planner to the same configured LLM.
- `50837d81eff33dcb08ada1136c5e15162db9bff0` — H1B loop safety contract tests.

Accepted baseline:
- Assignment 157: Browser C H0 harness GREEN.
- Assignment 160: H1A Registry GREEN, REAL AS21 exact parity, Playwright 5/5.
- Assignment 161: single-step 3/3 GREEN; multi-step absent in previous implementation.
- PO Agent target LLM remains the working Qwen 3.8 configuration. Do not change it.

## Architectural acceptance rules
H1B is GREEN only if ALL are proven:
1. The LLM chooses capability actions from the H1A registry; no phrase-specific/hard-coded multi-step route.
2. One user turn can execute at least two registry capabilities.
3. A second-step source constraint can be derived only from a validated prior observation (for example assignee login from task lookup), not invented by the LLM.
4. Every capability call is contract-validated before execution and postcondition-validated after execution.
5. REAL AS21/MCP-SWTR remains authoritative for every tool step.
6. The planner is called again after observation and receives prior observations.
7. Duplicate capability+constraint calls are blocked.
8. Loop is bounded (`max_steps=4`) and fails closed when it cannot finish safely.
9. Single-step H0/H1A behavior does not regress.
10. No entity facts, member logins, task IDs, counts or approved answers are hard-coded into planner/registry production code.

## Absolute test rules
- Oracle B = fresh direct REAL AS21/MCP-SWTR reads only.
- No local DB, sync, fake, frozen or surrogate truth.
- Concurrency=1.
- Source-backed timeout 300s.
- A proven source error must receive exactly 2 retries with 30s backoff before being called transient.
- Exact task-key-set equality is mandatory wherever a task set is returned.
- Do not accept prose-only evidence; inspect `_agent_core_v3.loop_steps`, observations, executor args and evidence.
- Production/backend/frontend/test code edits are forbidden.
- No caveat GREEN.

## Phase 0 — provenance and runtime preflight
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
2. Record HEAD and git status.
3. Verify all 4 owner commits above are ancestors of HEAD.
4. Verify Assignment 161 report exists and proves previous `CURRENT_SINGLE_SHOT` boundary.
5. Start/reuse production-like runtime with:
   - `PO_AGENT_AGENT_CORE_V3_ENABLED=true`;
   - working Qwen 3.8 LLM configuration;
   - REAL Task API + MCP-SWTR;
   - source healthy.
6. `/health` must prove v3=true, LLM semantic mode, source healthy before Phase 1.

STOP as `BLOCKED_BY_PROVEN_ENVIRONMENT` if runtime preflight is not healthy. Do not waste later phases on a wrong feature flag/model/source state.

## Phase 1 — H1B unit/safety gate
Run focused tests:

`pytest -q tests/test_agent_core_v3_foundation.py tests/test_agent_core_v3_registry.py tests/test_agent_core_v3_loop.py`

Require all PASS.

Static audit these files without editing:
- `src/po_agent/harness/agent_core_v3_loop.py`
- `src/po_agent/harness/agent_core_v3_pilot.py`
- `src/po_agent/harness/runtime_factory.py`

Prove:
- planner catalog comes from `CapabilityRegistryV3`;
- no entity facts are embedded in planner code;
- `$obs.<step>.<path>` is resolved deterministically from already-returned observation data;
- literal task keys/spaces cannot be silently invented;
- max step bound is 4;
- duplicate identical calls fail closed.

## Phase 2 — REAL multi-step A/B challenge A
Fresh session. User request:

`Проверь DMS-380 и затем покажи задачи его исполнителя`

### Oracle B
Independently, directly against REAL AS21:
1. point-read `DMS-380`;
2. extract its current authoritative assignee login/external identifier from the source result;
3. independently search all tasks assigned to that exact person using the live source path;
4. persist exact normalized task-key set and timestamp.

Do NOT reuse Agent A's assignee as Oracle input unless you independently verify it against the point-read first.

### Agent A
Execute the exact natural-language request once through `/api/v1/query` in a fresh session.

Require:
- status `COMPLETED`;
- `architecture_stage == H1B_AGENT_LOOP`;
- `loop_step_count >= 2` and `<= 4`;
- first relevant capability is `task-lookup-v3` with `task_key=DMS-380`;
- first observation contains the real task and source-backed assignee identity;
- a later capability is `task-search-v3`;
- its assignee executor arg equals the assignee from the prior observation;
- the trace proves the second arg originated from an observation binding, not a hard-coded/person guess;
- every step postcondition result PASS;
- source authority REAL_AS21;
- Agent A final task-key set == fresh Oracle B exact task-key set.

If it returns the correct prose but only one capability ran, verdict is RED.

## Phase 3 — REAL multi-step A/B challenge B
Fresh session. User request:

`Найди задачи Гаранина в DMS и затем покажи подробности DMS-380`

Oracle B must independently read:
- fresh exact task set for Garanin in DMS;
- fresh point-read for DMS-380.

Agent A must execute two distinct capability calls in one turn and observations must preserve BOTH requested outcomes. Require:
- one `task-search-v3` call with grounded assignee + DMS;
- one `task-lookup-v3` call for DMS-380;
- no loss of DMS constraint in the search step;
- no mutation of DMS-380;
- exact key parity for search result and exact identity parity for point lookup;
- final response grounded only in observations.

The order may be chosen by the LLM planner; do not require a specific order as long as dependencies/constraints are correct.

## Phase 4 — negative safety challenges
Run fresh-session negative cases and prove fail-closed behavior:
1. Ask a compound request whose second step requires a capability outside the current task registry. It must NOT fabricate a tool or answer.
2. Attempt a request where an assignee for step 2 is not available in the prior observation. It must clarify/fail closed, not invent a login.
3. Verify no duplicate identical tool call loop occurs.
4. Verify no run exceeds 4 capability executions.

Persist failure code/trace for each control.

## Phase 5 — protected single-step regression
Fresh Oracle B first, then Agent A for the protected baseline:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`

Require exact parity with fresh Oracle B and no stale session/correction state.

Then run existing Browser C regression:

`npm run e2e:h0`

Require 5/5 PASS.

## Phase 6 — Browser C H1B multi-step proof
Use real Playwright Chromium against the mounted WorkspaceApp. Do NOT substitute API-only evidence.

Because committed Playwright test source is QA-protected in this assignment, use an ephemeral non-repository script/spec under `/tmp` or equivalent and do not commit it.

In a fresh browser conversation execute Challenge A from Phase 2 and record:
- screenshot of the final rendered answer;
- browser session id;
- correlated backend trace id;
- visible absence of stale correction/clarification;
- backend H1B loop metadata for the same request;
- exact task-key-set parity with the SAME fresh Oracle B from the browser-run time window.

If Browser C cannot be executed due to tooling/environment, verdict cannot be GREEN.

## Phase 7 — final report
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_HERMES_LOOP_162.md`

Allowed verdicts ONLY:
- `AGENT_CORE_V3_H1B_HERMES_LOOP_GREEN`
- `H1B_PLANNER_SELECTION_RED`
- `H1B_OBSERVATION_PROPAGATION_RED`
- `H1B_CONSTRAINT_SAFETY_RED`
- `H1B_AGENT_ORACLE_PARITY_RED`
- `H1B_BROWSER_REGRESSION_RED`
- `H1B_SINGLE_STEP_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

Report MUST include for both positive multi-step challenges:
- planner/capability step sequence;
- resolved executor args per step;
- observation source facts used by later steps;
- postcondition results;
- exact Agent A vs Oracle B comparison;
- total loop iterations and latency.

Commit/push ONLY the QA report and STOP.

## Start now
Execute Assignment 162 completely. Do not modify code. The purpose is to prove whether the new owner implementation is a REAL observation-driven Hermes-style loop, not merely new metadata around the old single-shot path.