# GigaCode — NEXT ACTION

## A230R3.14-P31-D0-SPRINT-FORECAST-SOURCE-DISCOVERY

**Only independent QA / investigation, no development.** Do not modify application code, scripts, docs, config, frozen Core V4, Public repo, AS21 or sbeproject. No commits, pushes, merges, unbounded source scans or write-capable MCP. Do not stop existing Review/Public services. Preserve dirty files. Record exact LOCAL=REMOTE=TESTED_HEAD.

### Read first
- `PO_AGENT_HARNESS_EVOLUTION_PLAN_UPDATE_2026-11-01.md` P3.1.
- `PO_AGENT_P31_SPRINT_DELIVERY_FORECAST_DISCOVERY_2026-11-01.md` (owner design, **not implementation**).
- Existing Review `Pages.tsx` around sprint predictability and 6 snapshots, `task-api/src/s21_team_performance/skills/sprint_health.py`, `sprint/intelligence.py` and the source-backed V4 plugin graph.

### Gate A — actual implementation contract
1. Independently identify **which code path and skill** currently produce Predictability N/A for the active `DMS-SPRNT-5` UI. Track request → V4 capability → Task API → AS21; inspect raw typed fields without revealing PII. Distinguish historical committed baseline from live scope.
2. Trace `SprintMetrics.tsx` and `task-api/src/s21_team_performance/skills/sprint_health.py` reachable vs legacy paths; pinpoint use of `len(completed_tasks) * 3.0`, if reachable from any UI/CLI then flag **P1 fake-metric risk**. No false-positive claim of production impact without call graph proof.
3. Identify canonical sprint status, start/end timezone, statuses representing DONE/WIP/BLOCKED, and authoritative closure timestamps; reject using `updated_at` as a completion timestamp without proof.

### Gate B — scoped independent REAL AS21 oracle
1. With existing read-only authorized access, query **only DMS-SPRNT-5** and at most 3–5 immediately preceding comparable DMS sprints. Strict bounded pagination/limit (explicit max pages/time), no tenant scan. Record exact `as_of` and request counts; no task/member payload in report.
2. Inventory fields: sprint start/end, historical membership and committed start baseline (if available), current task scope, task resolution dates, creation timestamps, status transitions, WIP, blocked, task-point fields if actually present; throughput of previous sprints, missing values and source lag.
3. Independently compute a **sample-only illustrative formula from REAL source** if all required facts exist. Otherwise typed `INSUFFICIENT_EVIDENCE`. No fabricated scores or invented confidence. Compare all numbers to source B and classify incomplete/partial rather than pretending 0.
4. Check selected 18/36 and 18/35 historical screenshots as **old snapshots only**; never present either as current counts.

### Gate C — feasibility/design review
1. Confirm ability to backtest forecast using information as it existed at the start/middle of prior sprints: no look-ahead leakage.
2. Propose concise exact contracts for `sprint.delivery_forecast` plugin (outside frozen Core), Task API bounded source facade, frontend card and UI data; list unprovable fields and safe fallbacks. Compare alternative rate estimators: current sprint throughput vs prior 3–5 comparable sprints; do not overpromise statistical confidence.
3. Run no code changes. State whether P31-D1 is READY, BLOCKED_BY_SOURCE or NEEDS_DATA_CONTRACT; include specific source field evidence. Read-only checks of frozen Core 6/6.

### Deliverable
One clear in-chat report `P31-D0`: exact TESTED_HEAD, code-path map, evidence matrix `field | AS21 source | completeness | authority | outcome`, bounded requests, DMS-SPRNT-5 source-backed facts with timestamps, unsafe legacy code reachability, initial MVP design, first blocking boundary and suggested smallest non-Core implementation. Optionally save a sanitized **untracked** QA report, never commit. STOP.

### Short command
Execute A230R3.14-P31-D0-SPRINT-FORECAST-SOURCE-DISCOVERY from current Review GIGACODE_NEXT_ACTION.md. Inspect implementation, bounded read-only AS21 oracle for DMS-SPRNT-5 and up to 5 previous DMS sprints, fake-metric reachability, Core 6/6. No fixes/commits. Report and STOP.
