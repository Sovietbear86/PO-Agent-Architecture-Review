# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_095C_FAILURE_TRIAGE`

## Role boundary — mandatory
You are QA/tester only. **Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, or this file.**

If a defect is found, prove `FIRST_FAILING_BOUNDARY` and report it. Do not repair it.

## Why 095C exists

The latest 095 background run finally reached REAL AS21 successfully:
- 54 skills represented;
- 162 REAL AS21 reads;
- HTTP 500 = 0;
- HTTP 502 = 0;
- fake/mock/frozen = 0;
- AS21 writes = 0;
- result: 25 PASS / 9 FAIL / 20 BLOCKED.

This is useful evidence, but the reported root cause for the 9 FAIL rows was not proven. Statements such as "backend metrics not implemented" or "additional data missing" are hypotheses, not a `FIRST_FAILING_BOUNDARY`.

Assignment 095C is therefore a **targeted failure/blocker triage only**. Do not rerun the whole 54-skill marathon unless a specific trace requires comparison with a known-green skill.

## Scope

Investigate exactly:

### A. 9 FAIL rows
1. `sprint-throughput`
2. `sprint-wip`
3. `sprint-cycle-time`
4. `sprint-lead-time`
5. `sprint-carryover`
6. `sprint-scope-change`
7. `sprint-predictability`
8. `sprint-risk-queue`
9. `release-forecast`

### B. 20 BLOCKED rows from the latest report
Triage each blocked row and classify it as exactly one of:
- `BAD_QA_QUERY_OR_MISSING_REQUIRED_SLOT`
- `EXPECTED_CLARIFICATION`
- `SOURCE_CAPABILITY_UNAVAILABLE_BY_DESIGN`
- `ENVIRONMENT_BLOCKED`
- `PRODUCT_DEFECT_PROVEN`
- `NOT_BLOCKED_AFTER_VALID_RETEST`

Do not automatically treat `NEEDS_CLARIFICATION` as failure. First compare it with the skill contract and required slots.

## Phase 0 — clean provenance

1. Pull current branch and record exact HEAD.
2. Record `git status --short`; production files must remain clean.
3. Restart/verify the same production runtime used by successful 095 background testing.
4. Confirm `task-api` + REAL AS21 mode.
5. Confirm fake/mock/frozen authoritative calls = 0 and AS21 writes = 0.
6. Reuse valid REAL entities discovered in previous successful runs, but revalidate them against current REAL AS21 before using them.

## Phase 1 — recover the real contract for every suspect skill

For each of the 29 suspect rows (9 FAIL + 20 BLOCKED), inspect the production catalog/skill definition and record:
- `skill_id`;
- required slots;
- optional slots;
- expected source facts/capabilities;
- whether a sprint/release/task/member identifier is mandatory;
- expected clarification behavior when a required value is absent;
- expected deterministic output/metric;
- whether history/changelog or another currently unavailable source is required.

Then compare the query used in the previous 095 report with the actual skill contract.

If the previous query was synthetic/invalid (for example query text that merely names the skill rather than a realistic user intent), do not call the product defective. Build a valid natural-language query using REAL source entities and retest.

## Phase 2 — targeted real-user retest

For each suspect skill construct:
1. one realistic canonical Russian user query that satisfies required slots;
2. one natural paraphrase;
3. only where relevant, one missing-slot query to verify expected clarification.

Use REAL valid entities from AS21:
- real sprint IDs for sprint skills;
- real release identifier/name for release skills;
- real task IDs for task analysis skills;
- real member identity where required.

Per request timeout >=120 sec; heavy metric/history/release requests may use up to 180 sec. Retry timeout/502 up to 2 times. 40–60+ sec is normal latency.

For every retest record exact query, session_id, elapsed time, resolved skill, semantic frame/slots, capability arguments, source calls, source response summary, final status and evidence IDs.

## Phase 3 — boundary trace for every remaining FAIL

For each skill that still fails with a contract-valid query and valid REAL entity, trace the production path:

`user query`
`-> semantic interpretation`
`-> resolved skill`
`-> grounded slots`
`-> capability arguments`
`-> REAL source call(s)`
`-> source response/data availability`
`-> deterministic calculation/skill execution`
`-> response status`

Identify the **first boundary where expected and actual diverge**.

Allowed `FIRST_FAILING_BOUNDARY` examples include:
- `SEMANTIC_INTERPRETATION`
- `SKILL_RESOLUTION`
- `ENTITY_GROUNDING`
- `CAPABILITY_ARGUMENT_BUILDING`
- `SOURCE_CONTRACT`
- `SOURCE_DATA_MISSING`
- `DETERMINISTIC_METRIC_CALCULATION`
- `RESPONSE_STATUS_MAPPING`

Do not use vague labels such as "SWTR backend" unless you show the exact request, response and missing/incorrect field that first proves the failure.

## Phase 4 — Sprint Intelligence cluster deep dive

The eight sprint metric FAILs may share one boundary, but do not assume that.

For each of the 8 skills:
- use the same known-valid REAL sprint where the metric contract permits it;
- capture the exact underlying task key set used by the metric;
- capture required source fields for the metric;
- compare source availability vs calculation requirements;
- if the metric fails, identify the exact first missing/invalid input or calculation branch.

Explicitly distinguish:
- metric mathematically computes wrong value;
- required historical fields are unavailable from current task-api source contract;
- correct behavior should be `UNAVAILABLE/NEEDS_CLARIFICATION` rather than `FAILED`;
- QA used an invalid sprint/query;
- product implementation genuinely throws/fails despite sufficient source data.

If several skills share one proven boundary, group them into one defect cluster with per-skill evidence.

## Phase 5 — Release Forecast deep dive

For `release-forecast`:
- discover a REAL valid release from source;
- verify the exact forecast input contract;
- use a valid natural user query;
- trace release grounding, release scope/task set, required metric/history inputs and calculation result;
- identify the first failing boundary if it remains FAIL.

Do not infer a defect solely from a generic "Покажи данные по release-forecast" style request.

## Phase 6 — blocked-row disposition

For all 20 previously BLOCKED skills, produce a disposition table:

| Skill | Previous status | Contract-valid query used now | Current status | Classification | Evidence |

A row that correctly asks for clarification because the user omitted a mandatory entity should be `EXPECTED_CLARIFICATION`, not product RED.

A source requirement genuinely absent from production `task-api` (for example required history capability) should be `SOURCE_CAPABILITY_UNAVAILABLE_BY_DESIGN` unless the product contract explicitly promises it in the current release.

If the skill becomes successful after using a valid query/entity, classify `NOT_BLOCKED_AFTER_VALID_RETEST`.

## Phase 7 — validate previous 095 methodology

Audit the previous 095 report itself:
- reconcile 25 PASS + 9 FAIL + 20 BLOCKED = 54;
- explain the suspicious `Duration: 0.00 hours` despite 162 REAL reads;
- determine whether the background runner wrote synthesized/result rows without actually waiting for every runtime call, or whether only report timing metadata was wrong;
- verify whether canonical/paraphrase/edge statuses in the report came from actual individual API calls;
- verify that skill IDs and categories/counts are internally consistent.

If the runner/report generator itself produced misleading certification data, call this a **QA HARNESS DEFECT**, not a production Harness defect, and identify the exact evidence.

Do not modify the QA runner during this assignment; only diagnose it.

## Phase 8 — learning applicability correction

The previous report changed many skills from learning N/A to applicable without per-skill proof.

For each suspect skill in 095C, record whether learning is actually applicable according to production policy/catalog/runtime evidence. Do not run the full persistent learning lifecycle again unless needed to resolve ambiguity.

This phase is classification/evidence only; Assignment 072 already proved the learning mechanism itself.

## Source integrity

For this focused run record:
- HTTP 500 count;
- HTTP 502 count + endpoints;
- timeout/retry count;
- REAL AS21 successful reads;
- fake/mock/frozen authoritative calls = 0;
- AS21 writes = 0.

## Final outputs

Create only QA artifacts under `po-agent-platform-v2/qa_reports/`.

Primary report:
`po-agent-platform-v2/qa_reports/TOTAL_BACKEND_FAILURE_TRIAGE_095C.md`

Optional raw trace artifact(s), if required:
`TOTAL_BACKEND_FAILURE_TRIAGE_095C_*`

The report must include:
- tested HEAD/runtime provenance;
- exact commands;
- suspect-skill contract matrix;
- previous-query-vs-valid-query comparison;
- targeted retest results;
- blocked-row disposition table;
- exact `FIRST_FAILING_BOUNDARY` for every genuinely remaining product failure;
- Sprint Intelligence cluster analysis;
- release-forecast analysis;
- previous-095 QA methodology audit;
- learning applicability evidence;
- source integrity counters;
- exact product defect clusters, if any;
- exact QA-harness/reporting defects, if any;
- final verdict.

## Final verdict

Allowed:
- `PRODUCT_DEFECTS_PROVEN`
- `NO_PRODUCT_DEFECTS_AFTER_VALID_RETEST`
- `MIXED_PRODUCT_AND_QA_DEFECTS`
- `BLOCKED_BY_ENVIRONMENT`

Do not fix anything.

Commit and push only allowed QA report/trace artifacts, verify the primary report exists in remote HEAD, report final SHA and STOP. Do not start Assignment 096 or any later assignment.