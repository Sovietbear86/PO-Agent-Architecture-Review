# A217D — Agent Core v4 Batch 4 Robust-Signature-Parity Re-Gate

**Verdict:** `AGENT_CORE_V4_BATCH4_ROUTING_GREEN_A217D`
**Classification:** `GREEN` — production robust runtime restored; full release-routing gate re-run clean
**START_HEAD / test base:** `763ce65fd7bbe1733c10f124b68f2dc8a894cf78`
**Date:** 2026-09-26

**All 8 phases PASS.** The A217C platform-wide `TypeError` is closed at the
production robust-runtime boundary; every release-routing surface from A217/A217B is
re-verified GREEN against fresh REAL AS21. No code modified (QA-only).

---

## Baseline

A217C verdict `AGENT_CORE_V4_BATCH4_ROUTING_RED_A217C`
(`RED_ROBUST_PLANNER_SIGNATURE_DRIFT`): base `SkillNativePlannerV4.next_decision` gained
`runtime_guidance` and the runtime passed it, but production
`RobustSkillNativePlannerV4.next_decision` did not accept it → deterministic
`TypeError: unexpected keyword argument 'runtime_guidance'` → 100% of V4 queries died
before LLM/source execution. F1: owner's Batch4 metadata test used a non-existent
`registry.catalog`.

## Owner fix under test

Commits:
- `b2c5319` — `RobustSkillNativePlannerV4.next_decision` now accepts
  `runtime_guidance: Mapping[str, Any] | None = None` and forwards it in the planner payload
  (`"runtime_guidance": dict(runtime_guidance or {})`), mirroring the base keyword contract.
- `1c0fa65` — Batch4 metadata test now builds `SkillCatalogV4(registry.skills(),
  registry.capability_specs())` instead of the non-existent `registry.catalog`.
- `fd6ba94` — new `tests/test_agent_core_v4_planner_signature_parity.py` locks base/robust
  `next_decision` keyword-contract equality (guards the recurring A205-1/A205B/A217C drift class).

No new release-routing logic added. Diff vs A217C `619a929` is limited to
`agent_core_v4_robust.py` (+2 lines), `test_agent_core_v4_batch4.py` (+2/−2), and the new
parity test (+26).

## Phase 0 — production runtime recovery: PASS

- Signature-parity test `test_agent_core_v4_planner_signature_parity.py` **PASS** (asserts
  robust == base params, includes `session_context` and `runtime_guidance`).
- `test_agent_core_v4_batch4.py` **9/9 PASS** (incl. the fixed metadata test).
- Agent restarted at `763ce65` (agent 8212, task-api 8241, MCP-SWTR 3000, UI 5175 all 200).
- 3 ordinary **non-release** queries through the production robust/pluginized runtime:
  - "Покажи DMS-380" → `COMPLETED runtime_contract`, `task.lookup`.
  - "Открытые задачи Жданова в DMS" → `COMPLETED runtime_contract`,
    `space.resolve → member.resolve → task.search`, **2 open [DMS-371, DMS-1]** (exact).
  - "Задачи в текущем спринте DMS" → `COMPLETED runtime_contract`,
    `space.resolve → sprint.current → task.search`, **73 tasks DMS-SPRNT-3** (exact).
- **Zero TypeError, zero `v4_runtime_failure`**, planner reaches LLM, source calls execute.
  The A217C 100%-fail boundary is closed.

## Phase 1 — full V4 regression: PASS

`test_agent_core_v4_planner_signature_parity.py` + `test_agent_core_v4_batch4.py` +
`test_agent_core_v4*.py` + `test_v4*.py` = **194/194 PASS**, zero unexplained failures.
(A217C shipped with 8 RED robust-runtime tests; all now green.)

## Phase 2 — standalone release identity: PASS (21/21)

≥5 each, all `COMPLETED`, identity-only trajectory `space.resolve → release.search`,
**zero** `release.scope/health/progress/risk_queue/blockers/dependencies` calls:

| Goal | Result | Identity (source-backed) |
|---|---|---|
| "релиз 1.6.0 в OLP" | 5/5 COMPLETED | 1.6.0 (1 UUID) |
| "релиз 24Q1 в WMB" | 5/5 COMPLETED | 24Q1 (1 UUID) |
| "релиз 25Q1 в WMB" | 5/5 COMPLETED | 25Q1 (1 UUID) |
| "релизы WMB" (list) | 3/3 COMPLETED | 24Q1, 24Q2, 25Q1 (3 UUID) |
| "покажи версии OLP" (list) | 3/3 COMPLETED | 1.6.0 (1 UUID) |

**D-A217B-1 (standalone singular identity over-extension) is CLOSED** — deterministic 5/5,
no deeper-skill pivot. List goals remain exact catalog COMPLETED.

## Phase 3 — requested release analytics: PASS (17/17)

Each requested deeper skill executes after `release.search` identity resolution and
terminates the typed `v4_capability_unavailable` SOURCE_CONDITIONAL (current REAL AS21
release→task linkage is unpopulated). No fabricated zero metrics, no early identity-only
completion for analytical intents.

| Form | Runs | Executed | Outcome |
|---|---|---|---|
| progress WMB 24Q1 | 5/5 | `release.progress` | typed SC, no fake 0% |
| health WMB 24Q1 | 3/3 | `release.health` | typed SC |
| readiness OLP 1.6.0 | 3/3 | `release.health` | typed SC |
| blockers WMB 24Q1 | 2/2 | `release.blockers` | typed SC |
| dependencies WMB 24Q1 | 2/2 | `release.dependencies` | typed SC |
| risk_queue WMB 24Q1 | 2/2 | `release.risk_queue` | typed SC |

The A217 original blocker (analytics early-terminating at release.search) stays CLOSED.

## Phase 4 — no-space hardening: PASS

Capability-level (`build_release_search`) — 5/5:
- `query="OLP 1.6.0"` (no explicit space) → normalized to **space=OLP, query="1.6.0"**,
  1 bounded source call, 0 no-space calls.
- `query="релиз 24Q1"` (no approved space token) → typed `V4NeedsClarification`, **0 source calls**.
- `query="WMB OLP 24Q1"` (multiple spaces) → typed clarification with options [OLP, WMB], **0 source calls**.
- `space="wmb"` explicit → unchanged, 1 source call.
- empty args → typed clarification, 0 source calls.

Live NL: "OLP 1.6.0" 3/3 `COMPLETED` via `space.resolve → release.search` with explicit
`space=OLP`. **Zero no-space `/versions` calls** in the A217D window (all 119 space-scoped).

## Phase 5 — sibling Batch 4 + portfolio: PASS (8/8, A217 parity)

- `portfolio.overview` ("обзор портфеля продуктов") 2/2 `COMPLETED`: **144 tasks / 8
  blocked** across 3 confirmed sprints (DMS 73/18/55/31/2, OLP 70/2/68/52/6, WMB 1/1/0/0/0,
  CRPV+STS no current sprint) — exact A217B parity.
- `release.blockers` / `release.dependencies` / `release.risk_queue` 2/2 each → typed SC.

## Phase 6 — Browser C: PASS (5/5)

Real UI (vite 5175 → agent 8212):
1. generic sprint "задачи в текущем спринте DMS" → COMPLETED, DMS-SPRNT-3, 73 visible.
2. standalone identity "релиз 24Q1 в WMB" → COMPLETED, identity only, no analytic pivot.
3. progress "прогресс релиза 24Q1 в WMB" → FAILED, `release.progress` executed, typed source limitation visible.
4. health "здоровье релиза 24Q1 в WMB" → FAILED, `release.health` executed, typed source limitation visible.
5. portfolio "обзор портфеля продуктов" → COMPLETED, `portfolio.overview`, 144/8 visible.

No generic V4 ERROR, no session leak. The initial `100%` flag was a **false positive**: it is
the auto-rendered OverviewDashboard "Daily Brief" portfolio row for WMB-SPRNT-2
(1/1 completed = real 100%), present in every case's background widget — not a fabricated
metric. Clean re-run (with per-case text dumps) shows the only live percentage in each
answer is the legitimate DMS 24,7% (18/73).

## Phase 7 — retained regression: PASS

| Case | Result |
|---|---|
| sprint current "задачи в текущем спринте DMS" | 2/2 COMPLETED, 73 / DMS-SPRNT-3 |
| sprint health "здоровье текущего спринта DMS" | 2/2 COMPLETED, `sprint.health` executed |
| member time "трудозатраты Семавина … сентябрьском спринте DMS" | 2/2 COMPLETED, 64 ч |
| task worklogs "списания по задаче DMS-380" | 2/2 COMPLETED, 48 ч |
| sprint time "фактические трудозатраты спринта DMS-SPRNT-3" | 2/2 COMPLETED, **428,5 ч / 65 списаний** (exact) |
| team.capacity guard "проверь capacity команды DMS с базой 40 часов" | 2/2 FAILED, typed `v4_capability_unavailable` |
| dummy-55 plugin registry (`test_agent_core_v4_plugin_registry.py`) | 13/13 PASS |

Note: plain "утилизация команды DMS" routes to `team.utilization_actual` (actual-time,
COMPLETED, source-backed) — the documented A215F routing behavior, not a defect; the
planned-time `team.capacity` guard is verified with the explicit-baseline phrasing above.

## Audit

- **0 local factual reads** (`GET /api/v1/tasks`): 0 in the A217D window.
- **0 mutations** (POST/PUT/DELETE/PATCH to /api/v1): 0.
- **0 tenant-wide scans**: 0 no-space `/versions` (119 all space-scoped), 0 unscoped
  `task-query` (73 all space-scoped), 0 unscoped `assignee-tasks`.
- 1159 bounded `work-logs` calls (time accounting); **1 transient 502** on
  `tasks/DMS-93/work-logs` (self-healed; re-probe 200 = 40.0h/5, certified sprint total
  428,5ч/65 reproduced exactly in both runs — non-blocking).
- Agent log: **0 TypeError / 0 v4_runtime_failure / 0 traceback**. No LLM 429/ReadTimeout.

## Recommendation (GREEN)

Create an **immutable Batch 4 checkpoint** (release/portfolio skills + robust
signature-parity lock). Before Batch 5, land the queued **self-introspection UX patch**
(per A217C recommendation). The recurring planner signature-drift class (A205-1/A205B/
A217C) is now guarded by `test_agent_core_v4_planner_signature_parity.py`.

## Services left running

- UI 5175 (vite, [::1], proxy → 8212)
- agent 8212 (@ `763ce65`, 127.0.0.1)
- task-api 8241 (system python3, SSE)
- MCP-SWTR 3000
