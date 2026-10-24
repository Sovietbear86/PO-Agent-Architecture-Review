# GigaCode — CURRENT NEXT ACTION

## A230R3.3-SPRINT-WORKLOG-SEMANTICS-QA — independent QA, NO FIXES

**STRICT QA ONLY.** GigaCode may test/read source and REAL AS21 with approved narrowly scoped reads, but MUST NOT change production, tests, Core, config, prompts, frontend, MCP or task data. No commit/merge; report in chat and STOP. Defer Public GigaCode Skills QA and UI raw JSON remediation.

### Owner change on feat/core8-real-query-hardening-v2
1. `po-agent-platform-v2/src/po_agent/harness/v4_plugins/time_accounting_member.py` — sprint-specific answers now disclose sprint calendar start/finish, explicit exclusion of outside-sprint dates, and structured `time_basis=logged_on_within_sprint_dates`, `task_basis=sprint_task_membership`, `outside_period_included=false`. Aggregation algorithm intentionally unchanged.
2. `po-agent-platform-v2/src/po_agent/harness/v4_plugins/time_accounting_period.py` — person/date skill now also accepts `сегодня`, `вчера`, `за неделю`, `последняя неделя`, `за месяц`, `этот месяц` to match existing API free-text clarification acceptance. Fixed definitions: yesterday one previous Moscow day; last week rolling 7 calendar days inclusive, "за месяц" rolling 30 days, "этот месяц" first day of current calendar month through today.
3. Targeted tests updated in `po-agent-platform-v2/tests/test_member_worklogs_period.py` and added `po-agent-platform-v2/tests/test_member_sprint_scope_explanation.py`.
4. Frozen Core V4 6/6 must remain byte-identical to checkpoint `6fb335d`. No changes to Public repo.

### P0 — Review
- Fetch exact TESTED_HEAD (owner implementation landed after A230R3.2 GREEN, latest planned checkpoint `e862bb8`).
- Verify Core six hashes, no source/route changes, no unscoped reads, no secret/PII introduced.
- Confirm the sprint-specific member.time_spent/member.worklogs result shape preserves prior required fields and adds only explanatory metadata; no unsupported claim of lifetime task totals. Check `member.utilization_actual` logic untouched.
- Validate period interpretation in `Europe/Moscow`, inclusive boundaries, month boundary, leap-day, >366-day rejection and each word form. Date parser and API clarification MUST agree; unsupported word forms => specific clarification, not generic task filters.

### P1 — Regression and source A/B
- Run 2 updated/new test files, preexisting time accounting, 10 continuation tests + applicable API clarifications, full V4 tests, Task API SWTR suite and frontend build.
- Validate REAL AS21 sprint fixture DMS-SPRNT-5: membership 34 tasks, accurate author and sprint boundaries. The known zero was *logged within sprint dates* and not proof of lifetime zero; use bounded independent source read and date-match. Distinguish author worklogs from current task assignee.
- Explicitly test two **different** questions:
  (A) «Сколько часов Гаранин списал в период спринта DMS-SPRNT-5 по его задачам?»
  (B) «Сколько всего часов было списано по задачам DMS-SPRNT-5 за всё время?»
  A may be answerable by existing member sprint capability but B must NOT silently reuse A's zero; B requires an independent all-date, bounded sprint-task collection with a verified answer or typed unsupported explanation.
- Verify trailing zero and evidence provenance; AS21 outage, missing time unit and incomplete pages must never turn into factual zero.
- Test person/date continuation «за месяц», «вчера», «сегодня», «этот месяц» with independent scoped source A/B.
- Ensure agent chooses correct skill and that no new warning promotes a misleading zero.

### P2 — deliverable
Return chat-only test results, TESTED_HEAD, exact counts, source A/B, Core hashes 6/6, semantics A vs B, date parser matrix and GREEN/RED. At first RED identify smallest non-Core fix boundary; do NOT implement it. Mark pre-existing UI raw-envelope JSON and other planner/LLM design limits as separately OPEN, not part of A230R3.3.

### Short command
Run A230R3.3-SPRINT-WORKLOG-SEMANTICS-QA from GIGACODE_NEXT_ACTION.md. Independent tests + bounded REAL AS21 A/B, Core 6/6; no code edits. Return report and STOP.
