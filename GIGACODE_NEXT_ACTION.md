# GigaCode — CURRENT NEXT ACTION

## A230R3.4-UI-ENVELOPE-QA — independent frontend rendering gate

**QA ONLY.** No edits to product code, tests, prompts, Core, Task API, MCP, config or Git. No auto fixes, commits, PRs or merges. Fetch current origin/feat/core8-real-query-hardening-v2 and verify LOCAL_HEAD == REMOTE_HEAD == TESTED_HEAD. If dirty, preserve data and STOP instead of reset.

### Previous gate
A230R3.3-R3 **GREEN** on tested head `62002fb`, 6/6 frozen Core unchanged, V4 suite 326 passed, Task API 69 passed, frontend built. A transient LLM planner FAILED remained independently open; B lifetime sprint question now returns safe typed scope clarification rather than false 147.5h all-time. True all-time totals are **not implemented**.

### Owner A230R3.4 edit
- Frontend-only `po-agent-platform-v2/frontend/src/components/V4ResultPanel.tsx` now treats `data.results` as **internal planner step envelopes** rather than a business table. Rows only come from explicit allowlisted collections in top-level data or in `results[i].data`: tasks, sprints, matches, queue, timeline, durations, risks, risk_queue, dependencies, members, worklogs, entries.
- Label rows from allowlisted scalar fields only; never `JSON.stringify` arbitrary planner envelopes or display capability arguments, tool names or traces in the user view. A task collection should display compact key/title for entries.
- Remove visible `widget: ...`, `kind: ...` labels; translate `Evidence` caption to `Источники`.
- API / Task API / Core / MCP untouched. No public sync yet.

### P0 static review
1. Capture TESTED_HEAD and compare 6/6 frozen Core hashes against `6fb335d`, no unexpected diffs. Confirm TypeScript compile and no accidental field omissions.
2. Look for any other frontend rendering paths outputting `data.results` or JSON.stringify of V4 planner envelopes. Report scope and any remaining leak; do not modify.
3. Verify source and evidence type contracts; do not accidentally drop valid task/sprint tables, attachments, timeline, member rows, empty states or task metadata. Verify when `results` contains several steps, only user-appropriate business data appears (and whether multiple relevant business collections are preserved). If user data would be silently lost, RED with exact case.
4. Check no mock/fake fallback and no new exposed internal sensitive data.

### P1 execution
1. `cd po-agent-platform-v2/frontend && npm run build` and `npm run lint` if available; classify pre-existing lint failures.
2. In isolated UI/browser, replay source-backed V4 results for task.search (Agataeva 2 tasks or authorized equivalent), worklogs period, sprint aggregate, empty result, partial/error states, and planner-only results. Capture browser DOM/text checks (no literal `{"step"`, `capability_id`, `arguments`, `widget:`, `kind:` in normal result panel). Confirm 2 task keys/titles render as business rows; no duplicate raw envelope.
3. UI action 'Источники' remains available and evidence count accurate without raw AS21 payload dumps.
4. Full V4 regression and Task API smoke; Core frozen. Zero AS21 mutations.

### P2 report
Return concise GREEN/RED per render fixture, build/lint, exact TESTED_HEAD, Core 6/6, no raw envelope exposure, no business rows lost; exact first failing boundary and smallest frontend-only fix if RED. **No code changes.** STOP. Do not run Public GigaCode Skills QA yet.

### Short command
Execute A230R3.4-UI-ENVELOPE-QA from GIGACODE_NEXT_ACTION.md. QA only, use fresh HEAD, frontend browser/DOM and regression, do not modify anything; report and STOP.
