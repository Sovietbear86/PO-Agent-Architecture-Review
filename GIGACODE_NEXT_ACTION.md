# GigaCode — Current Action

## ACTIVE: Assignment A227R2 — P3-C re-gate, then resume

Role: QA/adversarial tester only. Do not modify code.

Owner fix is plugin-only. Stable Core must remain zero diff vs A227 baseline `db5e35f`.

### P0 — focused integrity
1. Pull current branch and record START_HEAD.
2. Prove zero diff vs `db5e35f` for stable Core/LLM files.
3. Run focused tests for:
   - plugin task-search status normalization;
   - attachment sprint/status composition;
   - retained task search/composition;
   - full V4 blast-radius.
4. Any unexplained failure => RED STOP.

### P3-C first — 5/5 exact parity
Query:
`Задачи в работе в сентябрьском спринте по DMS`

Build a fresh independent REAL AS21 oracle immediately before runs.

Require on all 5 runs:
- source-backed DMS September sprint resolution;
- terminal task collection;
- preserved space + sprint_id + status;
- Russian `В работе` and English `In Progress` converge on canonical IN_PROGRESS semantics;
- exact task-key/count parity with the canonical IN_PROGRESS oracle;
- no false zero;
- no tenant-wide scan.

If any run is RED, preserve trajectory and STOP.

### P3 remaining
After P3-C GREEN run:
A) `Открытые задачи Калачанова с вложениями в пространстве WMB`
B) `Задачи Семавина по рискам`
D) `Спринты в DMS`

Use independent REAL AS21 oracles and retained acceptance rules.

### P4–P7
If all P3 GREEN, continue unchanged:
- P4 task cards/persistence;
- P5 Quality refresh isolation;
- P6 fresh Aging exact parity DMS >7 / >15;
- P7 retained regression/source audit.

## Verdict
Exactly one:
- `AGENT_CORE_V4_PO_ACCEPTANCE_GREEN_A227R2`
- `AGENT_CORE_V4_PO_ACCEPTANCE_RED_A227R2`

If GREEN recommend checkpoint `checkpoint/v4-po-acceptance-green-a227r2` and release hardening next.
Learning Reviewer 2.0 remains blocked.

If RED preserve first failing evidence and STOP.
