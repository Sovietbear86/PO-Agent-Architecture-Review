# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_110_BACKEND_FULL_MATRIX_RECERTIFICATION`

## Role boundary
You are QA/forensic executor only. **Do not modify production code, frontend code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

Assignment 109 proved that the Agent is not currently reliable on basic task filters: member-only, status-only and multi-filter requests can return empty sets while independent REAL AS21 Oracle data are non-empty. Therefore previous A/B coverage is not sufficient as a product certification. This assignment is a full backend recertification and defect inventory before any further frontend work.

**Do not test or change frontend in Assignment 110. Do not start Vite unless required only to prove it is not involved; the acceptance surface is Direct Harness + independent REAL AS21 Oracle. Frontend Gate F is frozen until backend GREEN.**

## Goal
Build one exhaustive, reproducible backend truth matrix across:
1. every implemented Skill in the canonical catalog;
2. every required AS21 space: `WMB`, `STS`, `OLP`, `DMS`, `CRPV`;
3. every workflow status actually observed in each space, including space-specific/custom statuses;
4. sprint and non-sprint data, including `OLP`, `DMS`, and tasks whose sprint is genuinely `NONE`/empty in spaces such as WMB/CRPV;
5. every configured team member and declared competency/profile available to the Agent;
6. response latency and the exact contribution of semantic interpretation, grounding, source reads, deterministic capability execution and LLM generation.

This is not a smoke test. The output must tell the owner exactly what works, what fails, and the earliest failing boundary for every defect class.

## Non-negotiable A/B rules
- A = production PO Agent Harness under test.
- B = independent GigaCode Oracle from REAL AS21/SWTR/task-api/MCP-SWTR.
- Oracle B must not call the same Harness capability/calculation path to obtain expected values.
- Compare exact business facts; for task collections compare exact task-key sets, not counts only.
- HTTP 200 / `COMPLETED` does not count as PASS if business facts differ.
- Suspicious zero/empty results require Oracle proof before classification.
- REAL authoritative source only; fake/mock/frozen authoritative calls = 0; AS21 writes = 0.
- concurrency = 1 for source-heavy work. timeout >=120 s; heavy history/sprint/release calls may use 180 s. Retry timeout/502/503 up to 2 times with 20–30 s backoff.
- All Russian user queries must receive Russian user-facing prose. Source IDs/logins/status labels may retain their native form.
- Checkpoint results frequently so the marathon can resume after interruption without repeating certified rows unnecessarily.

## Phase 0 — provenance and clean backend runtime
1. Pull current branch and record exact remote HEAD, local HEAD and clean tracked worktree.
2. Stop/restart only the backend chain from current HEAD:
   - MCP-SWTR / AS21 bridge;
   - Task API;
   - PO Agent Harness.
3. Record PID/start time/port/config for each process.
4. Record model/provider and all timeout/retry configuration relevant to latency.
5. Confirm Harness adapter is REAL task-api/AS21.
6. Capture Learning Loop / learned policy state before testing.
7. Run an independent Oracle health check in all five spaces before certification starts.

## Phase 1 — build the authoritative source inventory first
Before asking the Agent any business question, build a fresh Oracle inventory from REAL AS21 for each space:

`WMB`, `STS`, `OLP`, `DMS`, `CRPV`.

For each space capture:
- total task count available through the authoritative read surface;
- exact task-key set or checkpointed corpus reference;
- all distinct raw workflow status values and counts;
- normalized status/category currently produced by the adapter, including every case mapped to `Unknown`/`UNKNOWN`;
- all distinct assignee identities/logins and counts;
- all sprint IDs and task counts;
- exact count/key set for tasks with no sprint (`NONE`, null, empty, or equivalent source representation);
- all release IDs where present;
- attachment types/counts sufficient for attachment skills;
- representative tasks with descriptions, acceptance criteria, dependencies, history and attachments where available.

For OLP and DMS explicitly validate current approved sprint targets plus any other live sprint needed for coverage. For WMB/CRPV explicitly prove at least one non-sprint (`NONE`) population if the source currently contains it.

Do not reuse historical expected counts from earlier reports.

## Phase 2 — team/competency inventory
Discover the actual team data/configuration consumed by the current runtime. Do not assume `config/team.example.yaml` is authoritative if another runtime file/environment source is used.

Build a complete team inventory containing every configured member with:
- login / canonical identity;
- name if available;
- products/spaces;
- role;
- capacity;
- professional profile;
- competencies/skills;
- team affiliation and any other fields used by team skills.

Then prove whether each configured member can be grounded against REAL AS21 assignee data where applicable. Keep configuration truth and AS21 workload truth separate.

A team skill must never silently ignore configured competencies merely because AS21 has no matching current task for that person.

## Phase 3 — status vocabulary and memory contract
This phase is mandatory for **every distinct source status in every space**.

For each `(space, raw_status)` pair discovered in Phase 1:
1. Oracle B selects the exact task-key set with that raw status.
2. A asks naturally in Russian for tasks with that status in the same space.
3. Compare exact task-key sets.
4. Inspect interpreter slots, grounding, capability arguments, mapped `status`, `status_raw`, and returned user-facing text.

### Required behavior for new/custom statuses
A status that exists authoritatively in AS21 is not an unknown business fact. If the Agent has not seen that status before, it must become usable from source grounding and must **not** be presented to the user as `UNKNOWN` merely because it is absent from a hard-coded enum.

Test all of the following:
- first encounter with a source-valid custom status;
- second query for the same status in the same session;
- fresh session query for the same status;
- cold Harness restart and query again.

The acceptable contract is: source-valid status remains discoverable/filterable by its real label without a user having to teach an enum value again. If the architecture persists a learned/source vocabulary, prove persistence. If it re-discovers from source on every clean runtime, that is also acceptable as long as the user never receives a false `UNKNOWN` and filtering remains correct.

Do **not** learn arbitrary user-invented statuses that are absent from source. Those should clarify/fail closed.

Classify separately:
- `STATUS_ENUM_LOSS`
- `STATUS_RAW_LOSS`
- `STATUS_GROUNDING_FAILURE`
- `STATUS_FILTER_MISMATCH`
- `STATUS_MEMORY/PERSISTENCE_FAILURE`

## Phase 4 — space dimension matrix
For each of the five spaces, run canonical and paraphrased natural Russian queries for:
- all tasks in the space;
- one exact task lookup;
- one member-only search using a source-present member;
- one status-only search using a status present in that space;
- member + status;
- sprint where the space has sprints;
- member + sprint where applicable;
- status + sprint where applicable;
- member + status + sprint where applicable;
- release filters where releases exist;
- attachment queries where source data exist.

For spaces with no sprint on some tasks, explicitly query non-sprint tasks and require exact equality to Oracle `sprint is NONE/null` set. The Agent must not invent a sprint or drop those tasks.

## Phase 5 — sprint coverage
At minimum validate:
- `OLP-SPRNT-5` if still source-valid;
- `DMS-SPRNT-1` if still source-valid;
- `DMS-SPRNT-2` if still source-valid;
- at least one additional live OLP/DMS sprint if available;
- non-sprint/NONE populations in WMB/CRPV if present.

For each real sprint run:
- sprint scope exact set;
- sprint health;
- current sprint resolution where supported;
- velocity;
- throughput;
- WIP;
- cycle time;
- lead time;
- carryover;
- scope change;
- predictability;
- risk queue.

Where a metric genuinely cannot be computed because the source contract/history is missing, require a truthful typed limitation. Do not classify a fabricated 0 as success and do not classify a missing capability as product defect without source-contract evidence.

## Phase 6 — complete 54-skill certification
Read the canonical `SKILL_CATALOG` from current HEAD and enumerate every implemented Skill. Current catalog should total 54; verify the count rather than assuming it.

For **every implemented skill** run:
- one canonical natural Russian query;
- one natural paraphrase;
- one negative/missing-slot or unavailable-source case where meaningful;
- one REAL Oracle comparison when the skill returns source-backed deterministic facts;
- evidence/trace and resolved skill/version;
- elapsed time.

For LLM-heavy analytical/drafting skills, Oracle B validates grounded inputs/evidence and invariants rather than prose equality. Hallucinated source facts are FAIL.

The final report must contain one row per implemented skill; no skill may disappear into a summary bucket.

## Phase 7 — every team member
For every configured team member, run at minimum:
- `Покажи задачи <member>` against Oracle AS21 where source workload exists;
- member + one valid status;
- member + sprint where the member has sprint work;
- workload/WIP/blocked facts as applicable;
- competency/profile retrieval/use;
- competency match on a representative task;
- assignee recommendation on a representative task, validating that declared competencies and current workload both influence grounded inputs.

If a configured member has zero current AS21 tasks, Oracle must prove the zero; the Agent must still retain the member's declared competencies/profile for competency skills.

Test names, surnames, canonical logins and at least one natural Russian case form where data permit. No hardcoding to Garanin or any single member is acceptable.

## Phase 8 — combinatorial filter integrity
Generate a bounded but comprehensive pairwise/3-way matrix from live Oracle values across:
- space;
- member;
- status;
- sprint/NONE;
- release where present.

Every combination must be constructed only from source-valid values. Compare exact A vs B task-key sets.

At least one non-empty and one genuine empty combination must be included per applicable dimension so that the Agent is tested both for false empty and false positive/broadening behavior.

Trace every mismatch through:
`query -> semantic frame -> grounding -> skill -> capability args -> candidate source corpus -> mapped fields -> deterministic filters -> final result`.

Do not label `CAPABILITY_ARGUMENT_BUILDING` unless the arguments themselves are proven wrong. If args are correct and candidate/mapped data are wrong, use the later correct boundary.

## Phase 9 — conversation/context regression
Run multi-turn sessions using live values from different spaces:
- member query -> add status;
- member + sprint -> replace status;
- switch from DMS to OLP and prove stale DMS slots do not survive;
- remove a constraint explicitly;
- correction after clarification;
- bare sprint ID;
- bare member surname;
- `только открытые` after a grounded prior request.

Required: slot retention only when intended, replacement/removal when requested, no invented IDs, no English prose on Russian turns.

## Phase 10 — performance and 10+ second latency forensic
Instrument each request end-to-end. For representative fast and heavy skills record at least:
- total request wall time;
- semantic LLM time;
- candidate/domain/capability ranking time if separately measurable;
- grounding/source-context time;
- Task API -> AS21 time and number of source calls;
- deterministic capability/filter/calculation time;
- response-generation LLM time;
- retries/backoff;
- cold vs warm behavior/cache hits.

Run enough repetitions to report p50/p95/max for:
- exact task lookup;
- member-only search;
- status-only search;
- sprint scope;
- one multi-filter query;
- one team skill;
- one LLM-heavy analytical skill.

Flag every normal user query >10 s and identify the dominant boundary. Specifically look for:
- full-corpus scans on every grounding turn;
- repeated `semantic_context()` source scans;
- pairwise LLM tournament explosion across domains/capabilities;
- repeated point hydration of the same tasks;
- sequential source reads that could be reused safely;
- duplicate Oracle-like reads inside the Agent;
- unnecessary second LLM generation.

Do not propose or implement optimization in QA. Produce an evidence-backed latency decomposition and prioritized hotspots.

## Phase 11 — QA methodology audit
Explain why prior A/B reports allowed basic regressions such as `Задачи Гаранина -> 0` to survive.

Audit specifically:
- whether historical matrices used only a few entities/spaces;
- whether expected clarification was accepted without completing the resumed query;
- whether counts were compared instead of exact sets;
- whether a direct skill call was substituted for normal semantic routing;
- whether source-valid custom statuses were excluded by hard-coded test data;
- whether PASS was inferred from HTTP 200/COMPLETED;
- whether Oracle B accidentally reused Harness logic;
- whether previous full-skill runs tested skill executability but not real business correctness across dimensions.

Output concrete rule changes/recommendations, but do not modify testing rules in this assignment.

## FIRST_FAILING_BOUNDARY labels
Use the earliest proven boundary, including:
- SEMANTIC_INTERPRETATION
- SKILL_RESOLUTION
- SESSION_CONTEXT
- CLARIFICATION_STATE_APPLICATION
- ENTITY_GROUNDING
- STATUS_VOCABULARY
- CAPABILITY_ARGUMENT_BUILDING
- SOURCE_ROUTING
- SOURCE_CONTRACT
- SOURCE_DATA
- TASK_SOURCE_HYDRATION
- CANONICAL_MAPPING
- DETERMINISTIC_FILTERING
- DETERMINISTIC_CALCULATION
- RESPONSE_MAPPING
- RESPONSE_LANGUAGE
- LEARNING/PERSISTENCE
- PERFORMANCE_SEMANTIC_LLM
- PERFORMANCE_GROUNDING
- PERFORMANCE_SOURCE_IO
- PERFORMANCE_HYDRATION
- PERFORMANCE_RESPONSE_LLM
- QA_METHODOLOGY

## Checkpoint/resume protocol
This run may be long. Maintain checkpoint artifacts after each major phase and each 10–15 skill rows. A restart must continue from already completed immutable Oracle snapshots only when source freshness remains valid; if a business fact may have changed, refresh Oracle B for that row.

Do not increase AS21 parallelism to speed the run. Prefer a longer reliable marathon over source overload.

## Required outputs
Primary report:
`po-agent-platform-v2/qa_reports/BACKEND_FULL_MATRIX_RECERTIFICATION_110.md`

Supporting artifacts prefix:
`BACKEND_FULL_MATRIX_RECERTIFICATION_110_`

The report must include:
- exact HEAD/runtime provenance;
- five-space Oracle inventory;
- per-space status dictionaries and UNKNOWN mapping audit;
- sprint/NONE inventory;
- complete team/competency inventory used by runtime;
- all 54 skill rows;
- per-member matrix;
- combinatorial filter A/B matrix with exact task-key diffs;
- conversation/context matrix;
- latency p50/p95/max and boundary decomposition;
- QA methodology audit;
- source-integrity/retry counters;
- fake/mock/frozen = 0 and AS21 writes = 0;
- Learning Loop state before/after;
- complete defect list with FIRST_FAILING_BOUNDARY.

Allowed final verdicts:
- `BACKEND_GREEN_FULL_MATRIX_CERTIFIED`
- `BACKEND_PRODUCT_DEFECTS_PROVEN`
- `MIXED_PRODUCT_SOURCE_AND_QA_DEFECTS`
- `BLOCKED_BY_ENVIRONMENT`

`BACKEND_GREEN_FULL_MATRIX_CERTIFIED` is forbidden while any basic member/status/space/sprint/NONE query differs from Oracle, any implemented skill lacks a certified row, any source-valid status is exposed as false UNKNOWN, any team competency is silently lost, or any unexplained >10 s latency remains without a localized cause.

Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`, report final SHA, then STOP. Do not change production code and do not begin frontend work.