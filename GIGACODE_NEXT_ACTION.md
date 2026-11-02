# GigaCode — CURRENT NEXT ACTION

## A230R3.17-P31-D2-SOURCE-CONTRACT-SEAM-QA

**Independent architecture/source QA only.** Do not change production code, tests, docs, frozen Core, git or AS21; no commits/merges. Keep existing services and dirty files untouched. Source requests read-only, scoped and bounded. All discoveries must cite actual paths and tool response types. No fake metric or inferred source fields.

### Prior result
A230R3.16-R2 **D1_R2_GREEN** on `f58add8`; owner fix `29ca0ac` is verified. Pure deterministic `sprint/delivery_forecast.py` has 11/11 tests and 15/15 independent adversarial checks, V4 299 passed, frontend build exit 0, frozen Core 6/6. Task API 115 passed /25 failed (21 legacy CRUD +4 MCP-dependent integration environment; source-backed 69 passed /1 known pre-existing). Calculator is NOT wired into runtime, agent capabilities, AS21 or UI.

### Objective
Provide exact minimal **outside-Core** integration contract and safe negative conditions for D2: `sprint.delivery_forecast` sourcing real AS21 data using existing read-only Task API, complete sprint membership, real closure history and explicit product-local working calendar. Committed predictability remains N/A (no start baseline). Do not pretend same scope/current status implies historical baseline.

### Gates
1. HEAD and 6 frozen Core byte hashes vs `6fb335d`. Inspect `get_sprint_tasks`, `get_task_history`, `get_sprints` / Task API GET routes, domain Task/StatusTransition fields, source completeness and bounded pagination. Existing `get_sprint_tasks` uses `search_tasks(... max_results=self._scan_limit)`; determine whether it **proves completeness**, especially at scan cap. If no completeness metadata, **BLOCK D2 READY** until source contract explicitly gains it.
2. Verify independently whether `/api/v1/swtr-read/tasks/{code}/history` is implemented and actually returns closure timestamps with a terminal status. Distinguish an open/absent endpoint from an empty task history; must fail closed. Determine if `closed_at` is source-visible without history. Avoid N task-history calls without a bounded cap. Evaluate N+1 health and avoid 35 cold-stdio MCP calls that time out the UI.
3. Locate existing V4 skill registration and plugin binding seam that powers `sprint.predictability` and `sprint.health`. Give exact constructor path, CapabilitySpecV4/SkillSpecV4/UIContractV4 and callable strategy, not speculative filenames. Do not change Core.
4. Check task status category mapping (RESOLVED, CLOSED, DONE, reopened), task ID dedup, status event timestamps versus updated_at, timezone (product-local TZ explicit), product calendar weekdays and holiday truth. Any field absent → `INSUFFICIENT_EVIDENCE`, not 0% or source-sourced claim. Distinguish source_unavailable and incomplete membership.
5. Propose small commits for owner: (a) bounded source facade with completeness and proven closure history, (b) projection adapter to SprintForecastInput, (c) plugin registration `sprint.delivery_forecast` OUTSIDE Core, (d) UI card in Sprint view. Include deterministic mocked tests, bounded REAL AS21 oracle DMS-SPRNT-5, max request/time budget, full regression/core 6/6 and rollback. No live source data or identifiers in Public tests.
6. Report `READY_TO_IMPLEMENT` **only** if membership completeness, closure semantics and local working-calendar contract can be reliably provided; otherwise `SOURCE_CONTRACT_BLOCKED` with first missing field/API and smallest safe owner fix. No feature implementation in this QA.

### One short command
Execute A230R3.17-P31-D2-SOURCE-CONTRACT-SEAM-QA from current Review GIGACODE_NEXT_ACTION.md. Inspect exact source/skill seams, completeness, closure history and DMS-SPRNT-5 bounded oracle. QA-only, no changes/commits; report and STOP.
