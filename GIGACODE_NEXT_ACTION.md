# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_157_H0_ROUTED_REQUEST_FINAL`

## Mission
Close H0 using request-time interception instead of response-context inspection. Assignments 153-156 proved that this Playwright runtime does not reliably expose POST body or request headers through `response.request()`. The Browser C harness now captures the PO Agent drawer request at request-time with `page.route()`, identifies it by the drawer `X-Session-Id`, continues that exact request, and awaits the response belonging to that exact Playwright Request object.

QA only. Do not modify production/backend/frontend/test source code.

Required ancestors:
- `2cf89fcb3e60db9d274f510dcb467dc00684e1af` — production chat send reads authoritative tab sessionStorage at send-time.
- `ee52805dee27be3c4a4617d37e5863483f17a2f0` — Browser C correlates drawer query through request-time `page.route()` interception.
- `a446939d1fe8f02009f43e3c51532c6d89279f98` — routed-request harness typing cleanup.

## Known background traffic
`OverviewDashboard.tsx` launches four unrelated `/api/v1/query` calls on mount without conversational session IDs. They must be observed/ignored by correlation and must never be mistaken for the drawer request.

## Absolute rules
- REAL AS21/MCP-SWTR is Oracle B.
- Browser C = real Playwright Chromium against mounted recovery/WorkspaceApp.
- No manual verification, API-only or code-review substitute.
- No source/backend/frontend/test edits.
- Concurrency=1.
- Backend/source timeout 300s; retry only proven transient source failures twice with 30s backoff.
- Exact task-key parity mandatory for Agent A vs Oracle B.
- No caveat GREEN.

## Phase 0 — provenance/build
1. Pull current branch and record HEAD/clean state.
2. Prove all three commits above are ancestors.
3. Verify test harness uses `page.route('**/api/v1/query', ...)`, reads request headers in the route handler, resolves only the request whose `x-session-id` equals current drawer sessionStorage ID, calls `route.continue()`, then awaits `request.response()`.
4. Verify background dashboard calls remain sessionless and are not selected as drawer request.
5. Frontend build PASS.
6. Start/verify REAL Task API, Agent backend v3=true, frontend, Chromium; health source=healthy, semantic=qwen-llm, v3=true.

## Phase 1 — focused routed-request/session proof
Run:
`npm run e2e:h0 -- --grep "session isolation"`

PASS requires:
- initial/reset sessions are `ui-*`;
- New dialogue changes session;
- second page receives another session;
- first page retains its session;
- route handler captures the drawer request with `X-Session-Id == resetSession`;
- background sessionless `/query` requests are not selected;
- the exact captured Request object's response has `payload.session_id == resetSession`;
- rendered trace session_id == resetSession;
- no correction_recheck/correction_clarification on first fresh turn.

If route-time `request.headers()` itself does not expose `X-Session-Id`, report the raw headers/evidence and STOP as harness RED. Do not speculate about production session mutation.

## Phase 2 — full real Chromium suite
Run:
`npm run e2e:h0`

All five tests must PASS:
- session isolation;
- `Задачи Гаранина`;
- `Задачи Гаранина в DMS`;
- `Задачи Калачанова в WMB`;
- `Покажи DMS-380`.

Per pilot require:
- request submitted via rendered drawer;
- captured route request session == browser sessionStorage;
- exact captured response session == browser session;
- status COMPLETED;
- Agent Core v3/current stage visible;
- `_agent_core_v3.llm_used=true` for natural-language cases;
- trace/session details render;
- no unnecessary correction/clarification;
- WMB evidence has no wrong-space task;
- DMS-380 exact key renders.

## Phase 3 — fresh exact Oracle B
Fresh-read REAL AS21 now for all four pilots. Persist exact task-key sets and timestamps.
Compare Agent A exact result sets to Oracle B exactly. Browser C must render a semantically correct result tied to that same Agent execution; do not invent keys not rendered/exposed.

## Phase 4 — final H0 decision
Confirm Playwright report/trace/screenshot/video artifacts.
Write:
`po-agent-platform-v2/qa_reports/PLAYWRIGHT_H0_ROUTED_REQUEST_FINAL_157.md`

Allowed verdicts ONLY:
- `PLAYWRIGHT_BROWSER_HARNESS_GREEN_H0_CERTIFIED`
- `H0_ROUTED_REQUEST_RED`
- `H0_SESSION_ISOLATION_RED`
- `H0_BROWSER_C_RED`
- `H0_AGENT_PARITY_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires Phase 1 PASS + all five Chromium tests PASS + fresh exact Oracle B parity. No manual placeholders/caveats.

Commit/push QA report only and STOP.

## Start now
Execute Assignment 157 completely.