# GigaCode — CURRENT NEXT ACTION

## A230R3.19-P31-D2-R3-BOUNDED-COLLECTOR-QA

**Independent QA ONLY.** No code/tests/config/README/Core edits; no commits, pushes, merges, AS21 writes or unbounded scans; preserve user services and dirty/untracked QA reports. Fetch origin and record LOCAL=REMOTE=TESTED_HEAD.

### Previous checkpoint
A230R3.18-R2 **D2_R2_GREEN** on `62e4322`: source-contract 16/16, adversarial 17/17, forecast 11/11, V4 299, frontend build exit 0, frozen Core 6/6; Task API 131 passed/25 failed (pre-existing: 21 legacy CRUD + 4 MCP-dependent integration). This closes R1 uncaught AttributeError from malformed source_data.

### Owner D2 incremental change, not QA-certified
- `d54284e` added `task-api/app/services/sprint_forecast_collector.py`, a dependency-injected bounded **read-only pure source orchestrator**: complete canonical sprint membership first; <=100 tasks; <=5 concurrent history calls; whole operation <=120s; per-task history completeness and timestamp verification; fails closed, returns compact source evidence plus explicit forecast=None and committed_predictability=None. No fabricated closure/forecast and no CORE changes.
- `ae762ca` added `task-api/tests/test_sprint_forecast_collector.py` offline tests for completeness, concurrency, timeout, identity, bounds.
- Not connected to HTTP route, AS21 runtime adapter, Agent V4 plugin or UI. **Do NOT call this a live feature or declare REAL AS21 forecast GREEN.**

### Gate 0 — integrity
Sync current branch; show delta only two new collector files and this assignment since `62e4322`. Core V4 six files byte-identical to checkpoint `6fb335d`; no credentials/PII/source writes.

### Gate 1 — focused independent test
Run `task-api/tests/test_sprint_forecast_collector.py` (expected 6 PASS), `task-api/tests/test_sprint_forecast_source_contract.py` (16 PASS) and 11 Delivery Forecast tests. Probe adversarially: malformed source_data/metadata; source not complete; history truncated; duplicate task IDs; task count 0 and >100; read_sprint non-dict/wrong ID; history non-dict; first history error while others await; >=6 simultaneous history attempts; 120s bound and cancellation; non-authoritative statuses; reused data from different sprint. **Check timeout on one bad stalled MCP/history call with cancellation.** If exceptions leak as HTTP 500 on future facade, document needed typed mapping.
Independently inspect generated response for raw PII/history; ensure pure orchestration does not yet expose it to UI.

### Gate 2 — regressions and next contract
Run V4 full (~299), Task API source-backed battery and broader Task API, frontend build. Classify known 25 previous failures as baseline. Confirm collector can be called by future Task API read-only route with *real* existing `get_sprint_tasks(complete=true)` and `get_task_history` while honoring QoS; inspect for FastAPI Query object defaults when calling handlers internally (must pass ordinary Python args).
Recommend next **smallest** owner patch: one GET source-proof endpoint with typed incomplete/unavailable response (no raw payload), isolated tests. Explicitly specify required source-proven sprint date/timezone/weekdays/terminal status classification before any projection or plugin.
Core 6/6 no drift, Public untouched.

### Verdict
`D2_R3_GREEN` only if collector gates all pass, else RED with first failing boundary and minimal owner fix. QA only, report then STOP.

### Short command
Execute A230R3.19-P31-D2-R3-BOUNDED-COLLECTOR-QA from Review GIGACODE_NEXT_ACTION.md. Independently test new bounded async collector (<=100 tasks, <=5 concurrency, fail closed), 16 source tests, 11 forecast, full regress and frozen Core 6/6. No edits/commits. Report and STOP.
