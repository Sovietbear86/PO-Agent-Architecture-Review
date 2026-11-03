# GigaCode — CURRENT NEXT ACTION

## A230R3.29-P31-DELIVERY-FORECAST-VERTICAL-E2E-QA

**ONE INTEGRATED ACCEPTANCE GATE ONLY.** You are independent GigaCode QA, not developer. No code/test/config/docs changes, no commits/push/merge, no modifications to frozen Agent Core V4 or Public, no AS21 writes or tenant-wide scans, do not stop user's 8004/5175/8241/3000 services. Preserve untracked QA files; use separate ports for your stack. Fetch origin; record LOCAL=REMOTE=TESTED_HEAD. Identify baseline from prior A230R3.28 R12 GREEN, tested HEAD 7e2b0d9. Don't report PASS for unexecuted cases.

### Product decision (explicitly approved by PO on 2026-11-03)
Terminal source statusType=`done` (exact, lowercase), product timezone `Europe/Moscow`, working days Monday-Friday; holidays NOT accounted for (label limitation). Operational **current-scope** throughput forecast, never historical committed Predictability; historical Predictability remains secondary with `н/д` until an actual committed baseline is supplied. Owner config `task-api/config/sprint_forecast_policy.json`, must NOT be inferred from sample AS21 tasks.

### Owner production vertical slice (NOT independently QA-certified)
1. `task-api/config/sprint_forecast_policy.json` v1 approved config (commit 906964e).
2. `task-api/app/services/sprint_forecast_delivery.py` policy parser + safe scalar observed-throughput calculator (b2a90ea).
3. `task-api/app/routers/swtr_read.py` GET `/api/v1/swtr-read/sprints/{sprint_id}/delivery-forecast` (bd1e0fd). Source-backed bounded sprint directory for real period, full authoritative current statuses+histories via policy-first `collect_and_project_sprint_closures`; fixed allowlist numeric DTO; never exposes per-task/history data. Original GET `.../forecast/source-evidence` must remain counts-only.
4. `po-agent-platform-v2/src/po_agent/adapters/task_api.py` read-only DTO method (b779d42); `po-agent-platform-v2/src/po_agent/api/v1/__init__.py` GET `/api/v1/sprints/{sprint_id}/delivery-forecast` through existing real TaskAPI adapter (cc19810).
5. External-Core Plugin `po-agent-platform-v2/src/po_agent/harness/v4_plugins/sprint_delivery_forecast.py` with skill and capability `sprint.delivery_forecast`, registered by existing trusted dynamic registry (0489681), plus tests `po-agent-platform-v2/tests/test_sprint_delivery_forecast_plugin.py` (7f52868).
6. Web `po-agent-platform-v2/frontend/src/api/client.ts` typed source GET (a3b8431), `po-agent-platform-v2/frontend/src/recovery/Pages.tsx` primary Delivery Forecast metric with typed loading/no-source and secondary historical Predictability (2bfbaad).
7. Offline scalar policy/forecast regressions `task-api/tests/test_sprint_forecast_delivery.py` (7fe25a).
8. This spec. **No frozen Core files were intentionally changed**; verify 6/6 independently.

### Gate A — correctness and source safety
- Compare all changes since R12 `7e2b0d9` exact files. Verify Core 6/6 same SHA as `6fb335d`, no leaked credentials or hardcoded source sprint/task/person, no uncontrolled raw output, no public repo modifications.
- Validate policy loading from repo path, authority/date and exact values; ensure no invisible default if config absent/invalid; no holidays claim. Verify malicious/unknown/whitespace/uppercase types cannot silently map to done. The policy is local PO-approved for the single-user app, **NOT a multi-user authorization system**.
- Run new `task-api/tests/test_sprint_forecast_delivery.py` and `po-agent-platform-v2/tests/test_sprint_delivery_forecast_plugin.py` plus all previous source/collector/policy/projection/pipeline/calculator/adapter tests. Critically compare task-api scalar calculator vs agent pure `forecast_sprint` on same inputs (exact parity for workday counting, projection, insufficient evidence, reopened, dates, timezones). Any false READY, fake 0/100, mismatched sprint ID, missing source provenance is **RED**.
- Validate single-sprint directory (<=5 pages), no tenant scans, full membership <=100, histories concurrency <=5, 90-second budget; query count audited, no writes, no local-task fallback. Source sprint start/end MUST be from real AS21 source directory, not UI/user fabricated dates.
- Check source event change AFTER current status observation fails closed, no optimistic blending; statusType source declared, no `updated_at` fallback; reopened not counted, strict history completeness.

### Gate B — backend + plugin
- Build/import Task API with fresh processes and correct config path, verify the new two GETs: direct Task API and agent proxy return **only allowed scalar fields**, status READY only on SOURCE_PROVEN. Source outage/incomplete returns typed no-forecast. Old source-evidence endpoint remains counts-only. Verify appropriate HTTP timeouts, errors, request regex and that no forbidden AS21 mutations occur.
- Registry discovery: `builtin.sprint.delivery_forecast`, skill `sprint.delivery_forecast`, argument `sprint_id`, completion/evidence, typed refusal; no Core modifications. Agent runtime adapter in REAL task-api mode supports method. Dynamic trusted plugin discovery works; no fake model/source payload.
- Check routing correctness for user prompts such as `Спрогнозируй завершение DMS-SPRNT-5`, `Delivery Forecast DMS-SPRNT-5`; if LLM endpoint unreliable label separately and run deterministic capability handler. Never claim agent live skill GREEN if only offline fixture passed.

### Gate C — full user journey REAL AS21 A/B
- With isolated agent:TaskAPI:MCP:Vite stack on free ports, without disrupting user's running processes, browser DOM tests on «Спринты» using DMS-SPRNT-5; primary card must say Delivery Forecast, show `XX%` ONLY with READY and confirmed REAL_AS21; historical Predictability remains secondary `н/д` (no committed baseline). Verify safe loading/source outage, refresh, switching sprint, no old stale percentage, as-of/source visible, no raw planner JSON/PII, no 5xx for malformed input.
- Independent bounded REAL AS21 A/B oracle: exact scope, current status types, closure date history, throughput and forecast math for DMS-SPRNT-5. 26/26 membership was observed in R12, **fresh drift is permitted** and must be reported with timestamps rather than marked failure without oracle. No broad scans. If date source fails or horizon ended, report typed INS UFFICIENT and REASON (not fake numeric forecast), explicitly.
- Compare totals to health/throughput widgets but distinguish different period/scope semantics.

### Gate D — full regression
- Agent V4 all (~299 baseline), Task API full (25 known historical failures separate), source-backed suites, UI TypeScript + Vite, 6 frozen Core files. Record exact first-failure boundary. Do not demand cleanup of unrelated historical tests; no automatic retries for failed source reads that can create scans.
- Security: no task-keyed `closed_at_by_task`, `history_by_task`, `current_status_types`, `snapshot_observed_at`, raw statuses/actors in browser/API. Agent evidence only aggregated. Explicitly inspect response JSON.
- Future items (P3.5 Overview spaces, Releases/sbeproject and Quality) remain in evolution plan, out of scope.

### Verdict
`P31_E2E_GREEN` ONLY if at least one actual live browser READY + independent REAL AS21 A/B + safe fail-closed + regressions. If no live READY due to real source insufficiency, `P31_E2E_SOURCE_CONDITIONAL` (not success). If code defect `P31_E2E_RED`, report first failing boundary with minimal specific owner patch, do not repair. **One comprehensive QA report and STOP; no new assignment series for small issues.** Write untracked `po-agent-platform-v2/qa_reports/P31_DELIVERY_FORECAST_E2E_QA.md`, no commits.

### GigaCode command
Execute A230R3.29-P31-DELIVERY-FORECAST-VERTICAL-E2E-QA from current Review GIGACODE_NEXT_ACTION.md. ONE integration QA of complete source→REST→V4 skill→Sprint UI Delivery Forecast; strict REAL AS21 DMS-SPRNT-5 A/B, fail-closed, full regression, frozen Core 6/6. QA-only, no edits/commits. Report and STOP.
