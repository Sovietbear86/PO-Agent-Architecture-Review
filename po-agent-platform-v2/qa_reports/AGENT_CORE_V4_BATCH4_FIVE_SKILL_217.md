# A217 — Agent Core v4 Batch 4 Five-Skill Gate

**Verdict:** `AGENT_CORE_V4_BATCH4_FIVE_SKILL_RED`
**Classification:** `RED_NL_ROUTING_EARLY_READY_BYPASSES_TYPED_SC`
**START_HEAD / test base:** `a8587e2c599e589f23770338c510f8e207fea5d5`
**Date:** 2026-09-25

---

## Owner Batch 4 under test

Five registry-discovered skills in plugin `builtin.batch4.release_portfolio`
(`wave_batch4.py`, 385 lines; `test_agent_core_v4_batch4.py`, 168 lines):
1. `release.progress`
2. `release.blockers`
3. `release.dependencies`
4. `release.risk_queue`
5. `portfolio.overview`

Owner commits: `828a005` (feat), `3d29ec6` (tests). Freeze docs: `9c88de8`, spec `a8587e2`.

Services: UI 5175 (PID 47416, [::1]), agent 8212 (PID 36624 @ a8587e2), task-api 8241
(PID 81954, system python3, SSE 48 tools), MCP-SWTR 3000 (PID 29268).

Note: spec's checkpoint tag `checkpoint/v4-batch3-green-a216` does not exist (same as
A211/A216 — tag never published). Diff base used: `8c95c36` (A216 report commit = Batch 3 GREEN state).

---

## Phase 0 — architecture invariant: GREEN

1. `git diff --stat 8c95c36..HEAD` = exactly 4 files: `GIGACODE_NEXT_ACTION.md`, `V4_DOD_LOCK.md`,
   `wave_batch4.py`, `test_agent_core_v4_batch4.py`. Batch 4 is plugin-registry only.
2. Zero Agent Core / planner / runtime / session-context / adapter / task-api edits.
3. All 5 skills have `CompletionRequirement` (data keys present in their capability data) and
   `UIContractV4` (widgets: release_progress, task_table, dependency_graph, risk_queue, portfolio_overview).
4. WIP predicate in `build_portfolio_overview` is byte-identical to the certified `wave_s1._is_wip`
   (`_WIP_BACKLOG_TYPES = {open,todo,backlog,registered}` + status_category!=backlog).
5. Release analytics share `_release_tasks` which raises `V4CapabilityUnavailable`
   ("release-to-task membership") on empty membership — fail-closed before any metric.
6. `portfolio.overview` iterates `sorted(APPROVED_PRODUCT_SPACES)` = {CRPV, DMS, OLP, STS, WMB};
   re-raises source exceptions (no hidden empty rows); explicit `NO_CURRENT_SPRINT` and
   `CURRENT_SPRINT_WITHOUT_MEMBERSHIP` states; bounded reads only
   (`get_current_sprint_id` per space + `get_sprint_tasks(complete=true)`).
7. dummy-55 / plugin registry invariant: `test_agent_core_v4_plugin_registry.py` 13/13 GREEN.

## Phase 1 — tests: GREEN

- `test_agent_core_v4_batch4.py`: **5/5** pass.
- Full V4 retained: `test_agent_core_v4*.py` + `test_v4*.py` = **190/190** pass (185 retained + 5 new).
- Zero unexplained failures.

## Phase 2 — fresh REAL AS21 release + portfolio oracle: GREEN

Release catalogs (bounded `/swtr-read/versions?space=`):
- WMB: 3 — `[24Q1=7a84006f-7823-4052-ae46-b94f5165518e, 24Q2=460d173f-2296-443b-87ea-a550cd68a945, 25Q1=4a1199c2-ac50-4490-adab-0aafb3d7e556]` — exact A212 parity.
- OLP: 1 — `[1.6.0=20ba588e-9b7e-43b2-b78a-465bdec0669a]` — exact A212 parity.
- DMS: 0 (REAL_EMPTY). CRPV/STS: 100 (route cap; platform releases, targets absent).

Bounded release membership (`task-query?space=<s>&release=<uuid>`, limit=100, max_pages=100):
- WMB 24Q1 → **0 rows**; OLP 1.6.0 → **0 rows**. A214 source state retained:
  release→task linkage unpopulated ⇒ all four release analytics must terminate typed SOURCE_CONDITIONAL.

Portfolio oracle (per space: current-sprint route → `sprints/{id}/tasks?complete=true` → certified
predicates via production `TaskApiAS21Adapter._map` + `is_completed/is_open/is_blocked` + wave_s1 WIP):

| space | state | sprint | total | completed | open | blocked | wip |
|---|---|---|---|---|---|---|---|
| CRPV | NO_CURRENT_SPRINT | — | — | — | — | — | — |
| DMS | SOURCE_BACKED | DMS-SPRNT-3 | 73 | 18 | 55 | 2 (DMS-352, DMS-379) | 31 |
| OLP | SOURCE_BACKED | OLP-SPRNT-8 | 70 | 2 | 68 | 6 (OLP-2906/2986/3059/3118/3133/3204) | 52 |
| STS | NO_CURRENT_SPRINT | — | — | — | — | — | — |
| WMB | SOURCE_BACKED | WMB-SPRNT-2 | 1 | 1 | 0 | 0 | 0 |

Drift vs A216: OLP 69→70 tasks; WMB now has a current sprint (1 completed task); DMS unchanged (73/18/55/2/31).

## Controlled fixture probes (owner-independent): 29/29 GREEN

`qa_217_fixture_probe.py` (QA probe, owner tests not modified):
- progress complete-estimates: total 20.0h, completed 12.0h, 60.0%, coverage 100%, no warnings.
- progress missing estimate (even on completed task): `effort_progress=None` + warning, counts still exact — **never zero-filled**.
- zero-estimate edge: total 0.0, `completion_percent=None` (no 0/0 division).
- blockers: exact blocked key set (includes blocked+completed rows).
- dependencies: exact internal/external partition incl. self-dependency; count 5.
- risk queue: exact deterministic scores `{K-B:100(cap), K-C:50, K-P:30, K-U:25, K-H:15}`, exact reasons,
  exact order (-score, key), zero-score tasks excluded, `scoring_version=release_risk_v1`.
- All four release builders fail closed with the typed membership message on empty membership.

## Phase 3 — release.progress: **RED (first failing boundary)**

Spec expectation: `space.resolve -> release.search -> release.progress -> typed source conditional`.

Observed across **14 live attempts** (3 spec forms + 2 re-probe forms):

| form | attempts | outcome |
|---|---|---|
| `прогресс релиза 24Q1 в WMB` | 7 (1+3+3) | **7/7 early-termination**: calls = [space.resolve, release.search] only, status=COMPLETED, completion=`runtime_contract`, honest "no progress data" answer. `release.progress` never loaded/invoked. |
| `готовность релиза OLP 1.6.0` | 4 (1+3) | **4/4** FAILED `warnings=["source_protocol_error"]`: planner calls `release.search` **without space** → `/versions?limit=100&query=OLP+1.6.0` → 400 (route requires space). Trajectory dies typed; `release.progress` never reached. |
| `release progress for 24Q1 in WMB` | 4 (1+2+1) | 1/4 correct (space.resolve→release.search→release.progress → typed `v4_capability_unavailable`); **3/4 early-termination**. |
| `здоровье релиза 24Q1 в WMB` (retained, P9) | 2 | **2/2 early-termination** of the pre-existing `release.health` (A214 had certified this phrase 3/3 typed). |

Typed SOURCE_CONDITIONAL for release.progress: **1/14** (7%). Zero fabrication in all runs (honest
answers, canonical UUID in text, empty evidence).

**Root cause (proven by trajectory dump, 4/4 identical signature):**
- Planner turn 1 loads only the `release.search` skill (rationale: "resolve identity … *then*
  query its progress" / "then use release.health or release.progress").
- After the `release.search` observation, the deterministic completion check
  (`agent_core_v4.py:1309`, "deterministic skill completion contract satisfied") mints terminal
  `ready` with `completion=runtime_contract`, because the only loaded skill's contract
  (`release.search`, `wave_s1.py:425`, `data_keys=("releases","count")`) is already satisfied.
- The intended analytics capability is never loaded ⇒ its contract (which would have blocked the
  premature READY and forced the typed `V4CapabilityUnavailable`) never enters the frontier.

For contrast, `release.blockers/dependencies/risk_queue` work because the planner loads the correct
analytics skill for those intents; its unsatisfied contract blocks the premature READY, so the
capability executes and fails closed typed.

Classification: same lineage as A200 D-A200-1 / A199 F3 (planner mis-route to identity-only skill +
semantic-agnostic completion frontier), now on the fresh-query release-metric-intent boundary.
**Not a Batch 4 plugin defect**: capability logic proven correct (fixtures 29/29 + the 1/14 routed
run + all three sibling skills), and the same early-termination now also hits the pre-existing
`release.health`.

## Phase 4 — release.blockers: GREEN (12/12)

9/9 (initial) + 3/3 (re-probe): `space.resolve → release.search(require_single) → release.blockers`
with canonical UUIDs; `warnings=["v4_capability_unavailable"]`,
`v4.error = "release analytics require authoritative release-to-task membership; the current REAL
AS21 source does not expose populated release linkage"`; status=FAILED (typed fail-closed),
empty evidence, zero "0 blockers" facts.

## Phase 5 — release.dependencies: GREEN (4/4)

3/3 + 1 re-probe: same typed SOURCE_CONDITIONAL; no empty dependency graph rendered as source fact.

## Phase 6 — release.risk_queue: GREEN (4/4)

3/3 + 1 re-probe: same typed SOURCE_CONDITIONAL; no fabricated queue rows;
`risk_score_is_deterministic_operational_priority_not_employee_score` semantics retained in code.

## Phase 7 — portfolio.overview REAL AS21: GREEN (5/5 runs)

3 spec forms + 2 re-probes, all COMPLETED, `portfolio.overview` executed, **exact row parity for all
5 spaces** vs the Phase 2 oracle (table above), including `NO_CURRENT_SPRINT` with null metrics for
CRPV/STS and the WMB 1/1/0/0/0 row. Answer: "Портфель: 3/5 пространств … заблокировано 8 задач"
(2+6+0=8 exact).

## Phase 8 — Browser C: 2/3 (C2 consequence of D-A217-1)

- C1 `обзор портфеля продуктов`: COMPLETED, portfolio widget data, all 5 spaces + real numbers
  visible (DMS-SPRNT-3/73, OLP-SPRNT-8, WMB-SPRNT-2). OK.
- C2 `прогресс релиза 24Q1 в WMB`: UI shows the honest early-termination answer ("no progress data");
  **no typed source limitation** surfaced (early-termination class). No generic error, no leak, no fake %.
- C3 `очередь рисков релиза 1.6.0 в OLP`: FAILED typed — membership limitation clearly visible,
  no fake queue. OK.
- Screenshots: `qa_217_browser_c/`.

## Phase 9 — retained regression: GREEN (after correcting QA oracle yardstick)

- bottlenecks DMS: COMPLETED, sprint DMS-SPRNT-3, active_tasks=55, 9 rows. EXACT.
- distribution DMS: COMPLETED, total_tasks=73, 13 members. EXACT.
- member.time_spent Semavin: **64.0h / 8 entries** — EXACT vs in-window oracle
  (sprint window 13–27 Sep: DMS-411 3×8h, DMS-408 2×8h, DMS-390 8h, DMS-403 8h, DMS-267 8h).
  (QA's first oracle used lifetime worklogs — wrong yardstick; certified A215F2/G window filter retained.
  Live drift: Semavin now holds 10 sprint tasks, lifetime 216h.)
- sprint.time_spent DMS-SPRNT-3: **428.5h / 65 entries** — EXACT A215F2 value (no new in-window entries).
- DMS-380 task.time_spent: **48.0h / 6 worklogs** — EXACT A215D parity (`time_spent_hours` field).
- team.capacity guard: explicit "capacity … базой 40 часов" → `team.capacity` executed → typed
  `v4_capability_unavailable` ("active assigned tasks do not expose source-backed estimates"). Guard retained.
- release.search WMB: [24Q1, 24Q2, 25Q1] EXACT.
- release.health: 2/2 early-terminated (see D-A217-1 — pre-existing skill affected).
- dummy-55: 13/13 (P1).

## Phase 10 — audit: GREEN

task-api access log (shared A215D→A217; violation classes global):
- local factual `GET /api/v1/tasks` reads: **0**
- mutations (POST/PUT/DELETE/PATCH): **0**
- `task-query`: 38 calls, **38/38 space-scoped**, 35 release-scoped (canonical UUIDs 7a84006f…/20ba588e…);
  zero unscoped tenant-wide scans. (6 space-scoped QA-oracle probes with name/None release values, all 0 rows.)
- sprint reads: 247, **all `complete=true`** (bounded); current-sprint reads: 185 (per-space bounded).
- work-logs: 6329 per-task bounded reads; versions: 74 (67 space-scoped).
- no-space `/versions` 400s: 7 — bounded, rejected before source, fail-closed (5 = "готовность" runs).
- 5xx: 2 transient work-logs 502s (DMS-334, DMS-263) — source-side, self-recovered, results unaffected.

---

## D-A217-1 (sole blocking defect)

**release-metric-intent NL queries systematically bypass the analytics capability.**
First failing boundary: Phase 3, form `прогресс релиза 24Q1 в WMB` (7/7 early-termination),
plus `готовность` 4/4 space-omission `source_protocol_error`, and the pre-existing `release.health`
(2/2 early-termination here; 3/3 typed in A214).

Mechanism (deterministic, 4/4 identical trajectories):
1. Planner loads only `release.search` (identity skill) for progress/readiness/health intents.
2. Deterministic completion check (`agent_core_v4.py:1309`) mints terminal `ready`
   (`runtime_contract`) once the loaded `release.search` contract (`("releases","count")`) is satisfied.
3. `release.<analytics>` never loads ⇒ its contract never blocks the READY ⇒ typed
   `V4CapabilityUnavailable` (the spec-required SOURCE_CONDITIONAL) unreachable (1/14 observed).
Second mode: planner omits `space` in `release.search` for "готовность" → route 400 → typed
`source_protocol_error` (fail-closed, but capability still unreachable).

Safety: intact in every run — zero fabrication, zero fake zeros, canonical UUIDs only, fail-closed.

**Proposed owner fix (platform, not Batch 4 code):**
1. Intent-pinning at the completion frontier for fresh release-metric queries (extend the A201
   `pinned_skills` mechanism beyond clarification continuations): when the query intent resolves to a
   release analytics capability, pin that skill so the deterministic READY cannot mint before it runs.
2. Planner procedure hardening for release search: `space.resolve` before `release.search` (the
   "готовность" space omission), e.g. via the skill procedure text or a deterministic arg-injection
   for `space` from the resolved observation (A199 precedent for optional resolved constraints).
3. Regression test: fresh-query release.progress trajectory must include `release.progress`
   (or the pinned-skill rejection of the premature READY) — non-mocked, against the robust runtime.

## Non-blocking findings

- **F1:** Browser C2 (release.progress UI) shows honest untyped answer — direct consequence of D-A217-1.
- **F2:** 2 transient work-logs 502s (source-side, self-recovered).
- **F3:** `/versions` route is limit=100-capped without a `complete` flag (CRPV/STS >100 releases) —
  pre-existing bounded route contract (A212), out of Batch 4 scope.
- **F4:** "утилизация команды DMS" routes to `team.utilization_actual` (certified A215F2 semantics,
  source-accurate) instead of `team.capacity` — known A215 F1 sibling-routing class; capacity guard
  separately proven with explicit phrasing.
- **F5:** spec checkpoint tag `checkpoint/v4-batch3-green-a216` absent (A211/A216 pattern); diff base
  `8c95c36` used.

## Verdict

`AGENT_CORE_V4_BATCH4_FIVE_SKILL_RED` — STOP. No Batch 5.

Batch 4 plugin code is correct and shippable (Phase 0/1 clean, fixtures 29/29, portfolio 5/5 exact,
release.blockers/dependencies/risk_queue 20/20 typed SOURCE_CONDITIONAL, audit clean). The sole
blocking boundary is D-A217-1: the platform's fresh-query release-metric routing + deterministic
completion gate bypasses `release.progress` (and now also `release.health`), so the spec-mandated
typed SOURCE_CONDITIONAL is unreachable in 13/14 attempts. Fix is platform-side (completion-frontier
intent-pinning + space-before-search), then full A217 re-gate.
