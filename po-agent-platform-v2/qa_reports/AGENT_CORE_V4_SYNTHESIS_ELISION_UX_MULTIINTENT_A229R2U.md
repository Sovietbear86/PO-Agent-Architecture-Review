# A229R2U — Synthesis-Elision UX + Multi-Intent Re-Gate (Agent Core v4)

**Verdict:** `AGENT_CORE_V4_SYNTHESIS_ELISION_UX_RED_A229R2U`
**First failing boundary:** P3 — multi-intent (the deterministic elider silently drops an
unaddressed intent for 1-terminal-converged multi-intent queries, while flag-OFF LLM synthesis,
which receives `user_query`, honestly flags the gap)

**START_HEAD / tested HEAD:** `fc449cc` (owner production: F1 key-list fix `20ebaed` + tests
`dcacf6d` + A229R2U assignment `fc449cc`), repo HEAD `46fe5b8` (QA report, docs-only; production
byte-identical to `fc449cc`)
**Baseline checkpoint:** `6fb335d6f67344245a5c65e5c1b5b145759e96da`
**Feature flag:** `PO_AGENT_V4_SYNTHESIS_ELISION` (default `false`)
**Role:** QA / tester only — production code NOT modified
**Date:** 2026-10-14

> **Scope note:** `GIGACODE_NEXT_ACTION.md` (commit `fc449cc`) carries the A229R2U assignment — a
> UX-focused follow-up to the completed A229R2I implementation re-gate
> (`AGENT_CORE_V4_SYNTHESIS_ELISION_A229R2I.md`, commit `9f24b48`): (1) UX after synthesis elision,
> (2) OFF/ON performance, (3) a **separate multi-intent investigation**.
>
> **Important:** between A229R2I and A229R2U the owner shipped the **F1 fix** (`20ebaed fix(v4):
> render complete compact task-key samples only`) that resolves the A229R2I F1 finding (the elider's
> inert key-append). This re-gate tests the F1-fixed code. An initial pass was run against the stale
> pre-F1 HEAD `9f24b48`; after the remote advanced this report was **re-verified live on `fc449cc`**
> (agent restarted on `46fe5b8`).

---

## Summary

P0 (integrity), P1 (single-intent UX), and P2 (performance) are **GREEN** on the F1-fixed code.
**P3 multi-intent is RED**: for a multi-intent query that the planner converges to a **single**
eligible terminal, the deterministic elider (flag ON) renders that one terminal's answer and
**silently drops the other requested intent with no acknowledgment**, whereas the flag-OFF LLM
synthesizer (which receives `user_query`) **honestly flags the unaddressed intent**. This is
**re-confirmed on the F1-fixed HEAD** (M1/M3/M4). It crosses the acceptance line — the dropped
intent is required content, not cosmetic terseness.

The F1 key-list fix (`20ebaed`) **resolves the A229R2I-F1 single-intent key-append** (A's ON answer
now lists all keys) and **does NOT** touch `_eligible_terminal`, so the multi-intent silent-drop
persists — and the now-confident full key list makes the single-intent answer read even more like a
complete answer. Genuine 2-terminal multi-intent (M5) **delegates safely**.

**Live stack (fresh REAL AS21):** agent 8004 (flag ON at report time, PID 11274 @ `46fe5b8`),
task-api 8241, MCP-SWTR SSE 3000, vite [::1]:5175. Oracle (fresh, `oracle.json`): A=6 WMB keys,
B=0 in-progress in DMS-SPRNT-3, C=DMS-267 Resolved/Semavin, D=0 in-window, E=0 in-window,
F=1 link DMS-253→DMS-267 (DMS-267 parent chain CRPV-90180→DMS-253→DMS-267).

---

## P0 — Integrity (GREEN)

| Check | Result |
|---|---|
| Core 6/6 byte-identical to baseline `6fb335d` (incl `v4_plugin_registry.py`) | ✅ empty diff on `fc449cc` |
| F1 fix change boundary | `20ebaed` touches only `harness/v4_synthesis_elision.py` (+22/−11): `_task_keys` now reads `task_keys_sample` and adds a completeness guard (render keys only when the sample is complete, i.e. `task_key_count == len(sample)`); 0 Core/planner/runtime/task-api |
| Focused (elision incl. 2 new key-list tests, runtime env aliases, runtime factory, browser api contract, created period, semantics hierarchy) | elision **8/8**; set 42 pass + 1 pre-existing (`test_harness_runtime_factory.py:21`, A/B-proven) |
| Full V4 blast | 264 passed (pre-F1); re-confirmed elision 8/8 on `fc449cc` |
| Frontend build / Task-api SWTR | exit 0 / 34 passed (production unchanged by F1) |

---

## P1 — Single-intent UX after elision (GREEN; F1 resolves the key-list gap)

**F1 fix verified live:** flag-ON `task.search_assignee` (A) now appends the complete key list:
`Для «Калачанов» найдено задач: 6. Ключи: WMB-30482, WMB-30000, WMB-29890, WMB-29995, WMB-29830, WMB-29242`
— matching the flag-OFF LLM answer's key list. The A229R2I-F1 inert key-append is **resolved**; the
truncation guard prevents implying a full list from a `>20` sample.

| Case | flag OFF (rich) | flag ON (elided, F1-fixed) | UX |
|---|---|---|---|
| A search_assignee | "…найдено 6 задач: [6 keys]" | "…найдено задач: 6. **Ключи: [6 keys]**" | ✅ now parity with OFF |
| B search (sprint+status) | "В DMS-SPRNT-3 (13–27 сент, завершён) задач «В работе» не найдено — 0" | "Найдено задач: 0." | ⚠️ cosmetic — loses sprint/status context in text (in structured data) |
| C lookup | full DMS-267 table | "DMS-267 — … Статус: Resolved. Исполнитель: Семавин. Вложений: 0." | ✅ cosmetic — drawer shows detail |
| D search_created | "…созданных за последние 2 дня, не найдено (0)" | "…со статусом «**not_completed**»: 0." | ⚠️ correct but leaks internal token `not_completed` |
| E type_analysis | "…не найдено. В периоде 3 открытые, но все тип «Задача», а не «Дефект»." | "Найдено задач типа «дефект»: 0." | ⚠️ correct but loses "why 0" (type-mismatch) explanation |
| F hierarchy | tree + table | "Для DMS-267: уровней родителей — 2, связанных — 0. Эпик: DMS-349." | ⚠️ correct but drops the visual tree from text |

No single-intent elided answer is **misleading**; all facts correct. Non-blocking polish:
- **U1:** B/E/F lose explanatory context present in the OFF LLM answer (sprint context / "why 0" /
  tree); the detail remains in structured response data + UI.
- **U2:** D leaks the canonical internal status token `not_completed` into user-facing text.

---

## P2 — Performance flag OFF vs ON (GREEN)

F1 is presentation-only (no LLM/source change), so the A229R2I + fresh A229R2U performance results
hold on `fc449cc`. Eligible single-intent A-F (n=3 each):

| Case | OFF p50/p90 (s) | ON p50/p90 (s) | LLM calls OFF→ON | source reads |
|---|---|---|---|---|
| A | 15.46 / 21.32 | 10.52 / 12.88 | 3→2 | unchanged (2) |
| B | 54.88 / 55.54 | 31.20 / 36.70 | 5,6,5→4,5,4 | unchanged (2) |
| C | 16.97 / 22.50 | **6.08 / 6.10** | 3,4,3→2 | unchanged (1) |
| D | 69.26 / 84.73 | 29.69 / 61.63 | 7,4,8→6,3,4,3,3 | unchanged (2-3) |
| E | 31.57 / 45.81 | 40.91 / 44.81 | 4→3 | unchanged (2) |
| F | 16.43 / 16.51 | 21.33 / 24.96 | 3→2 | unchanged (3) |
| **A-F total** | **24.57 / 59.77** | **22.43 / 42.37** | **exactly −1 on eligible COMPLETED** | **unchanged per case** |

−1 LLM call on eligible COMPLETED (A229R2I per-run counts + fresh trajectory + fresh log LLM-POST
totals); p90 wall −29%; source reads unchanged. **Redundant second `load_skill` in B/D still
present** (A229R2 O3) — not fixed in this assignment (per spec).

---

## P3 — Multi-intent investigation (RED — first failing boundary; re-confirmed on F1-fixed `fc449cc`)

Planner multi-intent behavior is **non-deterministic** (converges to 1 or 2 terminals). Re-verified
live on `fc449cc`:

| Query | intents | terminal(s) flag ON | flag ON answer |
|---|---|---|---|
| M1 "Калачанов WMB **и** Семавин DMS" | 2 | 1 (search_assignee) ×2 | "Для «Калачанов» найдено задач: 6. **Ключи: [6 WMB]**." ← **Semavin DMS silently dropped** |
| M3 "Калачанов WMB **и** иерархию DMS-267" | 2 | 1 (search_assignee) ×2 | "Для «Калачанов» найдено задач: 6. Ключи: [6 WMB]." ← **hierarchy silently dropped** |
| M4 "DMS-267 **,** иерархию **,** Калачанов WMB" | 3 | 1 (lookup) ×2 | "DMS-267 — … Статус: Resolved…" ← **2 intents dropped, no acknowledgment** |
| M5 "открытые Семавин DMS **и** Калачанов WMB" | 2 | **2 (task.search ×2)** | **full 2-part answer** (delegates — safe); one transient 148s LLM/timeout FAILED (not elision) |

The **flag-OFF LLM synthesizer** (which receives `user_query`) **honestly flags** the unaddressed
intent on the same 1-terminal trajectories (A229R2U OFF battery):
- M1 OFF: "Задачи Калачанова в WMB: 6… | **Задачи Семавина в DMS: данные по этому запросу
  отсутствуют — информация не была получена.**"
- M3 OFF: addresses both; flags the missing part.
- M4 OFF: table + "Иерархия: …корневая" + "**Задачи Калачанова в WMB:** информация отсутствует.
  Для получения … отдельный запрос."

**The regression:** the F1 fix did **not** change `_eligible_terminal` (observation-count-based:
"exactly 1 eligible terminal + rest intermediate"). When a multi-intent query converges to a single
terminal that does not cover the full `user_query`, the elider renders that one terminal's (now
confident, key-list-bearing) answer and silently omits the rest — materially more misleading than
the flag-OFF honest gap-flag. **M2** is a wash (the flag-OFF LLM *infers* "no hierarchy" from null
lookup fields — actually wrong, DMS-267 has parent DMS-253 — so both OFF and ON are imperfect there;
the true fix is the planner calling `task.hierarchy`).

### Root-cause decomposition
1. **Pre-existing (A229R2I F2):** planner converges multi-intent to a single terminal without
   observations for the other intents. Unchanged by F1.
2. **Elision-specific (this finding):** `TerminalSynthesisElider._eligible_terminal` ignores
   `user_query`; a multi-intent query that converged to 1 terminal is elided to a silent single-intent
   answer. The flag-OFF LLM synthesizer receives `user_query` and flags the gap — counterfactual,
   demonstrably better UX. The F1 key-list fix marginally increases the misleading confidence.

### Classification
RED. Per the acceptance criterion ("deterministic answer text must not be misleading or materially
worse; cosmetic terseness acceptable, missing required factual content is not"), the elided
1-terminal-converged multi-intent answer **silently omits a requested intent** — missing required
factual content + misleading, not cosmetic.

### Owner fix boundary (bounded; harness seam, NOT Core)
In `TerminalSynthesisElider` (or the factory seam installing it), do **not** elide when the single
eligible terminal does not plausibly cover the full multi-intent `user_query` — delegate to the LLM
synthesizer (which flags the gap) when the query references a second person / a second collection /
a hierarchy+collection compound that is not represented by an observation. Add a non-mocked
regression for a 1-terminal-converged multi-intent query asserting the answer still acknowledges the
unaddressed intent. Do **not** change Core/planner. (Redundant second LOAD + planner multi-intent
convergence remain separate out-of-scope gates.)

---

## Audit (fresh `fc449cc` logs, both flag states)

| Check | flag OFF | flag ON |
|---|---|---|
| Local legacy store reads | 0 | 0 |
| Mutations (non-LLM, non-`/query`) | 0 | 0 |
| Unscoped full-tenant scans | 0 | 0 |

No fabrication; the ON multi-intent answers **omit** (not invent) the unaddressed intent.

---

## Verdict & recommendation

`AGENT_CORE_V4_SYNTHESIS_ELISION_UX_RED_A229R2U` — **STOP** at P3.

- **F1 fix (`20ebaed`) certified:** single-intent `task.search*` elided answers now carry the
  complete (≤20) key list with a truncation guard (A verified live; 8/8 elision tests). P1's
  key-list gap is resolved; U1/U2 remain cosmetic polish.
- P0/P1/P2 GREEN on the F1-fixed HEAD.
- **P3 RED (re-confirmed on `fc449cc`):** synthesis elision silently drops an unaddressed intent for
  1-terminal-converged multi-intent queries, materially worse/misleading vs flag-OFF LLM synthesis
  that honestly flags the gap (M1/M3/M4); genuine 2-terminal (M5) delegates safely.

Owner action before re-gate: bound the elider's eligibility so a multi-intent `user_query` whose
secondary intent is not covered by an observation **delegates** (harness-seam only, no Core change)
+ non-mocked multi-intent regression. Then re-gate P3 (M1/M3/M4 must acknowledge the unaddressed
intent, or the planner must emit the second terminal) and re-confirm P1/P2. Do not flip the feature
default until P3 is GREEN.
