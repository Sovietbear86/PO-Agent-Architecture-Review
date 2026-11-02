# GigaCode — CURRENT NEXT ACTION

## A230R3.20-P31-D2-R4-SOURCE-PROOF-GET-QA

**INDEPENDENT QA ONLY.** GigaCode must not change application code, tests, documents, configs, frozen Core V4, Git history, Public repo or AS21. No commits, pushes, merges, mutations, tenant-wide scans, or stopping existing user services. Preserve dirty/untracked QA files. Fetch origin, confirm LOCAL=REMOTE=TESTED_HEAD.

### Baseline and approved product decision
- A230R3.19 D2_R3_GREEN on `38e9fe1`: 6/6 collector tests, 16/16 source validators, 11/11 pure calculator, 26/26 independent adversarial, V4 299, frontend build exit 0, frozen Core 6/6. Task API 137 passed/25 failed same pre-existing categories (21 legacy CRUD + 4 MCP integration). Source collector is bounded to <=100 tasks, <=5 concurrent histories, 90s runtime at route.
- **UX decision:** Delivery Forecast will **replace** main Predictability tile in Sprint view once genuinely source-proven; historical committed Predictability remains in expandable additional metrics and stays N/A absent baseline. NO UI change in this assignment.
- Owner-only first D2 transport patch (NOT yet QA certified):
  - `1faaa20`: one new GET `/api/v1/swtr-read/sprints/{sprint_id}/forecast/source-evidence` in `task-api/app/routers/swtr_read.py`, validated sprint ID, explicit plain Python args for existing complete collection and task history handlers, max_tasks<=100, concurrency=5, whole timeout=90s, no source mutations. Aggregates only task_count/history_complete_count and proven flags. **Does NOT compute forecast, does NOT expose raw task/history payload**.
  - `c3e27d5`: offline route contract tests `task-api/tests/test_sprint_forecast_source_route.py` (complete, incomplete, invalid id and truncated history).
- Agent V4 plugin, real forecast projection, product-local TZ/working-day config and UI tile NOT implemented. No Core change; Public remains at previously merged release.

### Gate 0 — integrity/security
1. Compare HEAD against `38e9fe1`; only one Task API router file + one new test + this spec. All 6 frozen Core files byte-identical to `6fb335d`.
2. Confirm no write-capable route/method, no raw history/user PII in response, no internal host or secret. Audited route must be bounded and must not fall back to local task stores/fake metrics.

### Gate 1 — isolated tests and adversarial cases
1. Run `pytest -q task-api/tests/test_sprint_forecast_source_route.py`; then collector 6, source contract 16, calculator 11.
2. Verify GET source-proof successful response contains only compact typed fields (no `events`, `complete_tasks`, `actor`, raw `history_by_task`), no `forecast` number (null only), committed predictability null.
3. Verify partial/incorrect source (incomplete page, membership truncated, wrong sprint identity, malformed source_data, missing history, wrong history task ID) results in safe typed error with correct HTTP status (not HTTP 200, not uncaught 500). Check error-code consistency and potential exception leaking.
4. Confirm all FastAPI handler `Query` defaults are explicitly passed as plain Python values. Confirm all handler arguments and route path match actual API source and registered router. Source MCP calls remain read-only. Route SLA: <=100 tasks, <=5 concurrent history, timeout 90s. Evaluate whether client timeout is shorter than route budget.
5. Optional, if authorized: one **bounded REAL AS21 DMS-SPRNT-5** GET against isolated Review Task API, independent direct read-only oracle, document exact as_of and complete counts; no broad scans. If source/LLM unavailable mark NOT VERIFIED.
6. Run full V4 (~299), Task API SWTR-read and full baseline (known 25 failures), frontend build. Report exact pass/fail and baseline classification, no blanket GREEN for failing suite. Core 6/6.

### Gate 2 — next D2 contracts
- Determine exact JSON of terminal `statusType` and lifecycle history that can prove a task remains terminal as of snapshot, handling reopened tasks. `updated_at` must NEVER substitute for closure timestamp.
- Define product-local timezone/weekday calendar explicit config (AS21 has no authoritative holiday calendar). If config missing, forecast `INSUFFICIENT_EVIDENCE`.
- Next owner patch after GREEN: adapt safe source evidence into date/timezone/weekday projection, then external-Core `sprint.delivery_forecast` plugin, then UI replacement. Do not attempt in QA.

### Verdict / STOP
`D2_R4_GREEN` only if route response and errors safe, tests/regr unchanged and bounded scoped source. Otherwise `RED` first failing boundary with minimal owner fix. Tested SHA, route URI, exact counts, Core hashes, assumptions, report and STOP.

### Short command
Run A230R3.20-P31-D2-R4-SOURCE-PROOF-GET-QA from current Review GIGACODE_NEXT_ACTION.md. Independent QA only: new GET source-proof route and tests, bounded AS21 read, safe outputs, full regress, Core 6/6. No edits/commits. Report and STOP.
