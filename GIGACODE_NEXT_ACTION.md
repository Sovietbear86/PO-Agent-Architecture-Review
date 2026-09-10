# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_175_H1B_GROUNDED_CLARIFICATION_RECONCILIATION`

## Mission
Certify the final H1B routing-fidelity fix exposed by Assignment 174.

Assignment 174 already certifies and MUST NOT be broadly repeated:
- full-collection cap fix is GREEN (large collections are no longer truncated at 50);
- `Задачи Гаранина` identity/grounding path is GREEN;
- typed 2-step loop is GREEN with exact Oracle parity;
- Browser C multi-step is GREEN;
- e2e:h0 was 5/5;
- remaining RED is compound task queries such as `Открытые задачи Андрея Моисеева в DMS` and `Открытые задачи Семавина в DMS` returning NEEDS_CLARIFICATION while equivalent Garanin/Kalachanov queries complete.

Owner fix under test:
- `9fc3b4f57ad462c44c21379b52e224431d283c25` — reconcile stale semantic clarification needs only after deterministic/source-backed grounding has proven all material requested constraints.
- `ba534718941395cb4bc76adab9b67c3f997b5492` — regression tests for safe clarification reconciliation.

The fix MUST NOT make semantic ambiguity unsafe. It may suppress an earlier generic LLM clarification only when the exact person/space/status constraints visible to the grounding layer are now authoritatively grounded. Specific unresolved sprint/release/person/product/status needs must remain fail-closed.

QA ONLY. Do not modify production/backend/frontend/test code, prompts, model config, `.env`, registry contracts, or runtime learning data.

## Absolute rules
- Pull first: `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
- Verify both owner commits are ancestors of HEAD.
- Oracle B = fresh direct REAL AS21/MCP-SWTR only. Never `/api/v1/tasks`, local DB, sync, fake/frozen/cached surrogate, or historical counts.
- Keep Qwen 3.8/current provider unchanged.
- Concurrency=1.
- Source timeout 300s; E2E QA timeout may be 600s.
- Exact task-key-set equality is mandatory for factual collection cases.
- No production code changes. If a new defect is found, identify FIRST FAILING BOUNDARY and STOP for owner fix.
- Commit/push only the final QA report.

## Phase 0 — Provenance / fresh runtime
1. Pull branch, print HEAD/status/current assignment.
2. Verify `9fc3b4f...` and `ba534718...` are ancestors.
3. Restart/reuse REAL MCP-SWTR + Task API + PO Agent v3 + frontend so owner code is loaded.
4. `/health`: v3=true, semantic LLM healthy, REAL source healthy, frontend reachable.
5. Static proof:
   - generic semantic clarification reconciliation exists in `ProductionEntityResolverV2`;
   - it suppresses only needs made obsolete by grounded values;
   - explicit requested space/status/person must be grounded before a generic filter clarification can disappear;
   - specific unresolved needs remain preserved;
   - no surname/login hardcoding or capability routing was added.

## Phase 1 — Unit/safety gate
Run the focused grounding recovery/reconciliation tests plus the previously accepted H1B grounding/literal safety tests.
Require all PASS.

At minimum prove:
- generic `filters` clarification + grounded Moiseev + DMS + open status => clarification removed;
- same clarification + missing grounded DMS => clarification preserved;
- specific unresolved sprint clarification => preserved;
- ambiguous/nonexistent person => fail closed;
- existing successful LLM person grounding is not overridden.

## Phase 2 — Fresh Oracle B
Resolve and fetch fresh exact Oracle key sets for:
- `Moiseev.A.N` in DMS, open/not-completed subset;
- `Moiseev.A.N` in OLP, open/not-completed subset;
- `Semavin.M.M` in DMS, open/not-completed subset;
- `Garanin.R.V` in DMS, open/not-completed subset;
- `Kalachanov.V.V` in WMB, open/not-completed subset.

Record canonical identity, canonical space, status semantics, counts and exact keys.

## Phase 3 — Compound-query routing fidelity gate
Fresh runtime session for every run. Execute 5x each:
1. `Открытые задачи Андрея Моисеева в DMS`
2. `Открытые задачи Андрея Моисеева в OLP`
3. `Открытые задачи Семавина в DMS`
4. `Открытые задачи Гаранина в DMS`
5. `Открытые задачи Калачанова в WMB`

For every run capture:
- `llm_used`;
- raw semantic intent/slots/clarifications;
- grounded values after reconciliation;
- remaining clarification list;
- selected path/skill;
- canonical assignee/space/status;
- actual downstream source query;
- status/latency;
- returned keys/count;
- exact Oracle parity.

Acceptance:
- every supported source-backed query must COMPLETE with exact Oracle parity;
- Moiseev/Semavin must not fail solely because the semantic LLM emitted a stale generic filter clarification;
- if LLM emits useful raw slots, they may be used; if deterministic grounding proves the same constraints, a stale generic clarification must not suppress execution;
- any unresolved specific constraint remains clarification/fail-closed.

Required result: 25/25 supported runs terminally correct. Any name-dependent NEEDS_CLARIFICATION with all canonical constraints proven => RED.

## Phase 4 — ambiguity/fail-closed controls
Fresh sessions:
- nonexistent team member in DMS;
- deliberately ambiguous person surname if the configured roster has one; otherwise create a non-production unit-only ambiguity using existing tests, do NOT invent source truth;
- unsupported/unknown space token;
- task query containing an explicit unresolved sprint/release constraint.

Require no generic reconciliation to erase a genuinely unresolved constraint.
No fabricated tasks, IDs, people or spaces.

## Phase 5 — OLAP/OLP control
Run:
- `Открытые задачи Андрея Моисеева в OLP`
- `Открытые задачи Андрея Моисеева в OLAP`

`OLAP` behavior may remain explicit clarification/fail-closed at H1B. It must not silently execute against arbitrary space. Record whether deterministic alias exists but is not yet integrated into the semantic path; this is H1C debt unless fabricated data is returned.

## Phase 6 — protected H1B regression
Do NOT rerun full long catalog. Run only protected regression:
- `Задачи Гаранина`
- `Задачи Калачанова`
- `Покажи DMS-380`
- 3x `Проверь DMS-380 и затем покажи задачи его исполнителя`

Use fresh Oracle B and require exact parity for factual results. Multi-step must remain typed two-step and full-collection safe.

## Phase 7 — Browser C
1. Run existing `npm run e2e:h0`; require 5/5.
2. Real Playwright Chromium, fresh conversation per case:
   - `Открытые задачи Андрея Моисеева в DMS`
   - `Открытые задачи Семавина в DMS`
   - `Открытые задачи Гаранина в DMS`
   - `Проверь DMS-380 и затем покажи задачи его исполнителя`
3. Persist screenshot, UI session id, correlated backend trace, selected path, grounded constraints, counts and exact Oracle keys.
4. Browser C == Agent A == Oracle B.

## Phase 8 — H1B closure decision
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_GROUNDED_CLARIFICATION_175.md`

Allowed verdicts only:
- `AGENT_CORE_V3_H1B_LOOP_GREEN`
- `H1B_CLARIFICATION_RECONCILIATION_RED`
- `H1B_ROUTE_FIDELITY_RED`
- `H1B_AGENT_ORACLE_PARITY_RED`
- `H1B_SAFETY_REGRESSION_RED`
- `H1B_BROWSER_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires Phases 0-7 all pass. If GREEN explicitly state:
- H1B task lookup/search Hermes loop is CLOSED/certified;
- source completeness, identity grounding, compound query grounding and Browser C parity are certified;
- remaining selector/progressive disclosure debt moves to H1C/H3 Progressive Skill Loading;
- next stage is H1C/H3 progressive capability/skill selection, not further H1B surname-specific patching.

Commit/push only the final QA report and STOP.

## Start now
Execute Assignment 175 completely. Do not modify production code.