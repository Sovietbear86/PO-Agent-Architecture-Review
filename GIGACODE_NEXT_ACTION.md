# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_106_FULL_LONG_REAL_AS21_REGRESSION`

## Role boundary
You are QA/test executor only. **Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.** You may create/update only QA artifacts under `po-agent-platform-v2/qa_reports/`.

Mandatory rules in `po-agent-platform-v2/docs/testing/POST_CHANGE_AB_ORACLE_CERTIFICATION.md` apply.

This is intentionally a **long, resumable, sequential regression marathon** after the recent history, sprint-routing and `search_versions` fixes. The purpose is to establish the real end-to-end state of the full skill surface before the owner proceeds to the next roadmap step.

## Core principle
Test the full user-facing catalog, but distinguish **product defects** from **authoritative source-data absence**.

A skill must NOT be failed merely because a particular REAL entity lacks optional business data (for example a task has no fix version), provided the absence is independently proven from AS21/SWTR and the product responds according to contract.

However, source-data absence is not a blanket excuse:
- first discover whether another valid REAL entity has the required data;
- if at least one valid entity exists, test the skill on that entity;
- only classify `SOURCE_DATA_NOT_AVAILABLE_FOR_VALID_TEST` when no suitable REAL entity can be found after bounded discovery + retry/retest;
- a runtime exception, wrong calculation, incorrect filtering, hallucinated value, fake fallback, or wrong typed status remains a defect even when some source entities have missing fields.

Known examples from prior proof:
- DMS version set may be empty while OLP currently has a REAL version (`1.6.0`); therefore version/release discovery must use live discovery and must not assume DMS has fix versions.
- `release-forecast` requires historical release timeline points. Current version metadata alone is not sufficient; if timeline remains unavailable after live proof, typed source limitation is expected rather than a product failure.
- `sprint-carryover` and `sprint-scope-change` require authoritative historical sprint commitment/membership facts. Current scope must never be substituted for the missing baseline.

## Runtime / load policy
This run is expected to be long.

1. Run sequentially: `concurrency=1`.
2. Standard REAL AS21 call timeout >=120 s.
3. History/sprint/release-heavy calls may use 180 s.
4. Timeout/502/503: retry up to 2 times with 20–30 s backoff.
5. If the source remains unstable, revalidate/restart the fresh Task API/Harness runtime and perform a focused retest before classifying environment failure.
6. Use a checkpoint/resume file so an interruption does not invalidate already completed evidence.
7. Do not rerun successful expensive cases unnecessarily after restart; revalidate provenance/source health and resume from checkpoint.
8. Never increase concurrency to shorten the marathon.

## Approved REAL sprint test surface
For all sprint-related skills use live-validated sprints in this order:
1. `DMS-SPRNT-2` — primary canonical/current and best-filled DMS sprint;
2. `DMS-SPRNT-1` — DMS cross-sprint control;
3. `OLP-SPRNT-5` — independent product cross-sprint control.

Never hardcode counts, task-key sets, statuses or metrics from previous reports. Oracle B must fetch them live in this run.

## Phase 0 — provenance and source gate
1. Pull current branch and record exact HEAD.
2. `git status --short` must show no unauthorized production modifications before testing.
3. Audit commits since Assignment 105A/105B and explicitly list every changed production file. If GigaCode-authored commits modified production code, flag `ROLE_BOUNDARY_VIOLATION` separately; do not silently treat them as owner fixes.
4. Fully restart/revalidate Task API and PO Agent from current HEAD; record PIDs/start times/import roots.
5. Establish at least 5 successful REAL source reads before the marathon:
   - one exact task point-read;
   - `DMS-SPRNT-2` exact scope;
   - `DMS-SPRNT-1` exact scope;
   - `OLP-SPRNT-5` exact scope;
   - one history/version/other independent REAL read.
6. fake/mock/frozen authoritative calls = 0; AS21 writes = 0.
7. Capture Learning Loop policy store exact state before testing.

If the REAL source gate cannot be established after mandatory retry/retest, stop `BLOCKED_BY_ENVIRONMENT`; do not generate pseudo-regression results.

## Phase 1 — recover authoritative test surface
Recover the **exact current 54 user-facing skills** from the current catalog/runtime rather than copying an old report.

For each skill record:
- skill ID/name/version;
- required arguments/entities;
- required source facts;
- deterministic/LLM/source-dependent behavior;
- expected success/clarification/unavailable semantics;
- exact capability handler/runtime registration.

Prove total catalog cardinality. If it is not 54, report the current true number and classify the catalog change explicitly.

## Phase 2 — live fixture discovery
Build a REAL test-fixture registry before running skills.

Discover and validate, as applicable:
- at least two existing exact task IDs with useful descriptions/history;
- one nonexistent task ID control;
- at least two real team members when skills require assignees;
- several real statuses with matching tasks;
- approved sprint surface above;
- valid product/space values including DMS and OLP where supported;
- valid release/version candidates by live `search_versions` (`space` required);
- tasks that actually carry a release/fix-version value if any can be found;
- any entity required for other catalog skills.

For every required optional field, search boundedly for an entity that actually has it before declaring source-data absence.

## Phase 3 — full skill regression
Execute every current user-facing skill once with a realistic canonical Russian query.

For skills with multiple materially different branches/filters, add the minimum additional cases required to exercise the contract. Do not inflate the run with cosmetic paraphrases unless they cover semantic routing/correction behavior.

For every executable/data-bearing skill capture Agent A:
- natural query and session ID;
- resolved skill/version;
- semantic frame and relevant slots;
- capability arguments;
- evidence IDs/source markers;
- response status/warnings;
- normalized business facts;
- elapsed time.

## Phase 4 — mandatory Agent A / Oracle B
Where the answer contains business facts from AS21/SWTR or deterministic calculations, build an independent Oracle B.

Oracle B must not use the Agent/Harness answer or the same final Harness capability as truth.

Examples:
- task lookup: direct REAL task read;
- filtered collections: independent source filtering, exact task-key set equality;
- sprint scope: exact task-key set equality;
- team/member workload: exact member/task sets and counts;
- task history/time-in-status: raw transition events + independent arithmetic;
- cycle/lead metrics: raw task histories + independently recovered repository formula;
- versions: direct MCP `search_versions` with schema-valid request and exact normalized version set;
- release forecast: only if authoritative historical timeline inputs exist.

HTTP 200/`COMPLETED` never overrides a business-fact mismatch.

## Phase 5 — source-data absence handling
Use one of these explicit classifications when REAL data prevents a meaningful positive test:

### `SOURCE_DATA_NOT_AVAILABLE_FOR_VALID_TEST`
Use only when:
1. the skill/capability is registered and reachable;
2. required source fact/field is proven absent for all bounded candidate entities searched in this run;
3. retries/retest rule has been satisfied for transient source errors;
4. the Agent fails closed/clarifies/types the limitation according to contract;
5. no fake/invented value is produced.

This classification is **excluded from the functional PASS denominator** but remains visible in the 54-skill matrix.

### `EXPECTED_SOURCE_CAPABILITY_UNAVAILABLE`
Use for a proven upstream capability gap, e.g. historical sprint commitment or release timeline, when the skill correctly exposes typed unavailability.

### `EXPECTED_CLARIFICATION`
Use only when the user query genuinely lacks a contract-required entity/slot and the clarification is correct.

Do not use any of these classifications for an integration defect, invalid routing, wrong formula, wrong filtering, stale runtime, or unhandled exception.

## Phase 6 — mandatory focused regression invariants
In addition to the 54-skill matrix, explicitly prove:
- exact task point-read for two valid task IDs;
- nonexistent exact task does not hallucinate;
- person-only filter;
- status-only filter;
- person + status AND semantics;
- sprint-only filter on `DMS-SPRNT-2`;
- sprint + person and sprint + status where valid REAL matches can be found;
- correction turn replaces corrected slot and preserves unaffected slots;
- independent second team member proves no hardcoding to one person;
- team workload does not return authoritative zero unless Oracle B also proves zero for the exact same scope;
- task-history and time-in-status remain timezone-safe;
- `sprint-carryover`/`sprint-scope-change` do not invent historical baseline;
- `/versions` without `space` returns typed 400;
- `/versions?space=DMS` and `/versions?space=OLP` match direct Oracle B;
- no release forecast is fabricated from a single current version snapshot.

## Phase 7 — failure triage
For every non-PASS/non-expected row identify the earliest proven `FIRST_FAILING_BOUNDARY`, choosing the most precise category:
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
- `ROLE_BOUNDARY_VIOLATION`

Do not label a calculation defect if execution never reached the calculation.

## Phase 8 — Learning Loop protection
Capture exact policy state before and after the marathon.

Requirements:
- deterministic/source regression testing must not create/promote unrelated new policies;
- existing promoted policy IDs/versions/states must be listed exactly;
- if a policy changes, identify the exact triggering interaction and classify it;
- Learning Loop must not be used as Oracle B;
- no teaching based on temporary source outages or source-data absence.

## Phase 9 — QA methodology audit
Before final verdict verify:
- every catalog skill appears exactly once in the primary matrix (plus optional branch cases separately);
- category totals add up exactly to current catalog cardinality;
- checkpoint/results correspond to real API calls, not generated placeholders;
- report contains no unresolved `{data[...]}` templates;
- source counters reconcile with raw/checkpoint evidence;
- PASS is never inferred from HTTP status alone;
- source-data exclusions are individually evidenced rather than bulk-labeled;
- no GigaCode production modifications occurred during Assignment 106.

## Phase 10 — source integrity counters
Report exact counts from this run:
- REAL AS21/SWTR reads by type;
- task point reads;
- sprint reads per approved sprint;
- task-history reads;
- version/release reads;
- HTTP 400 expected checks;
- HTTP 500;
- HTTP 502/503;
- timeouts;
- retries;
- runtime/source retests;
- fake/mock/frozen authoritative calls (must be 0);
- AS21 writes (must be 0).

## Acceptance model
The report must distinguish three numbers:

1. **Catalog coverage** = tested/classified skills / total catalog skills. Target: all 54 classified.
2. **Functionally testable skills** = skills for which sufficient REAL data/capability exists in this run.
3. **Functional PASS rate** = AB_PASS / functionally testable skills.

Do NOT lower catalog coverage by simply skipping source-limited skills. They must still be represented and classified.

A successful marathon requires:
- 100% catalog coverage/classification;
- 100% PASS for all functionally testable skills;
- source-limited skills only in proven expected source/data categories;
- zero unexplained product failures;
- zero fake/mock/frozen authoritative calls;
- zero AS21 writes;
- Learning Loop unchanged except pre-existing allowed state;
- no unauthorized production changes by GigaCode.

## Next-step gate
If all functionally testable skills PASS and every remaining row is only a proven source-data/source-capability limitation, final verdict:
`FULL_REGRESSION_GREEN_READY_FOR_NEXT_PLAN_STEP`

That verdict explicitly authorizes the owner to proceed to the next roadmap step after reviewing the report.

If one or more product defects are proven:
`PRODUCT_DEFECTS_PROVEN`

If both product defects and QA/harness methodology defects exist:
`MIXED_PRODUCT_AND_QA_DEFECTS`

If source instability prevents sufficient coverage after mandatory retries/retests:
`BLOCKED_BY_ENVIRONMENT`

If GigaCode modified production code during this assignment:
`ROLE_BOUNDARY_VIOLATION` must be present even if tests otherwise pass.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/FULL_LONG_REAL_AS21_REGRESSION_106.md`

Allowed supporting artifacts, all under `po-agent-platform-v2/qa_reports/`, prefix:
`FULL_LONG_REAL_AS21_REGRESSION_106_`

Use a resumable checkpoint artifact under the same prefix.

Commit/push **only** QA artifacts. Report final SHA and STOP. Do not start the next assignment yourself.