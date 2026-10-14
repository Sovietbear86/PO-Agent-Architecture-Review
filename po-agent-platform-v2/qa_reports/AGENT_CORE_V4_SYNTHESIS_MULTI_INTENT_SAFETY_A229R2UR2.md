# A229R2UR2 — Regex Hotfix Safety Re-Gate (Agent Core v4)

**Verdict:** `AGENT_CORE_V4_SYNTHESIS_MULTI_INTENT_SAFETY_GREEN_A229R2UR2`
**TESTED_HEAD:** `33090e02226723fbced4f63c7a6f3c356aa12ce8`
**Previous RED:** `AGENT_CORE_V4_SYNTHESIS_MULTI_INTENT_SAFETY_RED_A229R2UR` (commit `7db0227`,
boundary P0: dead `и`/`and` regex branches)
**Owner hotfix under test:** `53e6c72 fix(v4): correct regex escaping in synthesis-only multi-intent guard`
+ `33090e0` (A229R2UR2 assignment)
**Flag:** `PO_AGENT_V4_SYNTHESIS_ELISION` remains **OFF** by default — **not** flipped, per spec.
**Multi-intent execution gap:** **OPEN** (separate section below).
**Role:** QA / tester only — 0 production/test/config files modified by QA.
**Date:** 2026-10-14

---

## P0 — strict boundary and focused tests (GREEN)

| Check | Result |
|---|---|
| TESTED_HEAD / worktree | `33090e0`, tracked worktree clean |
| Core 6/6 byte-identical to checkpoint `6fb335d` | ✅ empty diff (agent_core_v4, robust, reliable, completion, v4_plugin_registry, llm/real) |
| Hotfix delta vs RED state (`7db0227` tree) | exactly **1 line**: `r"(?i)(?:\\s+и\\s+\|\\s+and\\s+\|[,;])"` → `r"(?i)(?:\s+и\s+\|\s+and\s+\|[,;])"` in `v4_synthesis_elision.py`; 0 other production/test changes |
| `test_v4_synthesis_elision.py` | **12/12 passed** — including the 2 previously failing coordinated-query cases |
| Regex semantics (live import) | 11/11: Russian `и` ✅, English `and`/`AND` ✅, comma ✅, semicolon ✅, single-intent ru/lookup/hierarchy ❌(correct), word-boundary safety (`иерархия`, `DMSband`) ✅, empty ✅ |
| Full V4 blast (`test_agent_core_v4*` + `test_v4*`) | 270/270 |
| Task API SWTR suites | 34/34 |
| Frontend build (tsc + vite) | exit 0 |

---

## P1 — precise previous live failure reproduced (GREEN — hotfix certified)

REAL AS21, fresh sessions, flag ON and OFF, 3 valid runs each. Oracles (fresh, 14:54 MSK):
Kalachanov WMB = 6 (WMB-30482/30000/29995/29890/29830/29242); Semavin DMS = 173 (3 open, 1 open
bug DMS-431 created 25.09); DMS-267 = Resolved / Semavin.M.M / Minor / DMS-SPRNT-3; DMS-267 links =
1 (DMS-253 → DMS-267 decomposition; full chain CRPV-90180 → DMS-253 → DMS-267, epic DMS-349).

| Case | flag ON (3 runs) | flag OFF (3 runs) |
|---|---|---|
| M1 "Задачи Калачанова в WMB **и** задачи Семавина в DMS" | 3/3 delegated (0 elided), 1 terminal `task.search_assignee`; answer: Kalachanov 6 keys **exact vs oracle** + "**Задачи Семавина в DMS:** данные по этому запросу отсутствуют" | 3/3 identical honest LLM behavior |
| M3 "Задачи Калачанова в WMB **и** иерархию DMS-267" | 3/3 delegated, 1 terminal; Kalachanov 6 keys exact + "**Иерархия DMS-267:** … в доступных наблюдениях информация о DMS-267 отсутствует. Если нужно, могу запросить иерархию отдельно." | 3/3 identical |
| M4 "Покажи задачу DMS-267, её иерархию **и** задачи Калачанова в WMB" | 3/3 delegated, 1 terminal `task.lookup`; DMS-267 table **exact vs oracle** + Kalachanov goal honestly flagged ("информация отсутствует. Для получения этого списка необходим отдельный запрос") | 3/3 identical |

- **No run emitted an unqualified one-goal answer** (deterministic elision pattern 0/15 ON); the
  previous A229R2UR boundary (M1/M3 silent drop) is **closed** — flag ON now behaves
  indistinguishably from flag OFF on these queries (same query-aware LLM synthesizer).
- Unexecuted goals (Semavin DMS in M1, hierarchy in M3, hierarchy+Kalachanov in M4) are
  **prose-acknowledged but NOT executed** → reported **OPEN** per spec (acknowledgment ≠ completion).
- **F1 (non-blocking, both flag states, pre-existing A229R2U-M2 class):** in M4 the LLM
  *infers* "Иерархия: задача не имеет родителя" from the null parent/epic fields of the lookup
  observation, while oracle F proves DMS-267 has parent DMS-253. This is an LLM-inference
  limitation of the lookup-only trajectory (identical in OFF — same synthesizer), not an elision or
  hotfix defect; it belongs to the OPEN multi-intent execution gap (planner should call
  `task.hierarchy` for that goal).

---

## P2 — feature ON retains optimization safely (GREEN)

Flag ON vs OFF, 3 valid runs each: A (person+space), C (lookup), F (hierarchy), Z (zero-result
created-period), H (incomplete-period clarification).

### −1 synthesis LLM call (per-run log attribution)

| Case | turns | OFF LLM (runs) | ON LLM (runs) | ON elided |
|---|---|---|---|---|
| A | 2 | 3,3,3 | 2, **3**¹, 2 | 3/3 |
| C | 2 | 3,3,3 | 2,2,2 | 3/3 |
| F | 2 | 3,3,3 | 2,2,2 | 3/3 |
| Z | 3 | 4, 8², 4 | 3,3,3 | 3/3 |

¹ ON A#2 = turns + **provider 429 retry** (log: `HTTP/1.1 429 Too Many Requests` 15:27:39 →
backoff → 200 15:28:21 → capability completed; **no synthesis POST after completion** — elision
held). Explicitly-allowed provider artifact per spec.
² OFF Z#2 had a longer trajectory (space.resolve + member.resolve) + intra-turn repairs.

**Result: exactly one synthesis call removed on all 12/12 eligible COMPLETED runs** (ON LLM = turn
count; OFF LLM = turn count + 1). H (NEEDS_CLARIFICATION) has no synthesis in either state —
elision never runs on non-COMPLETED.

### Facts / UX / taxonomy

- **Key lists intact** (F1 fix retained): A ON = "Для «Калачанов» найдено задач: 6. Ключи:
  WMB-30482, WMB-30000, WMB-29890, WMB-29995, WMB-29830, WMB-29242" (exact vs oracle).
- **Zero remains zero:** Z 3/3 elided "…: 0" (cosmetic `not_completed` token in text — pre-existing
  A229R2U U2 note).
- **Clarification + continuation:** H 3/3 typed NEEDS_CLARIFICATION (free-text period question,
  `clarification_id` issued, 0 elision); continuation "с 30.09.2026 по сегодня" → COMPLETED
  `task.type_analysis`, "0 дефектов в периоде" — **exact vs oracle** (open_bug_in_window=0; the
  one open bug DMS-431 was created 25.09, outside window). (LLM side-note "2 открытые задачи" vs
  oracle open_total=3 = benign live drift, non-blocking.)
- **Provider error taxonomy:** the 429 above self-healed via bounded backoff; trajectory completed
  with `runtime_contract`, no fabricated deterministic prose.
- **Elision hit-rate / false positives:** eligible single-intent COMPLETED 12/12 elided (100%);
  coordination-bearing queries 15/15 delegated (P1) — conservative by design; **0 false-positive
  delegations** on the 15 single-intent H/A/C/F/Z runs (no coordination signals present).
- **Wall (eligible A/C/F/Z):** p50 35.03s → 27.19s, p90 101.84s → 59.88s (Z most improved
  102.64→35.2 p50; A walls inflated in-session by the 429 window + LLM latency variance).

### Browser UI (flag ON, real Web UI) — 5/5 PASS

Task collection renders the deterministic answer **with the full key list + cards**; lookup drawer
readable (no raw internals); hierarchy readable; type-analysis readable; overview mount retained.
Audit: 0 4xx/5xx on `/api/v1/query`, 0 direct frontend source calls (no portal/8241/3000), 0
console errors.

### Audit (fresh A229R2UR2 logs)

| Check | flag OFF log | flag ON |
|---|---|---|
| Local legacy store reads | 0 | 0 |
| Mutations | 0 | 0 |
| Unscoped full-tenant scans | 0 | 0 |

(ON per-run source attribution captured pre-log-rotation for P2-ON: all reads carry
`space=`/`assignee=`/explicit task code; browser ON log audited clean in full.)

---

## Multi-intent execution gap (separate — **OPEN**)

The hotfix is a **presentation safeguard only** and did not (must not) fix multi-intent execution:

- **Where the planner omits a goal:** on M1/M3/M4 the planner converges to a single terminal
  (first goal only); no capability is loaded/called for the second goal; the completion contract
  is satisfied by the single terminal (`runtime_contract`), so nothing downstream detects the
  missing goal. First failing boundary: **planner turn-level goal decomposition** (pre-existing,
  A229R2U/A229R2 lineage).
- **Oracle per goal** (table in P1): executed goals exact; unexecuted goals now honestly
  acknowledged (M1 Semavin DMS, M3/M4 hierarchy; M4 hierarchy additionally carries the LLM
  wrong-inference F1 above — oracle says DMS-253 is the parent).
- **Recommended design (no Core changes):** typed **goal-coverage clarification** at the
  deterministic completion frontier — if the user query declares N coordinated goals and K<N have
  terminal observations, reject premature READY and emit NEEDS_CLARIFICATION ("Выполнить все
  части: 1) …; 2) … — продолжить со второй частью?") or schedule remaining goals as follow-up
  turns. Pattern precedent: A229F3R constraint-coverage postcondition guard at the API seam.
  Safe to clarify: the clarification-continuation machinery (session + clarification_id) is
  proven (this gate's H flow).
- **Can it safely clarify?** Yes — proven in this gate (H free-text continuation completed
  exactly). No phrase routing or multi-agent introduced here.

---

## Verdict

`AGENT_CORE_V4_SYNTHESIS_MULTI_INTENT_SAFETY_GREEN_A229R2UR2` — P0/P1/P2 all green:

1. Hotfix boundary exact (1 line, regex escaping only), Core frozen 6/6, all tests green (12/12
   elision, 270/270 V4, 34/34 task-api, build 0).
2. The exact previous live failure (M1/M3 silent one-goal elision) is **closed**: 9/9 delegated
   with honest gap-flags, indistinguishable from flag OFF.
3. Optimization retained: exactly −1 synthesis LLM call on 12/12 eligible COMPLETED runs, key
   lists/zero-results/clarification/taxonomy intact, browser accepted, audit clean.
4. **Multi-intent execution limitation remains OPEN** (planner single-terminal convergence;
   design above).

**Flag recommendation:** the hotfix is safe and the elision path is verified; however, per spec
the default **stays OFF** (no checkpoint, no default flip before an explicit owner decision).
When the owner enables it, the conservative guard retains LLM synthesis for all
coordination/enumeration queries at the cost of one extra call on those queries only.
