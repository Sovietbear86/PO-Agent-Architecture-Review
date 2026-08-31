# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_101_SOURCE_CAPABILITY_DISCOVERY`

## Role boundary
You are QA/research executor only. **Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

Assignment 100 established a trusted baseline: REAL AS21/SWTR is reachable and the current backend is GREEN for the source contract that exists today. We now move to the next product objective: reduce the current `47 ready / 7 unavailable` state toward `54/54` by proving what historical source facts AS21/SWTR can actually provide and what minimal read-layer additions are required.

Do not accept `source_capability_unavailable` as the end state. In this assignment, investigate the source deeply enough to determine whether the missing facts already exist under another REAL AS21/SWTR endpoint/field/event model or truly require a new task-api facade endpoint.

## Exact seven unavailable skills
According to source readiness, investigate:
1. `task-history`
2. `task-time-in-status`
3. `sprint-cycle-time`
4. `sprint-lead-time`
5. `sprint-carryover`
6. `sprint-scope-change`
7. `release-forecast`

They depend on three missing authoritative source facts:
- `history`
- `sprint_snapshots`
- `release_timeline`

## Phase 0 — provenance and live-source gate
1. Pull current branch; record exact HEAD and clean `git status --short`.
2. Fresh production `task-api` + REAL AS21/SWTR only.
3. Prove at least 3 successful REAL reads before historical discovery, including one task point-read and one sprint-scope read.
4. fake/mock/frozen authoritative calls = 0; AS21 writes = 0.
5. Use >=120 s timeout and retry timeout/502 up to 2 times.

If REAL reads cannot be established, stop `BLOCKED_BY_ENVIRONMENT`.

## Phase 1 — recover exact business/source contracts
For each of the seven skills, recover from repository contracts/code/tests:
- exact business definition;
- required source fields/events;
- whether point-in-time snapshot is required or event history is sufficient to derive it;
- exact deterministic formula/aggregation expected once data exists;
- current handler/source guard and why readiness marks it unavailable.

Build a dependency table:
`skill -> required fact -> minimal authoritative raw inputs -> derived values -> output`.

Do not infer formulas from skill names alone.

## Phase 2 — inventory current task-api and underlying SWTR read surface
Inspect the actual local task-api implementation/config/OpenAPI/routes and the underlying SWTR client/read methods used by it.

For each candidate historical capability, record:
- existing task-api route if any;
- underlying SWTR method/endpoint if any;
- request parameters;
- response fields;
- whether it is currently exposed through the PO Agent adapter;
- whether endpoint is read-only;
- whether pagination/time range is supported.

Search specifically for equivalent concepts, not only exact names:
- task changelog / audit / lifecycle / status transitions / activity / journal / event history;
- sprint metadata including start/end dates;
- sprint membership changes / task added-to-sprint and removed-from-sprint events;
- previous sprint membership;
- sprint version/audit/snapshot/commitment/baseline;
- release start/end/target dates;
- release task-history/timeline/burnup/completion history.

A 404 on a guessed facade URL is NOT proof that SWTR lacks the data. Trace through task-api/SWTR code and probe the actual available read surface.

## Phase 3 — REAL task history proof
Choose at least two valid REAL tasks, preferably one with nontrivial lifecycle.

Independently attempt to retrieve authoritative history/status-transition data.

Required evidence if available:
- exact source path/method;
- raw event identifiers/timestamps;
- from/to statuses or equivalent;
- creation timestamp;
- completion timestamp if available;
- enough evidence to derive `time-in-status`, cycle time and lead time without Harness output.

Then classify the `history` source fact:
- `AVAILABLE_ALREADY_NOT_WIRED`
- `DERIVABLE_FROM_EXISTING_SWTR_READS`
- `NEW_TASK_API_FACADE_ONLY`
- `UPSTREAM_SWTR_CAPABILITY_MISSING`

If derivable, show an independent calculation for at least one real task.

## Phase 4 — REAL sprint historical baseline proof
Using a validated REAL sprint such as `DMS-SPRNT-2` plus, where possible, a completed/older sprint, investigate whether authoritative sprint-start membership can be reconstructed.

Prove availability or absence of:
- sprint start/end timestamps;
- current membership;
- add/remove membership events with timestamps;
- previous-sprint membership;
- immutable/versioned sprint state;
- task history events containing sprint assignment changes.

Important: a dedicated `/snapshot` endpoint is NOT mandatory if the same authoritative baseline can be deterministically reconstructed from an event stream.

If sufficient data exists, independently reconstruct:
- committed task-key set at sprint start;
- added-after-start key set;
- removed-after-start key set;
- carryover key set according to repository business definition.

Classify `sprint_snapshots` as:
- `AVAILABLE_ALREADY_NOT_WIRED`
- `DERIVABLE_FROM_EXISTING_HISTORY`
- `NEW_TASK_API_FACADE_ONLY`
- `UPSTREAM_SWTR_CAPABILITY_MISSING`

## Phase 5 — REAL release timeline proof
Use a validated REAL release if one exists. Do not use a guessed release ID.

Investigate:
- release metadata/dates;
- release task scope;
- task completion timestamps/history;
- historical scope changes if forecast contract needs them;
- any release progress/burnup/timeline endpoint.

Determine whether `release-forecast` can be computed from existing authoritative reads once history is wired, or whether a separate release timeline source is truly required.

Classify `release_timeline` as:
- `AVAILABLE_ALREADY_NOT_WIRED`
- `DERIVABLE_FROM_EXISTING_TASK_HISTORY`
- `NEW_TASK_API_FACADE_ONLY`
- `UPSTREAM_SWTR_CAPABILITY_MISSING`
- `NO_VALID_REAL_RELEASE_AVAILABLE_FOR_PROOF`

## Phase 6 — implementation plan for owner
Do NOT change code. Produce the smallest evidence-backed implementation plan.

Prioritize reuse. Prefer one generalized authoritative event/history source that unlocks multiple skills over bespoke endpoints per skill.

For each proposed owner change give:
- exact repo/file/module likely affected;
- new or extended adapter/source contract;
- task-api facade endpoint only if actually necessary;
- normalized response schema;
- pagination/time-range requirements;
- fail-closed/error behavior;
- which of the seven skills it unlocks;
- expected readiness change (`47/54 -> X/54`).

Provide three tiers:
- `P0`: maximum skill unlock with minimum source work;
- `P1`: next source extension;
- `P2`: only if upstream SWTR lacks required facts.

## Phase 7 — no hardcoding / no learning
Verify:
- no new Learning Loop policy created/promoted/changed;
- no task/sprint/release IDs or expected answers are proposed for production hardcoding;
- all proposed calculations depend on authoritative source fields/events.

## Source integrity
Report exact counts for this run:
- successful REAL AS21 reads;
- HTTP 500/502/timeouts/retries;
- HTTP 404s separately as endpoint-discovery evidence;
- fake/mock/frozen authoritative calls = 0;
- AS21 writes = 0.

## Output
Create only QA/research artifacts under `po-agent-platform-v2/qa_reports/`.

Primary report:
`po-agent-platform-v2/qa_reports/SOURCE_CAPABILITY_DISCOVERY_101.md`

Optional raw evidence prefix:
`SOURCE_CAPABILITY_DISCOVERY_101_`

Final verdict must be one of:
- `SOURCE_PATHS_FOUND_READY_FOR_OWNER_IMPLEMENTATION`
- `PARTIAL_SOURCE_PATHS_FOUND`
- `UPSTREAM_SOURCE_GAPS_PROVEN`
- `BLOCKED_BY_ENVIRONMENT`

The report must end with a 7-row table:
`skill | current missing fact | discovered authoritative path | classification | owner change | projected readiness`.

Commit/push only allowed QA/research artifacts, report final SHA, then STOP. Do not modify production code and do not start a later assignment.