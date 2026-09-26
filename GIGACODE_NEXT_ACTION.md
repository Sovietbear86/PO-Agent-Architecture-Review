# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_221R2_RESUME_FROM_ROW49

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT rerun certified rows 1-48 unless the owner fix demonstrably affects them.
Do NOT start Learning Reviewer work.
Commit/push only QA reports and resumable artifacts.

## Prior state
A221R stopped at the next confirmed RED.

Retained certified progress:
- row 10 re-gate = GREEN_SOURCE_CONDITIONAL;
- rows 1-48 = GREEN/resumable;
- row 49 = RED;
- rows 50-54 + Phases 8-13 = NOT_RUN.

A221/A221R progress artifacts remain authoritative.

## Row 49 defect
Canonical requirement:
- Task search by product/space
- live skill: tasks.search
- query class: "покажи задачи по продукту DMS"

A221R root cause:
`AgentCoreV4Runtime._task_search` already contained a bounded space-only source branch:
`search_tasks(project = "<SPACE>")`
but the safety guard made it unreachable unless `unassigned=true`.

Old guard:
- assignee OR sprint_id OR (space AND unassigned)

This caused a valid product-only collection request to be re-scoped by the planner to current sprint or clarification instead of executing the requested full product-space collection.

## Owner fix
Commits:
- `fd922f42679cfc97ceef8e08ae0cff0b9a9a5dcb`
- `81e209be61b12cf7421306382513c56b8f8d7a47`
- `975bf5191562892a799478ae25469a46f3a82bb5`

Important architecture note:
this is a one-line safety-guard correction in Agent Core, not a new entity router or phrase-specific branch.
The already-existing bounded `project = space` execution path is now reachable.
Truly unscoped `task.search({})` remains fail-closed.
No tenant-wide search is introduced.

The third commit only aligns the stale row-10 catalog unit expectation with the already-certified directory-backed release-search contract.

## Phase 0 — owner-diff audit
1. Pull branch, record START_HEAD and clean worktree.
2. Diff from A221R report state.
3. Prove owner production delta is limited to:
   - one generic guard in `agent_core_v4.py`;
   - focused tests.
4. Prove:
   - no phrase/entity literals were introduced;
   - no planner prompt/routing changes;
   - no session-context changes;
   - no adapter/source fallback changes;
   - no tenant-wide path was added.

## Phase 1 — focused tests
Run:
- tests/test_agent_core_v4_task_search_source_status.py
- tests/test_agent_core_v4_task_catalog.py
- tests/test_agent_core_v4_task_search_release_regression.py
- planner signature parity
- relevant V4 suites

Require zero unexplained failures.

## Phase 2 — blocking row 49 re-gate
Fresh sessions.

Run >=5 exact/intended forms:
- "покажи задачи по продукту DMS"
- "все задачи в DMS"
- "список задач пространства DMS"
- "tasks in OLP"
- "покажи задачи по продукту WMB"

Required:
- tasks.search selected or loaded as the product/space collection skill;
- canonical space is resolved/validated when needed;
- terminal task.search call includes `space=<requested space>`;
- no sprint_id silently added;
- no current-sprint narrowing;
- no assignee silently added;
- no unassigned=true silently added;
- source route is bounded by project/space;
- result key set/count exactly matches independent full-space Oracle B;
- no tenant-wide scan;
- no local factual reads;
- no mutation.

For DMS, Oracle B must independently obtain the complete source-backed DMS product collection at the same source moment and compare exact key set/count.

If source supports 432 tasks at the test moment, Agent must return exactly 432; use current source truth, not a hardcoded expected count.

## Phase 3 — negative guard regression
Directly/probe via production-equivalent runtime:
- `task.search({})` => typed clarification/fail-closed;
- invalid space => clarification/fail-closed;
- space + unassigned => exact unassigned product subset;
- space + explicit status through composition => preserve both constraints;
- assignee + space => preserve both constraints;
- sprint + space => preserve both constraints.

No broadening is allowed.

## Phase 4 — retained row 10 quick smoke
Because one stale catalog unit was updated, re-probe only a compact row-10 smoke:
- WMB 24Q1 task search;
- OLP 1.6.0 task search.

Require same A221R GREEN_SOURCE_CONDITIONAL behavior.
Do NOT rerun rows 1-9 or 11-48.

## Phase 5 — resume rows 50-54
After row 49 GREEN:
continue canonical rows:
50 release.forecast
51 po.daily_brief
52 po.status_report
53 po.reminder_draft
54 po.local_task_draft

Use original A221 A/B/C rules.

## Phase 6 — resume Phases 8-13
After 54/54 rows terminal:
- unseen composition benchmark;
- clarification/session benchmark;
- Browser C full-surface pass;
- full source/write audit;
- latency observation;
- retained architecture extras.

## UI hard gate
Report Browser C failures honestly.
Do not mark overall product-ready merely because A/B backend behavior is GREEN.

Project plan after A221R2 remains:
1. widget/state/lineage remediation;
2. slide-derived UI visual design pass;
3. Browser C UX re-gate;
4. PO acceptance;
5. Learning Reviewer 2.0.

## Progress preservation
Continue the same artifacts:
- qa_artifacts/a221_canonical54_manifest.json
- qa_artifacts/a221_matrix_progress.json
- qa_artifacts/a221_source_audit.json
- qa_artifacts/a221_latency.json
- qa_221_browser_c/
- qa_reports/AGENT_CORE_V4_FULL_54_ABC_221.md

Do not create a disconnected second certification matrix.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_FULL_54_ABC_GREEN_A221R2`
- `AGENT_CORE_V4_FULL_54_ABC_RED_A221R2`

If GREEN:
report 54/54 terminal classifications, source-class counts, Browser C results, source audit, latency and live registry count.
Recommendation must be UI/widget lineage remediation next, before design and Learning Reviewer.

If RED:
identify first newly failing row/boundary, persist progress and STOP.

Do not modify code.
