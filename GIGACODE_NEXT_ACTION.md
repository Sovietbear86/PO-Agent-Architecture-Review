# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_102_HISTORY_WIRING_POST_CHANGE_AB`

## Role boundary
You are QA/tester only. **Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

Assignment 101 proved that authoritative task history already exists through REAL task-api/MCP-SWTR and that the production adapter was not advertising the proven `history` source fact. The owner has now wired that fact into the adapter hierarchy used by the production runtime.

Owner commits under test:
- `948577aeabe04da50ea248b266d5c18e3688fe4b`
- `3a35d698f81c0da74392c0803ff6080f0338b26d`
- `21cfdf8c2a3191ec8096d46f3db38bad8fa406c9`

This assignment is the mandatory post-change A/B certification. Do not start P1 sprint-snapshot or release-timeline implementation yet.

## Goal
Prove that the production runtime moves from `47/54` toward `51/54` by making these four history-backed skills genuinely source-ready and executable against REAL AS21:
1. `task-history`
2. `task-time-in-status`
3. `sprint-cycle-time`
4. `sprint-lead-time`

Do not count a skill as unlocked merely because `source_facts` contains `history`. It must execute against REAL history and agree with an independent Oracle.

## Phase 0 — fresh runtime and provenance
1. Pull the current branch and record exact HEAD.
2. Verify all three owner commits are in HEAD ancestry.
3. Require clean `git status --short` before testing.
4. Fully restart production task-api and Harness; record old/new PIDs and start times.
5. Confirm mode `task-api` + REAL AS21/SWTR.
6. Record source readiness before runtime execution: available facts and ready/unavailable counts.
7. fake/mock/frozen authoritative calls = 0; AS21 writes = 0.
8. Use >=120 s timeout; for history-heavy calls allow 180 s. Retry timeout/502 up to 2 times with 20–30 s backoff.

If REAL reads cannot be established, stop `BLOCKED_BY_ENVIRONMENT`.

## Phase 1 — owner-change integrity audit
Before functional testing, audit the exact diff from Assignment 101 HEAD `ef8a5b05a8ecdd7f2de85fa0dcca3a5e49d78f90` to current HEAD.

Verify:
- `TaskApiAS21Adapter.get_task_history()` still exists and preserves its prior behavior;
- `history` is declared in the base adapter fact set;
- production adapter fact propagation includes `history`;
- the concrete production runtime adapter `EvidenceValidatedProductionTaskApiAS21Adapter` includes `history` despite its hardened parent fact override;
- no unrelated production behavior was removed or changed in task lookup, search, sprint reads, attachment reads, QA fault handling, or source error mapping.

If the owner diff accidentally altered unrelated behavior, classify `OWNER_CHANGE_REGRESSION` and identify the exact changed boundary. Do not fix it.

## Phase 2 — mandatory REAL history preflight
Independently query REAL task-api/SWTR before calling the Agent.

Select at least two currently valid REAL tasks with non-empty workflow history. At least one must contain a real status transition.

For each task capture:
- task key;
- direct point-read status/title;
- exact history endpoint/request;
- HTTP status;
- ordered workflow-status transition events;
- timestamps;
- from/to normalized status values;
- actor where present;
- elapsed time.

Preflight requires at least 2 successful REAL history reads. Static source-fact declaration is not evidence.

## Phase 3 — task-history A/B
For one validated task with nontrivial history:

### Agent A
Use a natural Russian query asking for task history.
Capture query/session, intent, skill/version, status, warnings, data, evidence, answer, source calls and elapsed time.

### Oracle B
Use the independent REAL history read from Phase 2.
Compare:
- task identity;
- transition count if in contract;
- ordered from/to status sequence;
- timestamps where exposed;
- no fabricated transitions.

Verdict must be `AB_PASS` only if business facts agree.

## Phase 4 — task-time-in-status A/B
For the same or another validated task, independently calculate time-in-status from REAL transition timestamps without using Harness calculation code.

Capture exact Oracle calculation intervals and totals according to repository contract. Compare Agent output to Oracle.

If history exists but the product calculates incorrectly, classify `PRODUCT_DEFECT_PROVEN` at `DETERMINISTIC_CALCULATION`.

If the task does not contain enough events for a meaningful calculation, choose another REAL task rather than declaring the capability unavailable.

## Phase 5 — sprint-cycle-time / sprint-lead-time A/B
Use a validated REAL sprint. Obtain the exact current task-key set directly from AS21.

For each sprint task needed by the metric, retrieve REAL task history independently and determine whether the repository formula has enough authoritative inputs.

For each metric:
- show the exact sample task-key set;
- show raw timestamps used;
- independently calculate expected per-task values and aggregate result;
- compare Agent A result to Oracle B;
- distinguish valid `insufficient_history` for a genuinely insufficient sample from a product failure.

Do not classify these skills as unlocked merely because the source guard no longer rejects them. At least one history-backed computation path must be proven against REAL events if the source corpus permits it.

## Phase 6 — readiness proof
After the fresh runtime is built, record:
- exact `available_facts`;
- ready count;
- unavailable count;
- readiness rows for all seven historically blocked skills.

Expected structural outcome after this owner change:
- `history` is available;
- the four history-backed skills are no longer unavailable due to missing `history`;
- `sprint-carryover` and `sprint-scope-change` remain unavailable only because `sprint_snapshots` is missing;
- `release-forecast` remains unavailable only because `release_timeline` is missing.

Expected readiness target: `51/54`, unless the repository's authoritative readiness model yields a different evidence-backed count. If different, explain exactly why.

## Phase 7 — regression controls
On the same fresh runtime re-run at minimum:
- exact `task-lookup` for one Phase-2 task and compare core facts to Oracle;
- `sprint-scope` exact task-key set equality;
- attachment read for a task with attachment metadata if one is available without broad discovery cost;
- `sprint-carryover` or `scope-change` still returns typed source limitation for missing `sprint_snapshots`, not a fabricated metric.

## Phase 8 — Learning Loop protection
Capture exact policy store before and after:
- total policies;
- promoted/active policies;
- exact active IDs/versions;
- immutable hash or equivalent snapshot.

History wiring and deterministic history calculations must not create/promote/change a policy merely to compensate for source or implementation behavior.

## FIRST_FAILING_BOUNDARY
For every failed/non-expected row identify the earliest proven boundary:
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
- `OWNER_CHANGE_REGRESSION`
- `QA_HARNESS_ORACLE_DEFECT`

## Source integrity
Report exact counts from this run:
- successful REAL task point reads;
- successful REAL history reads;
- successful REAL sprint reads;
- HTTP 500/502/timeouts/retries;
- fake/mock/frozen authoritative calls = 0;
- AS21 writes = 0.

## Output
Create only QA artifacts under `po-agent-platform-v2/qa_reports/`.

Primary report:
`po-agent-platform-v2/qa_reports/HISTORY_WIRING_POST_CHANGE_AB_102.md`

Optional raw evidence prefix:
`HISTORY_WIRING_POST_CHANGE_AB_102_`

Allowed final verdicts:
- `HISTORY_4_SKILLS_CERTIFIED_51_OF_54`
- `PARTIAL_HISTORY_UNLOCK`
- `PRODUCT_DEFECTS_PROVEN`
- `OWNER_CHANGE_REGRESSION`
- `AB_MISMATCH`
- `BLOCKED_BY_ENVIRONMENT`

GREEN-equivalent `HISTORY_4_SKILLS_CERTIFIED_51_OF_54` requires:
- fresh runtime;
- >=2 successful independent REAL history reads;
- task-history A/B pass;
- task-time-in-status A/B pass;
- cycle/lead-time paths correctly use REAL history and match Oracle where source data is sufficient, otherwise only contract-valid insufficient-history outcomes;
- readiness reflects history as available and the remaining three gaps only;
- regression controls pass;
- Learning Loop unchanged;
- fake/mock/frozen=0 and AS21 writes=0.

Commit/push only allowed QA artifacts, report final SHA, then STOP. Do not modify production code and do not start Assignment 103 or later.