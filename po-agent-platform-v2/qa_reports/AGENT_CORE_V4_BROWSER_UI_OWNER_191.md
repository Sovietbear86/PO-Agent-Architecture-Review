# Agent Core V4 — Browser/UI owner implementation (pre-QA 191)

**Date:** 2026-09-16  
**Owner implementation:** complete; independent QA pending  
**Rollback:** `0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`

## Scope

This change wires the real Workspace browser path to the already-GREEN pluginized V4 runtime without changing planner, completion, source, identity, capability handlers, or plugin discovery semantics.

## Server cutover

The public `/api/v1/query` endpoint now selects the pluginized V4 runtime only when V4 is explicitly enabled and ready. Otherwise it preserves the legacy Harness path.

The browser does not select skills/capabilities/source routes. `/api/v1/query-v4` remains only as an explicit QA/A-B endpoint.

V4 responses expose:
- `runtime=agent_core_v4`;
- registry-derived `UIContract` metadata (`ui`);
- plugin ids for observability;
- existing `_agent_core_v4` trajectory/source metadata unchanged.

Health exposes `browser_runtime`, V4 readiness and plugin ids.

## Frontend wiring

The active UI path is `recovery/WorkspaceApp.tsx` (not the unused legacy `views/AssistantView.tsx`). It now:
- renders Agent Core v4 runtime state;
- keeps tab/session isolation through the existing `po-agent-runtime-session-id` contract;
- sends all user requests only to public `/api/v1/query` through the typed API client;
- renders V4 `UIContract` metadata and structured source-backed data through `V4ResultPanel`;
- preserves evidence/trace disclosure and clarification options;
- distinguishes success/real-empty/source-unavailable/error presentation states without changing business facts.

## Regression safety

No edits were made to:
- `agent_core_v4.py`;
- `agent_core_v4_reliable.py`;
- `agent_core_v4_robust.py`;
- `agent_core_v4_completion.py`;
- V4 source/identity handlers;
- planner/model strategy.

The explicit V4 QA endpoint remains for direct comparison with the public Browser path.

## Tests added/updated

- `tests/test_v4_browser_api_contract.py`: public API V4 cutover + legacy fallback contract.
- `frontend/e2e/h0-workspace.spec.ts`: Browser C re-based on V4, including session isolation, public `/query`, representative V4 scenarios, UIContract panel, evidence/trace and negative fail-closed state.
- existing plugin/completion tests remain mandatory in Assignment 191.

## Acceptance status

**NOT YET GREEN.** Owner implementation is committed, but no claim is made about local pytest/npm/Playwright/REAL-AS21 results from this environment.

Independent GigaCode Assignment 191 is authoritative for the V4-BROWSER gate.
