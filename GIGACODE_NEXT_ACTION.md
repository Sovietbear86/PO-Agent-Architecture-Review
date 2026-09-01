# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_110C_TRUE_AB_BACKEND_MARATHON`

## Goal
Assignment 110B is not accepted as backend certification: its summary showed only 5 REAL AS21 reads and did not prove the requested natural-language Agent A matrix. Run a real, exhaustive A/B backend marathon. Frontend remains frozen and out of scope.

## Role boundary
You are QA/test executor only. Do not modify production/backend/frontend code, prompts, skills, tests, fixtures, semantic/learning implementation, AS21 data, roadmap, QA rules, or this file. Create/update only QA artifacts under `po-agent-platform-v2/qa_reports/`. AS21 writes = 0.

## Mandatory source paths
No local task DB/cache population and no local/cache truth. Do not run sync/population utilities for this certification.

Agent A:
`Russian natural-language query -> PO Agent Harness -> Task API -> MCP-SWTR -> REAL AS21`

Oracle B:
`independent direct read -> MCP-SWTR -> REAL AS21`

Oracle B must be independent of Agent/Harness logic. Never infer PASS from old reports, static analysis, catalog enumeration, HTTP 200, or plausible prose.

## Execution strategy: resumable chunked marathon
Do NOT use one giant subagent call.
- concurrency=1;
- chunks of 5–10 Agent cases, maximum 15 before checkpoint;
- per-call timeout 120 s, heavy source/history calls up to 180 s;
- timeout/502/503: max 2 retries with 20–30 s backoff;
- checkpoint after every chunk;
- resume after any session/process timeout;
- >1 hour runtime is normal;
- finding defects does not permit early STOP.

Checkpoint: `po-agent-platform-v2/qa_reports/BACKEND_TRUE_AB_MARATHON_110C_CHECKPOINT.md`
Final: `po-agent-platform-v2/qa_reports/BACKEND_TRUE_AB_MARATHON_110C.md`
Raw evidence prefix: `BACKEND_TRUE_AB_MARATHON_110C_`

## Phase 0 — provenance and counters
Record exact HEAD, clean worktree, service start/restart evidence, start/end timestamps and wall time.
Maintain counters from raw execution:
- Agent A natural-language requests;
- Oracle B REAL AS21 reads;
- total REAL AS21 reads;
- retries/timeouts/502/503;
- fake/mock/frozen reads;
- local DB authoritative reads;
- AS21 writes;
- completed/remaining chunks.

GREEN is invalid if Agent A requests = 0 or Oracle B reads = 0. Required: fake/mock/frozen=0, local authoritative DB reads=0, AS21 writes=0.

## Phase 1 — all spaces
Live-test WMB, STS, OLP, DMS, CRPV. For each, independently discover via REAL AS21 task keys, raw statuses, assignees, sprint values including NONE/null, releases and representative rich task fields. Do not infer one space vocabulary from another. Retry correct existing MCP-SWTR read contracts before declaring a space unavailable.

## Phase 2 — every live status
For every distinct `(space, raw_status)` discovered live:
- Oracle B exact task-key set;
- Agent A canonical Russian query;
- Agent A Russian paraphrase;
- exact set comparison;
- semantic frame/slots, skill, args, trace, timing.

A valid source status must not become permanent UNKNOWN merely because it was unseen before. Test discovery/learning and fresh-session/cold-restart behavior according to product design. Do not hardcode statuses.

## Phase 3 — every configured team member and competencies
Discover the actual configured team data source. For EVERY member test:
- member-only tasks vs Oracle;
- member + status;
- member + sprint where applicable;
- workload/WIP/blocked where supported;
- role/profile and competencies;
- competency matching;
- recommendation using competency + workload where supported.

Mandatory regression includes Garanin.R.V and other real members. No Garanin special-casing.

## Phase 4 — sprints and NONE
Test live confirmed DMS-SPRNT-1, DMS-SPRNT-2, OLP-SPRNT-5 and another live DMS/OLP sprint if available. Explicitly test sprint NONE/null/empty in WMB, CRPV and every source where Oracle proves it. Agent must never invent a sprint not supplied or grounded.

## Phase 5 — full current skill catalog
Read current SKILL_CATALOG. Expected scale is 54, but report actual count. For EVERY skill execute:
1. canonical Russian natural request;
2. Russian paraphrase;
3. negative/missing-slot/unavailable case when meaningful;
4. independent Oracle comparison for deterministic/source-backed facts;
5. skill/version, evidence/trace, elapsed time and verdict.

Final report requires one explicit row per skill. Catalog enumeration is not execution.

## Phase 6 — combinatorial filters
Test bounded live combinations across `space × member × status × sprint/NONE × release`, including non-empty and empty intersections. Mandatory:
- `Задачи Гаранина`;
- second DMS member;
- OLP member;
- `In progress` in DMS-SPRNT-2 if source-valid;
- another DMS status;
- member+status;
- member+sprint;
- member+status+sprint;
- NONE sprint;
- space+status;
- space+member.

Compare exact task-key sets, not only counts.

## Phase 7 — dialogue, context, Russian language
Run real multi-turn DMS and OLP sessions:
- member -> add status;
- member+sprint -> replace status;
- remove status;
- switch space;
- bare sprint/surname clarification;
- clarification option selection;
- correction after wrong answer;
- `только открытые` continuation;
- typo/noise tolerance.

Russian queries must get Russian user-facing prose. No invented sprint/entity IDs.

Mandatory owner-observed regression:
`Покажи открытые задачи Гончарова в спринте OLP-SPRNT-5` (or another Oracle-proven OLP member if needed). If Agent asks what `открытые` means and user selects `Open`, Agent must retain member+sprint, apply status, resume the pending query and return Oracle-equal results. It must NOT enter generic `что именно нужно исправить` correction mode.

## Phase 8 — deep Learning Loop behavioral test
Do not test learning merely by probing guessed endpoints. Map actual executable runtime wiring, then use at least TWO genuine wrong-answer cases from this run.

For each, prove as far as real governance permits:
`wrong answer -> negative feedback -> Agent asks what to improve -> concrete user correction -> persisted feedback/observation -> pattern/candidate -> eval -> shadow/regression gate -> approval/promotion state -> policy application -> same-case retest -> analogous new case -> fresh session -> cold restart -> persistence -> rollback -> rollback verification`.

Critical: after `Что бы вы хотели улучшить?`, a concrete user answer must cause observable downstream state/action. Conversation-only acknowledgement is not learning. Capture before/after artifact/state IDs and timestamps.

If owner approval is required, do not bypass it: prove the candidate/evaluation/gate and mark that step `OWNER_APPROVAL_REQUIRED`. Test generalized learning; never memorize entity-specific answers or learn rules like `zero results are impossible`.

## Phase 9 — Harness capability reachability
Prove runtime reachability, not code existence, for semantic interpretation, grounding, session context, clarification persistence/resume, correction, satisfaction feedback, trace/evidence and skill/version linkage, observation/mining, candidate generation, eval generation, shadow eval, promotion gate, policy application, persistence/version lineage and rollback.

## Phase 10 — latency forensics
At least 5 repetitions each: exact task lookup, member-only, status-only, sprint-only, multi-filter, team/competency skill, one LLM-heavy skill. Report p50/p95/max and source-call count. Where instrumentation permits decompose semantic LLM, planning, grounding, AS21 I/O, hydration/N+1, deterministic execution, response LLM, retry/backoff. Flag normal interactive requests >10 s and identify dominant boundary. QA only; do not optimize.

## Phase 11 — audit 110B
Explain how 110B could report GREEN with only a tiny REAL AS21 read count. Check for static/historical evidence, inferred PASS, Oracle-only tests without Agent A, catalog enumeration without execution, cache/local data, or unexecuted rows classified as reachable/PASS. Classify 110B from evidence.

## Required per-case evidence
Every case must record: executed_case_id, timestamp, exact Russian Agent query, session ID, Agent request evidence, skill/version, slots/frame when available, capability args, trace/evidence, Agent normalized facts/task-key set, independent Oracle request/read, Oracle facts/task-key set, exact diff, Agent/Oracle timing, retries and verdict.

Allowed case verdicts:
- AB_PASS
- EXPECTED_CLARIFICATION
- EXPECTED_SOURCE_CAPABILITY_UNAVAILABLE
- OWNER_APPROVAL_REQUIRED
- ENVIRONMENT_BLOCKED
- AB_MISMATCH

HTTP 200/COMPLETED cannot override an A/B mismatch.

Use earliest evidence-backed FIRST_FAILING_BOUNDARY such as SEMANTIC_INTERPRETATION, LANGUAGE_POLICY, SESSION_CONTEXT, CLARIFICATION_STATE_APPLICATION, CORRECTION_STATE_CLASSIFICATION, ENTITY_GROUNDING, SKILL_RESOLUTION, SLOT_RETENTION, CAPABILITY_ARGUMENT_BUILDING, SOURCE_ROUTING, SOURCE_CONTRACT, SOURCE_DATA_MISSING, DETERMINISTIC_FILTERING, DETERMINISTIC_CALCULATION, RESPONSE_STATUS_MAPPING, LEARNING_FEEDBACK_CAPTURE, LEARNING_OBSERVATION, LEARNING_CANDIDATE_GENERATION, LEARNING_EVALUATION, LEARNING_POLICY_APPLICATION, LEARNING_PERSISTENCE, LEARNING_ROLLBACK, QA_HARNESS_ORACLE_DEFECT.

## Strict GREEN gate
`BACKEND_AGENT_GREEN_FULL_MATRIX_CERTIFIED` is allowed ONLY when all current skills, all required spaces, every live status, every configured member, sprint/NONE matrix, mandatory combinations, dialogue regressions, behavioral Learning Loop, Harness reachability and latency repetitions are executed with no unresolved AB_MISMATCH and counters prove substantial live Agent A + Oracle B execution.

If mandatory coverage is incomplete, verdict must not be GREEN.

Allowed final verdicts:
- BACKEND_AGENT_GREEN_FULL_MATRIX_CERTIFIED
- PRODUCT_DEFECTS_PROVEN
- MIXED_PRODUCT_LEARNING_AND_QA_DEFECTS
- QA_EXECUTION_INCOMPLETE
- QA_EXECUTION_INVALID
- BLOCKED_BY_ENVIRONMENT

## Final report
Include tested HEAD, timestamps/wall time, all counters, checkpoint history, five-space matrix, full status matrix, full member/competency matrix, sprint/NONE matrix, one-row-per-skill matrix, combinations, dialogue/language results, Learning Loop lifecycle, Harness reachability, latency p50/p95/max, all A/B diffs, 110B audit, and every unexecuted row.

Commit/push ONLY QA artifacts. Do not modify production code. Report final SHA and STOP.

## Start now
Execute Assignment 110C autonomously Phase 0 through Phase 11. Do not ask permission between phases and do not stop at the first defect.