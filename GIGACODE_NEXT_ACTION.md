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

## Baseline
A215 Batch 2 = GREEN.
Rollback checkpoint:
`checkpoint/v4-batch2-green-a215`

Harness/Core/planner/runtime remain frozen as a platform.

## Owner Batch 3
Five registry-discovered skills:
1. team.competency_match
2. team.assignee_recommendation
3. team.bottlenecks
4. team.distribution
5. release.scope

Owner commits:
- `44cf860cb64388f9d9a3d1e5c7a7f5cfbad0a41f`
- `3c00457751d465e9a4034716cdf72f0626302228`

Implementation:
`po-agent-platform-v2/src/po_agent/harness/v4_plugins/wave_batch3.py`

Focused tests:
`po-agent-platform-v2/tests/test_agent_core_v4_batch3.py`

## Contracts

### team.competency_match
Expected SOURCE_CONDITIONAL unless an authoritative competency/skill source exists.
It must not infer competence from current task ownership, task titles, historical assignment, or local roster metadata.

### team.assignee_recommendation
Expected SOURCE_CONDITIONAL under the current source contract unless both competency and availability/capacity are authoritative.
No employee scoring or recommendation from workload counts alone.

### team.bottlenecks
Descriptive current-sprint operational concentration only.
Exact current-sprint membership; count active work by canonical assignee and blocked hotspots.
This is not an employee performance score.

### team.distribution
Exact current-sprint task/status distribution by canonical assignee.
Must preserve authoritative status labels and exact member/task counts.

### release.scope
Use release.search to resolve a real release id, then bounded space-scoped release membership.
Current A214 source state is expected to make this terminal SOURCE_CONDITIONAL because release-to-task linkage is unpopulated.
Never interpret an empty membership query as proof that a real release has zero tasks.

## Phase 0 — architecture invariant
1. Pull branch, record START_HEAD, clean worktree.
2. Diff from A215 checkpoint.
3. Prove all five are plugin-registry additions only.
4. No Agent Core/planner/runtime routing edits.
5. CompletionContract + UIContract present for all five.
6. dummy-55/plugin invariant GREEN.

Any architecture drift => RED.

## Phase 1 — tests
Run:
- tests/test_agent_core_v4_batch3.py
- tests/test_agent_core_v4_batch2.py
- tests/test_agent_core_v4_wave_s2.py
- tests/test_agent_core_v4_wave_s1.py
- tests/test_agent_core_v4*.py
- tests/test_v4*.py

Classify only proven stale/test-logic artifacts as non-production; report them explicitly.

## Phase 2 — fresh REAL AS21 oracle
Use DMS plus at least one other space with an authoritative current sprint.

Capture exact:
- current sprint id;
- complete task-key membership;
- canonical assignee;
- raw/source status;
- completed/open/WIP/blocked classification.

For release.scope use WMB/OLP real release catalog entries from release.search and the bounded release task-query path.

## Phase 3 — team.bottlenecks
At least 5 NL forms across >=2 spaces.

Require exact parity for:
- current sprint;
- active task counts by member;
- blocked counts;
- WIP counts;
- rows selected by the declared deterministic threshold.

No employee score/ranking language in factual output.
Thresholds must be visible in data/contract and not model-invented.

## Phase 4 — team.distribution
At least 5 NL forms across >=2 spaces.

Require exact:
- total task set;
- per-member task counts;
- per-member WIP;
- per-member blocked;
- raw/source status distribution.

## Phase 5 — team.competency_match
Run representative natural-language requests.

Expected unless a real competency source is discovered:
- current-sprint/source context may be validated;
- then typed SOURCE_CONDITIONAL/capability-unavailable;
- zero inferred competency from task history/current ownership;
- zero local-roster-as-truth.

If a live competency source unexpectedly exists, document it and compare exact source facts.

## Phase 6 — team.assignee_recommendation
Run representative assignment/recommendation requests.

Expected under current source state:
- typed SOURCE_CONDITIONAL;
- no ranking/recommendation of people;
- no task-count-to-competence inference;
- no default capacity assumptions.

Any fabricated "best assignee" => RED.

## Phase 7 — release.scope
Use at least:
- WMB 24Q1;
- OLP 1.6.0;
- one product-only/single-release form if supported.

Expected:
- space.resolve -> release.search -> release.scope;
- canonical release UUID from validated release.search observation;
- bounded space-scoped task-query;
- under current source linkage: typed SOURCE_CONDITIONAL, not count=0;
- no tenant-wide scan.

## Phase 8 — Browser C
Representative UI for all five skills.
Source limitations must be explicit and no fake metrics/recommendations may render.

## Phase 9 — retained regression
At minimum:
- Batch 2 workload/wip/blocked;
- release.search;
- release.health SOURCE_CONDITIONAL;
- Wave S2 metric;
- sprint.health;
- DMS-380;
- person+status;
- dummy-55.

## Phase 10 — source audit
Require:
- local factual /api/v1/tasks reads = 0;
- unscoped tenant-wide task-query scans = 0;
- current-sprint team analytics use bounded sprint source;
- release.scope uses bounded release membership path only.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_BATCH3_FIVE_SKILL_GREEN`
- `AGENT_CORE_V4_BATCH3_FIVE_SKILL_RED`

If GREEN:
recommend immutable Batch 3 checkpoint and owner implementation of Batch 4.

If RED:
identify first failing boundary and STOP.
Do not modify code.
