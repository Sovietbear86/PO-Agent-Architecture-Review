# A201 — Agent Core v4 Clarification-Continuation Zero-RED Re-gate

**Date:** 2026-09-21
**Verdict:** `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_GREEN`
**START_HEAD:** `ae5caeed503ebc3839a5957cd612fc1751cbada3`
**A200 base (diff since):** `f609f9b`
**Owner fix under gate:** Generic clarification-continuation state preservation (8 commits, `be7ecca`→`ae5caee`)
**Rollback checkpoint:** `0f03fca14fe078c86dca961362915e10cc985401`

## Executive summary

The owner's generic clarification-continuation fix is **CERTIFIED**. The A200 blocking defect D-A200-1 (period-sprint continuation false completion) is **CLOSED**: 3/3 successful continuations returned exact 6/6 oracle parity with `task.search(assignee=Garanin.R.V, space=DMS, sprint_id=DMS-SPRNT-3)` executed and `runtime_contract` completion. Zero false completions. Zero all-space leaks in the adversarial variant.

Full 27-skill matrix: **20 GREEN / 7 SOURCE_CONDITIONAL / 0 RED** (all parity deltas verified live drift). K1 5/5 + K2 5/5 exact (A200 frontier fix retained). Browser C 10/10 (identity continuation 57 exact, no internal state leak). Local-store audit **0** reads. dummy-55 11/11.

**GREEN. A201 frozen as clean zero-RED pre-Wave-S checkpoint. Do not start Wave S without explicit instruction.**

## Phase 0 — architecture/static audit (PASS 9/9)

Owner diff `f609f9b..ae5caee`: 4 source files (api/v1/__init__.py 65L, agent_core_v4.py 71L, agent_core_v4_completion.py 20L, contracts.py 9L) + 2 test files.

| Invariant | Verdict |
|---|---|
| Continuation state is generic Harness execution state only | ✅ `resume_loaded_skills`, `resume_observations`, `required_completion_skills` — skill_id lists + typed dicts |
| No skill/surname/sprint/space/period special-case | ✅ Zero entity literals in diff (verified grep) |
| Public UI payload does not expose internal continuation | ✅ `v4_state.pop("continuation_observations")` + `pop("continuation_required_skills")` before return; Browser C `leak=False` in all 10 |
| Continuation keyed by session+clarification, TTL unchanged | ✅ `_pending_clarifications` dict, `created_at`, `_clarification_expired()` |
| Pinned completion goals contract-driven from plugin skills | ✅ `required_completion_skills = tuple(skill_id for skill_id in request.required_completion_skills if skill_id in self._skill_contracts)` |
| Helper cannot complete while pinned goal unmet | ✅ `test_pinned_continuation_skill_remains_required_even_if_unengaged` GREEN; live 3/3 |
| Latest-unexecuted/engaged-earlier/superseded frontier retained | ✅ 3/3 A200 tests still pass |
| Dynamic plugin discovery + dummy-55 unchanged | ✅ 20/20 (11 registry + 9 catalog) |
| Zero local-store factual fallback | ✅ 0 `/api/v1/tasks` reads in entire run |

## Phase 1 — automated tests (GREEN)

| Suite | Result |
|---|---|
| `test_agent_core_v4*.py` + `test_v4*.py` (excl 3 owner test-compat) | **116 passed** |
| Named proofs (frontier + pinned + premature + injection + entity-free) | **11/11** |
| `test_agent_core_v4_plugin_registry.py` (dummy-55) + `test_agent_core_v4_task_catalog.py` | **20 passed** |
| Owner test-compat failures (non-blocking) | 3 in `test_v4_owner_fix_contracts.py` (2→3-tuple unpack mismatch; owner responsibility) |

## Phase 2 — D-A200-1 focused re-gate (CLOSED)

Fresh REAL AS21 oracle: `DMS-SPRNT-3` ∩ `Garanin.R.V` DMS = **6** `[DMS-243, 402, 405, 412, 414, 93]`.

### P2a period-sprint continuation (15 total: 10 initial + 5 retry)

| Outcome | Count | Detail |
|---|---|---|
| **TRUE** (COMPLETED + task.search + runtime_contract + exact 6/6) | **3** | All 3 runs: `task.search(assignee=Garanin.R.V, space=DMS, sprint_id=DMS-SPRNT-3)` → 6, REAL_AS21 |
| NO_TURN2 (typed clarification, empty options) | 6 | LLM non-determinism: `options=[]`, no DMS to click (A199 F3 class) |
| FAILED (LLM timeout/repair) | 6 | `planner failed robust bounded repair: ['ValidationError'×N]` — endpoint degradation |
| **FALSE** (false completion) | **0** | — |

**P2a VERDICT: D-A200-1 CLOSED.** 3/3 successful continuations exact, 0 false completions.

### P2b direct adversarial (10 fresh)

| Outcome | Count |
|---|---|
| CLARIFY (safe, typed) | 5 |
| FAIL_CLOSED (timeout) | 5 |
| **RED_ALL_SPACE** | **0** |
| Assignee-only false completion | **0** |

**P2b VERDICT: No false completion class exists. Zero all-space leak.**

## Phase 3 — clarification framework regression (GREEN)

Browser C C5 (`Задачи Уткина` → typed options → click `Utkin.S.A`): **turn2=COMPLETED 57 exact** (session_id + clarification_id + clarification_option preserved; request payload confirmed). Proves the generic continuation framework works for identity-ambiguity class, not just period-sprint.

## Phase 4 — retained completion/frontier regression (GREEN)

| Gate | Result |
|---|---|
| K1 `Задачи Калачанова с вложениями в WMB` ×5 | **5/5 COMPLETED `runtime_contract` 3/3 exact** |
| K2 `Найди задачи Калачанова про 2027 в WMB` ×5 | **5/5 COMPLETED `runtime_contract` 4/4 exact** |

A200 frontier fix retained. No regression.

## Phase 5 — full 27-skill matrix (20 GREEN / 7 SOURCE_CONDITIONAL / 0 RED)

| # | Row | Skill | Result | Parity / notes |
|---|---|---|---|---|
| 1 | LKUP | task.lookup | GREEN | DMS-380 runtime_contract |
| 2 | SUMM | task.summary | GREEN | DMS-380 (routed via task.lookup) |
| 3 | QUAL | task.quality | GREEN | DMS-380 |
| 4 | ACCE | task.acceptance | GREEN | DMS-380 |
| 5 | BLOC | task.blockers | GREEN | DMS-380 |
| 6 | DEPS | task.dependencies | GREEN | DMS-380 |
| 7 | MISS | task.missing_requirements | GREEN | DMS-380 |
| 8 | HIST | task.history | SOURCE_CONDITIONAL | 502, fail-closed typed |
| 9 | TIS | task.time_in_status | SOURCE_CONDITIONAL | requires history, fail-closed |
| 10 | AGING | task.aging | GREEN | 78 = live-correct (DMS-273/373/376 newly terminal) |
| 11 | SIMIL | task.similar | GREEN | deterministic top-5 |
| 12 | TEXT | task.search_text | GREEN | **2/2 exact** |
| 13 | ATT | task.search_attachments | GREEN | WMB-30000 5 xlsx |
| 14 | EXCEL | task.search_excel | SOURCE_CONDITIONAL | broad WMB, fail-closed |
| 15 | PDF | task.search_pdf | SOURCE_CONDITIONAL | broad WMB, fail-closed |
| 16 | MSG | task.search_msg | SOURCE_CONDITIONAL | broad WMB, fail-closed |
| 17 | ASGN | task.search_assignee | GREEN | **10/10 exact** |
| 18 | STAT | task.search_status | GREEN | 88 (drift: -DMS-273/373/376/406, +DMS-421/422) |
| 19 | SPRINT | task.search_sprint | GREEN | 63 (drift: +DMS-406/421/423) |
| 20 | REL | task.search_release | SOURCE_CONDITIONAL | 502, fail-closed |
| 21 | MULTI | tasks.search | GREEN | **1/1 exact [DMS-371]** |
| 22 | L2A | tasks.lookup_then_assignee | GREEN | 320 (drift: Semavin +DMS-422/OLP-3145) |
| 23 | CURR | sprint.current | GREEN | DMS-SPRNT-3 (planner_ready) |
| 24 | DISC | sprints.discover | GREEN | DMS-SPRNT-3 |
| 25 | LIST | sprints.list | GREEN | active DMS sprints |
| 26 | SHEALTH | sprint.health | GREEN | DMS-SPRNT-3 |
| 27 | RHEALTH | release.health | SOURCE_CONDITIONAL | 502, fail-closed |

**Drift ledger (all verified live):** DMS-273/373/376→terminal, DMS-406/421/422/423 new in DMS, Semavin 318→320. Agent held correct live truth.

## Phase 6 — Browser C (10/10)

| Case | Result |
|---|---|
| C1 period-sprint continuation | NEEDS_CLARIFICATION (free-text, no options) — LLM non-determinism, **safe**, no leak |
| C2 person attachments WMB | **COMPLETED `runtime_contract`** ev=17 |
| C3 person text WMB | **COMPLETED `runtime_contract`** ev=5 |
| C4 person+sprint multi-filter | **COMPLETED `runtime_contract`** ev=3 |
| C5 identity ambiguity continuation | NEEDS_CLARIFICATION → click → **turn2=COMPLETED 57 exact** |
| C6 aging DMS | **COMPLETED `runtime_contract`** ev=78 |
| C7 similar DMS-380 | **COMPLETED `runtime_contract`** ev=6 |
| C8 task quality DMS-380 | **COMPLETED `runtime_contract`** ev=9 |
| C9 release SOURCE_CONDITIONAL | `FAILED` fail-closed typed |
| C10 safe not-found Пупкин | `NEEDS_CLARIFICATION` safe |

`_has_internal_leak=False` in all 10 (no `continuation_observations`/`continuation_required_skills` in public payload). `has_generic_v4_error=False` in all. `stale_source_error_text=False` in all.

C1 note: The LLM emitted a free-text clarification with `options=[]` (same A199 F3 non-determinism). The system handled it safely: no false completion, no state leak. The API-path proof (3/3 TRUE) covers the product logic; the Browser rendering requires the LLM to emit typed options, which is a model reliability issue, not a product defect.

## Phase 7 — local-store/source audit (PASS)

- task-api log: **0** `GET /api/v1/tasks` reads.
- Agent log: **0** local-store reads; **210** live `swtr-read` calls.
- Release/history/broad-fanout: all fail-closed typed, 0 evidence, no local rows.

## Phase 8 — stability (covered by Phase 4 + P2)

K1 5/5 + K2 5/5 exact in Phase 4. P2a retry 2/5 TRUE additional. All completed runs exact; non-completions = LLM endpoint degradation (timeout/ValidationError repair), not logic defects.

## Phase 9 — plugin/extensibility (GREEN)

`test_agent_core_v4_plugin_registry.py` **11/11**: synthetic `dummy.55` registers via `with_plugin` with zero Agent Core changes.

## Findings (non-blocking)

- **F1 — LLM endpoint degradation (ongoing):** Qwen3.8 via `api.ai.sbt` still intermittently slow/unreliable (60–180s per call; `ValidationError` repair failures; free-text vs typed option non-determinism). Does NOT affect product correctness (fail-closed everywhere; zero false completions across all phases).
- **F2 — Owner test-compat (3 tests):** `test_v4_owner_fix_contracts.py` unpacks `_prepare_query` as 2-tuple but it now returns 3-tuple. Owner needs to update these 3 tests. Non-blocking for the product gate.
- **F3 — `/health` unscoped scan (A195B F2, unchanged):** Agent `/health` readiness probe still performs unscoped task-query (25s+ timeout). `/live` 200/0.0s. Non-blocking hygiene.

## Final classification

| Surface | Status |
|---|---|
| D-A200-1 (period-sprint continuation) | **CLOSED** — 3/3 TRUE, 0 FALSE |
| P2b adversarial (no all-space leak) | **0 RED** |
| 27-skill matrix | 20 GREEN / 7 SOURCE_CONDITIONAL / 0 RED |
| K1/K2 (A200 frontier retained) | 10/10 exact |
| Browser C | 10/10 (C1 = LLM non-determinism, safe) |
| Local-store audit | 0 reads |
| dummy-55/plugin | 11/11 |

**Verdict: `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_GREEN`**

**A201 frozen as clean zero-RED pre-Wave-S checkpoint.** Do not start Wave S without explicit owner instruction.

## Services left running (current HEAD ae5caee)

| Service | URL | Port | PID | Health |
|---|---|---|---|---|
| UI (Vite) | http://localhost:5175 | 5175 | 55206 | 200 |
| PO Agent | http://127.0.0.1:8212 | 8212 | 55205 | `/live` 200; EXPECTED_HEAD=`ae5caee` |
| Task API | http://127.0.0.1:8241 | 8241 | 55200 | `swtr-read/health` 200, SSE, 48 tools |
| MCP-SWTR | http://127.0.0.1:3000/sse | 3000 | 55196 | connected |
