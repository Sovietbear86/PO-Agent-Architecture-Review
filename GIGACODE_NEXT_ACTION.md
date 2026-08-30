# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_097_POST_CHANGE_SPRINT_BASELINE_AB`

## Role boundary — mandatory
You are QA/tester only. **Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

Owner production change under test: commit `4c052f269eb3d743682a934425cb86b95492ffe9`.

This is the mandatory post-change A/B certification required by `po-agent-platform-v2/docs/testing/POST_CHANGE_AB_ORACLE_CERTIFICATION.md`.

## Purpose
Verify the minimal owner fix for the 096A `IMPLEMENTATION_CONTRACT_MISMATCH` without pretending that carryover/scope-change can be calculated from current scope alone.

Expected design after the fix:
- `sprint-carryover` is registered and executable;
- `sprint-scope-change` is registered and executable;
- deterministic routing can reach both;
- REAL current sprint scope may be read to prove the sprint;
- authoritative historical commitment baseline is still unavailable;
- the runtime must fail closed as `source_capability_unavailable` / `authoritative_commitment_baseline_unavailable` and must NOT invent a number;
- no Learning Loop policy should be created, promoted, changed, or applied because this is a source-contract limitation.

## Phase 0 — provenance
1. Pull current branch and record exact HEAD.
2. Confirm owner change `4c052f269eb3d743682a934425cb86b95492ffe9` is in HEAD ancestry.
3. `git status --short` must be clean before testing.
4. Record changed production files since 096A QA HEAD; expected owner production change is `po-agent-platform-v2/src/po_agent/harness/runtime.py` only.
5. Production `task-api` + REAL AS21(SWTR), fake/mock/frozen authoritative calls = 0, AS21 writes = 0.

## Phase 1 — static implementation proof
For both `sprint-carryover` and `sprint-scope-change`, prove from exact HEAD:
- skill registry contains the skill;
- capability registry contains `sprint.carryover` / `sprint.scope_change`;
- deterministic router maps explicit carryover/scope-change wording to the correct intent;
- execution no longer fails at `SKILL_RESOLUTION` or `CAPABILITY_ROUTING`;
- handler deliberately requires authoritative baseline instead of calculating from current task list.

Any `semantic_skill_unavailable`, `capability not allow-listed`, or generic `runtime_failure` is an immediate regression.

## Phase 2 — focused A/B with REAL sprint
Use a currently valid REAL sprint, preferably `DMS-SPRNT-2` if still valid.

Run at least these A queries:
1. `Покажи carryover спринта DMS-SPRNT-2`
2. `Покажи scope-change спринта DMS-SPRNT-2`
3. one natural Russian paraphrase for each metric.

For Agent A capture:
- query/session;
- resolved intent/skill/version;
- capability ID;
- grounded `sprint_id`;
- REAL source calls/evidence;
- status;
- data;
- warnings;
- answer;
- elapsed time.

### Independent Oracle B
Independently query REAL AS21/SWTR/task-api for the same sprint and prove:
- current sprint task set is available;
- authoritative historical commitment baseline / sprint-start snapshot is unavailable through the current production source contract;
- therefore no exact carryover/scope-change value can be independently calculated.

Do not use Harness output as Oracle and do not treat the current task list as a historical baseline.

### Required A/B verdict
For both skills the correct result is:
`AB_PASS_SOURCE_CAPABILITY_UNAVAILABLE`

Pass conditions:
- correct skill reached;
- no invented numeric metric;
- warning contains `source_capability_unavailable`;
- warning contains `authoritative_commitment_baseline_unavailable` or equivalently explicit structured reason;
- structured data identifies `SOURCE_CAPABILITY_UNAVAILABLE` or equivalent typed source limitation;
- Oracle independently confirms required baseline is unavailable.

A top-level `FAILED` status alone is not sufficient to fail this assignment if the existing response-status enum still uses FAILED for typed source-capability failure. Classify by the structured warning/data contract. However explicitly record this status-model limitation as technical debt; do not modify it.

## Phase 3 — neighboring sprint regression
A/B retest at minimum:
- `sprint-scope` on the same sprint -> AB_PASS with exact task-key-set equality;
- `sprint-predictability` -> existing documented proxy semantics preserved;
- `sprint-cycle-time` or `sprint-lead-time` -> no regression in history-backed path;
- `sprint-risk-queue` -> no regression.

Do not broaden to the full 54-skill marathon yet.

## Phase 4 — semantic and Learning Loop protection
Verify:
- explicit `scope-change` is not accidentally routed to plain `sprint-scope`;
- explicit `carryover` is not routed to `sprint-health` or generic task search;
- no learned semantic policy is created/promoted/changed during these source-unavailable responses;
- active policy count/version before and after is unchanged.

## Phase 5 — FIRST_FAILING_BOUNDARY after owner fix
Expected chain for both source-limited skills:
`query -> semantic -> skill -> grounding -> capability args -> capability execution -> REAL current-scope validation -> SOURCE_CONTRACT unavailable`

Expected boundary:
`SOURCE_CONTRACT`

The old `CAPABILITY_ROUTING / IMPLEMENTATION_CONTRACT_MISMATCH` must be proven closed.

## Source integrity
Record:
- HTTP 500 count;
- HTTP 502 count/endpoints;
- timeouts/retries;
- REAL AS21 reads;
- fake/mock/frozen authoritative calls = 0;
- AS21 writes = 0.

Use >=120 s timeout; source calls may take 40–60+ s. Retry timeout/502 up to 2 times.

## Output
Create only QA artifacts under `po-agent-platform-v2/qa_reports/`.

Primary report:
`po-agent-platform-v2/qa_reports/POST_CHANGE_SPRINT_BASELINE_AB_097.md`

Optional raw evidence prefix:
`POST_CHANGE_SPRINT_BASELINE_AB_097_`

Allowed final verdicts:
- `GREEN_SOURCE_LIMITATION_HANDLED_CORRECTLY`
- `PRODUCT_REGRESSION`
- `AB_MISMATCH`
- `BLOCKED_BY_ENVIRONMENT`

GREEN requires both target skills to reach the registered capability and fail closed for the independently proven missing historical baseline, with no invented metrics and no neighboring regression.

Commit/push only allowed QA artifacts, report final SHA, then STOP. Do not start any later assignment.