# GigaCode — Current Action

## ACTIVE: Assignment 223R2 — Sprint widget field re-gate

Role: QA/adversarial tester only. Do not modify code.

Prior verdict: AGENT_CORE_V4_UI_STATE_LINEAGE_RED_A223R.

Closed already:
- Quality WMB-102 now shows 85/100, Acceptance 0/100, 1 gap, REWORK, no NaN.

A223R blocker:
- Sprint risk queue read wrong fields: UI used risks/key/risk_score, source uses queue/task_key/rank.
- Sprint throughput read throughput_tasks, source uses throughput.

Owner fix:
- commit b0695506a1e218801eb17436979b8d2898246e9e
- SprintPage only
- no backend/Core/planner/runtime/session changes

## P0
1. Pull branch, clean worktree, record START_HEAD.
2. Diff from A223R report state.
3. Prove production delta is SprintPage leaf accessors only.
4. Run tsc --noEmit and vite build.

## P1 — blocking Sprint re-gate
Use DMS-SPRNT-3 with fresh Browser C.

Compare independently to current backend source.

If source is unchanged from A223R, expect:
- scope 73
- completed 19
- velocity 19 tasks/sprint
- WIP 31
- readiness 26%
- throughput 1.385 completed_tasks/calendar_day
- risk count 38
- risk queue 38 rows

Require:
- throughput exact, not em-dash
- risk count equals source count
- non-empty source queue renders non-empty body
- no "риски не выявлены" when count > 0
- task_key, reasons and rank render from source fields

## P2 — Sprint regression
Check:
- one non-empty risk sprint
- one source-proven empty risk sprint if available
- one source-limited/clarification case

Require:
- non-empty stays non-empty
- REAL_EMPTY only when source proves zero
- source-limited never becomes zero/no-risks
- health/WIP/velocity unchanged

## P3 — finish retained UI gate
Continue P5-P9 from A223R without redoing earlier GREEN phases.

Releases:
- source-conditional => state panels, no fake zero/empty

Team:
- no hardcoded 40h
- scoped workload/WIP/blocked exact
- capacity state-safe
- competency note retained

Tasks:
- list-mode non-empty query renders task cards
- clarification and proven-empty states correct
- single-key task.lookup mismatch may remain non-blocking UX finding

Chat:
- daily brief and competency markdown/table rendering still GREEN
- evidence/feedback controls work

Audit:
- 0 mutations
- 0 local factual fallback reads
- 0 tenant-wide broadening

## P4 — compact Quality smoke
WMB-102 must still be:
- 85/100
- 0/100
- missing 1
- REWORK
- no NaN

## Verdict
Use exactly one:
- AGENT_CORE_V4_UI_STATE_LINEAGE_GREEN_A223R2
- AGENT_CORE_V4_UI_STATE_LINEAGE_RED_A223R2

If GREEN:
- recommend checkpoint/v4-ui-state-lineage-green-a223r2
- next phase = visual design system + slide-derived backgrounds

If RED:
- save first failing screenshot + backend payload and STOP.

Do not modify code.
