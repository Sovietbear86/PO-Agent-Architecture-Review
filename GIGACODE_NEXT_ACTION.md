# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_191_V4_BROWSER_UI_REGATE`

## Role lock
GigaCode is **QA/adversarial tester only**.

Do NOT implement, refactor, fix, or improve production code, frontend code, tests, prompts, adapters, plugin code, config, or architecture docs. The owner has implemented the V4-BROWSER/UI cutover independently.

## Start state
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record `git rev-parse HEAD` as `START_HEAD`.
3. Worktree must be clean before testing. If it is not clean, STOP and report rather than deleting unknown changes.
4. Permanent rollback reference remains `0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`.
5. A190 plugin gate is already GREEN. Do not reopen plugin architecture unless Browser testing proves a regression.

## Mission
Independently certify the real Browser C path after the owner's V4 UI wiring.

The browser must use the public `/api/v1/query` entrypoint. When V4 is enabled/ready, the **server** selects the pluginized V4 runtime; the browser must never choose skills, capabilities, MCP routes, or source endpoints itself.

Prove simultaneously:
- Browser → public API → pluginized Agent Core V4 → governed capability → REAL AS21 → response → UI is real end-to-end;
- `UIContract` presentation metadata is propagated without controlling source execution;
- required UI states render safely;
- session isolation remains correct;
- A188/A190 backend behavior is not regressed.

## Files to inspect, not modify
- `po-agent-platform-v2/src/po_agent/api/v1/__init__.py`
- `po-agent-platform-v2/src/po_agent/harness/agent_core_v4_pluginized.py`
- `po-agent-platform-v2/src/po_agent/harness/v4_plugin_registry.py`
- `po-agent-platform-v2/src/po_agent/harness/v4_plugins/core.py`
- `po-agent-platform-v2/frontend/src/api/client.ts`
- `po-agent-platform-v2/frontend/src/recovery/WorkspaceApp.tsx`
- `po-agent-platform-v2/frontend/src/components/V4ResultPanel.tsx`
- `po-agent-platform-v2/frontend/e2e/h0-workspace.spec.ts`
- `po-agent-platform-v2/tests/test_v4_browser_api_contract.py`
- A188 and A190 QA reports

## Phase 0 — architecture/static audit
Verify:
- public `/query` selects V4 only when `agent_core_v4_enabled` and V4 runtime is ready;
- V4-disabled path still preserves the legacy Harness fallback;
- `/query-v4` remains available only as explicit QA/A-B endpoint;
- frontend calls only `/api/v1/query`; no MCP/SWTR/direct capability endpoint from browser;
- no new phrase/entity/person/task/sprint hardcode;
- no planner/model/completion/source/identity behavior change;
- UIContract remains presentation metadata only;
- plugin registry remains the source of UI metadata;
- `checkpoint/v4-poc-green-a188` remains untouched.

Architecture violation => bounded RED. Do not fix it.

## Phase 1 — backend/frontend build gates
Run at minimum:

```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_v4_browser_api_contract.py -v
python -m pytest tests/test_agent_core_v4_plugin_registry.py -v
python -m pytest tests/test_agent_core_v4_completion_contract.py -v
python -m pytest tests/ -k "v4" -v

cd frontend
npm ci
npm run build
```

Acceptance:
- new Browser API contract tests GREEN;
- plugin registry tests fully GREEN after owner test fixes;
- completion contract remains GREEN;
- V4-focused suite has no new failure;
- frontend TypeScript/build GREEN.

Do not change test code to make a failure disappear.

## Phase 2 — public API cutover proof
Start fresh Task API + PO Agent with V4 enabled. Use fresh REAL AS21 Oracle B.

For each selected factual scenario call **both**:
- `/api/v1/query` (Browser production entrypoint)
- `/api/v1/query-v4` (explicit V4 QA endpoint)

Required proof:
- both report `runtime=agent_core_v4`;
- normalized facts and exact key sets are identical;
- `_agent_core_v4.semantic_prepass_used=false`;
- successful contracted trajectories retain `completion=runtime_contract` where applicable;
- `ui` metadata matches the selected skill's registry `UIContract`;
- no browser-specific semantic transformation changes the result.

At minimum include:
- DMS-380 lookup→assignee→tasks;
- active sprints DMS;
- current-sprint task collection DMS;
- person collection;
- person+space+not_completed;
- one task lookup;
- one negative invented person/sprint.

## Phase 3 — real Browser C / Playwright
Run the real browser UI against the fresh backend (no mocked API as acceptance truth):

```bash
cd po-agent-platform-v2/frontend
npx playwright test e2e/h0-workspace.spec.ts
```

Also manually/adversarially inspect the drawer for the representative cases.

Mandatory Browser C checks:
- runtime visibly shows Agent Core v4;
- request goes to `/api/v1/query` and carries the tab session id;
- response `session_id` equals browser session id;
- new conversation creates a new isolated session;
- another browser tab has an independent session;
- factual answer rendered exactly from backend response;
- UIContract-backed result panel renders when contract exists;
- evidence/trace can be opened and corresponds to the same response;
- `NEEDS_CLARIFICATION` options remain clickable and stay in the same session;
- `FAILED`/source-unavailable is not rendered as a legitimate empty/success state;
- REAL empty collection is distinguishable from source failure;
- loading state is visible during execution;
- no hidden request to local `/tasks`, fake data, MCP/SWTR or another source is used to render the agent result.

## Phase 4 — retained regression sample
Re-run a bounded retained sample from A190 through direct V4 API after Browser C testing:
- 3x DMS-380 multistep exact Oracle parity;
- 2x person collection exact parity;
- 2x current-sprint tasks;
- 2x active-sprint list;
- B2 open-task classification;
- negative person/sprint.

This phase proves UI work did not mutate backend behavior.

## Phase 5 — classify findings
A UI defect is real if Browser C loses, changes, fabricates, hides, or misclassifies source-backed data/state even when backend A is correct.

A backend defect is real if `/query` and `/query-v4` differ in normalized facts or A no longer matches fresh Oracle B.

Source drift is not a defect if fresh Oracle B proves the new state.

Known unscoped Cyrillic identity mutation (`Задачи Семавина`) remains tracked separately; do not hardcode around it.

## Allowed output
Create/commit/push **only**:

`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_BROWSER_UI_REGATE_191.md`

Do not modify anything else.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_BROWSER_UI_GREEN`
- `AGENT_CORE_V4_BROWSER_UI_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires architecture/build/public-API/Browser-C/session/state/regression gates all to pass.

If GREEN, recommendation:
**Begin progressive migration of the 54 production skills through the V4 plugin surface, in bounded domain waves, while retaining Browser C and A188 regression gates.**

## STOP
After committing/pushing the QA report, stop. Do not start the 54-skill migration or modify production code.