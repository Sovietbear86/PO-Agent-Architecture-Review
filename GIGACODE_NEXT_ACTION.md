# GigaCode — CURRENT NEXT ACTION

## A230R3.22-P31-D2-R6-MISSING-EVENT-ID-QA

**Independent QA ONLY.** Do not change production code, tests, docs, Core V4, user services, public repo, AS21 or Git history. No commits, merges, pushes, writes, broad scans, destructive cleanup. Fetch origin; record LOCAL=REMOTE=TESTED_HEAD. Preserve all dirty/untracked QA files.

### Prior independent evidence (A230R3.21)
`D2_R5_SOURCE_BLOCKED`, tested `6b3de45`: pure closure projection unit suite 13 passed, adversarial 18/18, Agent V4 299, frontend build 0, Core V4 6/6 unchanged. REAL AS21 DMS-SPRNT-5: 26 tasks / 76 workflow transitions, **76/76 raw history entries have no id**; optional HistoryEvent.event_id is None for all. Source newValue contains per-event statusType, but current public read-only `/tasks/{code}/history` flattens to name strings so projection cannot prove terminal type. A per-task current statusType is present. No committed sprint baseline. Previous endpoint route 404 in a stale running Task API process is NOT proof of absent source code; check running HEAD/version.

### Owner incremental fix (not yet QA certified)
- `e796b97`: in `task-api/app/services/sprint_forecast_source.py`, if source history has no event_id, derive **explicitly LOCAL**, deterministic SHA-256 dedup key from task key, timestamp, old_value and new_value; reject identical transition signatures as ambiguous, reject missing old/new. Retain event_identity_source=local marker. Native source IDs remain native.
- `1f6707a`: synthetic tests for no-ID stability, duplicate signature rejection, missing transition values. No changes to frozen Core, route, MCP, plugin, UI or AS21. Event statusType mapping and projection binding remain UNIMPLEMENTED. Never claim live forecast GREEN on this patch.

### Gate 0 — integrity
Exactly source validator + its tests + this assignment changed since `6b3de45`. Frozen Core 6/6 byte-identical to `6fb335d`, no source writes, raw PII, security leakage.

### Gate 1 — no-event-ID evidence
- Run entire source validator contract suite (previous 16 + new 3 = 19 expected), projection unit tests (13 expected), collector (6), route (4), calculator (11), plus independent adversarial.
- Test history rows with event_id=None and known timestamp+old/new, stable task-scoped key, two distinct changes same timestamp but different old/new, duplicate identical events fail closed, missing old OR new fail closed, timezones and ordering, known source event IDs unchanged, no fake source ID/provenance, no exposure of locally computed signatures to UI.
- **Important:** source historical observations may have oldValue=None for first status event. If real DMS-SPRNT-5 includes this, report precise frequency: this patch correctly fails closed rather than inventing proof. Do not relax safety to turn RED to GREEN.
- Verify `statusType` from raw AS21 newValue really source-authoritative and find smallest **internal-only** route/adapter change preserving statusType per transition without disclosing PII in user-facing history API. If current route loses it, verdict may be `LOCAL_ID_GREEN_SOURCE_TYPE_BLOCKED`.

### Gate 2 — regressions and real oracle
Run full Agent V4, Task API source-backed/full baseline (25 pre-existing failures), frontend build, frozen Core 6/6. If authorized, one bounded DMS-SPRNT-5 read-only raw history consistency sample (max 5 tasks, explicit limit) for missing IDs and statusType, timestamp, old/new; no unscoped scan or mutation. If source cannot be queried, retain R5 sourced evidence with timestamp and label NOT RECHECKED.

### Deliverables
Exact tested HEAD, source validators/tests, source provenance and no-ID behavior, degree to which live statusType source can be preserved, first failure, next smallest owner change. Verdict `D2_R6_GREEN` for pure patch only / `D2_R6_RED` for regressions; separately flag `LIVE_SOURCE_TYPE_BLOCKED` until event statusType is preserved and mapped. QA-only STOP.

### Command
Run A230R3.22-P31-D2-R6-MISSING-EVENT-ID-QA from current Review GIGACODE_NEXT_ACTION.md. QA only: no-ID AS21 transition key fix, extra tests, real-source statusType contract, full regression, Core 6/6. No changes or commits. Report and STOP.
