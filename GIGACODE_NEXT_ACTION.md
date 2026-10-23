# GigaCode — CURRENT NEXT ACTION

## A230R3.2-CONTINUATION-QA — independent QA of free-text clarification continuation

**STRICT QA ONLY.** No source/test/config/Core/UI edits, no auto-fix, no commits except a sanitized QA report after testing. Do not start Public deployment skills QA. No modifications to frozen Core V4 (6 files).

### Owner change
- `po-agent-platform-v2/src/po_agent/api/v1/__init__.py`: bounded continuation in API seam, not Core. If same session has a pending time/date clarification and next free-text turn is ONLY a date interval/relative N-day/N-week reply, preserve original query, pending execution observations and completion goals even without an explicit `clarification_id`.
- "Что именно нужно уточнить?" must return the *pending concrete question*, without consuming pending context or invoking generic task.search.
- New unrelated full query must clear stale pending continuation. Explicit option-click with `clarification_id` retains strict option validation. Expiration remains fail-closed; session isolation remains mandatory.
- Tests: `po-agent-platform-v2/tests/test_api_free_text_clarification.py`.
- Change checkpoint: owner patch `48a8557` (fetch exact branch HEAD; do not assume this remains current).

### Gate P0 — code and provenance
- Verify exact TESTED_HEAD and frozen Core V4 six files byte-identical to `6fb335d`.
- Validate strict free-text parser: Russian dates, "за последние 2 недели", short meta question; no arbitrary query concatenation; option click, TTL, cross-session separation, no authority bypass.
- Confirm no secrets or source information disclosed by added API response and that raw continuation state stays server-side.
- Running environment may have older process; use isolated controlled QA or re-launch ONLY isolated process, not destroy unrelated service.

### Gate P1 — targeted tests and live conversational cases
- Run new tests plus pre-existing clarification/continuation suites; verify all pass; if RED stop without modifying tests.
- A/B per same session: «Покажи списания Иванова» → typed period clarification → «с 01.10.2026 по сегодня» → correct person+date skill, not task.search; repeat with «за последние 2 недели».
- Pending period clarification → «Что именно нужно уточнить?» → concrete period question, then «за 2 недели» completes.
- Option-click path stays GREEN, illegal option rejected.
- New unrelated query after pending («Покажи задачи Ивановой в DMS») does not inherit previous person intent.
- Different session must not inherit pending state; expired pending must not silently execute.
- If initial request is auto-fulfilled by current date defaults instead of clarification, verify pending continuation via another legitimate query with missing date. Never fabricate a pending status.
- When no new request matches bounded parser, report as design limit, not invented GREEN.

### Gate P2 — comprehensive regression
- Full V4 suite, Task API SWTR suite, frontend build; independent source check to REAL AS21 for one authorized person/date continuation. Validate no new source writes, no unscoped reads, no 5xx.
- Report latency separately from correctness and note prior UI raw JSON as **still open**.
- Check exact API schema, especially `_prepare_query` date regex matching and option-validation branch.

### Deliverable
A chat-only report with exact HEAD, test counts, source A/B, scenario matrix, first failing boundary, RED/GREEN verdict and Core 6/6 hashes. Do not commit unless separately asked; STOP after report. No code modifications.

### Short command
Run A230R3.2-CONTINUATION-QA from this file, tests + bounded REAL AS21 live continuation, no code edits, stop/report.
