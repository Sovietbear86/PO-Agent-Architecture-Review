# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_096_AB_FORENSIC_TRIAGE`

## Role boundary — mandatory
You are QA/tester only. **Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

If a defect is found, prove `FIRST_FAILING_BOUNDARY` and report it. Do not repair it.

This assignment is the first mandatory execution of the post-change A/B Oracle rules defined in:
`po-agent-platform-v2/docs/testing/POST_CHANGE_AB_ORACLE_CERTIFICATION.md`

## Why Assignment 096 exists

The latest 095B marathon successfully exercised 54/54 skills in REAL task-api/AS21 mode and produced:
- 26 PASS;
- 7 FAIL;
- 21 BLOCKED;
- HTTP/source environment healthy enough for the full run.

However, the reported root causes were not proven and some historical semantic regression rows were marked BLOCKED with `no matching skill found`. The report also contained QA-report-generation defects such as unresolved `{data[...]}` placeholders.

Assignment 096 is a **forensic A/B triage only**. Do not rerun the whole 54-skill marathon. Do not fix anything.

## Scope

### A. Seven current FAIL rows
1. `sprint-cycle-time`
2. `sprint-lead-time`
3. `sprint-carryover`
4. `sprint-scope-change`
5. `sprint-predictability`
6. `sprint-risk-queue`
7. `release-forecast`

### B. Historical semantic regression cases that were incorrectly/ambiguously BLOCKED
At minimum retest:
- exact task lookup for a second valid real task ID;
- nonexistent exact task ID;
- sprint ID only;
- sprint + person;
- sprint + status;
- sprint + product/project where supported;
- person only;
- status only;
- person + product + status;
- independent second team member;
- correction: new status replaces old status and unaffected slots survive.

### C. Suspicious team-workload anomaly
The latest preflight showed a `team-workload` response equivalent to `0 active tasks / 0 assignees`. This must be independently A/B verified against REAL AS21.

Do NOT assume zero is wrong. If Oracle B confirms genuine zero source facts, record `AB_PASS`. If Oracle B proves non-zero REAL facts, record `AB_MISMATCH` and trace the first failing boundary.

## Phase 0 — clean provenance

1. Pull current branch and record exact HEAD.
2. Record `git status --short`; production files must remain clean.
3. Start/reuse the same proven production environment as 095B.
4. Confirm `task-api` + REAL AS21(SWTR).
5. Confirm fake/mock/frozen authoritative calls = 0.
6. Confirm AS21 writes = 0.
7. Record runtime PID/start time, source health and non-secret environment fingerprint.
8. Revalidate every task/sprint/release/member entity used below against REAL AS21 before testing.

## Phase 1 — recover exact skill contracts

For every suspect FAIL and historical blocked case inspect the production skill/catalog contract and record:
- skill_id/version;
- required slots;
- optional slots;
- required source facts;
- expected clarification/unavailable behavior;
- deterministic calculation/output contract;
- whether history/snapshot/timeline/team profile is mandatory.

Do not use synthetic queries that simply name a skill such as `Покажи данные по sprint-cycle-time` unless that is explicitly a supported user phrase.

Build realistic Russian user queries with valid REAL entities.

## Phase 2 — A/B Oracle execution model

For every source-backed test run both paths independently.

### A — Agent under test
Send the natural-language query through production PO Agent and capture:
- query/session_id;
- resolved skill/version;
- semantic frame;
- grounded slots;
- capability arguments;
- source/evidence IDs;
- final status;
- normalized business facts;
- elapsed time.

### B — Independent GigaCode Oracle
Independently query REAL AS21/SWTR/task-api read paths without using the Harness answer or reusing the same Harness capability/calculation implementation as the oracle.

Capture:
- exact source request(s);
- source entity IDs;
- raw/source fact summary sufficient for reproduction;
- independent filtering/calculation method;
- normalized expected business facts;
- elapsed time.

Compare deterministic facts, not wording.

Allowed A/B row verdicts:
- `AB_PASS`
- `EXPECTED_CLARIFICATION`
- `SOURCE_CAPABILITY_UNAVAILABLE_BY_DESIGN`
- `ENVIRONMENT_BLOCKED`
- `AB_MISMATCH`

HTTP 200 or `COMPLETED` cannot override `AB_MISMATCH`.

## Phase 3 — Sprint Intelligence forensic A/B

Use the same known-valid REAL sprint wherever the contracts permit.

For each of the six failing sprint skills:
1. run a contract-valid Agent A query;
2. independently obtain the sprint task key set and all required source fields through Oracle B;
3. calculate whether the requested metric is actually computable from current source facts;
4. if computable, independently calculate the expected metric/value/state;
5. compare A vs B;
6. trace the full production path for every mismatch/failure.

Explicitly distinguish:
- metric can be calculated and Agent calculates it incorrectly;
- required source history/snapshot fields do not exist in current source contract;
- skill should return typed `UNAVAILABLE` rather than `FAILED`;
- semantic/grounding/argument loss;
- QA query invalid;
- genuine deterministic implementation defect.

Do not group all six into one cluster until evidence proves the same first boundary.

## Phase 4 — Release Forecast forensic A/B

1. Discover and validate a REAL release.
2. Recover exact forecast contract and required timeline/history/source inputs.
3. Run a realistic Agent A query.
4. Independently obtain release scope and required fields as Oracle B.
5. Determine whether forecast is computable from actual available source facts.
6. If computable, independently derive expected bounded forecast inputs/output.
7. Identify exact first failing boundary if A differs/fails.

Do not label backend missing implementation without evidence.

## Phase 5 — Historical semantic regression A/B

Re-run all cases in Scope B using valid REAL entities.

For each case compare:
`natural query -> semantic slots/constraints -> Agent task key set`
against
`independent Oracle B filtering over REAL AS21`.

For task collections, **exact task-key-set equality** is the primary acceptance criterion when possible. Count-only equality is insufficient.

Mandatory invariants:
- second valid exact task resolves by authoritative point read;
- nonexistent exact task returns typed not-found/appropriate non-hallucinated result;
- person/status/sprint/product constraints survive semantic interpretation and grounding;
- combined filters are ANDed correctly;
- correction replaces old status, does not append contradictory status, and preserves unaffected slots;
- second member proves no Garanin-specific hardcoding.

If any historical GREEN has regressed, report `AB_MISMATCH` and exact `FIRST_FAILING_BOUNDARY`.

## Phase 6 — team-workload anomaly + Learning Loop candidate eligibility

Run:
A. production query: `Покажи нагрузку команды` (or a more contract-valid natural equivalent if team scope must be specified);
B. independent REAL AS21 workload oracle using the exact same resolved team/product scope.

Compare at minimum:
- member/assignee set and count;
- active task key set and count;
- per-member task counts where available;
- blocked/WIP distribution if part of contract.

### If A/B matches zero
Record `AB_PASS`. Do not attempt to teach the Agent that zero is impossible.

### If Agent A says zero/empty but Oracle B proves non-zero
Record `AB_MISMATCH` and trace:
`query -> semantic -> scope grounding -> capability args -> source call -> source facts -> workload calculation -> response`.

Then assess whether this mismatch is **eligible** for Learning Loop testing under the production policy.

Do NOT promote/fix a policy in Assignment 096 unless the current explicit assignment text below says so. This assignment only proves eligibility and the correct generalized candidate shape.

A valid generalized candidate shape may be conceptually equivalent to:
`when a valid team scope produces an empty workload result, revalidate scope/filter/source grounding against authoritative source before finalizing the empty result`.

Forbidden candidate shapes:
- `zero is impossible`;
- hard-coded team/member/task IDs;
- storing the Oracle counts as universal truth;
- memorizing the original query/answer.

If team-workload A/B mismatch is proven and Learning Loop is applicable, mark it `LEARNING_CANDIDATE_PROVEN` for the owner to schedule a separate learning certification after any required owner fix.

## Phase 7 — FIRST_FAILING_BOUNDARY

For every genuine product mismatch/failure, trace:
`user query`
`-> semantic interpretation`
`-> skill resolution`
`-> entity grounding`
`-> capability argument building`
`-> REAL source call`
`-> source response/data availability`
`-> deterministic calculation`
`-> response/status mapping`.

Identify the earliest divergence.

Allowed labels include:
- `SEMANTIC_INTERPRETATION`
- `SKILL_RESOLUTION`
- `ENTITY_GROUNDING`
- `CAPABILITY_ARGUMENT_BUILDING`
- `SOURCE_CONTRACT`
- `SOURCE_DATA_MISSING`
- `DETERMINISTIC_CALCULATION`
- `RESPONSE_STATUS_MAPPING`
- `LEARNING_POLICY_APPLICATION`
- `QA_HARNESS_ORACLE_DEFECT`

Do not repair anything.

## Phase 8 — QA runner/report methodology audit

Audit the latest 095B QA artifacts:
- verify 26 + 7 + 21 = 54;
- verify reported 0.45 h duration against actual timestamps/logs/checkpoint;
- verify canonical/paraphrase/edge rows are backed by actual API calls;
- identify unresolved report template placeholders such as `{data[...]}`;
- verify source-integrity counters from raw logs/checkpoint rather than rendered placeholders;
- verify PASS/BLOCKED classification logic did not label expected clarification as failure or hide an A/B mismatch;
- verify the runner did not use Harness results as Oracle expectations.

Classify runner/report defects separately as `QA_HARNESS_ORACLE_DEFECT`; they are not production defects.

Do not modify the runner during Assignment 096.

## Phase 9 — source integrity

Record exact focused-run counters:
- HTTP 500;
- HTTP 502 + endpoint mapping;
- timeout/retries;
- successful REAL AS21 reads;
- fake/mock/frozen authoritative calls = 0;
- AS21 writes = 0.

40–60+ seconds may be normal SWTR latency. Per request timeout >=120 s; heavy metric/release/history calls may use 180 s. Retry timeout/502 up to 2 times before ENV classification.

## Output

Create only QA artifacts under:
`po-agent-platform-v2/qa_reports/`

Primary report:
`po-agent-platform-v2/qa_reports/AB_ORACLE_FORENSIC_TRIAGE_096.md`

Optional raw evidence artifacts must use prefix:
`AB_ORACLE_FORENSIC_TRIAGE_096_`

The primary report must include:
- exact commands and tested HEAD;
- clean-worktree/runtime provenance;
- exact contract matrix;
- A/B matrix for all seven FAILs;
- A/B matrix for all historical semantic regression cases;
- exact task-key-set comparisons where applicable;
- team-workload A/B anomaly result;
- Learning Loop candidate eligibility conclusion;
- Sprint Intelligence forensic evidence;
- Release Forecast forensic evidence;
- all exact `FIRST_FAILING_BOUNDARY` findings;
- QA runner/report methodology defects;
- source integrity counters;
- clearly separated PRODUCT vs SOURCE/DATA/CONTRACT vs QA defects;
- recommended owner-fix clusters, without code changes;
- final verdict.

## Final verdict
Allowed only:
- `PRODUCT_DEFECTS_PROVEN`
- `AB_MISMATCHES_PROVEN`
- `MIXED_PRODUCT_AND_QA_DEFECTS`
- `NO_PRODUCT_DEFECTS_AFTER_AB_RETEST`
- `BLOCKED_BY_ENVIRONMENT`

Do not fix anything.

Commit and push only the allowed QA report/evidence artifacts. Verify the primary report exists in remote HEAD. Report final SHA and STOP.

Do not start any later assignment.