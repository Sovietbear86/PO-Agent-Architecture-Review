# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_154_PLAYWRIGHT_H0_CERTIFICATION`

## Mission
Final machine-only H0 certification after fixing the Playwright request-body observation issue found in Assignment 153. QA only: do not modify production/backend/frontend/test source code.

Owner/test-harness commits to verify:
- `2cf89fcb3e60db9d274f510dcb467dc00684e1af` — production send() reads authoritative tab session from sessionStorage at send-time.
- `608c8066864fa744aa75467f28f44b3558b220b6` — browser session assertion model uses sessionStorage and network evidence.
- `63d40d8cf3ef98a9639e5147b19ec446ec53b686` — Playwright reads POST body via request.postData() + JSON.parse() instead of postDataJSON().

Assignment 153 proved Chromium/UI execution is real and the remaining RED was in test-harness request-body inspection. Do not reclassify harness failures as production failures without first proving the boundary.

## Absolute rules
- REAL AS21/MCP-SWTR is Oracle B.
- Browser C must be real Playwright Chromium against mounted `recovery/WorkspaceApp`.
- No manual verification, code review, curl or API-only substitute for Browser C.
- Production/backend/frontend/test edits are forbidden.
- Concurrency=1.
- Backend/source timeout 300s; transient source failures may be retried twice with 30s backoff, preserving every failed attempt.
- Exact key-set parity, not count-only parity.
- No caveat GREEN.

## Phase 0 — provenance/build
1. Pull branch, record HEAD and clean state.
2. Prove all three commits above are ancestors.
3. Run frontend build.
4. Verify REAL Task API, Agent backend v3=true, frontend and Playwright Chromium.
5. `/api/v1/health`: source healthy, qwen-llm, v3=true.

## Phase 1 — focused session/network identity proof
Run:
`npm run e2e:h0 -- --grep "session isolation"`

PASS requires the first fresh request after New dialogue to prove:
- sessionStorage ID starts `ui-`;
- visible UI label eventually equals sessionStorage;
- POST body session_id parsed from request.postData() equals sessionStorage;
- X-Session-Id header equals sessionStorage;
- backend response session_id equals sessionStorage;
- New dialogue changes the ID;
- second real browser page has a different ID;
- first page retains its own ID;
- no correction_recheck/correction_clarification leakage.

Any mismatch = `H0_SESSION_ISOLATION_RED` with raw request/response evidence.

## Phase 2 — full Browser C suite
Run:
`npm run e2e:h0`

All tests must PASS in real Chromium for:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`

Per case require:
- request originates from rendered Workspace UI;
- COMPLETED;
- Agent Core v3/current stage visible;
- sessionStorage = visible UI = POST body = X-Session-Id = backend response;
- `_agent_core_v3` exists and `llm_used=true` for natural-language pilots;
- trace/session details render;
- no unnecessary clarification/correction state;
- WMB result/evidence has no wrong-space task;
- DMS-380 exact key renders.

If a Playwright locator/timing assertion fails while network/backend is correct, classify it as a Browser C/harness/UI-observability failure with evidence; do not silently skip.

## Phase 3 — fresh Oracle B parity
Fresh-read REAL AS21 NOW for all four scenarios. Previous counts are historical only.
Persist exact task-key sets, timestamps and source route evidence.
Compare Agent/browser evidence to the same fresh Oracle B set.
A legitimate zero result is PASS only if fresh Oracle B is exactly zero and Agent C returns the same authoritative zero without source-unavailable/clarification.

## Phase 4 — artifacts and final decision
Confirm HTML report, traces, screenshots and failure videos are produced/retained as configured.
Write a NEW report:
`po-agent-platform-v2/qa_reports/PLAYWRIGHT_H0_BROWSER_CERT_154.md`

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
Execute Assignment 154 completely.