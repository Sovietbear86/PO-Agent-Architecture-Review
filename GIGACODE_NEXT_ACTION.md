# GigaCode — CURRENT NEXT ACTION

## A230R3.30-P35-OVERVIEW-CROSS-SPACE-SOURCE-AUDIT

### Purpose
Independent QA/discovery of the real running Overview dashboard (not a request to rewrite it). Check whether **any of its portfolio metrics, daily brief, owner attention queue, task counts or readiness** silently filter to OLP or otherwise omit authorized DMS/WMB/CRPV/STS spaces. Previous P3.1 A230R3.29 was **P31_E2E_SOURCE_CONDITIONAL**, NOT a code RED: DMS-SPRNT-5 finished with 26/26, 6 post-end closure events, no verified active READY forecast; retain that verdict and do not restart forecast QA.

### Hard rules
GigaCode is independent tester only. READ ONLY: no code/config/test/spec writes, no commit/push, no Core V4 changes, no Public changes, no AS21 writes, no tenant-wide scan. Do not stop/restart the user's servers (8004/8241/5175/3000). Use separate ports if running an isolated stack. Preserve dirty/untracked files. Fetch branch `feat/core8-real-query-hardening-v2` from `Sovietbear86/PO-Agent-Architecture-Review`, record tested HEAD local=remote and verified Core V4 6/6 vs `6fb335d`. Capture screenshots with no personal data/secrets in the report.

### Gate 0: Real UI/source map
Identify which actual router/page implementation serves the user's screenshot of «Обзор» with four tiles `Активно`, `Завершено`, `Заблокировано`, `Готовность портфеля`, `Очередь внимания PO`, `Daily Brief`, `Задачи по пространствам`. Do not mistakenly audit an old/dead OverviewPage. Trace exact React component -> useSnapshotHarness/query -> skill/capability -> source adapter -> AS21 MCP endpoint -> configured products/team roster. Report file:line pointers. Document any stale snapshot indicator versus actual current source.

### Gate 1: Configuration and filters
- Compare authorized spaces using actual `task-api/config/products.yaml` and `team_members.yaml` (or the actual `PRODUCTS_CONFIG_PATH` / `TEAM_CONFIG_PATH` effective config). Do not assume fixed five-space list without verifying config.
- Search all executed Overview / portfolio / daily brief / attention queue / per-space aggregation paths and query planner arguments for hardcoded `OLP`, `space=OLP`, default `OLP`, implicit first-space-only logic, config-based allowed spaces dropped, case-mismatch, space-specific page limits, per-assignee roster filter, dedup and stale snapshot cache keys.
- Distinguish **intended** scope (tasks assigned to configured members in configured spaces) from all tasks of each product, and from tenant-wide tasks. An OLP-only result can be valid for explicitly OLP-filtered user query, but not the default portfolio Overview.

### Gate 2: Bounded independent REAL AS21 oracle
Using *authorized*, *per-space and per-assignee bounded* source reads only (no tenant-wide scan), verify numeric tile aggregations and per-space table for OLP and at least DMS plus another configured space when access allows. At most 5 configured spaces and <=100 tasks per bounded page; obey existing source budgets. Log page counts, completeness, dedup keys, task IDs anonymized/hashed, statusType semantics and as_of. Verify:
- `active + completed` vs eligible task scope and status exclusions,
- blocked count and source statuses,
- portfolio readiness numerator/denominator,
- attention queue contains risks from non-OLP spaces if present,
- daily brief sprint mapping includes other configured spaces,
- OLP query results cannot contaminate cache for DMS/other products.
Where source is incomplete/outage, report typed SOURCE_UNAVAILABLE/INCOMPLETE instead of treating missing as zeros.
Check **cross-space ownership**: the same task assigned to multiple team members or returned by multiple queries must be counted once by canonical identity.

### Gate 3: Browser A/B/C and regression
Use isolated browser if feasible. Verify the actual Overview and click Refresh: no hidden OLP selection, all configured space headers shown, numeric tile and per-space sources match the independent oracle or are explicitly stale/incomplete. Do not mislabel prior cached snapshot as fresh. Inspect network response and UI for raw planner JSON or source PII. Cross-check `Спринты` forecast UI remains safe N/A when source is insufficient. Run only relevant targeted tests plus frozen Core hash and frontend compile; if production code unchanged and previous full regression GREEN, do not repeat expensive unrelated full suites. Classify baseline vs new defect separately. Note available status/health latency, source retries and failed updates.

### Output — one report, STOP
Write ONE untracked QA artifact `po-agent-platform-v2/qa_reports/P35_OVERVIEW_CROSS_SPACE_AUDIT.md`:
1. Exact `TESTED_HEAD`, executed UI source path and config scope.
2. Per-widget evidence matrix `widget | true scope | space filter | authoritative oracle | count parity | stale/complete`.
3. Verdict `P35_OVERVIEW_GREEN` (proven cross-space), `P35_OVERVIEW_RED` (specific verified OLP-only or misaggregation), or `P35_OVERVIEW_SOURCE_CONDITIONAL` (unverifiable source, no fabricated pass).
4. The **single first failing boundary** with minimal owner-only fix if RED. No edits by QA.

**Do not turn this into a new indefinite series of isolated checks. One bounded report and STOP.**
