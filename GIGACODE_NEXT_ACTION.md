# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_107B_FRONTEND_LIVE_SMOKE_AND_GATE_F_RECERTIFICATION`

## Role boundary
You are QA/research executor only. **Do not modify production code, frontend code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

Assignment 107 static discovery is useful but its final Gate F classification is not accepted yet because live smoke was not performed and the report contains an internal contradiction: it correctly shows the Vite dev server on port 5174 proxying `/api` to Harness on port 8004, but later describes that same configuration as a proxy mismatch/startup blocker. Starting the frontend with the documented `npm run dev` command does not itself require a source/configuration change.

Assignment 106 remains the backend baseline. Do not rerun the full 54-skill marathon.

## Goal
Run the current frontend **as-is**, with no code/config changes, and produce real end-to-end smoke evidence through the current PO Workspace against the certified Harness on REAL AS21 where applicable. Resolve the contradictory conclusions from Assignment 107 and make the Gate F readiness decision from live evidence rather than file presence.

## Phase 0 — provenance and clean runtime
1. Pull current branch and record exact remote HEAD and clean tracked worktree.
2. Confirm no production/frontend code changes since Assignment 107 except QA artifacts.
3. Revalidate/start:
   - Task API on its documented port;
   - PO Agent Harness on port 8004 in REAL task-api/AS21 mode;
   - frontend from `po-agent-platform-v2/frontend` using the documented command only: `npm run dev`.
4. Do not edit `vite.config`, environment files, package scripts or source.
5. Record frontend URL/port actually printed by Vite and verify `/api` proxy reaches `http://localhost:8004`.
6. If startup fails, capture the exact error and FIRST_FAILING_BOUNDARY. Do not infer a blocker from static config alone.

## Phase 1 — browser/manual live shell proof
Open the running frontend and prove the actual routed shell loads.

Capture evidence for:
- `/`;
- `/tasks`;
- `/sprint`;
- `/team`;
- `/releases`;
- `/quality`.

For each route record:
- HTTP/page load success;
- visible page title/major widgets;
- whether the route renders the expected component rather than blank/error/legacy UI;
- console/network errors if any.

If browser automation is unavailable, use the strongest available live method (browser/manual evidence, dev-server/network logs, route HTTP responses) and state the limitation. Do not claim visual proof from static code.

## Phase 2 — core conversational workflow smoke
Through the actual UI, not direct API only:
1. Submit one natural Russian task query for a REAL existing task.
2. Verify loading state is visible.
3. Verify answer renders.
4. Verify evidence/trace affordance renders and exposes trace/skill/source evidence.
5. Verify session persists across at least two consecutive queries in the same UI session.

Use direct API only as Oracle/supporting evidence, not as a substitute for the UI action.

## Phase 3 — clarification/resume UX
Choose a query that genuinely requires clarification under the current backend contract.

Prove through the UI:
- clarification question/options render;
- selecting an option/resuming sends the correct follow-up semantics;
- the flow completes without losing session/context;
- no duplicate or contradictory assistant state is shown.

If backend returns no clarification for the chosen query, use another realistic ambiguous query; do not fabricate clarification state.

## Phase 4 — sprint live smoke on approved REAL surface
Use sprint skills/screens with the approved live targets:
1. `DMS-SPRNT-2` primary;
2. `DMS-SPRNT-1` cross-check if needed;
3. `OLP-SPRNT-5` independent cross-check if needed.

Through the UI prove at least one sprint workflow reaches REAL backend facts. Compare key normalized facts with an independent direct AS21/Task API Oracle where practical.

AS21 transient failure rule applies: timeout/502/503 -> up to 2 retries with 20–30 s backoff and focused revalidation/retest before environment classification.

## Phase 5 — source limitation/error rendering
Without mutating AS21 and without inventing failures, exercise at least one currently known typed source limitation if naturally reachable, for example a capability that requires unavailable historical sprint/release timeline facts.

Prove the frontend does **not** display a fabricated metric or generic success. Record exactly how warnings/source-unavailable state is rendered.

If no safe typed limitation can be reached through current UI, record `NOT_SAFELY_REPRODUCIBLE` rather than forcing an artificial failure.

## Phase 6 — feedback controls smoke
Verify the feedback UI on a real response:
- positive/negative controls are present;
- comment/correction UX appears where designed;
- request contract matches backend.

Do not submit a negative correction that would create/promote learning policy unless the current accepted test contract explicitly requires it. UI presence and safe request validation are enough for this Gate F smoke.

## Phase 7 — duplicate AssistantView and route reality
Resolve the P2 conclusion from Assignment 107 with live routing evidence.

Determine whether `views/AssistantView.tsx` is:
- unreachable dead code;
- reachable by any route/navigation path;
- capable of causing an actual user-visible duplicate chat experience.

If unreachable and harmless, classify as cleanup debt, not a Gate F owner change requirement. Do not delete it.

## Phase 8 — AI-PDLC scope classification
Re-read the authoritative roadmap/master spec and classify `/aidpdlc` exactly as:
- `CURRENT_GATE_F_REQUIRED`, or
- `OPTIONAL_LEGACY_FUTURE_SCOPE`.

Do not set `FRONTEND_OWNER_CHANGES_REQUIRED` merely because an optional historical route is absent.

## Phase 9 — contract/network audit from live run
From browser/network/dev-server evidence verify the actual live request/response path for at least:
- query;
- clarification/resume if exercised;
- one domain page data request;
- feedback endpoint contract/presence.

Check for:
- 404/405;
- CORS/proxy failures;
- stale legacy endpoints;
- response-shape rendering errors;
- JS exceptions.

Any true mismatch must identify FIRST_FAILING_BOUNDARY and exact route/component/request.

## Phase 10 — Gate F recertification
Choose exactly one verdict:
- `FRONTEND_GATE_F_GREEN_READY_FOR_BROWSER_E2E`
- `FRONTEND_OWNER_CHANGES_REQUIRED`
- `FRONTEND_MAJOR_SCOPE_GAP`
- `FRONTEND_BLOCKED_BY_STARTUP_OR_ENVIRONMENT`

`FRONTEND_GATE_F_GREEN_READY_FOR_BROWSER_E2E` requires:
- frontend starts as-is with documented command;
- required routes load;
- real conversational UI works against Harness;
- clarification/resume works where applicable;
- at least one REAL sprint workflow works;
- evidence/trace works;
- source limitations are not fabricated as success;
- no P0/P1 gaps;
- no live frontend/backend contract mismatch;
- optional/dead-code cleanup does not count as blocker;
- production/frontend code changes = 0;
- AS21 writes = 0.

## QA artifact location
Write only under:
`po-agent-platform-v2/qa_reports/`

Primary report:
`po-agent-platform-v2/qa_reports/FRONTEND_LIVE_SMOKE_GATE_F_107B.md`

Optional supporting artifacts prefix:
`FRONTEND_LIVE_SMOKE_GATE_F_107B_`

## Required final summary
Include:
- exact HEAD;
- frontend start command and actual URL;
- routes live-tested;
- UI workflows live-tested;
- REAL AS21-backed UI workflow evidence;
- clarification evidence;
- network/console error counts;
- P0/P1/P2/P3 gaps after live evidence;
- resolution of Assignment 107 proxy contradiction;
- duplicate AssistantView classification;
- AI-PDLC current-scope classification;
- final Gate F verdict;
- production/frontend code changes = 0;
- AS21 writes = 0.

Commit/push only allowed QA/research artifacts, report final SHA, then STOP. Do not start Gate G/Assignment 108 on your own.