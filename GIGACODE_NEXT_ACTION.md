# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_210_WAVE_S2_REGATE`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT add skills.
Do NOT start release recovery or the next five-skill batch.
Commit/push **only the QA report and QA-only artifacts explicitly allowed by project rules**.

## Stable rollback
A208B is GREEN and frozen at:
`checkpoint/v4-a208b-green@2e284fdab79072d95ba0bf86058b4648f4bb9d6c`

## Context
Assignment 209 ended RED:
`AGENT_CORE_V4_WAVE_S2_FIVE_SKILL_RED`
classification:
`RED_SOURCE_TIMESTAMP_PLUMBING`

A209 proved:
- Harness/Core/planner/plugin architecture itself did not regress;
- `sprint.carryover` GREEN;
- `sprint.predictability` correctly SOURCE_CONDITIONAL because REAL AS21 exposes no committed baseline;
- `sprint.cycle_time`, `sprint.lead_time`, and `sprint.risk_queue` were blocked by missing source timestamps in sprint-task rows;
- retained regression remained GREEN;
- local factual `/api/v1/tasks` reads = 0.

## Owner remediation
Owner fixed the bounded source/capability path only. Agent Core/planner/runtime routing was not changed.

Relevant remediation includes:
- sprint-task live route preserves/enriches source-backed `created_at` / `updated_at` / `deadline`;
- provenance flags remain authoritative and source-missing timestamps fail closed;
- risk queue never interprets adapter fallback timestamps as source facts;
- lead/cycle timestamp arithmetic is timezone-normalized;
- adapter fallback timestamps are timezone-aware but remain marked non-source;
- focused regression coverage added.

Latest owner hardening commits:
- `00bc9b8ab5ea318abab6198b47dc55b4e9a23d50`
- `0f5ca3cde7d65f0203d6d6666a17849adae60055`
- `5d7980f69e6fbb82871c3e54a72da7cc367033a9`

## Goal
Re-gate the **same five Wave S2 skills**. This is not a new wave.

1. `sprint.cycle_time`
2. `sprint.lead_time`
3. `sprint.carryover`
4. `sprint.predictability`
5. `sprint.risk_queue`

## Phase 0 — pull / diff / architecture invariant
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record START_HEAD and verify tracked worktree clean.
3. Diff against A208B checkpoint and against A209 report head.
4. Prove:
   - no skill-specific branch was added to Agent Core/planner/runtime orchestration;
   - all five skills remain registry/plugin-discovered;
   - CompletionContract/UIContract still come from plugin contracts;
   - no hardcoded DMS/person/task/sprint facts;
   - no local/fake/cache fallback;
   - dummy-55/plugin invariant still passes.

Any architecture drift => RED.

## Phase 1 — automated suites
Run:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4_wave_s2.py -v
python -m pytest tests/test_agent_core_v4_wave_s1.py -v
python -m pytest tests/test_agent_core_v4*.py -v
python -m pytest tests/test_v4*.py -v
```

Zero unexplained failures.

## Phase 2 — fresh REAL AS21 oracle
Build a **fresh** Oracle for current DMS sprint. Do not reuse A209 counts as truth.

Capture:
- complete current sprint membership;
- complete previous sprint membership;
- source-backed `created_at`, `updated_at`, `deadline` coverage for sprint-task rows;
- completed-task histories;
- blocked/open state;
- authoritative due dates;
- sprint metadata relevant to committed baseline.

Explicitly prove timestamp provenance:
- count of sprint rows with source `created_at`;
- count with source `deadline`;
- no adapter fallback timestamp may be treated as source truth.

## Phase 3 — sprint.cycle_time re-gate
Run explicit-id, period, and current/product forms, **minimum 10 total runs**.

Independent Oracle B:
- completed tasks only;
- first workflow-status transition;
- terminal workflow transition;
- exact per-task cycle hours;
- avg/median/min/max.

Require:
- exact completed population;
- exact per-task timestamps;
- aggregate parity within rounding tolerance;
- no current-time substitution;
- source-missing history/timestamp => fail closed, never partial aggregate.

## Phase 4 — sprint.lead_time re-gate
Same form matrix, **minimum 10 total runs**.

Oracle:
`terminal workflow transition - authoritative task.created_at`

Require exact population, exact timestamps, exact aggregates.
Explicitly verify tz-aware and source-backed arithmetic.
No `updated_at` or current time substitute.

## Phase 5 — sprint.carryover retained
At least 3 representative runs.

Require exact set intersection:
`previous complete sprint membership ∩ current complete sprint membership`

Auto-previous resolution must remain source-backed.
No fuzzy/title matching.

## Phase 6 — sprint.predictability retained
Inspect live sprint metadata.

If committed/baseline exists:
- calculate independently and require exact parity.

If it does not exist:
- expected typed SOURCE_CONDITIONAL/SOURCE_UNAVAILABLE;
- prove no current-scope substitution;
- zero fabricated percentage.

This is not overall RED when source absence is independently proven.

## Phase 7 — sprint.risk_queue re-gate
Fresh Oracle on current DMS sprint.

Require exact source-backed queue:
- blocked tasks;
- overdue tasks from authoritative deadline;
- aging >=14d from authoritative created_at.

Ordering:
1. blocked first;
2. overdue_days desc;
3. age_days desc;
4. stable task-key tie-break.

Require:
- exact queue membership vs Oracle B;
- exact reasons/evidence per row;
- no silent truncation of aging-only tasks;
- no fallback timestamp interpreted as source fact;
- if a source timestamp is genuinely absent, explicit limitation/warning instead of age_days=0 being presented as fact;
- no employee/person scoring.

## Phase 8 — resolution forms
At least 3 each where applicable:
- `cycle time спринта DMS`
- `lead time сентябрьского спринта DMS`
- `carryover текущего спринта DMS`
- `predictability спринта DMS`
- `риски текущего спринта DMS`

Identity-only resolution must not terminate the analytical request.

## Phase 9 — Browser C
Real UI representative for all five skills.

Required:
- cycle/lead show real source-backed metric presentation;
- carryover task-table style;
- risk queue includes aging/overdue rows proven by Oracle, not only blocked rows;
- predictability is metric or typed source-unavailable depending on live source;
- no stack/contract/session leakage.

## Phase 10 — retained regression
At minimum:
- Wave S1 four sprint metrics;
- sprint.health;
- blocked tasks;
- raw status `На исправлении`;
- task.lookup DMS-380;
- task.history;
- task.time_in_status;
- person+status;
- attachments;
- same-session continuation;
- WIP/scope;
- dummy-55.

## Phase 11 — source/local/perf audit
Require:
- local factual `/api/v1/tasks` reads = 0;
- no tenant-wide scan used to fake sprint metrics;
- bounded/concurrency-bounded history reads;
- no fake/frozen cache;
- source outages fail closed;
- plugin invariant GREEN.

Re-probe `/api/v1/swtr-read/versions` once and record its current status only.
Do **not** remediate release search in this assignment.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_WAVE_S2_FIVE_SKILL_GREEN`
- `AGENT_CORE_V4_WAVE_S2_FIVE_SKILL_RED`

If GREEN:
- recommend creating a Wave S2 rollback checkpoint;
- recommend next work = bounded release source recovery (`release.search` + `release.health`) before the next five-skill batch.

If RED:
- identify the first failing boundary and STOP.
- no production edits.
- no next wave.
