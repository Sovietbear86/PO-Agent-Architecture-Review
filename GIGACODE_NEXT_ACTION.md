# GigaCode — CURRENT NEXT ACTION

## A230R3.26-P31-D2-R10-FORECAST-INPUT-ADAPTER-QA

**Independent QA ONLY.** No source/test/doc/config/Core edits, no commits/push/merge, no AS21 writes or tenant-wide scans. Preserve local dirty/untracked QA files and all user services. Fetch origin; confirm LOCAL_HEAD=REMOTE_HEAD=TESTED_HEAD.

### Previous independent gate
A230R3.25-R2 **D2_R9_R2_GREEN** on `ee8effe` (per user screenshot, QA same HEAD re-run): working_weekdays policy 18/18, all 34/34 adversarial fail-closed, Delivery Forecast calculator 11/11, full V4 299, Task API 182 passed/25 baseline failures, focused forecast 67/67, frontend build exit 0, Core V4 six frozen files byte-identical to checkpoint `6fb335d`. No real business-approved terminal categories / calendar / timezone deployed, and live Plugin/UI forecast remains absent.

### Owner incremental patch (NOT independently QA-certified)
- `45f40cb`: new `po-agent-platform-v2/src/po_agent/sprint/delivery_forecast_adapter.py`, pure **internal** adapter from source-proven closure evidence (output of complete status transition projector) to existing `SprintForecastInput` and `forecast_sprint`. Requires caller-provided product-local timezone and working weekdays, source-proven snapshot, exact closure evidence. Fails closed on missing/invalid evidence/config, never invents committed Predictability.
- `a3d38b4`: new `po-agent-platform-v2/tests/test_sprint_delivery_forecast_adapter.py`, offline synthetic tests of READY input and incomplete/invalid proof, timezone/calendar, reopen and outside scope.
- **NOT wired** to REAL AS21, REST forecast route, V4 Plugin or UI; source-proven status types and policy approval remain mandatory upstream. No Core change. Synthetic task keys only.

### Gates
1. Exact delta since `ee8effe`: only two new agent-side adapter/test files and this assignment. Frozen Core 6/6 vs `6fb335d`, no direct AS21 reads, no production endpoint changes, no forbidden literal identifiers/secrets.
2. Run new adapter tests and existing `po-agent-platform-v2/tests/test_sprint_delivery_forecast.py` (11). Inspect import isolation, handling of malformed proof dict: missing `sprint_id`, missing/invalid closure mapping, source=LOCAL_CACHE, type confusion booleans for counts, naive as_of/closure, unknown calendar, out-of-sprint dates and future closures, inclusive timezone boundary and rollover, malformed/unhashable weekdays. Confirm `READY` only when complete source-proven closures and valid product timezone/calendar. **Identify any uncaught TypeError/AttributeError** or false READY as RED.
3. Compare real provenance semantics: this adapter trusts a `SOURCE_PROVEN` gate. Confirm that upstream `bind_source_status_types` and explicit business policy are *mandatory* in future callers, not bypassed by raw user input. No premature live feature claims; inspect `closed_at_by_task` stays internal, never goes to UI.
4. Run full V4 (~299), Task API source-backed/full baseline (25 known pre-existing failures), frontend build; identify any delta, verify Core six blob SHA byte-identical.
5. Provide smallest subsequent owner step: an approved/source-authenticated source policy + current status snapshot contract, bounded private projection in Task API, safe compact HTTP response, external-Core V4 Plugin, UI replacement, independent REAL AS21 A/B. Recommend guarding cross-service DTO trust (the current source-proof route only returns counts and no closure timestamps, so the adapter cannot yet consume it).
6. Verdict `D2_R10_GREEN` only if focused tests and all adversarial checks pass; `RED` with first failing line otherwise. Be explicit about live integration still pending. QA only, report and STOP.

### Short command
Run A230R3.26-P31-D2-R10-FORECAST-INPUT-ADAPTER-QA from Review GIGACODE_NEXT_ACTION.md. Independent QA: new pure forecast input adapter, edge cases, full regress and frozen Core 6/6; no edits/commits. Report and STOP.
