# GigaCode — CURRENT NEXT ACTION

## A230R3.23-P31-D2-R7-STATUS-TYPE-PROPAGATION-QA

**Independent QA ONLY.** Do not change code, tests, docs, Core V4, Git history, AS21 or Public repo. No commits, pushes, merges, broad scans or mutations. Preserve local dirty/untracked QA files, GIGACODE.md additions and running user services. Fetch origin; record LOCAL=REMOTE=TESTED_HEAD.

### Previous gate
A230R3.22 **D2_R6_GREEN for pure no-ID closure identity**, **LIVE_SOURCE_TYPE_BLOCKED** on `7a31828` (subsequent unrelated Review HEAD may contain other owners' changes; compare exact git delta). Independent QA 53/53 source/projection/collector/route/calculator suites, 18/18 adversarial, live-shaped no-ID proof 5/5, V4 299, frontend build 0, Core V4 frozen 6/6; Task API 157 pass/25 baseline fail. Raw AS21 history has per-transition `newValue.statusType` while Task API `_history_value` flattens to a name. No live forecast was claimed.

### Owner narrow patch (NOT independently QA-certified)
- `cf54154` `task-api/app/models/history.py`: optional `from_status_type`, `to_status_type` fields on HistoryEvent (workflow status only, source-declared, no fabricated types).
- `936d25a` `task-api/app/routers/swtr_read.py`: source-only `_history_workflow_status_type` reads explicit `statusType` (string or dict.code) BEFORE `_history_value` flattens; populates optional types exclusively when field_code == workflow_status; missing/unknown => None.
- `dc597be` `task-api/app/services/sprint_forecast_source.py`: preserve optional source types in internal normalized history events.
- `37efaf8`, `3dd2cb3`: offline tests; no new REST routes, plugin, UI, new forecast computations or Core edits.
- **DO NOT claim this completes integration:** type mapping in `verify_forecast_closure_inputs`, authoritative per-task current statusType, product timezone and working calendar and end-to-end forecast still remain for owner later.

### Gates
1. Confirm exact TESTED_HEAD and delta. Scope limited to above source/model/router and tests plus this spec; if other unrelated branch changes appeared, inventory honestly and do NOT reset them. Core V4 6/6 byte-identical to checkpoint `6fb335d`.
2. Run focused tests `task-api/tests/test_sprint_forecast_source_route.py`, `task-api/tests/test_sprint_forecast_source_contract.py`, `task-api/tests/test_sprint_forecast_projection.py`, collector, forecast; independently inspect cases `newValue={"name":"Resolved","statusType":"DONE"}`, `statusType={"code":"DONE"}`, missing type, unknown structure, non-workflow history, prior no-ID records and reopened tasks. Existing history API's old/new display value must not change; no raw dict or actor metadata added to forecast output. Check no name->type inference. If ordinary non-status history event uses optional type incorrectly => RED.
3. Critical integration check: choose a bounded REAL AS21 DMS-SPRNT-5 workflow history sample (<=5 tasks) using read-only authorized source: verify `newValue.statusType` makes it into `HistoryEvent.to_status_type` and `complete_workflow_history()[...]["to_status_type"]`, with exact no-ID source provenance and no PII. If environment unavailable state NOT VERIFIED; pure QA GREEN does NOT mean live source contract GREEN.
4. Validate response schema compatibility for existing consumers (only optional added fields); run Task API source-backed/full regression (25 prior failures known), Agent V4 full (~299), frontend build, Core frozen 6/6. Report *first failing boundary*, not blanket GREEN for known failures.
5. Decide next owner patch scope: robust internal statusType mapping to projection, terminal status set from source metadata, as-of and local working-day contract, read-only Task API output without raw IDs, then plugin/UI. No QA code changes.
6. Verdict `D2_R7_GREEN` only if real source type propagation and all new tests pass; `D2_R7_SOURCE_NOT_VERIFIED` if live oracle inaccessible; `RED` if required focused test or source propagation fails. STOP.

### Short command
Run A230R3.23-P31-D2-R7-STATUS-TYPE-PROPAGATION-QA from current Review GIGACODE_NEXT_ACTION.md. QA only: AS21 workflow statusType preservation through model/route/validator, 5-task bounded oracle, all regress, Core V4 6/6. No fixes/commits. Report and STOP.
