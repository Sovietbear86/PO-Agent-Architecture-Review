# GigaCode — NEXT ACTION

## A230R3.42 — P3.2 Releases analytics dashboard, UI/UX owner implementation (ONE bounded patch)

### Confirmed user starting point (10.11.2026)
User's local PO Agent now has **live source**: `SBERPROJECT_FINAL_CONNECT_GREEN`, OLP 69 versions (20 on confirmed first page), DMS 16; TLS enabled via approved PEM and opt-in same-user CLI bridge. User screenshot: poor layout: tiny version rows in narrow left column, a large empty right area; missing analytical value. Existing `ReleasesPage` is just a source catalog; Sprint page has useful KPI cards. Core V4 frozen. Owner's last live commits may be **LOCAL ONLY** because git push failed due to GitHub auth; do not force-reset or overwrite them with stale origin. Before edits compare actual LOCAL HEAD with upstream; preserve user runtime `task-api/.env`, certs and running services.

### Target: make Releases a useful source-grounded dashboard without inventing tasks
Implement **one cohesive frontend-centric patch** based on the actual source fields. Never infer release-task membership from names or AS21 task space. Distinguish metadata KPIs now from task KPIs later.

#### UI layout, like Sprints
1. Top compact filter bar: product OLP/DMS, searchable version (ID/number), lifecycle status selector, refresh, source-as-of timestamp/status. All controls usable on mobile/small viewport. No giant empty area.
2. First row 4 KPI cards, **computed from the full verified version collection or clearly labeled loaded subset**:
   - Total versions (source `total`).
   - Released versions (`workflowStatus.code=RELEASED` or documented aliases).
   - Active/in implementation (only explicit states `INSTALLATION` etc.; do not invent mappings).
   - Upcoming / at risk: counts **only if** complete verified dates/status make them derivable; otherwise use `Не определено` and explanation. Better substitute "Без даты выпуска" for entirely source-grounded data.
3. Main full-width dashboard grid (responsive, 2 columns on wide screens):
   - Release timeline/table: version, SberProject ID, lifecycle badge, begin/end/release date, owner, overdue indicator derived from explicit planned end and unfinished status (date semantics confirmed), sortable.
   - Lifecycle status distribution by product. Use lightweight CSS bars; no new chart dependency.
   - Upcoming/recent releases ordered by verified dates, with no fake schedule.
4. Selecting a version opens an informative **full-width details panel** (or side panel consuming reasonable width): key dates, lifecycle, owner, relative deadline if provable, source/provenance. A separate disabled/unknown block `Задачи / прогресс / блокировки / зависимости: связь SberProject ↔ AS21 ещё не подтверждена`. Do not display 0 tasks, 0 blocked, percentages, fictitious progress or risk scores. Mark date gaps 'нет данных' and leave raw statuses readable.
5. End state with empty, partial, auth/TLS error and stale-refresh all distinct; preserve prior successful source snapshot visibly marked as stale (never relabel as fresh). Pagination remains honest: prior source CLI only supported page 1 -> never synthesize page 2. If full collection cannot be fetched, count cards based on confirmed total only for totals, and label status distribution `из N загруженных`.

### Evidence gates and completion
- FIRST read `frontend/src/recovery/Pages.tsx`, existing `SprintPage` cards/styles, `frontend/src/api/client.ts`, live JSON response contract and report `P32_SBERPROJECT_FINAL_CONNECT_E2E.md` (if present); confirm which status/date/owner fields are returned and whether date meaning is planned vs actual. No broad external scan.
- Implement small modular components/derivations outside Core V4. Responsive layout/consistent typography; remove the tiny left-column presentation. Prefer existing UI patterns and CSS. Avoid change to Task API unless absolutely necessary for reliable provenance.
- One local fixture/unit run for state arithmetic, no falsified AS21 fields; one frontend build + small browser smoke with real local OLP/DMS if running; 6/6 core integrity. No endless regression, no user services restart unless authorized and required.
- Single coherent commit (only frontend/docs/tests + any necessary route fixes), update evolution plan. Output `po-agent-platform-v2/qa_reports/P32_RELEASES_DASHBOARD_UI_QA.md`, verdict `RELEASES_DASHBOARD_UI_GREEN` only after actual browser checks, else precise typed partial and STOP.
- Do NOT push until GitHub authorization restored; do not claim remote synced. Preserve `task-api/.env`, PEM, keychain and unrelated dirty state.

### FOLLOW-ON (not in this task)
Release task membership + metrics similar to sprint throughput/WIP/forecast require a **verified release→task identity bridge** from SberProject/AS21 data owner. Record discovery question `task.plan.accountingObject → ProductVersion` (display ID vs internal ID); then scope bounded task collection before implementing progress, completed, remaining, blockers, forecast. Must never fill cards with fabricated 0%/100%.

**One implementation + one narrow QA, report, STOP.**
