# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_219_BATCH5_PO_WORKFLOW_GATE

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT start release.forecast / Batch 6.
Commit/push only the QA report.

## Frozen baseline
A218 = GREEN.
Rollback checkpoint:
`checkpoint/v4-self-introspection-green-a218`

A218 inventory truth:
- live registry before Batch 5 = 62 skills / 11 plugins;
- canonical product denominator = 54 requirements;
- covered before Batch 5 = 48/54;
- missing = 6.

Do NOT require live registry count == 54.
The acceptance goal is canonical 54 coverage, not artificial registry-count equality.

## Owner Batch 5
Commits:
- `b11a61f8137487b4521b6ca3633c0c367b4927d8`
- `b241b9434e8d3ed6830cab2a3cf51d183d37fa22`
- `b88f3222ce2d316c7920ee56a3df4a40b4a7fdc3`

Five plugin-only canonical skills:
1. po.attention_queue
2. po.daily_brief
3. po.status_report
4. po.reminder_draft
5. po.local_task_draft

No Agent Core/planner/runtime/session-context edits.

## Architectural change vs legacy POAssistantCapabilities
Legacy PO portfolio methods used `search_tasks("")` tenant-wide.
V4 MUST NOT preserve that unsafe retrieval shape.

Batch 5 intentionally uses:
approved product spaces -> bounded current-sprint lookup -> bounded sprint membership.

Draft skills remain read-only:
- reminder draft requires an explicit task key;
- local task draft may be user-input-only or grounded by one point-read task;
- zero external writes.

## Phase 0 — architecture invariant
1. Pull branch, record START_HEAD, clean worktree.
2. Diff from checkpoint/v4-self-introspection-green-a218.
3. Prove only plugin/tests/docs changed.
4. Zero Agent Core/planner/runtime/session-context changes.
5. Registry discovers exactly one new Batch 5 plugin and all five skills exactly once.
6. dummy-55 invariant GREEN.

## Phase 1 — tests
Run:
- tests/test_agent_core_v4_batch5_po.py
- tests/test_agent_core_v4_agent_help.py
- tests/test_agent_core_v4_plugin_registry.py
- tests/test_agent_core_v4_planner_signature_parity.py
- full tests/test_agent_core_v4*.py + tests/test_v4*.py

Zero unexplained failures.

## Phase 2 — independent REAL AS21 bounded oracle
For each approved space CRPV/DMS/OLP/STS/WMB:
1. independently obtain current sprint via the source-backed route;
2. if present, independently obtain complete bounded sprint membership;
3. classify completed/open/blocked/unassigned and task age/priority using certified predicates.

No tenant-wide task query may be used as Oracle or production source.

Record per-space:
- current sprint id/state;
- exact task-key set;
- counts;
- blocked keys;
- unassigned keys;
- score inputs for attention queue.

## Phase 3 — po.attention_queue
Run >=5 natural forms:
- "очередь внимания PO"
- "что требует моего внимания как PO"
- "покажи рисковые задачи по текущим спринтам"
- two equivalent variants.

Require exact parity to independent bounded Oracle:
score:
- blocked +50
- critical/urgent active +35
- age >=14 active +20
- else age >=7 active +10
- unassigned active +10
- completed excluded.

Require deterministic descending score then task key.
This is TASK operational priority, never employee scoring.

## Phase 4 — po.daily_brief
Run >=5 natural forms:
- "дай ежедневную сводку PO"
- "что у нас сегодня по продуктам"
- "daily PO brief"
- two variants.

Require exact bounded current-sprint parity:
- active
- blocked
- unassigned
- completed
- attention_count
- top_attention top 5

Spaces with no current sprint must remain explicit source states, not fabricated zero task sets.

## Phase 5 — po.status_report
Run >=5 natural forms.

Require:
- exact total/completed/active/blocked over source-backed current-sprint sets;
- exact by_product rows;
- NO_CURRENT_SPRINT / CURRENT_SPRINT_WITHOUT_MEMBERSHIP preserved with null metrics;
- no historical/full-tenant claim.

## Phase 6 — po.reminder_draft
Cases:
1. explicit real task key DMS-380;
2. another real task with assignee;
3. missing task key;
4. non-existent task key.

Require:
- explicit key -> one source point read only;
- source-backed task facts in draft;
- draft_created true only for found task;
- write_performed=false always;
- requires_approval_for_send=true;
- missing key -> typed clarification;
- no auto-selection from portfolio/tenant tasks;
- zero mutation calls.

## Phase 7 — po.local_task_draft
Cases:
1. source task key DMS-380;
2. user subject only;
3. source task + custom subject;
4. no subject and no source task;
5. invalid source task.

Require:
- point read only when key supplied;
- user-only draft causes zero AS21 calls;
- no external write;
- requires approval metadata;
- no invented AS21 facts.

## Phase 8 — Browser C
Real UI for all five:
- attention queue
- daily brief
- status report
- reminder draft
- local task draft

Require no generic V4 ERROR.
Draft UI must clearly state no write/send occurred.

## Phase 9 — retained regression
At minimum:
- agent.help full catalog
- ping
- DMS-380 lookup
- current sprint DMS
- Semavin time accounting
- portfolio.overview
- standalone release identity
- release progress/health typed SOURCE_CONDITIONAL
- dummy-55

## Phase 10 — source/write audit
Require:
- local factual task reads = 0;
- tenant-wide/unscoped task scans = 0;
- mutations = 0;
- PO aggregation source calls are bounded current-sprint/sprint-membership only;
- draft source calls are bounded point reads only.

## Phase 11 — inventory reconciliation
Fresh registry enumeration after Batch 5:
Expected live count = 67 if no unrelated drift.
Expected canonical coverage = 53/54.
Expected remaining canonical missing skill = exactly:
- release.forecast

Do NOT mark RED solely because live count is 67 rather than 54.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_BATCH5_PO_GREEN_A219`
- `AGENT_CORE_V4_BATCH5_PO_RED_A219`

Also report:
- exact live skill/plugin count;
- canonical coverage x/54;
- exact canonical missing list.

If GREEN:
recommend immutable Batch 5 checkpoint and next owner step = isolated Batch 6 release.forecast source-contract implementation.

If RED:
identify first failing boundary and STOP.

Do not modify code.
