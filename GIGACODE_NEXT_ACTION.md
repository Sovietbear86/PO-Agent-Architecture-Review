# GigaCode — CURRENT NEXT ACTION

## A230R3.1-WORKLOG-PERIOD-QA — Independent QA on owner's additive implementation

**STRICT QA ONLY — GigaCode MUST NOT edit application code, tests, Core, MCP, configs, scripts or frontend. No auto-fixes, no source writes, no commits except sanitized QA report.** Do not perform unrelated public deployment Skills QA at this stage.

### Context
Owner has now staged additions on `feat/core8-real-query-hardening-v2`:
- MCP tool `get_work_report_filter` using `POST /rest/api/timesheet/v1/report`;
- Task API `GET /api/v1/swtr-read/work-logs/report`, required `user,from,to`;
- Adapter `get_member_worklogs_period`, capped 20 x 50 pagination;
- plugin `member.worklogs_period`, relative weeks parser and fail-closed data;
- tests `test_swtr_person_worklogs_report.py` / `test_member_worklogs_period.py`.

Frozen Core V4 6/6 unchanged vs `6fb335d`. Expected MCP tool registry increased **48 -> 49** after MCP server restart; 48 on old running process is not proof of new implementation.

### P0 — Provenance & security
1. Fetch exact TESTED_HEAD; compare 6 Core files byte-for-byte with `6fb335d`; no unapproved changes, default flags OFF. Preserve current running services until controlled isolated QA.
2. Inspect new source/tool schemas; mandatory single employee canonical externalId, inclusive logged-on range, space/unit optional, page bounds, authorization, no empty tenant-wide filter and no per-task scans. No credential printing. Confirm no new personal data exposed in public changes.
3. Validate actual AS21 contract POST report request filter/users/spaces/units/range/page and response pageNumber/hasNext/content. Verify time.duration shape = MILLIS or report mismatch as RED, no invented conversion.
4. If new MCP tool or Task API argument aliases cannot be invoked as documented, report first failing boundary and STOP, do not self-fix.

### P1 — Targeted tests and negative paths
- Run syntax/import validation for 2 new tests and modified Python modules; execute new pytest files. Run existing SWTR facade and member worklog plugin tests. No test modifications.
- Test input: explicit dates, «2 недели», «за последние 2 недели», «с 21.09.2026 по сегодня», 400 for missing/invalid user/date, >366 days, future dates, missing page continuation, author mismatch, date mismatch, missing duration, 403/429/502/503, pagination max reached. Fail source-closed not 0 hours.
- Verify one employee's source-dated writes are distinct from tasks currently assigned to that employee.
- Execute one bounded REAL AS21 oracle read (author Garanin, 2026-10-01 to test-day or another authorized real account) via the POST filter. Compare ID, author, logged-on dates, total hours, count and fully traversed pages with MCP→Task API→adapter→plugin. Do not hardcode the historic 14 entries. Use isolated session.
- Test standalone conversational query «Покажи списания Гаранина за последние 2 недели» and scoped «в DMS с 01.10.2026 по сегодня». Confirm planner chooses `member.worklogs_period` (not task.search_created), resolves person identity and finishes COMPLETED with evidence, no generic task-filter clarification. If not, RED and identify planner/skill seam without modifying frozen Core.
- Test a true source-backed zero: complete=true only. Negative zero from source outage must produce typed failure, not facts.

### P2 — Full regression
- Full V4 test suite + Task API suite + frontend build; run existing 7 human queries in A230R3 for routing/continuation comparisons. Mark unrelated preexisting UI raw JSON and free-text clarification design gaps separate, never GREEN this feature based on partial completion.
- Record runtime services actually running (not pre-existing processes), exact MCP tools count, latency and measured oracle parity.
- Verify no regression to previous A230R2.1 week task-creation grammar or sprint-only member.worklogs.

### Report and stop
Return exact TESTED_HEAD, test counts, source A/B verdict, planner trajectory verdict, 6/6 Core hashes, redacted fail traces, first failing boundary, GREEN/RED/NOT VERIFIED and safe non-Core fix recommendations. Report to chat only or sanitized report file if requested; **no production changes, no merge, no Public synchronization**.
