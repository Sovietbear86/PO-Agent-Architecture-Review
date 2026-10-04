# GigaCode — Current Action

## ACTIVE: Assignment A229F2R3 — fixed in-progress created-period re-gate

Role: QA/adversarial tester only. Do not modify code.

Owner chose a plugin-only fix. Do NOT recommend or implement Core/planner/robust-repair changes in this gate.

New extra capability:
`task.search_created_in_progress`

Contract:
- handler = existing `build_task_search_created`;
- fixed plugin argument = `status="in_progress"`;
- planner supplies only period/person/space;
- canonical 54 is unchanged.

## P0 — integrity / registry

1. Pull current branch; record START_HEAD and clean worktree.
2. Prove stable Core/Harness/API session files remain byte-identical to `checkpoint/v4-stable-product-a229f1r2@9d71a795...`.
3. Instantiate production plugin registry and prove:
   - skill `task.search_created_in_progress` exists;
   - capability exists;
   - binding fixed_arguments = `{"status":"in_progress"}`;
   - no binding mismatch.
4. Run focused created-period tests including fixed-binding tests.
5. Run full V4 blast-radius.
6. Any Core/plugin-registry/test regression => RED STOP.

## P1 — blocking case first: IN_PROGRESS + period

Query:
`Задачи Калачанова в работе в пространстве STS созданные за последние 5 дней`

Build a fresh independent REAL AS21 oracle over Kalachanov+STS:
- authoritative created_at;
- last-5-calendar-days window;
- canonical IN_PROGRESS semantics.

Run 5 times.

Require:
- planner selects/loads `task.search_created_in_progress`;
- terminal capability = `task.search_created_in_progress`;
- planner arguments contain raw created_period + person + STS;
- planner does NOT need to emit status;
- executed handler observation shows fixed status=`in_progress`;
- exact key/count parity 5/5, including legitimate REAL_EMPTY=0 if oracle remains empty;
- must not broaden to all open tasks;
- 0 false zero, local fallback, tenant-wide scan.

Any bounded-repair failure before the fixed capability call => RED STOP with full trajectory.

## P2 — retained OPEN + period

Query:
`Открытые задачи Калачанова в пространстве STS созданные за последние 5 дней`

Run 3 times with fresh oracle.

Require:
- existing `task.search_created` path remains GREEN;
- exact parity;
- no accidental routing to fixed in-progress capability.

## P3 — recency-only wording

Query:
`Новые задачи Калачанова в STS за последние 5 дней`

Run 5 times.

Require:
- recency interpreted as created_period;
- no workflow status invented solely from recency wording;
- terminal `task.search_created` OR typed clarification if genuinely ambiguous;
- exact created-period parity for completed runs;
- target: 5/5 deterministic completion; any planner bounded-repair failure is RED.

## P4 — retained period controls

One run each:
- explicit 29.09.2026–01.10.2026;
- plain last 2 days;
- missing authoritative created_at fixture -> fail closed.

## P5 — architecture audit

Require:
- canonical 54 unchanged;
- extra skill/capability only;
- 0 Agent Core/planner/runtime/session changes;
- no surname/space/day-count hardcode;
- no phrase-specific router;
- fixed status uses generic plugin binding seam;
- public/community repo remains unsynced until GREEN.

## Verdict

Exactly one:
- `AGENT_CORE_V4_CREATED_PERIOD_STATUS_GREEN_A229F2R3`
- `AGENT_CORE_V4_CREATED_PERIOD_STATUS_RED_A229F2R3`

If GREEN:
- recommend checkpoint `checkpoint/v4-created-period-status-green-a229f2r3`;
- owner may sync the certified plugin change to public/community repo;
- return to stabilized release-hardening roadmap.

If RED:
- preserve first failing boundary and STOP.

Do not modify code.
