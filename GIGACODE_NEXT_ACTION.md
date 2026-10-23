# GigaCode — CURRENT NEXT ACTION

## A230R2.2-SOURCE-AUDIT — Worklogs by person and date range (READ-ONLY QA)

**GigaCode role is QA/source oracle only. NO production code, tests, runtime, config, frozen Core, or API modifications. No fixes or auto-implementation.** If critical safety or source boundary fails, stop and report. Only a QA report under `po-agent-platform-v2/qa_reports/` may be committed.

### Background
A230R1 C3: «покажи списания Гаранина с 01.10.2026 по сегодня» failed; task.worklogs is per-task, member.worklogs requires space+sprint. We want real person+date worklogs, not synthetic task-search fallback or unbounded N+1 per-task reads. A230R2.1 period regression is independently GREEN; do not modify.

### Read-only evidence required
1. Record TESTED_HEAD, confirm frozen Core six files byte-identical to checkpoint `6fb335d`, flags OFF.
2. Inspect real SWTR/AS21 read-side API contracts and existing Task API adapter capabilities for a **server-filtered** worklog query by stable employee ID and explicit date window, with pagination and permissions. Distinguish author/assignee/worklog owner and creation date vs logged-on date.
3. Read actual handler definitions: task.worklogs/task.time_spent, member.worklogs/member.time_spent/utilization_actual; identify exact required arguments and provenance. No source data invented.
4. Probe only safe, bounded READ operations where authorized. Do **not** scan all tenant tasks or fan out worklog calls across assignee's corpus. Capture source API route/method, request params, response shape (redacted), pagination/limits, evidence whether original worklog events are available, and date filtering semantics. If no safe server-side path, say UNSUPPORTED and specify smallest required API addition; do not implement.
5. Examine one real request for Гаранин, 01.10.2026 → current date, in a local isolated session, with bounded diagnostics. Identify first failed boundary and whether typed clarification/UNSUPPORTED is surfaced rather than task-search filter hints; separate LLM 429/timeout from capability absence.
6. Give owner precise minimally scoped non-Core design to implement: capability ID, typed input/output schemas, normalized person ID, from/to timezone, source endpoint, bounded pagination, source-backed result, 403/404/429/502/timeout handling, and tests. Only recommend supported contract; no speculative rollout.
7. Ensure no credential printing, no mutation, no source writes, no unscoped reads. Remote/multiuser auth ownership remains blocked.

### Verdict/report
Save report `po-agent-platform-v2/qa_reports/A230R2_2_WORKLOG_SOURCE_AUDIT.md` with TESTED_HEAD, proven endpoint availability (YES/NO/UNKNOWN), safe limits, source sample redacted, first failing boundary, recommended implementation seam outside Core, coverage gaps, GREEN for audit completeness only or RED if unsafe. Commit+push **only the report**. This is a source audit, NOT implementation GREEN.

### Short command
Run A230R2.2-SOURCE-AUDIT from GIGACODE_NEXT_ACTION.md. QA and bounded source API inspection only; do not edit application code. Report and stop.
