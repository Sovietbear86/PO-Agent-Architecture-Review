# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_215_BATCH2_FIVE_SKILL_GATE

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT add skills.
Do NOT start Batch 3.
Commit/push only the QA report.

## Baseline
A214 release remediation is closed:
- release.search = GREEN
- release.health = terminal SOURCE_CONDITIONAL
- Harness/Core platform invariant remains frozen.

## Owner Batch 2
Five registry-discovered skills:
1. sprint.scope_change
2. team.workload
3. team.wip
4. team.blocked
5. team.capacity

Owner commits:
- e0290faa653c717ec6e0c5d8222d6e88f00eb2dc
- a73e043a6eb32fd65dffa368f71d9d5553f7ea1a

Implementation file:
po-agent-platform-v2/src/po_agent/harness/v4_plugins/wave_batch2.py

Focused tests:
po-agent-platform-v2/tests/test_agent_core_v4_batch2.py

## Semantic contracts

### sprint.scope_change
Must validate a real sprint and then fail closed unless REAL AS21 exposes an authoritative sprint-start commitment baseline.
Do not substitute previous-sprint membership for a start-of-sprint baseline.

### team.workload
Current-sprint task-count workload only.
Resolve a product space, use its authoritative current sprint, retrieve the complete sprint set, and group by canonical assignee.
Do not present task count as capacity or employee performance.

### team.wip
Current-sprint WIP only.
Use the same non-terminal/backlog exclusion semantics as certified sprint WIP.
Exact task-key parity required.

### team.blocked
Current-sprint blocked tasks only.
Must use the canonical blocked predicate and exact task-key parity.

### team.capacity
Capacity may only be calculated when an explicit capacity_hours baseline is supplied and active assigned tasks have source-backed estimates.
No implicit/default 40 hours is acceptable.
Missing baseline or incomplete estimates must fail closed.
Flag any case where the planner invents a capacity baseline not present in the user request as RED.

## Phase 0 — architecture invariant
1. Pull branch, record START_HEAD, clean worktree.
2. Diff from A214.
3. Prove all five skills are added through plugin registry only.
4. Prove no Agent Core/planner/runtime routing changes for these skills.
5. Prove CompletionContract and UIContract exist.
6. dummy-55/plugin invariant GREEN.

Architecture drift => RED.

## Phase 1 — focused and retained tests
Run:
- tests/test_agent_core_v4_batch2.py
- tests/test_agent_core_v4_wave_s2.py
- tests/test_agent_core_v4_wave_s1.py
- tests/test_agent_core_v4*.py
- tests/test_v4*.py

Zero unexplained failures.

## Phase 2 — fresh REAL AS21 Oracle
Use DMS plus at least one other applicable space where current sprint exists.

For each tested space:
- resolve authoritative current sprint;
- retrieve complete sprint membership;
- independently classify completed/open/WIP/blocked;
- canonical assignee identity;
- source estimate coverage;
- prove no tenant-wide scan and no local factual reads.

## Phase 3 — team.workload
At least 5 natural-language forms across >=2 spaces.

Require exact:
- sprint id;
- active/completed totals;
- per-member task counts;
- WIP counts;
- blocked counts;
- unassigned active count.

No person scoring, no capacity inference.

## Phase 4 — team.wip
At least 5 forms.
Require exact task-key set parity and per-member counts.

## Phase 5 — team.blocked
At least 5 forms.
Require exact task-key set parity and same blocked predicate as sprint.health/risk logic.

## Phase 6 — team.capacity
Test both:
A) query without explicit capacity baseline;
B) query with an explicit numeric baseline in the user text.

Requirements:
- A must NOT invent 40 or any other baseline; expected typed clarification/source-conditional/fail-closed.
- B may calculate only if the numeric baseline is preserved from the user query AND every active assigned task has source-backed estimate_hours.
- if estimates are incomplete, fail closed and do not treat missing estimate as zero.
- no employee scoring.

Any planner-invented baseline => RED.

## Phase 7 — sprint.scope_change
Test explicit id, period/current forms.

Require:
- real sprint resolution;
- then terminal SOURCE_CONDITIONAL / capability-unavailable if sprint-start commitment baseline is not source-backed;
- no previous-sprint proxy;
- no fabricated percentage/count.

## Phase 8 — Browser C
Representative UI for all five skills.
SOURCE_CONDITIONAL states must be explicit and must not render fake metrics.

## Phase 9 — retained regression
At minimum:
- release.search WMB/OLP;
- release.health source-conditional;
- one Wave S2 metric;
- sprint.health;
- DMS-380 lookup;
- person+status;
- dummy-55.

## Phase 10 — source audit
Require:
- local factual /api/v1/tasks reads = 0;
- unscoped tenant-wide scans = 0;
- current-sprint team metrics use bounded current-sprint source path;
- exact task sets where applicable.

## Verdict
Use exactly one:
- AGENT_CORE_V4_BATCH2_FIVE_SKILL_GREEN
- AGENT_CORE_V4_BATCH2_FIVE_SKILL_RED

If GREEN:
recommend immutable Batch 2 checkpoint and owner implementation of Batch 3.

If RED:
identify first failing boundary and STOP.
Do not fix code.
