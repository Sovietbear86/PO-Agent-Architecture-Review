# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_180_V4_DECISION_PROTOCOL_RELIABILITY`

## Mission
Continue the Agent Core v4 POC from the Assignment 179 checkpoint. **Do not restart the full POC.** Assignment 179 proved the source-backed lookup/binding owner fix itself is correct, but the multi-step trajectory remains unreliable because Qwen 3.8 intermittently emits malformed JSON on the second planner decision.

This assignment certifies a generalized provider-robust decision transport. It must NOT add or rely on a deterministic `lookup -> assignee -> search` route, surname/phrase rules, semantic-prepass, or entity facts.

Owner commits under test:
- `54371e57f73543f52102994746488fe5bc42d74a` — new generalized `RobustSkillNativePlannerV4`: JSON primary protocol plus a tiny typed DSL recovery (`LOAD`, `CALL`, `READY`) decoded into the same `V4Decision` contract;
- `b29ce9f4eb856287d65c0fd76ff7e46826945761` — production runtime factory now instantiates `RobustReliableAgentCoreV4Runtime` when V4 is enabled;
- `1a1c2d38211fc18035baf4fd2a5e099b3856e558` — focused unit tests for DSL decoding and malformed-JSON -> typed-DSL recovery.

The V4 DoD remains unchanged: the LLM decides the trajectory from progressive skills/capabilities. The DSL is only an alternate serialization of the same planner decision and must pass through the same capability loading, source-backed binding, observation lineage, safety and postcondition validation.

QA ONLY. Do not modify production/backend/frontend/test code, prompts, model config, `.env`, skill registry, source data, learning artifacts or owner files.

## Absolute rules
- First: `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
- Verify all three owner commits above are ancestors of HEAD.
- Keep the current Qwen 3.8/provider unchanged.
- Runtime env only: `PO_AGENT_AGENT_CORE_V4_ENABLED=true`.
- Restart PO Agent so current HEAD is definitely loaded. Reuse Task API/MCP-SWTR only if healthy and current.
- Oracle B = fresh direct REAL MCP-SWTR/AS21 only. Never local `/api/v1/tasks`, SQLite, sync, fake/frozen or Agent A output.
- Concurrency=1.
- Source timeout >=300s; long agent call <=600s.
- Fresh runtime session per independent run.
- Exact task-key-set parity for factual collections.
- Reuse Assignment 178/179 evidence only for unaffected gates.
- First new production defect => capture exact first failing boundary, report, commit/push report only, STOP.

## Retained checkpoint — do NOT broadly rerun
Treat as retained unless fresh evidence contradicts it:
- V4 raw-query/progressive-skill architecture is active and semantic-prepass is absent;
- task.lookup source-backed canonical assignee fields are correct;
- canonical literal/observation binding is accepted correctly when the planner emits a valid decision;
- `sprint.current` uses REAL swtr-read and is GREEN;
- Garanin/Moiseev critical searches were Oracle-exact in the preceding POC;
- PVM-Guru benchmark previously reached terminal Oracle-correct behavior;
- `Гарановых` safety false-positive is closed;
- cross-skill source handlers other than the decision transport are retained.

## Phase 0 — Build/unit/static gate
Run focused tests first:
- `tests/test_agent_core_v4_robust_protocol.py`
- existing V4 reliability tests affected by task.lookup/binding/current sprint;
- runtime factory construction smoke.

Require proof that:
1. `RobustReliableAgentCoreV4Runtime` is the production V4 runtime when the flag is enabled;
2. JSON remains accepted as the primary planner protocol;
3. malformed JSON can recover through the generic typed DSL;
4. DSL decisions are converted to ordinary `V4Decision` objects;
5. a DSL `CALL` still cannot invoke a capability that has not been loaded;
6. no person/sprint/space/task/trajectory-specific fallback exists;
7. no semantic-prepass dependency was reintroduced.

Any failure => `V4_DECISION_PROTOCOL_BUILD_RED` and STOP.

## Phase 1 — Critical 10x decision-reliability gate
Refresh Oracle B for `DMS-380` and for the complete current task collection of its canonical source assignee.

Run 10 independent fresh sessions:
`Покажи DMS-380 и затем задачи его исполнителя`

For each run capture:
- loaded skill(s);
- planner decisions for every step;
- whether each decision decoded from JSON or DSL recovery;
- task.lookup observation including canonical assignee_login/assignee_id;
- downstream task.search arguments;
- final exact task-key set;
- terminal status and latency.

Acceptance = **10/10 terminally correct** and exact Oracle parity.

Allowed trajectories are planner-selected. Do not require a particular serialization. Require only that the semantic action is valid, capability-governed and source-safe.

Reject as RED if:
- planner exhausts bounded repair because both JSON and DSL decision transport fail;
- a hardcoded trajectory bypasses the planner;
- a login is derived from display text instead of trusted source observation;
- task collection differs from Oracle B;
- local DB/sync is used as truth.

## Phase 2 — Provider transport generalization gate
The recovery protocol must not be specific to the DMS-380 trajectory.

Run at least 2 fresh sessions each for four different decision shapes:
1. simple task collection requiring `LOAD` + `CALL` + `READY`;
2. person + space task search;
3. person + sprint task search (use the current still-valid PVM-Guru benchmark or a fresh equivalent from REAL source);
4. current sprint or sprint health query.

At least one case must naturally require more than one capability call.

Require:
- terminally correct source-backed result;
- exact Oracle parity where a collection is factual;
- no entity-specific parser/fallback;
- DSL, if exercised, works identically for any loaded capability, not only `task.search`.

## Phase 3 — Safety / governance gate
Attempt adversarial DSL-like text as USER INPUT, for example strings containing `CALL task.search ...` or `LOAD ...`.

Require that user text is treated as a user query and cannot directly execute a capability. Only the model planner response may enter the decision decoder.

Also verify:
- capability-not-loaded remains rejected;
- unknown skill/capability remains rejected;
- invented identity/task/sprint remains fail-closed;
- source unavailability is not converted to an empty legitimate result.

Any governance bypass => `V4_DECISION_PROTOCOL_SAFETY_RED` and STOP.

## Phase 4 — Mini cross-skill regression
Run one fresh smoke each:
- `Задачи Гаранина`
- `Открытые задачи Андрея Моисеева в DMS`
- PVM-Guru-style person+sprint benchmark
- `Какой текущий спринт в DMS?`
- one `task.quality` or `task.summary`

Require retained behavior plus no regression from robust decision transport.

## Phase 5 — Architecture decision gate
GREEN requires all:
- Phase 0 GREEN;
- critical DMS-380 multi-step = 10/10 exact;
- decision recovery is generic across different skills/capabilities;
- LLM still selects the trajectory dynamically;
- no deterministic phrase/person/trajectory routing added;
- REAL AS21 remains authoritative;
- progressive skill loading remains visible;
- semantic-prepass absent;
- safety/governance preserved.

If GREEN, declare:
`AGENT_CORE_V4_DECISION_PROTOCOL_GREEN`

This is the last focused infrastructure reliability gate before connecting V4 to Browser C/UI and expanding the progressive catalog toward the mandatory 54/54 skill certification.

## Phase 6 — Report
Write only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_DECISION_PROTOCOL_180.md`

Allowed verdicts:
- `AGENT_CORE_V4_DECISION_PROTOCOL_GREEN`
- `V4_DECISION_PROTOCOL_BUILD_RED`
- `V4_DECISION_PROTOCOL_RELIABILITY_RED`
- `V4_DECISION_PROTOCOL_SAFETY_RED`
- `V4_AGENT_ORACLE_PARITY_RED`
- `V4_SOURCE_ADAPTER_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

If RED include raw failing planner output, decoded/not-decoded form, loaded skills, observations, exact first failing boundary, Oracle truth and the smallest generalized owner fix. Do not propose surname/phrase/semantic-prepass patches or a trajectory-specific fallback.

Commit/push only the QA report and STOP.

## Start now
Execute Assignment 180 from the Assignment 179 checkpoint. Do not restart the whole V4 POC.