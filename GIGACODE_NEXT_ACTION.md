# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_150_H0_REAL_WORKSPACE_CUTOVER`

## Mission
Certify the actual mounted Workspace UI after owner H0 cutover. This replaces the invalid old browser certification that tested the wrong assistant entry point.

Owner commit to verify:
- `e0ba90672ceb50bd4546c870067750947df0570e` — real `recovery/WorkspaceApp` chat moved to tab-scoped session lifecycle, explicit New dialogue, visible runtime/session metadata, Agent Core API entry.

QA only. Do not modify production/backend/frontend code.

## Absolute rules
- REAL AS21/MCP-SWTR is the only factual Oracle B.
- Browser C must be the actual mounted `recovery/WorkspaceApp` rendered by `main.tsx`; direct API cannot substitute.
- Production code edits are forbidden.
- Start current HEAD with task-api mode, production LLM settings, and `PO_AGENT_AGENT_CORE_V3_ENABLED=true`.
- Fresh browser tab/context for the first case.
- Concurrency=1. Timeout 300s. Retry transient source failures twice with 30s backoff.
- Exact key-set parity, not counts only.

## Phase 0 — provenance/build
1. Pull current branch, record HEAD and clean state.
2. Prove owner commit `e0ba9067...` is ancestor.
3. Prove `main.tsx` mounts `recovery/WorkspaceApp`.
4. Prove the mounted WorkspaceApp no longer uses localStorage for transient session identity; it uses sessionStorage and exposes New dialogue.
5. Frontend build/typecheck must pass.

## Phase 1 — real browser session isolation
In the actual Workspace UI:
1. Open the PO Agent drawer and record visible session ID and runtime label.
2. Click `Новый диалог`; session ID must change and chat must reset.
3. Open a second browser tab/context; it must receive a different tab-scoped session ID.
4. Return to first tab; its session ID must remain unchanged.
5. First request in a fresh conversation must not inherit correction/recheck state from any prior conversation.

## Phase 2 — fresh Oracle B
Independently read REAL AS21 for:
- Garanin.R.V all approved spaces;
- Garanin.R.V in DMS;
- Kalachanov.V.V in WMB;
- DMS-380 point read.
Persist exact key sets and timestamps.

## Phase 3 — actual Workspace A/B/C 4/4
For each case click `Новый диалог` first, then submit through the real browser drawer:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`

Require for every case:
- request sent from actual Workspace browser C;
- visible response runtime says Agent Core v3/current v3 stage, not Legacy Harness;
- response trace/session_id visible and matches request/backend response;
- natural-language pilot trace proves `llm_used=true`;
- Agent result exact keys == fresh Oracle B;
- browser rendered/evidence keys == fresh Oracle B;
- explicit constraints survive end-to-end;
- no unrelated-space/member evidence;
- postconditions PASS;
- no unnecessary login/filter clarification for uniquely grounded identities.

## Phase 4 — stale correction regression
1. In one conversation execute any pilot request.
2. Click New dialogue.
3. First query in new conversation: `Задачи Калачанова в WMB`.
4. It must be treated as a new independent turn, never `correction_recheck` or correction clarification solely due to previous chat.

## Phase 5 — v3/legacy visibility
Restart isolated Agent backend with `PO_AGENT_AGENT_CORE_V3_ENABLED=false` without committing config changes.
Refresh/new browser context.
- Workspace drawer must visibly show Legacy Harness.
- Pilot-shaped query must not claim `_agent_core_v3` execution.
Restore/terminate isolated runtime afterward.

## Final report
Write `po-agent-platform-v2/qa_reports/H0_REAL_WORKSPACE_CUTOVER_150.md`.

Allowed verdicts:
- `H0_REAL_WORKSPACE_CUTOVER_GREEN`
- `H0_FRONTEND_ENTRY_RED`
- `H0_SESSION_ISOLATION_RED`
- `H0_RUNTIME_WIRING_RED`
- `H0_BROWSER_PARITY_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires actual mounted Workspace browser 4/4 A/B/C, session isolation, no stale correction leakage, and truthful v3/legacy visibility.

Commit/push QA report only and STOP.

## Start now
Execute Assignment 150 completely.