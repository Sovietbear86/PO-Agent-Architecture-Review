# GigaCode — Current Action

## ACTIVE: Assignment 224R — UI usability re-gate

Role: QA/adversarial tester only. Do NOT modify production code.

A224 stopped at P2 because full-space row materialization hit the 10k pagination ceiling. Owner remediation now uses the bounded REAL AS21 per-space count surface based on source totalElements, isolates unavailable spaces, and removes false-zero UI.

### P0
Pull current branch and record HEAD. Prove no Agent Core/planner/runtime/session changes. Run V4 tests, batch5 tests, tsc --noEmit and vite build. Require 0 unexplained failures and 0 AS21 mutations.

### P2R — first mandatory re-gate
For WMB, DMS, OLP, CRPV and STS:
- independently read the bounded REAL AS21 count surface/source metadata;
- compare exact total with po.status_report.data.by_space_tasks[SPACE].total;
- require exact total parity for every source-ready space, including CRPV/STS above 10k;
- prove the count path does not enumerate the entire task corpus and does not use task-query pagination;
- verify a single unavailable space is represented only as typed SOURCE_UNAVAILABLE with total=null while other source-ready spaces remain usable;
- Browser C title must be "Задачи по пространствам";
- source-ready total is shown exactly;
- unavailable total is "—"/typed unavailable, never 0;
- active/completed/blocked must not be fabricated. Current bounded source certifies total only, so typed SOURCE_CONDITIONAL status breakdown is expected and GREEN.

If P2R is RED, STOP.

### P1 — Overview
Attention renders at most 10 rows initially; when more exist show "Показаны первые N из M"; internal scroll works; Attention and Daily Brief have comparable visible height; desktop and 480px viewports have no harmful horizontal overflow.

### P3 — local task CRUD
Create a local task with HIGH priority, TODO status, at least two labels, owner and description. Verify reload persistence, status TODO -> IN_PROGRESS -> DONE persistence, deletion, old-schema migration to MEDIUM/TODO/[], and 0 AS21 writes.

### P4 — Sprint predictability
DMS-SPRNT-3. If authoritative sprint-start commitment baseline is absent, predictability remains fail-closed and UI explains the missing baseline. No fabricated percentage/current-scope substitution.

### P5 — Releases
OLP 1.6.0 and WMB 24Q1: explicit source limitation, no fake zero/empty scope, no pseudo forecast. Sparse UI is accepted until AS21 release linkage exists.

### P6 — Team
Test DMS, OLP, WMB and CRPV or STS. No manual capacity baseline input and no "Пересчитать". 40h/week/person policy is visible and automatic. Every team request carries selected space. Source-ready widgets populate and switching space cannot leak old-space values. Capacity may be SOURCE_CONDITIONAL when estimates are absent, never fake 0.

### P7 — Quality Aging
WMB and DMS, thresholds 7 and 15. Query includes selected space plus threshold. Compare source-ready keys/count/age_days with independent bounded Oracle B. REAL_EMPTY only when source proves it. No unscoped aging query.

### P8 — retained smoke
Do not rerun full 54/54. Retain Quality WMB-102 semantics, Sprint DMS-SPRNT-3 throughput/risk, rich chat rendering, competency recommendation and release source-conditional behavior.

### P9 — audit
Require 0 AS21 mutations, 0 local factual fallback, 0 tenant-wide task scans, no full-space row materialization for counts, and localStorage writes only for LOCAL tasks.

### Verdict
Exactly one:
- AGENT_CORE_V4_UI_USABILITY_GREEN_A224R
- AGENT_CORE_V4_UI_USABILITY_RED_A224R

If GREEN recommend checkpoint/v4-ui-usability-green-a224r and next owner phase = visual design system plus slide-derived backgrounds. Do NOT start Learning Reviewer yet.

If RED preserve exact source/backend/UI evidence and stop at first confirmed boundary.

Do not modify code.
