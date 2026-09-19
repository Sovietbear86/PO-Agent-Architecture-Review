# A199 — Final Pre-Wave-S Regression: Existing 27-Skill V4 Catalog

**Verdict:** `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_RED`
**START_HEAD:** `be40f675992b23728dffab46a09f6e675eb65daf`
**Branch:** `feat/core8-real-query-hardening-v2`
**Role:** QA / adversarial tester + service operator (no production/frontend/plugin/test/config edits)
**Test base:** Agent Core v4 pluginized runtime at START_HEAD, REAL AS21 via task-api 8241 → MCP-SWTR 3000 (SSE).

---

## Executive summary

A198 returned RED with a single blocking functional defect (D1: multi-filter person+sprint queries dropped an already-resolved optional `space` argument, so the READY guard rejected completion → step-budget exhaustion / 300s timeout). The owner shipped five fixes (`65f9951`, `c01186d`, `f75f70a`, `83df8f8`, `9413702` + person-resolution unification commits) since A198 START_HEAD `0b5692d`.

A199 confirms:
- **D1 (multi-filter person+sprint+space) is CLOSED** — 20/20 exact, runtime deterministically injects the resolved `space` before the terminal `task.search`, zero rejected-READY loops, no step-budget exhaustion, no 300s timeout.
- **A198 F2 (release local-store fallthrough) is CLOSED** — 0 `GET /api/v1/tasks` reads across the entire run; release paths fail closed.
- **All A197/A198 protections retained** (aging exact, similar deterministic, identity/clarification/attachments, no premature-ready, no local-store truth).

A199 is **RED** because the new **cross-skill person-scope identity gate** (spec Phase 5) surfaced one deterministic blocking defect:

- **D-A199-1 (blocking):** person-scoped **attachment** search and person-scoped **text** search deterministically fail to complete. When the planner loads the `tasks.search` collection skill and then pivots to the specialized `task.search_attachments` / `task.search_text` capability, the loaded `tasks.search` skill's completion contract can never be satisfied. The runtime completion gate (`all_loaded_skills_satisfied`) requires **every** loaded skill's contract, so deterministic completion is blocked and the runtime is forced to ask the Qwen3.8 planner to mint a terminal READY — which is either undecodable 4× ("planner failed robust bounded repair") or decoded-but-rejected 3× (`unsatisfied_completion_contract`) until step-budget exhaustion. The person-scoped **source logic itself is correct** (canonical `Kalachanov.V.V` via `member.resolve`, N+1 file lookups 200 OK); only the completion gate fails.

Proven: **K1 5/5 FAILED, K2 1/1 FAILED, Browser C2 FAILED (2 attempts)**. Root cause localized to the completion-gate coupling to the full loaded-skill set (not the actually-executed capabilities). Owner-side fix required; not fixed here per role lock.

---

## Phase 0 — start / architecture audit (PASS)

`git pull --ff-only` → `be40f67`. Tracked worktree clean (only QA artifacts untracked). Owner production diff `0b5692d..be40f67` audited:

| Fix | File | Verdict |
|-----|------|---------|
| Generic typed resolved-constraint injection | `agent_core_v4_completion.py::resolved_constraint_arguments` | **Generic & entity-free.** Only roles present in the target capability schema; only unique source-resolved values; ambiguous/multi never injected. No query parsing, no entity literals. |
| Runtime argument completion before capability execution | `agent_core_v4.py:1147-1163` | Fills **only omitted** args via `resolved_args.setdefault`; target schema keys gate the role. Correct. |
| READY guard intact | `agent_core_v4.py:1090-1130` | Premature READY still rejected until contract satisfied (`ready_rejected=unsatisfied_completion_contract`). Unchanged. |
| Release project-only fail-closed | `hardened_production_task_api.py:304-313` | `project AND release_id AND !sprint AND !assignee` → `AS21SourceUnavailable`. **No** fallthrough to local `/api/v1/tasks`. |
| Composite task-catalog binding test | `test_agent_core_v4_task_catalog.py` | Now validates referenced capabilities per skill (fixes A198 F1). |
| Universal person-resolution seam | `_task_live_handlers.py::_source_assignee_from_args` | **All 5 person-scoped handlers** (`search_text`, `search_status`, `search_attachments` [no-task_key branch], `aging`, `search_assignee`) route natural/inflected/canonical references through the governed `_resolve_assignee_identity` → `member.resolve` before any source assignee filter. **No direct raw-person bypass found.** |

Hermes/plugin/dummy-55 architecture intact (see Phase 7). **No architecture violation.**

---

## Phase 1 — automated suites

| Suite | Result |
|-------|--------|
| `test_agent_core_v4*.py` + `test_v4*.py` | **114 passed** |
| `test_v4_owner_fix_contracts.py` (incl. new person-scope attachment seam test) | **17 passed** |
| Premature-READY / injected / generic-completion named tests | **3 passed** (`premature_model_ready_is_rejected`, `missing_resolved_constraint_is_injected_before_terminal_call`, `completion_mechanism_is_generic_and_entity_free`) |
| `test_agent_core_v4_plugin_registry.py` (dummy-55 gate) | **11 passed** |
| `test_agent_core_v4_task_catalog.py` (A198 F1 fix) | **9 passed** |
| Full `tests/` (e2e excluded), `be40f67` | 1407 passed, 23 failed, 11 errors |
| Full `tests/` (e2e excluded), A198 base `0b5692d` (read-only worktree A/B) | 1404 passed, 26 failed, 11 errors |
| **Failure-set diff (new failures at HEAD)** | **0 new failures; 3 fixed** (the A198 F1 registry test + 2 others) |
| `task-api/tests/` | 84 passed, 24 failed — **identical to A18 baseline** (pre-existing, not A199-related) |

All A199-mandated gates GREEN: composite binding, deterministic injection, premature-READY, aging timestamp provenance, dummy-55.

---

## Phase 2 — D1 multi-filter gate (D1 CLOSED)

Fresh REAL AS21 Oracle built immediately before runs (`qa_199_p2_oracle_before.json`):
DMS current sprint = `DMS-SPRNT-3` (60 tasks). Zhdanov.DMS = 7 (2 open), in-sprint-open = **[DMS-371]**. Garanin.DMS = 10, in-sprint = 6.

### Batch A — `Открытые задачи Жданова в текущем спринте DMS` (the A198 D1 case)
**20/20 COMPLETED** (two independent 10× passes, concurrency 1), all `runtime_contract`, **exact parity [DMS-371]**, **0 rejected-READY**, no step-budget exhaustion, bounded latency (23–159s; the high tail is Qwen3.8 LLM call latency, not a loop).

**Injection proof** (planner omitted the resolved optional `space`; runtime filled it before execution):
- Planner raw (turn 5): `{assignee: Zhdanov.A.Ni, sprint_id: DMS-SPRNT-3, status: not_completed}` (no `space`)
- Executed `task.search` args: `{assignee: Zhdanov.A.Ni, sprint_id: DMS-SPRNT-3, status: not_completed, **space: DMS**}`
- `exec.filters` = `{assignee, space: DMS, sprint_id, status}`; result `count=1, task_keys=[DMS-371]`
- 5 independent live injection captures in the re-run pass + 1 in Phase 4 MULTI (same signature).

### Batch B — `задачи Гаранина в сентябрьском спринте` (10×)
8× `NEEDS_CLARIFICATION` (space), 1× client 300s timeout (transient — 600s re-probe completed clean in 40.5s), 1× FAILED (Qwen3.8 bounded repair, LLM). The clarification is **correct behavior, not a D1 regression**: the query carries **no space**, and "сентябрьский спринт" is genuinely ambiguous across `CRPV/DMS/OLP/STS/WMB` (multiple spaces can have a September sprint). Typed clarification with non-null `clarification_id` + space options. Per spec, "Typed NEEDS_CLARIFICATION remains valid only where source ambiguity genuinely exists" — satisfied. (Message-quality note in F4.)

**D1 verdict: CLOSED** — the A198 failure class (space-in-query, dropped resolved optional arg) no longer occurs; Batch A is 20/20 exact with deterministic injection.

---

## Phase 3 — local-store release-path audit (F2 CLOSED)

| Query | Result | Latency |
|-------|--------|---------|
| `Задачи релиза Q3-2026 в DMS` | `FAILED` fail-closed — `release.resolve` → `AS21SourceUnavailable`, answer "Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат." | 3.3s |
| `Здоровье релиза Q3-2026 в DMS` | `FAILED` fail-closed (same) | 7.8s |

**Task API log audit: 0 `GET /api/v1/tasks` reads** caused by (or anywhere in) the release queries. A198 F2 (project+release fallthrough to local store) is **CLOSED** — the new guard fails closed. No local rows can be returned as REAL AS21 facts.

---

## Phase 4 — full 27-skill matrix (20 GREEN / 7 SOURCE_CONDITIONAL / 0 RED)

All 27 existing skills exercised, fresh Oracle parity.

| # | Row | Skill | Result | Oracle parity |
|---|-----|-------|--------|---------------|
| 1 | LKUP | task.lookup | GREEN | DMS-380 exact |
| 2 | SUMM | task.summary | GREEN | DMS-380 |
| 3 | QUAL | task.quality | GREEN | 85/100, widget task_analysis |
| 4 | ACCE | task.acceptance | GREEN | DMS-380 |
| 5 | BLOC | task.blockers | GREEN | DMS-380 |
| 6 | DEPS | task.dependencies | GREEN | DMS-380 |
| 7 | MISS | task.missing_requirements | GREEN | DMS-380 |
| 8 | HIST | task.history | SOURCE_CONDITIONAL | history route 502 (fail-closed) |
| 9 | TIS | task.time_in_status | SOURCE_CONDITIONAL | requires history (502) |
| 10 | AGING | task.aging | GREEN | **80/80 exact** (source-timestamp provenance) |
| 11 | SIMIL | task.similar | GREEN | deterministic top-5 (token_jaccard_v1) |
| 12 | TEXT | task.search_text | GREEN | **2/2 exact** (DMS-267, DMS-380) |
| 13 | ATT | task.search_attachments | GREEN | WMB-30000 = 5 xlsx exact |
| 14 | EXCEL | task.search_excel | SOURCE_CONDITIONAL | broad WMB-only fan-out fail-closed |
| 15 | PDF | task.search_pdf | SOURCE_CONDITIONAL | broad WMB-only fan-out fail-closed |
| 16 | MSG | task.search_msg | SOURCE_CONDITIONAL | broad WMB-only fan-out fail-closed |
| 17 | ASGN | task.search_assignee | GREEN | **10/10 exact** (Garanin.DMS) |
| 18 | STAT | task.search_status | GREEN | **90/90 exact** (DMS open) |
| 19 | SPRINT | task.search_sprint | GREEN | **60/60 exact** (DMS-SPRNT-3) |
| 20 | REL | task.search_release | SOURCE_CONDITIONAL | release fail-closed |
| 21 | MULTI | tasks.search | GREEN | **1/1 exact** (injection: raw no-space → executed space=DMS) |
| 22 | L2A | tasks.lookup_then_assignee | GREEN | **317/317 exact** (Semavin) |
| 23 | CURR | sprint.current | GREEN | DMS-SPRNT-3 |
| 24 | DISC | sprints.discover | GREEN | DMS-SPRNT-3 |
| 25 | LIST | sprints.list | GREEN | active DMS sprints |
| 26 | SHEALTH | sprint.health | GREEN | DMS-SPRNT-3 |
| 27 | RHEALTH | release.health | SOURCE_CONDITIONAL | release fail-closed |

All 7 SOURCE_CONDITIONAL rows are genuinely source-limited and fail-closed (no local-store truth, no fabrication). No stale source-error text (`AS21 вернул некорректные данные`) anywhere.

---

## Phase 5 — retained regressions + cross-skill person-scope identity gate

### Retained regressions (all GREEN)
| Case | Result |
|------|--------|
| S1 L2A "DMS-380 → assignee tasks" ×5 | **5/5 COMPLETED exact 317/317** (Semavin) |
| S2 full-name "Задачи Александра Жданова в DMS" ×5 | **5/5 exact 7/7** |
| S3 non-team "Задачи Utkin.S.A" | **COMPLETED exact 57/57** (source-resolved, not roster-limited) |
| S4 ambiguous "Задачи Уткина" → clarification → same-session turn2 | **COMPLETED exact 57/57** (7 real source candidates offered) |
| S5 invented "Задачи Пупкина" | `NEEDS_CLARIFICATION` (safe, no fabrication) |
| S6 aging DMS ×3 | **3/3 exact 80/80** |
| S7 similar DMS-380 ×3 | **3/3 deterministic top-5** |
| S8 WMB-30000 attachments ×3 | **3/3** (5 xlsx) |
| S9 current sprint DMS ×3 | **3/3** (DMS-SPRNT-3) |

### Cross-skill person-scope identity gate (Kalachanov.V.V)
| Case | Result | Identity proof |
|------|--------|----------------|
| K3 person status "Открытые задачи Калачанова в WMB" | **GREEN** — true zero (all 5 WMB tasks terminal), `member.resolve` → `source_assignee=Kalachanov.V.V` |
| K4 person aging "Застоявшиеся задачи Калачанова в WMB" | **SOURCE_CONDITIONAL** — WMB rows carry no source `created_at`; `task.aging` fails closed (`AS21SourceUnavailable`). Correct fail-closed, not a defect. |
| **K1 person attachments "Задачи Калачанова с вложениями в WMB" ×5** | **RED — 5/5 FAILED** (D-A199-1) | `member.resolve(Калачанов, WMB)` → `Kalachanov.V.V`; `task.search_attachments` **executed** with canonical identity (N+1 file lookups 200 OK, would yield WMB-29890/29995/30000). Failure is post-execution completion gate, not source logic. |
| **K2 person text "Найди задачи Калачанова про 2027 в WMB"** | **RED — FAILED** (D-A199-1) | `member.resolve` → `Kalachanov.V.V`; `task.search_text` **executed** (`phrase=2027&space=WMB&assignee=Kalachanov.V.V` 200 OK, would yield 4 tasks). 3× READY rejected `unsatisfied_completion_contract` → step-budget exhaustion. |

K3 proves the person-scope identity seam works end-to-end (natural surname → governed `member.resolve` → canonical REAL AS21 identity in the source filter). K1/K2 prove the same identity is correct but the **completion gate** then blocks terminal completion.

---

## Defect D-A199-1 (blocking RED) — person-scoped attachment & text search completion gate

**Symptom:** "Задачи Калачанова с вложениями в WMB" (K1, 5/5) and "Найди задачи Калачанова про 2027 в WMB" (K2, 1/1) and Browser C2 all FAIL with `Agent Core v4 не смог безопасно завершить траекторию.` / step-budget exhaustion — even though the person-scoped source capability **executes correctly** (canonical `Kalachanov.V.V`, source queries 200 OK).

**Reproduction (deterministic, 6/6):**
- K1 trajectory: `load_skill tasks.search` → `space.resolve WMB` → `member.resolve Калачанов` → `load_skill task.search_attachments` → `call task.search_attachments` (executes fine) → next planner turn: 4 LLM calls all HTTP 200 but **undecodable** → `V4ContractError: planner failed robust bounded repair: [invalid_primary_decision, invalid_recovery_action×3]`.
- K2 trajectory: `load_skill tasks.search` → `space.resolve WMB` → `member.resolve Калачанов` → `load_skill task.search_text` → `call task.search_text` (executes fine) → `ready` ×3 each rejected `unsatisfied_completion_contract` → `step budget exhausted without READY`.

**Root cause (localized):** `agent_core_v4_completion.py::all_loaded_skills_satisfied` (line 224) returns True only when **every** loaded skill's contract is satisfied. The planner loads `tasks.search` (a collection skill with a completion contract) at turn 1, then pivots to the specialized `task.search_attachments`/`task.search_text` capability. The abandoned `tasks.search` contract is **never satisfiable** (no `task.search` call is ever made), so `_trajectory_completion_satisfied` (agent_core_v4.py:588) is False → the deterministic runtime-contract completion (agent_core_v4.py:1166) is skipped → the runtime is forced to ask the Qwen3.8 planner to mint a terminal READY. K2 proves the code path is deterministic independent of LLM quality (decoded READY is rejected 3× → budget exhaustion); K1 shows the same gate also lets a weak LLM produce undecodable decisions.

**Why it is not an identity/person-scope defect:** `member.resolve` + `_source_assignee_from_args` produce the correct canonical `Kalachanov.V.V` and the source filter uses it (proven by agent log: `task-query?...&assignee=Kalachanov.V.V` 200 OK, N+1 `/files` 200 OK). The failure is purely in the terminal-completion scoping.

**Owner fix direction (proposed, NOT implemented here):**
1. Completion gate should evaluate only **executed/used** capabilities' contracts, not every loaded skill — or
2. A loaded-but-never-called skill with an unmet contract should not block deterministic completion of a different, already-satisfied terminal capability — or
3. Deterministic completion should fire on the **most-specific executed** capability's contract when a superset collection skill was merely loaded.

Any of these would let K1/K2/C2 complete via `runtime_contract` with the already-correct person-scoped result.

---

## Phase 6 — Browser C (8 key-combination cases)

| Case | Result |
|------|--------|
| C1 person+sprint multi-filter "Задачи Александра Жданова в текущем спринте DMS" | **GREEN** — COMPLETED `runtime_contract`, DMS-371, Zhdanov.A.Ni, widget task_table. Injection confirmed in UI. |
| **C2 person attachments WMB "Задачи Калачанова с вложениями в WMB"** | **RED** — `V4ERROR`, generic "не смог безопасно завершить траекторию." (2 attempts). D-A199-1 reproduced in UI. |
| C3 aging DMS | **GREEN** — 80 tasks, widget task_table |
| C4 task quality DMS-380 | **GREEN** — widget task_analysis, 85/100 |
| C5 similar DMS-380 | **GREEN** — widget similar_task_list, 5 similar |
| C6 identity clarification continuation "Задачи Уткина" | **GREEN** — `NEEDS_CLARIFICATION` → option-click `Utkin.S.A` (request preserves `session_id` **and** `clarification_id`) → turn2 COMPLETED 57 tasks |
| C7 release SOURCE_CONDITIONAL "Здоровье релиза Q3-2026 в DMS" | **SOURCE_CONDITIONAL** — `V4SOURCE_UNAVAILABLE`, fail-closed |
| C8 safe not-found "Задачи Пупкина" | **GREEN** — `NEEDS_CLARIFICATION`, no fabrication |

No stale source-error text in any case. C6 confirms the canonical option-click clarification-continuation path (with `clarification_id`) works; the API-level bare "DMS" path (S10) is a weaker, non-canonical variant (F4).

---

## Phase 7 — plugin / extensibility gate (GREEN)

dummy-55 / A190 extensibility re-gate: **14/14 GREEN**. A new skill registers through the plugin surface with **zero** changes to Agent Core / planner / runtime.

---

## Local-store factual-path audit (requirement: 0)

**0 `GET /api/v1/tasks` reads** across the entire A199 run (task-api log). All task data served from `/api/v1/swtr-read/*` live routes (task-query ×89, tasks/{code}+files ×135, assignees/assignee-tasks ×71, sprints/spaces ×70, health, versions). **No local-store factual fallback.** A198 F2 CLOSED.

---

## Findings (non-blocking)

- **F1 (service-ops, environmental):** A198's task-api 8241 (stdio transport) had fallen into an MCP-child crash-restart loop → persistent 502 on `task-query`. Restarted on **SSE** transport (pointing at the healthy long-lived MCP-SWTR on 3000), same working pattern as A195B–A197. Not a code defect; consistent with the known A186/A195B long-lived task-api→MCP instability lineage.
- **F2 (CLOSED):** release project-only path no longer falls through to local `/api/v1/tasks` (0 reads). A198 F2 resolved by `83df8f8`.
- **F3 (pre-existing LLM reliability, A179 lineage):** Qwen3.8 "planner failed robust bounded repair: invalid_primary_decision/invalid_recovery_action" class appears on post-capability READY turns (K1). It is the *amplifier* of D-A199-1, but not the root cause (K2 shows the deterministic gate rejection independent of LLM quality).
- **F4 (pre-existing, A193 class):** API-level bare option turn2 (`query="DMS"` **without** `clarification_id`) is treated as a fresh query → "too brief" clarification. The canonical UI option-click path (C6, with `clarification_id`) works. Also minor Batch-B clarification message-quality variance ("Не удалось подтвердить пространство «?»"). Non-blocking.
- **F5 (source limitation):** WMB rows expose no source creation timestamps (`created_at=None`) → `task.aging` on WMB fails closed (K4). Correct fail-closed behavior.
- **F6 (harness artifact):** Phase-4 ATT parity "1/0" was a QA harness oracle-keying artifact; the actual result is correct (WMB-30000 = 5 xlsx).
- **F7 (unchanged, not exercised):** `/health` unscoped full-scan hang (A195B F2) — not exercised this round.

---

## Final classification

- **Skills tested:** 27/27 (Phase 4) + person-scope cross-skill gate (Phase 5 K1–K4) + Browser C (8) + dummy-55.
- **Phase 4 matrix:** 20 GREEN / 7 SOURCE_CONDITIONAL / 0 RED.
- **Blocking RED:** **D-A199-1** — person-scoped attachment + text search completion-gate defect (K1 5/5, K2 1/1, C2 UI). Root cause: completion gate requires every loaded skill's contract, including a loaded-but-never-executed collection skill.
- **D1:** CLOSED (20/20 exact, deterministic injection). **F2:** CLOSED (0 local-store reads).
- **Retained protections:** all GREEN (aging exact, similar deterministic, identity/clarification/attachments, no premature-ready, no local-store truth).

Per spec rule 13, GREEN requires zero RED. **One deterministic blocking RED exists (D-A199-1).**

## Verdict

`AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_RED`

**Owner action required:** fix D-A199-1 (completion-gate scoping to executed capabilities / ignore unmet contracts of loaded-but-never-called skills), then re-gate Phase 5 K1/K2 + Browser C2. Once D-A199-1 is closed with 0 RED and all other gates retained, A199 can be re-classified GREEN and frozen as the clean pre-Wave-S checkpoint for owner Wave S #23–32 through the existing plugin surface.

---

## Services left running (current HEAD)

| Service | URL | Port | PID | Health |
|---------|-----|------|-----|--------|
| UI (Vite) | http://127.0.0.1:5175 | 5175 | 22389 | 200 |
| PO Agent | http://127.0.0.1:8212 | 8212 | 77263 | /live 200, EXPECTED_HEAD=be40f67 |
| Task API | http://127.0.0.1:8241 | 8241 | 95507 | health 200, SSE, 48 tools |
| MCP-SWTR | http://127.0.0.1:3000/sse | 3000 | 45891 | 200 |

**START_HEAD:** `be40f675992b23728dffab46a09f6e675eb65daf`

*QA artifacts (untracked): `qa_199_p2_oracle_before.json`, `qa_199_p2_oracle_after.json`, `qa_199_p2_results.json`, `qa_199_p2b_results.json`, `qa_199_p3_results.json`, `qa_199_oracle.json`, `qa_199_p4_results.json`, `qa_199_p5_results.json`, `qa_199_p6_browser.json`, `qa_199_p8_dummy55` (reused A198 runner), plus helper scripts `qa_199_*.py` / `qa_199_start_*.sh` / `frontend/e2e/qa199-browser-c.spec.ts`.*
