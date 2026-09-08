# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_167_H1B_QWEN_NO_RESPONSE_FORMAT`

## Mission
Certify the owner fix for the Qwen 3.8 typed-planner provider incompatibility proven by Assignment 166. The typed CALL/FINAL protocol itself was correct, but the Qwen OpenAI-compatible endpoint corrupted planner JSON whenever `response_format` was supplied. Production planner now sends NO `response_format` at all and every bounded retry starts from a fresh conversation so malformed provider output cannot contaminate the next attempt.

QA ONLY. Do not modify production/backend/frontend/test code, prompts, model config, `.env`, registry contracts, Playwright tests or runtime learning data.

## Required owner commits
Both MUST be ancestors before testing:
- `118b4ef9226a48cebf785dbca5d5e9713f696008` — typed planner removes all `response_format` usage and uses clean independent retries.
- `01a4da13629e2c239ee351086af30b63af356ea1` — safety/unit proof for clean no-format retry construction.

Accepted evidence from Assignment 166:
- typed CALL/FINAL structural decision protocol is valid;
- REAL source and runtime were healthy;
- direct Qwen test without response_format produced correct typed JSON;
- json_schema/json_object response_format corrupted output and polluted subsequent retry history;
- 166 stopped at reliability gate as required.

## Absolute rules
- Oracle B = fresh direct REAL AS21/MCP-SWTR only. No local DB/sync/fake/frozen/surrogate truth.
- Keep target model Qwen 3.8; do not switch models.
- Concurrency=1.
- Source timeout=300s. Only proven source outage gets exactly 2 retries with 30s backoff.
- No caveat GREEN.
- Exact task-key-set equality for collections.
- Commit/push only final QA report.

## Phase 0 — preflight
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
2. Print HEAD, git status and this Status line.
3. Verify both owner commits above are ancestors.
4. Restart/reuse REAL MCP-SWTR, Task API, PO Agent v3 and frontend so latest code is loaded.
5. `/health`: v3=true, semantic LLM healthy, REAL source healthy. Frontend reachable.
6. Static proof from loaded planner source:
   - NO `response_format` argument is passed by `TypedAgentLoopPlannerV3.next_action()`;
   - retries rebuild a fresh base conversation and do not append malformed assistant output;
   - decision is still typed CALL/FINAL, not legacy action enum;
   - no deterministic regex/keyword fallback was added.

If environment is not healthy, STOP `BLOCKED_BY_PROVEN_ENVIRONMENT` before expensive tests.

## Phase 1 — unit/static safety gate
Run:
`pytest -q tests/test_agent_core_v3_foundation.py tests/test_agent_core_v3_registry.py tests/test_agent_core_v3_loop.py tests/test_agent_core_v3_h1b_grounding.py tests/test_agent_core_v3_typed_planner.py`

Require all PASS.

Prove:
- CALL and FINAL mutual exclusivity;
- both-null/both-selected fail closed;
- unknown capability and unsupported constraints fail closed;
- `$ground` and `$obs` safety preserved;
- duplicate blocking/postconditions/max_steps=4 preserved;
- retry messages contain no previous malformed assistant response;
- no response_format anywhere in typed planner runtime call.

## Phase 2 — mandatory 10/10 reliability gate
This is the STOPPING GATE. Use fresh sessions and concurrency=1.

### 2A — 5x point-read
Exactly five fresh requests:
`Покажи DMS-380`

Every run must be COMPLETED and prove:
- H1B_AGENT_LOOP;
- typed CALL to `task-lookup-v3`;
- exact DMS-380 identity from REAL source;
- typed FINAL after observation;
- no invalid_json/no_typed_branch caused by provider formatting;
- record planner attempt count and latency.

### 2B — 5x grounded human search
Fresh same-window Oracle B for `Garanin.R.V` in DMS, then exactly five fresh requests:
`Задачи Гаранина в DMS`

Every run must be COMPLETED and prove:
- canonical source-backed login reaches AS21, raw Russian display name never does;
- typed CALL `task-search-v3`;
- exact task-key set equals fresh Oracle B;
- typed FINAL after observation.

Phase 2 acceptance = **10/10 PASS**. If ANY planner/typed-decision failure occurs, STOP immediately with `H1B_NO_FORMAT_DECISION_RELIABILITY_RED`. Do not run later phases. A proven source error must use only the defined source retry policy and be evidenced separately.

## Phase 3 — REAL multi-step Challenge A
Fresh Oracle B then:
`Проверь DMS-380 и затем покажи задачи его исполнителя`

Require typed CALL lookup -> authoritative observation -> typed CALL assignee search using `$obs` -> typed FINAL; 2–4 calls; all postconditions PASS; exact final key-set parity.

## Phase 4 — REAL multi-step Challenge B
Fresh Oracle B then:
`Найди задачи Гаранина в DMS и затем покажи подробности DMS-380`

Require one typed task-search and one typed task-lookup (order may vary), canonical grounded login, both outcomes preserved, exact collection parity + exact DMS-380 identity, COMPLETED.

## Phase 5 — safety / no silent truncation
Prove:
1. both-null and both-selected typed decisions never succeed;
2. legacy action-only decision never succeeds as typed decision;
3. unknown capability / unsupported constraint / invented `$ground` / invented `$obs` fail closed;
4. duplicate calls blocked and max 4;
5. unsupported compound `Проверь DMS-380 и затем покажи историю его статусов` cannot silently return partial success.

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
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_QWEN_NO_RESPONSE_FORMAT_167.md`

Allowed verdicts:
- `AGENT_CORE_V3_H1B_LOOP_GREEN`
- `H1B_NO_FORMAT_DECISION_RELIABILITY_RED`
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
Execute Assignment 167 completely. First pull, print HEAD + Status, verify owner commits, then healthy preflight before tests.