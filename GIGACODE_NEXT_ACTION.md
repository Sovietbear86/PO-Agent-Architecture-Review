# GigaCode — Current Action

## ACTIVE: Assignment A229F2R — created-period + status re-gate

Role: QA/adversarial tester only. Do not modify production/plugin/frontend/backend/test code.

Owner change is intentionally plugin-only:
- `task.search_created` now accepts optional `status`;
- existing generic typed status matcher is reused;
- Core/planner/runtime/session files must remain unchanged.

## P0 — integrity

1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD and clean worktree.
2. Prove stable Core/Harness/API session files are byte-identical to stable checkpoint `checkpoint/v4-stable-product-a229f1r2@9d71a795...`:
   - `src/po_agent/harness/contracts.py`
   - `src/po_agent/harness/agent_core_v4.py`
   - `src/po_agent/harness/agent_core_v4_robust.py`
   - `src/po_agent/api/v1/__init__.py`
3. Run focused created-period tests including new status cases.
4. Run plugin registry/catalog tests and full V4 blast-radius.
5. Any unexplained regression => RED STOP.

## P1 — manual PO case: OPEN + created period

Query:
`Открытые задачи Калачанова в пространстве STS созданные за последние 5 дней`

Immediately build an independent REAL AS21 oracle over the bounded canonical Kalachanov+STS corpus:
- authoritative source created_at;
- window = 00:00 Europe/Moscow of current_day-4 through execution time;
- task.is_open / canonical not-completed semantics.

Run 5 times.

Require all 5:
- planner selects `task.search_created` as the terminal task-collection capability;
- arguments preserve raw `created_period="последние 5 дней"`, person, space=STS, and explicit open/not-completed status;
- no separate `task.search_status` terminal hop is needed;
- exact task-key/count parity vs oracle;
- every returned task is inside the created window AND open/not-completed;
- 0 false zero;
- 0 local factual fallback;
- 0 tenant-wide scans.

## P2 — IN_PROGRESS + created period

Query:
`Задачи Калачанова в работе в пространстве STS созданные за последние 5 дней`

Build fresh independent oracle with canonical IN_PROGRESS semantics.

Run 3 times.

Require:
- single `task.search_created` capability with status preserved;
- exact key parity;
- no status loss and no broadening to all open tasks.

## P3 — recency wording must not invent workflow status

Query:
`Новые задачи Калачанова в STS за последние 5 дней`

Interpretation under the skill contract:
- "за последние 5 дней" is the explicit creation-period constraint;
- do NOT fabricate workflow status=New unless the planner has an explicit user-requested workflow-state signal.

Run 3 times.

Require:
- terminal `task.search_created`;
- period/person/space preserved;
- no invented workflow status solely from the adjective `новые`;
- exact parity with created-period-only oracle for the same window.

If the planner legitimately requests clarification rather than inventing a status, document it; a fabricated status or malformed trajectory is RED.

## P4 — retained created-period certification

One run each:
- explicit period `с 29.09.2026 по 01.10.2026`;
- relative plain period `созданные за последние 2 дня`;
- missing authoritative created_at fixture -> fail closed.

Require retained A229F1R2 semantics.

## P5 — architecture/source audit

Require:
- canonical 54 unchanged;
- `task.search_created` remains plugin-owned extra capability;
- 0 Core/planner/session modifications;
- no surname/STS/5-days special implementation branch;
- no phrase-specific router;
- no local date/status factual cache;
- source scan remains bounded by person and/or space.

## Verdict

Exactly one:
- `AGENT_CORE_V4_CREATED_PERIOD_STATUS_GREEN_A229F2R`
- `AGENT_CORE_V4_CREATED_PERIOD_STATUS_RED_A229F2R`

If GREEN:
- recommend checkpoint `checkpoint/v4-created-period-status-green-a229f2r`;
- owner may then sync the certified plugin change to `PO-Agent-Architecture-Public`;
- return to the stabilized release-hardening roadmap.

If RED:
- preserve first failing boundary and STOP.

Do not modify code.
