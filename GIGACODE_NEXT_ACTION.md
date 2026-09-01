# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_107_FRONTEND_PO_WORKSPACE_DISCOVERY`

## Role boundary
You are QA/research executor only. **Do not modify production code, frontend code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

Assignment 106 is treated as the completed backend regression baseline pending owner audit of its QA artifacts and any non-owner production changes. Do not rerun the 54-skill marathon unless explicitly instructed.

The authoritative roadmap is `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`. After backend Gate E closure, the next planned phase is **Gate F — Frontend / PO Workspace acceptance**, followed later by full browser E2E Gate G.

This assignment is discovery and gap analysis only. The owner will decide and implement frontend changes after your evidence is reviewed.

## Goal
Recover the intended original PO Agent / PO Workspace frontend scope, compare it with the current frontend implementation screen-by-screen and workflow-by-workflow, and produce an evidence-backed implementation plan for the owner.

Do not beautify or redesign anything yet. First prove what exists, what is missing, what is stale, what is disconnected from the certified backend, and what must be implemented before browser E2E.

## Phase 0 — provenance and baseline integrity
1. Pull current branch and record exact remote HEAD.
2. Record clean tracked worktree before starting.
3. Confirm Assignment 106 remains the latest backend certification baseline; do not alter its conclusions.
4. Identify all frontend applications/packages in the repository, their start commands, ports, frameworks and entry points.
5. Identify the backend API endpoint(s) used by the frontend and verify the current runtime target is the certified Harness/API path rather than a legacy/fake endpoint.
6. Do not modify any code.

## Phase 1 — recover authoritative frontend requirements
Use repository evidence only: roadmap, historical frontend docs, README files, original UI implementation, screenshots/assets/specs, archived app code and integration documents.

Recover the expected user-facing areas at minimum:
- conversational PO workspace;
- clarification UX / resume after clarification;
- task search, task results and task detail;
- sprint / flow analytics;
- team workload, capacity and competency;
- release / product analytics;
- evidence / trace visibility;
- feedback / correction / learning controls;
- loading, empty, partial, source-unavailable and error states;
- AI-PDLC / lifecycle surfaces if present in the original scope.

For every recovered requirement record the exact repository source/path and whether it is authoritative, historical-only or ambiguous.

## Phase 2 — inventory the current frontend
Inspect the current frontend implementation read-only.

Produce a screen/component/workflow inventory including:
- routes/pages/views;
- major components;
- API clients and endpoints called;
- state/session handling;
- clarification handling;
- evidence rendering;
- feedback controls;
- error/empty/loading states;
- skill-specific or domain-specific views;
- any hardcoded/fake/demo data;
- legacy API calls or disconnected components.

Do not infer that a component is functional merely because a file exists. Trace actual route -> component -> API call -> response handling.

## Phase 3 — live frontend smoke, if runnable without changes
If the current frontend can be started from the repository without modifying source/configuration:
1. Start it using documented commands only.
2. Start/revalidate the certified backend in task-api/REAL AS21 mode if required.
3. Capture the actual accessible routes/screens.
4. Execute a small non-destructive smoke set through the UI where practical:
   - normal task query;
   - clarification case;
   - sprint query using `DMS-SPRNT-2`;
   - source unavailable/error rendering if safely reproducible without source mutation;
   - feedback UI presence only, unless submission is explicitly safe and part of existing test contract.
5. Do not use browser automation to mutate AS21 or any production source.

If the frontend cannot start without a code/config change, classify the exact startup/integration blocker and continue static discovery. Do not fix it.

## Phase 4 — screen-by-screen gap matrix
Create one row per required frontend area/workflow with these fields:
- Requirement / workflow
- Evidence source
- Current route/component
- Current API/backend dependency
- Status: `PRESENT_AND_CONNECTED`, `PRESENT_BUT_DISCONNECTED`, `PARTIAL`, `MISSING`, `LEGACY_ONLY`, `BLOCKED_BY_STARTUP`
- Functional evidence
- UX/state gaps
- Owner change required
- E2E criticality: `BLOCKER`, `HIGH`, `MEDIUM`, `LOW`

A visually present screen is not `PRESENT_AND_CONNECTED` unless the current certified backend path is proven.

## Phase 5 — backend/frontend contract reconciliation
Using the current certified backend contract, compare frontend assumptions with actual API response shapes.

At minimum verify:
- query request/response contract;
- session_id handling;
- clarification question/options/clarification_id semantics;
- skill/intent fields used by UI;
- data payload rendering assumptions;
- evidence objects;
- warnings and source capability unavailable states;
- trace/correlation IDs;
- feedback endpoint contract;
- learning-related controls/status where exposed.

List every mismatch as `FRONTEND_BACKEND_CONTRACT_GAP` with exact first failing boundary.

Do not propose backend changes merely to preserve stale frontend assumptions when frontend can be aligned to the certified backend contract.

## Phase 6 — preserve backend certification and source rules
Do not reclassify a frontend gap as a backend defect without independent evidence.

If AS21/SWTR is temporarily unavailable during live smoke:
- follow mandatory retry/retest rules from `po-agent-platform-v2/docs/testing/POST_CHANGE_AB_ORACLE_CERTIFICATION.md`;
- do not change frontend/backend code;
- use `DMS-SPRNT-2` as primary sprint smoke, with `DMS-SPRNT-1` and `OLP-SPRNT-5` only where a cross-sprint check is relevant.

Known source-data limitations must be rendered correctly by the frontend rather than disguised as generic success or generic failure.

## Phase 7 — owner implementation plan
Produce the smallest ordered frontend implementation plan for the owner.

Separate work into:
- **P0 — E2E blockers:** frontend cannot run, wrong API base/path, broken request/response contract, clarification unusable, certified backend unreachable from UI;
- **P1 — core PO Workspace acceptance:** task/sprint/team/release views, evidence, source states, feedback controls;
- **P2 — UX completeness:** loading/empty/partial/error polish, traceability, session UX, navigation consistency;
- **P3 — optional/legacy reconciliation:** historical surfaces not required for current acceptance.

For each owner change identify exact files/components likely affected and the acceptance test that should follow it.

Do not implement any of these changes yourself.

## Phase 8 — Gate F readiness decision
Choose exactly one final classification:
- `FRONTEND_READY_FOR_BROWSER_E2E_AS_IS`
- `FRONTEND_OWNER_CHANGES_REQUIRED`
- `FRONTEND_MAJOR_SCOPE_GAP`
- `FRONTEND_BLOCKED_BY_STARTUP_OR_ENVIRONMENT`

`FRONTEND_READY_FOR_BROWSER_E2E_AS_IS` is allowed only if all Gate F required areas are present, connected to the certified backend and smoke evidence shows no blocker/high gap.

## QA artifact location
All artifacts must be written under:
`po-agent-platform-v2/qa_reports/`

Do **not** create root-level `qa_reports/` artifacts. Assignment 106 path drift is not to be repeated.

Primary report:
`po-agent-platform-v2/qa_reports/FRONTEND_PO_WORKSPACE_DISCOVERY_107.md`

Optional supporting artifacts must use prefix:
`FRONTEND_PO_WORKSPACE_DISCOVERY_107_`

## Required final report summary
Include:
- exact HEAD;
- frontend package(s) and startup state;
- recovered requirement count;
- current screen/workflow count;
- gap counts by status and criticality;
- all frontend/backend contract mismatches;
- live smoke results, if runnable;
- P0/P1/P2/P3 owner plan;
- final Gate F classification;
- confirmation: production/frontend code changes = 0, AS21 writes = 0.

Commit/push only allowed QA/research artifacts, report final SHA, then STOP. Do not start Assignment 108 or browser E2E on your own.