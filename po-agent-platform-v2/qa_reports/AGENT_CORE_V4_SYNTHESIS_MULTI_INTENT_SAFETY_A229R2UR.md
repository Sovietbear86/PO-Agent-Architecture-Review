# A229R2UR — Multi-Intent Synthesis Safety Re-Gate (Agent Core v4)

**Verdict:** `AGENT_CORE_V4_SYNTHESIS_MULTI_INTENT_SAFETY_RED_A229R2UR`
**First failing boundary:** P0 — owner's own new regression tests fail (2/3 parametrize cases of
`test_single_terminal_multi_intent_uses_query_aware_synthesizer`), root-caused to a double-escaped
regex that disables the "и"/"and" coordination branches; P1 live-confirmed: M1/M3 (the canonical
A229R2U RED cases) still elide to the unqualified one-goal answer.

**TESTED_HEAD:** `73b88a05e6914f9cf8b12e1ca2da3f5a39279a17`
**Previous verdict:** `AGENT_CORE_V4_SYNTHESIS_ELISION_UX_RED_A229R2U` (commit `17a2337`)
**Owner fix under test:** `0685faf fix(v4): delegate coordinated queries to query-aware synthesizer`
+ `ab8e37a test(v4): delegate single-terminal multi-intent to original synthesis`
**Role:** QA / tester only — production code NOT modified
**Date:** 2026-10-14

---

## Summary

The owner's coordination guard is **half-effective**: only its `[,;]` (comma/semicolon) branch
works. The `\s+и\s+` / `\s+and\s+` branches are **dead code** — the pattern in the raw string is
double-escaped (`\\s` = literal backslash + `s`), so it can never match a real query. Result:

- **M4** "Покажи DMS-267, её иерархию и задачи Калачанова в WMB" (has comma) → **delegated** →
  query-aware honest LLM answer (verified live).
- **M1** "Задачи Калачанова в WMB **и** задачи Семавина в DMS" (no comma) → **still elided** →
  "Для «Калачанов» найдено задач: 6. Ключи: [6 WMB]." — Semavin DMS silently dropped (verified live).
- **M3** "Задачи Калачанова в WMB **и** иерархию DMS-267" (no comma) → **still elided** → same
  one-goal answer — hierarchy silently dropped (verified live).

The owner shipped with **2 of their own new tests RED** (exactly the "и" cases) — the recurring
owner pattern (A205-1 / A205B / A217C / A229F1R: new tests not run to completion before ship).

**STOP** at first failing boundary (P0, corroborated by P1 live). P2/P3/P5 not executed per STOP
rule. Flag remains OFF by default; **do not enable** until the regex is fixed and re-gated.

---

## P0 — Integrity / tests (RED — first failing boundary)

| Check | Result |
|---|---|
| Core 6/6 byte-identical to baseline `6fb335d` | ✅ empty diff (agent_core_v4, robust, reliable, completion, v4_plugin_registry, llm/real) |
| Owner delta | presentation-only: `v4_synthesis_elision.py` (+42: F1 key-list from A229R2I + 9-line coordination guard), tests (+79), docs. 0 Core/planner/runtime/factory/settings |
| **`test_v4_synthesis_elision.py`** | **2 FAILED / 10 passed** — `test_single_terminal_multi_intent_uses_query_aware_synthesizer` cases "…в WMB **и** задачи Семавина в DMS" and "…в WMB **и** иерархию DMS-267" fail; comma case + all 8 pre-existing pass |
| Full V4 blast (`test_agent_core_v4*` + `test_v4*`) | 268 passed + the same 2 failures (no other regressions) |
| Task API SWTR / frontend build | not executed (STOP at P0) |

### Root cause (byte-proven)

`src/po_agent/harness/v4_synthesis_elision.py` (owner `0685faf`):

```python
return bool(re.search(r"(?i)(?:\\s+и\\s+|\\s+and\\s+|[,;])", str(query or "")))
```

The file's raw string literally contains `\\s` (two backslashes). In a raw string, `\\s` is the
regex "escaped backslash + literal s" — it matches the 2-character sequence `\s`, which never
occurs in user queries. Verified directly:

```
pattern compiled: '(?i)(?:\\\\s+и\\\\s+|\\\\s+and\\\\s+|[,;])'
match('Задачи Калачанова в WMB и задачи Семавина в DMS') = False   # "и" branch DEAD
match('DMS-267, иерархию, задачи Калачанова в WMB')             = True    # comma branch alive
match('Задачи Калачанова в WMB')                                = False   # (correct: single intent)
```

**Owner fix (one-character class, per occurrence):** write the pattern with single backslashes,
`r"(?i)(?:\s+и\s+|\s+and\s+|[,;])"`. The owner's own 3 parametrize cases are the regression lock —
all 3 must pass, then re-gate from P0.

---

## P1 — Multi-intent boundary re-check (live, flag ON @ 73b88a0) — RED (corroborates P0)

| Case | query | trajectory | flag-ON answer | verdict |
|---|---|---|---|---|
| M1 | Задачи Калачанова в WMB **и** задачи Семавина в DMS | 1 terminal `task.search_assignee` (Kalachanov only) | "Для «Калачанов» найдено задач: 6. Ключи: WMB-30482, WMB-30000, WMB-29890, WMB-29995, WMB-29830, WMB-29242" | **ELIDED — Semavin DMS silently dropped** (no comma → guard not triggered) |
| M3 | Задачи Калачанова в WMB **и** иерархию DMS-267 | 1 terminal `task.search_assignee` | "Для «Калачанов» найдено задач: 6. Ключи: [6 WMB]." | **ELIDED — hierarchy silently dropped** |
| M4 | Покажи DMS-267 **,** её иерархию **,** задачи Калачанова в WMB | 1 terminal `task.lookup` | LLM (70.5s): full DMS-267 table + "Иерархия: …корневая" (LLM inference) + "**Задачи Калачанова в WMB:** информация … отсутствует. Для получения этого списка нужен отдельный запрос" | **DELEGATED — honest gap flag** (comma → guard triggered) |

- M1/M3 = the exact A229R2U failing boundary → **NOT closed** (guard dead for "и").
- M4 = closed (delegation works; unexecuted goals flagged honestly in prose → still **OPEN** as
  unexecuted, per spec: prose acknowledgment ≠ completion).
- Same class also affects M2 "Покажи задачу DMS-267 **и** её иерархию" (no comma → would elide to
  the lookup one-goal answer) and any English "… and …" query.
- **Residual heuristic gap (non-blocking, owner consideration):** coordination phrasings without
  "и"/"and"/comma/semicolon (e.g., "плюс", "а также", "кроме") bypass the guard and still elide.
  The owner's own comment accepts this as "conservative presentation safety"; a coverage-based
  guard (goal coverage vs observations) would be the stronger long-term form.

---

## P2 / P3 / P5 — NOT executed (STOP at first failing boundary)

P2 (elision retention on single-intent, conjunctive-filter hit-rate), P3 (2-terminal delegation,
clarification/taxonomy, browser audit), P5 (GREEN gate) were not run. Prior-session evidence
(A229R2I/A229R2U, same code path except the 9-line guard) shows single-intent elision, 2-terminal
delegation, and the clarification/error taxonomy are unaffected by the guard (the guard only adds
delegation for coordination-bearing queries); these must be re-confirmed in the re-gate after the
regex fix.

---

## P4 — Multi-intent execution gap (separate, remains OPEN)

The presentation guard does not (and is not meant to) fix multi-intent **execution**: the planner
converges multi-intent queries to a single terminal without observations for the other goals.

Per-goal REAL AS21 oracles (fresh, this session + A229R2U battery):

| Goal | Oracle |
|---|---|
| Калачанов tasks in WMB | 6: WMB-30482, WMB-30000, WMB-29890, WMB-29995, WMB-29830, WMB-29242 (all terminal) |
| Семавин tasks in DMS | 173 all-time (A229R2U M1-2-terminal run); 3–4 open (drift: DMS-486 closed between sessions) |
| DMS-267 lookup | Resolved / Semavin.M.M / DMS-SPRNT-3 / Minor |
| DMS-267 hierarchy | CRPV-90180 → DMS-253 → DMS-267 (parent DMS-253 via decomposition; epic DMS-349) — **NOT** "root" as the M4 LLM inferred from null lookup fields (known LLM-inference limitation, A229R2U M2) |

**Exact first failing boundary (execution):** planner turn-level — after member/lookup resolution
the planner emits READY with one terminal covering only the first goal; no capability is loaded or
called for the second goal; the completion contract is satisfied by the single terminal
(`runtime_contract`), so nothing downstream can detect the missing goal.

**Recommended design (no Core changes):**
1. **Plugin/catalog level:** a goal-coverage check at the deterministic completion frontier for
   multi-goal queries — if the user query declares N coordinated goals (typed, from the query
   contract, not phrase routing) and only K<N have terminal observations, reject premature READY
   and emit a **typed NEEDS_CLARIFICATION** ("Выполнить все части: 1) задачи Калачанова в WMB;
   2) задачи Семавина в DMS — продолжить со второй частью?") or schedule the remaining goals as
   follow-up turns. This mirrors the A229F3R constraint-coverage guard pattern (postcondition at
   the API seam, no planner changes).
2. **API seam alternative:** a `goal_coverage` postcondition (like `_guard_completed_constraint_coverage`)
   that downgrades COMPLETED→NEEDS_CLARIFICATION when structured evidence covers fewer declared
   goals than the query contract — presentation-safe, auditable, no Core.
3. **V5 sidecar (future):** a planner-level multi-step decomposition (plan per goal, sequential
   trajectories) — separate gate, not this workstream.

**Can it safely clarify?** Yes — the clarification-continuation machinery (clarification_id +
session) is proven (A229F3R/A227); a typed "second part?" continuation would resolve the gap
without inventing facts.

---

## Audit

- Agent 8004 @ `73b88a0` (flag ON, PID 56825 at report time), task-api 8241, MCP 3000 live.
- QA touched 0 production files; report-only commit.
- Live runs this session: 4 (M1, M3, M4 ×2) — 0 local store reads, 0 mutations, 0 unscoped scans
  (single-terminal bounded reads only).

---

## Verdict & recommendation

`AGENT_CORE_V4_SYNTHESIS_MULTI_INTENT_SAFETY_RED_A229R2UR` — **STOP**.

- **First failing boundary:** P0 — 2/3 of the owner's new delegation regression cases fail because
  the coordination regex's `и`/`and` branches are dead (`\\s` double-escape in the raw string);
  live-confirmed at P1: M1/M3 (canonical A229R2U RED) still elide to the unqualified one-goal
  answer; only the comma-bearing M4 delegates (honestly).
- **Owner fix:** single backslashes in the pattern (`r"(?i)(?:\s+и\s+|\s+and\s+|[,;])"`), re-run
  `test_v4_synthesis_elision.py` (all 12 cases green), then full A229R2UR re-gate from P0 (P1 M1/M3
  must delegate with honest gap-flags; P2 single-intent elision −1 call retained; P3 2-terminal
  delegation + taxonomy + browser audit; P5 GREEN gate).
- Multi-intent **execution** limitation stays **OPEN** (P4 design above) — independent of this
  presentation guard.
- **Flag recommendation:** keep `PO_AGENT_V4_SYNTHESIS_ELISION=false`; do not enable by default
  until the re-gate is GREEN.
