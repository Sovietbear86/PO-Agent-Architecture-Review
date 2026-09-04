# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_155_PLAYWRIGHT_H0_FINAL_CERTIFICATION`

## Mission
Close H0 after Assignment 154 proved the remaining RED is only an unavailable Playwright request-body observation, not production session propagation. QA only: do not modify production/backend/frontend/test source code.

Required ancestor commits:
- `2cf89fcb3e60db9d274f510dcb467dc00684e1af` — production send() reads authoritative tab session from sessionStorage at send-time.
- `1386f22c05cb3540f929c323b66705c71d42e61d` — Browser C harness no longer depends on Playwright POST-body visibility; it proves effective end-to-end session identity from browser sessionStorage to backend response and UI trace, while retaining X-Session-Id as additional evidence when exposed.

## Absolute rules
- REAL AS21/MCP-SWTR is Oracle B.
- Browser C must be actual Playwright Chromium against mounted recovery/WorkspaceApp.
- No manual verification, API-only substitute or code-review substitute.
- Production/backend/frontend/test source edits are forbidden.
- Concurrency=1.
- Backend/source timeout 300s; retry proven transient source failures at most twice with 30s backoff and preserve failed attempts.
- Exact task-key-set parity is mandatory.
- Do NOT require Playwright `postData()`/`postDataJSON()`; Assignment 153-154 proved that body inspection is unavailable in this runtime. Absence of request-body observability is not itself a product failure.
- No caveat GREEN.

## Phase 0 — provenance/build
1. Pull branch; record HEAD/clean state.
2. Prove both commits above are ancestors.
3. Run frontend build.
4. Verify Task API REAL AS21, Agent backend v3=true, frontend and Playwright Chromium.
5. `/api/v1/health` must show source healthy, qwen-llm, v3=true.

## Phase 1 — machine session isolation proof
Run:
`npm run e2e:h0 -- --grep "session isolation"`

PASS requires:
- sessionStorage ID starts `ui-`;
- visible UI session label converges to the same ID;
- New dialogue changes the ID;
- second real Chromium page gets a distinct ID;
- first page keeps its own ID;
- browser sessionStorage immediately before send == backend response session_id;
- if X-Session-Id is exposed by Playwright, it must equal the same ID;
- first request after New dialogue is not correction_recheck/correction_clarification.

This proves effective propagation because the backend response session is derived from request session identity; do not reintroduce unavailable request-body inspection.

## Phase 2 — full Browser C pilot suite
Run:
`npm run e2e:h0`

All five tests must PASS in real Chromium: session isolation plus the four pilots:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`

Per pilot require:
- actual rendered Workspace UI submission;
- COMPLETED;
- visible Agent Core v3/current stage;
- browser sessionStorage == backend response session_id == rendered trace session_id;
- X-Session-Id equality when Playwright exposes the header;
- `_agent_core_v3` exists and `llm_used=true` for natural-language cases;
- trace/session details render;
- no unexpected clarification/correction state;
- WMB evidence has no wrong-space task;
- DMS-380 exact key renders.

If a locator waits for text that does not correspond to the actual returned payload, classify the exact locator/harness defect. Do not wait for an unrelated historical text string.

## Phase 3 — fresh exact Oracle B parity
Fresh-read REAL AS21 in this assignment for all four scenarios. Do not reuse previous counts as truth.
Persist exact task-key sets and timestamps.

Compare the Agent/browser response evidence to Oracle B exact sets:
- Garanin all approved spaces;
- Garanin DMS;
- Kalachanov WMB;
- DMS-380 point read.

A legitimate zero is PASS only if fresh Oracle B is exactly zero and Agent/browser returns the same authoritative zero without source-unavailable or clarification.

## Phase 4 — final H0 gate
Confirm Playwright HTML report, traces, screenshots and failure-video configuration.
Write:
`po-agent-platform-v2/qa_reports/PLAYWRIGHT_H0_BROWSER_FINAL_CERT_155.md`

Allowed verdicts ONLY:
- `PLAYWRIGHT_BROWSER_HARNESS_GREEN_H0_CERTIFIED`
- `H0_SESSION_ISOLATION_RED`
- `H0_BROWSER_C_RED`
- `H0_AGENT_PARITY_RED`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires Phase 1 PASS + full Chromium suite PASS + fresh exact Oracle B parity. No manual placeholders and no caveat GREEN.

Commit/push QA report only and STOP.

## Start now
Execute Assignment 155 completely.