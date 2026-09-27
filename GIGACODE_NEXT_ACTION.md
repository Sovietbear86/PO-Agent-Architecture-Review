# GigaCode — Current Action

## ACTIVE: Assignment 224R2 — team-scoped overview + task status filters + attention scrolling

Role: QA/adversarial tester only. Do NOT modify code.

### Important scope correction
The previous A224/A224R full-space counting requirement is SUPERSEDED.

Do NOT try to count every task in WMB/DMS/OLP/CRPV/STS.

The product requirement is now:
**"Задачи по пространствам" = tasks assigned to configured team members, grouped by space.**

Canonical team identities come from:
`task-api/config/team_members.yaml`

The source path must reuse the already-certified REAL AS21 assignee search used by the Tasks page.

### Owner changes under test
- po.status_report now loads configured team logins and performs bounded assignee reads;
- returned tasks are grouped by approved space and deduplicated by task key;
- total / active / completed / blocked are computed from those team-assigned tasks;
- no full-space task corpus scan is used;
- one failed assignee read => SOURCE_PARTIAL, not an exact-looking partial total;
- Overview attention queue renders the complete queue inside the scroll container; no dataset slice to first 10;
- Tasks page has separate AS21-status and local-status filters.

No Agent Core/planner/runtime/session change.

## P0 — build / architecture
1. Pull branch and record HEAD.
2. Diff from A224R report state.
3. Prove po.status_report no longer calls get_space_task_count or full-space search for this widget.
4. Prove all task reads are person-scoped assignee reads using configured logins.
5. Run relevant V4/batch5 tests, tsc --noEmit and vite build.
6. Zero unexplained failures and zero AS21 mutations.

## P1 — team-scoped task summary exactness
Independent Oracle B:
1. Read all canonical logins from team_members.yaml.
2. For every login, use the certified REAL AS21 assignee route.
3. Union tasks by canonical key.
4. Group by WMB/DMS/OLP/CRPV/STS.
5. Compute total / active / completed / blocked.

Compare exact values with:
`po.status_report.data.by_space_tasks`

Require:
- exact parity for all spaces when all member reads are source-ready;
- Kalachanov.V.V tasks are included wherever source says they belong;
- no unrelated unassigned/other-team space corpus enters the totals;
- no duplicate task counted twice;
- no whole-space task-query/count route used for this widget.

Failure safety:
- force one configured member source read unavailable;
- summary becomes SOURCE_PARTIAL and UI does not present its numeric values as exact;
- all-member failure => capability fail-closed.

## P2 — Overview Browser C
Block title remains "Задачи по пространствам".

Require:
- explanatory note says counts are tasks assigned to configured team members;
- cards show exact total / active / completed / blocked for source-ready team summary;
- CRPV/STS may legitimately be zero only if the team-login Oracle B proves zero;
- no previous giant full-space totals (150k/460k) appear.

## P3 — PO Attention scrolling
Use a source state with >10 attention items.

Require:
- all queue rows are present in DOM/data, not only first 10;
- panel has bounded visible height and internal vertical scrolling;
- scrolling reaches item 11 and the final item;
- label states total count / "прокрутите список";
- Daily Brief remains comparable in visible height;
- downstream Overview blocks remain reachable without page-height explosion.

## P4 — Tasks AS21 status filter
Use a non-empty AS21 result set with >=2 statuses.

Require:
- "Статус AS21" selector lists source statuses present in current result;
- ALL shows all returned AS21 tasks;
- selecting a status filters cards exactly, case-insensitive;
- changing display status does not trigger an AS21 mutation;
- existing explicit backend "Статус" search mode still works and is not broken.

## P5 — local task status filter
Create local tasks in TODO / IN_PROGRESS / BLOCKED / DONE.

Require:
- "Статус локальных" ALL shows all;
- each status filter shows exact local subset;
- changing a local task status immediately moves it between filtered views;
- reload persistence remains GREEN;
- delete remains GREEN;
- zero AS21 writes.

## P6 — resume deferred A224 usability checks
Continue the not-yet-certified checks:
- local task CRUD full flow;
- Sprint predictability honest source limitation;
- Releases honest sparse/source-conditional behavior;
- Team space selector + automatic 40h/week policy;
- Quality Aging space+threshold;
- compact retained Quality/Sprint/chat/competency smoke.

Do NOT re-run abandoned full-space count route as a product requirement.

## P7 — responsive layout
Desktop + 480px:
- Overview internal scroll usable;
- no harmful horizontal overflow;
- Tasks filter controls remain usable and wrap cleanly.

## P8 — audit
Require:
- 0 AS21 mutations;
- 0 local factual fallback;
- 0 tenant-wide scans;
- 0 whole-space corpus scans for Overview task-by-space summary;
- assignee reads only for configured team logins;
- localStorage writes only for LOCAL tasks.

## Verdict
Exactly one:
- `AGENT_CORE_V4_UI_USABILITY_GREEN_A224R2`
- `AGENT_CORE_V4_UI_USABILITY_RED_A224R2`

If GREEN:
- recommend checkpoint/v4-ui-usability-green-a224r2;
- next owner phase = visual design system + slide-derived page backgrounds;
- do NOT start Learning Reviewer yet.

If RED:
- preserve first failing source/backend/UI evidence and STOP.

Do not modify code.
