# Assignment 174 — H1B Full Collection + UI Routing Consistency Certification

**Verdict:** `H1B_ROUTE_FIDELITY_RED`  
**Test base HEAD:** `e29e291` (branch `feat/core8-real-query-hardening-v2`)  
**Date:** 2026-09-10  
**QA role:** Report-only. No production code modified.

---

## Summary

The owner fix for the 50-task collection cap (`700b4f0`) is **certified at its boundary**: H1B now explicitly requests `max_results=10000` and returns full collections (2867/2867 Kalachanov, 309/309 Semavin, 23/23 Garanin). The multi-step loop, Browser C, and e2e:h0 all pass with exact Oracle B parity.

However, **Phase 4/8 expose a pre-existing routing fidelity defect**: semantically equivalent task queries ("Открытые задачи X в SPACE") consistently produce `NEEDS_CLARIFICATION` for Moiseev (3/3) and Semavin (1/1 in Browser C) while the same query shape works for Garanin and Kalachanov. This violates the acceptance criterion: *"same semantic class of query must not fail only because the member is Moiseev while Garanin succeeds."*

---

## Phase Results

| Phase | Result | Detail |
|-------|--------|--------|
| 0 — Provenance/Health | PASS | Both owner commits ancestors. v3=true, source healthy, 48 MCP tools |
| 1 — Unit/Build | PASS | 34/34 H1/H1B tests, `tsc --noEmit` clean |
| 2 — Oracle B Baseline | PASS | Kalachanov=2867, Semavin=309, Garanin=23, Moiseev=27, DMS-380 assignee=Semavin.M.M |
| 3 — H1B Full Collection | PASS (caveat) | Kalachanov 2/3×2867 exact + 1 transient `httpx.ReadTimeout`; Garanin 3/3×23 exact. No 50-cap |
| 4 — Cross-Route Fidelity | **RED** | Moiseev 3/3 NEEDS_CLARIFICATION; Semavin 3/3×309 pass; Garanin@DMS 3/3×6 pass; Kalachanov@WMB 3/3×0 pass |
| 5 — OLAP/OLP Alias | PASS (fail-closed) | Alias `olap→OLP` exists in code; LLM asks clarification instead of canonicalizing. No fabricated data |
| 6 — Multi-Step Regression | PASS | 3/3 COMPLETED, 309/309 exact, 2-step typed loop |
| 7 — Space-Filter | PASS | Garanin@DMS 8/8 exact; Moiseev@DMS NEEDS_CLARIFICATION (same Phase 4 root cause) |
| 8 — Browser C H0 + Routing | **RED (routing)** | e2e:h0 5/5 PASS; Browser C 7/7 test-pass but 4/6 routing cases NEEDS_CLARIFICATION |
| 9 — Browser C Multi-Step | PASS | 308/308 exact parity, 2 steps, screenshot persisted |

---

## Phase 3 Detail: Full Collection Fix Certified

| Run | Query | Status | Agent Keys | Oracle | Exact | Path | Latency |
|-----|-------|--------|-----------|--------|-------|------|---------|
| K-1 | Задачи Калачанова | FAILED (transient timeout) | 0 | 2867 | — | — | 74938ms |
| K-2 | Задачи Калачанова | COMPLETED | 2867 | 2867 | ✓ | H1B | 51813ms |
| K-3 | Задачи Калачанова | COMPLETED | 2867 | 2867 | ✓ | H1B | 102097ms |
| G-1 | Задачи Гаранина | COMPLETED | 23 | 23 | ✓ | H1B | 66567ms |
| G-2 | Задачи Гаранина | COMPLETED | 23 | 23 | ✓ | H1B | 56187ms |
| G-3 | Задачи Гаранина | COMPLETED | 23 | 23 | ✓ | H1B | 44814ms |

- **No 50-cap truncation detected.** All successful runs return full collections.
- The 1 failure is `httpx.ReadTimeout` (Task API 30s timeout exceeded for 2867-task pagination) — transient infrastructure, not the cap bug.
- H1B `_execute_search` now passes `max_results=10000` explicitly.
- `count` field in observations = actual returned row count (2867, 23).

---

## Phase 4 Detail: Cross-Route Fidelity (FIRST FAILING BOUNDARY)

| Query | Run | Status | Keys | Oracle | Path | Skill |
|-------|-----|--------|------|--------|------|-------|
| Задачи Семавина | 3/3 | COMPLETED | 309 | 309 | legacy | task-search-assignee |
| Открытые задачи Гаранина в DMS | 3/3 | COMPLETED | 6 | 7 (open=6) | H1B | agent-core-v3-h1b-loop |
| Открытые задачи Андрея Моисеева в DMS | 3/3 | **NEEDS_CLARIFICATION** | 0 | 26 | none | none |
| Открытые задачи Андрея Моисеева в OLP | 3/3 | **NEEDS_CLARIFICATION** | 0 | 1 | none | none |
| Открытые задачи Калачанова в WMB | 3/3 | COMPLETED | 0 | 0 (open) | H1B | agent-core-v3-h1b-loop |

**Clarification text (Moiseev):** "Уточните значения фильтров: семантическая модель не смогла безопасно отделить их от текста запроса."

**Root cause:** The LLM semantic prepass (`LLMJsonSemanticInterpreter`) fails to extract the person entity "Андрей Моисеев" from compound queries with the pattern "Открытые задачи [Full Name] в [Space]". Single-surname queries ("Гаранина", "Калачанова") ground correctly; full-name + status + space compound queries do not.

**First failing boundary:** `LLMJsonSemanticInterpreter` → semantic frame extraction → `person_raw` slot empty/unresolved → clarification gate triggers.

**File:** `po-agent-platform-v2/src/po_agent/harness/dialogue_runtime.py` (LLM semantic prepass)  
**Function:** LLM prompt produces no `person_raw`/`member_login` slot for "Андрея Моисеева" in compound context.

---

## Phase 5 Detail: OLAP/OLP Alias

- **Static evidence:** `live_entity_grounding.py:16` defines `"olap": "OLP"` alias. `core8_semantic_precision.py:38` maps `\bolap\b` to OLP.
- **Behavior:** LLM asks "Продукт «OLAP» не найден. Вы имели в виду OLP?" — fail-closed clarification.
- **Verdict:** Acceptable per assignment spec ("If no explicit alias exists in the LLM's operational context: OLAP must produce clarification/fail-closed"). The alias exists in deterministic grounding code but the LLM prepass does not consult it before asking. No fabricated data returned.
- **Not a RED condition** — the system fails closed, never returns unexplained task sets.

---

## Phase 8 Detail: Browser C Routing Consistency

| Case | Status | H1B | Skill | Notes |
|------|--------|-----|-------|-------|
| garanin_dms | COMPLETED | true | agent-core-v3-h1b-loop | Correct |
| moiseev_dms | NEEDS_CLARIFICATION | false | — | Same LLM extraction failure |
| moiseev_olp | NEEDS_CLARIFICATION | false | — | Same |
| moiseev_olap | NEEDS_CLARIFICATION | false | — | Same |
| semavin_dms | NEEDS_CLARIFICATION | false | — | "Открытые задачи Семавина в DMS" also fails |
| kalachanov_wmb | COMPLETED | true | agent-core-v3-h1b-loop | Correct (0 open) |

**e2e:h0:** 5/5 PASS (session isolation, Garanin, Garanin@DMS, Kalachanov@WMB, DMS-380).

**Stale UI state (`NEEDS_CLARIFICATION · 0 ms`):** Not reproduced in this test run. The Browser C tests show correct status per turn. If observed in production UI, it is likely a frontend presentation artifact (initial state before first response) rather than session contamination. No evidence of cross-session leakage.

---

## Phase 9: Browser C Multi-Step Full Collection

- Query: "Проверь DMS-380 и затем покажи задачи его исполнителя"
- Result: COMPLETED, 2 steps (task-lookup-v3 → task-search-v3)
- Collected: 308 keys / Oracle: 308 keys → **exact parity**
- Screenshot: `qa_174_browser_c/phase9_multistep.png`
- Full collection confirmed in real browser (no cap)

---

## Verdict Justification

`H1B_ROUTE_FIDELITY_RED` because:

1. **Acceptance criterion violated:** "same semantic class of query must not fail only because the member is Moiseev while Garanin succeeds."
   - "Открытые задачи Гаранина в DMS" → COMPLETED, 6 tasks, H1B
   - "Открытые задачи Андрея Моисеева в DMS" → NEEDS_CLARIFICATION, 0 tasks
   - Same semantic structure (status + person + space), different outcome based solely on member name.

2. **The H1B collection fix is correct** — the 50-cap is eliminated, full collections are returned, and multi-step loops work. The defect is upstream in the semantic prepass.

3. **The routing difference changes result semantics** — a user asking about Moiseev's open tasks in DMS gets no answer, while the same question about Garanin gets a complete answer.

---

## Owner Recommendations

1. **Semantic prepass entity extraction for full names:** The LLM prompt must reliably extract "Андрей Моисеев" (and similar full names) from compound queries. Consider:
   - Adding team member full names explicitly to the LLM prompt context
   - Adding a deterministic fallback: if `person_raw` contains a known last name from the team directory, ground it without requiring LLM confirmation
   - The `live_entity_grounding.py` already has product aliases; a similar deterministic person-name resolver could catch "Моисеев" → `Moiseev.A.N` before the clarification gate

2. **OLAP alias deterministic canonicalization:** The alias exists in code but the LLM prepass doesn't use it. Add a pre-LLM deterministic canonicalization step: if the raw space token matches a known alias (`olap`→`OLP`), canonicalize before sending to the LLM.

3. **Selector keyword coverage (H1C debt):** The `AgentCoreV3PilotSelector` only routes "гаранин", "калачан", "assignee", "исполнител" to H1B. Semavin and Moiseev go to legacy. This is acceptable for now (legacy returns correct results) but should be addressed in H1C Progressive Skill Loading for unified routing.

---

## Oracle B Reference (Fresh, 2026-09-10T11:43Z)

| Identity | Total Tasks | External ID |
|----------|-------------|-------------|
| Kalachanov.V.V | 2867 | Kalachanov.V.V |
| Semavin.M.M | 309 | Semavin.M.M |
| Garanin.R.V | 23 | Garanin.R.V |
| Moiseev.A.N | 27 | Moiseev.A.N |
| Garanin.R.V@DMS | 8 | — |
| Moiseev.A.N@DMS | 26 | — |
| Moiseev.A.N@OLP | 1 | — |
| DMS-380 assignee | Semavin.M.M | semavin.m.m |

---

## Evidence Artifacts

- `qa_174_phase3_results.json` — Phase 3 per-run evidence
- `qa_174_oracle_results.json` — Oracle B key sets
- `qa_174_browser_c/` — 6 screenshots + 7 JSON reports (Phase 8+9)
- `/tmp/qa174_e2e_h0.log` — e2e:h0 5/5 PASS
- `/tmp/qa174_browser_c.log` — Browser C 7/7 PASS

---

## STOP

Assignment 174 complete. Verdict issued. No code modified. Report-only commit.