# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_164_H1B_GROUNDED_PLANNER_RECOVERY`

## Mission
Retest H1B after Assignment 163 proved three concrete defects: Qwen 3.8 sometimes emits an empty `action` for an otherwise final-shaped planner result; loop-first bypassed semantic grounding for human names; and H0 regressed as a consequence.

Owner fixes are now present. This is QA ONLY. Do not modify production/backend/frontend/test source code, prompts, `.env`, registry contracts or committed Playwright tests.

## Required owner commits
All MUST be ancestors before testing:
- `444929f06764c49202ca9dfa5cc5aa65a4c802e7` — planner receives source-grounded semantic values and only normalizes an empty action when the returned shape is unambiguously final (`final_answer` present, no capability/constraints).
- `31c481716b865d2ea174d3a003cfa224c08b3856` — H1B performs semantic grounding before the planner and supports `$ground.<field>` bindings; human names must reach AS21 as canonical logins.
- `db79fe9f6fa2f7ae56dd578ada5b361c5edbaef8` — grounding safety tests.

Accepted evidence from 163:
- real loop mechanics and observation propagation were already proven;
- 163 RED was planner-final reliability + missing grounding;
- Playwright baseline before the defect was 5/5.

## Absolute rules
- REAL AS21/MCP-SWTR is Oracle B. No local DB/sync/fake/frozen/surrogate truth.
- Qwen 3.8 remains the target model.
- Concurrency=1. Source timeout=300s. Proven source failures get exactly 2 retries with 30s backoff.
- Exact task-key-set parity required for task collections.
- No caveat GREEN.
- Commit/push only the QA report.

## Phase 0 — preflight
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
2. Record HEAD and git status.
3. Verify all 3 owner commits above are ancestors.
4. Restart/reuse REAL MCP-SWTR + Task API + PO Agent v3 with Qwen 3.8 and frontend used by Playwright.
5. `/health` must prove v3=true, semantic LLM healthy, source healthy; frontend must answer before Browser phases.

## Phase 1 — unit/safety gate
Run:
`pytest -q tests/test_agent_core_v3_foundation.py tests/test_agent_core_v3_registry.py tests/test_agent_core_v3_loop.py tests/test_agent_core_v3_h1b_grounding.py`

Require all PASS.

Static proof:
- planner catalog still comes only from H1A registry;
- `$obs` remains authoritative observation binding;
- `$ground.member_login` can only resolve from semantic grounder output, never an LLM-invented login;
- empty planner action is normalized to final ONLY when `final_answer` exists and there is no capability/constraints;
- empty/ambiguous actions without an explicit final answer still fail closed;
- max_steps=4 and duplicate blocking remain intact.

## Phase 2 — focused REAL challenge A
Fresh Oracle B then fresh Agent A:
`Проверь DMS-380 и затем покажи задачи его исполнителя`

Require:
- COMPLETED;
- H1B_AGENT_LOOP;
- lookup DMS-380 -> observation -> assignee task-search;
- second-step assignee exactly equals the source-backed login from the first observation;
- >=2 and <=4 capability calls;
- every postcondition PASS;
- exact task-key-set parity with fresh Oracle B;
- no planner empty-action failure on finalization.

Persist planner raw action/final shape on the final re-plan so the normalization behavior is auditable.

## Phase 3 — grounded REAL challenge B
Fresh Oracle B then fresh Agent A:
`Найди задачи Гаранина в DMS и затем покажи подробности DMS-380`

Require:
- semantic pre-pass resolves the human reference to the authoritative current login;
- AS21 task-search executor receives the canonical login, NOT raw `Гаранин/Гаранина`;
- one task-search-v3 with DMS + grounded assignee and one task-lookup-v3 for DMS-380;
- both outcomes preserved;
- exact search key parity + exact point-read parity;
- COMPLETED.

Any HTTP 409 caused by sending a raw human name is RED.

## Phase 4 — final-shape and safety controls
Prove all:
1. Empty `action` + nonempty `final_answer` + no capability/constraints can be normalized as final.
2. Empty `action` without final_answer still fails closed.
3. Invented `$ground.member_login` when grounder has no such value fails closed.
4. Invented `$obs` path fails closed.
5. Duplicate capability+constraints blocked; no >4 calls.
6. Unsupported compound request `Проверь DMS-380 и затем покажи историю его статусов` MUST NOT silently return only lookup as success. It must explicitly report unsupported/fail closed/clarify.

## Phase 5 — protected single-step recovery
Fresh Oracle B then Agent A for:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`

Require exact parity and COMPLETED where source truth supports it. Human-name cases must show canonical grounded logins in executor args.

## Phase 6 — Browser C regression
Run existing:
`npm run e2e:h0`

Require 5/5 PASS. Start frontend if needed; do not skip.

## Phase 7 — Browser C multi-step
Use real Playwright Chromium in a fresh conversation for Challenge A and persist screenshot/session/trace/H1B metadata plus exact Oracle parity from the same time window.

## Phase 8 — report
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_GROUNDED_PLANNER_RECOVERY_164.md`

Allowed verdicts:
- `AGENT_CORE_V3_H1B_LOOP_GREEN`
- `H1B_FINALIZATION_RELIABILITY_RED`
- `H1B_GROUNDING_RED`
- `H1B_OBSERVATION_PROPAGATION_RED`
- `H1B_AGENT_ORACLE_PARITY_RED`
- `H1B_SILENT_TRUNCATION_RED`
- `H1B_SINGLE_STEP_REGRESSION_RED`
- `H1B_BROWSER_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires all phases including Browser C. Commit/push only this report and STOP.

## Start now
Execute Assignment 164 completely. First pull, print HEAD, verify the owner commits, then run the preflight before any expensive tests.