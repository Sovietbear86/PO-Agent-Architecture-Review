# GigaCode — Current Action

## ACTIVE: Assignment 221R3 — Phase 8 sprint->attachments re-gate

Role: QA/adversarial tester only. Do not modify production/frontend/plugin/test/config code.

### Retained A221R2 GREEN
- canonical matrix: 54/54
- Phase 9: 6/6
- Browser C: 54/54 PASS
- Phase 11: PASS
- Phase 12: p50 10.1s / p95 31.9s / 0 >60s
- Phase 13: 13/13
- sole RED: Phase 8 = 23/24, sprint->attachments composition

Do not rerun unaffected rows/phases.

### Owner fix
Commits:
- 6491f2e6e9fb82bf5cee2d23cba7d0d5213cc2da
- eadd41da7d01040cd7fcd35c62e4e7919423a1a6
- 5710bc99798fb0597ed812cb354e91a61e31a582

Change:
- attachment capabilities now accept canonical sprint_id;
- sprint-scoped candidate collection uses get_sprint_tasks(sprint_id, space);
- optional person constraint is intersected inside sprint membership;
- existing fan-out guard remains;
- no Core/planner/runtime/session-context change.

### P0 — diff/tests
1. Diff from A221R2 QA commit 6a811eece7fde3fb3add86599bb0ae726d20d9c5.
2. Prove only attachment handler/catalog/tests/docs changed.
3. Run:
   - test_agent_core_v4_attachment_sprint_scope.py
   - test_agent_core_v4_task_catalog.py
   - attachment-focused suites
   - planner signature parity
   - relevant V4 registry/plugin suites
4. Zero unexplained failures.

### P1 — blocking sprint->attachments composition
Re-run the exact A221R2 failed case, then >=6 natural forms:
- "вложения в текущем спринте WMB"
- "какие задачи текущего спринта WMB имеют вложения"
- "покажи вложения по задачам WMB-SPRNT-2"
- "есть ли файлы у задач текущего спринта WMB"
- one DMS current-sprint form
- one explicit sprint-id form

Require:
- source-backed sprint resolution first;
- task.search_attachments receives canonical sprint_id;
- candidates come only from get_sprint_tasks for that sprint;
- no broadening to whole product/person corpus;
- exact parity with independent Oracle B.

If current WMB-SPRNT-2 still has no qualifying attachments, require source-proven REAL_EMPTY. If source changed, use current exact source truth.

### P2 — intersection
Test:
- sprint + person + attachments
- sprint + Excel attachments

Require exact intersection within sprint membership.

### P3 — retained canonical attachment smoke
Re-probe canonical rows 3-6 only:
- attachments
- Excel
- PDF
- MSG

Require prior exact behavior/counts or current-source exact parity.
Do not rerun rows 1-2 or 7-54.

### P4 — audit delta
Require:
- 0 local factual reads
- 0 mutations
- 0 tenant-wide scans
- bounded sprint membership for sprint attachment queries
- fan-out guard retained
- no source-unavailable converted to REAL_EMPTY

### Closure
If sprint->attachments is GREEN and retained attachment smoke is clean:
- Phase 8 becomes 24/24 GREEN;
- retain A221R2 Phase 9-13 results;
- update the existing A221 artifacts/report;
- overall functional certification is GREEN.

Verdict exactly one:
- AGENT_CORE_V4_FULL_54_ABC_GREEN_A221R3
- AGENT_CORE_V4_FULL_54_ABC_RED_A221R3

If GREEN, recommend immutable full-functional checkpoint and next owner phase = UI widget/state/lineage remediation.
If RED, preserve retained GREEN progress and STOP.
