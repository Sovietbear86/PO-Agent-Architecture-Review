# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_163_H1B_PLANNER_HARDENING_RETEST`

## Mission
Retest H1B after Assignment 162 proved that the real two-capability loop and observation propagation work, but exposed two owner defects: planner structured-output reliability on the final re-plan and compound requests being intercepted by the old single-shot path.

This is QA ONLY. Do not modify production/backend/frontend/test code, prompts, `.env`, registry contracts or committed Playwright tests.

## Accepted evidence from 162
Do NOT re-litigate these findings unless regression appears:
- real loop executed two source-backed capability calls;
- DMS-380 lookup observation supplied `assignee_login` to the later task-search call;
- REAL AS21 remained authoritative;
- H1A single-step behavior was still healthy;
- 162 RED root causes were planner JSON reliability + single-shot interception;
- Browser C was not executed only because frontend was not started.

## Required new owner commits
All must be ancestors of HEAD:
- `de77bb1147343352e9b0d349076c7350d1d31f44` — robust planner JSON extraction + strict structured-output schema with bounded fallbacks.
- `95b1da53259bf01ad534b74248464512a17e73d6` — H1B loop-first processor; planner is now primary control flow for certified v3 task requests.
- `5f8a2d36680d95782a09b778f6874b4a8cb7578f` — production runtime wires the loop-first H1B processor.
- `09453e8ddb5d97d0130a6480983554c2179dc6d8` — regression tests for wrapped/embedded planner JSON.

## Absolute rules
- Oracle B = fresh direct REAL AS21/MCP-SWTR only.
- No local DB/sync/fake/frozen/surrogate truth.
- Concurrency=1.
- Source-backed timeout=300s; exactly 2 retries with 30s backoff for proven transient source failures.
- Exact task-key-set equality mandatory for task collections.
- Qwen 3.8 target model remains unchanged.
- No caveat GREEN.
- Commit/push only the final QA report.

## Phase 0 — pull and runtime preflight
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
2. Record HEAD and git status.
3. Verify the four new owner commits above are ancestors.
4. Start/restart production-like services so the NEW code is loaded:
   - REAL MCP-SWTR / Task API healthy;
   - PO Agent backend with `PO_AGENT_AGENT_CORE_V3_ENABLED=true` and working Qwen 3.8;
   - frontend/Vite on the port expected by Playwright (normally 5173).
5. Verify `/health`: v3=true, semantic LLM healthy, REAL source healthy.
6. Verify frontend URL responds before Browser phases. If frontend is not running, START IT; do not mark Browser C unavailable merely because it was not started.

## Phase 1 — unit/static gate
Run:
`pytest -q tests/test_agent_core_v3_foundation.py tests/test_agent_core_v3_registry.py tests/test_agent_core_v3_loop.py`

Require all PASS.

Static proof:
- production runtime uses `AgentCoreV3H1BProcessor` when v3=true;
- loop-first `process()` does not execute the old semantic single-shot path before planner invocation;
- planner response parser accepts valid JSON wrapped in `<think>`, markdown or provider prose but still validates closed capability/action contracts;
- capability registry, observation-reference safety, max_steps=4 and duplicate blocking remain intact.

## Phase 2 — focused planner reliability / REAL challenge A
Fresh Oracle B, then fresh Agent A:
`Проверь DMS-380 и затем покажи задачи его исполнителя`

Oracle B:
1. fresh point-read DMS-380;
2. independently verify current source-backed assignee login;
3. fresh live assignee-task search;
4. persist exact key set.

Agent A must be COMPLETED and prove:
- `architecture_stage=H1B_AGENT_LOOP`;
- >=2 and <=4 capability executions;
- lookup DMS-380 -> validated observation -> search using observation-derived assignee;
- planner re-plan/final completes successfully; no `V3_PROCESSOR_UNAVAILABLE`;
- every postcondition PASS;
- exact final task-key set == Oracle B.

Persist planner-call count and latency. A valid final JSON hidden in provider wrapper must not cause RED.

## Phase 3 — loop-first / REAL challenge B
Fresh Oracle B, then fresh Agent A:
`Найди задачи Гаранина в DMS и затем покажи подробности DMS-380`

Require:
- request enters H1B planner directly, NOT old task_lookup interception/fallback;
- one task-search-v3 for grounded Garanin + DMS;
- one task-lookup-v3 for DMS-380;
- both requested outcomes preserved in observations;
- exact search key parity and exact task identity parity;
- COMPLETED.

Order may vary.

## Phase 4 — no silent truncation safety
Fresh session:
`Проверь DMS-380 и затем покажи историю его статусов`

Current task registry does not provide a status-history capability. Therefore acceptable result is fail-closed/unsupported/clarification. It MUST NOT return COMPLETED with only the DMS-380 lookup while silently ignoring the second requested operation.

Also verify:
- invented observation reference fails closed;
- unavailable assignee reference fails closed;
- duplicate same capability+constraints is blocked;
- no run exceeds 4 capability executions.

## Phase 5 — protected single-step regression through LOOP-FIRST
Fresh Oracle B for each:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`

Important: because H1B is now primary, prove these still return correct results through the new control flow. Require exact Oracle parity and no stale session/correction contamination.

## Phase 6 — full existing Browser C regression
Run:
`npm run e2e:h0`

Require 5/5 PASS. If frontend is down, start it and rerun. Do not classify a non-started frontend as product failure or acceptable skip.

## Phase 7 — Browser C multi-step
Using real Playwright Chromium and a fresh conversation, execute Challenge A.

Persist:
- screenshot;
- browser session id;
- correlated backend trace;
- H1B loop metadata;
- rendered final result;
- exact task-key parity with a fresh Oracle B read from the same time window;
- no stale correction/clarification.

Ephemeral `/tmp` test code is allowed; do not edit committed Playwright test source.

## Phase 8 — report
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_PLANNER_HARDENING_163.md`

Allowed verdicts:
- `AGENT_CORE_V3_H1B_LOOP_GREEN`
- `H1B_PLANNER_RELIABILITY_RED`
- `H1B_LOOP_FIRST_ROUTING_RED`
- `H1B_OBSERVATION_PROPAGATION_RED`
- `H1B_AGENT_ORACLE_PARITY_RED`
- `H1B_SILENT_TRUNCATION_RED`
- `H1B_SINGLE_STEP_REGRESSION_RED`
- `H1B_BROWSER_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires ALL phases including Browser C. Commit/push only this report and STOP.

## Start now
Execute Assignment 163 completely. First pull the branch and print HEAD + this Status line.