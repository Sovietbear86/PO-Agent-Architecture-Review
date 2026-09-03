# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_145_AGENT_CORE_V3_H1B_RETEST`

## Mission
Re-test H1B after owner fixes from Assignment 144. QA only: do not modify production/backend/frontend code.

Owner fixes to verify in ancestry:
- `f3baf402238f7c416735dfa8dd2f986b3d5d5363` — Settings exposes `PO_AGENT_AGENT_CORE_V3_ENABLED`, default false.
- `8bb8220d193a6e800da8b103ddbb6045cf7cf7c9` — API passes the setting into runtime factory; health exposes v3 state; X-Session-Id fallback restored.
- `ace38f4b4e439a8272e427b4b08671da12528a17` — live assignee adapter no longer re-filters authoritative AS21 identity into a false zero result.

The prior report established fresh Oracle B truth: Garanin all approved spaces=16, Garanin DMS=8, Kalachanov WMB=0, DMS-380 exists. Re-read Oracle B fresh for this run; do not reuse counts as truth.

## Absolute rules
- QA/tester only. No production code changes.
- REAL AS21/MCP-SWTR is the only factual Oracle. No local DB, sync, fake, frozen or cached task facade as truth.
- Do not run the 54-skill marathon.
- Concurrency=1. Timeout 300s. Retry transient transport/source failures twice with 30s backoff.
- Fresh session UUID per independent case.
- Exact task-key-set equality is mandatory.
- Do not declare semantic GREEN unless `_agent_core_v3.llm_used=true` for natural-language pilot cases.

## Phase 0 — provenance/config gate
1. Pull branch and record HEAD/clean state.
2. Prove all three owner fixes are ancestors.
3. Prove Settings behavior directly:
   - env unset -> `agent_core_v3_enabled == False`;
   - `PO_AGENT_AGENT_CORE_V3_ENABLED=true` -> True after settings reset.
4. Start isolated v3 runtime using existing project `.env`/LLM credentials plus:
   `PO_AGENT_AS21_MODE=task-api`, live task-api base URL, `PO_AGENT_AGENT_CORE_V3_ENABLED=true`.
5. `/health` must report `agent_core_v3_enabled=true` and `semantic_mode=qwen-llm`. If LLM credentials are absent, classify environment evidence precisely; do not call this a code semantic failure.

## Phase 1 — adapter live-route certification before Harness
Fresh direct Oracle B via MCP-SWTR and independent Agent-side adapter call.

Cases:
- `adapter.search_tasks("assignee = Garanin.R.V", max_results=100)` must equal fresh Oracle B exact key set across approved spaces.
- `adapter.search_tasks("assignee = Garanin.R.V AND project = DMS", max_results=100)` must equal fresh DMS Oracle B exact key set.
- `adapter.search_tasks("assignee = Kalachanov.V.V AND project = WMB", max_results=100)` must equal fresh WMB Oracle B exact key set, including valid zero if Oracle B is zero.

Capture endpoint/path proof showing the adapter uses `/api/v1/swtr-read/assignee-tasks`, not `/api/v1/tasks`.

## Phase 2 — v3 trace and A/B
Run isolated v3 requests:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`

For each v3-routed response capture `_agent_core_v3` completely. Require:
- stage H1B;
- natural-language cases `llm_used=true`;
- interpreter class is LLM-backed production semantic stack, not FailClosedSemanticInterpreter;
- raw semantic frame and grounded values present;
- immutable accepted contract contains every explicitly requested constraint;
- capability/executor/source authority/oracle metadata present;
- postcondition validation passes;
- exact key-set equality vs fresh Oracle B;
- no unrelated-space evidence;
- DMS-380 exact point read;
- valid zero result is not source-unavailable.

If a request does not contain `_agent_core_v3`, classify ROUTING_RED and capture health/config plus selector evidence.

## Phase 3 — safety/strangler regression
- Synthetic wrong-space row under WMB accepted contract -> typed `RESULT_CONTRACT_VIOLATION`.
- Missing requested space in executor args -> typed `CONSTRAINT_LOSS`.
- v3 enabled + validated non-pilot sprint/release query -> legacy delegation.
- v3 disabled + pilot-shaped query -> legacy delegation.
- `DMS-999999999` -> authoritative NOT_FOUND, not source unavailable.

## Phase 4 — report
Write `po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_RETEST_145.md` with raw evidence references, fresh Oracle sets, Agent sets, diffs, trace metadata, latency, retries and exact failure localization.

Allowed verdicts:
- `AGENT_CORE_V3_H1B_GREEN`
- `AGENT_CORE_V3_CONFIG_RED`
- `AGENT_CORE_V3_ADAPTER_RED`
- `AGENT_CORE_V3_SEMANTIC_RED`
- `AGENT_CORE_V3_AB_PARITY_RED`
- `AGENT_CORE_V3_CONSTRAINT_RED`
- `AGENT_CORE_V3_ROUTING_RED`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires config activation proven, LLM-backed v3 execution proven, adapter parity proven, all four pilot scenarios exact A/B, and safety/strangler checks PASS.

Commit/push QA report only and STOP.

## Start now
Execute Assignment 145 completely.