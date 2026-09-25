# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_215F_ACTUAL_TIME_AGGREGATION_GATE

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT start A216 / Batch 3.
Commit/push only the QA report.

## Baseline
A215D task-level time accounting = GREEN.
A215E owner capacity policy = GREEN.

A215E non-blocking F1 identified a semantic granularity issue:
143.26h is a monthly average capacity, while team.capacity is scoped to a sprint.
Owner has now normalized the same policy to the authoritative sprint calendar length.

## Owner implementation

Commits:
- `9e1782b864db85edd1be611863209015d2781873` — period-normalized owner capacity helper;
- `114b6d0e63d6480dacaef2095c739da37b3b88e3` — plugin skills:
  - sprint.time_spent
  - team.time_spent
  - team.utilization_actual
  - release.time_spent
- `b133e3cd5627c9d24d56bb5aca3146c6163dfa6a` — focused aggregation tests;
- `1337b204217ae1f229c3b57160f4a3ffa526ce20` — normalize team.capacity default denominator to sprint period;
- `a98b6d2c3026917f1849d56d9c96c4416824c4ab` — capacity regression tests.

Architecture remains plugin/source-layer only. No skill-specific Agent Core/planner/runtime routing.

## Capacity policy semantics

Owner policy remains:
- 247 working days in RU 2026
- 40h/week => 8h/workday
- availability factor 0.87

Annual available hours:
`247 * 8 * 0.87 = 1719.12h`

For a sprint/period of N calendar days:
`capacity = N * (1719.12 / 365)`

This deliberately uses annual-average 2026 workday density, not a date-specific holiday calendar.
The policy must remain tagged OWNER_POLICY.

Example 14-day sprint:
`14 * 1719.12 / 365 = 65.94h/person` after 2dp rounding.

## Phase 0 — architecture invariant
1. Pull branch, record START_HEAD, clean worktree.
2. Diff owner commits.
3. Prove:
   - new skills are plugin-registry discovered;
   - no Agent Core/planner/runtime business-routing changes;
   - CompletionContract/UIContract exist;
   - dummy-55 invariant GREEN.

## Phase 1 — focused tests
Run:
- tests/test_agent_core_v4_time_accounting_aggregate.py
- tests/test_agent_core_v4_time_accounting.py
- tests/test_agent_core_v4_batch2.py
- relevant V4/plugin suites

Require zero unexplained failures.

## Phase 2 — capacity period normalization
Independently verify the policy math.

For a source-backed 14-calendar-day sprint:
- capacity/person = 65.94h
- metadata includes OWNER_POLICY, 247, 0.87, 40h/week, period calendar days, normalization id.

Verify team.capacity:
- missing source estimates still fails closed BEFORE denominator use;
- explicit user capacity still overrides owner policy exactly;
- complete-estimate QA fixture with no explicit baseline uses period-normalized capacity, not 143.26 monthly.

## Phase 3 — sprint.time_spent REAL AS21
Use DMS-SPRNT-3 and at least one other source-backed sprint if bounded budget allows.

Oracle:
1. authoritative complete sprint task membership;
2. authoritative sprint start/finish dates;
3. bounded per-task worklogs;
4. include only entries whose worklog date is within sprint period inclusive.

Require exact:
- total hours;
- worklog count;
- by_member;
- by_task;
- by_type;
- by_date;
- no worklogs outside sprint date range.

No tenant-wide scans.

## Phase 4 — team.time_spent
Current DMS sprint.

Require:
- resolves authoritative current sprint;
- exact parity with sprint.time_spent for that sprint;
- member attribution by worklog user.externalId, NOT current task assignee;
- unknown-user hours reported separately if present.

## Phase 5 — team.utilization_actual
Current DMS sprint.

Formula per member:
`actual worklog hours within sprint / period-normalized owner-policy capacity * 100`

Require:
- numerator source = REAL_AS21_WORKLOGS
- denominator source = OWNER_POLICY
- denominator scaled to actual sprint calendar length
- exact per-member math
- can exceed 100%; no clipping
- worklog author is the member identity
- no estimate/task-count substitution

Explicitly prove this is ACTUAL utilization, distinct from team.capacity planned utilization.

## Phase 6 — release.time_spent
Use real WMB/OLP release catalog candidates.

Expected under current A214 source state:
- release.search resolves real release id;
- release.time_spent attempts bounded release membership;
- missing release-to-task linkage => terminal SOURCE_CONDITIONAL;
- no 0h fabricated result;
- no tenant-wide scan.

## Phase 7 — Browser C
Real UI:
- sprint time spent
- team time spent
- actual utilization
- release time spent source limitation

Require readable breakdowns and clear provenance; no generic ERROR where typed source-conditional applies.

## Phase 8 — retained regression
At minimum:
- DMS-380 task.time_spent = 48h
- task.worklogs = 6 entries
- team.workload
- team.capacity source-estimate guard
- release.search
- release.health SOURCE_CONDITIONAL
- dummy-55

## Phase 9 — source/performance audit
Require:
- local factual /api/v1/tasks reads = 0
- unscoped tenant-wide scans = 0
- bounded per-task worklog fan-out with concurrency <= 8
- no mutation calls
- source outage/incomplete page => fail closed, no partial aggregate

## Verdict
Use exactly one:
- `ACTUAL_TIME_AGGREGATION_GREEN_A215F`
- `ACTUAL_TIME_AGGREGATION_RED_A215F`

If GREEN:
- recommend immutable time-aggregation checkpoint;
- recommend resume A216 / Batch 3 QA.

If RED:
- identify first failing boundary and STOP.

Do not modify production code.
