# Assignment 216 — Agent Core v4 Batch 3 Five-Skill Gate

**Verdict:** `AGENT_CORE_V4_BATCH3_FIVE_SKILL_GREEN`
**Date:** 2026-09-25
**Role:** QA/adversarial tester only (no production code changes)

## Baseline

| Item | Value |
|---|---|
| Branch | `feat/core8-real-query-hardening-v2` |
| START_HEAD | `3cff2986982fe89ed2ba9082f6392ddb8cc7974a` |
| Agent 8212 | PID 88549, launched with `PO_AGENT_EXPECTED_HEAD=3cff298…` (production-equivalent) |
| Task API 8241 | PID 81954 (log `/private/tmp/qa215d_taskapi.log`) |
| MCP-SWTR 3000 | PID 29268 |
| UI 5175 | PID 47416 (`[::1]`, vite proxy → 8212) |
| Frozen baseline | A215D/E/F2/G = GREEN (member-time freeze `0a7274b`; checkpoint tag not published locally/remotely, same as A211) |

Batch 3 scope: `team.competency_match`, `team.assignee_recommendation`, `team.bottlenecks`, `team.distribution`, `release.scope` — plugin `builtin.batch3.team_release` (`wave_batch3.py`, 285 lines) + `test_agent_core_v4_batch3.py` (146 lines).

## Phase 0 — Architecture invariants: PASS (6/6)

1. Branch pulled; START_HEAD recorded; tracked worktree clean (only QA artifacts untracked).
2. `git diff 0a7274b..HEAD` = docs only (`GIGACODE_NEXT_ACTION.md`). Batch 3 implementation predates the freeze: `44cf860` (1 file: `wave_batch3.py`, +285) + `3c00457` (1 file: tests, +146).
3. **Plugin-registry only**: the two commits touch nothing else; no Agent Core/planner/runtime/session-context edits.
4. Grep audit: all other occurrences of the five capability names are legacy non-V4 paths (`runtime.py`, `dialogue_runtime.py`, `team_intelligence.py`, `skill_catalog.py`, …); Batch 3 has zero core references.
5. All five skills carry `CompletionContract` (data_keys) + `UIContract` (widget + required fields) in the plugin.
6. dummy-55 / plugin-registry invariants: 19/19 pass.

## Phase 1 — Tests: GREEN

| Suite | Result |
|---|---|
| `test_agent_core_v4_batch3.py` | 6/6 pass |
| `test_agent_core_v4*.py` + `test_v4*.py` | 185/185 pass (A215G parity) |
| Full suite vs pre-Batch-3 worktree (`44cf860^`) | HEAD failure set is a **strict subset**: base 25F/11E → HEAD 23F/11E (2 legacy failures fixed by later commits: `test_team_capacity_never_defaults_to_40…`, `test_as21_diagnostics_reports_runtime_wiring_without_secrets`). **Zero new failures.** Remaining 23F/11E are the pre-existing legacy/real-LLM-integration baseline classes. |

## Phase 2 — Fresh REAL AS21 oracle (2026-09-25)

Independent raw-route oracle replicating the production mapping (statusType category → is_open/is_completed; `normalize_task_status` name map; `NEED_INFO` = blocked; login > externalId > display member identity):

| Sprint | Total | Completed | Open | WIP | Blocked | Active |
|---|---|---|---|---|---|---|
| DMS-SPRNT-3 (DMS) | 73 | 18 | 55 | 31 | 2 (DMS-352, DMS-379 — A208/A210 parity) | 55 |
| OLP-SPRNT-8 (OLP) | 69 | 2 | 67 | 51 | 6 (OLP-2986/3059/3118/2906/3204/3133) | 67 |

- Drift: DMS-SPRNT-3 68 → 73 tasks since A210 (new tasks carry no worklogs — P9 consistent).
- Release catalogs: WMB `[24Q1=7a84006f-7823-4052-ae46-b94f5165518e, 24Q2, 25Q1]`, OLP `[1.6.0=20ba588e-9b7e-43b2-b78a-465bdec0669a]`, DMS `[]`.
- Bounded `task-query?space=&release=` → **0 rows** for 24Q1 and 1.6.0 (release→task linkage unpopulated — A212 state retained).

## Phase 3 — team.bottlenecks: GREEN (5/5 required forms, exact parity, 2 spaces)

All five: `COMPLETED` + `runtime_contract`, rows **exactly equal** to oracle (member / active_tasks / share_percent / wip / blocked / reasons), `semantics=descriptive_task_concentration_not_employee_performance`, warning `descriptive_operational_metric_not_employee_score`, `source=REAL_AS21`:

| Form | Space | Result |
|---|---|---|
| «Узкие места команды DMS в текущем спринте» | DMS | PASS (34.4s) |
| «Где у команды OLP возможны бутылочные горлышки в текущем спринте?» | OLP | PASS (52.4s) |
| «bottlenecks команды OLP в текущем спринте» | OLP | PASS (28.6s) |
| «Узкие места в текущем спринте OLP» | OLP | PASS (33.1s) |
| «Найди узкие места команды DMS в спринте DMS-SPRNT-3» | DMS | PASS (58.4s) |

No employee scoring/ranking language; no worklog/utilization used as a hidden performance score.

**Non-blocking F1 (pre-existing planner-routing class, A210-F1/A215-F2 lineage):** 4 adjacent phrasings deterministically route to sibling `team.*` skills — «концентрации нагрузки» → `team.workload` (3/3), «Кто перегружен…» → `team.workload`, «Концентрация и блокировки…» → `team.blocked`, «задачи копятся» → `team.wip` (31 = exact oracle WIP total). Every adjacent route `COMPLETED` with source-accurate data; no fabrication.

## Phase 4 — team.distribution: GREEN (5/5 required forms, exact parity, 2 spaces)

| Form | Space | Result |
|---|---|---|
| «Распределение задач команды DMS в текущем спринте» | DMS | PASS (43.9s) |
| «Как распределены задачи в текущем спринте OLP?» | OLP | PASS (35.6s) |
| «team distribution DMS current sprint» | DMS | PASS (16.5s) |
| «Покажи распределение задач по исполнителям в текущем спринте OLP» | OLP | PASS (34.9s) |
| «Распределение задач и статусов команды DMS в текущем спринте» | DMS | PASS (24.3s) |

Exact: `total_tasks` (73/69), all 13/13 member rows (tasks/wip/blocked) and per-member `status_distribution` preserving **raw source labels** (incl. `Закрыт`, `Зарегистрирован`, `На исправлении`, `In review`, `Ready for QA`).

**Non-blocking (F1 class):** «Как разделены задачи между исполнителями в спринте OLP-SPRNT-8» → `sprint.resolve` + `task.search`; answer honestly states no assignee breakdown in available data (69 tasks confirmed), zero fabrication.

## Phase 5 — team.competency_match: GREEN (typed fail-closed, zero inference)

5/5 forms reach `team.competency_match` (after `space.resolve` + authoritative current-sprint resolution) and terminate:
`status=FAILED`, `warnings=[v4_capability_unavailable]`, error:
`team.competency_match for <SPACE>/<SPRINT> requires an authoritative competency/skill source; REAL AS21 currently exposes task assignment/state but not validated team competencies`.

Forms: DMS «Команда … подходит задача по фронтенду», DMS «Какие компетенции есть», OLP «Сопоставь навыки», EN «Which DMS team members have the right skills…», OLP «Оцени компетенции…». No live competency source exists (no MCP tool, no task attribute, no roster metadata used as truth). **Zero inferred competencies** from tasks/worklogs/utilization/assignment history.

## Phase 6 — team.assignee_recommendation: GREEN (typed fail-closed, zero recommendations)

5/5 forms (RU + EN, DMS + OLP) terminate:
`status=FAILED`, `warnings=[v4_capability_unavailable]`, error:
`team.assignee_recommendation for <SPACE>/<SPRINT> requires source-backed competencies and availability; the current source contract is insufficient for a defensible assignee recommendation`.

No ranking/scoring/best-assignee language; no workload/time-spent/utilization→competence conversion; no default-capacity inference; **no fabricated assignee**.

## Phase 7 — release.scope: GREEN on required forms (canonical UUID + bounded path + typed SOURCE_CONDITIONAL)

Production chain verified in code and live: `release.scope` → `adapter.get_release_tasks(release_id, space)` → `project = X AND release = Y` → hardened search_tasks → bounded `GET /swtr-read/task-query?space=X&release=Y&limit=100&max_pages=100`.

| Form | Trajectory | Result |
|---|---|---|
| «Покажи scope релиза 24Q1 в WMB» | space.resolve → release.search(require_single) → release.scope(`7a84006f…`, WMB) | typed FAILED `v4_capability_unavailable`: "requires authoritative release-to-task membership; the current REAL AS21 task source does not expose populated release linkage" (30.2s) |
| «release scope OLP 1.6.0» | space.resolve → release.search(require_single) → release.scope(`20ba588e…`, OLP) | same typed fail-closed (10.3s) |

- release_id in the capability call is the **canonical UUID from validated release.search** — never the name.
- **count=0-as-proof never rendered**; no tenant-wide scan (audit: 12 release task-queries, all `space=`+`release=`).

**Non-blocking findings (deterministic 2/2, both fail-closed, no fabrication):**
- «Задачи в релизе 1.6.0 в OLP» → planner picks core `release.resolve(reference=1.6.0, space=OLP)` (name-based resolve unsupported by that capability) → typed `NEEDS_CLARIFICATION` (clarification_id present, no options — free-text shape, A193 class).
- «Состав релиза 24Q1» (product-only, no space) → `release.search` without space → `/versions?query=24Q1` → 400 "space required" → typed FAILED `source_protocol_error`.

## Phase 8 — Browser C: GREEN (5/5)

Real UI (`[::1]:5175` → agent 8212), screenshots in `qa_216_browser_c/`:

| Case | Backend | UI check |
|---|---|---|
| C1 bottlenecks DMS | COMPLETED `team.bottlenecks` | exact table (55 active / 9 rows), REAL_AS21 + semantics flag visible, no leak |
| C2 distribution DMS | COMPLETED `team.distribution` | 73 tasks / 13 members, raw source status labels visible |
| C3 competency OLP | FAILED typed | typed message rendered (no generic error), no ranking |
| C4 recommendation DMS | FAILED typed | typed message rendered, no recommendation |
| C5 release scope WMB | COMPLETED | honest identity (canonical UUID) + «Детали scope … в текущих данных не представлены», `bounded=true`, no count=0-as-proof |

No fake metrics, no generic error where typed source-conditional applies, no session/trace leaks, no stale «AS21 вернул некорректные данные».
Note: the first Browser C pass hit a transient LLM endpoint 500 window (5/5 `HTTPStatusError` in ~3s; direct API A/B immediately after clean; rerun 5/5 green — F2).

## Phase 9 — Retained regression: GREEN (7/7 + dummy-55)

Fresh worklog oracle (DMS-SPRNT-3 period 2026-09-13…27, 73 bounded per-task reads, 355 out-of-period entries excluded):

| Check | Result |
|---|---|
| sprint.time_spent DMS-SPRNT-3 | **428.5h / 65 entries exact** (A215F2 parity); by_member exact: Kondratchikova 52.5, Moiseev 48, Zhdanov 64, Semavin 64, Garanin 72, Galtsov 40, Agataeva 40, Alekseev 48 |
| member.time_spent Semavin DMS-SPRNT-3 | **64.0h / 8 entries, by_task exact** (DMS-411 24, DMS-408 16, DMS-390 8, DMS-403 8, DMS-267 8; all 4Р_Тестирование) — A215G parity |
| member.utilization_actual | 64.0h; `numerator_source=REAL_AS21_WORKLOGS`, `denominator_source=OWNER_POLICY`; utilization consistent with 70.65h/15d policy |
| DMS-380 task.time_spent | **48.0h / 6 worklogs exact** (A215D parity) |
| team.capacity source-estimate guard | typed `v4_capability_unavailable`: "active assigned tasks do not expose source-backed estimates; an explicit capacity baseline alone is insufficient" (A215B/E parity). Bare «Утилизация команды DMS» routes to `team.utilization_actual` — documented A215F-F1 behavior, completed exact (70.65h policy capacity shown) |
| release.search WMB | [24Q1, 24Q2, 25Q1] (A212 parity) |
| release.health 24Q1/WMB | typed SOURCE_CONDITIONAL "requires authoritative release-to-task membership" (A214 parity) |
| dummy-55 | 19/19 plugin-registry/dummy tests pass |

## Phase 10 — Audit: GREEN (task-api access log, full A216 live window)

| Invariant | Result |
|---|---|
| Local factual `/api/v1/tasks` reads | **0** |
| Unscoped tenant-wide scans (`task-query` without `space=`) | **0** (15 task-queries, all space-scoped; 12 with `space=`+`release=`) |
| Bounded current-sprint source for team analytics | sprint-tasks route 200 calls — only DMS-SPRNT-3 / OLP-SPRNT-8; current-sprint route 88 calls |
| Bounded release membership path only | 12 `task-query?space=&release=` (0 rows each → typed fail-closed) |
| Mutation calls | **0** (no POST/PUT/PATCH/DELETE to `/api/v1/swtr*`) |
| versions route | 21 calls, all space-scoped (2×400 = product-only planner form, typed failure) |
| work-logs | 6010 bounded per-task reads (2 transient 502s, self-recovered by the resilient client) |

## Non-blocking findings

- **F1 — planner routing ambiguity on adjacent semantics** (pre-existing class A210-F1/A215-F2/A212-F1): 4 bottleneck-adjacent forms → `team.workload`/`team.blocked`/`team.wip`; 1 distribution form → `task.search`; «Задачи в релизе X» → `release.resolve` (no-options clarification); product-only release form → `release.search` without space (typed protocol error). All outcomes fail-closed or source-accurate; zero fabrication; zero unscoped scans.
- **F2 — transient LLM endpoint 500 window** during the first Browser C pass (self-resolved; rerun green).
- **F3** — `/health` unscoped full-scan hang (A195B F2) unchanged; out of A216 scope.

## Conclusion

All five Batch 3 skills are registry-discovered, contract-complete, and behave per contract against live REAL AS21: bottlenecks/distribution exact-parity descriptive analytics; competency/recommendation/health-class fail-closed typed guards with zero inference or fabrication; release.scope canonical-UUID bounded path terminating SOURCE_CONDITIONAL under unpopulated linkage (never count=0). No architecture drift, no test regressions, zero local reads / unscoped scans / mutations.

**Verdict: `AGENT_CORE_V4_BATCH3_FIVE_SKILL_GREEN`**

**Recommendation:** create the immutable Batch 3 checkpoint and proceed to owner implementation of Batch 4.
