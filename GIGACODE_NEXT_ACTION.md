# GigaCode — CURRENT NEXT ACTION

## A230R3.5-INTEGRATED-AB-REGRESSION — full independent A/B QA of A230R3.1–R3.4

**STRICTLY QA ONLY.** GigaCode does not fix or modify product code, Core, tests, MCP, Task API, UI, plugin configs, prompts, or AS21 data. No commits, merges, pushes, branch rewrite, force operations. Results in chat and a sanitized local QA report only, if writable; do not stage/commit it. Never leak tokens, private user/task metadata or internal URLs. Stop at first new RED with first failing boundary. Existing local dirty files (including prior QA report) must remain intact.

### Baseline
- A230R3.1 person/date worklogs: previous independent GREEN, bounded filter author+logged-on date, 49 MCP tools, fail-closed pagination, exact REAL AS21 parity, frozen Core.
- A230R3.2 free-text clarification: previous GREEN, original intent+member retained across date-only follow-up without clarification_id, typed "Что именно нужно уточнить?", session isolation.
- A230R3.3 sprint semantics: R3 independent GREEN, calendar-only 147.5h NOT represented as historical total, explicit lifetime intent gets typed unsupported clarification (actual all-date sprint-total capability not implemented); planner LLM reliability remains separate.
- A230R3.4 frontend: R2 independent GREEN on TESTED_HEAD `be7f5e5`; 12 ranked candidates rendered, task lists and sources work, planner JSON not shown, 326 V4 tests, 69 Task API tests, frontend build GREEN; `Pages.tsx` QualityPage raw JSON is a **separate pre-existing open issue**.
- Next milestones: only after this A/B gate GREEN, owner may synchronize sanitized Public and then re-gate deployment/health-check skills. GigaCode does not do those changes in this task.

### Gate 0 — revision and secure execution
1. `git fetch origin`; record exact remote HEAD for `feat/core8-real-query-hardening-v2`; prove `LOCAL_HEAD == REMOTE_HEAD == TESTED_HEAD`. If mismatch/dirty prevents QA, STOP and report; don't reset/stash unsafely. Record exact branch, flags/defaults OFF, agent/task-api/MCP/UI versions, service ports; test against actual running revision or isolated services, never claim live HEAD from only a source checkout.
2. Check **six Core V4 files byte-identical to checkpoint `6fb335d`**; no regression in security/session auth/ownership. Test no state mutation and no unscoped / tenant-wide AS21 reads. Do not run live MCP write tools.
3. Control workload: limited number of bounded requests; no unrestricted full-tasks queries or bulk staff scans; backoff/stop on repeated 429/5xx instead of load. User-specific values and source outputs remain sanitized.

### Gate 1 — functional A/B independent REAL AS21
For each case, compare (A) **PO Agent end-to-end** vs (B) **independent bounded direct AS21/MCP or task-api oracle**. Verify actual task IDs/counts/dates/worklog author externalId/total hours and provenance, but report only sanitized aggregates. A and B must match exactly for the same snapshot/time range; don't hardcode prior dynamic counts.
1. Member worklogs: named individual, explicit date range, rolling "за последние 2 недели", "вчера", "за месяц", and "этот месяц"; include with/without space and person resolution; check logged-on date not task creation, author not task assignee, full pagination and `complete=true`.
2. Date clarification: "Покажи списания [authorized employee]" -> period clarification -> "с 01.10.2026 по сегодня" or "за 2 недели" without clarification_id; "Что именно нужно уточнить?" returns concrete pending period question; new unrelated request must not inherit pending intent; cross-session data isolation. Note today is local date of actual execution, not a frozen 2026-10-24.
3. Sprint calendar vs lifetime: DMS-SPRNT-5 (or valid authorized sprint). Test individual and team hours within exact sprint date bounds; independently collect bounded authorized logs and prove zeros/completeness; check sprint task membership can drift. Lifetime ("за всё время по задачам спринта") MUST NOT be answered using calendar-only hours; typed unsupported clarification is acceptable because all-date sprint-total capability is not implemented. No fabricated lifetime figure.
4. Tasks: member tasks in current sprint, multiple members, active/open statuses, task types, space, simple combined filters; compare authoritatively with AS21 oracle. Ensure task-creation "за последнюю неделю / за последние 2 недели" grammar either works or is **explicitly OPEN** if pre-existing; no silent zero or wrong date dimensions.
5. Worklog failure cases: missing/expired token, denied space, network unavailable, malformed/missing duration, missing pagination continuation, 429/502. Should fail closed as typed error, not factual zero; use safe fakes for negative/error injection and no real secret sharing.
6. REAL AS21 oracle sources: prove no fake/local fallback; exact source proof or NOT VERIFIED. Compare bounded results, include evidence counts.

### Gate 2 — Web UI & user-visible content
1. Fresh browser / DOM tests: `task.search` task rows (keys/titles), sprints, member worklogs, `team.competency_match` matches, `team.assignee_recommendation` candidates, empty lists, error/partial statuses; count rows vs returned business collection.
2. Never render raw planner `data.results` envelopes or internal `step/capability_id/arguments/widget:/kind:`; sources count and accordions accurate; avoid loss of `data.candidates` and other known business arrays. Verify one meaningful business row in source gives one UI row (subject to documented bounded display caps).
3. Isolate pre-existing `Pages.tsx` QualityPage JSON leak; don't mark it solved. Report exact severity and whether it must become separate next task.
4. Basic UI states: no infinite spinner, no stale session bleed or mixed replies. No public AS21 payload dump.

### Gate 3 — full regression and release decision
- Execute V4 full suites, Task API SWTR, new A230R3 tests, frontend build, security-scoped tests. Record exact passed/failed/skip/error and compare with baseline; never describe `full po-agent` as all-GREEN if pre-existing failures remain.
- Run controlled recent complex-query scenarios that historically produced generic "нужны все фильтры", partial planner errors, or false zero. Repeated LLM failures should be marked environmental if trace proves it; do not auto-classify as code.
- Confirm six frozen Core V4 files unchanged, no new production/test changes from QA, no source writes, tenant-wide scans, secret leaks or cross-session mix.
- Verdicts: GREEN only if no **new regressions**, all critical intended A/B scenarios pass, provenance is complete, and no user-visible raw envelope; RED with first failing boundary otherwise; INCOMPLETE if oracle/credentials unavailable. Distinguish separate pending features/issues.
- Chat-only summarized report with TESTED_HEAD, 1–3 tables (scenarios, regressions, remaining OPEN), source oracle summary, exact counts, and recommendation on **whether owner may synchronize Public**. Do not sync Public or invoke public-deploy/public-health-check skills yet.

### Short command
Execute A230R3.5-INTEGRATED-AB-REGRESSION from GIGACODE_NEXT_ACTION.md. Independent end-to-end agent-vs-REAL-AS21 bounded oracle, UI regression and full suites. QA-only; no code fixes/commits. Report + STOP.
