# GigaCode — CURRENT NEXT ACTION

## A230R3.10-REVIEW-SNAPSHOT-FAIL-CLOSED-QA

**INDEPENDENT QA ONLY.** GigaCode must not edit product code, tests, docs, config, Core, Git history, or any AS21 data. No commits/pushes/merges. Preserve existing user services and dirty files. Only read-only bounded REAL AS21 calls. Fetch origin and ensure LOCAL_HEAD = REMOTE_HEAD = TESTED_HEAD before testing.

### Evidence from QA_REVIEW_INCIDENT_2026-10-30
- Prior incident 2026-10-30: V4 FAILED after 80.7s at planner repair / fail-closed without source evidence. Earlier exact trace/logs unavailable; do not assert that 429 caused that exact request. Triage live rerun on later Review runtime: one bounded person+space+creation-period query COMPLETED 46/46 EXACT vs REAL AS21, one task lookup passed; no new code regression. LLM limit/endpoint degradation during previous incident remains plausible, not proven.
- Overview previously timed out after 120s with 3 separate snapshot queries (Snapshot MAX_CONCURRENCY=2) and showed correctly timestamped last-good cache. Sprint 18/36=50% snapshot was stale; fresh observed count 18/35=51.4%, not an AS21 source-data regression. Predictability N/A is valid because no committed baseline.

### Owner frontend-only corrective change (NOT yet QA verified)
- `b395bd6` `po-agent-platform-v2/frontend/src/recovery/pageSnapshot.tsx`: rejects refresh when the Agent returns status other than COMPLETED (FAILED/NEEDS_CLARIFICATION/PARTIAL are **never** saved as successful snapshot), retains previous verified cache and timestamp; safe error taxonomy timeout/rate_limit/source/agent/network/request. Does not expose raw payload/error text or source data.
- `a269f26` `po-agent-platform-v2/frontend/src/recovery/OverviewDashboard.tsx`: Overview displays classified failure reason from the three snapshot requests rather than generic flag only.
- Frozen six Core V4 files, Task API, MCP, LLM planner and source semantics were NOT changed; Public PR #3/#4 remain separate and untouched.

### Gate 0 — source and safety
1. Fetch origin and verify exact tested HEAD and owner delta relative to `ceac9fe`; changes only new QA markdown and these two frontend files; Core V4 6/6 bytes match `6fb335d`.
2. Ensure no secret/token/data leakage, no added unbounded AS21 queries, no API mutation. Public staging unaffected.

### Gate 1 — deterministic non-network frontend tests
1. `npm ci` / `npm run build` in frontend, TypeScript contract. Exercise `useSnapshotHarness` with mocked agent.query and mocked sessionStorage. Cases:
   - COMPLETED -> new snapshot and timestamp.
   - FAILED -> no snapshot overwrite; error visible as "Агент не завершил запрос"; cached rows retain last successful provenance/date.
   - NEEDS_CLARIFICATION or PARTIAL -> not silently presented as refreshed complete data; old snapshot stays.
   - rejected HTTP 429, 503, ERR_NETWORK, timeout -> correct safe user-facing class, stale cache preserved, no raw response/error included.
   - non-cached failed first run -> no fake current data; timestamp remains null.
   - successful retry after failure resets error and refreshes snapshot; stale late response cannot overwrite a newer query.
   - SnapshotStatus / SnapshotRefresh interfaces: all existing callers compile, Overview combines three failure reasons with no unsafe output.
2. Check existing 120s timeout and global max concurrency 2 remain; no repeated parallel requests or increased load. No logging sensitive request bodies.

### Gate 2 — browser/AS21 smoke (read-only scoped)
1. If safe, run isolated Review browser with valid existing session; prove "Обзор" UI status on one failed request and next success; do not interfere with user's services. Explicitly check "Обзор", "Задачи", "Спринты", "Качество" after owner frontend delta. Preserve good snapshots, no planner JSON leak.
2. Test one bounded existing task and one person+space+creation-period query, compare with independent REAL AS21 oracle; if LLM 429 recurs classify accordingly, don't claim code bug or fail correctness. No multiple repeated broad scans.
3. Confirm sprint 18/35 fresh value only if source snapshot/current state proves so; do not hardcode historic count.

### Gate 3 — full regression
Execute V4 full regression, Task API SWTR and frontend build. Report exact passed/failed/skipped and baseline vs delta. Confirm frozen Core 6/6, no Public modifications, no QA commits.

### Verdict
GREEN only if UI failure/last-success semantics and TypeScript build pass, no new regression; RED first failing boundary otherwise; INCOMPLETE when live oracle/browser unavailable. Distinguish original external LLM transient from UI status telemetry fix. Detailed QA report and STOP.

### Short command
Execute A230R3.10-REVIEW-SNAPSHOT-FAIL-CLOSED-QA from current GIGACODE_NEXT_ACTION.md (Review branch). Independent QA only, no code changes. Recheck stale-cache/error taxonomy, frontend build, full V4/Task API and frozen Core 6/6; report and STOP.
