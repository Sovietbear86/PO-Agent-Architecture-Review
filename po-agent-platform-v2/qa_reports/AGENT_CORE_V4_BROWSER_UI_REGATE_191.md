# A191 — V4 Browser/UI Independent Re-Gate

**QA Role:** Adversarial tester (QA-only)
**Branch:** `feat/core8-real-query-hardening-v2`
**START_HEAD:** `300b8a42ee11e75e272061d364ffcd5d9eb5286e`
**Rollback reference:** `0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188` (commit verified present and untouched)
**Date:** 2026-09-16

---

## Verdict

**`AGENT_CORE_V4_BROWSER_UI_GREEN`**

---

## Phase 0 — Architecture / Static Audit

Owner commits since A190 (`f157515` → `300b8a4`): `a26430f` (V4 routing in public query), `1b13f06` (typed browser metadata), `8838c8c` (V4ResultPanel), `407ab7b` (assistant view wiring), `c41beca` (browser API contract tests), `e0141cc` (Workspace cutover), `0180a59` (e2e rebase on V4), `2dce77d` (spec), `08adced` (chore), `bfb0dc2` (fail-closed on runtime init errors), `300b8a4` (docs).

| Invariant | Status | Evidence |
|-----------|--------|----------|
| Public `/query` selects V4 only when `agent_core_v4_enabled` and V4 runtime ready | PASS | `use_v4 = settings.agent_core_v4_enabled and bundle.v4_runtime is not None` in `query_agent` |
| V4-disabled path preserves legacy Harness fallback | PASS | else-branch uses `get_runtime().process`, tags `runtime=legacy_harness`; covered by `test_public_query_preserves_legacy_path_when_v4_disabled` |
| `/query-v4` remains explicit QA/A-B endpoint | PASS | unchanged semantics (503 when V4 not enabled/ready), documented as A/B/rollback QA |
| Frontend calls only `/api/v1/query`; no MCP/SWTR/direct capability endpoint | PASS | `agent.query` posts to `/query` only; `tasks` CRUD client is a separate non-agent feature area, not used by agent result rendering; runtime `page.on('request')` audit in QA e2e confirmed only `POST /api/v1/query` + `GET /api/v1/health` for agent traffic |
| No new phrase/entity/person/task/sprint hardcode in production | PASS | added literals appear only in the e2e test file (DMS-380, invented "Абракадабров" negative) — test fixtures, not production code |
| No planner/model/completion/source/identity behavior change | PASS | zero diff on `agent_core_v4*.py`, plugins, adapters (only `api/v1/__init__.py` in backend diff) |
| UIContract remains presentation metadata only | PASS | `_decorate_v4_response` reads `runtime.ui_contract(skill_id)` and attaches `ui`; never passes UI data into the planner/handlers |
| Plugin registry is source of UI metadata | PASS | `ui_contract()` delegates to `self._ui_contracts` built from `registry.ui_contracts()` |
| Checkpoint `0f03fca` untouched | PASS | `git cat-file -t 0f03fca` = commit; not in A191 diff base |

No architecture violations.

## Phase 1 — Build Gates

| Suite | Result |
|-------|--------|
| `test_v4_browser_api_contract.py` | 2/2 PASS |
| `test_agent_core_v4_plugin_registry.py` | 11/11 PASS (owner fixed the 2 A190 test-logic bugs in `66cf68a`) |
| `test_agent_core_v4_completion_contract.py` | 20/20 PASS |
| `pytest tests/ -k "v4"` | 82/82 PASS |
| Frontend `npm run build` (tsc + vite) | GREEN (97 modules, built in 614ms) |

Note: `npm ci` fails with a pre-existing lockfile desync (`package.json` declares `@playwright/test@1.63.0` absent from `package-lock.json`; last touched in pre-A191 commit `67741f3`, A191 did not modify either file). `node_modules` was already installed; tsc, vite build and Playwright 1.62.1 all run fine. Not an A191 defect; flagged as a bounded hygiene item for the owner.

## Phase 2 — Public API Cutover Proof (47/47)

Fresh task-api + PO Agent (V4 enabled) on fresh ports, fresh REAL AS21 oracle (Semavin.M.M 309, Zhdanov.A.Ni 11).

For each scenario, **both** `/api/v1/query` and `/api/v1/query-v4` were called with independent sessions:

| Scenario | /query vs /query-v4 |
|----------|---------------------|
| DMS-380 lookup→assignee→tasks | identical, exact 309/309 key parity vs oracle, `completion=runtime_contract` |
| Active sprints DMS | identical, COMPLETED |
| Current-sprint task collection DMS | identical, COMPLETED |
| Person collection (Zhdanov) | identical, exact 11/11 key parity vs oracle |
| Person+space+not_completed | identical, COMPLETED |
| One task lookup | identical, COMPLETED, `ui={task, task_detail}` |
| Invented person | both `NEEDS_CLARIFICATION`, fail-closed |
| Invented sprint | both `NEEDS_CLARIFICATION`, fail-closed |

All checks: `runtime=agent_core_v4` on both endpoints; `semantic_prepass_used=false` everywhere; normalized facts (status, steps, counts, keys, completion, skill, ui, plugin_ids) byte-identical between the two endpoints; `ui` metadata matches the registry `UIContract` for the selected skill; `plugin_ids=["builtin.core.a188"]` propagated. No browser-specific semantic transformation (same endpoint, same request schema for both).

## Phase 3 — Real Browser C / Playwright

Environment: real backend (V4, REAL AS21) behind vite dev server; Chromium 151.

**Owner e2e `h0-workspace.spec.ts`: 5/5 PASS (5.2 min)**
- session isolation: new conversation mints new `ui-*` session; second tab has independent session; request `X-Session-Id` header == browser sessionStorage session; response `session_id` == browser session;
- 3 V4 pilots (DMS-380 multistep, active sprints DMS, current-sprint tasks DMS): `runtime=agent_core_v4`, `semantic_prepass_used=false`, `COMPLETED`, UIContract panel rendered, evidence drawer shows `trace_id`/`session_id`/`runtime: Agent Core v4 · completion=…`;
- fail-closed negative: invented person → `NEEDS_CLARIFICATION`, `runtime=agent_core_v4`, 0 evidence.

**QA adversarial e2e (`qa191-adversarial.spec.ts`, QA-only file, not committed): 2/2 PASS**
- Clarification flow: "Спринт OLP за август" → `NEEDS_CLARIFICATION` with clickable `.option-row` options; clicking "OLP-SPRNT-5" stays in the same session and completes;
- Network audit over the whole flow: only `POST /api/v1/query` (×6) and `GET /api/v1/health` — no local `/tasks`, no MCP/SWTR, no fake data route used for agent rendering;
- Loading state: `data-testid="agent-loading"` appears during execution and disappears on completion.

**UI states (from `V4ResultPanel` + observed behavior):**
- `SUCCESS_WITH_DATA`: structured panel renders rows from backend `tasks/sprints/task` (capped at 50 rows with explicit overflow counter);
- `REAL_EMPTY` vs `SOURCE_UNAVAILABLE`/`ERROR`: derived from backend `status`/`warnings` (`source_unavailable` → SOURCE_UNAVAILABLE; FAILED otherwise → ERROR); FAILED is never rendered as success/empty — confirmed by negative cases (status surfaced, no fake rows);
- `NEEDS_CLARIFICATION`: options remain clickable in the same session (proven live);
- Presentation metadata (`ui.result_kind`, `preferred_widget`) displayed in panel header and evidence drawer — display-only, never fed back into the request.

## Phase 4 — Retained Regression Sample (13/13)

Direct V4 API after all Browser C testing, fresh oracle (live source drift: Semavin 310, Zhdanov 10):

| Case | Result |
|------|--------|
| 3x DMS-380 multistep | 3/3 exact 310/310 parity, `runtime_contract`, prepass=false |
| 2x person collection (Zhdanov) | 2/2 exact 10/10 parity |
| 2x current-sprint tasks DMS | 2/2 (52 tasks, stable) |
| 2x active-sprint list DMS | 2/2 COMPLETED |
| 2x B2 open classification (Kalachanov STS) | 2/2 count=405 of 2694 — **identical to A190's agent B2 value**, proving UI work did not touch status classification |
| Negative person / sprint | 2/2 `NEEDS_CLARIFICATION`, fail-closed, 0 keys |

No backend mutation from the UI cutover.

## Phase 5 — Findings Classification

- **No real UI defect.** Browser C neither lost, changed, fabricated, hid nor misclassified source-backed data/state; rendering is a strict function of the `/api/v1/query` response.
- **No backend defect.** `/query` and `/query-v4` normalized facts are identical in all 8 Phase-2 scenarios; direct API matches fresh Oracle B exactly in Phase 4.
- **Source drift is not a defect:** Semavin 306→309→310 and Zhdanov 12→11→10 across A188/A190/A191 are all confirmed against fresh Oracle B; agent always held live truth.
- **Known tracked item (not a defect):** unscoped Cyrillic identity mutation ("Задачи Семавина") — unchanged, not hardcoded around.
- **Bounded owner hygiene items (non-blocking):**
  1. `package.json`/`package-lock.json` desync for `@playwright/test` (pre-dates A191) breaks `npm ci` reproducibility;
  2. `vite.config.ts` proxies `/api` to hardcoded `localhost:8004` (not configurable via env) — QA had to place the agent on 8004 for Browser C; consider `process.env`-driven target.

## Recommendation

**Begin progressive migration of the 54 production skills through the V4 plugin surface, in bounded domain waves, while retaining Browser C and A188/A190 regression gates.** Keep `checkpoint/v4-poc-green-a188` permanently as the rollback reference.
