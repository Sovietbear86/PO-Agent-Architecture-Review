# GigaCode — Current Action

## ACTIVE: Assignment 226R — timestamp plumbing + final UX re-gate

Role: QA/adversarial tester only. Do NOT modify production/frontend/backend/plugin/test/config code.

## Prior verdict

A226:
`AGENT_CORE_V4_UI_POLISH_SNAPSHOT_RED_A226`

First confirmed boundary:
`RED_SOURCE_TIMESTAMP_PLUMBING`

Cause:
- team-scoped task.aging correctly used bounded assignee reads;
- live assignee route did not request/surface source created_at;
- task.aging therefore correctly failed closed.

## Owner remediation under test

### P4 source fix
Task API assignee route now:
- requests created_at, createdAt, updated_at, updatedAt, deadline, dueDate from REAL AS21;
- surfaces canonical created_at / updated_at / deadline;
- preserves source timestamps through the production adapter;
- has a timestamp regression test.

Commits:
- 6f5a9b220a9c604ecde64495b6f8d94d7b23d4bb
- 154de24bc41090728ec3f10e12931086c005e991
- cba8824869a5ff720decb390119aaf94e82b4f4a

### Consolidated PO UX fixes
Also under test:
- persisted Tasks search context;
- explicit Text / Attachments / Excel / PDF / MSG task search modes;
- richer local-task priority/tags/deadline UX;
- persisted Quality task + Aging criteria;
- single refresh control on Sprint/Release entity toolbar with last-update date+time;
- WORKS -> Platform V;
- Daily Brief richness restored;
- existing page snapshot semantics preserved.

## P0 — build / diff

1. Pull branch, clean worktree, record START_HEAD.
2. Diff from A226 report commit.
3. Prove:
   - no Agent Core/planner/runtime architecture changes;
   - task-api semantic change is timestamp plumbing only;
   - plugin semantics unchanged except already-approved team aging;
   - frontend changes are UX/session-state/presentation only.
4. Run:
   - task-api canonical/assignee/timestamp tests;
   - team-aging tests;
   - time-accounting tests;
   - V4 registry/task catalog regressions;
   - tsc --noEmit;
   - vite build.
5. Zero unexplained failures.

## P1 — re-gate A226 P4 first

### Team-scoped Aging exactness
WMB threshold 7 and DMS threshold 15.

Independent Oracle B:
1. Read configured team logins from team_members.yaml.
2. For each login call the REAL assignee route with selected space.
3. Require returned rows to carry source created_at.
4. Deduplicate task keys.
5. Keep active/open tasks whose source-created age >= threshold.
6. Sort age descending.

Require production:
- task.aging(team_scope=true) completes source-backed;
- exact task-key/count/age_days parity with Oracle B;
- no whole-space scan;
- no fabricated timestamp proxy;
- adapter marks _canonical_created_at_from_source=true;
- any truly missing member/source read still fails closed.

If this phase RED, STOP.

## P2 — dark structured surfaces (deferred A226 P1)

Browser C:
- Overview Daily Brief;
- PO Agent V4 structured result;
- competency recommendation table.

Require no white/light legacy surfaces, readable dark-glass table/body/header, readable Evidence/Trace/Skill.

## P3 — Tasks search behavior + persisted criteria

### Text search
Use exact scenario:
`БП 2027`

Select Text and press Найти.

Require:
- UI query is explicitly title+description oriented;
- production routes to the correct text-search capability;
- returned keys exactly match independent Agent/API/Oracle search for the same text;
- description matches are included, not title-only.

### Attachment modes
Run at least one bounded source-ready case for:
- Вложения
- Excel
- PDF
- MSG

Require route to attachment-capable skills and no fake empty result. If the source contract cannot support a broad attachment search, typed SOURCE_UNAVAILABLE is acceptable; silent zero is not.

### Find vs Refresh state
1. Select a mode + value and press Найти.
2. Navigate away/back.
3. Require mode, typed value, submitted value, status filters and result snapshot preserved.
4. Press page-level Обновить.
5. Require the last submitted criteria to run again without replacing them with defaults.
6. Changing the input without pressing Найти must NOT silently change the displayed result context.

## P4 — local task UX

Create local task with:
- title;
- description;
- owner;
- priority = Критичный;
- tags = Управленческие задачи + Поручения;
- deadline;
- status TODO.

Require list/card shows:
- Russian priority label;
- both tags;
- deadline;
- owner/status.

Require persistence after reload, status edit, deletion, old-schema migration and 0 AS21 writes.

## P5 — Quality persisted interaction semantics

### Task check
1. Change task key.
2. Press Проверить.
3. Navigate away/back.
4. Require task input + submitted task + result snapshot restored.

### Aging
1. Select space + threshold.
2. Press Aging Обновить.
3. Navigate away/back.
4. Require selected space + threshold + submitted Aging snapshot restored.
5. Re-press Aging Обновить and prove same persisted criteria are re-read from source.

The page-level manual snapshot refresh may remain, but it must not overwrite these explicit control semantics.

## P6 — Sprint / Release single refresh control

For Sprint and Releases:
- exactly one visible Обновить action for the entity;
- no duplicate header-level Обновить beside "Спросить PO Agent";
- entity toolbar shows `Последнее обновление: DD.MM.YYYY HH:MM`;
- if input unchanged, Обновить re-runs current submitted entity;
- if input changed, Обновить submits the new entity and loads/caches it;
- navigation away/back restores input/submitted context and snapshot;
- old snapshot remains visible while refresh runs.

## P7 — brand + Daily Brief

### Brand
Sidebar brand must show:
`Platform V`
and must not show `WORKS`.

### Daily Brief
Require source-backed Daily Brief shows:
- summary text;
- active;
- completed;
- blocked;
- unassigned;
- attention_count;
- top attention task rows;
- current product/sprint breakdown.

It may remain inside internal scroll. Do NOT accept regression back to the minimal 3-line version.

## P8 — snapshot policy + isolation (deferred A226 P5/P6)

Complete the original A226 snapshot tests on all six pages:
- first unseen context => live load;
- navigate away/back => no new source read;
- manual refresh => page-bounded re-read;
- failed refresh => stale snapshot preserved + error timestamp;
- no background polling.

Context isolation:
- Tasks query A/B;
- Sprint A/B;
- Release A/B;
- Team DMS/OLP;
- Quality task A/B;
- Quality Aging space/threshold A/B.

AS21 snapshots=sessionStorage only.
LOCAL tasks=localStorage only.

## P9 — retained business/design smoke + audit

Retain:
- team.utilization_actual exact parity;
- only OLAP + DataMarts chips;
- six page backgrounds;
- 1440 + 480 no document overflow;
- Overview full Attention scroll;
- Sprint metrics/risk;
- Releases honest source limitation;
- Quality WMB-102 semantics;
- competency recommendation.

Audit:
- 0 AS21 mutations;
- 0 local factual fallback;
- 0 tenant-wide scans;
- no extra source traffic from cached page revisit;
- manual refresh traffic bounded to current page/context.

## Verdict

Exactly one:
- `AGENT_CORE_V4_UI_POLISH_SNAPSHOT_GREEN_A226R`
- `AGENT_CORE_V4_UI_POLISH_SNAPSHOT_RED_A226R`

If GREEN:
- recommend `checkpoint/v4-ui-polish-snapshot-green-a226r`;
- next owner phase = final PO visual acceptance + release hardening;
- Learning Reviewer still waits for owner acceptance.

If RED:
- preserve first failing source/backend/UI/network/storage evidence;
- STOP.

Do not modify code.


### A226R owner addendum — local task editing / numbering

Owner feedback added during A226R:
- local task creation/edit drawer must visibly expose a native date picker for deadline;
- saved deadline must appear in the local-task list;
- previously created local tasks must be clickable and reopen the same drawer in edit mode;
- editing must allow title/description/owner/priority/status/tags/deadline changes and persist them;
- local tasks must use a stable user-facing sequential number №1, №2, №3...;
- technical LOCAL-* id remains separate secondary metadata and must not visually merge with title/description;
- existing old-schema localStorage rows without number/deadline must migrate safely;
- deletion must not renumber existing tasks or reuse an older task number; the next new task uses max(existing number)+1.

Commits:
- 14927a7e23ce2a69d7e34d0c73e21ebe24f06a0b
- b55e4b642758c6c670cc3eb39bff1c447e250a15

A226R P4 must additionally prove:
1. create task №N with deadline using visible date picker;
2. deadline is rendered in list as a readable date;
3. click task row -> edit drawer opens with all saved fields prefilled;
4. edit title/tags/priority/deadline -> save -> list and localStorage update;
5. reload -> edits persist;
6. create second task -> №N+1;
7. delete first task -> remaining number stays unchanged;
8. create another -> next number is max+1, not reused;
9. technical LOCAL-* id is visually separate from the user-facing number and title;
10. zero AS21 writes.
