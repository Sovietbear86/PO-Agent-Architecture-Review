# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_105B_SEARCH_VERSIONS_POST_FIX_AND_RELEASE_DISCOVERY`

## Role boundary
You are QA/research executor only. **Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

Mandatory rules in `po-agent-platform-v2/docs/testing/POST_CHANGE_AB_ORACLE_CERTIFICATION.md` apply. AS21/SWTR can be transiently unavailable: timeout/502/503 requires retries up to 2 times with 20–30 s backoff and a focused retest after runtime/source revalidation before environment classification. Concurrency=1. Heavy calls may use 180 s.

Assignment 105A proved the live MCP `search_versions` contract:
- `space` is REQUIRED;
- `calculatedAttributes` is optional with default `None`;
- all other request fields have defaults;
- the previous Task API behavior incorrectly allowed `/versions` without `space`, which reached MCP and surfaced as misleading HTTP 502.

Owner fix under test:
- commit `f77088ae83950ea71a0eb3f8e50a956fd5febd97`
- Task API now fails locally with typed HTTP 400 when `/api/v1/swtr-read/versions` is called without `space`.

The schema-aware builder already forwards caller-provided `space` into the live nested request; do not invent calculated attribute names or hardcode DMS/OLP into production behavior.

## Goal
Certify the owner fix against REAL AS21/MCP-SWTR and immediately continue the release/version discovery that Assignment 105 could not complete.

Primary success condition: `/versions?space=DMS` must reach the REAL MCP `search_versions` path successfully and return authoritative version/release data or an authoritative empty result. Missing-space must return local HTTP 400, never upstream 502.

## Phase 0 — provenance and fresh runtime
1. Pull current branch; record exact HEAD and clean tracked worktree.
2. Verify owner fix commit is in ancestry.
3. Fully restart/revalidate Task API and PO Agent from the tested HEAD; record PIDs/start times.
4. Establish ordinary REAL AS21 reads in this run: task point-read plus approved sprint controls.
5. Approved sprint control order:
   - `DMS-SPRNT-2` primary;
   - `DMS-SPRNT-1` cross-check;
   - `OLP-SPRNT-5` independent-product cross-check.
6. Validate sprint facts live; never hardcode expected task counts or key sets from prior reports.
7. fake/mock/frozen authoritative calls=0; AS21 writes=0.

## Phase 1 — missing-space contract regression
Call exactly:
`GET /api/v1/swtr-read/versions`

Expected:
- HTTP 400;
- typed local detail containing `space is required`;
- no MCP `search_versions` invocation for this request;
- no HTTP 502.

If this fails, verdict `OWNER_CHANGE_REGRESSION` and trace FIRST_FAILING_BOUNDARY.

## Phase 2 — REAL DMS versions read
Call:
`GET /api/v1/swtr-read/versions?space=DMS`

Requirements:
1. This must use the REAL MCP-SWTR `search_versions` capability.
2. Capture actual request shape / facade evidence sufficient to prove `space=DMS` reached the nested MCP request.
3. Record HTTP status, version count, pagination metadata, and normalized version identifiers/names/date/status fields returned.
4. An authoritative HTTP 200 empty version set is allowed if Oracle independently confirms DMS has no versions matching the request; do not fabricate releases.
5. A validation error saying `space` or `calculatedAttributes` is missing is a product/integration regression, not environment downtime.
6. A timeout/502/503 unrelated to validation must follow mandatory retry/retest before environment classification.

## Phase 3 — independent Oracle B
Use an independent read-only path against the same live MCP `search_versions` contract, without using the Task API response as expected truth.

Because MCP transport may be owned by Task API, an independent Oracle may use a separate direct MCP client/process or another schema-valid read route. If direct transport cannot be opened independently, prove equivalence through raw MCP call evidence/logs and do not claim a stronger Oracle than the evidence supports.

Compare normalized version/release identifiers and metadata. Allowed row outcomes:
- `AB_PASS`
- `AUTHORITATIVE_EMPTY_SOURCE`
- `PRODUCT_DEFECT_PROVEN`
- `ENVIRONMENT_BLOCKED`

## Phase 4 — OLP cross-space control
Call:
`GET /api/v1/swtr-read/versions?space=OLP`

Use the same retry/retest rules. Compare space isolation: DMS and OLP results must not be silently cross-contaminated. Empty OLP result is valid if authoritative.

## Phase 5 — resume release discovery
Using only REAL versions actually returned by Phase 2/4:
1. Select at least one valid release/version candidate represented in the authoritative source.
2. Capture exact version identifier/name and available metadata.
3. Determine whether tasks expose membership via `fix_version_s` / release identifier.
4. Recover the exact release-forecast contract from repository code if not already captured.
5. Determine whether current source data can supply at least two historical timeline points required by forecast.

Do not guess release IDs. Do not equate a current version record with a historical release timeline.

## Phase 6 — release timeline source classification
Classify `release_timeline` as exactly one of:
- `AVAILABLE_ALREADY_NOT_WIRED`
- `DERIVABLE_FROM_EXISTING_TASK_HISTORY`
- `DERIVABLE_WITH_SMALL_ADAPTER_EXTENSION`
- `NEW_TASK_API_FACADE_ONLY`
- `UPSTREAM_SWTR_CAPABILITY_MISSING`
- `NO_VALID_REAL_RELEASE_AVAILABLE_FOR_PROOF`

A 404 on a guessed endpoint is not enough to prove upstream absence. Search equivalent release/version/task-history paths.

If exact authoritative timeline facts exist, independently calculate the expected release forecast and compare Agent A to Oracle B. If only current release metadata exists and no historical timeline can be recovered, keep `release-forecast` unavailable and state the exact missing fact/event.

## Phase 7 — source and regression integrity
Report exact counts from this run:
- successful task reads;
- successful sprint reads, listing all sprint IDs;
- successful DMS version reads;
- successful OLP version reads;
- successful release task/history reads;
- HTTP 400 expected contract checks;
- HTTP 500;
- HTTP 502/503;
- retries/retests;
- fake/mock/frozen=0;
- AS21 writes=0.

Verify no new Learning Loop policy is created/promoted/changed by this source-contract fix.

## Output
Create only QA/research artifacts under `po-agent-platform-v2/qa_reports/`.

Primary report:
`po-agent-platform-v2/qa_reports/SEARCH_VERSIONS_POST_FIX_RELEASE_DISCOVERY_105B.md`

Allowed final verdicts:
- `SEARCH_VERSIONS_FIX_CERTIFIED_RELEASE_PATH_PROVEN`
- `SEARCH_VERSIONS_FIX_CERTIFIED_RELEASE_TIMELINE_GAP_PROVEN`
- `SEARCH_VERSIONS_FIX_CERTIFIED_NO_REAL_RELEASES`
- `PRODUCT_DEFECTS_PROVEN`
- `OWNER_CHANGE_REGRESSION`
- `AB_MISMATCH`
- `BLOCKED_BY_ENVIRONMENT`

A GREEN-like verdict requires missing-space HTTP 400 plus successful REAL `/versions?space=DMS` (or authoritative empty DMS source) after the mandatory retry/retest rules, with no fake data and no AS21 writes.

Commit/push only allowed QA/research artifacts, report final SHA, then STOP.