# Assignment 198 — Final pre-Wave-S regression re-gate of the existing 27-skill V4 catalog

**Verdict:** `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_RED`
**Sole RED cause:** D1 — multi-filter person+sprint(+status) trajectories cannot complete: the A198 READY guard (630b536) interacts with the pre-existing `covers_resolved_constraints` completion predicate so that a legitimate `task.search` call that omits the `space` argument (after `space.resolve`) is judged contract-unmet → planner READY rejected in a bounded loop → step-budget exhaustion / client 300s timeout. Fail-closed throughout (no fabrication, no premature completion), but the query class is non-functional: P5 MULTI row RED, S3 stability 0/6.

- **START_HEAD:** `0b5692d7f6a5f776d62381690d023da9cc366b45` (`docs(v4): advance checkpoint to A198 final re-gate`)
- **A197 base (owner diff):** `303f5a9a0982b3817a5953bd601c2cba161f3d81`
- **Date:** 2026-09-18 (all local times MSK, UTC+3)
- **Owner commits audited:** 3ab768a, 5aeb5b3, 4c79bc4, 630b536, e30ec7d, afaa7e0, a65eba6 (+ spec 86139c2, checkpoint 0b5692d)

---

## Provenance — terminal-restart boundary (explicit)

The QA terminal was restarted once mid-Phase-6. Per instruction, all previously completed phases/runs are treated as valid; the two pre-restart S3 300s timeouts observed live in the terminal are preserved in this report (they are not represented in any artifact file — the surviving `qa_198_p6b_results.json` comes from the post-restart re-run of the p6b script, which produced its own 4×300s + 1×step-budget S3 results).

**Pre-restart results (12:19–15:23):** services boot (agent 8212 PID 31893, task-api 8241 PID 31647, both 12:19; UI 5175 PID 22389 and MCP-SWTR 3000 PID 45891 long-lived), Phase 2 Oracle B (12:31–12:41), Phase 3 aging (12:43–12:48), Phase 4 readymate (12:49–13:13), Phase 5 27-skill matrix (13:18–13:33), Phase 6 first batch P4 A–D (valid; ~14:0x; P4E/P4F/S1–S5 invalidated by LLM endpoint 4xx storm at 0.2s), p6b stability S1–S5 (14:33–15:23: S1 5/5, S2 5/5 exact, S3 4×300s-timeout + 1×step-budget, S4 3/3, S5 3/3).

**Post-restart results (15:56–17:0x):** p6c continuation (S3 probe, L2A drift re-check, P4E/P4F re-runs, SIMIL×3), Phase 0/1 audits re-executed for the record, Browser C run 1 (16:36–16:42: C1–C3 valid, C4–C14 invalidated by LLM 429 storm), Browser C run 2 (16:53–17:06: C4–C14; C9 closed by standalone API re-probe), frontend build gate, local-store log audit.

## Phase 0 — start / architecture audit: PASS

Owner production diff since A197 base (`303f5a9..0b5692d`): 4 files, +40/−5.

| File | Change | Audit |
|---|---|---|
| `task-api/app/routers/swtr_query.py` | camelCase timestamp aliases at the source boundary (`createdAt`→`created_at`, `updatedAt`→`updated_at`, `dueDate`/`due_date`→`deadline`) | Source-boundary only; no local store; no entity hardcode ✓ |
| `po-agent .../adapters/task_api.py` | preserves provenance flags `_canonical_created_at_from_source` / `_canonical_updated_at_from_source`; `datetime.now()` fallback remains only for the model field, never as an aging fact | Provenance prevents fallback from becoming a fact ✓ |
| `po-agent .../v4_plugins/_task_live_handlers.py` (task.aging) | ages only rows with source-creation provenance; raises `AS21SourceUnavailable` when no row exposes a source timestamp (fail-closed, no age=0 fabrication) | ✓ |
| `po-agent .../harness/agent_core_v4.py` | generic READY guard: when **every** loaded skill has a typed completion contract and the trajectory is unmet, planner READY is advisory — rejected with `ready_rejected="unsatisfied_completion_contract"` and a bounded extra turn; contractless skills retain legacy planner READY | Generic, entity-free, no planner/prompt change, no semantic prepass ✓ |

Test diff: 3 files (completion contract, task-catalog registry, owner-fix contracts incl. aging provenance). No new business/entity hardcode; Hermes/plugin extension model intact; no local-store truth/fallback added. No Phase 0 invariant violated (but see D1 — the guard's interaction with the pre-existing A187 coverage predicate is a functional defect, classified in Phases 5/6).

## Phase 1 — automated suites (post-restart, fresh)

| Suite | Result |
|---|---|
| `tests/test_agent_core_v4*.py` + `tests/test_v4*.py` | **109 passed, 1 failed** (F3 below) |
| `test_agent_core_v4_completion_contract.py` + `test_v4_owner_fix_contracts.py` | **33/33 passed** — incl. `test_premature_model_ready_is_rejected_until_contract_is_satisfied`, `test_aging_rejects_adapter_fallback_timestamps`, `test_completion_mechanism_is_generic_and_entity_free` |
| `tests/test_agent_core_v4_plugin_registry.py` | **11/11 passed** (incl. `test_dummy_55_can_be_added_without_agent_core_change`) |
| Full po-agent suite | **1402 passed, 24 failed, 12 skipped, 11 errors** (177s) |
| A/B vs A197 base (read-only worktree at 303f5a9, same venv, removed after) | **Zero new failures at HEAD**; 3 baseline-only failures fixed/replaced by the owner commits (old `test_model_ready_path_still_works_when_contract_not_satisfied` superseded by the new contract test; `test_harness_api_v1::test_as21_diagnostics_reports_runtime_wiring_without_secrets` now passing; `test_aging_uses_bounded_live_space_collection` fixed by the 3ab768a/4c79bc4 line) |
| task-api: 5 production swtr test files | **37/37 passed** |
| task-api full | 84 passed / 24 failed — all 24 pre-existing legacy (local-store CRUD suites + first-commit `6b3bee0` stale `test_s21_agent_integration.py` asserting removed `SWTRAdapter.mcp_host`; documented already in A197) |
| frontend `tsc --noEmit` + `vite build` | **GREEN** (build 695ms) |

**F3 (test-logic bug, non-blocking, A197 F1 lineage, still not fixed by afaa7e0):** `test_task_wave_capabilities_bind_only_through_registry_contract` fails at HEAD: it validates skill IDs against handler keys on the full registry, but `task.search_sprint` is a **composite** skill bound to `sprint.resolve` + `task.search` (both handlers present; production routing proven live in the P5 SPRINT row). afaa7e0 fixed the registry scope but the assertion still conflates composite skill IDs with handler keys. No production impact.

## Phase 2 — fresh REAL AS21 Oracle B (pre-restart 12:31–12:41; valid per instruction)

| Entity | Live value at 12:35 | Note |
|---|---|---|
| DMS task-query rows | **410** (open 85 / terminal 135 / undecodable 190) | A197: 409 (+1 drift) |
| DMS open rows with source `created_at` | **85/85 present, 0 missing** | provenance 100% on open set |
| DMS aging ≥7d open | **80** keys | Phase 3 oracle |
| DMS-380 | Closed, Semavin.M.M, created `2026-09-02T07:10:43.292552Z` | |
| **Timestamp mapping proof (≥3 keys, raw `unit.createdAt` == canonical `created_at`)** | **DMS-380, DMS-1, DMS-3 — exact string equality** (`qa_198_rawprobe.json` vs `mapping_proof`) | mandatory proof ✓ |
| WMB-30000 attachments | 5 × xlsx | + WMB-29890 1×pdf, WMB-29995 10, WMB-29996/30001 7 each |
| Zhdanov.A.Ni / Garanin.R.V / Utkin.S.A | 7 / 9 / 57 | |
| Semavin.M.M | 315 (at 12:35) | live 316 by 16:1x (drift, proven in L2ADRIFT) |
| «Уткин» resolve | 7 source candidates | |
| DMS current sprint / tasks | DMS-SPRNT-3 / 55 | |
| versions route | **HTTP 400** | release source unavailable → REL/RHEALTH fail-closed |
| history | **502** (MCP tool error) | HIST/TIS fail-closed |

## Phase 3 — task.aging final gate: GREEN

`Застоявшиеся открытые задачи в DMS`, fresh sessions, concurrency 1 (pre-restart 12:43–12:48): **5 valid runs COMPLETED, 80/80 declared==ground-truth, key-set EXACT** (i=1,2,3,4,6; 24.6–47.8s), skill `task.aging`, completion `runtime_contract`, route exactly `task-query?space=DMS` (bounded, one call), **0 local-store hits**, `semantic_prepass_used=false`, trajectory `load_skill → call task.aging → ready`. Run i=5 FAILED at 0.3s = LLM endpoint 4xx outage (environmental; same storm that invalidated the first p6 batch — recorded, not hidden). No adapter-fallback timestamp counted (provenance filter live; unit test green). **A197 D1 (false zero) CLOSED.**

## Phase 4 — completion-gate adversarial: gate met (no premature planner READY)

- **A_10x** `задачи Гаранина в сентябрьском спринте`: 7/10 typed `NEEDS_CLARIFICATION` (space confirmation, non-null `clarification_id`, evidence = resolver-only member identity, typed options), 3/10 fail-closed `FAILED` (planner bounded repair: `ValidationError`/`invalid_recovery_action`), **0/10 completed, 0/10 premature-ready violations**. `ready_rejections=["unsatisfied_completion_contract", …]` observed in 4 runs — **the 630b536 guard is live** (A197 F3 hole closed: no resolver-only completion remains).
- **B_5x** `Задачи Александра Жданова в текущем спринте DMS` (full name + current sprint): **5/5 COMPLETED, DMS-371 exact, all `runtime_contract`**, capabilities `member.resolve + sprint.current + task.search` (+`space.resolve` in 3 runs), 41.9–84.8s.
- **Control (contractless skill):** `Текущий спринт DMS` 3/3 COMPLETED via **`planner_ready`** (S4) → normal READY semantics for contractless skills **not** globally disabled. ✓

## Phase 5 — full 27-skill API matrix (pre-restart 13:18–13:33; valid per instruction)

All 27 exposed skills, fresh sessions, concurrency 1, `semantic_prepass_used=false` on every row. Result: **19 GREEN, 7 SOURCE_CONDITIONAL, 1 RED (MULTI = D1)**.

| Row | Skill | Query | Status | Completion | Trajectory (decisions) | Ev | Parity vs fresh Oracle | Verdict |
|---|---|---|---|---|---|---|---|---|
| LKUP | task.lookup | Открой задачу DMS-380 | COMPLETED 30.4s | runtime_contract | load → lookup(DMS-380) → ready | 1 | Closed/Semavin.M.M = oracle | GREEN |
| SUMM | task.summary | Расскажи о задаче DMS-380 | COMPLETED 39.6s | runtime_contract | load → lookup → ready | 1 | source-accurate summary | GREEN |
| QUAL | task.quality | Насколько полностью описана задача DMS-380 | COMPLETED 13.5s | runtime_contract | load → quality → ready | 9 | 85/100 good (6137-char description bounded) | GREEN |
| ACCE | task.acceptance | Критерии приёмки задачи DMS-380 | COMPLETED 20.4s | runtime_contract | load → acceptance → ready | 3 | 0/100, no explicit AC section = source truth | GREEN |
| BLOC | task.blockers | Какие блокеры есть у задачи DMS-380 | COMPLETED 9.5s | runtime_contract | load → blockers → ready | 4 | no blockers, Closed = source truth | GREEN |
| DEPS | task.dependencies | Зависимости задачи DMS-380 | COMPLETED 30.1s | runtime_contract | load → dependencies → ready | 3 | 0 dependencies = source truth | GREEN |
| MISS | task.missing_requirements | Каких требований не хватает в задаче DMS-380 | COMPLETED 19.4s | runtime_contract | load → missing_requirements → ready | 3 | missing acceptance expectations = source truth | GREEN |
| HIST | task.history | История изменений задачи DMS-380 | FAILED 14.5s | — (fail-closed) | load → history | 0 | history source 502 (MCP tool error) | SOURCE_CONDITIONAL |
| TIS | task.time_in_status | Сколько времени задача DMS-380 провела в статусах | FAILED 17.4s | — (fail-closed) | load → time_in_status | 0 | same history source 502 | SOURCE_CONDITIONAL |
| AGING | task.aging | Застоявшиеся открытые задачи в DMS | COMPLETED 37.2s | runtime_contract | load → aging(space=DMS) → ready | 80 | **80/80 = Phase 3 oracle, key-set exact** | GREEN |
| SIMIL | task.similar | Найди похожие задачи на DMS-380 | COMPLETED 40.1s | runtime_contract | load → similar(DMS-380) → ready | 6 | top-5 deterministic (SIMIL_X3) | GREEN |
| TEXT | task.search_text | Найди задачи про аутентификацию в DMS | COMPLETED 22.9s | runtime_contract | load → search_text(phrase,space) → ready | 2 | DMS-380 + DMS-267 = oracle | GREEN |
| ATT | task.search_attachments | Какие вложения есть у задачи WMB-30000 | COMPLETED 23.0s | runtime_contract | load → search_attachments → ready | 5 | 5×xlsx = oracle | GREEN |
| EXCEL | task.search_excel | Задачи с Excel-вложениями в WMB | FAILED 69.5s | — (fail-closed) | load → search_excel(space=WMB) | 0 | typed fail-closed before N+1 fan-out (max_fanout guard) | SOURCE_CONDITIONAL |
| PDF | task.search_pdf | Задачи с PDF-вложениями в WMB | FAILED 66.8s | — (fail-closed) | load → search_pdf(space=WMB) | 0 | same bounded fail-closed | SOURCE_CONDITIONAL |
| MSG | task.search_msg | Задачи с MSG-вложениями в WMB | FAILED 59.8s | — (fail-closed) | load → search_msg(space=WMB) | 0 | same bounded fail-closed | SOURCE_CONDITIONAL |
| ASGN | task.search_assignee | Задачи Родиона Гаранина в DMS | COMPLETED 32.5s | runtime_contract | load → search_assignee(Родион Гаранин,DMS) → ready | 9 | 9 = oracle Garanin DMS | GREEN |
| STAT | task.search_status | Открытые задачи в DMS | COMPLETED 46.4s | runtime_contract | load → search_status(not_completed,DMS) → ready | 85 | 85 = oracle DMS open (B2 classification retained) | GREEN |
| SPRINT | task.search_sprint | Задачи в спринте DMS-SPRNT-3 | COMPLETED 50.5s | runtime_contract | load → **sprint.resolve** → **task.search(sprint_id,space)** → ready | 56 | 55 tasks + sprint evidence = oracle | GREEN |
| REL | task.search_release | Задачи релиза Q3-2026 в DMS | NEEDS_CLARIFICATION 7.8s | — (typed) | load → release.resolve | 0 | versions source HTTP 400 → release not confirmable, fail-closed | SOURCE_CONDITIONAL |
| **MULTI** | tasks.search | Открытые задачи Жданова в текущем спринте DMS | **FAILED 83.9s** | — (budget exhausted) | load → space.resolve → sprint.current → member.resolve → **task.search(assignee, sprint_id, status — no space)** → ready ×3 rejected → `v4 planner step budget exhausted without READY` | 0 | n/a | **RED (D1)** |
| L2A | tasks.lookup_then_assignee | Покажи DMS-380 и затем задачи его исполнителя | COMPLETED 32.2s | runtime_contract | load → task.lookup(DMS-380) → task.search(assignee=semavin.m.m) → ready | 317 | 316 unique (drift 315→316 proven in L2ADRIFT; unique parity exact) | GREEN |
| CURR | sprint.current | Текущий спринт DMS | COMPLETED 28.2s | planner_ready (contractless) | load → space.resolve → sprint.current → ready | 1 | DMS-SPRNT-3 = oracle | GREEN |
| DISC | sprints.discover | Сентябрьский спринт DMS | COMPLETED 59.5s | runtime_contract | load → space.resolve → sprint.search(period=сентябрь) → ready | 1 | DMS-SPRNT-3 13.09–27.09 = oracle | GREEN |
| LIST | sprints.list | Активные спринты в DMS | COMPLETED 31.7s | runtime_contract | load → space.resolve → sprint.list(active_only) → ready | 1 | 1 active sprint = oracle | GREEN |
| SHEALTH | sprint.health | Здоровье спринта DMS-SPRNT-3 | COMPLETED 36.1s | runtime_contract | load → sprint.resolve → sprint.health → ready | 56 | 55 tasks / 8 done at 13:1x = live truth | GREEN |
| RHEALTH | release.health | Здоровье релиза Q3-2026 в DMS | NEEDS_CLARIFICATION 16.7s | — (typed) | load → release.resolve | 0 | versions source HTTP 400, fail-closed | SOURCE_CONDITIONAL |

Notes: (1) every GREEN fact row sourced exclusively from live `swtr-read`/`task-query` routes (route histogram, Phase 6 audit); (2) B2 status classification retained — STAT 85 counts only decodable non-terminal rows, the 190 statusless rows are not reported open; (3) L2A evidence 317 raw / 316 unique — the 17:0x L2ADRIFT re-probe (fresh oracle 316) proves agent unique parity exact (missing=0, extra=0); raw dup is the known DMS-380 evidence-dup cosmetic (A196/A197).

## Phase 6 — retained high-risk regression (post-restart 14:33–17:1x)

| Gate | Requirement | Result |
|---|---|---|
| S1 DMS-380 → assignee tasks 5× exact | L2A ×5 | **5/5 COMPLETED, runtime_contract**; 317 raw / 316 unique per run; 108.2–172.5s (SSE-session latency under load, A186 owner item). Oracle at run time (316) made `exact=false` — **L2ADRIFT** (fresh oracle 316 vs agent 316 unique): `exact_unique_vs_oracle=true, missing=[], extra=[]` → parity exact, drift explained |
| S2 inflected/full-name assignee 5× exact | `Задачи Александра Жданова в DMS` ×5 | **5/5 COMPLETED, 7/7 EXACT, runtime_contract** (61.7–111.1s) |
| S3 multi-filter person+sprint(+status) | `Открытые задачи Жданова в текущем спринте DMS` ×5 + S3PROBE | **0/6** — 4× client 300s timeout + 2× `v4 planner step budget exhausted without READY` (102.9–178.8s when not client-timed-out). **= D1 (sole RED)** |
| S4 current sprint 3× (contractless control) | `Текущий спринт DMS` ×3 | **3/3 COMPLETED via `planner_ready`** — normal READY semantics intact |
| S5 WMB-30000 attachments 3× | ×3 | **3/3 COMPLETED, 5 files, runtime_contract** (47.9–85.4s) |
| P4-A inflected full name | `Задачи Александра Жданова в DMS` | COMPLETED **7/7 exact** |
| P4-B non-team identity | `Задачи Utkin.S.A` | COMPLETED **57/57 exact** (CRPV/STS/WMB cross-space) |
| P4-C ambiguous surname | `Задачи Уткина` | typed NEEDS_CLARIFICATION, options = **7 source candidates, options_match_source=true** |
| P4-D same-session continuation | click Utkin.S.A | turn2 COMPLETED **57/57 exact** (61.3s) |
| P4E2 invented person safe | `Задачи Пупкина` | typed NEEDS_CLARIFICATION (12.2s), zero facts, no stale error text (pre-restart P4E invalid — LLM 4xx storm, re-run valid) |
| P4F2 person+sprint fail-closed | `задачи Гаранина в сентябрьском спринте` turn1 | FAILED via bounded planner repair (`ValidationError`/`invalid_recovery_action`), 0 facts — fail-closed, no premature completion (A197 F3 class; LLM reliability, not an A198 owner defect) |
| SIMIL×3 deterministic | ×3 | **3/3 COMPLETED, identical top-5** [DMS-380, DMS-375, DMS-113, DMS-400, DMS-329, DMS-339], 32.1–68.8s |
| Stale source-error text | all rows | **0 occurrences** (`stale_source_error_text=false` on every recorded row) |

### Local-store log audit (task-api `/private/tmp/qa198_taskapi.log`, full service window since 12:19 boot)

Route histogram: all fact traffic on live routes — `swtr-read/task-query` (space/assignee/phrase-scoped), `swtr-read/sprints/DMS-SPRNT-3/tasks?complete=true`, `swtr-read/spaces/DMS/current-sprint`, `swtr-read/assignees/resolve`, `swtr-read/tasks/*/files`. **3** `GET /api/v1/tasks?limit=10000&offset=0` reads (13:28:46, 13:33:27, 16:58:04), each correlated in the agent log (`/private/tmp/qa198_agent.log`) with one `/api/v1/query` completion (13:29:01, 13:33:50, 17:00:34).

**Root cause (traced to code, deterministic):** all three are `release.resolve` calls (P5 REL, P5 RHEALTH, browser C10). `_release_resolve` (agent_core_v4.py:867) → `adapter.get_release_tasks(...)` → inherited legacy base `TaskApiAS21Adapter.get_release_tasks` (task_api.py:482) → `HardenedProductionTaskApiAS21Adapter.search_tasks` else-branch (hardened_production_task_api.py:310-314): a query with `project` but **no** assignee/sprint is explicitly delegated to `TaskApiAS21Adapter.search_tasks(self, "release = ...")` → `_fetch_tasks` → local `GET /api/v1/tasks`.

**Impact assessment:** local store live-verified **empty** (`GET /api/v1/tasks` → `[]`, 0 items) → **zero facts** obtained, all three queries ended in typed fail-closed clarification (consistent with the versions source returning HTTP 400). No factual GREEN row relied on local truth. Classified as finding **F2** (latent local-store truth path in the release route; same lineage as A193 D1/A197 F4), not a fact-path RED: it cannot produce facts while the store is empty, but it would silently return local rows as `source: REAL_AS21` if the store were ever populated. No unexplained local reads remain.

## Phase 7 — Browser C gate (Playwright, UI 5175 → agent 8212 → task-api 8241)

Run 1 (16:36–16:42): **C1 task_detail**, **C2 task_table** (Garanin DMS, 10 — live drift 9→10, agent held live truth), **C3 attachment_table** (5×xlsx) all COMPLETED with correct V4 widgets; C4–C14 invalidated by the Qwen3.8 4xx/429 storm (uniform 0.2s-class `HTTPStatusError` failures), re-run in run 2.

Run 2 (16:53–17:06) + API close:

| Case | Query | UI result | Verdict |
|---|---|---|---|
| C4 task.quality | Насколько полностью описана задача DMS-380 | COMPLETED, widget **task_analysis** (85/100) | GREEN |
| C5 dependencies | Зависимости задачи DMS-380 | COMPLETED, widget **task_dependencies** (0) | GREEN |
| C6 history | История изменений задачи DMS-380 | FAILED, panel **V4SOURCE_UNAVAILABLE**, typed message | GREEN (correct typed source-unavailable) |
| C7 similar | Найди похожие задачи на DMS-380 | COMPLETED, widget **similar_task_list** (5) | GREEN |
| C8 sprint health | Здоровье спринта DMS-SPRNT-3 | COMPLETED (attempt 2), widget **sprint_health**, 8/60 13.3% (live drift 55→60) | GREEN |
| C9 sprint list | Активные спринты в DMS | browser attempt FAILED (429 storm) → **closed by standalone API re-probe: COMPLETED 17.3s, `sprints.list`, runtime_contract, 1 active DMS-SPRNT-3** (`qa_198_p9_c9_reprobe.json`) | GREEN |
| C10 release health | Здоровье релиза Q3-2026 в DMS | typed NEEDS_CLARIFICATION (release not confirmable, versions 400) | GREEN (SOURCE_CONDITIONAL, fail-closed) |
| C11 clarification continuation | Задачи Уткин → click Utkin.S.A | turn1 typed NEEDS_CLARIFICATION, 7 source-candidate option buttons rendered; **turn2 COMPLETED 57/57 exact**, same session, widget task_table | GREEN |
| C12 safe not-found | Задачи Пупкина | typed NEEDS_CLARIFICATION, zero facts | GREEN |
| C13 aging DMS | Застоявшиеся открытые задачи в DMS | COMPLETED (attempt 2), widget **task_table**, data `{threshold_days:7, count:80}` = Phase 3 oracle | GREEN |
| C14 person+sprint | Задачи Александра Жданова в текущем спринте DMS | COMPLETED, DMS-371 exact; step-4 `task.search(assignee, sprint_id, **space=DMS**)` — guard satisfied, runtime_contract | GREEN (and the exact D1 contrast: with `space` present the same query class completes) |

No Legacy Harness execution for any tested query (every row `ui_trace=Agent Core v4`, v4 panel states `V4SUCCESS_WITH_DATA`/`V4NEEDS_CLARIFICATION`/`V4SOURCE_UNAVAILABLE`); zero stale source-error text; network confined to `/api/v1/query` + `/health` (A191 pattern).

## Phase 8 — plugin/extensibility (A190 dummy-55 re-gate)

`qa_198_p8_dummy55.py` (identical 14-check probe; check 1 refreshed to the current 2-plugin base registry `("builtin.catalog.tasks", "builtin.core.a188")` — the A190 script's single-plugin assertion is stale, not a production change): **14/14 GREEN** — `with_plugin` injection, compact catalog exposure, full skill contract load, typed handler binding, completion-contract declaration, UIContract metadata, zero Agent Core edits. 27 base skills confirmed in registry (20 catalog + 7 core). No new skill/core coupling.

## Findings (non-blocking)

- **F1 (test-logic):** `test_task_wave_capabilities_bind_only_through_registry_contract` still fails at HEAD — afaa7e0 fixed the registry scope but the assertion still conflates composite skill IDs (e.g. `task.search_sprint` = `sprint.resolve`+`task.search`) with flat handler keys. No production impact (production routing proven live, SPRINT row).
- **F2 (latent local-store path, release route):** see Phase 6 audit — `HardenedProductionTaskApiAS21Adapter.search_tasks` else-branch routes project-only (release) searches to the legacy local store. Safe today (store empty, fail-closed), but would serve local rows as `REAL_AS21` if the store were populated. Owner fix: route release-filter searches through the live versions/task-query facade or fail closed when the release source is unavailable.
- **F3 (environmental):** Qwen3.8 4xx/429 storms (0.2s-class `HTTPStatusError` waves) invalidated the first p6 batch (P4E/P4F/S1–S5) and browser C4–C14 run 1. Every invalidated row was re-run and is accounted for above; no storm-invalidated result was used in any verdict.
- **F4 (latency):** L2A 108–172s and S3 client 300s timeouts under sequential load = long-lived task-api→MCP-SWTR SSE session latency spikes (A186 owner item). D1's bounded rejection loop amplified single-run latency to client timeouts in 4/5 S3 runs.
- **F5 (source drift, live):** Semavin 315→316 (unique; L2ADRIFT exact), DMS-SPRNT-3 55→60 tasks, Garanin DMS 9→10, DMS open 85, aging 80 — agent consistently held live truth; oracles refreshed at the point of comparison.
- **F6 (pre-existing, unchanged):** `/health` unscoped full-scan hang (A195B F2) — today's probe timed out again (liveness `/live` 200). Non-blocking for V4 query paths.
- **F7 (planner reliability, A179 lineage):** P4F2 bounded-repair failures and the 3/10 A_10x fail-closed `FAILED` runs are Qwen3.8 planner reliability on constrained multi-turn trajectories — fail-closed, zero fabrication; no premature completion in any of them.

## D1 — defect specification (sole RED cause)

**Symptom:** the query class "multi-filter person + current/period sprint (+ status)" cannot complete: P5 MULTI FAILED (83.9s, `v4 planner step budget exhausted without READY`), S3 0/6 (4× client 300s timeout + 2× step-budget exhaustion). Fail-closed throughout — zero fabrication, zero premature completion.

**Mechanism (proven from code + live trajectory):**
1. `tasks.search` contract (v4_plugins/core.py:45): `CompletionRequirement("task.search", data_keys=("count",), covers_resolved_constraints=True)`.
2. `_CONSTRAINT_RESOLVERS` (agent_core_v4_completion.py:34) registers `space.resolve → ("space", "space")`: after `space.resolve` returns `DMS`, the value `dms` is a resolved user constraint.
3. `_constraints_covered` (agent_core_v4_completion.py:153) requires every resolved constraint value to appear, casefolded, **among the literal argument values of the terminal `task.search` observation**.
4. Live MULTI trajectory: `task.search(assignee=Zhdanov.A.Ni, sprint_id=DMS-SPRNT-3, status=not_completed)` — **no `space`** (legal: the capability schema declares `space` "optional", agent_core_v4.py:477). The resolved space `dms` is absent from the argument set → contract judged unmet.
5. The A198 guard (630b536, agent_core_v4.py:1116-1120) then rejects planner READY with `ready_rejected="unsatisfied_completion_contract"`; the planner has no signal that `space` is the missing piece and re-emits READY; bounded turns exhaust the step budget → FAILED (or client 300s timeout under load).

**Proof that completion is reachable:** B_5x (5/5), browser C14 (step 4 carries `space=DMS`), and P4 A (no `space.resolve` called → no space constraint to cover) all complete the same query class — completion depends on the planner voluntarily repeating the resolved space in the terminal call.

**Owner fix proposals (generic, entity-free, no planner/prompt dependency preferred):**
- (a, recommended) **Deterministic argument completion:** when a terminal call of a `covers_resolved_constraints` capability omits a resolved constraint value that is a valid optional argument of that capability, the runtime injects it from the resolver observation before execution/coverage evaluation. Removes planner cooperation entirely.
- (b) **Implied coverage:** extend `_constraints_covered` to accept a resolved space constraint as covered when the terminal call carries a `sprint_id` (or `release_id`) whose resolving observation exposes the same space (semantically the sprint already scopes the space).
- (c) **Informative rejection:** surface the specific missing constraint(s) in the `ready_rejected` hint so the model can repair within the bounded turn (weakest alone; keep as complement).

**Re-gate after fix:** P5 MULTI 3×, S3 5× (must complete exact against a refreshed person+sprint+status oracle), B_5x 5× retained, S4 control retained, full 27-row matrix spot re-run of all contracted rows, then A198 re-gate = GREEN only with zero RED rows.

## Verdict

**`AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_RED`** — sole RED cause D1 (multi-filter person+sprint(+status) completion blocked by the 630b536 READY guard × `covers_resolved_constraints` literal-argument coverage predicate).

All A197 protections retained and re-proven:
- **aging exact** — Phase 3 5 valid runs 80/80 key-set exact, real source timestamps, provenance filter live, A197 D1 (false zero) CLOSED;
- **no premature planner-ready completion** — Phase 4: 0 violations across 10+5+3 runs, guard rejections observed live (4 runs), contractless control intact (`planner_ready` preserved);
- **A196/A197 protections intact** — text 2/2, attachments 5/5, status 85/85, sprint 55/55, identity matrix exact, clarification continuation, safety negatives fail-closed, zero stale source-error text, zero unexplained local-store reads;
- **27/27 skills explicitly tested** — 19 GREEN, 7 SOURCE_CONDITIONAL (all truly source-limited and fail-closed: history 502 ×2, broad WMB attachment fan-out bounded ×3, release source 400 ×2), 1 RED (D1).

## Service keepalive (left running at START_HEAD)

| Service | Port | PID | Health |
|---|---|---|---|
| PO Agent (agent_core_v4, `PO_AGENT_EXPECTED_HEAD=0b5692d…`) | 8212 | 31893 | `/live` 200 (`/health` hangs — F6 pre-existing) |
| Task API (swtr-read, MCP stdio, 48 tools) | 8241 | 31647 | `/api/v1/swtr-read/health` 200 connected |
| MCP-SWTR SSE | 3000 | 45891 | serving (agent log shows live reads) |
| Frontend (Vite → 8212) | 5175 | 22389 | 200 |

**START_HEAD:** `0b5692d7f6a5f776d62381690d023da9cc366b45`
