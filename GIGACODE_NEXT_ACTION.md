# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_152_PLAYWRIGHT_H0_RETEST`

## Mission
Re-test the real Playwright Browser C harness after the owner fix for the session-id timing race found in Assignment 151. QA only: do not modify production/backend/frontend source code.

Owner fix to verify in ancestry:
- `2cf89fcb3e60db9d274f510dcb467dc00684e1af` — `send()` now reads the authoritative tab session from `sessionStorage` at send-time, removing dependence on asynchronous React state commit timing after `Новый диалог`.

Assignment 151 already proved that Playwright Chromium itself launches and interacts with the mounted Workspace. Do not replace browser execution with code review or API calls.

## Absolute rules
- Production/backend/frontend source edits are forbidden.
- REAL AS21/MCP-SWTR is Oracle B for business truth.
- Browser C = real Playwright Chromium interacting with rendered `recovery/WorkspaceApp`.
- Direct API/curl/code review cannot substitute for C.
- Concurrency=1.
- Backend/source timeout 300s.
- For transient source/transport failures retry the affected test at most twice with 30s backoff; do not hide failed attempts.
- Preserve traces/screenshots/videos on failures.
- No manual-user-verification verdict is allowed.

## Phase 0 — provenance/build
1. Pull current branch and record HEAD/clean state.
2. Prove owner commit `2cf89fcb...` is ancestor.
3. Confirm Assignment 151 report exists and prior RED root cause was session-id mismatch.
4. Install/use Playwright dependencies without committing generated files.
5. Run frontend build.
6. Start/verify Task API, Agent backend v3=true, and frontend. `/api/v1/health` must show healthy source, qwen-llm, v3=true.

## Phase 1 — focused session race regression
Run:
`npm run e2e:h0 -- --grep "session isolation"`

Require PASS and capture evidence that:
- browser-visible session starts `ui-`;
- New dialogue changes it;
- the next request response `session_id` EXACTLY equals the new visible/sessionStorage ID;
- second browser page has a different session;
- first page retains its own session;
- no first-turn correction/recheck leakage.

If response session differs from visible/sessionStorage session, STOP with `H0_SESSION_ISOLATION_RED` and raw trace evidence.

## Phase 2 — full real Browser C suite
Run:
`npm run e2e:h0`

All tests must PASS in real Chromium:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`

Require per case:
- request submitted through rendered Workspace UI;
- terminal status COMPLETED;
- runtime/footer identifies Agent Core v3/current v3 stage;
- response session == visible UI session == sessionStorage session;
- v3 metadata exists, `llm_used=true` for natural-language cases;
- trace/session details render;
- no unexpected clarification/correction state;
- WMB evidence contains no wrong-space task;
- DMS-380 renders exact key.

## Phase 3 — Oracle B parity confirmation
Fresh-read REAL AS21 for the four pilot truths used by the browser suite. Compare exact keys where applicable. Counts alone are insufficient.

Browser C rendered/evidence keys must correspond to the same Agent execution and match Oracle B for cases where task sets are rendered/exposed.

## Phase 4 — artifact/harness gate
Confirm Playwright HTML report, trace, screenshots and failure-video configuration still works. Do not deliberately corrupt application code or source data.

## Final report
Write a NEW report:
`po-agent-platform-v2/qa_reports/PLAYWRIGHT_H0_BROWSER_RETEST_152.md`

Allowed verdicts ONLY:
- `PLAYWRIGHT_BROWSER_HARNESS_GREEN_H0_CERTIFIED`
- `H0_SESSION_ISOLATION_RED`
- `H0_BROWSER_C_RED`
- `H0_AGENT_PARITY_RED`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires focused session regression PASS + full Playwright suite PASS + fresh Oracle parity. No manual verification placeholders.

Commit/push QA report only and STOP.

## Start now
Execute Assignment 152 completely.