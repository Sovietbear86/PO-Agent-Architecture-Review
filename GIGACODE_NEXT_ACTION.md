# GigaCode — CURRENT NEXT ACTION

## A230R3.15-P31-D1-FORECAST-DETERMINISTIC-CORELESS-QA

**Independent QA only.** Do not modify code, tests, docs, configs, source data, frozen Agent Core V4, or Public. No commits/pushes/merges. Preserve existing user worktree, services, and credentials; use read-only bounded source queries only when needed.

### Context
Previous A230R3.14 P31-D0 **READY** for Delivery Forecast, **BLOCKED_BY_SOURCE** for historical committed predictability. Independent bounded oracle reported DMS-SPRNT-5 as of 2026-11-01T20:45Z: 35 tasks, 20 closed, 15 open, 20 closure timestamps, no committed start baseline, indicative observed 2.0 tasks/workday. Numbers are dated snapshots, not today's facts. Cannot silently use a current snapshot as original committed baseline.
Owner implemented only pure deterministic calculator `po-agent-platform-v2/src/po_agent/sprint/delivery_forecast.py` plus offline tests `po-agent-platform-v2/tests/test_sprint_delivery_forecast.py` (commits `ef20e70`, `10dfd4c`, `2810a55`). **NO plugin wiring, AS21 adapter or UI change yet**. This is a new pure module, NOT frozen Agent Core V4.

### Required gates
1. Fetch origin; record exact `LOCAL_HEAD=REMOTE_HEAD=TESTED_HEAD`, diff relative to previous discovery checkpoint `519ac33`, confirm only new pure module + tests and no Core/service changes. Core V4 6/6 byte-identical to `6fb335d`. No rebase/overwrite dirty files.
2. Run `python -m pytest -q po-agent-platform-v2/tests/test_sprint_delivery_forecast.py` with correct package install/PYTHONPATH. Check 8 test cases all passed; run complete V4/Task API regression and frontend build for unrelated regressions. Report exact counts, first failure if RED.
3. Independently inspect formula implementation: no committed-baseline fabrication; `closed_at` authoritative timestamps, explicit complete membership, counted closed events, verified working calendar and timezone, source=REAL_AS21, no made-up 3 story points, zero/partial/source outage fail closed, current-scope vs committed semantic separation, no lookahead in retrospective mode (currently not implemented).
4. Test boundaries with additional independent adversarial cases: 2 or fewer closures, no working days, sprint just started, closed outside end, naive dates, in-flight future closure, percent never exceeds 100, zero open with all tasks done, leap/month/year changes, invalid status/negative counts and duplicates. Note exact first bug and minimal owner-only fix recommendation; do not edit.
5. Explicit **risk check**: current calculator accepts `closed_total` and `closed_at` as authoritative from caller; identify any unvalidated input that could contaminate metrics, and whether source can provide both. No code path is currently wired to actual AS21; do not report Live A/B forecast GREEN. No UI test for new feature yet.
6. Confirm DMS-SPRNT-5 authoritative source constraints and any missing fields before next stage: no committed baseline, closure timestamps available, current membership exact, working calendar/timezone must be specified and source-backed. Validate normalized timestamps in product timezone rather than UTC unless contract says UTC.
7. Write report: tested SHA, test matrix, code-source evidence, frozen Core 6/6, correctness/fail-closed assessment, remaining API/plugin/UI wiring contracts, recommendations and `D1_GREEN / RED / INCOMPLETE`. No QA code changes, report and STOP.

### Short command
Run A230R3.15-P31-D1-FORECAST-DETERMINISTIC-CORELESS-QA from current Review GIGACODE_NEXT_ACTION.md. QA-only, fresh HEAD, pure forecast unit/adversarial tests + full regress, source semantics and Core 6/6. No commits, report and STOP.
