# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_217_BATCH4_FIVE_SKILL_GATE

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT add skills.
Do NOT start Batch 5.
Commit/push only the QA report.

## Frozen baseline
A216 Batch 3 = GREEN.
Rollback checkpoint:
`checkpoint/v4-batch3-green-a216`

Harness/Core/planner/runtime/session-context remain frozen as a platform.

## Owner Batch 4
Five registry-discovered skills:
1. release.progress
2. release.blockers
3. release.dependencies
4. release.risk_queue
5. portfolio.overview

Owner commits:
- `828a005ea0e35a1b026468a8e9a5198313459fa7`
- `3d29ec6eac5e60002513dfd4246093fe30928681`

Implementation:
`po-agent-platform-v2/src/po_agent/harness/v4_plugins/wave_batch4.py`

Focused tests:
`po-agent-platform-v2/tests/test_agent_core_v4_batch4.py`

## Contracts

### release.progress
Resolve canonical release via release.search, then bounded release membership.
Task-count completion may be computed only from authoritative membership.
Effort progress may be computed only when every release task has source-backed estimate_hours.
Missing estimates must not be treated as zero.

Under the current A214 source state, expected live behavior is SOURCE_CONDITIONAL before any metric because release membership is unpopulated.

### release.blockers
Blocked release task set only from authoritative release membership.
Current expected live state: SOURCE_CONDITIONAL.

### release.dependencies
Dependency edges only from authoritative release membership and task depends_on fields.
Internal = dependency target inside release membership.
External = dependency target outside release membership.
Current expected live state: SOURCE_CONDITIONAL.

### release.risk_queue
Deterministic operational task-risk queue:
- blocked +50
- critical/urgent +30
- high +15
- unassigned active +15
- age >=14d active +10
cap 100.
This is task operational priority, NOT employee scoring.
Current expected live state: SOURCE_CONDITIONAL because membership is missing.

### portfolio.overview
Bounded cross-space current-sprint snapshot over the configured allow-list:
CRPV, DMS, OLP, STS, WMB.

For each space:
- current sprint via bounded source route;
- sprint membership via bounded sprint route;
- exact total/completed/open/blocked/WIP;
- if no current sprint, report explicit NO_CURRENT_SPRINT state;
- never tenant-scan to fabricate an overview.

## Phase 0 — architecture invariant
1. Pull branch; record START_HEAD and clean worktree.
2. Diff from checkpoint/v4-batch3-green-a216.
3. Prove Batch 4 is plugin-registry only.
4. No Agent Core/planner/runtime/session-context routing edits.
5. CompletionContract + UIContract for all five.
6. dummy-55/plugin invariant GREEN.

Any architecture drift => RED.

## Phase 1 — tests
Run:
- tests/test_agent_core_v4_batch4.py
- Batch 3 retained suite
- member/time-accounting retained suites
- tests/test_agent_core_v4*.py
- tests/test_v4*.py

Zero unexplained failures.

## Phase 2 — fresh release source oracle
Use WMB 24Q1 and OLP 1.6.0.

Require:
- release.search exact catalog parity;
- canonical UUID from release.search;
- bounded `task-query?space=<space>&release=<uuid>`;
- confirm current membership result.

If current source still returns zero rows:
all four release analytics must terminate typed SOURCE_CONDITIONAL.
No 0%, no 0 blockers, no empty dependency graph, no empty risk queue rendered as source facts.

## Phase 3 — release.progress
Use at least:
- `прогресс релиза 24Q1 в WMB`
- `готовность релиза OLP 1.6.0`
- one concise English form.

Expected current state:
space.resolve -> release.search -> release.progress -> typed source conditional.

Controlled QA fixture with source-backed release membership:
- exact total/completed/blocked/active;
- task completion exact;
- incomplete estimate coverage => effort_progress=null + warning;
- complete estimates => exact effort progress;
- never missing estimate = 0.

## Phase 4 — release.blockers
Representative forms for WMB/OLP.
Current live expected SOURCE_CONDITIONAL.

Controlled membership fixture:
exact blocked task-key set using canonical blocked predicate.

## Phase 5 — release.dependencies
Representative forms.
Current live expected SOURCE_CONDITIONAL.

Controlled fixture:
exact internal/external edge partition.
No inferred dependency from prose.

## Phase 6 — release.risk_queue
Representative forms.
Current live expected SOURCE_CONDITIONAL.

Controlled fixture:
exact deterministic score/reasons/order.
No person ranking/performance language.

## Phase 7 — portfolio.overview REAL AS21
Run at least 3 natural-language forms:
- `обзор портфеля продуктов`
- `состояние продуктов DMS OLP WMB STS CRPV`
- `portfolio overview`

Independent oracle per approved space:
1. current-sprint source route;
2. complete sprint membership if current sprint exists;
3. compute total/completed/open/blocked/WIP with certified predicates.

Require exact row parity for every space.

If a space has no current sprint:
- state=NO_CURRENT_SPRINT;
- metrics null;
- do NOT infer from arbitrary tasks.

No tenant-wide scan.

## Phase 8 — Browser C
Real UI for:
- portfolio overview;
- release.progress source limitation;
- release.risk_queue source limitation.

Typed source limitations must be clear; no fake zero metrics.

## Phase 9 — retained regression
At minimum:
- Batch 3 bottlenecks/distribution
- member.time_spent Semavin
- sprint/team time spent
- DMS-380 48h/6 worklogs
- team.capacity guard
- release.search/release.health SOURCE_CONDITIONAL
- dummy-55

## Phase 10 — audit
Require:
- local factual /api/v1/tasks reads = 0;
- unscoped tenant-wide scans = 0;
- portfolio uses only bounded current-sprint + sprint-membership reads per approved space;
- release uses only bounded release membership path;
- mutations = 0.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_BATCH4_FIVE_SKILL_GREEN`
- `AGENT_CORE_V4_BATCH4_FIVE_SKILL_RED`

If GREEN:
recommend immutable Batch 4 checkpoint and owner implementation of Batch 5.

If RED:
identify first failing boundary and STOP.

Do not modify code.
