# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_158_H1A_CAPABILITY_REGISTRY`

## Mission
Certify H1A of the Hermes re-architecture: Agent Core v3 now uses a reusable self-registering Capability Registry instead of the pilot-local hard-coded capability table.

This is a QA assignment only. Do not modify production/backend/frontend/test source code. If a defect is found, localize it and STOP for owner fix.

Required owner commits:
- `4b45864c71a1b02758608a3227fc39ad9e4f5a6f` — new `agent_core_v3_registry.py` with reusable registry/catalog.
- `9798faa350eeb593c30a797169b88526f26ddd59` — H1 task pilot consumes the registry and exposes registry metadata.
- `0b643d7e6bf7a4dcef2b4df939f81f4ea558b8d1` — registry unit tests.

H0 Browser baseline is already certified by Assignment 157 and MUST remain green.

## Architectural acceptance rules
H1A is not a rename. Prove all of the following:
1. Capability contracts are registered in one reusable registry abstraction, not duplicated in `AgentCoreV3PilotProcessor`.
2. Intent ownership is unique and duplicate registration fails closed.
3. Unknown intents fail closed; they are not guessed/routed to a default capability.
4. Registry metadata contains NO entity facts: no team-member names/logins, task IDs, counts, or hard-coded source results.
5. Compact catalog is deterministic and contains discovery metadata only; executor/oracle internals are not exposed in the compact LLM catalog.
6. Current task pilot resolves `task_lookup` and `task_search` through `registry.resolve_intent()`.
7. Accepted constraints still pass unchanged to capability validation/executor args.
8. Source authority remains REAL AS21.
9. H0 session/browser behavior and the four certified task scenarios do not regress.

## Absolute QA rules
- REAL AS21/MCP-SWTR is Oracle B for business facts.
- Browser C is real Playwright Chromium using the routed-request correlation certified in Assignment 157.
- No local DB/sync/fake/frozen/surrogate truth.
- Concurrency=1.
- Timeout 300s for source-backed cases; retry only proven transient source failures twice with 30s backoff.
- Exact task-key-set parity, not count-only parity.
- Production/backend/frontend/test edits forbidden.
- No caveat GREEN.

## Phase 0 — provenance/build
1. Pull current branch and record HEAD/clean state.
2. Prove all three H1A commits are ancestors.
3. Prove Assignment 157 report has verdict `PLAYWRIGHT_BROWSER_HARNESS_GREEN_H0_CERTIFIED`.
4. Inspect `agent_core_v3_registry.py` and `agent_core_v3_pilot.py`; explicitly show that the old local `PilotCapabilityRegistryV3`/hard-coded registration table is gone from the pilot.
5. Build/import smoke gate.

## Phase 1 — registry unit/contract gate
Run at minimum:
`pytest -q tests/test_agent_core_v3_registry.py tests/test_agent_core_v3_foundation.py`

Require all PASS.

Also report explicit evidence for:
- registry size = 2 for current certified task family;
- `task_lookup -> task-lookup-v3`;
- `task_search -> task-search-v3`;
- duplicate capability id rejected;
- duplicate intent owner rejected;
- unknown intent rejected;
- compact catalog stable across repeated reads;
- compact catalog contains no executor_id/oracle_id and no entity facts.

## Phase 2 — focused runtime registry proof
Start/verify production-like v3 runtime with REAL Task API and qwen LLM.

Execute through Agent A with fresh sessions:
1. `Задачи Гаранина`
2. `Покажи DMS-380`

For each require:
- COMPLETED;
- `_agent_core_v3.architecture_stage == H1A_REGISTRY`;
- `capability_catalog_size == 2`;
- correct capability id/version/family;
- source_authority == REAL_AS21;
- executor id is selected from the resolved registration;
- accepted constraints == executor args for requested constraints;
- llm_used=true for natural-language case;
- postconditions PASS.

Do not accept branch-by-intent evidence alone: show registry resolution metadata in returned trace/data.

## Phase 3 — fresh A/B exact parity
Fresh-read REAL AS21 Oracle B NOW for the same two scenarios.
Compare exact task-key sets:
- Garanin all approved spaces;
- DMS-380 point read.

Agent A exact keys must equal Oracle B exactly.

## Phase 4 — H0 Browser C protected regression
Run:
`npm run e2e:h0`

All five existing Playwright H0 tests must still PASS in real Chromium. This protects:
- session isolation;
- routed request correlation;
- `Задачи Гаранина`;
- `Задачи Гаранина в DMS`;
- `Задачи Калачанова в WMB`;
- `Покажи DMS-380`.

If browser expectations fail only because capability version changed from H1B to H1A, do NOT edit tests; report the exact mismatch for owner review. Existing UI semantics must remain compatible unless owner explicitly changes the contract.

## Phase 5 — final decision
Write:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1A_CAPABILITY_REGISTRY_158.md`

Allowed verdicts ONLY:
- `AGENT_CORE_V3_H1A_REGISTRY_GREEN`
- `H1A_REGISTRY_CONTRACT_RED`
- `H1A_RUNTIME_REGRESSION_RED`
- `H1A_BROWSER_REGRESSION_RED`
- `H1A_AGENT_ORACLE_PARITY_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires registry contract PASS + focused runtime PASS + fresh exact A/B parity + full H0 Playwright regression PASS.

Commit/push QA report only and STOP.

## Start now
Execute Assignment 158 completely.