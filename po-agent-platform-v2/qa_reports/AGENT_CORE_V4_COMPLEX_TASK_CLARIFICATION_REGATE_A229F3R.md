# A229F3R — complex task clarification re-gate (period constraint coverage)

**Verdict: `AGENT_CORE_V4_COMPLEX_TASK_CLARIFICATION_GREEN_A229F3R`**

- **Branch:** `feat/core8-real-query-hardening-v2`
- **START_HEAD / TESTED_HEAD:** `6fb335d6f67344245a5c65e5c1b5b145759e96da`
- **Previous verdict:** `AGENT_CORE_V4_COMPLEX_TASK_CLARIFICATION_RED_A229F3` (report `764e96f`)
- **Previous first failing boundary:** P4-A planner silently omitted the user-requested `created_period` and still COMPLETED an over-broad task result in 3/6 runs.
- **Date:** 2026-10-09
- **Role:** QA/source-forensics/browser testing only. No production code modified.

---

## Owner fix under test

Commits on the branch since the RED report `764e96f` → `6fb335d` (3 production files, 227+/14-):

1. **Catalog hardening** — `task_catalog.py`: `task.search_created` and `task.type_analysis` procedures now explicitly forbid silently dropping a user-requested period (pass raw wording for typed fail-closed parsing, or ask clarification).
2. **API/dialogue postcondition guard** — `api/v1/__init__.py` (+163): `_guard_completed_constraint_coverage`, applied after `_promote_planner_failure_to_clarification` inside `_run_query`. For a COMPLETED response whose original query matches a conservative period-intent regex (`период`, `за последние N день(ей)`, `с DD.MM.YYYY`, …) and whose executed `task.*` results carry **no** non-empty `created_period`, the response is converted to `NEEDS_CLARIFICATION`: answer→null, over-broad `results` removed from `data`, evidence cleared, typed warning `v4_constraint_coverage_clarification`, `constraint_coverage_failure={constraint: created_period, reason: requested_but_not_applied}` recorded. The guard does not route, infer, re-execute, or query AS21.
3. **Tests** — `test_v4_browser_api_contract.py` (+122): silent drop → clarification (results/evidence stripped), applied `created_period` → COMPLETED unchanged, non-period task query → COMPLETED unchanged.

## P0 — integrity / tests: GREEN

- `git pull --ff-only` clean; tracked worktree clean (only untracked QA artifacts + local GIGACODE.md memory).
- **Core 6/6 byte-identical** to certified checkpoint `afb6fa1d9b6e5d13a5d743f0d45afef94d1821a1` (`agent_core_v4.py`, `agent_core_v4_robust.py`, `agent_core_v4_reliable.py`, `agent_core_v4_completion.py`, `v4_plugin_registry.py`, `llm/real.py`) — `git diff afb6fa1..6fb335d` over the six files is empty.
- Focused suites: `test_agent_core_v4_task_created_period.py` + `test_agent_core_v4_task_semantics_hierarchy.py` + `test_agent_core_v4_task_catalog.py` + `test_v4_browser_api_contract.py` → **39/39 passed** (includes the 3 new guard tests).
- Full V4 blast (`test_agent_core_v4*.py` + `test_v4*.py`) → **258/258 passed**.
- Task API SWTR suites (9 files) → **57/57 passed**.
- Frontend `npm run build` (tsc + vite) → **exit 0**.
- Agent restarted fresh on `6fb335d` (PID 77981, `/health` 200, `PO_AGENT_EXPECTED_HEAD=6fb335d…`, `TASK_API_BASE_URL=http://127.0.0.1:8241` override, `PO_AGENT_AGENT_CORE_V4_ENABLED=true`).

## P1 — exact previous failing boundary: GREEN (A229F3 P4-A CLOSED)

Query: `Открытые задачи Семавина с типом дефект в DMS за период`

**6/6 valid runs** (90 s spacing, zero provider-invalid reruns in the session):

| run | status | path | wall | clarification_id | question mentions period | reformulation examples | DMS-431/any task key exposed | results payload |
|---|---|---|---|---|---|---|---|---|
| 1 | NEEDS_CLARIFICATION | A planner-native | 55.07 s | yes | yes | yes | no | absent |
| 2 | NEEDS_CLARIFICATION | A planner-native | 45.67 s | yes | yes | yes | no | absent |
| 3 | NEEDS_CLARIFICATION | A planner-native | 10.26 s | yes | yes | yes | no | absent |
| 4 | NEEDS_CLARIFICATION | A planner-native | 36.47 s | yes | yes | yes | no | absent |
| 5 | NEEDS_CLARIFICATION | A planner-native | 16.35 s | yes | yes | yes | no | absent |
| 6 | NEEDS_CLARIFICATION | A planner-native | 35.64 s | yes | yes | yes | no | absent |

- **Zero silent COMPLETED without the requested period — zero over-broad results.** The A229F3 3/6 silent-drop mode is closed; every run took **safe path A** (planner-native clarification after the catalog hardening, warnings `v4_planner_needs_clarification`).
- **Backstop (path B) proven separately**: the unit probe of `_guard_completed_constraint_coverage` on the exact A229F3 over-broad payload (task.type_analysis without `created_period`, query with period intent) converts COMPLETED → NEEDS_CLARIFICATION with `results` removed, `evidence` cleared, `constraint_coverage_failure={created_period, requested_but_not_applied}`; applied-period / non-period-intent / non-task-capability / FAILED / already-clarified responses pass through untouched (7 intent-regex checks + 6 coverage cases, all OK). So even if the planner ever regresses to a silent drop, the public answer becomes a typed clarification, not an over-broad task list.

**Clarification continuation** (answered `Период создания задач: с 30.09.2026 по сегодняшний день`, same session, `clarification_id` from run 6):

- COMPLETED, wall 40.04 s, prepass=false, completion=`runtime_contract`.
- Terminal `task.type_analysis` with **all 5 constraints in one call**: `{task_type: "дефект", reference: "Семавин", space: "DMS", status: "open", created_period: "с 30.09.2026 по сегодняшний день"}` — original goal preserved, full original request not repeated.
- **Exact REAL AS21 oracle parity**: count 0, keys [] (REAL_EMPTY, drift 0: corpora fetched before 16:17 and after 17:11 both 174 Semavin+DMS rows, 0 missing created_at; window 30.09.2026 00:00 MSK → execution time contains 14 open tasks, all type `task/Задача` — zero open defects in window). `type_breakdown=[{task, Задача, 4}]` equals the exact open-window defect-excluded composition. The answer honestly states: 4 open tasks in the period, all «Задача», no defects.
- Browser-side free-text continuation (P4-A test, same boundary): t1 NEEDS_CLARIFICATION (`v4_planner_needs_clarification`) → typed answer → t2 COMPLETED `task.type_analysis` `{дефект, Семавин, DMS, not_completed, с 30.09.2026 по сегодня}` count 0.

## P2 — false-positive guard controls: GREEN (10/10, 0 false clarifications)

| case | query | runs | terminal | result vs oracle |
|---|---|---|---|---|
| C1 | Открытые задачи Семавина с типом дефект в DMS | 2/2 | task.type_analysis (no period) | COMPLETED count 1 = [DMS-431] = all-time open defects EXACT (guard inert) |
| C2 | … в DMS с 30.09.2026 | 2/2 | task.type_analysis, created_period applied | COMPLETED 0 = oracle 0 REAL_EMPTY EXACT (open window 4, all Задача) |
| C3 | … в DMS за последние 2 дня | 2/2 | task.type_analysis, created_period applied | COMPLETED 0 = oracle 0 EXACT (open window 1) |
| C4 | Открытые задачи Калачанова в WMB за последние 2 дня | 2/2 | task.search_created, status=not_completed | COMPLETED 0 = oracle 0 REAL_EMPTY EXACT (6-row WMB corpus, drift 0) |
| C5 | Задачи Калачанова в STS за 1 день | 2/2 | task.search_created | COMPLETED **26/26 EXACT** vs independent MCP-derived oracle (2815-row corpus, drift 0) |

No false `NEEDS_CLARIFICATION` from the new guard; no guard intervention recorded on any of the 10 runs (`constraint_coverage_failure` absent).

## P3 — full complex-query regression: GREEN (12/12 EXACT)

Fresh independent REAL AS21 oracles (MCP-direct corpora fetched immediately before the batch: c1=2815 STS+Kalachanov rows, c2=6 WMB+Kalachanov, c3=174 DMS+Semavin; after-fetch counts identical → **drift 0** for the whole window):

| case | query | runs | terminal | parity |
|---|---|---|---|---|
| P1 | Задачи Калачанова в STS за 1 день | 3/3 | task.search_created | **26/26 EXACT** keys, constraints (reference+space+created_period) all present |
| P2 | Открытые задачи Калачанова в WMB за последние 2 дня | 3/3 | task.search_created (+status=not_completed) | 0 = oracle 0 REAL_EMPTY EXACT |
| P3 | Открытые задачи Семавина с типом дефект в DMS с 30.09.2026 | 3/3 | task.type_analysis (5 constraints) | 0 = oracle 0 EXACT; type_breakdown [Задача:4] = exact open window |
| P4 | … в DMS за период с 30.09.2026 по сегодняшний день | 3/3 | task.type_analysis (5 constraints, raw period wording preserved) | 0 = oracle 0 EXACT; type_breakdown [Задача:4] |

All 12 runs: prepass=false, completion=runtime_contract, all requested constraints present in the single terminal call, 0 local reads, 0 tenant scans.

## P4 — clarification / error taxonomy: GREEN

- **Free-text clarification continuation** (browser, P4-A test): COMPLETED, exact terminal args, honest answer. ✅
- **Option-button (deterministic) clarification + continuation** (browser, P4-B test, 46.3 s): t1 `Задачи Гаранина в сентябрьском спринте` → typed NEEDS_CLARIFICATION with space options `[CRPV, DMS, OLP, STS, WMB]` → click **DMS** → continuation POST carries `clarification_id` + option → COMPLETED `task.search {assignee: Garanin.R.V, sprint_id: DMS-SPRNT-3, space: DMS}` count 0 (honest: sprint FINISH, 0 tasks — matches live source where SPRNT-3 is finished; agent also reports the sprint status in the answer). ✅
- **Provider / source / internal taxonomy** (unit probe `qa_229f3_p4c_taxonomy.py`, 11/11): period-syntax / planner-repair / step-budget / ungrounded → `NEEDS_CLARIFICATION` (user ambiguity, resumable); provider 429 / timeout / connect, source unavailable, source missing created_at, internal runtime/contract → `FAILED` (not disguised as user ambiguity). ✅
- Note: the first two P4-B browser attempts hit the test-side 360 s polling window before the (slow, ~30–90 s) continuation response landed; the agent log proves the continuation executed correctly (`task-query?assignee=Garanin.R.V&space=DMS` + `sprints/DMS-SPRNT-3/tasks` → 200). The re-run with a 480 s window passed. Environmental (LLM endpoint latency), not a product defect.

## P5 — architecture / no-router audit + retained gates: GREEN

- Core 6/6 byte-identical (P0); production delta limited to `api/v1/__init__.py` + `task_catalog.py` (+ `_task_live_handlers.py` from A229F3, unchanged by this fix).
- **No query-specific route**: delta contains no `SkillSpecV4`/`CapabilitySpecV4`/`CapabilityBindingV4` additions (0), no new capabilities/skills. Registry inventory unchanged: **13 plugins / 72 skills**, canonical 54 intact.
- **No hardcodes** in the delta: 0 person names, 0 space literals; the only date strings are the human-readable clarification *example sentence* ("например: «с 30.09.2026 по сегодня»…") — presentation text, not logic.
- The guard is **post-execution fail-closed validation only**: regex intent signal + executed-`task.*`-with-no-applied-`created_period` → converts presentation/dialogue state; it never creates factual values, never re-runs capabilities, never routes (unit-verified: non-task trajectories, applied period, and no-intent queries pass through byte-unchanged).
- **0 local fallback reads, 0 mutations** (session-wide HTTP audit: 339 GET source, 283 POST LLM, 0 PUT/DELETE/PATCH, 0 `GET /api/v1/tasks`), **0 tenant-wide scans** (every task-query/assignee-tasks/assignees-resolve call carries space/assignee/reference), **0 5xx** on either plane.
- Retained gates:
  - **task type + latest sprint**: `Задачи с типом дефект в текущем спринте DMS` → space.resolve → sprint.current → DMS-SPRNT-4 (source rolled current sprint overnight: SPRNT-3 FINISHED, SPRNT-4 IN_PROGRESS) → task.type_analysis → **4 defects [DMS-402, DMS-431, DMS-456, DMS-461] EXACT** vs independent oracle (34/34 complete membership_proven collection; `task_type_code` bug-set = the same 4 keys; each of the 4 point-read `unit.suit = {bug, Дефект}`; control DMS-399 also a bug but not a SPRNT-4 member — correctly excluded). ✅
  - **hierarchy**: `Покажи иерархию задачи DMS-267` → task.hierarchy inspect → `CRPV-90180 → DMS-253 → DMS-267`, depth 2, epic DMS-349 — exact vs relations oracle (mcp:get_unit_links, parent DMS-253, no ambiguity). ✅
  - **Overview KPI** (browser): snapshot filled after load — Активно 80 / Завершено 34 / Заблокировано 5, attention queue 58 (DMS-427 blocked·aging, OLP-3304…) — grounded, no «Дай обзор и риски»-style injected POST (only the 3 standard snapshot queries: очередь внимания, daily brief, status report). ✅
  - **task drawer** (browser): bounded query «Задачи в спринте DMS-SPRNT-4» → 34 cards (matches oracle total) → card DMS-466 opened, drawer rendered, details visible. ✅

## P6 — latency observation (no optimization in this assignment)

- LLM calls per query: 2–9 (P1 clarification runs: 6, 6, 2, 4, 4, 9, 4, 4 incl. continuation); session total 283 LLM + 339 source calls, **0 × 429, 0 × 5xx on both planes** — the provider was healthy all session (contrast A229F3, which needed cooldowns).
- P1 walls 10.3–55.1 s; continuation 40.0 s; P2/P3 walls 11.4–98.5 s (STS 1-day scans are the slowest at 71–99 s, matching the A229R1 known bottleneck class).
- **Guard effect**: the guard was never the visible savior on this HEAD (path A planner-native 6/6) — the catalog hardening changed planner behavior; the guard remains the proven backstop for any future silent-drop regression (unit-verified on the exact A229F3 payload). No measurable guard overhead on passing queries (pure in-memory postcondition check).

## Non-blocking observations

- F1 (environmental): LLM endpoint latency 30–90 s per trajectory in the browser phase; P4-B first attempts expired the test polling window before the response. Suggest longer browser-test windows in the harness (480 s used here).
- F2 (source drift, expected): DMS current sprint rolled SPRNT-3 → SPRNT-4 between A229F3 and this re-gate; «сентябрьский спринте» still resolves to DMS-SPRNT-3 (the September sprint) and correctly reports FINISH.
- F3 (route): the sprint-collection rows expose `task_type_code` but not `swtr_suit` under the A229S1 name; suit verification for R1 required point reads / `task_type_code`. Not a defect (both fields are source-backed).

## QA artifacts

- `qa_229f3r_p1_runner.py`, `qa_229f3r_p2p3_runner.py`, `qa_229f3r_retained.py` (repo root, untracked); `frontend/e2e/qa229f3-clarification.spec.ts` (edited OUT path + P4-B polling), `frontend/e2e/qa229f3r-retained.spec.ts`.
- Evidence: `/private/tmp/qa229f3r/` (p1.json, p1.log, p2p3_runs.json, p2p3_parity.json, p4_browser.json, p5_browser.json, retained.json, p6_p1_latency.json); agent log `/private/tmp/qa229f3r_agent.log`.

## Recommendation

1. Freeze a small checkpoint on TESTED_HEAD `6fb335d` (e.g. `checkpoint/v4-complex-task-clarification-green-a229f3r`).
2. Resume **A229R2** (planner-turn reduction latency gate) — this functional gate is GREEN and no planner/Core changes are in flight.

**Services left running:** agent 8004 (PID 77981 @6fb335d), task-api 8241, MCP 3000, vite [::1]:5175.
