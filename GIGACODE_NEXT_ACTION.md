# GigaCode — CURRENT NEXT ACTION

## A230R3.27-P31-D2-R11-CURRENT-STATUS-SNAPSHOT-QA

**INDEPENDENT QA ONLY.** No edits of source/tests/docs/config, no commits/pushes/merges, no AS21 writes or tenant-wide scans, no changes to frozen Core V4, Public repository or user's running services. Preserve dirty/untracked local QA files. Fetch origin and record LOCAL=REMOTE=TESTED_HEAD.

### Previously certified
A230R3.26 D2_R10_GREEN on previous `d190a29` checkpoint: pure forecast adapter 14/14, calculator 11/11, >50 independent adversarial probes, full V4 299, Task API 182 passed/25 same pre-existing failures, frontend build exit 0, Core V4 6/6. Two nonblocking findings: source proof adapter does not yet require sprint_id and the source-proof route gives only counts, not the private closure evidence. No live Delivery Forecast or product-approved terminal-set. This QA must not misclassify isolated pure-module GREEN as live production forecast.

### Owner-only R11 changes (NOT YET QA CERTIFIED)
1. `6c5e2b3` NEW `task-api/app/services/sprint_forecast_snapshot.py`: pure function `extract_sprint_current_status_types` reads a complete sprint membership's canonical `source_data.swtr_attributes[code=workflow_status].value.statusType` and returns exact source types keyed by canonical task ID. Lowercase values preserved, no name inference, cannot silently accept conflicting status types/missing source metadata. This is source-declared *current* status only; not a transactional AS21 historical snapshot.
2. `140ddbe` changes only Task API `sprint_forecast_collector.py`: new **opt-in** `require_current_status_types=False`. When explicitly True, extract types from the SAME single bounded complete sprint read (no extra scans), capture local UTC `snapshot_observed_at` after that read, before concurrently fetching task histories. Fail closed before history fetch if source status types absent. Internal `current_status_types` and `snapshot_observed_at` are included ONLY in this opt-in collection; default and existing source-evidence GET stay counts-only. Local as-of is NOT an AS21 transactional snapshot or proof statuses remain stable while reading histories; later projector must enforce history/current status agreement and reject transitions after captured as_of.
3. `aafc2bf` NEW offline `task-api/tests/test_sprint_forecast_snapshot.py`: exact lower-case source values, duplicate/conflict, invalid/missing/unknown type, no display-name fallback, incomplete scope.
4. `41af2a3` appended 3 collector tests for opt-in, no extra reads and legacy safe output. No new REST endpoint, authorization/config changes, calc/agent adapter/plugin/UI changes or Core edits. **No approved terminal-status product policy; live forecast remains gated.**

### Gate 0 — integrity and scope
- Compare current HEAD delta against prior QA-tested head. Enumerate exact 2 production files (one NEW snapshot helper + one collector additive opt-in), 2 test files (one NEW), this QA assignment; classify any unrelated commits without modifying them.
- Agent Core V4 frozen 6/6 byte-identical to `6fb335d`. Verify no AS21 writes, secrets, hardcoded sprint names/personnel or tenant scans. Public unchanged.

### Gate 1 — independent offline tests
- Run new snapshot test file (expected ~16 parametrized tests), collector tests (previous 6 + 3 new = 9), source-contract (19), source-proof REST route (6), projection (16), policy (18), forecast adapter (14), calculator (11), plus full V4 and Task API. Report exact actual counts, not estimates; known Task API baseline 25 failures must remain separately classified.
- Probe adversarial: `status` only with no `statusType` MUST fail closed; `value.statusType` lowercase exact; dict `statusType.code`; empty/malformed/ambiguous status type; duplicate conflicting attrs; source_data missing; `complete=False`, duplicate task IDs, >100 tasks. No absent field may become a fake `done`.
- Opt-in MUST use one canonical sprint source read, <=100 tasks, <=5 concurrent histories, fail BEFORE history reads on invalid current status type. Default collector remains backward-compatible and existing public GET output has ONLY safe compact counts (no current_status_types/history/PII).
- Temporal contract: `snapshot_observed_at` is server-local UTC *observation* immediately after sprint list read, not an AS21 source as-of timestamp. Induce a task status change/history event after captured as_of in mocked collector and ensure downstream projection rejects or fails on current/history mismatch; **never silently count newer closure**.
- Do not rely on actual user status names, timestamp updated_at or current source metadata to infer terminal classification.

### Gate 2 — REAL AS21 contract (bounded read-only)
- If authorized and available, request **up to 5 tasks** from DMS-SPRNT-5 using existing bounded complete sprint reader; inspect only sanitized `workflow_status.statusType` and no task descriptions/actors, test `extract_sprint_current_status_types` with canonical rows. Cross-check with independent direct MCP oracle. If AS21 does not encode statusType under the assumed canonical attribute schema, report `LIVE_SNAPSHOT_SOURCE_BLOCKED` with actual redacted schema and minimal owner correction; do not guess/copy a display status or rewrite implementation.
- Do not run unbounded/tenant searches. If unavailable, mark LIVE NOT VERIFIED, do not call the feature live.

### Gate 3 — regression and next integration recommendation
- V4 full (~299), Task API full/source-backed (25 known baseline failures), frontend build. Confirm unchanged counts-only GET. Identify any new regressions and Core hashes.
- Next smallest owner step AFTER this green: source-approved terminal-status policy + source sprint dates/weekdays/timezone; private source projection combining same-list status types and complete histories via `bind_source_status_types`, safe typed HTTP response, then external-Core V4 plugin + UI. **No numeric forecast without these gates.**
- Mention earlier nonblocking F1: adapter missing `sprint_id` guard to address before live route.

### Verdict
`D2_R11_GREEN` only if focused/new regresses pass with safe snapshot contract; `D2_R11_RED` with first failing boundary otherwise. Separately mark LIVE source contract VERIFIED/BLOCKED/NOT_VERIFIED. QA-only, report and STOP.

### Short command
Run A230R3.27-P31-D2-R11-CURRENT-STATUS-SNAPSHOT-QA from latest Review GIGACODE_NEXT_ACTION.md. Independently verify opt-in same-read current statusType snapshot and as_of, bounded DMS-SPRNT-5 A/B, safe default GET, full V4/Task API/UI regression and frozen Core 6/6. QA only, no edits/commits. Report and STOP.
