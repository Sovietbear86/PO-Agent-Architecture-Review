# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_221R_RESUME_FULL_V4_54_ABC_FROM_ROW10

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT restart rows 1-9 unless the owner fix demonstrably affects them.
Do NOT start Learning Reviewer work.
Commit/push only QA reports and resumable artifacts.

## Prior A221 state
A221 verdict:
`AGENT_CORE_V4_FULL_54_ABC_RED_A221`

Certified before STOP:
- rows 1-9 GREEN and frozen/resumable;
- row 10 RED;
- rows 11-54 NOT_RUN.

First failing boundary:
row 10 `task.search_release`.

A221 artifacts are authoritative and must be resumed:
- qa_artifacts/a221_canonical54_manifest.json
- qa_artifacts/a221_matrix_progress.json
- qa_artifacts/a221_source_audit.json
- qa_artifacts/a221_latency.json
- qa_reports/AGENT_CORE_V4_FULL_54_ABC_221.md

## Owner fix
Commits:
- `3347e33df7264a928ea855d18bb892e321f540fb`
- `c18a03d5bd7d494e35adedd5921faf5d4126bd5a`

Scope:
- plugin-only `task_catalog.py`;
- focused regression test;
- no Agent Core/planner/runtime/session-context change.

### Defect closed by design
Old row-10 trajectory:
`task.search_release -> release.resolve`

Problem:
`release.resolve` is task/fix_version-link based. Current AS21 release linkage is unpopulated, so a directory-valid release could never validate and produced a zero-option clarification.

New intended trajectory:
`space.resolve -> release.search(require_single=true) -> task.search_release`

Semantics:
1. release identity comes from authoritative live version directory;
2. task.search_release performs bounded source membership read with canonical release_id + space;
3. if release exists but membership is empty/unpopulated, terminate typed `V4CapabilityUnavailable` / SOURCE_CONDITIONAL;
4. never return 0-task REAL_EMPTY for this source state;
5. never ask user to clarify a release already verified by the version directory.

The new task.search_release handler is plugin-owned and does not use a tenant-wide scan.

## Phase 0 — baseline + checkpoint sanity
1. Pull branch, record START_HEAD, clean worktree.
2. Resolve remote branch:
   `checkpoint/v4-canonical54-green-a220`
   Expected SHA:
   `5c23ac5bd68cbbf41e3eb7d39f64382ab0d7c625`
3. Note: A221 F2 was a local-fetch observation; GitHub remote branch currently exists. Do not classify checkpoint missing without remote branch enumeration/fetch.
4. Diff owner fix from A221 STOP state.
5. Prove zero core/planner/runtime/session-context changes.
6. Run focused test:
   `tests/test_agent_core_v4_task_search_release_regression.py`
7. Run relevant V4 regression suites.

Any generic runtime regression => RED STOP.

## Phase 1 — blocking row 10 re-gate
Fresh sessions.

Run >=5:
- "задачи в релизе 24Q1 в WMB"

Run >=3:
- "покажи задачи в релизе 1.6.0 в OLP"

Run >=3:
- "какие задачи входят в релиз 24Q1 WMB"

Required every run:
- directory-backed release identity is resolved;
- no `release.resolve` dead-end;
- `task.search_release` receives canonical UUID + canonical space;
- bounded release-membership source route only;
- current empty/unpopulated membership => typed SOURCE_CONDITIONAL / v4_capability_unavailable;
- zero-option clarification = 0;
- fabricated REAL_EMPTY = 0;
- generic ERROR = 0;
- tenant-wide task scan = 0;
- mutation = 0.

Oracle B must independently reconfirm:
- WMB 24Q1 release exists in version directory;
- OLP 1.6.0 release exists in version directory;
- authoritative release membership remains unpopulated/empty at the source moment.

If source has evolved, classify from the current source truth instead of forcing SOURCE_CONDITIONAL.

If row 10 is not GREEN_SOURCE_CONDITIONAL (or GREEN_SOURCE_READY if the source evolved and membership is truly populated), verdict RED and STOP.

## Phase 2 — resume matrix, do not restart 1-9
After row 10 GREEN:
- update a221_matrix_progress.json row 10;
- continue canonical rows 11 through 54 using the original A221 rules;
- preserve rows 1-9 exactly unless owner fix can affect them (it should not).

Checkpoint progress after every 9 newly completed rows or at existing group boundaries.

## Phase 3 — Phases 8-13
After all canonical rows 10-54 terminally classified:
resume original A221:
- cross-skill unseen composition;
- clarification/session benchmark;
- Browser C full-surface pass;
- full source/write audit;
- latency observation;
- retained architecture extras.

## UI reminder / hard gate
Do NOT hide Browser C failures behind backend GREEN.

The project plan now explicitly requires after A221:
1. V4 widget/state/lineage remediation;
2. slide-derived UI visual design pass;
3. Browser C UX re-gate;
4. only then PO acceptance and Learning Reviewer 2.0.

For A221R, Browser C still reports the actual current UI state honestly.

## Required final artifacts
Continue using A221 artifact names; do not create a disconnected second matrix:
- qa_artifacts/a221_canonical54_manifest.json
- qa_artifacts/a221_matrix_progress.json
- qa_artifacts/a221_source_audit.json
- qa_artifacts/a221_latency.json
- qa_221_browser_c/
- qa_reports/AGENT_CORE_V4_FULL_54_ABC_221.md

Append re-gate/resume history to the report so row-level provenance is preserved.

## Final verdict
Use exactly one:
- `AGENT_CORE_V4_FULL_54_ABC_GREEN_A221R`
- `AGENT_CORE_V4_FULL_54_ABC_RED_A221R`

If GREEN report:
- 54/54 terminal classifications;
- counts by GREEN_SOURCE_READY / GREEN_SOURCE_FREE / GREEN_SOURCE_CONDITIONAL;
- 0 RED;
- Browser C coverage/failures explicitly enumerated;
- source audit;
- p50/p95 latency;
- live registry count;
- recommendation: UI/widget lineage remediation is next blocking owner phase before Learning Reviewer.

If RED:
- first newly failing row/boundary after resume;
- preserve all completed progress;
- STOP.

Do not modify code.
