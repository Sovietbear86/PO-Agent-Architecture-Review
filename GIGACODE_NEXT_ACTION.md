# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_215G_MEMBER_TIME_ACCOUNTING_GATE

## Role
QA/adversarial tester only. Do not modify production code. Do not start A216.

## Baseline
A215F2 = GREEN.
Checkpoint: checkpoint/v4-actual-time-green-a215f2

## Owner implementation
Commits:
- b5fa16f2ad2c493d832210b6f70569acc5ed6047
- fad2580b58228a819470523d9116e2636a41df9e

New plugin-only skills:
- member.time_spent
- member.worklogs
- member.utilization_actual

No Agent Core/planner/runtime/session-context changes were made.

## Intent
Fix the manual-test gap:
"трудозатраты Семавина по задачам в сентябрьском спринте DMS"
must complete end-to-end in one trajectory rather than stop after listing Semavin's assigned tasks and ask the user to continue.

Attribution MUST use worklog author externalId, never current task assignee.

Rolling-period requests such as "за 2 недели" without a bounded sprint/task scope must clarify product/sprint context; do not tenant-scan or infer assignment as worklog ownership.

## Phase 0 — architecture invariant
1. Pull branch; record START_HEAD and clean worktree.
2. Prove only plugin + tests + docs changed.
3. No Agent Core/planner/runtime/session-context modifications.
4. Registry discovers all three skills.
5. dummy-55 GREEN.

## Phase 1 — tests
Run:
- tests/test_agent_core_v4_time_accounting_member.py
- tests/test_agent_core_v4_time_accounting_aggregate.py
- relevant V4/plugin suites

Require zero unexplained failures and zero-worklog completion safety.

## Phase 2 — DMS Semavin oracle
Use REAL DMS-SPRNT-3 / current source equivalent.

Resolve Semavin through member.resolve.
Independent oracle:
- complete authoritative sprint membership;
- complete bounded worklogs for every sprint task;
- filter by sprint dates;
- filter by worklog user.externalId == resolved Semavin login.

Capture exact:
- total hours;
- worklog count;
- task breakdown;
- work type breakdown;
- dates.

## Phase 3 — member.time_spent NL gate
Run at least:
- "трудозатраты Семавина по задачам в сентябрьском спринте DMS"
- "сколько Семавин списал в DMS-SPRNT-3"
- "фактические трудозатраты Семавина в текущем спринте DMS"

Require:
- space/sprint/member resolution;
- direct member.time_spent execution;
- exact oracle parity;
- NO intermediate task-list final answer;
- NO "готов продолжить";
- NO confirmation before bounded worklog fan-out.

## Phase 4 — member.worklogs
Run:
- "покажи списания Семавина в сентябрьском спринте DMS"
- "кто/когда: списания Семавина в DMS-SPRNT-3"

Require exact member-only entries with task/date/type/hours.
Prove entries on tasks currently assigned to other people are still attributed to Semavin if the worklog author is Semavin.

## Phase 5 — member.utilization_actual
Require formula:
Semavin actual worklog hours / period-normalized OWNER_POLICY capacity.
Exact numerator, denominator, percentage, provenance.

## Phase 6 — insufficient-scope behavior
Run:
- "трудозатраты Семавина за 2 недели"

Expected:
- typed clarification for bounded product/sprint/task scope;
- no claim that capability is missing;
- no tenant-wide scan;
- no inference from current task assignments.

## Phase 7 — continuation safety
Re-test the original manual pattern:
1. member/sprint time-spent request
2. "Продолжи"

Expected:
- first request already completes the requested aggregation;
- no artificial continuation is needed;
- second turn must not resurrect stale intermediate observations or cross-session state.
Do NOT require any new session-memory mechanism.

## Phase 8 — Browser C
Real UI for member.time_spent and member.worklogs.
Readable totals/breakdowns; no generic ERROR; no fake continuation prompt.

## Phase 9 — retained regression
- A215F2 sprint/team actual-time parity
- DMS-380 = 48h / 6 entries
- team.capacity guard
- release.search / release.health source-conditional
- dummy-55

## Audit
0 local factual reads, 0 tenant-wide scans, bounded worklog fan-out <=8, 0 mutations.

## Verdict
Use exactly one:
- MEMBER_TIME_ACCOUNTING_GREEN_A215G
- MEMBER_TIME_ACCOUNTING_RED_A215G

If GREEN: recommend checkpoint and resume A216.
If RED: identify first failing boundary and STOP.
