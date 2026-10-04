# GigaCode — Current Action

## ACTIVE: Assignment A229F2R2 — created-period + status re-gate

Role: QA/adversarial tester only. Do not modify code.

Previous A229F2R RED was test-only:
- invalid `TaskStatus.DONE` in the new test fixture;
- no production/plugin/Core defect was proven;
- owner changed only the test to use real terminal enum values.

## P0 — integrity / retained test gate

1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD and clean worktree.
2. Prove stable Core/Harness/API session files are byte-identical to `checkpoint/v4-stable-product-a229f1r2@9d71a795...`.
3. Run focused created-period tests, including:
   - explicit period;
   - relative period;
   - open + period;
   - in-progress + period;
   - missing created_at provenance fail-closed.
4. Run plugin registry/catalog tests and full V4 blast-radius.
5. Any production/plugin/Core failure => RED STOP.
6. A failure caused only by a new test fixture must still be reported, not auto-fixed.

## P1 — OPEN + created period

Query:
`Открытые задачи Калачанова в пространстве STS созданные за последние 5 дней`

Build a fresh independent REAL AS21 oracle over canonical Kalachanov+STS:
- authoritative created_at;
- window = 00:00 Europe/Moscow of current_day-4 through execution time;
- canonical not-completed/open semantics.

Run 5 times.

Require:
- terminal capability = `task.search_created`;
- raw created_period preserved;
- person + STS + explicit open/not-completed status preserved;
- no separate terminal `task.search_status`;
- exact task-key/count parity 5/5;
- every result satisfies BOTH period and open constraints;
- 0 false zero / local factual fallback / tenant-wide scan.

## P2 — IN_PROGRESS + created period

Query:
`Задачи Калачанова в работе в пространстве STS созданные за последние 5 дней`

Fresh independent canonical IN_PROGRESS oracle.

Run 3 times.

Require:
- one `task.search_created` capability carrying status;
- exact key parity;
- no broadening to all open tasks.

## P3 — recency wording without invented workflow state

Query:
`Новые задачи Калачанова в STS за последние 5 дней`

Require:
- creation-period semantics are preserved;
- no workflow status=New is invented solely from `новые`;
- terminal capability = `task.search_created` OR typed clarification if genuinely ambiguous;
- malformed/fail-closed trajectory due to artificial status composition is RED;
- if completed, exact parity with created-period-only oracle.

Run 3 times.

## P4 — retained A229F1R2

One live run each:
- explicit range;
- plain relative period;
plus fixture control for missing authoritative created_at.

Require retained semantics.

## P5 — architecture audit

Require:
- canonical 54 unchanged;
- plugin-only extension;
- 0 Core/planner/runtime/session changes;
- no surname/STS/5-day special route;
- no phrase router;
- bounded source read;
- existing generic status matcher is used.

## Verdict

Exactly one:
- `AGENT_CORE_V4_CREATED_PERIOD_STATUS_GREEN_A229F2R2`
- `AGENT_CORE_V4_CREATED_PERIOD_STATUS_RED_A229F2R2`

If GREEN:
- recommend checkpoint `checkpoint/v4-created-period-status-green-a229f2r2`;
- owner may sync this certified plugin change to the public/community repo.

If RED:
- preserve first failing boundary and STOP.

Do not modify code.
