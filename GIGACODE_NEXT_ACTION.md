# GigaCode — Current Action

## ACTIVE: Assignment 227 — PO acceptance corrections

Role: QA/adversarial tester only. Do NOT modify production/frontend/backend/plugin/test/config code.

A226R3 was GREEN, but PO browser review reopened sign-off with three UX/reliability issues:
1. Overview refresh can false-fail because the previous 65s client timeout races slow source reads.
2. Tasks should be one Google-like natural-language search field, not mode buttons/selectors.
3. Quality page refresh and Aging refresh must be isolated; Aging must actually populate from REAL AS21.

## Owner changes under test

- snapshot timeout increased from 65s to 120s;
- Tasks page now has one natural-language input only;
- no Assignee/Status/Sprint/Release mode buttons;
- no product-space selector;
- no automatic query on first Tasks open;
- raw submitted text is sent directly to V4 Agent Core;
- task collections render as cards; non-task results render the grounded answer;
- local-task status filter remains only inside Local Tasks;
- Quality uses separate taskRefreshNonce and agingRefreshNonce;
- page-level Quality refresh updates quality/missing/acceptance only;
- Aging Refresh updates Aging only.

## P0 — build/diff

1. Pull current branch; clean worktree; record START_HEAD.
2. Prove no Agent Core/planner/runtime architecture drift.
3. Run:
   - tsc --noEmit;
   - vite build;
   - focused V4 task search/composition tests;
   - aging/team-scoped task tests;
   - snapshot/result-state tests.
4. Any unexplained build/test regression => RED STOP.

## P1 — Overview refresh reliability

Browser C:
1. Load populated Overview.
2. Press Обновить.
3. Preserve old snapshot while requests run.
4. Under normal source latency (including 60–80s), refresh must complete successfully rather than false-timeout at 65s.
5. Button must return from Обновляем… to Обновить.
6. Timestamp must advance on successful refresh.
7. Inject genuine failure/timeout >120s: stale data remains, error state appears, retry remains available.
8. Away/back after success = 0 unwanted POSTs.

If normal source read completes before 120s but UI still reports failure => RED STOP.

## P2 — Tasks UI surface

Require exactly one search field plus:
- Найти
- + Локальная задача

Require absent:
- Исполнитель mode button
- Статус mode button
- Спринт mode button
- Релиз mode button
- product-space selector
- attachment/Excel/PDF/MSG buttons

On first open with no prior submitted query:
- no automatic agent POST;
- result area says to enter a natural-language query.

Search input and last submitted query persist on away/back.
Page-level Refresh repeats the exact last submitted natural-language query.

## P3 — Natural-language task/work search composition

Run all four browser cases and independently inspect trajectory/source reads:

A. `Открытые задачи Калачанова с вложениями в пространстве WMB`
- preserve person + open-status + attachments + WMB constraints;
- use compositional V4 skills/capabilities;
- no tenant-wide scan;
- exact source parity for returned task keys where source supports the intersection.

B. `Задачи Семавина по рискам`
- resolve Semavin from authoritative team identity;
- use risk/task analysis skills, not a phrase-specific UI router;
- no invented risk rows.

C. `Задачи в работе в сентябрьском спринте по DMS`
- resolve the relevant DMS sprint from source;
- preserve in-progress status constraint;
- exact source parity.

D. `Спринты в DMS`
- this is intentionally non-task output;
- page must render a grounded rich answer / sprint result rather than fake empty task cards.

For ambiguous natural-language queries:
- clarification is acceptable;
- tenant-wide fallback scan is not.

## P4 — task result rendering/persistence

1. For a task-collection query, cards show real key/title/status/assignee and are clickable into Task Details.
2. For a non-task skill result, render grounded answer, not "tasks not found".
3. Navigate away/back: 0 new POST and exact result retained.
4. Modify input without pressing Найти: displayed submitted result must not silently change.
5. Press Refresh: one re-run of the submitted query.

## P5 — Quality page refresh isolation

Use DMS-380 or another source-ready task.

Top page Обновить:
- only quality/missing/acceptance refresh;
- Aging query must NOT re-fire;
- old quality snapshot remains while loading;
- successful source response before 120s must not show false refresh failure.

Task Проверить with same task:
- re-runs task quality group only;
- Aging remains untouched.

## P6 — Aging queue source load

Use:
- DMS > 15 days
- DMS > 7 days

Require:
- Aging own button triggers only Aging query;
- team-scoped bounded assignee reads;
- exact key/count parity vs independent REAL AS21 oracle;
- rows render with key/title/assignee/status/age_days;
- same criteria + Refresh performs a live re-read;
- no page-quality fanout;
- source-proven empty is allowed only when oracle proves empty;
- SOURCE_UNAVAILABLE/CONDITIONAL must not render as zero.

## P7 — retained regression

Recheck:
- LOCAL-NNNN CRUD + deadline/tags/priority/edit/delete;
- Platform V / OLAP + DataMarts;
- Sprint DMS-SPRNT-3 still source-exact;
- Releases remain honest typed source limitation;
- Team utilization remains source-backed;
- six backgrounds + 1440/480 no overflow;
- 0 local factual fallback;
- 0 unauthorized mutations;
- 0 tenant-wide scans.

## Verdict

Exactly one:
- `AGENT_CORE_V4_PO_ACCEPTANCE_GREEN_A227`
- `AGENT_CORE_V4_PO_ACCEPTANCE_RED_A227`

If GREEN:
- recommend checkpoint `checkpoint/v4-po-acceptance-green-a227`;
- next owner phase = release hardening/security/restart/latency/rollback rehearsal;
- Learning Reviewer still not started unless owner explicitly opens it.

If RED:
- preserve first failing evidence and STOP.

Do not modify code.
