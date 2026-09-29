# GigaCode — Current Action

## ACTIVE: Assignment 227R — re-gate first RED only

Role: QA/adversarial tester only. Do NOT modify production/frontend/backend/plugin/test/config code.

A227 stopped correctly at P3. P0/P1/P2 and P3-D were GREEN. Preserve those results; do not repeat unaffected gates.

Owner fixes since A227 RED:
- generic composite completion frontier now terminates when the latest loaded typed terminal skill is source-satisfied, so an earlier helper skill does not force four identical stochastic repair attempts;
- REAL task rows retain authoritative status_raw/status_type in typed observations;
- generic task.search literal workflow status filtering uses those authoritative source fields instead of collapsing "В работе" to a false zero.

## P0R — focused build/regression
1. Pull current HEAD; clean worktree; record START_HEAD.
2. Run tsc --noEmit and vite build.
3. Run focused V4 reliable/plugin/completion tests including the new literal-status regression.
4. No production edits.

## P3R-A — exact original composite case
Query exactly:
`Открытые задачи Калачанова с вложениями в пространстве WMB`

Require:
- person + WMB + open/not-completed + attachment constraints preserved;
- source-backed identity resolution;
- bounded source reads only;
- terminal attachment collection completes without planner repair loop;
- exact source parity for returned keys/count;
- no tenant-wide scan;
- no fabricated rows.
Run 5 times. All 5 must complete correctly. Any planner failed robust bounded repair => RED STOP.

## P3R-C — exact original sprint/status case
Query exactly:
`Задачи в работе в сентябрьском спринте по DMS`

Require:
- source-backed September DMS sprint resolution;
- literal source status "В работе" preserved;
- exact task-key/count parity against independent REAL AS21 oracle;
- do not accept false zero when oracle has matching rows;
- bounded reads only.
Run 5 times. All 5 must match oracle exactly.

## Then resume A227 from P4
Only if P3R-A and P3R-C are GREEN:
- resume P4 completion/card/drawer checks;
- P5 Quality refresh isolation;
- P6 exact Aging DMS >15 and >7;
- P7 retained regression.
Do not rerun already GREEN P1/P2/P3-D unless a focused regression requires it.

## Verdict
Exactly one:
- `AGENT_CORE_V4_PO_ACCEPTANCE_GREEN_A227R`
- `AGENT_CORE_V4_PO_ACCEPTANCE_RED_A227R`

If RED: preserve first failing evidence and STOP.
If GREEN: recommend checkpoint `checkpoint/v4-po-acceptance-green-a227r`.

Do not modify code.
