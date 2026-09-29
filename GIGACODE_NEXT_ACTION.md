# GigaCode — Current Action

## ACTIVE: Assignment 226R3 — Tasks scope fix + deferred final UX forensic

Role: QA/adversarial tester only. Do NOT modify code.

Prior verdict:
`AGENT_CORE_V4_UI_POLISH_SNAPSHOT_RED_A226R2`

A226R2 P1 was GREEN. First RED was P2:
- selected search space was dropped on submit, so DMS UI selection could still execute WMB;
- Status mode omitted space and expanded into an all-space scan.

## Owner fixes under test

- Tasks uses persisted `searchSpace`;
- Text and Status submit the selected space explicitly;
- snapshot key includes submitted space;
- Status mode shows the same space selector;
- task-api partial-search tests now pass concrete endpoint args;
- all prior A226R2 fixes remain in place.

## P0 — preflight

1. Pull current branch; clean worktree; record START_HEAD.
2. Prove no Agent Core/planner/runtime architecture drift.
3. Run focused tests:
   - task-api phrase-search partial/isolation tests;
   - task catalog/live-handler tests;
   - aging/time/local-task regressions;
   - tsc --noEmit;
   - vite build.
4. Any unexplained failure => RED STOP.

## P1 — Tasks space selector exactness

### Text
- select DMS;
- enter `БП 2027`;
- press Найти.

Require:
- submitted query says DMS, never WMB;
- task-api network/log shows space=DMS;
- exact DMS oracle parity;
- switch to WMB and repeat; exact WMB parity;
- away/back preserves both selected and submitted space;
- page Refresh re-runs the same submitted space/query.

### Status
Use a source-ready status and WMB first.
Require:
- query includes selected WMB;
- task-api reads WMB only;
- no all-space scan;
- exact source parity.
Then change to DMS and repeat.

If any mode silently falls back to another space or scans all spaces => RED STOP.

## P2 — Tasks UX retained

Visible modes exactly:
- Текстовый поиск
- Исполнитель
- Статус
- Спринт
- Релиз

No attachment/Excel/PDF/MSG buttons.
Assignee Kalachanov.V.V remains source-exact.
Sprint uses DMS-SPRNT-3.
Release mode uses a source-backed release identity and remains typed if membership is unavailable.

## P3 — local drawer hit testing

At 1440×900 and a common laptop viewport:
- open local task create drawer;
- fill title, priority, tags, deadline;
- click center of Создать.

Require:
- AI launcher hidden/non-hit-testable while local or AS21 task drawer is open;
- create/edit/reload/delete works;
- LOCAL-NNNN stable;
- 0 AS21 writes.

## P4 — Overview refresh completion

Press Обновить on populated Overview:
- old snapshot stays visible;
- loading ends on success/error/timeout;
- must not remain indefinitely in `Обновляем…`;
- timestamp is ru-RU date+time;
- timeout/failure preserves stale data and shows error;
- away/back causes 0 new POST.

## P5 — Quality Aging

DMS + 15:
- load once;
- press Aging Обновить with unchanged criteria.

Require one live re-read with same DMS/15 criteria and exact source parity.

## P6 — Sprint forensic

Use exact id:
`DMS-SPRNT-3`

Verify independently:
- Scope
- Completed
- Velocity
- Throughput
- WIP
- Risk Queue
- Predictability/readiness

No generic NEEDS_CLARIFICATION/FAILED is acceptable for a source-ready metric with this valid id.
For Predictability, prove the actual source-backed baseline:
- if historical previous-sprint data is sufficient, exact value required;
- otherwise typed SOURCE_CONDITIONAL is acceptable;
- no fabricated baseline/current-scope proxy.

## P7 — Releases forensic

Use release.search/source directory first.
Test valid current release identities, including 1.6.0 / 24Q1 if still present.

Verify separately:
- Scope
- Progress
- Blockers
- Dependencies
- Risk Queue

If release-to-task membership is absent:
- typed SOURCE_CONDITIONAL/UNAVAILABLE is expected;
- no fake zero;
- no pseudo forecast;
- valid release id must not degrade to generic clarification merely because membership is unavailable.

## P8 — retained snapshot/design/audit

Recheck:
- Platform V brand;
- OLAP + DataMarts only;
- rich Daily Brief;
- Team actual utilization;
- team-scoped Aging;
- six backgrounds;
- 1440 + 480 no document overflow;
- cached revisit = 0 extra POST;
- manual refresh page-bounded;
- 0 mutations;
- 0 local factual fallback;
- 0 tenant-wide scan.

## Verdict

Exactly one:
- `AGENT_CORE_V4_UI_POLISH_SNAPSHOT_GREEN_A226R3`
- `AGENT_CORE_V4_UI_POLISH_SNAPSHOT_RED_A226R3`

If GREEN:
- recommend checkpoint `checkpoint/v4-ui-polish-snapshot-green-a226r3`;
- next owner phase = final PO Browser UX acceptance + release hardening;
- Learning Reviewer still waits for owner acceptance.

If RED:
- preserve first failing evidence and STOP.

Do not modify code.
