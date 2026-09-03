# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_149_AGENT_CORE_V3_H1C_BROWSER_ABC`

## Mission
Certify the first REAL browser/UI vertical for Agent Core v3. This is the first mandatory A/B/C gate:
A = Agent Core v3 backend result,
B = independent REAL AS21/MCP-SWTR Oracle,
C = actual browser UI result.

QA only. Do not modify production/backend/frontend code.

## Owner changes to verify
- `efd568f27b4e85068ef8de9dc2ca4c3f476a7bdd` — accepted space constraint pushed into live source query.
- `ddcb15f5dc3ace922202e12e0be341d6d8cff18d` — UI API client exposes runtime health and sends explicit X-Session-Id.
- `9bb7908b6554e3c826495f378ce656863fbc1ff5` — Assistant UI uses tab-scoped session, explicit New dialogue, runtime/v3 trace indicator.
- `3b760966ccf558f9f38640c0ab37ccc3ba489279` — v3 feature flag documented.

## Absolute rules
- REAL AS21/MCP-SWTR is the only Oracle B.
- No local DB, sync, fake, frozen or previous report counts as truth.
- Browser C MUST be a real browser interaction with the rendered Assistant UI. Direct API calls cannot substitute for C.
- Start backend from current HEAD with `PO_AGENT_AGENT_CORE_V3_ENABLED=true`, task-api mode and production LLM settings.
- `/api/v1/health` must show `agent_core_v3_enabled=true`, `semantic_mode=qwen-llm`, healthy source.
- Use a NEW browser tab/incognito context with clean sessionStorage for the first case.
- Concurrency=1. Source timeout 300s. Retry transient source failures twice with 30s backoff.
- Exact task-key sets are mandatory where tasks are returned.
- Do not edit code if something fails. Localize and report.

## Phase 0 — build/runtime gate
1. Pull branch and record HEAD/clean state.
2. Verify the four owner commits are ancestors.
3. Build/typecheck frontend from current HEAD. Record exact command/result.
4. Start Task API, Agent backend with v3=true, and frontend.
5. Capture `/health` and browser runtime card. Browser must visibly show `Agent Core v3`, not Legacy Harness.

## Phase 1 — session isolation C gate
In browser C:
1. Record the visible session ID.
2. Click `Новый диалог`; prove session ID changes and chat resets.
3. Open a second browser tab/context; prove it gets a distinct tab-scoped session ID.
4. Return to first tab; prove its session ID is unchanged.
5. No first-turn response may enter stale correction/clarification state solely because of previous sessions.

## Phase 2 — fresh Oracle B
Independently read REAL AS21 for current exact truth of:
- Garanin.R.V all approved spaces;
- Garanin.R.V in DMS;
- Kalachanov.V.V in WMB;
- DMS-380 point-read.
Persist exact key sets and timestamps.

## Phase 3 — REAL A/B/C pilot 4/4
For each case use a fresh browser conversation (click New dialogue) and separately capture Agent A backend response/trace and browser C rendered result:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`

For every case require:
- Browser actually submits the text and renders the result;
- response footer visibly identifies `v3/H1B` (or current certified v3 stage), not legacy;
- natural-language cases visibly/trace-prove LLM use;
- Agent A exact task keys equal Oracle B;
- Browser C rendered answer/count/evidence correspond to the same Agent A response and trace_id;
- requested constraints survive: assignee, space, task_key as applicable;
- no unrelated-space evidence;
- postconditions PASS;
- first visible turn is not stale `correction_clarification`.

For Kalachanov+WMB specifically require exact fresh Oracle key set and no DMS evidence.

## Phase 4 — browser stale-session regression
1. In one browser conversation execute one pilot request.
2. Click New dialogue.
3. Execute a different pilot request.
4. Prove second request has a different session/conversation and is handled as a new turn, not a correction/recheck of the first.

## Phase 5 — strangler visibility
Restart isolated Agent backend with `PO_AGENT_AGENT_CORE_V3_ENABLED=false` without committing config changes.
Refresh/new browser context and prove runtime card shows Legacy Harness.
Submit a pilot-shaped query and prove browser footer does NOT claim v3 execution.
Restore/terminate isolated runtime after evidence.

## Final report
Write `po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1C_BROWSER_ABC_149.md`.

Allowed verdicts:
- `AGENT_CORE_V3_H1C_BROWSER_ABC_GREEN`
- `H1C_UI_SESSION_RED`
- `H1C_UI_RUNTIME_WIRING_RED`
- `H1C_BROWSER_PARITY_RED`
- `H1C_AGENT_AB_PARITY_RED`
- `H1C_FRONTEND_BUILD_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires all 4 scenarios complete in REAL browser C, exact A=B task truth, browser C linked to the same traces, session isolation proven, and v3/legacy runtime visibility proven.

Commit/push QA report only and STOP.
