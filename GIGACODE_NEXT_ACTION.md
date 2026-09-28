# GigaCode — Current Action

## ACTIVE: Assignment 226 — final UI polish + actual utilization + team aging + page snapshots

Role: QA/adversarial tester only. Do NOT modify production/frontend/backend/plugin/test/config code.

## Frozen baseline

A225 verdict:
`AGENT_CORE_V4_UI_VISUAL_DESIGN_GREEN_A225`

Checkpoint:
`checkpoint/v4-ui-visual-design-green-a225@09bcbd22d87b478396970d0ddf89cbf6d531d421`

A226 is an owner feedback batch after visual acceptance. Preserve all A224R2/A225 business/state/design semantics unless explicitly changed below.

## Owner changes under test

Expected changes after A225:
- shared `pageSnapshot.tsx` session-snapshot/manual-refresh layer;
- snapshot/manual refresh wired to all six main pages;
- remaining light Daily Brief / V4 structured-result surfaces removed;
- Team page switched from estimate-based `team.capacity` to existing certified `team.utilization_actual`;
- `team.utilization_actual` now exposes per-member worklog_count;
- top-right chips now only OLAP + DataMarts;
- `task.aging` extended with explicit team_scope using configured team logins;
- Quality Aging query now explicitly asks for team-scoped aging;
- focused regressions for actual-utilization row counts and team-scoped aging.

No Agent Core/planner/runtime architecture changes.

## P0 — diff / build / architecture

1. Pull current branch, record START_HEAD, clean worktree.
2. Diff from A225 checkpoint.
3. Prove:
   - 0 Agent Core/planner/runtime/session architecture changes;
   - backend semantic deltas are limited to plugin-level task aging + actual-utilization output;
   - frontend changes are presentation/snapshot wiring;
   - no AS21 mutation capability added.
4. Run:
   - V4 plugin/registry regressions;
   - `test_agent_core_v4_time_accounting_aggregate.py`;
   - `test_agent_core_v4_team_aging.py`;
   - task catalog regressions;
   - `tsc --noEmit`;
   - `vite build`.
5. Zero unexplained failures.

Any core architecture drift => RED STOP.

## P1 — dark structured surfaces

Browser C:
- Overview Daily Brief with a markdown table;
- PO Agent answer with V4 structured result;
- competency recommendation table.

Require:
- no white/light legacy table or V4ResultPanel surfaces;
- table wrapper/header/body all use dark glass theme;
- primary text remains readable;
- state labels/evidence remain readable;
- no raw markdown regression.

Capture screenshots.

## P2 — Team actual utilization

Use source-ready Team space, preferably DMS first.

Independent Oracle B:
1. Resolve authoritative current sprint and period.
2. Read bounded worklogs for sprint task membership.
3. Aggregate worklogs by worklog-author external_id.
4. Apply owner capacity policy for sprint period.
5. Compute per-member:
   - actual_hours;
   - worklog_count;
   - available_capacity_hours;
   - utilization_percent;
   - over_capacity.

Require UI:
- underlying skill = `team.utilization_actual`, NOT `team.capacity`;
- exact per-member parity with Oracle B;
- numerator source = REAL AS21 worklogs;
- denominator source = OWNER_POLICY;
- 40h/week policy remains visible;
- estimate absence does not incorrectly produce SOURCE_UNAVAILABLE;
- true worklog/source failure still fails closed.

Important:
`team.capacity` may remain SOURCE_CONDITIONAL because it requires task estimates. This is NOT a defect; the UI now intentionally uses actual utilization instead.

Test DMS + one additional source-ready space.

## P3 — top-right products

Require exactly two chips/buttons:
- OLAP
- DataMarts

Require:
- DTMS absent;
- route navigation unaffected;
- no functional request fired by merely rendering the chips.

## P4 — Team-scoped Aging queue

Quality page, WMB and DMS, threshold 7 and 15.

Independent Oracle B:
1. Read configured member logins from `task-api/config/team_members.yaml`.
2. For each login perform bounded REAL AS21 assignee+space read.
3. Deduplicate by canonical task key.
4. Keep only source-created-at rows that are active/open and age >= threshold.
5. Sort by age descending.

Require:
- agent trajectory for Quality Aging calls `task.aging` with team_scope=true;
- no whole-space corpus scan;
- exact task-key/count/age parity with Oracle B;
- tasks assigned to people outside configured team are excluded;
- duplicate task keys are counted once;
- if one member read is unavailable, capability fails closed rather than presenting a partial exact queue;
- REAL_EMPTY only when complete team-member reads prove empty.

## P5 — page snapshot policy

Test every main page:
- Overview
- Tasks
- Sprints
- Releases
- Team
- Quality

Fresh browser session:
1. Clear only `po-page-snapshot:v1:*` sessionStorage keys.
2. Open page first time.
3. Prove live agent/AS21 queries occur and snapshot timestamp appears.
4. Navigate away and back without pressing Refresh.
5. Prove page restores the snapshot and makes NO new agent query/source reads for the cached context.

Manual Refresh:
1. Press page-level `Обновить`.
2. Old data must remain visible while refresh is in progress.
3. Only the current page's required query set re-runs.
4. Successful refresh atomically updates visible data + timestamp + sessionStorage snapshot.

Refresh failure:
- force safe source/backend failure after a valid snapshot exists;
- old snapshot must remain visible;
- UI shows `Не удалось обновить · данные на HH:MM`;
- snapshot must not be erased/replaced by null;
- retry after recovery succeeds.

No background polling/timer refresh is allowed.

## P6 — snapshot context isolation

Require separate cache identity for:
- Team DMS vs Team OLP;
- Quality WMB-102 vs another task;
- Quality Aging WMB:7 vs DMS:15;
- Sprint id A vs sprint id B;
- Release id A vs release id B;
- Tasks search mode/value A vs B.

Switching context:
- cached value for one context must never leak into another;
- first unseen context loads live;
- returning to a previously cached context restores its own snapshot without a live request.

Storage policy:
- AS21 snapshots use `sessionStorage` only;
- `localStorage` remains reserved for LOCAL tasks;
- new browser session must reload live source data.

## P7 — retained functional/design smoke

Retain:
- A225 six distinct page backgrounds;
- 1440 + 480 no document overflow;
- Overview 107-row internal Attention scroll;
- Tasks AS21/local status filters + local CRUD;
- Sprint throughput/risk + predictability fail-closed;
- Releases honest source limitation;
- Quality WMB-102 = current source-backed quality semantics;
- competency recommendation;
- Evidence/Trace/Skill lineage.

## P8 — audit

Require:
- 0 AS21 mutations;
- 0 local factual fallback reads;
- 0 tenant-wide scans;
- no new background source traffic after page snapshots are populated;
- manual refresh traffic is page-bounded;
- localStorage writes only LOCAL tasks;
- sessionStorage page snapshots are the only new persistence.

## Verdict

Use exactly one:
- `AGENT_CORE_V4_UI_POLISH_SNAPSHOT_GREEN_A226`
- `AGENT_CORE_V4_UI_POLISH_SNAPSHOT_RED_A226`

If GREEN:
- recommend `checkpoint/v4-ui-polish-snapshot-green-a226`;
- next owner phase = PO final Browser UX acceptance / release-hardening continuation;
- Learning Reviewer still waits for owner acceptance.

If RED:
- identify first confirmed boundary;
- preserve screenshot + source/network/storage evidence;
- STOP.

Do not modify code.
