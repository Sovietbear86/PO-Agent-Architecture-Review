# A229R2I — Synthesis-Turn Elision Re-Gate (Agent Core v4)

**Verdict:** `AGENT_CORE_V4_SYNTHESIS_ELISION_GREEN_A229R2I`

**START_HEAD:** `36e814511de880f40703fa6b4dcaeb874b18722c` (owner implementation)
**Baseline checkpoint:** `6fb335d6f67344245a5c65e5c1b5b145759e96da`
**Feature flag:** `PO_AGENT_V4_SYNTHESIS_ELISION` (default `false`)
**Role:** QA / tester only — production code NOT modified
**Date:** 2026-10-13

---

## Summary

The owner implemented **synthesis-turn elision** (Candidate S from the A229R2 design gate): a
`TerminalSynthesisElider` wrapper installed at the public synthesizer seam in `runtime_factory.py`.
For a narrow, source-grounded subset of V4 trajectories (exactly one eligible terminal task
capability, all other observations intermediate/resolver), it renders the terminal capability's
own answer deterministically, removing exactly the final LLM synthesis round-trip. Every other
trajectory (multi-terminal, unknown capability, empty answer, non-COMPLETED) delegates to the
original LLM synthesizer.

All phases P0–P7 + audit are **GREEN**. The elision is correct, safe, and a strict rollback
behind a flag that defaults OFF. One non-blocking finding is documented (§F1: the `task.search*`
"append keys" branch is inert in production because it reads keys that `_compact_data` has already
replaced — no user-facing regression).

**Live stack (fresh REAL AS21):** agent 8004 (PID 12986, flag ON at report time), task-api 8241
(PID 78133, system py3), MCP-SWTR SSE 3000 (PID 78067), vite [::1]:5175 (PID 81246).

---

## P0 — Integrity & change boundary (GREEN)

| Check | Result |
|---|---|
| Core 6 files byte-identical to baseline `6fb335d` | ✅ empty diff: `agent_core_v4.py`, `agent_core_v4_reliable.py`, `agent_core_v4_robust.py`, `agent_core_v4_pluginized.py`, `agent_core_v4_completion.py`, `llm/real.py` |
| Owner delta (production) | 4 files only — `harness/v4_synthesis_elision.py` (new, +105), `harness/runtime_factory.py` (+9/−3 seam), `config/settings.py` (+5 flag), `api/v1/__init__.py` (+1 flag passthrough). **0 Core / planner / runtime / task-api.** |
| V4-focused suite (`test_v4_synthesis_elision.py` + `test_agent_core_v4*.py` + `test_v4*.py`) | ✅ 264 passed |
| Owner elision unit tests (`test_v4_synthesis_elision.py`) | ✅ 6/6 passed |
| Factory wiring (in-process) | ✅ flag OFF → bare `ResponseSynthesizerV4`; flag ON → `TerminalSynthesisElider` wrapping it (only when flag ∧ `agent_core_v4_enabled` ∧ planner_client present) |
| Pre-existing (A/B-proven at checkpoint, NOT owner delta) | `tests/test_harness_runtime_factory.py:21` (asserts `task-history == "unavailable"`), `task-api/tests/integration/test_s21_agent_integration.py::test_swtr_adapter_initialization` (removed `mcp_host` attr). Not in the V4-focused set. |

The design honors the A229R2 boundary: presentation-layer only; planning, capability execution,
completion, evidence, and clarification semantics are untouched.

---

## P1 — Flag OFF rollback (GREEN)

24 runs (A–H × 3, flag OFF, model-call count ~3 for the baseline class). Answers are **rich LLM
prose** (markdown tables / trees), proving the synthesis turn is active and the rollback path is
the original behavior. All facts exact vs the fresh REAL AS21 oracle (`oracle_before.json`):

| Case | Query class | Terminal capability | LLM calls (OFF) | Result vs oracle |
|---|---|---|---|---|
| A | "Задачи Калачанова в WMB" | `task.search_assignee` | 3, 3, 3 | count=6, keys = 6/6 exact (`WMB-29242,29830,29890,29995,30000,30482`) |
| B | in-progress in DMS-SPRNT-3 | `task.search` | 5, 6, 5 | count=0 (sprint 51 tasks all Closed/Resolved → REAL_EMPTY) |
| C | "Покажи задачу DMS-267" | `task.lookup` | 3, 4, 3 | DMS-267 / Resolved / Semavin.M.M exact |
| D | open created last 2 days (WMB Kalachanov) | `task.search_created` | 7, 4, 8 | count=0 (only open WMB-30482 created 10-06 < window 10-12 → REAL_EMPTY) |
| E | open defects ≥30.09 (DMS Semavin) | `task.type_analysis` | 5, 5, 4 | count=0 (only open bug DMS-431 created 25.09 < 30.09 → REAL_EMPTY) |
| F | "Покажи иерархию DMS-267" | `task.hierarchy` | 3, 3, 3 | CRPV-90180 → DMS-253 → DMS-267 exact |
| G | incomplete period (clarify) | — | 7, 5, 4 | typed NEEDS_CLARIFICATION (free-text) |
| H | continuation of G | `task.type_analysis` | 3, 3, 5 | count=0 (REAL_EMPTY) |

---

## P2 — Flag ON: exactly −1 final LLM call (GREEN)

Flag ON, A/C/F × 5. The elided call is exactly the final synthesis; the capability trajectory is
byte-identical to OFF (same `load_skill → … → terminal → ready` sequence).

| Case | LLM OFF | LLM ON (×5) | Delta | Trajectory |
|---|---|---|---|---|
| A | 3, 3, 3 | **2, 2, 2, 2, 2** | **−1 each** | `load_skill → task.search_assignee → ready` |
| C | 3, 4, 3 | **2, 2, 2, 2, 2** | **−1** (OFF's 4th was a bounded-repair retry) | `load_skill → task.lookup → ready` |
| F | 3, 3, 3 | **2, 2, 2, 2, 2** | **−1 each** | `load_skill → task.hierarchy → ready` |

ON answer becomes the deterministic capability answer (e.g. A: `Для «Калачанов» найдено задач: 6.`),
vs OFF's rich LLM prose. Source reads unchanged (A: 2/run both states).

---

## P3 — Full A–H parity, flag ON (GREEN)

OFF vs ON structured parity — **CAP_OK, KEYS_OK, COUNT_OK all True for every case.** The
executed capability, its resolved constraints (semantically), and the resulting key set / count are
identical; only the final answer text and LLM count change.

- **No silent constraint drop (proven):** D and E return `0` *despite* 1 and 4 open tasks existing
  in source respectively — the created-period filter is applied (WMB-30482 created 10-06 < 10-12
  window; DMS-431 created 25.09 < 30.09). If the period were dropped, counts would be 1 and 1.
- **Args surface variance (B/E/H) is pre-existing planner non-determinism, not elision:** B
  `status` varies `in_progress` / `In Progress` / `in progress`; E/H vary `open` / `not_completed`.
  The OFF data already varied within itself (OFF E used both `not_completed` and `open`). Every
  form semantically converges (all → `is_open` / canonical IN_PROGRESS) to the same count=0 result.
  Core/planner are byte-identical, so elision cannot introduce argument variance.
- **Source reads unchanged per case** (elision is post-execution; structurally cannot touch source).

| Case | LLM OFF | LLM ON (×5) | source reads OFF→ON |
|---|---|---|---|
| A | 3,3,3 | 2,2,2,2,2 | 2→2 each |
| B | 5,6,5 | 4,5,4,5,4 | 2→2 each |
| C | 3,4,3 | 2,2,2,2,2 | 1→1 (one 2 = files) |
| D | 7,4,8 | 6,3,4,3,3 | 3,2,3→3,2,2,2,2 |
| E | 5,5,4 | 3,3,3,4,4 | 2→2 each |
| F | 3,3,3 | 2,2,2,2,2 | 3→3 each |
| H | 3,3,5 | 3,2,2,2,2 | 2→2 each |

(Planner bounded-repair retries — the source of OFF's D=7/8 and C=4 — are LLM non-determinism,
independent of elision.)

---

## P4 — Delegation safety (GREEN)

**In-process probe (10/10):** 2 terminals, terminal+analytical, unknown capability, empty answer,
and multi-part inputs all **delegate** to the wrapped LLM synthesizer (never deterministically
flatten). `_eligible_terminal` returns `None` whenever terminals ≠ 1 or a non-resolver/non-terminal
observation is present.

**Live multi-part probe:** the planner converges composite phrasings to a single terminal on all 4
phrasings tested ("Покажи задачу DMS-267 и её иерархию", "Задачи Калачанова в WMB и задачи Семавина
в DMS", etc.) — a **pre-existing multi-part planner limitation** (drops the second goal), unaffected
by elision. No stable live 2-terminal example was reachable; the in-process 10/10 is the primary
P4 evidence (spec-permitted). The safety property holds regardless: the elider **delegates** rather
than flattens whenever ≥2 terminals or an unknown non-resolver observation is present.

---

## P5 — Clarification / error taxonomy retained (GREEN)

- **Incomplete period (G):** 5/5 typed `NEEDS_CLARIFICATION` with a usable `clarification_id`
  (free-text period prompt). G LLM counts ON = 2,10,7,9,3 vs OFF 7,5,4 — **not** systematically −1,
  confirming the elider does **not** run on non-COMPLETED trajectories (planner-frontier retries
  dominate; no synthesis turn exists to elide).
- **Option-button space-ambiguity:** T1 "Задачи Гаранина в сентябрьском спринте" →
  `NEEDS_CLARIFICATION` options `[CRPV, DMS, OLP, STS, WMB]` + `clarification_id`; T2 (DMS click,
  same session + clarification_id) → **COMPLETED** resuming the original goal
  (`space.resolve → sprint.search → task.search(assignee=Garanin.R.V, sprint_id=DMS-SPRNT-3, space=DMS)`),
  result 0 (grounded). The COMPLETED continuation is elided (`Найдено задач: 0.`) — exactly as required
  (only COMPLETED continuation may elide).
- **Unit taxonomy (API contract guard suite):** 11/11 pass — period-drop backstop
  (`test_completed_task_period_drop_is_promoted_to_clarification`), provider-failure-is-not-
  misreported-as-clarification, clarification continuation, multi-hop, and the "applied period is
  allowed" / "non-period task not affected" guards.

---

## P6 — Browser / UI acceptance, flag ON (GREEN — 5/5)

Ran against vite [::1]:5175 + agent 8004 (flag ON).

| Test | Result |
|---|---|
| P6-1 task collection (A) | ✅ COMPLETED; chat shows `найдено задач: 6`; **6 task cards** rendered (`kind: task_collection`, all 6 `task_keys`) |
| P6-2 exact lookup (C) | ✅ DMS-267 drawer readable; no raw `swtr_attributes` / `{"attribute":` / internal payload leaked |
| P6-3 hierarchy (F) | ✅ readable tree; no raw `"source":`/`"destination":`/HTTP lines |
| P6-4 type-analysis (E) | ✅ readable, no generic error |
| P6-5 overview mount + audit | ✅ retained widgets intact; 2 snapshot POSTs, **0 bad status, 0 external direct source calls, 0 console errors** |

---

## P7 — Performance (GREEN)

| Metric | OFF | ON |
|---|---|---|
| COMPLETED-eligible p50 wall | 12.68 s | 11.8 s |
| COMPLETED-eligible p90 wall | **33.19 s** | **21.49 s** (−35%) |
| LLM calls / eligible COMPLETED query | baseline | **baseline − 1** (proven 15/15 on A/C/F, consistent on B/D/E/H) |
| Source reads | unchanged per case | unchanged per case |

Wall time is dominated by LLM round-trips (2–20 s each); the −1 call is a consistent structural
saving, and its wall-time benefit is largest for planner-heavy queries (D: p50 34→19.9 s). Source
reads are provably unchanged because elision is strictly post-execution.

---

## Audit (both flag states, agent outbound HTTP)

| Check | OFF | ON |
|---|---|---|
| Local legacy store reads (`/api/v1/tasks`, non-swtr) | 0 | 0 |
| Mutations (non-LLM, non-`/query`) | 0 | 0 |
| Unscoped full-tenant scans (`task-query`/`assignee-tasks` without space/assignee) | 0 | 0 |
| swtr-read source reads | 59 | 444 (more runs + P4/P5/P6 probes; per-run identical) |

---

## Findings

- **F1 (non-blocking) — elider `task.search*` "append keys" path is inert in production.**
  `TerminalSynthesisElider._task_keys()` reads `data.get("task_keys")` / `data.get("tasks")` from
  the **observation** data, but the runtime stores `_compact_data(...)` in `V4Observation.data`,
  which **pops** both `tasks` and `task_keys` (replacing them with `task_keys_sample` +
  `task_key_count`). Consequently `_task_keys()` returns `[]` and the elider returns the capability
  answer verbatim (e.g. `Для «Калачанов» найдено задач: 6.`) with **no** `Ключи: …` line.
  **No user-facing regression:** the count is correct and grounded, and the UI renders the full
  structured task collection from the *unchanged* response data (`data.results[].data.task_keys` —
  the raw capability payload, not the compacted observation) — P6-1 proved all 6 cards render.
  If the owner wants the key list in the chat text, the elider should read `task_keys_sample`
  instead of `task_keys`/`tasks`.
- **F2 (non-blocking, pre-existing) — multi-part planner convergence.** Composite
  "X и Y" queries converge to a single terminal (second goal dropped). Unaffected by elision;
  tracked as a pre-existing planner limitation (A229R2 O3 lineage).

## Recommendation

The synthesis-turn elision is **correct, safe, and fully rollback-able** behind
`PO_AGENT_V4_SYNTHESIS_ELISION` (default OFF). Recommend freezing an immutable
`checkpoint/v4-synthesis-elision-green-a229r2i` on `36e8145`. Optionally fix F1 (read
`task_keys_sample`) so the `task.search*` deterministic answer also carries the key list; it is
not a correctness or regression blocker.
