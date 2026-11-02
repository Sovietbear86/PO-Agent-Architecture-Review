# GigaCode — CURRENT NEXT ACTION

## A230R3.24-P31-D2-R8-SOURCE-STATUS-BINDING-QA

**Independent QA ONLY.** No changes to code, tests, docs, config, frozen Core V4, Git history, Public, AS21, existing user services. No commits/pushes/merges/writes/unbounded scans. Keep local untracked QA artifacts and dirty state. Fetch origin; record LOCAL=REMOTE=TESTED_HEAD.

### Previous checkpoint
A230R3.23 D2_R7_GREEN, TESTED_HEAD `7adcf5f`: optional HistoryEvent from/to_status_type and source-preserved workflow statusType confirmed by bounded REAL AS21 DMS-SPRNT-5 oracle (5 tasks/17 events, 17/17 status types), focused 57/57, independent 22/22, V4 299, Task API 161 passed/25 existing failures, frontend build 0, frozen Core 6/6. REAL AS21 statusType values are **lowercase** (done, in_progress, pause); test mocks uppercase; terminal status set must derive from source metadata, never from task display name or hardcoded synthetic guesses. Running Task API process may be stale; identify HEAD before live recheck.

### Owner-only next patch (NOT QA certified)
- `4729c11` appended pure `bind_source_status_types` to `task-api/app/services/sprint_forecast_projection.py`. It maps per-event **source-declared** `to_status_type` by locally proven event identity into existing `verify_forecast_closure_inputs`. Requires explicit caller-provided *source-authoritative* current per-task types, terminal types and snapshot as_of. Exact lowercase values preserved; no name inference or synthetic terminal set, fail closed on missing/duplicate event IDs, missing status types, inconsistent history.
- `77336d8` added three offline tests in `task-api/tests/test_sprint_forecast_projection.py`: lowercase source-proven closed count, absent event type, absent terminal contract.
- **No live adapter/current task type extraction, no terminal source metadata reader, no product-local calendar/TZ, no forecast HTTP route, no V4 Plugin and no UI.** Live Delivery Forecast remains NOT IMPLEMENTED. No frozen Core changes.

### Gates
1. Source integrity: compare delta after previous A230R3.23; only projection + its tests + this assignment. Verify frozen Core 6/6 byte-identical to checkpoint `6fb335d`, no secrets, hardcodes, writes or raw AS21 leaks.
2. Run projection tests (prior 13 + three new = expected **16**), source contract tests (19/19 baseline), collector (6), source-proof route (6), forecast calculator (11). Run independent adversarial: mixed uppercase/lowercase source types, wrong current status, duplicate event IDs, event time future/outside as_of, reopened after done, missing event type, source complete=false, non-dict histories; all must fail closed, with no fake 100% or committed predictability.
3. Source contract review: verify the actual fields for current task statusType in `get_sprint_tasks` complete tasks and **source-defined terminal categories** (e.g. status metadata). Source may return type strings lowercase; do not treat sample `done` as universal production terminal classification. Confirm how to validate statusType lookup against AS21 rather than UI text or manually fabricated values. If missing, `LIVE_ADAPTER_BLOCKED` (pure QA can still pass).
4. Run full Agent V4 (~299) and Task API source-backed/full regression against known 25 Task API baseline failures; frontend build; Core 6/6. Report exact counts, first failing boundary. Do not claim source-to-UI working.
5. Deliver next minimal owner integration contract: task statusType as-of snapshot, authoritative terminal set, explicit product timezone and workdays, projection output conversion to `SprintForecastInput`, HTTP-facing safe response, Plugin/UI change separate. Preserve real source provenance.
6. Verdict: `D2_R8_GREEN` if focused tests and independent guards pass; `RED` if any production regression; *separately* report `LIVE_ADAPTER_BLOCKED` if current/terminal statusType source cannot be proved. QA-only, no code modification, STOP.

### Short command
Execute A230R3.24-P31-D2-R8-SOURCE-STATUS-BINDING-QA from current Review GIGACODE_NEXT_ACTION.md. Verify source-declared lowercase statusType binding and strict fail-closed, current/terminal source contracts, all regression and frozen Core 6/6. Independent QA only; report and STOP.
