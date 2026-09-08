# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_168_H1B_FINAL_TOKEN_BUDGET`

## Mission
Certify the owner fix for the exact failure proven by Assignment 167. The typed CALL/FINAL protocol and step-1 CALL are working, but the post-observation FINAL branch was deterministically truncated because the planner used `max_tokens=350` while REAL DMS-380 carries a ~6 KB description into the observation. Production now uses a bounded `max_tokens=1600` and explicitly instructs the planner to summarize source observations instead of copying long raw descriptions.

QA ONLY. Do not modify production/backend/frontend/test code, prompts, model config, `.env`, registry contracts, Playwright tests or runtime learning data.

## Required owner commit
Must be an ancestor before testing:
- `ce4f3695a5543d0ead5abf93b64d0cb6dc43d833` — raise H1B typed planner output budget 350 -> 1600 and require concise FINAL answers over large observations.

Accepted evidence from 167:
- no-response-format fix is correct;
- fresh retry construction is correct;
- typed CALL/FINAL structure, registry validation, `$ground/$obs`, duplicate blocking and max_steps=4 are intact;
- REAL DMS-380 step-1 CALL executes correctly;
- all failures were at step-2 FINAL after observation;
- raw evidence showed finish_reason=length and invalid truncated JSON at max_tokens=350;
- higher direct budgets (700/1400) stopped truncating, so this assignment must test the real production loop at the new 1600 budget rather than infer success from unit tests.

## Absolute rules
- Oracle B = fresh direct REAL AS21/MCP-SWTR only. No local DB/sync/fake/frozen/surrogate truth.
- Keep target model Qwen 3.8. Do not switch model or endpoint.
- Concurrency=1.
- Source timeout=300s. Only proven source outage gets exactly 2 retries with 30s backoff.
- Exact task-key-set equality for collections.
- No caveat GREEN.
- Commit/push only final QA report.

## Phase 0 — pull / preflight
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
2. Print HEAD, git status and this Status line.
3. Verify owner commit `ce4f3695...` is an ancestor.
4. Restart/reuse REAL MCP-SWTR + Task API + PO Agent v3 + frontend so the new planner code is loaded.
5. `/health` must prove v3=true, semantic LLM healthy, REAL source healthy; frontend reachable.
6. Static runtime proof from the LOADED planner source:
   - no `response_format` in planner runtime call;
   - `max_tokens=1600`;
   - fresh retry conversations remain intact;
   - typed CALL/FINAL protocol remains active;
   - concise-FINAL instruction is present;
   - no regex/keyword fallback.

If environment is unhealthy, STOP `BLOCKED_BY_PROVEN_ENVIRONMENT` before probes.

## Phase 1 — unit/static safety gate
Run:
`pytest -q tests/test_agent_core_v3_foundation.py tests/test_agent_core_v3_registry.py tests/test_agent_core_v3_loop.py tests/test_agent_core_v3_h1b_grounding.py tests/test_agent_core_v3_typed_planner.py`

Require all PASS.

Prove no regressions in:
- CALL/FINAL mutual exclusivity;
- both-null/both-selected fail closed;
- unknown capability/unsupported constraints fail closed;
- `$ground` and `$obs` source safety;
- duplicate blocking/postconditions/max_steps=4;
- no response_format;
- no deterministic task/person router fallback.

## Phase 2 — mandatory 10/10 production reliability gate
This is the STOPPING GATE. Use fresh sessions and concurrency=1. Do not proceed unless all ten pass.

### 2A — five REAL DMS-380 point reads
Run exactly 5 fresh production requests:
`Покажи DMS-380`

Each MUST:
- COMPLETED;
- `architecture_stage=H1B_AGENT_LOOP`;
- typed CALL `task-lookup-v3` for DMS-380;
- executor fetches REAL DMS-380;
- post-observation typed FINAL succeeds;
- no `finish_reason=length`, no truncated JSON, no invalid_json/no_typed_branch;
- returned task identity matches REAL Oracle B;
- record latency, planner attempts, loop steps, and if available finish_reason/output length for the FINAL planner call.

### 2B — five grounded human-name searches
Fresh same-window Oracle B for Garanin in DMS, then exactly 5 fresh requests:
`Задачи Гаранина в DMS`

Each MUST:
- COMPLETED;
- canonical source-backed login reaches AS21; raw Russian name does not;
- typed CALL `task-search-v3`;
- exact task-key set == same-window Oracle B;
- typed FINAL after observation;
- no output-token truncation or planner shape failure.

Phase 2 acceptance = **10/10 PASS**. If ANY run fails due to FINAL truncation/planner decision reliability, STOP with `H1B_FINAL_TOKEN_BUDGET_RED`. If a source error occurs, apply only the source retry policy and prove it separately.

## Phase 3 — REAL multi-step Challenge A
Fresh Oracle B then Agent A:
`Проверь DMS-380 и затем покажи задачи его исполнителя`

Require:
- COMPLETED, H1B_AGENT_LOOP;
- typed CALL lookup -> authoritative observation -> typed CALL assignee search via `$obs` -> typed FINAL;
- 2–4 capability calls;
- all postconditions PASS;
- exact final task-key-set parity;
- no truncation on finalization.

## Phase 4 — REAL multi-step Challenge B
Fresh Oracle B then Agent A:
`Найди задачи Гаранина в DMS и затем покажи подробности DMS-380`

Require one typed task-search and one typed task-lookup (order may vary), canonical grounded login, both outcomes preserved, exact collection parity + exact DMS-380 identity, COMPLETED.

## Phase 5 — safety / no silent truncation
Prove:
1. both-null and both-selected typed decisions never succeed;
2. legacy action-only decision never succeeds as typed decision;
3. unknown capability / unsupported constraint / invented `$ground` / invented `$obs` fail closed;
4. duplicate calls blocked and max 4;
5. unsupported compound `Проверь DMS-380 и затем покажи историю его статусов` cannot silently return partial lookup success;
6. planner must not dump the full ~6 KB DMS-380 description into FINAL merely because it exists in the observation unless the query explicitly requests full text.

## Phase 6 — protected single-step exact parity
Fresh Oracle B then Agent A:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`

Require COMPLETED + exact parity.

## Phase 7 — Browser C regression
Run existing `npm run e2e:h0`; require 5/5 PASS. Start frontend if needed. Do not skip.

## Phase 8 — Browser C multi-step
Fresh Playwright Chromium conversation for Challenge A. Persist screenshot, browser session, correlated backend trace, CALL/CALL/FINAL metadata, rendered result and same-window Oracle parity.

## Phase 9 — report
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_FINAL_TOKEN_BUDGET_168.md`

Allowed verdicts ONLY:
- `AGENT_CORE_V3_H1B_LOOP_GREEN`
- `H1B_FINAL_TOKEN_BUDGET_RED`
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

GREEN requires ALL phases including 10/10 and Browser C. Commit/push only this report and STOP.

## Start now
Execute Assignment 168 completely. First pull, print HEAD + Status, verify the owner commit, then healthy preflight before any expensive test.