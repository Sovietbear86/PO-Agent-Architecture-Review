# GigaCode — Current Action

## ACTIVE: Assignment A227R — resume P3–P7

Role: QA/adversarial tester only. Do not modify code.

Pre-gate R2 is GREEN. Core is proven identical to A227 baseline; Tasks UI parity, Sprint Predictability, Release Forecast and full V4 regression are GREEN. Do not repeat P0-P2 unless owner code changes again.

## P3 — multi-constraint composition
Run each live case 5 times with an independent REAL AS21 oracle first.

A) `Открытые задачи Калачанова с вложениями в пространстве WMB`
Require all constraints preserved, exact source parity, valid REAL_EMPTY allowed, no repair-loop failure, no tenant-wide scan.

B) `Задачи Семавина по рискам`
Require source-backed identity, compositional task/risk path, no fabricated rows, 5/5 correct.

C) `Задачи в работе в сентябрьском спринте по DMS`
Require source-backed September sprint resolution; terminal result is task collection; preserve space+sprint_id+status; exact task-key/count parity; false zero is RED.

D) `Спринты в DMS`
Require grounded rich non-task result.

Any P3 RED => preserve first failing trajectory/oracle and STOP.

## P4 — task cards / persistence
Require real task cards and Task Details for task collections; grounded rich answer for non-task result; away/back zero POST with snapshot preserved; input edits without submit do not change current result; Refresh repeats exactly one last submitted raw query.

## P5 — Quality refresh isolation
Top Quality Refresh updates quality/missing/acceptance only. Task Проверить updates task-quality group only. Neither triggers Aging. Aging Refresh triggers Aging only. Preserve stale snapshot while refreshing.

## P6 — Aging live parity
Refresh independent REAL AS21 oracle immediately before DMS >7 and >15. Require exact keys/count, team-scoped bounded reads, live reread on same criteria, expected row fields, no false zero, no tenant-wide scan.

## P7 — retained regression
Recheck local-task CRUD; Platform V + OLAP/DataMarts; Sprint DMS-SPRNT-3 metrics/risk/predictability state; Release limitation; Team utilization; six backgrounds and responsive overflow; zero local factual reads; zero unauthorized mutations; zero tenant-wide scans.

## Verdict
Exactly one:
- `AGENT_CORE_V4_PO_ACCEPTANCE_GREEN_A227R`
- `AGENT_CORE_V4_PO_ACCEPTANCE_RED_A227R`

If GREEN recommend checkpoint `checkpoint/v4-po-acceptance-green-a227r` and next owner phase release hardening: restart/recovery, latency, security, rollback rehearsal. Learning Reviewer 2.0 remains blocked.

If RED preserve first failing evidence and STOP.
