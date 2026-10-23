# A230R2.2 — Owner implementation design: person/date worklogs

Status: A230R3.1 owner implementation STAGED (MCP + Task API + adapter + V4 plugin + unit tests), NOT YET QA-GREEN. GigaCode is independent QA only. No public rollout before A/B regression.

Source evidence: `po-agent-platform-v2/qa_reports/A230R2_2_WORKLOG_SOURCE_AUDIT.md` (report commit `e16b925` on 2026-10-23). The source has a fast server-side filtered endpoint, which is not exposed by existing agent paths.

## Verified backend
- Raw AS21: `POST /rest/api/timesheet/v1/report`.
- Body: `{filter:{users:[externalId], range:{from:"YYYY-MM-DD",to:"YYYY-MM-DD"}, spaces?:[], units?:[]},page:{page:0,size:50}}`.
- Response: `{content:[WorkLogInfo],pageNumber,pageSize,hasNext}`. Filtering uses **worklog author** (`user.externalId`) and logged-on `date`, not task assignee or task creation time.
- Probed `Garanin.R.V`, 2026-10-01..2026-10-23: 14 worklogs, HTTP 200, ~0.1 s; these counts are historical evidence, **never** hardcode into acceptance tests.
- If range missing AS21 silently uses roughly last 30 days: NEVER omit date range.
- Empty filter streams tenant-wide: NEVER send it.
- Current MCP/task-api/agent only expose per-task reports or space+sprint member aggregates; person+range must be new, additive path.

## Smallest architecture-preserving implementation (owner, not GigaCode)
1. MCP SWTR read-only wrapper `get_work_report_filter`. Validate nonempty explicit users (single resolved ID), valid inclusive range, bounded page <= 100 and no mutation. Auth using existing MCP credentials.
2. Task API: `GET /api/v1/swtr-read/work-logs/report` with required `user,from,to`, optional `space,unit`, bounded `page,size`; reuse identity canonicalization, capture `complete`/pagination and source REAL_AS21. 400 on invalid filters/date, 403 on denied source, typed unavailable or 502 on source/pagination failure.
3. Agent plugin: additive `member.worklogs_period`, args `member_login,from,to[,space,unit]`, map identity via member.resolve. Return `{member_login,from,to,worklog_count,total_hours,entries,complete,source:"REAL_AS21",attribution:"worklog_author_external_id",date_semantics:"logged_on_date_not_created"}`. All entry totals must match underlying time fields and page completeness. No per-task fanout or unscoped scans.
4. Skill/planner procedure (not frozen Core): person+worklogs+explicit dates -> new capability, not `task.search_created` or sprint-only `member.worklogs`. If no dates, ask for range; if source unsupported, typed explicit capability/source error.
5. UI: concise person/date report, count, summed hours, entries with source provenance, no internal envelope dump (C5 separately open).

## Mandatory regression
- Typed schema; inclusive from/to; timezone interpretation; correct author != assignee, zero entries vs source failure, 400/401/403/429/502, pagination `hasNext`, capped size/pages, mismatch sums, incomplete=false closed, no default 30-day window, no empty tenant-wide filter.
- Live A/B: independently fetch filtered AS21 oracle at test execution time; person Garanin 2026-10-01 to test day; compare IDs/dates/author/units/count/hours, not fixed historic count.
- Full V4 + task-api SWTR + frontend, browser; core frozen 6/6 vs 6fb335d, default flags OFF, no mutation.
- GigaCode QA only **after owner implementation**; QA reports must name exact TESTED_HEAD. Do not mark implementation GREEN because source audit was GREEN.

## Open blockers / independent tracks
- C4 fast ping; C5 meta envelope rendering; C2 bare period continuation.
- Session/auth ownership binding remains required for remote multiuser.

## A230R3.1 staged owner changes (2026-10-24)
- `mcp-swtr/mcp_server.py`: bounded `get_work_report_filter` via server-filtered AS21 report API; from/to and author mandatory; max page 99, size 100.
- `task-api/app/routers/swtr_read.py`: `GET /api/v1/swtr-read/work-logs/report?user=...&from=...&to=...`, page-filtered provenance/author/date/duration guard. Explicit missing hasNext => 502.
- `po-agent-platform-v2/src/po_agent/adapters/task_api.py`: bounded complete pagination (20 pages x 50 max), fail closed rather than 0 if incomplete.
- `po-agent-platform-v2/src/po_agent/harness/v4_plugins/time_accounting_period.py`: additive `member.worklogs_period`; independent worklog date grammar including last N weeks; no Core changes.
- New targeted tests: `task-api/tests/test_swtr_person_worklogs_report.py`, `po-agent-platform-v2/tests/test_member_worklogs_period.py`.
- **Not yet verified**: source schema parity, planner selecting the new plugin, resolver with live user, exact date semantics, full regression, 49 MCP tools vs earlier 48. Test independently before any merge or propagation to Public. No changes to PR #3 Public deploy skills.
