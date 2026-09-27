# GigaCode — Current Action

## ACTIVE: Assignment 224R — exact space totals + finish usability gate

Role: QA/adversarial tester only. Do NOT modify code.

### Prior verdict
A224 = RED_P2_FULL_SPACE_COUNTS_UNAVAILABLE_PAGINATION_CAP

Root cause:
- full-space row materialization via /task-query is capped by pagination;
- CRPV/STS cannot be fully materialized;
- one space failure sank the entire status report;
- UI could show false 0 next to SOURCE_UNAVAILABLE.

### Owner remediation
Commits:
- d6993d4402be9ca16f54a6c6792f807b3164bc89 — task-api /swtr-read/task-count using one-page totalElements metadata
- 984a601484dde37234a812d4529372c612c58568 — adapter get_space_task_count()
- 94c41d3307520254380a9f60fe7f557484441834 — po.status_report uses metadata counts + per-space isolation
- a2e866f0c4e47eb45e0386ef8cda8b74d564378e — Overview renders exact totals and typed unavailable state
- a36a2a8990695ba6ce27823da1e301e9da5cd0ac — Overview status-breakdown note styling
- 5f496598d770c519b6a616bd42c6435d93099523 — focused metadata-count tests
- 11fdba597cb8c6ef63ef55a8cfca9669f09efb37 — per-space failure-isolation regression

### Revised source contract
Important: do NOT require full-space active/completed/blocked parity in A224R.

A224 proved that current source contract cannot safely produce those breakdowns for >10k spaces without a verified source-side aggregation/filter-count capability.

Current intended behavior:
- full-space TOTAL per space = SOURCE_READY exact count from source totalElements
- active/completed/blocked full-space breakdown = SOURCE_CONDITIONAL / not displayed as factual numbers
- one failed space => that space typed SOURCE_UNAVAILABLE; remaining spaces still return
- all failed => whole capability may fail source-unavailable
- no row materialization for total counting
- no false zero

## P0 — diff/build/tests
1. Pull branch, clean worktree, record START_HEAD.
2. Diff from A224 report commit.
3. Prove count route uses one source page only, page=0, size=1, query scoped to one approved space.
4. Prove no tenant-wide scan.
5. Run:
   - task-api relevant tests / import checks
   - test_agent_core_v4_batch5_po.py
   - full relevant V4 regression
   - frontend tsc --noEmit
   - vite build
6. Zero unexplained failures.

## P1 — task-count route exactness
For each:
- WMB
- DMS
- OLP
- CRPV
- STS

Call:
GET /api/v1/swtr-read/task-count?space=X

Independently compare returned total against REAL AS21 source metadata from find_units_by_filter with the same space predicate.

Require:
- exact total parity
- CRPV/STS succeed without walking all pages
- one bounded source call per count request
- latency materially below previous full row scans
- route returns status_breakdown_available=false
- no task rows returned

If source metadata itself is missing/unreliable, RED and stop.

## P2 — po.status_report isolation
Run po.status_report repeatedly.

Require:
- by_space_tasks contains all approved spaces
- each SOURCE_READY row has exact total
- active/completed/blocked are null / not fabricated
- no current-sprint count is mislabeled as full-space count
- current-sprint by_product/current totals remain A219/A221 compatible
- one injected/stubbed per-space count failure does not sink other spaces
- failed row state=SOURCE_UNAVAILABLE, total=null
- if at least one space succeeds, report remains terminal/usable

## P3 — Overview Browser C
Require:
- title exactly "Задачи по пространствам"
- cards show exact total task count
- status breakdown is explicitly marked unavailable/conditional
- no false 0 beside SOURCE_UNAVAILABLE
- CRPV/STS no longer show zero merely due pagination cap
- PO Attention still shows first 10 of total and internal scroll
- Daily Brief comparable visible height
- no page-length explosion

Also re-check narrow viewport:
- no destructive horizontal overflow
- if minor overflow remains, record as finding and only RED if core controls/content are unreachable.

## P4 — local task CRUD
Continue previously deferred A224 P3:
- create with HIGH + TODO + >=2 labels
- reload persists
- change TODO -> IN_PROGRESS -> DONE
- reload persists state
- delete removes from UI/localStorage
- old-schema row safely defaults MEDIUM/TODO/[]
- zero AS21 mutation

## P5 — Sprint predictability
Continue deferred A224 P4:
- DMS-SPRNT-3
- source-limited predictability must explain missing authoritative sprint-start baseline
- no fake percentage
- retained sprint metrics remain GREEN

## P6 — Releases
Continue deferred A224 P5:
- OLP 1.6.0 / WMB 24Q1
- honest SOURCE_CONDITIONAL/UNAVAILABLE
- no fake zero/empty
- no pseudo forecast
- sparse UI is accepted

## P7 — Team
Continue deferred A224 P6:
- test DMS, OLP, WMB and one of CRPV/STS
- no manual capacity baseline field
- no Recalculate button
- visible 40h/week owner-policy baseline
- requests are space-scoped
- workload/WIP/blocked/bottlenecks/distribution populate for source-ready selected space
- space switch does not leak stale values
- capacity may remain SOURCE_CONDITIONAL if estimates are missing

## P8 — Quality Aging queue
Continue deferred A224 P7:
- WMB and DMS
- thresholds 7, 15 and one source-proven empty threshold
- request must include selected space + threshold
- exact count/keys/age_days vs Oracle B where source-ready
- no unscoped aging request
- source-unavailable != proven empty

## P9 — retained smoke/audit
Retain:
- Quality WMB-102 = 85/100, 0/100, missing 1, REWORK
- Sprint DMS-SPRNT-3 throughput/risk queue
- chat rich rendering
- competency recommendation
- release source limitation

Audit:
- 0 AS21 mutations
- 0 local factual fallback reads
- 0 tenant-wide task scans
- localStorage writes only for local tasks

## Verdict
Use exactly one:
- AGENT_CORE_V4_UI_USABILITY_GREEN_A224R
- AGENT_CORE_V4_UI_USABILITY_RED_A224R

If GREEN:
- recommend checkpoint/v4-ui-usability-green-a224r
- next owner phase = visual design system + slide-derived backgrounds
- do NOT start Learning Reviewer

If RED:
- preserve first failing screenshot + exact backend/source evidence
- STOP

Do not modify code.
