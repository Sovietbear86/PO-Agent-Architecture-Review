# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_153_PLAYWRIGHT_H0_FINAL`

## Mission
Final machine-only H0 certification after fixing the Playwright assertion model. Assignment 152 proved the production session fix is correct and localized the remaining failure to the test reading stale React DOM state. The Browser C harness now reads authoritative sessionStorage identity and separately waits for UI observability to converge.

Owner/test-harness commit to verify:
- `608c8066864fa744aa75467f28f44b3558b220b6` — Playwright session assertions now use sessionStorage as authoritative browser identity, capture POST body + X-Session-Id, and require the visible UI session label to converge to the same value.
- Production owner fix `2cf89fcb3e60db9d274f510dcb467dc00684e1af` must also remain ancestor.

QA only. Do not modify production/backend/frontend/test source code.

## Absolute rules
- REAL AS21/MCP-SWTR is Oracle B.
- Browser C must be real Playwright Chromium against mounted `recovery/WorkspaceApp`.
- No manual verification, code review, curl, or API-only substitute.
- Concurrency=1.
- Backend/source timeout 300s. Retry transient source failures at most twice with 30s backoff.
- Every failed attempt is evidence; never skip or relabel timeout as PASS.
- Preserve Playwright traces/screenshots/videos on failure.

## Phase 0 — provenance/build
1. Pull branch and record HEAD/clean state.
2. Prove `2cf89fcb...` and `608c8066...` are ancestors.
3. Run frontend build.
4. Start/verify Task API REAL AS21, Agent backend v3=true, frontend.
5. `/api/v1/health` must show healthy source, qwen-llm, v3=true.

## Phase 1 — focused session isolation
Run:
`npm run e2e:h0 -- --grep "session isolation"`

PASS requires all four identities to agree for the first fresh request after New dialogue:
- browser sessionStorage ID;
- eventually rendered UI session label;
- POST body `session_id`;
- request `X-Session-Id` header;
- backend response `session_id`.

Also require:
- ID changes after New dialogue;
- second real browser page receives a distinct ID;
- first page retains its ID;
- no correction_recheck/correction_clarification on the first turn.

If any identity differs, verdict `H0_SESSION_ISOLATION_RED` with trace/network evidence.

## Phase 2 — full Browser C pilots
Run full:
`npm run e2e:h0`

All Playwright tests must PASS for:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`

Per case require:
- actual rendered Workspace request;
- COMPLETED;
- Agent Core v3/current stage visible;
- sessionStorage = UI label = POST body = X-Session-Id = response session;
- `_agent_core_v3` exists and `llm_used=true` for NL pilots;
- trace/session details render;
- no unnecessary clarification;
- WMB has no wrong-space evidence;
- DMS-380 exact key renders.

## Phase 3 — fresh Oracle B parity
Fresh-read REAL AS21 now, not Assignment 150 counts, for the same four scenarios. Compare exact task-key sets. Browser/Agent evidence must match Oracle B where applicable.

## Phase 4 — final H0 decision
Write:
`po-agent-platform-v2/qa_reports/PLAYWRIGHT_H0_BROWSER_FINAL_153.md`

Allowed verdicts ONLY:
- `PLAYWRIGHT_BROWSER_HARNESS_GREEN_H0_CERTIFIED`
- `H0_SESSION_ISOLATION_RED`
- `H0_BROWSER_C_RED`
- `H0_AGENT_PARITY_RED`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires Phase 1 PASS, full Playwright suite PASS, and fresh Oracle B parity. No caveat GREEN.

Commit/push QA report only and STOP.

## Start now
Execute Assignment 153 completely.