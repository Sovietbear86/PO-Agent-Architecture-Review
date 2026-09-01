# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_108_UI_TO_AS21_END_TO_END_FORENSIC`

## Role boundary
You are QA/forensic executor only. **Do not modify production code, frontend code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

Assignment 107B reported `FRONTEND_GATE_F_GREEN_READY_FOR_BROWSER_E2E`, but an immediate owner/manual run produced a counterexample: the frontend appeared not to load expected AS21-backed data, and the Agent did not return results for normal/typical task-search queries. Per project rules, a later source-backed counterexample reopens historical GREEN.

Therefore Gate F is **REOPENED** until the actual browser/UI -> Harness -> Task API -> REAL AS21 path is proven on representative business queries, not just route 200s and direct API smoke.

Assignment 106 remains the backend regression baseline, but its conclusions do not override a browser-layer counterexample.

## Goal
Localize the first failing boundary for the owner's manual symptom:

`browser UI request -> frontend request payload -> Vite proxy -> Harness /query -> semantic frame/skill resolution -> capability args -> Task API -> REAL AS21/SWTR -> response payload -> frontend rendering`

The assignment must determine whether the observed failure is:
- frontend request/wiring/rendering defect;
- stale/wrong runtime or wrong API target;
- session/context contamination;
- semantic/skill-resolution regression in the running Agent;
- Task API/AS21 source failure;
- transient AS21 availability issue;
- test-data/query issue;
- or QA methodology error in 107B.

Do not close GREEN merely because `/api/v1/query` returns HTTP 200.

## Phase 0 — fresh end-to-end provenance
1. Pull current branch; record exact remote HEAD and clean tracked worktree.
2. Fully stop and restart all test-chain processes from current HEAD:
   - MCP-SWTR / required AS21 bridge;
   - Task API;
   - PO Agent Harness;
   - Vite frontend.
3. Record PID/start time/port for each process.
4. Record actual frontend URL and exact Vite proxy target.
5. Confirm Harness is in REAL task-api/AS21 mode; fake/mock/frozen authoritative calls=0; AS21 writes=0.
6. Before UI testing, prove REAL AS21 health with independent Oracle reads.
7. AS21 transient failure rule is mandatory: timeout/502/503 -> up to 2 retries with 20–30s backoff; if still unstable, revalidate/restart the affected runtime and perform one focused retest before classifying environment failure.

## Phase 1 — independent REAL AS21 truth set
Build a fresh Oracle truth set for representative entities before asking the Agent.

Mandatory source controls:
- exact point-read for at least two existing tasks, including `DMS-271` if still present;
- exact sprint scope for `DMS-SPRNT-2`;
- cross-check sprint scopes for `DMS-SPRNT-1` and `OLP-SPRNT-5`;
- obtain at least one real member/login and at least one real status represented in DMS tasks from source data rather than assumptions.

Capture exact task-key sets/counts and member/status facts from the live source. Do not reuse expected answers from historical reports.

## Phase 2 — mandatory typical-query matrix
Execute each query through THREE paths in the same fresh runtime/session window:

A. **Browser/UI Agent** — submit from the actual Agent drawer/input and capture what is visibly rendered.
B. **Direct Harness** — send the exact same text to `POST /api/v1/query` with a fresh controlled session ID.
C. **Oracle B** — independently query/filter REAL Task API/AS21 without using the Harness answer as truth.

Mandatory queries:
1. `Покажи задачу DMS-271` (or another live exact key only if DMS-271 is proven absent).
2. `Покажи задачи в DMS-SPRNT-2`.
3. `Покажи задачи <REAL_MEMBER> в DMS-SPRNT-2` using a member actually present in the Oracle source set.
4. `Покажи задачи <REAL_MEMBER> в DMS со статусом <REAL_STATUS>` using source-proven member/status values.
5. `Покажи задачи в DMS со статусом <REAL_STATUS>`.
6. One paraphrase of query 3 or 4 in natural Russian.

If historical Garanin/Гаранин data is currently present, add the historical regression query for him. If he is not present in the live source, do not use his absence as a product failure; use the source-proven member for the mandatory verdict and record the historical case separately.

## Phase 3 — compare exact business facts
For each query capture:
- browser-visible text/status/result rows;
- browser network request body and response body;
- session_id and clarification_id if any;
- Direct Harness status, skill/version, semantic frame/slots, filters/capability arguments, warnings/evidence;
- Oracle exact expected task-key set or exact task record;
- exact equality/difference of task-key sets;
- elapsed time and retries.

Verdict per row:
- `UI_AGENT_ORACLE_PASS`
- `UI_RENDER_MISMATCH`
- `FRONTEND_REQUEST_MISMATCH`
- `HARNESS_ORACLE_MISMATCH`
- `EXPECTED_CLARIFICATION`
- `AUTHORITATIVE_EMPTY_SOURCE`
- `ENVIRONMENT_BLOCKED`

HTTP 200 or `COMPLETED` cannot override wrong business facts.

## Phase 4 — UI source-data pages forensic
The owner's symptom also concerns frontend data pages. Test actual browser pages, not route HTTP only:

### `/tasks`
- prove whether rows are loaded from current API;
- capture network call(s), response count and at least several source IDs;
- compare displayed IDs/count with API response;
- determine whether data are REAL AS21-backed, cached local-only, or empty.

### `/sprint`
Use `DMS-SPRNT-2` as primary and validate a displayed source-backed fact against Oracle B. If the screen does not allow sprint selection, trace what scope it actually uses.

### `/team`
Determine whether member/workload facts come from live backend/AS21 or static/local data. Compare at least one member with Oracle/source response.

### `/releases`
Do not fail the UI because DMS has no fix versions. Use a space/entity with real release data if available (OLP may be used if still source-valid), otherwise require a truthful empty/source-limited state.

For each page identify exact route -> API call -> response -> rendered state.

## Phase 5 — stale runtime / wrong-target checks
Explicitly rule out common causes of "frontend looks alive but has no AS21 data":
- frontend proxy pointing at wrong/stale Harness process;
- multiple Harness processes on different ports;
- Harness process started before latest branch changes;
- Task API pointing at fake/cache/local mode;
- stale browser session/localStorage causing semantic context contamination;
- frontend localStorage task data shadowing live task data;
- service worker/browser cache if applicable;
- a dev server on a different port than the one the owner opened.

Use a unique runtime marker/health evidence if available. Do not modify code to create one.

## Phase 6 — session isolation and correction state
Run the mandatory typical-query matrix twice:
- once with a brand-new browser session/localStorage session id;
- once after two unrelated queries in the same session.

If fresh session passes but reused session fails, trace conversation/context state and classify `SESSION_STATE_REGRESSION` with FIRST_FAILING_BOUNDARY.

Do not create or promote Learning Loop policies during this investigation. Record policy store before/after and require no new policy changes.

## Phase 7 — FIRST_FAILING_BOUNDARY
For every mismatch identify the earliest proven boundary among:
- FRONTEND_INPUT_STATE
- FRONTEND_REQUEST_BUILDING
- DEV_PROXY_ROUTING
- HARNESS_RUNTIME_TARGET
- SESSION_CONTEXT
- SEMANTIC_INTERPRETATION
- SKILL_RESOLUTION
- ENTITY_GROUNDING
- CAPABILITY_ARGUMENT_BUILDING
- TASK_API_ROUTING
- SOURCE_CONTRACT
- SOURCE_AVAILABILITY
- SOURCE_DATA
- RESPONSE_SERIALIZATION
- FRONTEND_RENDERING
- QA_METHODOLOGY

Do not jump directly to AS21/source unavailability unless independent Oracle B also fails after mandatory retest.

## Phase 8 — audit Assignment 107B methodology
Explain how 107B could be GREEN while the owner immediately observed broken typical behavior.

Verify for each 107B claimed UI workflow whether the evidence was:
- actual browser interaction;
- direct API substituted for UI;
- route HTTP response only;
- static code inspection;
- or actual visible source-backed result.

Any overstated evidence must be classified `QA_METHODOLOGY_DEFECT` and separated from product defects.

## Gate decision
Allowed final verdicts:
- `GATE_F_RECONFIRMED_WITH_OWNER_QUERIES`
- `PRODUCT_DEFECTS_PROVEN`
- `FRONTEND_DATA_WIRING_DEFECT_PROVEN`
- `SESSION_STATE_REGRESSION_PROVEN`
- `MIXED_PRODUCT_AND_QA_DEFECTS`
- `BLOCKED_BY_ENVIRONMENT`

`GATE_F_RECONFIRMED_WITH_OWNER_QUERIES` is allowed only if:
- independent REAL AS21 Oracle is healthy;
- every mandatory data-backed typical query has UI A = Harness = Oracle business facts (or genuine expected clarification);
- `/tasks`, `/sprint`, `/team`, and `/releases` render truthful live/empty/source-limited data according to their contracts;
- fresh and reused sessions do not introduce unexplained regressions;
- no fake/mock/frozen authoritative data;
- no AS21 writes;
- 107B methodology is audited and any previous overstatement is disclosed.

## QA artifact location
Write only under `po-agent-platform-v2/qa_reports/`.

Primary report:
`po-agent-platform-v2/qa_reports/UI_TO_AS21_END_TO_END_FORENSIC_108.md`

Supporting artifacts prefix:
`UI_TO_AS21_END_TO_END_FORENSIC_108_`

## Required final summary
Include:
- exact HEAD and process PIDs/ports;
- REAL AS21 preflight counts;
- typical-query A/UI vs Direct Harness vs Oracle table;
- exact task-key-set diffs for collection queries;
- per-page live data provenance matrix;
- fresh vs reused-session comparison;
- FIRST_FAILING_BOUNDARY for every mismatch;
- 107B QA methodology audit;
- Learning Loop before/after exact state;
- fake/mock/frozen=0 and AS21 writes=0;
- final verdict.

Commit/push only allowed QA/forensic artifacts, report final SHA, then STOP. Do not modify production/frontend code and do not start any later assignment.