# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_216_BATCH3_FIVE_SKILL_GATE

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT add skills.
Do NOT start Batch 4.
Commit/push only the QA report.

## Frozen baseline
A215D/E/F2/G = GREEN.
Member-time checkpoint:
`checkpoint/v4-member-time-green-a215g`

Harness/Core/planner/runtime remain frozen as a platform.

## Owner Batch 3
Five registry-discovered skills:
1. team.competency_match
2. team.assignee_recommendation
3. team.bottlenecks
4. team.distribution
5. release.scope

Implementation already present from owner:
- `po-agent-platform-v2/src/po_agent/harness/v4_plugins/wave_batch3.py`
- `po-agent-platform-v2/tests/test_agent_core_v4_batch3.py`

## Contracts

### team.competency_match
Expected SOURCE_CONDITIONAL unless an authoritative competency/skill source exists.
Never infer competence from current task ownership, titles, historical assignment, worklogs or local roster metadata.

### team.assignee_recommendation
Expected SOURCE_CONDITIONAL unless both competencies and availability/capacity are authoritative.
No employee scoring or "best assignee" from workload, utilization, worklogs or task counts alone.

### team.bottlenecks
Descriptive current-sprint operational concentration only.
Exact current-sprint membership, active-task concentration, WIP and blocked hotspots.
Not an employee performance score.

### team.distribution
Exact current-sprint task/status distribution by canonical assignee.
Preserve source status labels and exact member/task counts.

### release.scope
Resolve a real release via release.search, then use bounded space-scoped release membership.
Under the current A214 source state this is expected to terminate SOURCE_CONDITIONAL because release-to-task linkage is unpopulated.
Never return count=0 as proof that a real release has no tasks.

## Phase 0 — architecture invariant
1. Pull branch, record START_HEAD and clean worktree.
2. Diff from checkpoint/v4-member-time-green-a215g.
3. Prove Batch 3 is plugin-registry only.
4. No Agent Core/planner/runtime/session-context routing edits for Batch 3.
5. CompletionContract + UIContract exist for all five skills.
6. dummy-55/plugin invariant GREEN.

Architecture drift => RED.

## Phase 1 — tests
Run:
- tests/test_agent_core_v4_batch3.py
- member/time-accounting retained suites
- Batch 2 / Wave S2 retained suites
- tests/test_agent_core_v4*.py
- tests/test_v4*.py

Zero unexplained failures.

## Phase 2 — fresh REAL AS21 oracle
Use DMS plus at least one other source-backed current sprint.

Capture exact:
- current sprint id;
- complete task membership;
- canonical assignee;
- raw/source status;
- completed/open/WIP/blocked classification.

For release.scope use real WMB/OLP release catalog entries and the bounded release task-query path.

## Phase 3 — team.bottlenecks
At least 5 NL forms across >=2 spaces.

Require exact parity for:
- current sprint;
- active-task counts by member;
- blocked counts;
- WIP counts;
- rows selected by the deterministic declared thresholds.

No employee scoring/ranking language.
No use of worklog hours or utilization as a hidden performance score.

## Phase 4 — team.distribution
At least 5 NL forms across >=2 spaces.

Require exact:
- total task set;
- per-member task counts;
- WIP;
- blocked;
- raw/source status distribution.

## Phase 5 — team.competency_match
Representative natural-language requests.

Expected unless a real competency source is discovered:
- typed SOURCE_CONDITIONAL/capability unavailable;
- zero inferred competency from tasks, worklogs, utilization or assignment history;
- zero local-roster-as-truth.

If a live competency source exists, document it and compare exact source facts.

## Phase 6 — team.assignee_recommendation
Representative recommendation requests.

Expected under current source state:
- typed SOURCE_CONDITIONAL;
- no ranking/recommendation of people;
- no conversion of workload/time-spent/utilization into competence;
- no default-capacity inference.

Any fabricated "best assignee" => RED.

## Phase 7 — release.scope
Use at least:
- WMB 24Q1;
- OLP 1.6.0;
- one product-only/single-release form if supported.

Expected:
- space.resolve -> release.search -> release.scope;
- canonical release UUID from validated release.search;
- bounded space-scoped task-query;
- current missing linkage => typed SOURCE_CONDITIONAL, not count=0;
- no tenant-wide scan.

## Phase 8 — Browser C
Representative UI for all five skills.
Source limitations explicit; no fake metrics/recommendations; no generic error where typed source-conditional applies.

## Phase 9 — retained regression
At minimum:
- member.time_spent Semavin DMS-SPRNT-3 = fresh oracle parity;
- member.utilization_actual provenance;
- sprint/team actual time;
- DMS-380 48h / 6 worklogs;
- team.capacity source-estimate guard;
- release.search;
- release.health SOURCE_CONDITIONAL;
- dummy-55.

## Phase 10 — audit
Require:
- local factual /api/v1/tasks reads = 0;
- unscoped tenant-wide scans = 0;
- bounded current-sprint source for team analytics;
- bounded release membership path only;
- no mutation calls.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_BATCH3_FIVE_SKILL_GREEN`
- `AGENT_CORE_V4_BATCH3_FIVE_SKILL_RED`

If GREEN:
recommend immutable Batch 3 checkpoint and owner implementation of Batch 4.

If RED:
identify first failing boundary and STOP.

Do not modify code.
