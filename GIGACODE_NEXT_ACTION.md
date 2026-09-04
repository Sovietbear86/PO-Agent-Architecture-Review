# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_156_H0_RESPONSE_CORRELATION_FINAL`

## Mission
Re-test H0 after identifying the real Browser C harness defect from Assignment 155: the Playwright waiter accepted the first arbitrary `/api/v1/query` response on the page, while `OverviewDashboard` itself launches four background agent queries on mount without a conversational session ID. Those background responses use backend-generated UUID session IDs and were being falsely compared with the drawer's `ui-*` session.

QA only. Do not modify production/backend/frontend/test source code.

Required ancestor commits:
- `2cf89fcb3e60db9d274f510dcb467dc00684e1af` — production chat send reads authoritative tab sessionStorage at send-time.
- `a939c86e90a811dec0fce596049a467573a71fda` — Browser C test now correlates the awaited `/api/v1/query` response by the drawer conversation's `X-Session-Id`, so background dashboard queries cannot be mistaken for chat responses.

## Critical root-cause correction
Assignment 155's conclusion that sessionStorage mysteriously changed is NOT accepted unless reproduced after response correlation.

The mounted `OverviewDashboard.tsx` executes these four background calls on mount via `agent.query({ query })` with no session_id:
- `Дай обзор и риски`
- `Покажи очередь внимания`
- `Сделай daily brief`
- `Сделай status report`

Therefore the old Playwright predicate `any POST /api/v1/query` could capture one of those responses. A backend-generated UUID such as `b0376e75-...` without the `ui-` prefix is strong evidence of that contamination, not proof that the drawer sessionStorage changed.

## Absolute rules
- REAL AS21/MCP-SWTR is Oracle B.
- Browser C = actual Playwright Chromium against mounted recovery/WorkspaceApp.
- No manual verification/API-only/code-review substitute.
- Production/backend/frontend/test source edits forbidden.
- Concurrency=1.
- Backend/source timeout 300s; retry only proven transient source failures twice with 30s backoff.
- Exact task-key parity is mandatory where exposed.
- No caveat GREEN.

## Phase 0 — provenance/build
1. Pull current branch; record HEAD and clean state.
2. Prove `2cf89fcb...` and `a939c86e...` are ancestors.
3. Verify `OverviewDashboard.tsx` really emits background `/api/v1/query` calls without conversational session IDs.
4. Verify `h0-workspace.spec.ts` now waits only for a `/api/v1/query` request whose `x-session-id` header equals the current drawer `sessionStorage` ID.
5. Frontend build PASS.
6. Start/verify REAL Task API, Agent backend v3=true, frontend, Playwright Chromium; health source=healthy, semantic=qwen-llm, v3=true.

## Phase 1 — focused response-correlation/session proof
Run:
`npm run e2e:h0 -- --grep "session isolation"`

PASS requires:
- initial and reset session IDs are `ui-*`;
- New dialogue changes the session;
- second Chromium page has another `ui-*` session;
- first page retains its session;
- chat request observed by the test has `X-Session-Id == resetSession`;
- backend payload.session_id == resetSession;
- rendered trace session_id == resetSession;
- no correction_recheck/correction_clarification on first fresh turn.

Also record any concurrent background `/api/v1/query` responses and prove they are ignored by the chat waiter. If the old random UUID mismatch disappears, classify Assignment 155 as `FALSE_RESPONSE_CORRELATION`, not a production session bug.

## Phase 2 — full Chromium H0 suite
Run full:
`npm run e2e:h0`

Require all five tests PASS:
- session isolation;
- `Задачи Гаранина`;
- `Задачи Гаранина в DMS`;
- `Задачи Калачанова в WMB`;
- `Покажи DMS-380`.

Per pilot require COMPLETED, Agent Core v3 stage visible, `llm_used=true` for NL cases, browser session == request X-Session-Id == backend session == rendered trace, no unexpected correction/clarification, WMB no wrong-space evidence, DMS-380 exact key rendered.

## Phase 3 — fresh Oracle B
Fresh-read REAL AS21 for all four pilot truths now. Persist exact key sets and timestamps. Compare Agent/browser evidence against the fresh exact sets, not historical counts.

If browser evidence currently renders only a bounded subset, explicitly distinguish `exact Agent A parity` from `rendered Browser C evidence subset`; do not invent unseen keys. H0 GREEN requires the user-visible result to be semantically correct and the corresponding Agent A execution to have exact Oracle parity.

## Phase 4 — final decision
Write NEW report:
`po-agent-platform-v2/qa_reports/PLAYWRIGHT_H0_RESPONSE_CORRELATION_156.md`

Allowed verdicts ONLY:
- `PLAYWRIGHT_BROWSER_HARNESS_GREEN_H0_CERTIFIED`
- `H0_RESPONSE_CORRELATION_RED`
- `H0_SESSION_ISOLATION_RED`
- `H0_BROWSER_C_RED`
- `H0_AGENT_PARITY_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires Phase 1 PASS + all five Chromium tests PASS + fresh Oracle parity. No manual placeholders and no caveat GREEN.

Commit/push QA report only and STOP.

## Start now
Execute Assignment 156 completely.