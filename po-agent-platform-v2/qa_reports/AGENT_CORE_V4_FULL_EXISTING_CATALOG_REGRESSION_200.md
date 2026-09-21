# A200 — Agent Core v4 Full Existing-Catalog Regression (Pre-Wave-S Zero-RED Freeze Gate)

**Date:** 2026-09-21
**Verdict:** `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_RED`
**START_HEAD:** `3d97c9a3d4442f933fe0ab368a2308b90e691f17`
**A199 base (diff since):** `be40f67`
**Owner fix under gate:** `da24608` (generic completion frontier) + `4156914` (Agent Core uses active frontier) + `f359ae2` (supersession unit tests)
**Rollback checkpoint:** `0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`

## Executive summary

The owner's completion-frontier fix is **certified at its own gate**: the A199 blocking defect D-A199-1 (person-scoped attachment/text search completion gate) is **CLOSED** — K1 `Задачи Калачанова с вложениями в WMB` **10/10** and K2 `Найди задачи Калачанова про 2027 в WMB` **10/10** COMPLETED `runtime_contract` with exact fresh-Oracle parity, governed `member.resolve`, canonical `Kalachanov.V.V` source identity, zero rejected-READY, zero bounded-repair loops.

The full 27-skill matrix re-ran with **20 GREEN / 7 SOURCE_CONDITIONAL / 0 RED** (all parity deltas proven live source drift), local-store audit **0** factual local reads, Browser C **10/10**, dummy-55 **11/11**.

**Sole blocking RED = D-A200-1**: the Phase-4 period-sprint clarification/continuation case (`задачи Гаранина в сентябрьском спринте` → typed space clarification → `DMS` with `clarification_id`) produced a **user-visible false completion 2/2 fresh**: `COMPLETED`/`runtime_contract` after `sprints.discover` + `space.resolve` + `sprint.search` only — `task.search` never executed, 0 task evidence, and the answer text itself admits the requested task list was not retrieved. A second sub-variant (1×): turn-1 direct `COMPLETED` via `task.search_assignee` with **no space/sprint filter** (all-space 23-task DMS/OLP/STS set). Root cause: Qwen3.8 planner non-deterministically routes the (re)planned task intent to sprint-identity/assignee-only skills whose structural contracts are satisfied without `task.search`; the semantic-agnostic frontier then accepts. Pre-existing class (A199 F3 "completion-gate hole"); **not introduced by the frontier fix** (fix works correctly everywhere else). STOP per A200 rules: no Wave S.

Secondary (non-blocking): the Qwen3.8 LLM endpoint was in sustained degradation from ~10:30 local — 11/31 Phase-8 runs failed as `planner failed robust bounded repair: ['ReadTimeout'×4]` (agent 240s LLM client timeout → fail-closed) or 300s client timeouts; zero logic errors, zero fabrication, all completed runs exact.

## Phase 0 — start / architecture audit (PASS)

- `git pull --ff-only` — already up to date; `START_HEAD 3d97c9a`. Tracked worktree carried only pre-existing QA-run artifacts (`GIGACODE.md` memory, `.po_agent/learned_policies.json` runtime file, `vite.config.ts` QA proxy edit) — no owner code pending; untracked files are QA scripts/reports only.
- Owner diff `be40f67..3d97c9a` (code): `agent_core_v4.py` (2 lines: import + call-site switch to `completion_frontier_satisfied`), `agent_core_v4_completion.py` (new `completion_frontier_skills`/`completion_frontier_satisfied`, 63 lines), `test_agent_core_v4_completion_contract.py` (+3 tests), docs. **Zero** task-api/frontend/plugin changes.
- Frontier logic review — all invariants hold structurally:
  - generic & entity-free: only `capability_id`/`skill_id` structure consulted; no query text, no entity literal, no skill-id literal branch (only `skill_id == latest`);
  - latest loaded contracted skill always on frontier → cannot auto-complete without its requirement (unit test 3);
  - earlier skill with an observed required capability stays required (unit test 2);
  - earlier loaded-but-unengaged skill = superseded, may not poison (unit test 1);
  - empty frontier (latest uncontracted) → deterministic completion unavailable → normal planner path (fail-closed).
- READY safety guard intact (A198 `covers_resolved_constraints` code untouched; `premature_model_ready_is_rejected` GREEN).
- Person-scoped handlers untouched by diff (A199 Phase-0 proof of `_resolve_assignee_identity` seam retained); live K1/K2 show `member.resolve` (REAL_AS21) + `source_assignee=Kalachanov.V.V`.
- No `/api/v1/tasks` references in harness code; plugin/dummy-55 invariant re-verified in Phase 1/9.

## Phase 1 — automated suites (GREEN)

| Suite | Result |
|---|---|
| `test_agent_core_v4*.py` + `test_v4*.py` | **117 passed** (A199: 114; +3 new frontier tests) |
| Named frontier proofs | **3/3**: `ignores_unengaged_superseded_skill`, `retains_earlier_engaged_skill`, `latest_unexecuted_skill_still_blocks` |
| Premature-READY / injection / generic / marker | **4/4** (`premature_model_ready_is_rejected`, `missing_resolved_constraint_is_injected`, `completion_mechanism_is_generic_and_entity_free`, `runtime_contract_completion_marker`) |
| `test_agent_core_v4_plugin_registry.py` (dummy-55) + `test_agent_core_v4_task_catalog.py` | **20 passed** (11 + 9) |
| Full `tests/` (e2e excluded) | 1409 passed, 24 failed, 12 skipped, 11 errors — **zero V4/plugin/completion-related**; failure set = pre-existing environmental (real-LLM integration, live-service e2e, core8 hardening, historical intelligence) |
| `task-api/tests/` | 83 passed, 25 failed — identical pre-existing A18/A199 failure classes (s21 live-MCP integration, local-fixture api/repository/service); owner diff touches **zero** task-api files, so any delta is environmental |

## Phase 2 — A199 blocking-defect re-gate (D-A199-1 CLOSED)

Fresh REAL AS21 oracle (2026-09-21 09:22): Kalachanov WMB = 5 tasks `[WMB-29242, 29830, 29890, 29995, 30000]`; K1 with-attachments = 3 `[WMB-29890 (1 pdf), WMB-29995 (10 files), WMB-30000 (5 xlsx)]`; K2 phrase-2027 = 4 `[WMB-29830, 29890, 29995, 30000]`.

| Gate | Result |
|---|---|
| **K1** `Задачи Калачанова с вложениями в WMB` ×10 | **10/10 COMPLETED `runtime_contract`**, 3/3 exact every run, `member.resolve` in trajectory all runs, `source_assignee=Kalachanov.V.V` REAL_AS21, skills `[tasks.search, task.search_attachments]` — broad skill loaded but **superseded**, specialized skill completed deterministically, **0** ready-rejections, **0** repair loops, prepass=0, 48–116s |
| **K2** `Найди задачи Калачанова про 2027 в WMB` ×10 | **10/10 COMPLETED `runtime_contract`**, 4/4 exact every run, same governance, skills `[tasks.search, task.search_text]`, **0** rejections, 35–85s |
| Negative frontier controls (synthetic) | **3/3** unit (Phase 1) + live: 0 false completions across 20/20 K1/K2 runs |

The exact A199 failure signature (broad `tasks.search` loaded → pivot to specialized skill → `unsatisfied_completion_contract` rejection loop) is **gone**.

## Phase 3 — cross-skill person-scope gate (GREEN)

| Case | Result |
|---|---|
| P3a person status `Открытые задачи Калачанова в WMB` | **GREEN** — true zero (all 5 WMB tasks terminal), 0 task evidence, no fabrication |
| P3b person aging `Застоявшиеся задачи Калачанова в WMB` | **SOURCE_CONDITIONAL** — `FAILED` fail-closed typed ("Источник AS21 временно недоступен…"), 0 evidence (WMB rows carry no source `created_at`; A199 K4 same) |
| P3c `task.search_assignee` `Задачи Родиона Гаранина в DMS` | **10/10 exact** (fresh oracle), canonical |
| P3d non-team unique `Задачи Utkin.S.A` | **57/57 exact** (source-resolved, not roster-limited) |
| P3e ambiguous `Задачи Уткина` | **NEEDS_CLARIFICATION** 7 real source candidates → same-session continuation → **COMPLETED 57/57 exact** |
| P3f invented `Задачи Пупкина` | **NEEDS_CLARIFICATION** typed, safe, no fabrication |

Every person-scoped capability resolved through governed source-backed resolution; no raw-surname-as-assignee bypass observed.

## Phase 4 — multi-filter retained gate (P4a/P4b GREEN; P4c RED)

| Case | Result |
|---|---|
| P4a `Открытые задачи Жданова в текущем спринте DMS` ×10 | **10/10 COMPLETED `runtime_contract` [DMS-371]** exact, deterministic resolved-constraint injection retained |
| P4b `Задачи Александра Жданова в текущем спринте DMS` ×5 | **5/5 [DMS-371]** exact |
| P4c period-sprint clarification/continuation | **RED — D-A200-1** (below) |

### Defect D-A200-1 (blocking RED) — period-sprint continuation false completion

**Reproduction (fresh, this run):**
1. turn1 `задачи Гаранина в сентябрьском спринте` → `NEEDS_CLARIFICATION` (typed, non-null `clarification_id`, options `[CRPV, DMS, OLP, STS, WMB]`, "Не удалось подтвердить пространство «?»") — the space ambiguity is **genuine** (period sprint exists in multiple spaces; A199 classified this typed clarification as correct).
2. turn2 `{query: "DMS", session_id, clarification_id}` (identical payload shape to the UI) → **`COMPLETED` `runtime_contract`** with trajectory `sprints.discover → space.resolve → sprint.search → ready`; **`task.search` never executed; 0 task evidence**; answer: "Спринт за сентябрь в DMS найден: DMS-SPRNT-3… К сожалению, в доступных данных нет информации о задачах Гаранина в этом спринте — не удалось получить список задач…" — **the agent completed while admitting the requested data is missing**. Reproduced **2/2** (continuation probe + classifier probe).
3. Sub-variant B (1×, same query class): turn1 **direct `COMPLETED`** via `task.search_assignee` — log shows `task-query?assignee=Garanin.R.V` with **no space/sprint filter** → 23 tasks across DMS/OLP/STS presented for a DMS-September-sprint request.

**Expected:** turn2 `COMPLETED` with `task.search(assignee=Garanin.R.V, sprint=DMS-SPRNT-3, space=DMS)` → 6 exact keys `[DMS-243, 402, 405, 412, 414, 93]` (achieved 1/1 on sep-19 same-HEAD run; the correct path exists).

**Class distribution (fresh):** turn1: typed-options clarification (majority), free-text empty-options clarification 2×, direct-COMPLETED 1×, client-300s timeouts 6× (environmental), FAILED robust-repair 1× (sep-19). turn2 continuation: **FALSE 2/2 fresh** vs TRUE 1/1 (sep-19).

**Root cause (localized):**
- (a) Planner (Qwen3.8) non-deterministically routes the restored task-intent plan to `sprints.discover` (sprint-identity-only skill) and stops after `sprint.search`, or to `task.search_assignee` dropping the space/sprint constraints, instead of loading `tasks.search` and executing the constrained terminal call.
- (b) The completion frontier — **by design** structural and semantic-agnostic — accepts `runtime_contract` when the latest loaded contracted skill's requirement is structurally satisfied (`sprints.discover` requires only a `sprint.search` observation with `sprint_id`). It cannot see that the user's intent was a task collection.
- This is the pre-existing "completion-gate hole" class documented in **A199 F3** ("planner_ready after only member.resolve, primary task.search never invoked — completion-gate hole, pre-existing class, track before Wave S"). **Not introduced by the A200 frontier fix**, which is verified correct in all other scenarios (20/20 K1/K2, 27-row matrix, 0 spurious supersessions).

**Owner fix direction (not implemented, QA role locked):** make the deterministic completion gate intent-aware at continuation boundaries without becoming semantic — e.g. (1) on a typed-clarification continuation, re-execute the original plan with the confirmed constraint deterministically injected (the `resolved_constraint_arguments` machinery already exists) instead of a fresh planner skill-selection; and/or (2) require the continuation frontier to cover the original resolved-constraint set (person + period-sprint ⇒ a `covers_resolved_constraints` terminal `task.search` must be observed before `runtime_contract`). Deterministic re-execution is preferred over planner-side biasing for reliability.

## Phase 5 — complete 27-skill regression (20 GREEN / 7 SOURCE_CONDITIONAL / 0 RED)

Fresh matrix (one run/row; high-risk rows re-verified in Phases 2/4/8). Parity deltas below all **proven live source drift** (verified per-row against the live source after the batch):

| # | Row | Skill | Result | Parity / notes |
|---|---|---|---|---|
| 1 | LKUP | task.lookup | GREEN | DMS-380, runtime_contract |
| 2 | SUMM | task.summary | GREEN | DMS-380 (planner routed via task.lookup, source-accurate) |
| 3 | QUAL | task.quality | GREEN | DMS-380 |
| 4 | ACCE | task.acceptance | GREEN | DMS-380 |
| 5 | BLOC | task.blockers | GREEN | DMS-380 |
| 6 | DEPS | task.dependencies | GREEN | DMS-380 |
| 7 | MISS | task.missing_requirements | GREEN | DMS-380 |
| 8 | HIST | task.history | SOURCE_CONDITIONAL | history route 502, fail-closed typed |
| 9 | TIS | task.time_in_status | SOURCE_CONDITIONAL | requires history, fail-closed typed |
| 10 | AGING | task.aging | GREEN | 79 = live-correct set at run time (oracle 80 − DMS-373/DMS-376 which went `done` during the run + DMS-404 crossing the 7-day boundary: created 2026-09-14T07:45:59Z) |
| 11 | SIMIL | task.similar | GREEN | deterministic top-5 |
| 12 | TEXT | task.search_text | GREEN | **2/2 exact** (DMS-267, DMS-380) |
| 13 | ATT | task.search_attachments | GREEN | WMB-30000 = 5 xlsx exact (count-based parity per A199 convention) |
| 14 | EXCEL | task.search_excel | SOURCE_CONDITIONAL | broad WMB-only fan-out fail-closed typed |
| 15 | PDF | task.search_pdf | SOURCE_CONDITIONAL | same |
| 16 | MSG | task.search_msg | SOURCE_CONDITIONAL | same |
| 17 | ASGN | task.search_assignee | GREEN | 11 during batch = correct live truth at run time (DMS-422 was assigned to Garanin then); **re-probe 2/2 = 10/10 exact** after reassignment to Semavin |
| 18 | STAT | task.search_status | GREEN | 90/90 count; key deltas = verified drift (−DMS-373/376 →`done`, +DMS-421 `pause`/+DMS-422 `progress` new) |
| 19 | SPRINT | task.search_sprint | GREEN | 61 = 60 + DMS-421 (new, in DMS-SPRNT-3) |
| 20 | REL | task.search_release | SOURCE_CONDITIONAL | release source unavailable, fail-closed typed |
| 21 | MULTI | tasks.search | GREEN | **1/1 exact [DMS-371]** (injection retained) |
| 22 | L2A | tasks.lookup_then_assignee | GREEN | **318/318 exact** (Semavin at run time; 319 by Phase 8 = +1 drift) |
| 23 | CURR | sprint.current | GREEN | DMS-SPRNT-3 (uncontracted skill → `planner_ready` by catalog design) |
| 24 | DISC | sprints.discover | GREEN | DMS-SPRNT-3 |
| 25 | LIST | sprints.list | GREEN | active DMS sprints |
| 26 | SHEALTH | sprint.health | GREEN | DMS-SPRNT-3 |
| 27 | RHEALTH | release.health | SOURCE_CONDITIONAL | release fail-closed typed |

**Drift ledger (all verified live after the batch):** DMS-373 `done`, DMS-376 `done` (both were open at oracle time); DMS-421 new `pause` (in sprint, unassigned); DMS-422 new `progress` (Semavin; was transiently Garanin during the ASGN row); Semavin 317→318→319 across the run; DMS-404 crossed the 7-day aging boundary 2026-09-21 ~07:46 UTC. Agent held correct live truth in every case.

## Phase 6 — local-store / source audit (PASS)

- task-api log: **0** `GET /api/v1/tasks` (local store) reads over the entire run.
- Agent log: **0** local-store reads via task-api; **302** outbound calls, **all** `/api/v1/swtr-read/*` (live source).
- Release routes fail closed when the live release source is unavailable (REL, RHEALTH, EXCEL/PDF/MSG broad fan-outs, HIST/TIS): typed "Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат.", 0 evidence, no local rows, no REAL_AS21 mislabeling.

## Phase 7 — Browser C (10/10)

| Case | Result |
|---|---|
| C1 person attachments WMB (K1) | **COMPLETED `runtime_contract`**, 17 evidence, V4 result rendered — **no generic V4 ERROR** |
| C2 person text 2027 WMB (K2) | **COMPLETED `runtime_contract`**, 5 evidence, rendered |
| C3 person status WMB | **true zero rendered** ("открытых задач нет — найдено 0") |
| C4 person+sprint multi-filter | **COMPLETED `runtime_contract` [DMS-371]** exact |
| C5 aging DMS | **COMPLETED 79** (live-correct set) |
| C6 similar DMS-380 | **COMPLETED** 5 similar |
| C7 task quality DMS-380 | **COMPLETED** (task_analysis widget facts) |
| C8 ambiguity → option-click continuation | NEEDS_CLARIFICATION → click `Utkin.S.A` (request preserved `session_id` + `clarification_id`) → turn2 **COMPLETED 57 exact** |
| C9 release SOURCE_CONDITIONAL | `FAILED` fail-closed typed |
| C10 safe not-found `Пупкин` | `NEEDS_CLARIFICATION`, no fabrication |

`stale_source_error_text=false` in all 10; `has_generic_v4_error=false` in all 10.

## Phase 8 — stability (logic GREEN; 11/31 environmental LLM-endpoint failures)

| Batch | Result |
|---|---|
| K1 attachments ×5 | 3/5 COMPLETED 3/3 exact; 2 client-300s timeouts |
| K2 text ×5 | 2/5 COMPLETED 4/4 exact; 3 client-300s timeouts |
| L2A DMS-380→assignee ×5 | **5/5 COMPLETED** 319 (oracle 318 = +1 live drift) |
| full-name assignee ×5 | **5/5 COMPLETED 7/7 exact** |
| person+sprint ×5 | 2/5 COMPLETED [DMS-371] exact; 2 timeouts; 1 FAILED ReadTimeout-repair |
| aging DMS ×3 | 2/3 COMPLETED 79 (live set); 1 FAILED ReadTimeout-repair |
| exact-task attachments WMB-30000 ×3 | 1/3 COMPLETED ok; 2 FAILED ReadTimeout-repair |

Every non-success shares one signature: `planner failed robust bounded repair: ['ReadTimeout' ×4]` (agent 240s LLM-client timeout → fail-closed) or 300s client timeout on a still-processing request. A post-batch 900s-timeout re-probe also FAILED at 347.9s, confirming **sustained** (not transient) endpoint degradation from ~10:30 local. **Zero** logic errors, **zero** false completions, **zero** fabrication in Phase 8. Classification: environmental LLM-endpoint reliability (A179/A186 lineage), not a product-logic regression. Completed runs in the same window were exact.

## Phase 9 — plugin / extensibility (GREEN)

`test_agent_core_v4_plugin_registry.py` **11/11** at START_HEAD: synthetic `dummy.55` plugin registers via `with_plugin` with **zero** Agent Core/planner/runtime business-logic edits; A190 gate retained.

## Findings (non-blocking)

- **F1 — LLM endpoint degradation (environmental):** Qwen3.8 via `api.ai.sbt` from ~10:30 local: single planner calls 2–5 min; 11/31 Phase-8 runs + P4c probe timeouts + 1 re-probe failed with 240s LLM ReadTimeout → bounded repair exhaustion → fail-closed FAILED, or >300s → client timeout. Owner item (A179/A186 lineage): constrained/structured output or deterministic fallback, and endpoint health/timeout policy.
- **F2 — `/health` unscoped-scan hang (A195B F2, unchanged):** agent `/health` readiness probe performs an unscoped full-scan task-query; 25s+ ReadTimeout observed. `/live` 200/0.0s; task-api `swtr-read/health` 200/0.2s. Non-blocking hygiene.
- **F3 — live source drift during the run:** 4 task-level changes + 2 assignee/status transitions (see Phase 5 ledger). Oracle-refresh discipline required for long matrices.
- **F4 — QA-artifact gotchas (fixed during run, for reproducibility):** p2/p3p4 runners' `member_resolve_used` checked a non-existent `capability` field on raw trajectory (false negatives; trajectories prove `member.resolve` was called); p3p4 P4c turn2 omitted `clarification_id` (UI sends it) — the dedicated cont/classify probes use the UI payload shape.

## Final classification

| Surface | Status |
|---|---|
| Owner frontier fix (its own gate) | **CERTIFIED** — D-A199-1 CLOSED (20/20 exact, governance intact, 0 rejections) |
| 27-skill matrix | 20 GREEN / 7 SOURCE_CONDITIONAL / 0 RED (drift-verified) |
| Cross-skill person-scope gate | GREEN |
| Multi-filter retained gate | P4a 10/10 + P4b 5/5 GREEN; **P4c RED (D-A200-1)** |
| Local-store audit | 0 factual local reads |
| Browser C | 10/10 |
| Stability | logic GREEN; 11/31 environmental endpoint failures (fail-closed) |
| dummy-55 / plugin | 11/11 |

**Verdict: `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_RED`** — single blocking defect D-A200-1 (period-sprint clarification/continuation false completion; pre-existing A199 F3 class, surfaced at the A200 hard gate).

**STOP.** Do not recommend Wave S. Do not add skills. Return D-A200-1 for owner remediation (intent-aware completion at clarification-continuation boundaries / deterministic continuation re-execution), then another full re-gate.

## Services left running (current HEAD)

| Service | URL | Port | PID | Health |
|---|---|---|---|---|
| UI (Vite) | http://localhost:5175 | 5175 | 98719 | 200 (localhost/::1 bind; 127.0.0.1 refused by design) |
| PO Agent | http://127.0.0.1:8212 | 8212 | 98718 | `/live` 200/0.0s; EXPECTED_HEAD=`3d97c9a`; `/health` hangs (F2) |
| Task API | http://127.0.0.1:8241 | 8241 | 98713 | `swtr-read/health` 200/0.2s, SSE, 48 tools |
| MCP-SWTR | http://127.0.0.1:3000/sse | 3000 | 98709 | connected (task-api SSE session healthy) |
