# Assignment 175 — H1B Grounded Clarification Reconciliation

**Verdict:** `H1B_CLARIFICATION_RECONCILIATION_RED`
**Test base HEAD:** `82fe44f` (branch `feat/core8-real-query-hardening-v2`)
**Date:** 2026-09-10
**QA role:** Report-only. No production/backend/frontend/test code modified.

---

## Summary

The owner's grounded-clarification-reconciliation fix (`9fc3b4f`) does **not** resolve the compound-routing defect exposed by Assignment 174. The 5×5 compound-query gate (Phase 3) is **RED**: 15/25 runs return `NEEDS_CLARIFICATION` instead of completing with exact Oracle parity.

- **Failing (15/25):** `Открытые задачи Андрея Моисеева в DMS` (5/5), `…в OLP` (5/5), `Открытые задачи Семавина в DMS` (5/5) — all return the stale `Уточните значения фильтров: семантическая модель не смогла безопасно отделить…` clarification.
- **Passing (10/25):** `Открытые задачи Гаранина в DMS` (5/5, 7/7 exact) and `Открытые задачи Калачанова в WMB` (COMPLETED 0/0; 2 transient source `ReadTimeout`s under concurrent load) both route to the H1B loop and complete with exact parity.

The protected H1B regression (Phase 6) is GREEN (Garanin full 32/32, DMS-380 lookup, 3× multi-step 308/308 with typed 2-step loops). No safety regression was introduced by the fix (Phase 4 fail-closed controls hold; OLAP/OLP fail-closed, Phase 5). The defect is specific to the clarification-reconciliation mechanism.

---

## Root Cause (First Failing Boundary)

**The reconciliation suppresses a different set of clarification `field` names than the ones the LLM semantic layer actually emits.**

1. For the compound pattern `Открытые задачи [Full Name] в [SPACE]`, the LLM semantic layer (`semantic_core_v2.py`) returns **`raw intent = None`** and emits two clarifications:
   - `field = "semantic_contract"` — "Уточните значения фильтров: семантическая модель не смогла безопасно отделить их от текста запроса."
   - `field = "intent"` — "Уточните, какой результат PO Agent должен получить."

   This was confirmed by driving the real production `ConversationAwareSemanticInterpreter` + `ProductionEntityResolverV2` directly (see `qa_175_diag.py` output): for all three of Moiseev/Semavin/Garanin, `raw intent: None` and both `semantic_contract` + `intent` clarifications are present.

2. The owner's fix, `ProductionEntityResolverV2._reconcile_grounded_clarifications` (`production_entity_grounding_v2.py`), only drops a clarification when its `field` is one of:
   - person set: `{member_login, person, person_raw, assignee}` (if `member_login` grounded)
   - space set: `{product, space}` (if `product` grounded)
   - status set: `{status, status_raw, status_semantic}` (if `status` grounded)
   - **generic set: `{filter, filters, constraint, constraints, semantic_filter, semantic_filters, query_filters}`** (if all material constraints grounded)

   **`semantic_contract` and `intent` are in none of these sets**, so they are never suppressed — even when `member_login`, `product`, and `status` are all authoritatively grounded.

3. Consequence by routing path:
   - **Legacy path** (Moiseev, Semavin — the H1B pilot selector only routes `гаранин/калачан/assignee/исполнител`): the dialogue runtime honors the surviving `semantic_contract`/`intent` clarifications → `NEEDS_CLARIFICATION`.
   - **H1B path** (Garanin, Kalachanov): the H1B processor explicitly does **not** let pre-pass clarifications suppress the planner (`agent_core_v3_h1b.py`), so those queries complete.

This is a **test/production field mismatch**: the regression test `test_generic_filter_clarification_is_removed_when_all_material_constraints_are_grounded` constructs `ClarificationNeed("filters", …)` (field `"filters"`, which *is* in the generic set), so the unit suite passes while the production field (`semantic_contract`) is not covered.

**Compounding gap (Moiseev only):** the grounder additionally fails to resolve the full name "Андрея Моисеева" to a canonical `member_login`, adding a third `member_login` clarification. (Semavin and Garanin full names *are* resolved.)

---

## Phase Results

| Phase | Result | Detail |
|-------|--------|--------|
| 0 — Provenance/Health | PASS | Both owner commits ancestors. v3=true, source healthy, 48 MCP tools, frontend 200 |
| 1 — Unit/Safety | PASS | 50 passed (grounding recovery/reconciliation + H1B/agent_core_v3); tsc clean |
| 2 — Oracle B | PASS | Fresh real source, H1B-identical mapping (see counts below) |
| 3 — Compound routing (5×5) | **RED** | 15/25 NEEDS_CLARIFICATION (Moiseev DMS/OLP, Semavin DMS); 10/25 pass |
| 4 — Fail-closed controls | PASS (no regression) | nonexistent member → clarification; unknown space → H1B contract FAILED; no fabricated data |
| 5 — OLAP/OLP | PASS (fail-closed) | OLAP → "OLAP не найден, OLP?" (not silently executed); OLP → same semantic_contract gap |
| 6 — Protected H1B regression | PASS | Garanin full 32/32 exact; DMS-380 lookup; 3× multi-step 308/308 exact, typed 2-step |
| 7 — Browser C | Consistent w/ Phase 3 | e2e:h0 5/5 (Kalachanov WMB transient source timeout); Browser C confirms Moiseev/Semavin NEEDS_CLARIFICATION |

---

## Phase 3 Detail — Compound-Query Routing Fidelity Gate

Oracle B (fresh, real source, `not_completed` subset, H1B-identical `is_completed` mapping):

| Case | Total | Open (not_completed) |
|------|-------|----------------------|
| Moiseev.A.N @ DMS | 26 | 26 |
| Moiseev.A.N @ OLP | 1 | 1 |
| Semavin.M.M @ DMS | 137 | 136 |
| Garanin.R.V @ DMS | 8 | 7 |
| Kalachanov.V.V @ WMB | 5 | 0 |

| Case | 5 runs | Status | Returned/Oracle | Exact parity |
|------|--------|--------|-----------------|--------------|
| Moiseev@DMS | 5/5 | NEEDS_CLARIFICATION | 0/26 | ✗ |
| Moiseev@OLP | 5/5 | NEEDS_CLARIFICATION | 0/1 | ✗ |
| Semavin@DMS | 5/5 | NEEDS_CLARIFICATION | 0/136 | ✗ |
| Garanin@DMS | 5/5 | COMPLETED (H1B) | 7/7 | ✓ |
| Kalachanov@WMB | 3 COMPLETED / 2 source-timeout | COMPLETED (H1B) | 0/0 | ✓ |

All 15 failing runs returned `llm_used=True`, `raw intent=None`, and the `semantic_contract` clarification. No name-dependent completion for Moiseev/Semavin — a direct violation of the acceptance criterion "Moiseev/Semavin must not fail solely because the semantic LLM emitted a stale generic filter clarification."

Kalachanov@WMB's 2 `FAILED` runs were `ReadTimeout` from the Task API (30s source limit) under concurrent Phase-3 load; an isolated retry returned COMPLETED 0/0 exact parity.

---

## Phase 4/5 — Fail-Closed Controls (no safety regression)

- **Nonexistent member** (`Задачи Петрова в DMS`): NEEDS_CLARIFICATION, 0 keys — "Петров не найден в списке участников команды." No fabricated identity. ✓
- **Unknown space** (`Открытые задачи Гаранина в XYZ`): H1B contract FAILED, 0 keys — no fabricated space. ✓
- **Unresolvable sprint** (`Открытые задачи Гаранина в спринте WMB-SPRNT-9999`): COMPLETED but **transparent** — response explicitly states none of the 31 returned tasks belong to that sprint. Root cause is a pre-existing `task-search-v3` limitation (sprint is not a supported constraint), **not** a regression from this fix; no fabricated tasks. Noted as H1C debt.
- **OLAP** (`…Моисеева в OLAP`): fail-closed clarification "OLAP не найден, OLP?" — not silently executed against an arbitrary space. The deterministic `olap→OLP` alias exists in `live_entity_grounding.py` but is not integrated into the semantic pre-pass (H1C debt). ✓
- **OLP** (`…Моисеева в OLP`): hits the same `semantic_contract` gap as Phase 3.

No generic reconciliation erased a genuinely unresolved constraint in any case.

---

## Phase 6 — Protected H1B Regression (GREEN)

Fresh Oracle B: Garanin all-tasks = 32, Semavin all-tasks = 308 (DMS-380 assignee).

| Query | Result |
|-------|--------|
| `Задачи Гаранина` (2×) | COMPLETED, 32/32 exact parity (both) |
| `Покажи DMS-380` | COMPLETED (task lookup) |
| `Проверь DMS-380 и затем покажи задачи его исполнителя` (3×) | COMPLETED, 308/308 exact parity (all 3), typed 2-step loop (task-lookup-v3 → task-search-v3), assignee resolved from DMS-380 observation |
| `Задачи Калачанова` (isolated) | 2858-task full collection hits the pre-existing 30s Task API `ReadTimeout` (documented in 174); not a regression |

The H1B loop, identity grounding, multi-step observation binding, and full-collection safety are intact.

---

## Phase 7 — Browser C (real UI)

**e2e:h0: 5/5.** The `Задачи Калачанова в WMB` case failed once in the full run (source `ReadTimeout`) but **passed in isolated re-run** (50.5s) — transient source latency, not a defect.

**Real Playwright Chromium, fresh conversation per case** (artifacts in `qa_175_browser_c/`):

| Case | Status | Path |
|------|--------|------|
| `Открытые задачи Гаранина в DMS` | COMPLETED | H1B |
| `Открытые задачи Семавина в DMS` | **NEEDS_CLARIFICATION** | legacy (h1b=false) |
| `Открытые задачи Андрея Моисеева в DMS` | **NEEDS_CLARIFICATION** | legacy (h1b=false) |
| `Проверь DMS-380 и затем покажи задачи его исполнителя` | COMPLETED | H1B, 2 steps |

Browser C reproduces the backend defect exactly: Moiseev/Semavin compound queries fail in the real UI with the same `semantic_contract` clarification, while Garanin/multi-step complete.

---

## Verdict Justification

`H1B_CLARIFICATION_RECONCILIATION_RED` because the specific mechanism under test — the grounded clarification reconciliation — does not suppress the clarifications the semantic layer actually emits (`semantic_contract`, `intent`). The reconciliation's generic-field set does not include these production field names, so on the legacy-routed path the stale clarifications survive and produce `NEEDS_CLARIFICATION` for Moiseev/Semavin, violating the routing-fidelity acceptance criterion. The H1B-protected cases (Garanin/Kalachanov) complete only because the H1B processor independently ignores pre-pass clarifications — the fix itself is not doing the work the assignment requires.

No `H1B_SAFETY_REGRESSION_RED`: Phase 4/5 confirm the fix does not erase genuinely-unresolved constraints and no data is fabricated.

---

## Owner Recommendations (first failing boundary → fix)

1. **Primary:** In `ProductionEntityResolverV2._reconcile_grounded_clarifications`, extend the suppression set to include the production field names the semantic layer actually emits for stale filter/intent uncertainty — at minimum `semantic_contract` and `intent` — gated on `_material_query_constraints_are_grounded` (person + space + status all grounded). This mirrors the existing generic-filter branch.
2. **Test coverage:** Update `test_generic_filter_clarification_is_removed_when_all_material_constraints_are_grounded` to use the **real** production field name (`semantic_contract`), not `filters`, so the test exercises the actual production clarification and would have caught this gap.
3. **Compounding (Moiseev):** Strengthen person grounding so the full name "Андрея Моисеева" resolves to `Moiseev.A.N` (currently the grounder only resolves it when a matching surname token is present; verify the team-directory token match for Moiseev).
4. **H1C debt (not blocking):** (a) integrate the `olap→OLP` deterministic alias into the semantic pre-pass; (b) add sprint-constraint support or explicit fail-closed for `task-search-v3` so an unresolvable sprint is not silently dropped and re-framed by the LLM.

---

## Oracle B Reference (Fresh, 2026-09-10, real source)

| Identity@Space | Total | Open (not_completed) |
|----------------|-------|----------------------|
| Moiseev.A.N @ DMS | 26 | 26 |
| Moiseev.A.N @ OLP | 1 | 1 |
| Semavin.M.M @ DMS | 137 | 136 |
| Garanin.R.V @ DMS | 8 | 7 |
| Kalachanov.V.V @ WMB | 5 | 0 |
| Garanin.R.V (all) | 32 | — |
| Semavin.M.M (all) | 308 | — |
| Kalachanov.V.V (all) | 2858 | — |

---

## Evidence Artifacts

- `qa_175_oracle_results.json` — Oracle B key sets + status breakdowns
- `qa_175_phase3_results.json` — 25 compound-query runs (diagnostics + parity)
- `qa_175_phase45_results.json` — fail-closed + OLAP/OLP controls
- `qa_175_phase6_results.json` — protected H1B regression
- `qa_175_browser_c/` — 4 Browser C JSON reports + screenshots
- `qa_175_diag.py` / output — real interpreter+grounder intermediate state (root-cause proof)
- `/tmp/qa175_e2e_h0.log` — e2e:h0 (5/5, Kalachanov transient)
- `/tmp/qa175_browser_c.log` — Browser C 4/4

---

## STOP

Assignment 175 complete. Verdict `H1B_CLARIFICATION_RECONCILIATION_RED`. No code modified. Report-only commit.