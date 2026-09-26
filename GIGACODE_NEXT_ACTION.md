# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_219R_BATCH5_PO_REGATE

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT start Batch 6 / release.forecast.
Commit/push only the QA report.

## Frozen baseline
A218 = GREEN.
A219 = RED only on D-A219-1.
Everything else from A219 is retained GREEN unless the owner fix regresses it.

Owner fix commits:
- `51b2fd3438dce69ce4c3beeb3c5cce6764353feb`
- `7be95ad22343ddf48ae4da7997e911863c4c9849`

The fix is plugin-only + focused test only.
No Agent Core/planner/runtime/session-context changes.

## Defect to close
A219 D-A219-1:
`po.local_task_draft` + invalid source task key caused the planner to detour to `task.lookup`, which was not loaded, then exhaust the step budget and return `v4_runtime_failure`.

The intended architecture is:
user task key -> directly call po.local_task_draft -> capability owns one bounded get_task point read -> found => draft; not found => typed draft_created=false terminal.

No separate task.lookup is required or allowed for this skill.

## Phase 0 — fix-scope audit
1. Pull branch and record START_HEAD.
2. Diff from A219 report commit `6d408073e494305ec1e6ee73f6afa34e77856e39`.
3. Prove only:
   - wave_batch5_po.py
   - focused Batch 5 test
   - docs/QA assignment
   changed.
4. Zero Agent Core/planner/runtime/session-context edits.
5. Registry count remains 67 skills / 12 plugins before any Batch 6 work.

## Phase 1 — focused tests
Run:
- tests/test_agent_core_v4_batch5_po.py
- tests/test_agent_core_v4_plugin_registry.py
- tests/test_agent_core_v4_planner_signature_parity.py

Then full:
- tests/test_agent_core_v4*.py
- tests/test_v4*.py

Zero unexplained failures.

## Phase 2 — direct invalid-key regression (blocking)
Use fresh sessions.

Run at least 8 times total across >=4 natural-language forms equivalent to:
1. "создай локальный черновик задачи на основе DMS-999999"
2. "подготовь local task draft по DMS-999999"
3. "сделай черновик follow-up задачи из DMS-999999"
4. "локальная задача на базе DMS-999999"

Required EVERY run:
- loaded goal is po.local_task_draft;
- NO task.lookup call;
- po.local_task_draft called directly with task_key=DMS-999999;
- exactly one bounded point read GET /swtr-read/tasks/DMS-999999;
- source 404 maps safely to task=None;
- terminal is typed, not generic failure;
- draft_created=false;
- write_performed=false;
- zero mutation;
- no v4_runtime_failure;
- no step-budget exhaustion.

Any single recurrence of the old task.lookup detour => RED.

## Phase 3 — valid-key retained regression
Fresh sessions, >=4 runs:
- DMS-380
- DMS-434
- one valid source+custom subject case

Require:
- direct po.local_task_draft trajectory;
- one bounded point read per source-key draft;
- draft_created=true;
- source=REAL_AS21;
- write_performed=false;
- requires_approval_for_external_write=true.

## Phase 4 — user-only draft retained
Run >=3 natural forms with subject only and no source task.

Require:
- po.local_task_draft direct;
- zero AS21 calls;
- source=USER_INPUT_ONLY;
- draft_created=true;
- write_performed=false.

## Phase 5 — clarification retained
Run no-subject/no-task-key shape.

Require:
- typed NEEDS_CLARIFICATION;
- zero source calls;
- no generic error.

## Phase 6 — compact retained Batch 5 smoke
Re-run at least one representative browser/API case each:
- po.attention_queue
- po.daily_brief
- po.status_report
- po.reminder_draft

Require A219 oracle parity retained and no tenant-wide scans.

## Phase 7 — source/write audit
Require:
- tenant-wide/unscoped task scans = 0;
- local factual reads = 0;
- mutations = 0;
- draft calls = bounded point reads only;
- user-only drafts = zero source calls.

## Phase 8 — inventory
Require unchanged:
- live registry = 67 skills / 12 plugins;
- canonical coverage = 53/54;
- missing canonical list = exactly [release.forecast].

## Verdict
Use exactly one:
- `AGENT_CORE_V4_BATCH5_PO_GREEN_A219R`
- `AGENT_CORE_V4_BATCH5_PO_RED_A219R`

If GREEN:
- recommend immutable Batch 5 checkpoint;
- next owner action = isolated Batch 6 release.forecast source-contract work.

If RED:
- identify first failing boundary;
- STOP.

Do not modify code.
