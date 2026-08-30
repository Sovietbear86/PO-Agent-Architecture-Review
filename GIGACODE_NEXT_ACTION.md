# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_098_FULL_POST_CHANGE_AB_CERTIFICATION`

## Role boundary — mandatory
You are QA/tester only. **Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

Owner production change under certification: commit `4c052f269eb3d743682a934425cb86b95492ffe9`.

Assignment 097 is GREEN. Assignment 098 is the broad post-change certification required before considering the current backend/source-contract state certified.

## Goal
Run a complete 54-skill backend certification against REAL AS21/SWTR using independent A/B Oracle comparison where source-backed business facts are available, while correctly treating documented source limitations as expected typed unavailable behavior rather than product failure.

Do not fix anything. Do not promote Learning Loop policies. Do not change source data.

## Execution model
- production `task-api` + REAL AS21/SWTR;
- concurrency = 1;
- request timeout >= 120 s;
- for known heavy calls allow up to 180 s;
- retry timeout/HTTP 502 up to 2 times with 20–30 s backoff;
- 40–60+ s per SWTR request is normal and must not be treated as a failure;
- fake/mock/frozen authoritative calls = 0;
- AS21 writes = 0;
- resumable/background execution is allowed and encouraged;
- checkpoint progress so an interrupted marathon can resume without repeating successful cases unnecessarily.

## Phase 0 — provenance and environment gate
1. Pull current branch and record exact HEAD.
2. Confirm owner change `4c052f269eb3d743682a934425cb86b95492ffe9` is in HEAD ancestry.
3. `git status --short` must be clean before testing.
4. Record runtime PID/start time, adapter mode, source health, source facts, skill catalog counts, Learning Loop policy count/active versions.
5. Preflight REAL AS21 with at least:
   - exact task lookup for a known-valid task;
   - `sprint-health` for a valid sprint;
   - one team/source-backed query.
6. If preflight cannot establish healthy REAL reads after retry policy, stop as `BLOCKED_BY_ENVIRONMENT`.

## Phase 1 — recover the authoritative 54-skill test surface
Use the repository skill catalog/master test plan. The denominator must be exactly 54 user-facing skills.

For each skill record:
- skill id;
- domain;
- required slots;
- source facts required;
- whether history/snapshot/write/LLM is required;
- expected response class for valid source conditions;
- documented expected unavailable/clarification behavior.

Do not invent unsupported contracts from memory.

## Phase 2 — realistic canonical queries
For every skill construct at least one realistic Russian end-user query using currently valid REAL entities where the contract requires them.

Rules:
- validate task/sprint/release/person/status/product identifiers before using them;
- a malformed QA query is a QA defect, not a product defect;
- do not reuse one hardcoded person/entity where an independent second entity is required for anti-hardcoding checks;
- for source-limited skills, use a valid query and verify the documented typed limitation rather than manufacturing a fake expected number.

## Phase 3 — Agent A / Oracle B

### A — Agent under test
For each source-backed skill capture where applicable:
- query/session_id;
- resolved intent/skill/version;
- semantic frame and grounded slots;
- capability args;
- source calls/evidence IDs;
- status;
- normalized business facts;
- warnings/data contract;
- elapsed time.

### B — independent Oracle
Independently query REAL AS21/SWTR/task-api and derive the expected business facts without using the Harness answer as authority and without reusing the same Harness deterministic calculation implementation as the Oracle.

Compare normalized business facts, not wording.

For task collections, exact task-key-set equality is the primary correctness check, not merely count equality.

For numeric metrics, compare exact independently derived inputs/formula/result when the authoritative inputs exist.

For documented source limitations, independently prove the missing source contract and verify that Agent A returns typed unavailable/fail-closed behavior with no invented metric.

## Phase 4 — verdict classes per skill
Use exactly one of:
- `AB_PASS`
- `AB_PASS_SOURCE_CAPABILITY_UNAVAILABLE`
- `EXPECTED_CLARIFICATION`
- `EXPECTED_UNAVAILABLE`
- `PRODUCT_DEFECT_PROVEN`
- `QA_HARNESS_ORACLE_DEFECT`
- `ENVIRONMENT_BLOCKED`

`HTTP 200`, `COMPLETED`, or non-empty prose does NOT override an A/B mismatch.

A product defect requires evidence of the first actual product divergence from authoritative/independent expected facts.

## Phase 5 — mandatory focused protections
In addition to the 54 canonical skill rows, explicitly include these regression protections:

### Semantic/history cases
- second valid exact task ID;
- nonexistent exact task ID must not hallucinate a task;
- sprint ID only;
- sprint + person;
- sprint + status;
- person only;
- status only;
- person + product + status where supported;
- independent second team member to detect person-specific hardcoding;
- correction turn: new status replaces old status while unaffected slots survive.

### Sprint baseline fix protection
For `sprint-carryover` and `sprint-scope-change`:
- correct skill/capability must be reached;
- no invented metric;
- current source must still independently prove missing historical commitment baseline unless source contract has genuinely changed;
- expected current disposition is `AB_PASS_SOURCE_CAPABILITY_UNAVAILABLE` if snapshot remains unavailable;
- if snapshot becomes available, independently calculate and compare the real metric instead of forcing unavailable.

### Neighboring sprint protection
- `sprint-scope` exact task-key-set equality;
- `sprint-predictability` documented proxy semantics preserved;
- cycle/lead time history semantics preserved;
- risk queue no regression.

### Team workload anomaly protection
Run `team-workload` for a valid scope and independently compare:
- member set/count;
- active task key set/count;
- per-member counts;
- blocked/WIP fields if in contract.

If Agent returns zero and Oracle also proves zero, classify PASS. Never teach a rule that zero is impossible.

## Phase 6 — Learning Loop protection
Before and after the full certification record:
- total policies;
- active policies;
- active versions.

Testing must not create/promote/change policies merely because a source capability is unavailable or a deterministic implementation is wrong.

If a genuine semantic/policy candidate is discovered, report it only; do not promote or repair it in Assignment 098.

## Phase 7 — FIRST_FAILING_BOUNDARY
For every non-pass/non-expected row identify the earliest proven boundary from:
- `SEMANTIC_INTERPRETATION`
- `SKILL_RESOLUTION`
- `ENTITY_GROUNDING`
- `CAPABILITY_ARGUMENT_BUILDING`
- `CAPABILITY_ROUTING`
- `SOURCE_CONTRACT`
- `SOURCE_DATA_MISSING`
- `DETERMINISTIC_CALCULATION`
- `RESPONSE_STATUS_MAPPING`
- `LEARNING_POLICY_APPLICATION`
- `QA_HARNESS_ORACLE_DEFECT`

Do not infer a downstream boundary when an earlier boundary already failed.

## Phase 8 — QA methodology audit
Verify:
- denominator exactly 54;
- every skill has an actual executed canonical case;
- reported counts sum to 54;
- duration is derived from real timestamps;
- source counters come from raw evidence/checkpoint, not placeholders;
- no unresolved template placeholders such as `{data[...]}` remain in the report;
- runner did not use Harness A as Oracle B;
- QA query-generation/classification defects are reported separately from product defects.

## Phase 9 — source integrity
Record:
- HTTP 500 count/endpoints;
- HTTP 502 count/endpoints;
- timeouts/retries;
- successful REAL AS21 reads;
- fake/mock/frozen authoritative calls = 0;
- AS21 writes = 0.

## Acceptance logic
Current backend/source-contract state is certified GREEN only if:
- no `PRODUCT_DEFECT_PROVEN` rows remain;
- no unexplained A/B mismatches remain;
- documented source limitations are correctly typed/fail-closed;
- semantic regression pack is clean or only contains contract-valid clarification/unavailable outcomes;
- Learning Loop state is unchanged by the test run;
- QA methodology audit is clean enough to trust the result.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/FULL_POST_CHANGE_AB_CERTIFICATION_098.md`

Checkpoint:
`po-agent-platform-v2/qa_reports/FULL_POST_CHANGE_AB_CERTIFICATION_098_checkpoint.json`

Optional raw evidence prefix:
`FULL_POST_CHANGE_AB_CERTIFICATION_098_`

Allowed final verdicts:
- `BACKEND_CERTIFIED_GREEN`
- `PRODUCT_DEFECTS_PROVEN`
- `MIXED_PRODUCT_AND_QA_DEFECTS`
- `QA_HARNESS_DEFECTS_ONLY`
- `BLOCKED_BY_ENVIRONMENT`

Commit and push only allowed QA artifacts. Verify the primary report exists in remote HEAD, report final SHA and STOP.

Do not modify production code and do not start any later assignment.