# Mandatory Post-Change A/B Oracle Certification

## Status
MANDATORY QA RULE. This certification MUST run after every production behavior/code change before the changed HEAD can be accepted as GREEN.

## Purpose
Prove that PO Agent answers agree with independently retrieved REAL AS21/SWTR facts, and prove that the Learning Loop can detect, correct, generalize, persist, and safely roll back a proven semantic/behavioral error without inventing facts.

## Non-negotiable role separation
- A = PO Agent Harness under test.
- B = independent GigaCode Oracle.
- GigaCode is QA/tester only. It MUST NOT modify production code, prompts, skills, capabilities, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, or acceptance expectations to obtain GREEN.
- Oracle B MUST NOT derive expected values from the Harness answer or reuse the same Harness capability/calculation path being tested.
- Oracle B MUST retrieve REAL source facts independently from AS21/SWTR/task-api/MCP-SWTR and independently calculate the expected business result.
- All source interaction is read-only. AS21 writes = 0.

## Trigger
Run this protocol after EVERY change that can affect production behavior, including runtime, semantic interpretation, routing, grounding, skill/capability code, metrics, source adapters/contracts, prompts, learning/policy behavior, persistence, response/status mapping, or shared dependencies/configuration.

Documentation-only and QA-report-only commits do not require a new product certification unless they change executable behavior or acceptance rules.

A changed HEAD is NOT certified merely because unit tests, pytest, HTTP health, skill resolution, or response status are green.

## Gate 0 — provenance and clean start
1. Record exact branch and HEAD.
2. Record `git status --short`.
3. Restart the production runtime from the exact tested HEAD when the change affects loaded runtime behavior.
4. Verify task-api + REAL AS21/SWTR mode.
5. Verify fake/mock/frozen authoritative calls = 0.
6. Verify AS21 writes = 0.
7. Record environment/source health and any timeout/502 counters.

### Gate 0A — transient AS21/SWTR availability rule
AS21/SWTR can be temporarily slow or unavailable during a valid test window. A single timeout, 502, 503, transport error, or failed read MUST NOT be used to conclude that a skill/source capability is unavailable or that a product defect exists.

Mandatory retry/retest behavior:
- concurrency = 1 for source-heavy tests;
- normal source request timeout >=120 s;
- history/sprint/release-heavy calls may use 180 s;
- on timeout/502/503, retry the same authoritative read up to 2 times with 20–30 s backoff;
- if the whole source preflight is unstable, restart/revalidate task-api + Harness and repeat the focused test once more in a fresh runtime before final classification;
- where one known entity fails due to source instability, try another valid REAL entity from the approved test surface rather than immediately declaring the capability unavailable;
- only after retries/retest fail consistently may the row be classified `ENVIRONMENT_BLOCKED` / final verdict `BLOCKED_BY_ENVIRONMENT`.

Do not transform transient environment instability into `SOURCE_CAPABILITY_UNAVAILABLE_BY_DESIGN`, `SOURCE_DATA_MISSING`, `EXPECTED_INSUFFICIENT_HISTORY`, or `PRODUCT_DEFECT_PROVEN` without independent source evidence.

## Gate 1 — deterministic automated regression
Run the complete automated regression suite required by the current branch. Any regression is RED and stops certification unless explicitly classified as an external environment/source block with evidence.

## Gate 2 — A/B Oracle matrix
### 2.1 Required coverage
For every source-backed skill affected directly or transitively by the change, run at least:
- one canonical natural Russian user query;
- one natural paraphrase;
- one negative/missing-slot case where the contract requires clarification/unavailable behavior;
- one REAL source-backed business-fact comparison.

For broad/shared changes (semantic interpreter, dialogue runtime, grounding, source adapter, common capability layer, learning runtime), execute the full source-ready skill matrix, not only one skill.

### 2.1A Approved sprint test surface
For sprint-related analysis, regression, Oracle comparisons, source discovery, and metric certification, use this approved REAL sprint set before selecting arbitrary alternatives:
1. `OLP-SPRNT-5`
2. `DMS-SPRNT-1`
3. `DMS-SPRNT-2` — preferred primary sprint because it is currently the most representative/filled DMS sprint for testing.

Rules:
- validate each sprint live before using it; the identifiers are approved test targets, not hardcoded expected answers;
- prefer `DMS-SPRNT-2` for canonical positive sprint-skill tests when REAL data is available;
- use `DMS-SPRNT-1` and `OLP-SPRNT-5` as independent cross-sprint controls/generalization cases;
- if one sprint is temporarily unavailable because of AS21/SWTR instability, retry/retest per Gate 0A and then use another approved sprint before declaring environment/source failure;
- never infer a historical snapshot, expected metric, task count, or task-key set merely from the approved sprint ID. All expected facts must still come from REAL Oracle B reads in the current run.

### 2.2 A path — Agent
Send the normal natural-language query through the production PO Agent endpoint. Record:
- exact query and session_id;
- resolved skill/version;
- semantic frame and grounded slots;
- capability arguments;
- source calls/evidence IDs;
- final status;
- normalized business facts returned by the Agent;
- elapsed time.

### 2.3 B path — Independent Oracle
For the same user intent, GigaCode independently queries REAL AS21/SWTR without asking the Harness for the answer. It must record:
- exact source request(s);
- real entity IDs used;
- raw/source fact summary sufficient to reproduce the expectation;
- independent calculation/filtering logic;
- normalized expected business facts;
- elapsed time.

40–60+ seconds per SWTR request is normal. Use >=120 s per request; heavy calls may use 180 s. Do not convert normal source latency into a false failure. Keep concurrency conservative enough not to overload SWTR.

### 2.4 Compare facts, not prose
A/B equality is evaluated on deterministic business facts, not wording. Depending on skill, compare the applicable normalized fields:
- exact task key set;
- task count;
- member/assignee set and count;
- sprint/release identity and scope;
- status distribution;
- blocked/WIP counts;
- deterministic metric inputs and result;
- release/task membership;
- evidence-backed entity values.

Textual style differences do not fail A/B. Missing, extra, wrong, stale, or invented source facts do.

### 2.5 Verdict per row
Allowed row verdicts:
- `AB_PASS` — normalized A facts equal independent B facts within the explicit deterministic contract.
- `EXPECTED_CLARIFICATION` — required slot genuinely absent.
- `SOURCE_CAPABILITY_UNAVAILABLE_BY_DESIGN` — required fact is not exposed by the current source contract.
- `ENVIRONMENT_BLOCKED` — external source/runtime condition proven after Gate 0A retries/retest.
- `AB_MISMATCH` — Agent and Oracle differ on source-backed facts.

HTTP 200/`COMPLETED` alone can never override `AB_MISMATCH`.

## Gate 3 — mandatory anomaly guard
Treat suspicious empty/zero results as hypotheses requiring verification, not as automatically valid and not as automatically wrong.

Examples: `0 исполнителей / 0 задач`, empty sprint scope, zero workload, empty release scope.

Rule:
- If Oracle B independently confirms the source is genuinely empty, PASS is allowed.
- If Oracle B proves non-empty REAL data, the Agent result is `AB_MISMATCH`.
- Never teach a policy such as “zero tasks is impossible”. The learned behavior must be source-grounded and generalizable.

## Gate 4 — FIRST_FAILING_BOUNDARY for every mismatch
For every `AB_MISMATCH`, trace:
`user query -> semantic interpretation -> skill resolution -> entity grounding -> capability arguments -> REAL source call -> source response -> deterministic calculation -> response mapping`.

Identify the first boundary where expected and actual diverge. Do not repair production code during GigaCode QA.

Recommended labels:
- `SEMANTIC_INTERPRETATION`
- `SKILL_RESOLUTION`
- `ENTITY_GROUNDING`
- `CAPABILITY_ARGUMENT_BUILDING`
- `SOURCE_CONTRACT`
- `SOURCE_DATA_MISSING`
- `DETERMINISTIC_CALCULATION`
- `RESPONSE_STATUS_MAPPING`
- `LEARNING_POLICY_APPLICATION`

## Gate 5 — Oracle-triggered Learning Loop certification
Run this gate for learning-applicable, safely reproducible mismatches. `team-workload` returning a false empty result is a preferred acceptance scenario when REAL AS21 independently proves a non-empty team workload.

### 5.1 Baseline failure
Capture A/B mismatch before learning. Example form only:
- A: `0 members / 0 active tasks`
- B: non-zero REAL member/task facts.

### 5.2 Authoritative recheck
The Learning Loop must perform an authoritative source recheck and preserve evidence. No correction may be based solely on plausibility or LLM opinion.

### 5.3 Candidate generation
The candidate must encode a generalized behavioral correction, not memorized entity facts.

GOOD pattern: when a valid team scope yields an unexpectedly empty workload, revalidate scope/filter/source grounding before finalizing the empty result.

FORBIDDEN pattern: this specific team always has N people/tasks; zero is impossible; hard-coded task/member IDs; copying Oracle output into a policy.

### 5.4 Promotion safety
A single raw mismatch must not silently mutate production behavior. The existing governed lifecycle remains mandatory: evidence -> candidate -> offline/shadow evaluation -> regression gate -> required approval/promotion contract -> versioned policy.

### 5.5 Same-case correction proof
After approved promotion, rerun the original case. A must now match B without fake/mock facts.

### 5.6 Generalization proof
Run a materially different query/entity that exercises the same learned behavioral class. The learned policy must improve/correct behavior without memorizing the original answer.

### 5.7 Negative control
Run a legitimate empty/zero case when one is available, or another case where the policy must not trigger. The policy must not convert genuine empty source data into invented non-zero facts.

### 5.8 Persistence proof
Perform a genuine cold restart. Verify the promoted policy is loaded from persistent storage and still produces the expected generalized behavior.

### 5.9 Rollback proof
Roll back the candidate/policy using the supported lifecycle and prove the rollback state. Cleanup must not leave a test-specific active policy behind.

## Gate 6 — learning safety invariants
Certification is RED if any of the following occurs:
- entity facts are stored as learned universal truth;
- source facts are invented because they “look plausible”;
- Oracle expected values leak into production code/prompt/policy as fixtures;
- a candidate bypasses required evaluation/approval/promotion controls;
- learning corrupts session state or semantic cache;
- learning breaks previously certified skills;
- policy does not survive required persistence semantics;
- rollback cannot restore the previous policy state.

## Gate 7 — post-learning regression
After learning-loop testing, rerun:
1. the affected A/B cases;
2. at least one known-green unrelated source-backed skill;
3. automated regression suite;
4. source-integrity counters.

For shared/core changes, rerun the full source-ready A/B matrix.

## Required report
Create a QA report under `po-agent-platform-v2/qa_reports/` named with the tested assignment/change, containing:
- tested HEAD and runtime provenance;
- changed production files/behavioral surface;
- automated test results;
- complete A/B matrix;
- Agent A facts vs Oracle B facts;
- exact source evidence for Oracle results;
- all mismatch traces and `FIRST_FAILING_BOUNDARY`;
- anomaly/zero-result checks;
- Learning Loop baseline, candidate, evaluation/promotion evidence, same-case correction, generalization, negative control, cold restart and rollback evidence where applicable;
- source integrity: HTTP 500, HTTP 502, timeout/retry, REAL AS21 reads, fake/mock/frozen calls, AS21 writes;
- retry/retest evidence when AS21/SWTR instability was observed;
- sprint IDs actually used from the approved sprint test surface for sprint-related testing;
- remaining blockers/defects;
- final verdict.

## Final verdicts
Only:
- `GREEN_AB_ORACLE_CERTIFIED`
- `REGRESSION_DETECTED`
- `AB_MISMATCH_DETECTED`
- `LEARNING_LOOP_REGRESSION`
- `BLOCKED_BY_ENVIRONMENT`

`GREEN_AB_ORACLE_CERTIFIED` requires all applicable gates above. A code-changing HEAD without this certification MUST NOT be treated as accepted/merge-ready.

## QA operating rule
GigaCode may diagnose and report. GigaCode MUST NOT fix production code. If certification is RED, STOP after committing/pushing only the authorized QA artifacts and return evidence for the developer/owner to decide the code change.
