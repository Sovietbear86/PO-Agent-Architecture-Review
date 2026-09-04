# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_159_H1A_RUNTIME_CONTINUATION`

## Mission
Continue H1A certification after Assignment 158 proved the Capability Registry contract GREEN but failed runtime/browser verification only because the QA backend was started with `agent_core_v3_enabled=false`.

DO NOT restart Assignment 158 from scratch. Phases 0-1 are already accepted PASS from report `po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1A_CAPABILITY_REGISTRY_158.md`.

This is QA only. Do not modify production/backend/frontend/test source code or committed `.env` files.

Required owner commits already certified at contract level:
- `4b45864c71a1b02758608a3227fc39ad9e4f5a6f`
- `9798faa350eeb593c30a797169b88526f26ddd59`
- `0b643d7e6bf7a4dcef2b4df939f81f4ea558b8d1`

Protected H0 baseline:
- Assignment 157 verdict `PLAYWRIGHT_BROWSER_HARNESS_GREEN_H0_CERTIFIED`.

## Absolute rules
- REAL AS21/MCP-SWTR is Oracle B.
- Browser C = real Playwright Chromium against mounted WorkspaceApp.
- No local DB, sync, fake, frozen or surrogate truth.
- Concurrency=1.
- Source-backed timeout 300s. Retry only proven transient source failures twice with 30s backoff.
- Exact task-key-set parity is mandatory.
- No production/backend/frontend/test source edits.
- Do not edit/commit `.env` just to enable v3.
- No caveat GREEN.

## Phase 0 — mandatory runtime preflight BEFORE any tests
1. Pull branch and record HEAD/clean state.
2. Read Assignment 158 report and confirm Phase 0-1 PASS; do not rerun them unless provenance changed.
3. Stop the old Agent backend on port 8004.
4. Start the Agent backend from `po-agent-platform-v2` with an environment override, preserving all existing working LLM/source environment variables:

`PO_AGENT_AGENT_CORE_V3_ENABLED=true PO_AGENT_AS21_MODE=task-api PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8003 python3 -m uvicorn po_agent.main:app --host 127.0.0.1 --port 8004 --timeout-keep-alive 300`

If the local runtime normally needs additional already-existing environment variables for qwen/AS21, preserve/reuse them. Do not erase them and do not create fake replacements.

5. BEFORE continuing, query `/health` and require all of:
- `agent_core_v3_enabled == true`
- semantic mode is qwen/LLM (`qwen-llm` or the equivalent configured production LLM mode)
- REAL AS21 source is healthy.

If v3 is false: STOP as `BLOCKED_BY_PROVEN_ENVIRONMENT` with raw startup/health evidence.
If source is degraded: restore/restart the existing REAL Task API/MCP-SWTR runtime and recheck health. Do not use local DB/sync/fake. If still unavailable after proven retries, STOP as `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`.

DO NOT launch Playwright or business tests until this preflight is GREEN.

## Phase 1 — focused H1A runtime registry proof
Use fresh session IDs and execute through Agent A:
1. `Задачи Гаранина`
2. `Покажи DMS-380`

For each require:
- `COMPLETED`;
- `_agent_core_v3.architecture_stage == H1A_REGISTRY`;
- `capability_catalog_size == 2`;
- correct capability id/version/family;
- `source_authority == REAL_AS21`;
- executor selected from resolved registry registration;
- accepted requested constraints preserved into executor args;
- `llm_used=true` for the natural-language case;
- postconditions PASS;
- no unexpected clarification/correction state.

Persist raw v3 metadata/trace evidence. Unit-level registry evidence alone is NOT sufficient here.

## Phase 2 — fresh REAL A/B exact parity
Fresh-read Oracle B directly from REAL AS21/MCP-SWTR NOW, not historical counts.

Compare exact task-key sets for:
- `Задачи Гаранина` — all approved spaces;
- `Покажи DMS-380` — exact point read.

Require Agent A exact key set == Oracle B exact key set. Persist timestamps/raw normalized sets.

## Phase 3 — protected Browser C regression
With the same healthy v3=true backend, run from frontend:

`npm run e2e:h0`

Require all 5 tests PASS in real Chromium:
- session isolation/new conversation;
- `Задачи Гаранина`;
- `Задачи Гаранина в DMS`;
- `Задачи Калачанова в WMB`;
- `Покажи DMS-380`.

The routed-request correlation from Assignment 157 must remain intact. UI must show Agent Core v3/current stage, fresh sessions must not enter correction state, and task results must remain semantically/source correct.

If Browser fails, report the exact first failing boundary. Do not edit tests or product code.

## Phase 4 — final decision
Write a NEW continuation report:

`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1A_RUNTIME_CONTINUATION_159.md`

Allowed verdicts ONLY:
- `AGENT_CORE_V3_H1A_REGISTRY_GREEN`
- `H1A_RUNTIME_REGRESSION_RED`
- `H1A_BROWSER_REGRESSION_RED`
- `H1A_AGENT_ORACLE_PARITY_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires:
- mandatory v3=true/LLM/source-healthy preflight PASS;
- focused runtime registry proof PASS;
- fresh exact A/B parity PASS;
- all 5 protected Playwright H0 tests PASS.

Commit/push ONLY the new QA report. Do not alter Assignment 158 report. STOP.

## Start now
Execute Assignment 159 completely. First output the current HEAD and the `Status` line above so it is explicit that this is a NEW continuation assignment, not completed Assignment 158.