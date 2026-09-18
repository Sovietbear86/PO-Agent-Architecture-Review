# A196 — Full Regression of All Existing V4 Skills (27)

**Date:** 2026-09-18
**Branch:** `feat/core8-real-query-hardening-v2`
**START_HEAD:** `bf810fc573eb19896c44a843781d2145c2c7da19`
**Permanent rollback:** `0f03fca14fe078c86dca961362915e10cc985401`
**Role:** QA/adversarial tester + service operator (no production changes)
**Source:** REAL AS21 via task-api (8241) → MCP-SWTR SSE (3000), live throughout

## VERDICT: `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_RED`

27/27 existing V4 skills executed, none skipped. **18 GREEN, 5 RED (avoidable implementation defects), 4 SOURCE_CONDITIONAL (proven live source 502, fail-closed correct).** All identity adversarial, stability, Browser C, and plugin gates are GREEN. No A192/A193/A195 defect regressed — all three previously-RED rows are now exact-parity GREEN.

**RED rows (first bounded defects):**
1. `task.aging` — unscoped full-tenant scan `adapter.search_tasks("")` → 246.6 s client timeout, ev=0
2. `task.similar` — same unscoped scan → 234.0 s client timeout, ev=0
3. `task.search_excel` / `task.search_pdf` / `task.search_msg` (space-scoped WMB, 2363 rows) — per-task file-metadata N+1 loop → 300 s client timeout each; **person-scoped variant completes in 79.3 s with correct data** (probe EXCEL2), proving the capability works and the space-scoped path is an avoidable N+1 defect

---

## Phase 0 — Inventory, static invariants, services

- `git pull --ff-only`: `cd2f12f` → `bf810fc`. Window `cd2f12f..bf810fc` touches **docs only** (`GIGACODE_NEXT_ACTION.md`, `V4_54_SKILL_MIGRATION_PLAN.md`); `git diff --stat ... -- src tests` = empty.
- Registry inventory (`qa_196_p0_inventory.json`): **2 plugins, 27 unique skills, 23 UI contracts** — matches spec exactly.
  - `builtin.core.a188` (12): tasks.search, sprints.discover, sprints.list, tasks.lookup_then_assignee, task.lookup, task.summary, task.quality, task.acceptance, task.blockers, sprint.health, sprint.current, release.health
  - `builtin.catalog.tasks` (15): task.search_text, task.search_attachments, task.search_excel, task.search_pdf, task.search_msg, task.search_assignee, task.search_status, task.search_sprint, task.search_release, task.missing_requirements, task.dependencies, task.history, task.time_in_status, task.aging, task.similar
- Services restarted fresh at `bf810fc`: task-api PID 55923 (8241, connected), po-agent PID 55928 (8212, `/live` 200). UI 5175 and MCP-SWTR 3000 carried from A195D session, verified up.
- `semantic_prepass_used=false` on every live matrix row (no semantic prepass in the V4 path).

## Phase 1 — Automated suites

| Suite | Result |
|---|---|
| po-agent `pytest -q` | **101 passed, 4 failed** |
| task-api tests | **37 passed** |

The 4 failures are all in `tests/test_agent_core_v4_task_catalog.py` and are **pre-existing stale contract tests**: they expect `task.search_assignee` to expand to `[member.resolve, task.search]`, while A195D owner commits changed the contract to `[task.search_assignee]`. Proven pre-existing: those test files were last modified at `2794609`/`901c5e4`, predating the A195D owner commits (`043823f`–`f6e44ad`); `src`/`tests` diff since A195D checkpoint = 0 lines. Not an A196 regression; flagged for owner (test-contract refresh).

## Phase 2 — Oracle pack (live AS21 ground truth)

`qa_196_oracle.json`: DMS-380 (Semavin.M.M, DMS-SPRNT-3, Закрыт/done, created 2026-09-02, desc 6137 chars); DMS-380 history → 502 (source unavailable); WMB-30000 = 5 xlsx; WMB-29890 = 1 pdf; WMB-29995 = 10 files; assignee key sets — Zhdanov.A.Ni DMS 7, Garanin.R.V DMS 8, Agataeva.A.Z 17, Semavin.M.M 312, Utkin.S.A 57; Уткин → 409 with 7 source matches; DMS sprints SPRNT-3 (IN_PROGRESS), SPRNT-1/2 (FINISH); DMS-SPRNT-3 = 53 tasks; DMS open = 84/408; `search_versions` DMS → 502; text «аутентификация» DMS = 2 (DMS-267, DMS-380); task-query rows carry `assigned_to`, `scrum_board_plugin_sprint`, `workflow_status` only (no top-level `created_at`).

## Phase 3 — 27-skill API matrix (`qa_196_p3_results.json`)

| # | Skill (plugin) | Query | Status | Evidence | Classification |
|---|---|---|---|---|---|
| 1 | task.lookup (core) | Открой задачу DMS-380 | COMPLETED | 1 [DMS-380] | GREEN |
| 2 | task.summary (core) | Расскажи о задаче DMS-380 | COMPLETED | 1 | GREEN¹ |
| 3 | task.quality (core) | Насколько полностью описана DMS-380 | COMPLETED | 9 | GREEN² |
| 4 | task.acceptance (core) | Критерии приёмки DMS-380 | COMPLETED | 3 | GREEN |
| 5 | task.blockers (core) | Блокеры DMS-380 | COMPLETED | 4 | GREEN |
| 6 | task.dependencies (catalog) | Зависимости DMS-380 | COMPLETED | 3 | GREEN |
| 7 | task.missing_requirements (catalog) | Чего не хватает в DMS-380 | COMPLETED | 3 | GREEN |
| 8 | task.history (catalog) | История DMS-380 | FAILED, ev=0, typed fail-closed 11.8 s | — | SOURCE_CONDITIONAL (502 proven) |
| 9 | task.time_in_status (catalog) | Время в статусах DMS-380 | FAILED, ev=0, typed fail-closed 8.0 s | — | SOURCE_CONDITIONAL (502 proven) |
| 10 | task.aging (catalog) | Застоявшиеся открытые задачи в DMS | **FAILED**, ev=0, **246.6 s** | — | **RED** (unscoped scan) |
| 11 | task.similar (catalog) | Похожие на DMS-380 | **FAILED**, ev=0, **234.0 s** | — | **RED** (unscoped scan) |
| 12 | task.search_text (catalog) | Задачи про аутентификацию в DMS | COMPLETED | **2/2 exact** (DMS-267, DMS-380) | GREEN (A192 #1 closed) |
| 13 | task.search_attachments (catalog) | Вложения WMB-30000 | COMPLETED | 5 (5×WMB-30000) | GREEN (A193 closed) |
| 14 | task.search_excel (catalog) | Excel-вложения в WMB | **ERROR**, 300 s client timeout | — | **RED** (N+1, see 14b) |
| 15 | task.search_pdf (catalog) | PDF-вложения в WMB | **ERROR**, 300 s client timeout | — | **RED** (N+1) |
| 16 | task.search_msg (catalog) | MSG-вложения в WMB | **ERROR**, 300 s client timeout | — | **RED** (N+1) |
| 14b | probe EXCEL2 (catalog) | Задачи Utkin.S.A с Excel-вложениями | COMPLETED, **79.3 s** | 13 (2 tasks: WMB-29996×6, WMB-30001×5) | capability works when scoped |
| 17 | task.search_assignee (catalog) | Задачи Родиона Гаранина в DMS | COMPLETED | **8/8 exact** | GREEN (A195 closed) |
| 18 | task.search_status (catalog) | Открытые задачи в DMS | COMPLETED | **84/84 exact** | GREEN (A192 closed) |
| 19 | task.search_sprint (catalog) | Задачи в спринте DMS-SPRNT-3 | COMPLETED | 54 (53 tasks + sprint entity ID) | GREEN |
| 20 | task.search_release (catalog) | Задачи релиза Q3-2026 в DMS | NEEDS_CLARIFICATION | 0 | SOURCE_CONDITIONAL (release absent in source; versions 502) |
| 21 | tasks.search (core, multi-filter) | Открытые задачи Жданова в текущем спринте DMS | COMPLETED | 3 (DMS + Zhdanov.A.Ni entities + **DMS-371** = oracle 1/1) | GREEN |
| 22 | tasks.lookup_then_assignee (core) | Покажи DMS-380 и задачи его исполнителя | COMPLETED | 313 = **312 unique** (Semavin oracle) + 1 cosmetic DMS-380 dup | GREEN (A188 lineage retained) |
| 23 | sprint.current (core) | Текущий спринт DMS | COMPLETED | DMS-SPRNT-3 | GREEN |
| 24 | sprints.discover (core) | Сентябрьский спринт DMS | COMPLETED | DMS-SPRNT-3 | GREEN |
| 25 | sprints.list (core) | Активные спринты в DMS | COMPLETED | 1 active | GREEN |
| 26 | sprint.health (core) | Здоровье спринта DMS-SPRNT-3 | COMPLETED | 54 (53 + entity) | GREEN |
| 27 | release.health (core) | Здоровье релиза Q3-2026 в DMS | NEEDS_CLARIFICATION | 0 | SOURCE_CONDITIONAL (same as #20) |

¹ One-off planner routing anomaly: the matrix run loaded `task.lookup` for the summary phrasing. Probe SUMM2/SUMM3 (different phrasings) load `task.summary` with `skill_match=True` (6.9 s / 5.7 s) — same known Qwen3.8 routing variance as A195D; not a catalog defect.
² Minor UI-contract gap: `task.quality` has no `widget:` mapping, so the V4 panel renders raw trace JSON (see Phase 6 C4).

## Phase 4 — Identity adversarial (`qa_196_p45_results.json`)

| Case | Query | Result |
|---|---|---|
| A inflected full name | «…Александра Жданова в DMS» (genitive) | COMPLETED, **7/7 exact**, stale=false |
| B non-team login | «Задачи Utkin.S.A» | COMPLETED, **57/57 exact** |
| C ambiguous | «Задачи Уткина» | NEEDS_CLARIFICATION, options == source 409 set (7), typed, stale=false |
| D continuation | C → click Utkin.S.A | turn2 COMPLETED, **57/57 exact** |
| E invented | «Задачи Пупкина» | NEEDS_CLARIFICATION, empty options, safe, stale=false |
| F sprint reference | «задачи Гаранина в сентябрьском спринте» | COMPLETED directly (sprint resolvable, no spurious clarification) |

All `semantic_prepass_used=false`, `stale_source_error_text=false` everywhere.

## Phase 5 — Stability

| Loop | Query | Result |
|---|---|---|
| S1 ×5 | L2A «Покажи DMS-380 и задачи его исполнителя» | 5/5 COMPLETED, n=313 deterministic (312 unique + 1 dup) |
| S2 ×5 | «Задачи Александра Жданова в DMS» | 5/5 COMPLETED, all exact=True (7/7) |
| S3 ×5 | multi-filter Жданов ∩ current sprint | 5/5 COMPLETED, n=3 (1 task + 2 entity IDs) |
| S4 ×3 | «Текущий спринт DMS» | 3/3 COMPLETED |
| S5 ×3 | «Вложения WMB-30000» | 3/3 COMPLETED (5 files) |

## Phase 6 — Browser C, 12 UI result shapes (`qa_196_p6_results.json` + `qa_196_p6b_results.json`)

All 12 cases executed via UI 5175 → agent 8212. `has_stale_source_error_text=false` in **all 12**.

| Case | Shape | Backend | UI |
|---|---|---|---|
| C1 task-detail | DMS-380 | COMPLETED ev=1 | task_detail widget ✓ |
| C2 task-table | Гаранов DMS | COMPLETED ev=8 | task_table widget ✓ |
| C3 attachment-table | WMB-30000 | COMPLETED ev=5 | attachment_table widget ✓ |
| C4 task-analysis | quality DMS-380 | COMPLETED ev=9 | SUCCESS_WITH_DATA, **no widget mapping** (raw trace JSON in panel) — minor UI-contract gap, backend answer correct (85/100 good) |
| C5 dependencies | DMS-380 | COMPLETED ev=3 | task_dependencies widget ✓ |
| C6 history | DMS-380 | FAILED ev=0 | **V4SOURCE_UNAVAILABLE** — correct fail-closed mapping of the 502 (7.3 s) |
| C7 similar | DMS-380 | FAILED ev=0 (274 s) | V4SOURCE_UNAVAILABLE — timeout mapped to source-unavailable presentation; root cause = RED unscoped scan |
| C8 sprint-health | DMS-SPRNT-3 | COMPLETED ev=54 | sprint_health widget ✓ (53 tasks, 7 done) |
| C9 sprint-list | DMS | COMPLETED ev=1 | sprint_list widget ✓ |
| C10 release-health | Q3-2026 | NEEDS_CLARIFICATION | V4NEEDS_CLARIFICATION — «Не удалось подтвердить релиз по данным REAL AS21» ✓ |
| C11 clarification-continuation | Уткин → Utkin.S.A | turn1 NEEDS_CLARIFICATION (7 source options, cid) → turn2 **COMPLETED ev=57 exact** | payload preserves `session_id` + `clarification_id` + `clarification_option` ✓ |
| C12 safe-not-found | Пупкин | NEEDS_CLARIFICATION, empty options | safe, no stale text ✓ |

(The first Browser C run completed C1–C10 before the 6-min test timeout hit C11; C11+C12 were re-executed in a focused spec — results merged above. No case was skipped.)

## Phase 7 — Plugin/dummy-55 structural gate

`pytest tests/test_agent_core_v4_plugin_registry.py -v`: **11/11 passed (0.49 s)**, incl. `test_dummy_55_can_be_added_without_agent_core_change`, duplicate/missing-handler/malformed-skill fail-closed, untrusted-package rejection. No agent-core changes required for catalog extension — retained from A190/A195D.

---

## RED defects (bounded, for owner)

**D1 — unscoped full-tenant scan in `task.aging` and `task.similar` (rows 10–11).**
Both handlers iterate `adapter.search_tasks("")` (entire tenant, multi-space, multi-thousand rows) to compute aging/similarity for what the user asked as a space-scoped question («в DMS»). Observed: 246.6 s and 234.0 s → client read timeout → ev=0 fail-closed. The queries themselves are correctly scoped in intent; the implementation is not.
Proposed fix: route through the same space-scoped task-query collection used by `task.search_status` (bounded pages + `complete` contract from A185 B1), compute aging/similarity over the scoped set; for `task.similar` restrict candidate pool to the task's space (or an explicit bounded radius) instead of the tenant.

**D2 — N+1 per-task file-metadata loop in `task.search_excel/pdf/msg` for space-scoped queries (rows 14–16).**
Space-scoped WMB = 2363 rows; the handler fetches file metadata per task → >300 s → client timeout → ERROR. Probe EXCEL2 (person-scoped, 57 tasks) completed in 79.3 s with correct data (WMB-29996 ×6 xlsx, WMB-30001 ×5 xlsx), so the capability is functionally sound; the defect is the unbounded per-row fan-out.
Proposed fix: batch the file-metadata lookup (single paged file query per page of tasks, or a task-query attribute filter for attachment presence where the source supports it), with the same bounded `complete` contract; keep fail-closed on partial completion.

**Not defects (verified):** `task.history` / `task.time_in_status` / `task.search_release` / `release.health` failures are live source 502s (`get_unit_change_history` ToolError, `search_versions` ToolError, release absent) with correct typed fail-closed behavior and no empty-result fabrication → SOURCE_CONDITIONAL.

## Non-blocking findings

- **F1 (test hygiene):** 4 stale tests in `test_agent_core_v4_task_catalog.py` still assert the pre-A195D `[member.resolve, task.search]` expansion for `task.search_assignee`; contract is now `[task.search_assignee]`. Owner to refresh the expectations.
- **F2 (UI contract):** `task.quality` has no `widget:` entry in the UI contract → the V4 result panel falls back to raw trace JSON (C4). Add a widget mapping (e.g. `task_analysis`/`score`) for presentation parity.
- **F3 (cosmetic, retained from A195D):** L2A evidence contains DMS-380 twice (lookup evidence + assignee set); unique set is exact (312/312).
- **F4 (known, environmental):** Qwen3.8 one-off planner routing variance (summary phrasing → task.lookup once; probes prove correct skill on re-phrase). Same class as A195D's transient anomaly.
- **F5 (known, environmental):** `/health` unscoped-scan hang unchanged (A195B F2); QA used `/live` throughout.

## Regression vs A195D checkpoint

- A192 RED rows: `task.search_text` now 2/2 exact; `task.search_status` now 84/84 exact; NL assignee 8/8 exact + full adversarial battery green → **closed**.
- A193 RED rows: `task.search_attachments` 5/5 files → **closed**; clarification continuation (C11) preserves session/clarification metadata → **closed**.
- A195D protections retained: inflected full names exact (S2 5/5), non-roster logins source-confirmed (57/57), ambiguous → typed clarification with source-exact options, invented → safe clarification, no stale «AS21 вернул некорректные данные» text anywhere.
- A188 P1 multistep lineage (L2A) deterministic 5/5.
- No new failures in automated suites vs A195D baseline (same 4 pre-existing stale tests).

## Services left running

| Service | Port | PID |
|---|---|---|
| UI (vite) | 5175 | 22389 |
| po-agent | 8212 | 55928 |
| task-api | 8241 | 55923 |
| MCP-SWTR (SSE) | 3000 | 45891 |

## Recommendation

STOP Wave S migration until D1/D2 are fixed and re-gated (aging/similar ×3 space-scoped, excel/pdf/msg ×3 space-scoped, plus the 27-row matrix re-run). After GREEN, proceed per `V4_54_SKILL_MIGRATION_PLAN.md`.
