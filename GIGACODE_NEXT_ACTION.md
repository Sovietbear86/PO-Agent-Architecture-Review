# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_193_ATTACHMENT_ORACLE_AND_UI_KEEPALIVE`

## Role lock
GigaCode is **QA/adversarial tester + service operator only** for this assignment.

Do NOT implement, refactor, fix, improve, or rewrite production code, frontend code, plugin code, tests, prompts, adapters, config, or architecture docs. Do not start Wave S. The owner will implement production fixes after this bounded verification.

## Start state
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record `git rev-parse HEAD` as `START_HEAD`.
3. Read:
   - `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_CATALOG_TASK_WAVE_192.md`
   - `V4_DOD_LOCK.md`
   - `V4_54_SKILL_MIGRATION_PLAN.md`
4. Permanent rollback remains `0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`.

## Context from A192
A192 is RED with three already-proven defects:
- `task.search_text` scans the empty local `/api/v1/tasks` corpus instead of live SWTR;
- `task.search_assignee` cannot resolve natural-language person names reliably;
- `task.search_status` cannot execute status-only / space+status queries.

A new manual Browser-C reproduction shows the attachment family is also suspect and A192's `SOURCE_CONDITIONAL` classification for rows #3–6 is not sufficient.

Observed manually in Browser C:
- `Задачи Калачанова с вложениями в пространстве WMB` -> agent returned 0;
- follow-up stating that such tasks do exist -> agent still returned 0;
- `Проверь на наличие вложений задачу WMB-30000` -> task is found, but agent says attachment information is absent.

Static inspection already shows legacy `PortfolioCapabilities.task_search_attachments()` obtains its candidate corpus via `self.a.search_tasks("")` before calling `get_attachment_metadata(task_key)`. A192 proved that the same unscoped `search_tasks("")` path can resolve to the empty local store. A193 must independently prove the live Oracle boundary for attachments and prevent a false REAL_EMPTY classification.

## Mission
Perform a **bounded QA-only attachment-source investigation**, keep the service UI running for manual owner testing, and produce exact evidence needed for the owner fix.

Answer these questions:
1. Does REAL AS21/SWTR expose attachments for `WMB-30000` or another fresh WMB task assigned to `Kalachanov.V.V`?
2. Can attachment metadata be obtained through a direct live/source-backed route even when `task.search_attachments` returns 0?
3. Is the defect the candidate-task corpus (`search_tasks("")` / local store), the attachment metadata route itself, source field mapping, or more than one layer?
4. Should canonical rows #3 `task.search_attachments`, #4 `task.search_excel`, #5 `task.search_pdf`, #6 `task.search_msg` remain `SOURCE_CONDITIONAL`, or are one/more now definitively RED?
5. Can Browser C be left running after QA so the owner can manually test the same live stack?

## Phase 0 — services and operational keepalive
Start/reuse a **fresh live stack** with V4 enabled and REAL AS21/SWTR authoritative:
- Task API on a free localhost port;
- PO Agent backend on a free localhost port;
- frontend/Browser C on a free localhost port.

Rules:
- concurrency 1 for agent QA;
- do not use fake/local source as Oracle;
- do not kill unrelated processes;
- if an existing project process is healthy, it may be reused only after verifying its branch/HEAD/config;
- choose new free ports otherwise;
- keep all three project services running after the assignment finishes unless they crash on their own.

Record in the report and final response:
- frontend URL;
- backend URL;
- Task API URL;
- PID for each process;
- health/status result for each service;
- exact `START_HEAD`.

## Phase 1 — direct REAL Oracle for attachment-bearing tasks
Use live source routes/capabilities, not the agent result itself, to discover attachment truth.

At minimum:
1. Fetch `WMB-30000` from the live source.
2. Query attachment metadata/content-list surface for `WMB-30000` directly.
3. Fetch the live task collection for `Kalachanov.V.V` scoped to WMB using the proven source-backed assignee route and inspect candidates for attachment metadata.
4. If `WMB-30000` truly has no attachments at test time, continue through the assignee WMB collection until either:
   - at least one attachment-bearing task is found, or
   - the live source itself proves attachment metadata is unavailable for the whole tested surface.
5. Record exact task keys and attachment names/types/sizes when the source exposes them.

Do not infer source absence from `task.search_attachments=0`.

## Phase 2 — reproduce canonical attachment skills A/B
Through public `/api/v1/query`, use fresh sessions and execute at minimum:
- `Задачи Калачанова с вложениями в пространстве WMB`
- `Проверь на наличие вложений задачу WMB-30000`
- `Найди задачи с вложениями Excel в WMB`
- `Найди задачи с PDF-вложениями в WMB`
- `Найди задачи с MSG-вложениями в WMB`

Where the current skill contract cannot accept a space/person filter directly, record that separately; do not rewrite the query into a different semantic request merely to make it pass.

For each case capture:
- loaded skill id;
- called capability and arguments;
- source route(s) actually touched;
- completion/status;
- returned keys/attachment metadata;
- exact Oracle B comparison.

Any source-proven attachment omitted by the skill => RED.
Any `REAL_EMPTY` emitted while the direct Oracle contains matching attachments => RED and specifically classify as **false REAL_EMPTY / wrong-source defect**.

## Phase 3 — code-path confirmation
Without modifying code, inspect and cite the exact production path responsible for the result. At minimum trace:
`task.search_attachments` SkillSpec -> plugin binding -> legacy capability -> adapter method(s) -> Task API route(s).

Explicitly determine whether the candidate corpus still uses local `/api/v1/tasks` / SQLite or another non-authoritative fallback.

Also check specialized Excel/PDF/MSG bindings: fixed attachment type is acceptable, but they are RED if they inherit the same wrong candidate corpus.

## Phase 4 — bounded retained checks
Do not re-run the full 20-skill wave. Only confirm that the already-proven A192 defects still reproduce on current HEAD:
- one `task.search_text` live phrase case;
- one natural-language assignee case;
- one space+open/status case.

This is for owner-fix bundling only; no production changes.

## Classification
For rows #3–6 use exactly one each:
- `GREEN_SOURCE_SUPPORTED`
- `SOURCE_CONDITIONAL`
- `RED_FALSE_REAL_EMPTY_WRONG_SOURCE`
- `RED_ATTACHMENT_ROUTE_OR_MAPPING`
- `RED_OTHER` (explain precisely)

`SOURCE_CONDITIONAL` is allowed only if direct REAL Oracle proves the necessary source surface is genuinely unavailable. An empty local corpus or omitted attachment field is not source unavailability.

## Allowed output
Create/commit/push **only**:

`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_ATTACHMENT_ORACLE_193.md`

Do not modify production/frontend/tests/config/plans/plugins.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_ATTACHMENT_ORACLE_CONFIRMED_DEFECT`
- `AGENT_CORE_V4_ATTACHMENT_SOURCE_CONDITIONAL_PROVEN`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

Expected recommendation if a live attachment exists but the skill returns 0:
**Owner must fix the entire Task Wave source boundary together: text search + attachments + natural-language assignee + status search, then run one consolidated QA re-gate before Wave S.**

## STOP / KEEP UI RUNNING
After committing/pushing the QA report:
- **do not stop the three project services**;
- return their URLs, ports, PIDs and health statuses;
- stop and wait for the owner.
