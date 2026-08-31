# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_105_RELEASE_TIMELINE_SOURCE_PROOF`

## Role boundary
You are QA/research executor only. **Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

Assignment 104 proved an upstream source gap for historical sprint commitment: current scope and current-sprint timing are available, but authoritative sprint-start membership history/snapshots are not. Therefore `sprint-carryover` and `sprint-scope-change` must remain unavailable for now; do not invent a snapshot from current scope.

We now target the last independent unavailable capability: `release-forecast`, currently blocked by missing `release_timeline`.

## Goal
Prove, on REAL AS21/SWTR data, whether `release-forecast` can be computed exactly from existing authoritative release metadata + task history, or whether a new upstream source capability is required.

If proof succeeds, owner should be able to move readiness from `51/54` to `52/54` while the two sprint-snapshot skills remain blocked upstream.

## Phase 0 — provenance and live-source gate
1. Pull current branch; record exact HEAD and clean tracked worktree.
2. Fresh production task-api + REAL AS21/SWTR.
3. Establish at least 3 successful REAL reads in this run, including one task point-read and one release-related read.
4. fake/mock/frozen authoritative calls = 0; AS21 writes = 0.
5. concurrency = 1; timeout >=180 s for history-heavy calls; retry timeout/502/503 up to 2 times with 20–30 s backoff.

If REAL source cannot be established, stop `BLOCKED_BY_ENVIRONMENT`.

## Phase 1 — recover exact release-forecast contract
Recover from repository code/contracts/tests the exact business definition and formula for `release-forecast`.

Determine exact required inputs, for example only if repository contract actually requires them:
- release ID and validated existence;
- target/end date;
- release start date;
- release task-key set;
- task completion timestamps;
- historical scope changes;
- throughput/velocity window;
- confidence or sample-size rules.

Do not infer the formula from the skill name. Produce an explicit dependency chain:
`raw authoritative facts -> derived inputs -> deterministic forecast output`.

## Phase 2 — discover a valid REAL release
Do not use a guessed release ID.

Use existing task-api/SWTR read paths to discover at least one release/version that is currently represented in REAL task data or release metadata.

Prove:
- exact release/version identifier;
- at least one authoritative source path returning it;
- exact task-key set if available;
- target/end date if available;
- status/name/project/space where available.

If no valid release can be discovered, classify `NO_VALID_REAL_RELEASE_AVAILABLE_FOR_PROOF`; do not fabricate one.

## Phase 3 — inventory release read surface
Trace current local task-api implementation/config/OpenAPI/routes and underlying SWTR/MCP read methods for release/version data.

Search equivalent concepts, not only exact endpoint names:
- fix version / release / version metadata;
- release dates / start date / target date / end date;
- release task membership;
- version changelog / release history / burnup / progress;
- historical task membership changes;
- completion history for release tasks.

For each candidate record exact endpoint/tool, parameters, response fields, pagination/time-range support and read-only status.

A 404 on a guessed URL is not proof the upstream capability is missing.

## Phase 4 — REAL release task/history proof
For the validated release:
1. Independently obtain the exact current release task-key set.
2. Select enough tasks to establish whether the forecast formula can be computed.
3. Retrieve REAL workflow histories and completion timestamps independently of Agent A.
4. Capture raw timestamps and task status/current completion state.
5. If contract depends on historical release scope changes, prove whether those events exist or not.

If history is sufficient, independently derive the historical completion series required by the repository formula.

## Phase 5 — independently calculate forecast if possible
Only if all contract-required authoritative inputs exist:
- independently calculate the exact expected forecast without using Harness implementation as Oracle;
- show all raw inputs and intermediate values;
- show final expected date/value/confidence exactly according to repository contract.

Then run Agent A with a natural Russian release forecast query and compare normalized business facts.

Allowed row outcomes:
- `AB_PASS`
- `PRODUCT_DEFECT_PROVEN`
- `SOURCE_DATA_OR_CAPABILITY_UNAVAILABLE`
- `EXPECTED_INSUFFICIENT_HISTORY`
- `ENVIRONMENT_BLOCKED`

HTTP 200/COMPLETED is not sufficient if facts differ.

## Phase 6 — release_timeline classification
Classify the missing `release_timeline` fact as exactly one of:
- `AVAILABLE_ALREADY_NOT_WIRED`
- `DERIVABLE_FROM_EXISTING_TASK_HISTORY`
- `DERIVABLE_WITH_SMALL_ADAPTER_EXTENSION`
- `NEW_TASK_API_FACADE_ONLY`
- `UPSTREAM_SWTR_CAPABILITY_MISSING`
- `NO_VALID_REAL_RELEASE_AVAILABLE_FOR_PROOF`

For `DERIVABLE_*`, provide concrete evidence and exact owner implementation path.

## Phase 7 — owner implementation contract
Do not change code. Produce the smallest evidence-backed owner plan.

If derivable, specify exact modules/files likely affected and a normalized contract such as:
```text
get_release_timeline(release_id, space?) -> {
  release_id,
  started_at?,
  target_at?,
  current_task_keys,
  completion_events: [{task_key, completed_at}],
  scope_events?: [...],
  evidence
}
```

Specify:
- which REAL source provides each field;
- whether a new facade endpoint is required;
- pagination/retry behavior;
- fail-closed behavior;
- when `release_timeline` can honestly be advertised;
- projected readiness (`51/54 -> 52/54`) only if proven.

If upstream gap is proven, state exactly which missing upstream field/event blocks the forecast and do not propose current-state proxies as authoritative forecast inputs unless the repository contract explicitly allows them.

## Phase 8 — protect prior conclusions
Verify:
- `sprint-carryover` and `sprint-scope-change` remain unavailable due to Assignment 104 upstream sprint-history gap;
- no new Learning Loop policy is created/promoted/changed;
- no task/release IDs or expected outputs are proposed for production hardcoding.

## Source integrity
Report exact numeric counts from this run only:
- successful REAL release reads;
- successful REAL release-task reads;
- successful REAL task-history reads;
- HTTP 500;
- HTTP 502/503;
- HTTP 404 discovery attempts;
- timeouts/retries;
- fake/mock/frozen = 0;
- AS21 writes = 0.

## Output
Create only QA/research artifacts under `po-agent-platform-v2/qa_reports/`.

Primary report:
`po-agent-platform-v2/qa_reports/RELEASE_TIMELINE_SOURCE_PROOF_105.md`

Allowed final verdicts:
- `RELEASE_TIMELINE_DERIVATION_PROVEN_READY_FOR_OWNER`
- `PARTIAL_RELEASE_TIMELINE_PATH_PROVEN`
- `UPSTREAM_RELEASE_TIMELINE_GAP_PROVEN`
- `NO_VALID_REAL_RELEASE_AVAILABLE_FOR_PROOF`
- `PRODUCT_DEFECTS_PROVEN`
- `BLOCKED_BY_ENVIRONMENT`

Commit/push only allowed QA/research artifacts, report final SHA, then STOP. Do not modify production code and do not start Assignment 106 or later.