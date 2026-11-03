# GigaCode — CURRENT NEXT ACTION

## A230R3.28-P31-D2-R12-PRIVATE-CLOSURE-PIPELINE-QA

**Independent QA only.** You are an independent tester, NOT developer. Never change code, tests, configs, Core, UI, task-api, MCP-SWTR, public repository, or owner documentation. Do not commit, merge, push, install/update dependencies globally, restart/stop user's services, write AS21 or run tenant-wide scans. Preserve dirty/untracked QA files and all local user processes. Fetch origin; establish LOCAL=REMOTE=TESTED_HEAD before tests; if branch moved, record exact diff and do not overwrite.

### Already certified baseline
A230R3.27 D2_R11_GREEN, tested `aca94e4`: SAME complete DMS-SPRNT-5 sprint read emits 26/26 exact source-declared lowercase current workflow status types (independent MCP A/B oracle 26/26), no task-display inference, opt-in local UTC observation snapshot; 33/33 adversarial; 111 focused; V4 299/299; Task API 25 *pre-existing baseline failures*; frontend build exit 0; frozen Core V4 6/6 byte-identical to `6fb335d`. No numeric live forecast. Owner-approved terminal set / working calendar / TZ not yet deployed. In A230R3.26 F1 the agent-side adapter silently accepted absent sprint_id and generated sprint_key=""; now fixed but NOT QA-certified.

### Owner incremental patch (NOT independently tested)
- `12a5242`: new `task-api/app/services/sprint_forecast_pipeline.py`, INTERNAL `collect_and_project_sprint_closures`. Requires explicit `SprintForecastPolicy` preflight BEFORE any AS21 reads, then bounded `collect_sprint_workflow_evidence(require_current_status_types=True)` same-read UTC observation; calls `bind_source_status_types` with **exact** source types and caller-provided explicit terminal types. Returns `SOURCE_PROVEN` internal proof with task-keyed closure timestamps, NOT numeric forecast or public API. Refuses future events, current/history mismatch, incomplete membership or statusTypes; no hardcoded terminal statuses. No new REST route or V4 skill.
- `b0c2e47`: 6 offline pipeline unit scenarios, including policy-before-read, one sprint+2 history reads, reopened task, missing status type and future transition.
- `87ca38c`: agent `delivery_forecast_adapter.py` now rejects missing/malformed sprint_id; optional `expected_sprint_id` rejects wrong sprint scope BEFORE calculator.
- `9997658`: 8 parameterized/new adapter tests for identity and mismatches.
- This assignment only, no Core files touched; existing Public unchanged.
- **No actual product owner has approved terminal types, workdays or timezone for production**. The synthetic policy in tests is NOT an approval. Nothing runs the pipeline in live app, no new API/plugin/UI, no numeric forecast claimed; stage is strictly internal.

### Gate 0 — integrity
- HEAD and exact delta since `aca94e4`: one NEW internal task-api pipeline, one NEW pipeline test, one modified agent-side adapter, one modified adapter test, this QA spec; document unrelated branch commits if any.
- Frozen 6 canonical Core V4 files same blobs as `6fb335d`; no hardcode of PRD/DMS real IDs, source writes, credentials/PII or reintroduction of hidden default production terminal types.
- Existing `/sprints/{id}/forecast/source-evidence` REST response remains counts-only and does NOT expose `history_by_task`, `current_status_types`, `closed_at_by_task`, timestamps mapped by task key or raw AS21 actors.

### Gate 1 — offline source-to-projection
- Execute new `task-api/tests/test_sprint_forecast_pipeline.py` (6 expected) and existing snapshot/collector/projection/source/policy/source-proof tests. Run independent adversarial: policy=None, approval authority malformed, malformed working weekdays, unknown statusType, missing conflicting types, missing history identity, duplicated/same-timestamp transitions, reopened lifecycle, history after captured observation as_of (must fail), wrong source/sprint identity, >100 tasks, >5 concurrent histories, source outage/timeout, no source-admin/tenant scans. Record first failing boundary.
- Verify `current_status_types` comes from same complete source read; no N+1 unit rereads; verified closure uses **last terminal transition** and reopened task is not considered done. Check timestamps exactly preserved, no `updated_at` fallback or display-name `done` inference. Out-of-sprint closure guard remains future adapter input (sprint dates needed); do not count that as present here.
- Test `SprintForecastPolicy` is **caller-supplied** and has no auto-default; synthetic test policy never activates live forecast. Note the current policy's `authority` field is syntax validation, not cryptographic authorization; do not suggest enabling as public write input.

### Gate 2 — agent adapter identity guard
- Run `po-agent-platform-v2/tests/test_sprint_delivery_forecast_adapter.py` (prior 14 + new 8 = 22 collected expected) and calculator (11). Check missing/invalid/non-string sprint_id, mismatched `expected_sprint_id`, valid target, invalid closure key/timestamp/format, missing REAL_AS21 provenance and incomplete data. A fabricated `SOURCE_PROVEN` JSON from a user is **not** sufficient as live authorization: this module remains private/offline. No false READY, no committed Predictability fabricated.
- Any AttributeError/TypeError/HTTP 500 from malformed source/proof or wrong scope is RED.

### Gate 3 — bounded live compatibility and regression
- If authorized, perform one read-only source schema/AS21 A/B on scoped DMS-SPRNT-5 (<=5 selected tasks for status/history checks; full complete sprint list allowed within cap=100). The tested path must not expose internal closure maps via REST. Do NOT compute/claim live numerical forecast using synthetic policy.
- Full Agent V4 (prior 299), Task API source-backed and full (25 known pre-existing failures), frontend TypeScript/Vite build, 6/6 frozen Core. Label tests with baseline/delta; no fake "full GREEN" if baseline fails.
- Check `task-api` module imports and asyncio sequencing: policy validation BEFORE read_sprint; capture as_of after sprint read and BEFORE history read; no race silently turns incomplete status into success.

### Deliverable
QA report `po-agent-platform-v2/qa_reports/P31_D2_R12_PRIVATE_CLOSURE_PIPELINE_QA.md` (untracked, no commits) with TESTED_HEAD, source hashes, test counts, first failing boundary, external AS21 availability, proof DTO exposure risk, and next owner contract for a PRIVATE source-to-forecast bridge + safe scalar-only HTTP response after genuinely approved policy. Verdict `D2_R12_GREEN` or `D2_R12_RED`. Preserve all services, STOP.

### Short command
Execute A230R3.28-P31-D2-R12-PRIVATE-CLOSURE-PIPELINE-QA from current Review GIGACODE_NEXT_ACTION.md. Independently test policy-first same-read closure pipeline + agent sprint identity fix; full regress, safe counts-only public REST and frozen Core 6/6. QA-only, no edits or commits; report and STOP.
