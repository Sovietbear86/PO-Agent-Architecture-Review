# GigaCode — Current Action

## ACTIVE: Assignment 224 — UI usability/data correctness gate before visual redesign

Role: QA/adversarial tester only. Do NOT modify code.

### Frozen baseline
A223R2 is GREEN.
Checkpoint:
`checkpoint/v4-ui-state-lineage-green-a223r2@e0f435d10b586fbb7bfb31c6e0e853496338e099`

The shared state/lineage gate is closed. A224 validates owner-observed product usability/data corrections before the visual redesign.

### Owner implementation
Commits under test:
- `bb3ebf93ad08edeb66f1595984112c83719f17be` — bounded full-space task counts in po.status_report
- `ea666f1687d3ed8da02ce342ea50bd15a4b67250` — Overview scroll + "Задачи по пространствам"
- `ad6c202d69bdcf1597bdacd30d74828e703b6308` — balanced overview panel scrolling
- `8385a3eadb000d1a45dd3d425542fcdde60e2a34` — local task priority/labels/status/delete
- `4aa4d915bef637bf9bdb549f7802c8536be606b7` — Team space selector + automatic 40h/week owner policy
- `41c290ce67e9b7680ec6a6be4395be6c011df29a` — Aging queue bounded by selected space
- `e04bc678addca176ec194eee3f8899b3ee8556dc` — explicit predictability source-limitation hint
- `004e0e33a7c9303b3286c1f513e59f72b27dccdb` — status-report full-space regression tests

No Agent Core/planner/runtime/session changes.

## P0 — build / architecture
1. Pull branch, clean worktree, record START_HEAD.
2. Diff from A223R2 checkpoint.
3. Prove:
   - only one backend plugin semantic extension: po.status_report adds bounded full-space counts;
   - all full-space reads are project-scoped per approved space;
   - no tenant-wide task scan;
   - no AS21 writes;
   - other changes are frontend/tests/docs only.
4. Run:
   - relevant Python tests including test_agent_core_v4_batch5_po.py
   - relevant V4 regression for po.status_report
   - frontend tsc --noEmit
   - vite build
5. Zero unexplained failures.

## P1 — Overview panel height / scrolling
Browser C on Overview.

Require:
- PO Attention and Daily Brief have comparable visible height;
- page does not expand to the full attention queue height;
- PO Attention renders at most 10 task rows initially;
- if source count > rendered count, UI explicitly says "Показаны первые N из M";
- internal vertical scrolling works where content exceeds panel height;
- "Задачи по пространствам" is visible without scrolling through dozens of attention rows.

Test responsive/narrow viewport too: no unusable nested overflow.

## P2 — full-space task counts
This is a source-correctness gate.

For each approved space:
- WMB
- DMS
- OLP
- CRPV
- STS

Independently query REAL AS21 using a bounded project/space query and obtain:
- total
- active
- completed
- blocked

Compare exact values with:
`po.status_report.data.by_space_tasks[SPACE]`

Require:
- exact parity for all 5 spaces;
- CRPV/STS must not appear as blank/zero unless Oracle B independently proves true zero;
- WMB count must represent the entire WMB space, NOT current sprint membership;
- no tenant-wide scan;
- UI block title exactly "Задачи по пространствам";
- each card shows total/active/completed/blocked.

If any space query is source-unavailable, the block must not silently fabricate zero.

## P3 — local task CRUD
Browser C, Tasks page.

Create a local task with:
- title
- description
- owner
- priority = HIGH
- status = TODO
- >=2 labels

Require:
- card shows owner + priority + labels;
- task persists after reload through browser localStorage;
- change status TODO -> IN_PROGRESS -> DONE and verify persistence;
- delete task and verify it disappears from localStorage and UI;
- create/load an old-schema localStorage row without priority/status/labels and confirm safe defaults:
  priority=MEDIUM, status=TODO, labels=[];
- 0 AS21 mutations.

## P4 — Sprint predictability
Use source-ready sprint DMS-SPRNT-3.

Require:
- other Sprint metrics remain correct from A223R2;
- predictability remains fail-closed if the source still lacks authoritative sprint-start commitment baseline;
- UI explicitly explains the missing baseline;
- no fabricated percentage;
- no substitution of current scope as commitment unless backend contract explicitly supplies it.

## P5 — Releases retained limitation
Use OLP 1.6.0 and WMB 24Q1.

Require:
- source limitation panels remain explicit;
- no fake 0/empty release scope;
- no pseudo forecast;
- page may remain sparse; this is accepted until AS21 release linkage is improved.

This is GREEN if it remains honest, even if low-information.

## P6 — Team page
Browser C.

Space selector:
- test DMS, OLP, WMB and at least one of CRPV/STS.

Require:
- no manual capacity baseline field;
- no "Пересчитать" button;
- visible policy says 40h/week/person and automatic normalization;
- workload/WIP/blocked/bottlenecks/distribution requests include selected space;
- selected source-ready space populates actual widgets, not bare-query NEEDS_CLARIFICATION;
- switching space refreshes data and does not leak previous-space values;
- capacity may be SOURCE_CONDITIONAL if task estimates are absent; this must show as a limitation, not fake 0 utilization.

Audit exact scoped source calls.

## P7 — Quality Aging queue
Browser C.

For each of WMB and DMS:
- select space;
- threshold 7;
- threshold 15;
- one large threshold expected to be empty if source proves it.

Require:
- query includes selected space + threshold;
- source-ready rows render exact task keys/count/age_days vs Oracle B;
- threshold change refreshes results;
- proven zero may show empty;
- source-limited/unavailable must not look like a proven empty queue;
- no unscoped aging query.

## P8 — compact retained smoke
Do not rerun full 54/54.

Retain:
- Quality WMB-102 = 85/100, 0/100, missing 1, REWORK
- Sprint DMS-SPRNT-3 throughput/risk queue from A223R2
- chat rich rendering
- competency recommendation
- release source-conditional behavior

## P9 — audit
Require:
- 0 AS21 mutations
- 0 local factual fallback reads
- 0 tenant-wide task scans
- full-space queries are individually scoped by project/space
- localStorage writes only for LOCAL tasks

## Verdict
Use exactly one:
- `AGENT_CORE_V4_UI_USABILITY_GREEN_A224`
- `AGENT_CORE_V4_UI_USABILITY_RED_A224`

If GREEN:
- recommend checkpoint/v4-ui-usability-green-a224
- next owner phase = visual design system + slide-derived backgrounds for all six pages
- do NOT start Learning Reviewer

If RED:
- report first confirmed failing boundary
- preserve screenshot + exact backend/source comparison
- STOP

Do not modify code.
