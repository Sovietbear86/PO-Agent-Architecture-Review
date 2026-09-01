# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_110_BACKEND_FULL_MATRIX_AND_LEARNING_RECERTIFICATION`

## Role boundary
You are QA/forensic executor only. **Do not modify production code, frontend code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.** You may exercise supported Harness feedback/learning APIs and lifecycle operations strictly as product behavior under test, with complete audit evidence and mandatory rollback/cleanup. AS21 writes remain forbidden.

Assignment 109 proved that the Agent is not currently reliable on basic task filters: member-only, status-only and multi-filter requests can return empty sets while independent REAL AS21 Oracle data are non-empty. Previous A/B coverage is therefore not sufficient as product certification.

The owner also reports that the Learning Loop appears inert after the Agent asks variants of `Что бы вы хотели улучшить?`: the user provides feedback, but there is no visible evidence that the Harness mines the failure, creates a governed learning artifact, evaluates it, applies an approved improvement, generalizes it, persists it or can roll it back.

**Do not test or change frontend in Assignment 110. Frontend Gate F is frozen until backend + Harness + Learning Loop are GREEN.**

## Goal
Build one exhaustive, reproducible backend/Harness truth matrix across:
1. every implemented Skill in the canonical catalog;
2. every required AS21 space: `WMB`, `STS`, `OLP`, `DMS`, `CRPV`;
3. every workflow status actually observed in each space, including custom/space-specific statuses;
4. sprint and non-sprint data, including OLP/DMS sprints and genuine `NONE`/null sprint populations in WMB/CRPV where present;
5. every configured team member and declared competency/profile available to the Agent;
6. response latency and exact bottleneck decomposition;
7. the complete Harness conversational capability surface: semantic interpretation, grounding, clarification, session continuation, correction, satisfaction feedback, learning candidate generation, evaluation, governed promotion, generalization, persistence, rollback and negative controls.

This is not a smoke test. The output must tell the owner exactly what works, what fails, and the earliest failing boundary for every defect class.

## Non-negotiable A/B rules
- A = production PO Agent Harness under test.
- B = independent GigaCode Oracle from REAL AS21/SWTR/task-api/MCP-SWTR.
- Oracle B must not obtain expected values from the Harness capability/calculation path being tested.
- Compare exact business facts; for task collections compare exact task-key sets, not counts only.
- HTTP 200 / `COMPLETED` does not count as PASS if business facts differ.
- Suspicious zero/empty results require Oracle proof.
- REAL authoritative source only; fake/mock/frozen authoritative calls = 0; AS21 writes = 0.
- concurrency = 1 for source-heavy work. timeout >=120 s; heavy history/sprint/release calls may use 180 s. Retry timeout/502/503 up to 2 times with 20–30 s backoff, then revalidate/restart and focused retest before environment classification.
- All Russian user queries must receive Russian user-facing prose. Source IDs/logins/status labels may retain native values.
- Checkpoint frequently; the marathon must be resumable.
- A GREEN verdict is forbidden if a learning flow claims success without a versioned artifact + evaluation evidence + governed state transition.

## Phase 0 — provenance and clean backend runtime
1. Pull current branch; record remote/local HEAD and clean worktree.
2. Stop/restart MCP-SWTR/AS21 bridge, Task API and PO Agent Harness from current HEAD.
3. Record PID/start time/port/config/model/provider/timeouts/retries.
4. Confirm REAL task-api/AS21 adapter, fake/mock/frozen=0, AS21 writes=0.
5. Capture exact Learning Loop state before testing: persistent policy store, aliases/rules/candidates/eval artifacts, active/promoted versions, pending feedback state and any Harness learning endpoints/capabilities.
6. Run independent Oracle health checks in WMB, STS, OLP, DMS, CRPV.

## Phase 1 — authoritative five-space source inventory
Before asking the Agent questions, build a fresh REAL AS21 inventory for `WMB`, `STS`, `OLP`, `DMS`, `CRPV`.

For each space capture:
- task count and exact/checkpointed key corpus;
- all distinct raw workflow statuses + counts;
- adapter normalized status/category and every mapping to `Unknown/UNKNOWN`;
- all assignee identities/logins + counts;
- all sprint IDs + counts;
- exact key set/count for sprint `NONE`/null/empty;
- releases where present;
- attachment types;
- representative tasks with description/acceptance/dependencies/history/attachments where available.

For OLP/DMS validate approved sprint surface: `OLP-SPRNT-5`, `DMS-SPRNT-1`, `DMS-SPRNT-2` when source-valid. For WMB/CRPV prove non-sprint populations if present. Never reuse old report counts as truth.

## Phase 2 — team/competency inventory
Discover the **actual** team/config data consumed by the running Harness; do not assume `team.example.yaml` is authoritative.

Build every configured member with login, name, spaces/products, role, capacity, professional profile, competencies/skills, affiliation and every field consumed by team skills. Separately ground each member against REAL AS21 workload where applicable.

Configuration truth and AS21 workload truth are separate. A member with zero tasks may still have valid competency/profile knowledge.

## Phase 3 — status vocabulary, discovery and memory
For every `(space, raw_status)` discovered in Phase 1:
1. Oracle B derives the exact key set.
2. Agent A receives a natural Russian query for that status in that space.
3. Compare exact sets and inspect semantic slots, grounding, capability args, `status`, `status_raw`, output text.

For any source-valid status not previously known to the Harness, test:
- first encounter;
- immediate repeated query;
- fresh session;
- cold Harness restart.

A source-valid status must remain usable by its real label and must not be falsely exposed as `UNKNOWN`. It may be persisted or rediscovered from source, but the user must not have to reteach it after every turn/restart. Arbitrary user-invented statuses absent from source must not be learned.

Classify separately: `STATUS_ENUM_LOSS`, `STATUS_RAW_LOSS`, `STATUS_GROUNDING_FAILURE`, `STATUS_FILTER_MISMATCH`, `STATUS_MEMORY_PERSISTENCE_FAILURE`.

## Phase 4 — five-space natural-query matrix
For each of WMB/STS/OLP/DMS/CRPV run canonical + paraphrased Russian requests for:
- all tasks in the space;
- exact task lookup;
- member-only;
- status-only;
- member + status;
- sprint where applicable;
- member + sprint;
- status + sprint;
- member + status + sprint;
- release where real data exist;
- attachment queries where real data exist;
- explicit non-sprint/NONE task search where applicable.

Compare exact task-key sets. The Agent must not invent a sprint or broaden/narrow scope silently.

## Phase 5 — sprint and NONE coverage
At minimum validate `OLP-SPRNT-5`, `DMS-SPRNT-1`, `DMS-SPRNT-2` when live, one additional OLP/DMS sprint if available, and genuine NONE/null populations in WMB/CRPV.

For each real sprint run sprint scope, health, current resolution, velocity, throughput, WIP, cycle time, lead time, carryover, scope change, predictability and risk queue. Missing historical source capability must produce truthful typed limitation, not fabricated zero and not an invented metric.

## Phase 6 — all implemented Skills
Read current `SKILL_CATALOG`, verify implemented count (expected 54 but do not assume), and create one explicit row per implemented Skill.

For every Skill run:
- canonical natural Russian query;
- natural paraphrase;
- negative/missing-slot or source-unavailable case where meaningful;
- REAL Oracle comparison for deterministic/source-backed facts;
- resolved skill/version, evidence/trace, elapsed time.

For LLM-heavy analytical/drafting skills, Oracle validates grounded inputs, evidence and invariants, not prose equality. Hallucinated source facts = FAIL.

## Phase 7 — every configured team member + competencies
For every configured member run:
- `Покажи задачи <member>` vs REAL Oracle;
- member + valid status;
- member + sprint if applicable;
- workload/WIP/blocked where applicable;
- role/profile/competency retrieval and use;
- competency match on representative task;
- assignee recommendation, proving both competencies and current workload are in grounded inputs.

Test surname, full/canonical login and at least one natural Russian grammatical form where data permit. No Garanin-specific hardcoding.

## Phase 8 — bounded combinatorial filter integrity
Generate live-data pairwise/3-way combinations over space × member × status × sprint/NONE × release. Include genuine non-empty and genuine empty cases. Compare exact A/B task-key sets.

Trace every mismatch through:
`query -> semantic frame -> grounding -> skill -> capability args -> candidate corpus -> mapped fields -> deterministic filters -> result`.

Do not call a defect `CAPABILITY_ARGUMENT_BUILDING` if the arguments are correct. Find the first real divergence: source routing, hydration, canonical mapping, deterministic filtering, etc.

## Phase 9 — dialogue/session/correction capabilities
Run multi-turn conversations using live values from multiple spaces:
- member -> add status;
- member+sprint -> replace status;
- switch DMS -> OLP and prove stale slots disappear;
- explicitly remove a constraint;
- correction after clarification;
- bare sprint ID;
- bare surname;
- `только открытые` after grounded prior request;
- user rejects an answer and gives a corrected executable request.

Required: correct slot retention/replacement/removal, no invented IDs, Russian prose, no clarification/correction loops.

## Phase 10 — latency forensic
Instrument end-to-end timings for representative fast/heavy requests. Record total, semantic LLM, ranking/planning, grounding/source context, AS21 calls/count, hydration, deterministic capability, response LLM, retries, cold/warm/cache.

Report p50/p95/max for exact lookup, member-only, status-only, sprint scope, multi-filter, team skill and one LLM-heavy analytical skill. Flag every normal user request >10 s and identify dominant boundary.

Specifically test for repeated full-corpus scans, repeated `semantic_context()` source discovery, pairwise LLM tournament explosion, repeated hydration, duplicate source calls and unnecessary second LLM generation.

## Phase 11 — deep Harness capability inventory
Before testing learning behavior, recover the actual executable Harness capability graph from current HEAD and runtime, not only documentation.

Inventory and prove reachability of:
- semantic interpreter;
- entity grounding/resolvers;
- clarification state persistence + resume;
- correction classification/application;
- satisfaction/feedback endpoints or runtime handlers;
- negative feedback reason capture;
- trace/session/skill/version linkage;
- learning observation/mining step;
- candidate generation;
- eval/regression case generation;
- shadow/offline evaluation;
- approval/promotion gate;
- active-policy application;
- persistence/load-on-cold-start;
- rollback/version history;
- cleanup/test isolation.

For each capability record code path, API/runtime entry point, state/artifact produced, expected lifecycle transition and whether it is actually exercised in production Harness mode.

The architecture contract says that negative feedback must produce an improvement/eval candidate and that the Agent must not claim to have learned without a versioned artifact + evaluation evidence. Treat this as an acceptance contract.

## Phase 12 — reproduce the owner's `Что бы вы хотели улучшить?` suspicion
Create at least two **proven A/B mismatches** suitable for learning, preferably one task-filter failure and one semantic/dialogue failure. Do not manufacture a failure if current owner fixes make the case pass; choose another reproducible mismatch from the matrix.

For each case:
1. Agent gives the wrong source-backed answer.
2. User supplies negative feedback through the normal Harness satisfaction/feedback path.
3. If Agent asks `Что бы вы хотели улучшить?` or equivalent, answer with a concrete natural Russian correction that describes desired behavior but **does not provide the expected task IDs/counts as a memorized answer**.
4. Capture every state change after the feedback turn.

Mandatory questions to answer with evidence:
- Was the feedback linked to original session/trace/skill/version/frame/source evidence?
- Was the user's improvement text persisted anywhere?
- Was a failure pattern mined?
- Was an eval/regression case created?
- Was a learning candidate created and versioned?
- Was any evaluation run?
- Did state transition beyond a conversational acknowledgement?
- If nothing happened after the phrase, identify the exact first failing boundary.

If the Agent merely says/asks an improvement phrase and no artifact/lifecycle action occurs, classify `LEARNING_FEEDBACK_NOOP` and RED.

## Phase 13 — full governed Learning Loop lifecycle certification
For at least one safe, generalizable, reproducible learning-applicable defect, exercise the complete product lifecycle **through supported Harness/learning operations only**. Do not edit code/config manually to simulate learning.

Required sequence:
1. `BASELINE_AB_MISMATCH` — Agent A differs from REAL Oracle B.
2. `AUTHORITATIVE_RECHECK` — learning path independently rechecks source where appropriate; never learn from plausibility alone.
3. `FEEDBACK_CAPTURED` — negative/improvement feedback tied to trace/session/skill/version/frame.
4. `PATTERN_MINED` — generalized failure class identified.
5. `CANDIDATE_CREATED` — versioned artifact produced.
6. `EVAL_CASE_CREATED` — original failure converted into regression/eval case without leaking Oracle answer as production truth.
7. `SHADOW_OFFLINE_EVAL` — baseline vs candidate evidence captured.
8. `REGRESSION_GATE` — unrelated known-green cases included.
9. `APPROVAL_PROMOTION_GATE` — exercise configured governance. If manual approval is required and QA cannot approve, stop at `AWAITING_APPROVAL` and prove the gate works; do not bypass it. If the test environment supports governed test promotion, use it and record exact version.
10. `SAME_CASE_RETEST` — after legitimate promotion, original A must match B.
11. `GENERALIZATION` — materially different entity/space/wording with same failure class must improve without memorizing original facts.
12. `NEGATIVE_CONTROL` — legitimate empty/different case must remain correct; learned policy must not over-trigger.
13. `FRESH_SESSION` — behavior persists outside original conversation.
14. `COLD_RESTART` — promoted policy/artifact reloads and behavior persists.
15. `ROLLBACK` — revert through supported lifecycle and prove prior state restored.
16. `CLEANUP` — no test-specific active policy remains unless explicitly part of pre-existing baseline.

Forbidden learning artifacts:
- hard-coded task IDs/member IDs/counts;
- `zero is impossible`-type universal rules;
- copying Oracle expected set into policy;
- bypassing source grounding/security/write boundaries;
- mutating deterministic metric definitions/source contracts through online learning.

## Phase 14 — learning generalization matrix
If a candidate can legitimately be promoted in the QA environment, validate it across at least:
- a different member;
- a different space;
- a paraphrased Russian request;
- a real positive case;
- a real empty/negative case.

For status-learning behavior additionally test a source-valid custom status from another space. A learned rule must generalize by behavior/semantic class, not entity identity.

If promotion cannot legally occur without owner/manual approval, report pre-promotion evaluation and exact blocked governance state; do not falsely mark post-promotion steps PASS.

## Phase 15 — Learning Loop/Harness latency and observability
Measure feedback/learning operations separately:
- feedback submission latency;
- candidate-generation latency;
- eval latency;
- promotion/application latency where exercised;
- cold-start policy load time.

Verify observability exists for every lifecycle transition: artifact/version IDs, before/after state, timestamps, originating trace/session, evaluation outcome and rollback lineage. Missing observability that makes it impossible to prove learning is functioning is a defect (`LEARNING_OBSERVABILITY_GAP`).

## Phase 16 — QA methodology audit
Explain why previous A/B/learning reports allowed basic regressions and potentially inert learning behavior to survive.

Audit:
- narrow entity/space coverage;
- clarification marked PASS without completing resumed execution;
- counts instead of exact sets;
- direct capability calls substituted for normal Harness semantic routing;
- hard-coded status test vocabulary;
- HTTP 200/COMPLETED treated as correctness;
- Oracle path reusing Harness logic;
- full-skill runs checking executability rather than real business correctness;
- feedback UI/endpoint returning 200 without verifying downstream learning artifacts;
- `policy count unchanged` interpreted as learning safety when the test actually expected learning to occur;
- candidate creation/evaluation/persistence/rollback not proven in one continuous lifecycle.

Recommend concrete testing-rule changes in the report, but do not modify rules in Assignment 110.

## FIRST_FAILING_BOUNDARY labels
Use the earliest proven boundary, including:
- SEMANTIC_INTERPRETATION
- SKILL_RESOLUTION
- SESSION_CONTEXT
- CLARIFICATION_STATE_APPLICATION
- CORRECTION_STATE_APPLICATION
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
- FEEDBACK_CAPTURE
- FEEDBACK_TRACE_LINKAGE
- LEARNING_PATTERN_MINING
- LEARNING_CANDIDATE_GENERATION
- LEARNING_EVAL_CASE_GENERATION
- LEARNING_SHADOW_EVAL
- LEARNING_REGRESSION_GATE
- LEARNING_APPROVAL_GATE
- LEARNING_POLICY_APPLICATION
- LEARNING_PERSISTENCE
- LEARNING_GENERALIZATION
- LEARNING_ROLLBACK
- LEARNING_OBSERVABILITY
- PERFORMANCE_SEMANTIC_LLM
- PERFORMANCE_GROUNDING
- PERFORMANCE_SOURCE_IO
- PERFORMANCE_HYDRATION
- PERFORMANCE_RESPONSE_LLM
- PERFORMANCE_LEARNING
- QA_METHODOLOGY

## Checkpoint/resume protocol
This is expected to be a long marathon. Maintain checkpoint artifacts after each major phase and every 10–15 Skill rows. Continue from checkpoints only when source freshness remains valid; refresh Oracle facts if they may have changed. Never increase AS21 parallelism to make the run faster.

## Required outputs
Primary report:
`po-agent-platform-v2/qa_reports/BACKEND_FULL_MATRIX_RECERTIFICATION_110.md`

Supporting artifacts prefix:
`BACKEND_FULL_MATRIX_RECERTIFICATION_110_`

Required report sections:
- exact HEAD/runtime provenance;
- five-space Oracle inventory;
- per-space status dictionaries + UNKNOWN audit;
- sprint/NONE inventory;
- actual runtime team/competency inventory;
- all implemented Skill rows;
- every-member matrix;
- combinatorial A/B exact-set matrix;
- dialogue/context matrix;
- latency p50/p95/max + decomposition;
- Harness capability graph/inventory;
- owner feedback-flow reproduction (`Что бы вы хотели улучшить?`);
- Learning Loop lifecycle state machine with before/after artifacts;
- baseline mismatch -> candidate -> eval -> governance -> correction/generalization -> persistence -> rollback evidence where legally exercisable;
- learning negative controls;
- learning observability + latency;
- QA methodology audit;
- source integrity/retry counters;
- fake/mock/frozen=0 and AS21 writes=0;
- complete defect list with FIRST_FAILING_BOUNDARY.

Allowed final verdicts:
- `BACKEND_AND_LEARNING_GREEN_FULL_MATRIX_CERTIFIED`
- `BACKEND_PRODUCT_DEFECTS_PROVEN`
- `LEARNING_LOOP_DEFECTS_PROVEN`
- `MIXED_BACKEND_LEARNING_SOURCE_AND_QA_DEFECTS`
- `BLOCKED_BY_ENVIRONMENT`

`BACKEND_AND_LEARNING_GREEN_FULL_MATRIX_CERTIFIED` is forbidden while any basic member/status/space/sprint/NONE query differs from Oracle, any implemented Skill lacks a row, any source-valid status is falsely exposed as UNKNOWN, any team competency is silently lost, any unexplained normal request >10 s lacks a localized cause, or the feedback/Learning Loop cannot prove a governed versioned lifecycle beyond conversational acknowledgement.

Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`, report final SHA, then STOP. Do not change production code and do not begin frontend work.