# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_151_PLAYWRIGHT_BROWSER_HARNESS`

## Mission
Certify the new Playwright-based real Browser C harness and then use it to close the H0 browser evidence gap automatically. QA only: do not modify production/backend/frontend source code.

Owner browser-harness commits to verify in ancestry:
- `67741f3042a6cca46e3f2ef1fd8551fef0035e37` — Playwright scripts/dependency declared.
- `16baf0d2e2acca933f1de96fca2329aa55541507` — Playwright Chromium configuration.
- `f8aadce49655f901f281b4fbb12857bb1cf7bd40` — real Workspace H0 browser tests.
- `7d7f131ded15d99677ba2c08bc249d889847e5c3` — Playwright artifacts ignored.

The purpose is to eliminate all future `Browser C manual user verification required` verdicts. Browser C must now be machine-executed through a real Chromium page.

## Absolute rules
- Production/backend/frontend source edits are forbidden.
- REAL AS21/MCP-SWTR remains Oracle B for business truth.
- Browser C must be Playwright Chromium interacting with the rendered `recovery/WorkspaceApp`.
- Direct API/curl/code review cannot substitute for Browser C.
- Concurrency=1.
- Backend/source timeout 300s; transient retries only when the test/instruction explicitly allows them.
- Preserve Playwright traces/screenshots/videos for failures.
- Do not silently skip a failed browser test.

## Phase 0 — provenance and install
1. Pull current branch; record HEAD/clean state.
2. Prove the four owner commits are ancestors.
3. In `po-agent-platform-v2/frontend` install declared dependencies WITHOUT mutating committed lock/source files:
   `npm install --package-lock=false`
4. Install Chromium:
   `npx playwright install chromium`
5. Run `npm run build` and record result.
6. Record `npx playwright --version` and Chromium availability.

If npm/browser installation is blocked by a proven network/policy restriction, report `BLOCKED_BY_PROVEN_ENVIRONMENT`; do not fake Browser C.

## Phase 1 — start real services
Start/verify the real stack from current HEAD:
- Task API live REAL AS21 route;
- Agent backend with task-api mode, production LLM settings and `PO_AGENT_AGENT_CORE_V3_ENABLED=true`;
- frontend on the configured Vite port (Playwright may reuse/start it).

Require `/api/v1/health` to show healthy source, qwen-llm and v3 enabled before browser tests.

## Phase 2 — Playwright smoke / session proof
Run:
`npm run e2e:h0 -- --grep "session isolation"`

Require Chromium to actually launch and interact with the UI. PASS must prove automatically:
- drawer opens;
- visible runtime contains Agent Core v3;
- visible UI session starts `ui-`;
- New dialogue changes session ID and resets chat;
- second real browser page gets a distinct sessionStorage session;
- first page retains its own session;
- first fresh request is not correction/recheck state.

Capture test stdout and artifact paths.

## Phase 3 — automated real Browser C pilots
Run full:
`npm run e2e:h0`

Require all Playwright tests PASS in real Chromium for:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`

For each test verify from Playwright/browser evidence:
- request originates from rendered Workspace UI;
- terminal status is COMPLETED;
- visible footer/runtime identifies Agent Core v3;
- response session equals visible browser session;
- `_agent_core_v3` metadata exists and `llm_used=true`;
- trace/session details render in UI;
- WMB case contains no wrong-space evidence;
- DMS-380 renders the exact key.

Do not call this full business A/B certification by itself. Reuse/fresh-read Oracle B evidence from Assignment 150 only where still demonstrably fresh; if source truth may have changed, re-read REAL AS21 before claiming exact parity in the final report.

## Phase 4 — failure-artifact proof
Intentionally run a harmless test-name filter that matches no tests OR otherwise demonstrate Playwright report/artifact configuration without modifying source. Confirm:
- HTML report path is configured;
- failure traces/screenshots/video would be retained according to config.
Do not intentionally damage production/runtime/source data.

## Phase 5 — H0 gate decision
If Phase 2-3 PASS in real Chromium and fresh Oracle B/business parity remains valid, update the existing H0 status in a NEW report, not by rewriting historical evidence:
`po-agent-platform-v2/qa_reports/PLAYWRIGHT_H0_BROWSER_CERT_151.md`

Allowed verdicts:
- `PLAYWRIGHT_BROWSER_HARNESS_GREEN_H0_CERTIFIED`
- `PLAYWRIGHT_BROWSER_HARNESS_RED`
- `H0_BROWSER_C_RED`
- `H0_AGENT_PARITY_RED`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires actual Chromium execution. Code review/manual-user-required evidence is forbidden as substitute.

## Repository hygiene
- Commit/push QA report only.
- Do NOT commit `node_modules`, `playwright-report`, `test-results`, generated browser binaries, package-lock changes, production code or frontend source changes.
- If `package-lock.json` was changed locally by npm despite the instruction, restore it before committing.

## Start now
Execute Assignment 151 completely and STOP.