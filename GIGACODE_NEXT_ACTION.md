# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_215E_CAPACITY_POLICY_GATE

## Role lock
GigaCode is QA/adversarial tester only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT start A216 / Batch 3.
Commit/push only the QA report.

## Baseline
A215D task time-accounting = GREEN.

Owner capacity policy:
- official 2026 Russian production calendar: 247 working days;
- 40h/week => 8h/workday;
- availability factor = 0.87;
- average monthly available days = 247 / 12 * 0.87 = 17.9075;
- default monthly available capacity = 17.9075 * 8 = 143.26h/person.

This is an OWNER_POLICY baseline, not a REAL AS21 fact.

Owner commits:
- b2435d411954fdd709a4cb9054f03bd889da0454
- db12bde68aa6b4e271fa559b5ee795c24250acd9
- 1e1ccf6ae8a04a95eee71ddbfc62d05c0852e3b6

## Goal
Certify that team.capacity uses the owner policy only as a denominator baseline and never hides missing source estimates.

## Phase 0 — architecture invariant
1. Pull branch and record START_HEAD.
2. Diff only the three owner commits.
3. Prove:
   - no Agent Core/planner/runtime business routing changes;
   - policy lives outside Agent Core;
   - Batch 2 remains plugin-owned;
   - dummy-55 remains GREEN.

## Phase 1 — formula verification
Independently verify:
- 247 working days / 12 = 20.583333...
- × 0.87 = 17.9075 available workdays/month
- × 8h = 143.26h/person/month after rounding to 2 decimals

Require policy metadata to expose:
- 247
- 0.87
- 40h/week
- 8h/day
- 143.26h/month
- source=OWNER_POLICY

## Phase 2 — source-estimate guard
On current REAL AS21 DMS, where active assigned task estimates are not source-backed:
- `утилизация команды DMS`
- `утилизация команды DMS с capacity 40 часов`

Both must remain terminal SOURCE_CONDITIONAL / capability unavailable on missing estimates.
The 143.26h default must NOT make the metric appear calculable when the numerator is missing.

## Phase 3 — controlled positive fixture
Using a QA fixture with complete source-backed estimates:
A) no explicit capacity -> use 143.26h default;
B) explicit capacity 40h -> use 40h and mark explicit_user_baseline.

Require exact utilization math and capacity_source metadata.

## Phase 4 — time-accounting separation
Prove:
- `task.time_spent` / `task.worklogs` remain actual-time metrics;
- `team.capacity` remains planned utilization from estimates;
- worklogs are NOT silently substituted for estimates in team.capacity;
- actual utilization will be a separate skill.

## Phase 5 — retained smoke
Re-run:
- DMS-380 time_spent = 48h;
- team.workload DMS;
- release.search;
- dummy-55;
- local factual reads = 0;
- tenant-wide scans = 0.

## Verdict
Use exactly one:
- `TEAM_CAPACITY_POLICY_GREEN_A215E`
- `TEAM_CAPACITY_POLICY_RED_A215E`

If GREEN:
- recommend capacity policy checkpoint;
- recommend implementing actual-time aggregation (sprint/team time_spent) next or resuming A216 per owner priority.

STOP after report. No code changes.
