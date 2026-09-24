# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_215C_TIME_ACCOUNTING_SOURCE_FORENSIC

## Role lock
GigaCode is QA/source-forensic tester only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement a skill or fix.
Do NOT start A216 / Batch 3.
Commit/push only the QA report and evidence.

## Context
The AS21 UI for task DMS-380 visibly contains a time-accounting block ("Учет времени") with a non-zero "Затрачено" value (shown by the owner as 1н. 1д.).

The canonical Task model already has:
- estimate_hours
- time_spent_hours

but current live V4 mapping has not been certified for actual time-accounting/worklog data.

This may materially change the semantics of team utilization:
- planned load/capacity requires estimates;
- actual utilization may be computable from source-backed spent/worklog time, but only if the source exposes enough authoritative detail.

## Goal
Find the authoritative REAL AS21 source contract for time spent/worklogs, using DMS-380 as the primary proof case.

Do not assume that the UI aggregate is directly suitable for team utilization.

## Phase 0 — baseline
1. Pull the branch and record START_HEAD.
2. No code changes.
3. Preserve A215B GREEN and Batch 3 pending state.

## Phase 1 — inspect live MCP tool schema
List/search the connected MCP-SWTR tools for any capability related to:
- worklog
- logged time / time spent
- time tracking / accounting
- labor / effort actuals
- task/unit detail that may contain spent-time attributes

Record exact tool names and schemas. Do not infer from repo code.

## Phase 2 — raw DMS-380 source proof
Use only bounded reads for DMS-380.

Capture the raw source payload(s) that correspond to the AS21 UI time-accounting block.

Determine whether the source exposes:
A. only a cumulative aggregate on the task;
B. individual worklog entries;
C. both.

For every discovered field record:
- source field/attribute code;
- raw value and unit;
- normalized interpretation;
- whether it is task total or per-user;
- author/member identity if present;
- worklog date/timestamp if present;
- whether the value can be scoped to a sprint/date window;
- whether deleted/edited worklogs can be distinguished.

Do not expose secrets/tokens in the report.

## Phase 3 — UI parity for DMS-380
Independently reconcile the source value with the UI screenshot value "Затрачено 1н. 1д.".

Determine the AS21 duration convention:
- hours per workday;
- days per week if encoded;
- raw seconds/minutes/hours if available.

Do not assume 8h/day or 5d/week unless the source/config explicitly proves it.

Verdict must say whether exact parity is proven or only approximate.

## Phase 4 — adapter/path inventory
Inspect current production source path and answer:
- does task-api already receive the time-spent/worklog field but drop it?
- does TaskApiAS21Adapter currently map it to Task.time_spent_hours?
- is a new bounded swtr-read endpoint needed?
- can existing task detail/query return it without tenant scan?
- is per-member attribution available?

Identify the first missing boundary only. Do not fix.

## Phase 5 — utilization feasibility
Classify each metric independently:

1. task actual time:
   "сколько времени списано на DMS-380"

2. member actual time:
   "сколько списал Иванов"

3. sprint actual spent:
   total worklogs whose timestamps fall inside a sprint window / membership rules

4. team actual utilization:
   actual spent / authoritative capacity for the same member and time window

5. planned utilization:
   estimate / authoritative capacity

For each return one:
- SOURCE_READY
- SOURCE_PARTIAL
- SOURCE_BLOCKED

Important:
- a cumulative task total without dated/user worklogs is NOT enough to attribute utilization to a person or sprint;
- actual spent alone is NOT enough for utilization without an authoritative capacity denominator;
- never substitute task-count workload for hours.

## Phase 6 — recommended skill contracts
Without implementing, propose the smallest plugin-only additions, likely candidates:
- task.time_spent
- task.worklogs (only if source exposes entries)
- sprint.time_spent
- team.time_spent
- team.utilization_actual (only if numerator + capacity denominator are authoritative)

State which should be implemented now vs SOURCE_CONDITIONAL.

## Phase 7 — retained smoke
Verify no regression from the forensic activity:
- team.workload DMS
- team.capacity DMS remains fail-closed under current implementation
- release.search
- dummy-55
- local factual reads = 0
- tenant-wide scans = 0

## Verdict
Use exactly one:
- `TIME_ACCOUNTING_SOURCE_READY_FOR_OWNER_IMPLEMENTATION`
- `TIME_ACCOUNTING_SOURCE_PARTIAL`
- `TIME_ACCOUNTING_SOURCE_BLOCKED`

Report:
1. exact live tool/field contract;
2. DMS-380 source/UI parity;
3. normalization/unit semantics;
4. attribution/time-window capability;
5. first missing production boundary;
6. metric feasibility matrix;
7. minimal owner implementation plan.

STOP after report. Do not modify code.
