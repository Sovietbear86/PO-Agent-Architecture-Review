# Agent Core v4 — Definition of Done Lock

**Status:** AUTHORITATIVE RELEASE GATE  
**Created:** 2026-09-11  
**Purpose:** prevent local QA success, partial skill migration, or short-term routing fixes from being mistaken for completion of the PO Agent program.

This document is intentionally short and binary. Future implementation plans, owner assignments and GigaCode QA assignments MUST preserve these gates. A stage may be GREEN while the product remains `RELEASE_READY=NO`.

## 1. Product DoD — non-negotiable

PO Agent is NOT done until all of the following are true:

1. **Skill-native V4 is the primary orchestration path.**
   - Natural-language requests are solved by progressive skill discovery and plan -> act -> observe -> re-plan.
   - No required semantic-prepass schema, surname router, phrase router, hardcoded member/sprint/space list, or entity-specific production branch is needed for supported requests.
   - New source entities (member/sprint/release/etc.) become usable through source-backed capabilities without production-code edits when the underlying source supports them.

2. **All 54 production user-facing skills are migrated/certified.**
   - The 54 skills are a composable procedural capability library, not 54 independent phrase handlers.
   - Every skill is terminally classified; no silent skip.
   - Every source-supported skill is GREEN through Agent A / independent Oracle B / real Browser C.
   - Certification covers applicable combinations of approved spaces `WMB`, `STS`, `OLP`, `DMS`, `CRPV` and authoritative team/source identities.
   - **Skill extensibility is pluginized before bulk migration:** adding a new skill MUST NOT require edits to Agent Core, planner logic, or runtime orchestration.
   - Skills/capabilities are discovered through registries and stable extension contracts, not hardcoded `_handlers`, `_build_skill_catalog()` branches or domain-specific runtime conditionals.
   - The stable extension surface includes at minimum `SkillSpec`, `CapabilitySpec`, `CapabilityHandler`, `CompletionContract`, and `UIContract` (names may vary, semantics may not).
   - Completion conditions belong to the skill/procedure contract; they MUST NOT be implemented as `if skill_id == ...` logic inside Agent Core.
   - UI/widget metadata belongs to the skill/UI contract so a new skill can expose its presentation needs without editing core orchestration.
   - **Mandatory extensibility proof:** a synthetic 55th dummy skill is added only as a plugin/artifact, with **zero Agent Core/planner/runtime code changes**; it must be discovered in the compact catalog, loadable by the planner, able to invoke a registered capability, honor its completion contract, and expose its UI contract. This gate must be GREEN before progressive migration of the remaining 54-skill catalog.

3. **REAL AS21/SWTR remains authoritative — live-read only for production facts.**
   - No local DB, SQLite/local task store, sync snapshot, cache, fixture, fake/frozen source, remembered count or previous answer can become production truth or Oracle B.
   - **A production factual capability MUST NOT read `/api/v1/tasks` or any equivalent local-store collection as its source of truth.**
   - The accepted factual path is `V4 capability -> governed live Task API read facade -> MCP-SWTR -> REAL AS21` (or another explicitly certified live REAL-AS21 read facade).
   - Local storage may exist for technical/runtime purposes only; it MUST NOT be used as a production fallback when a live route is unavailable or empty.
   - If the required live source/read surface is unavailable, return typed `SOURCE_UNAVAILABLE` / `SOURCE_CONDITIONAL`; never fall back to local storage and never convert an outage into a legitimate zero/empty result.
   - `REAL_EMPTY` is valid only when the live authoritative source proves an empty result.
   - Collections require exact task-key parity, not only count/prose parity.
   - Future QA must statically and dynamically prove that factual skills did not touch local task-store reads.

4. **Agentic composition works for unseen combinations.**
   Mandatory benchmark families include:
   - person + space + status;
   - person + sprint + status;
   - task -> assignee -> tasks;
   - current sprint -> downstream task query;
   - task/release/sprint/team analytical compositions where source contracts support them.
   The agent must construct trajectories from skills/capabilities rather than depend on dedicated phrase-specific code.

5. **Execution remains governed and safe.**
   - LLM reasoning may be flexible; external actions must use registered typed capabilities.
   - Requested constraints are preserved or explicitly clarified.
   - Deterministic postcondition validation blocks contradictory source rows/counts.
   - Ordinary production execution does not generate arbitrary local Python, expose credentials, or call unregistered endpoints.
   - Unauthorized AS21 writes = 0; secret leakage = 0.

6. **UI is product truth, not an afterthought.**
   - Real Browser C uses V4, not legacy V3/H1B.
   - Session/new-dialog isolation is proven.
   - Every screen/widget/action has data lineage to V4 capability/trajectory/source.
   - Required states are explicit: loading, success, real-empty, partial, not-found, source-unavailable, error.
   - Zero unexplained blank/zero/wrong-space widgets.

7. **Self-improvement is implemented, not merely planned.**
   A separate Learning Reviewer must be able to:
   - capture the failed/criticized trajectory;
   - independently recheck authoritative source truth;
   - determine whether a mismatch is provable;
   - identify the first failing boundary without requiring the user to diagnose it;
   - create a generalized procedural skill/policy candidate;
   - validate it on replay plus independent analogous cases;
   - version/promote or reject it;
   - persist promoted learning where supported;
   - rollback to the previous version.

   Learning MUST NOT memorize entity facts such as current task counts, task ownership or sprint contents as durable truth.

8. **Skills/policies are modifiable artifacts under governance.**
   - Agent learning may evolve procedural skill definitions, planner policies, capability-selection hints, trajectory examples and validation/postcondition rules.
   - Each promoted artifact has version, provenance/evidence, certification result and rollback metadata.
   - Silent self-edit of arbitrary production Python/config/secrets is forbidden.

9. **Performance and operability are acceptable after correctness.**
   - Latency is observable by semantic/planner/capability/source/synthesis stage.
   - Ordinary factual requests operate at practical interactive latency after functional GREEN.
   - Long QA runs are checkpointed/resumable and do not silently skip timed-out cases.

10. **Release gate is explicit.**
    `RELEASE_READY=YES` is forbidden until items 1–9 are all proven GREEN and P0 defects = 0.

## 2. V4 decision/rollback checkpoint

Pre-V4 rollback checkpoint remains:

`1a87e3e3ea5da14ef44da6c4515dbf2961df0423`

The independently certified V4 POC rollback checkpoint is:

`0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`

Rules:
- V3/H1B remains a rollback/reference path until V4 proves the full 54-skill A/B/C gate.
- V4 is the primary architectural direction because it removes the mandatory semantic-prepass bottleneck.
- A RED in an individual V4 capability is not by itself a reason to return to V3; first distinguish a bounded implementation defect from failure of the skill-native architecture.
- If V4 repeatedly cannot satisfy unseen-entity composition, exact source parity, governed execution, or progressive skill loading after bounded architectural fixes, pause migration and review against this checkpoint before further investment.
- Do not delete the rollback point or legacy reference path before V4 full-catalog certification.

### POC reliability stop-rule
A188 closed the representative backend POC GREEN; A190 proved plugin extensibility; A191 proved Browser C/UI cutover. Backend POC remediation is closed. Future REDs inside V4-CATALOG are bounded catalog/capability defects unless evidence proves an architectural regression.

This rule exists specifically to prevent an infinite fix/test loop from being mistaken for architectural progress.

## 3. Mandatory milestone gates

### Gate V4-P0C
Prove representative skill-native operation across task/sprint/identity/multi-step/safety scenarios using REAL AS21. This proves architecture viability only; it is NOT product DoD.

### Gate V4-PLUGIN
Before mass migration of the 54-skill catalog, remove concrete skill/capability wiring from Agent Core and prove a pluginized registry/discovery model.

Required GREEN evidence:
- adding/removing a skill does not require Agent Core, planner-logic or runtime-orchestration edits;
- capability handlers are resolved from a governed registry rather than a core hardcoded mapping;
- skill procedure, completion contract and UI/widget contract are loadable artifacts;
- compact catalog discovery remains progressive;
- the synthetic **55th dummy skill** passes discovery -> load -> capability execution -> completion -> UI-contract propagation with **zero core-code edits**.

This gate is a hard prerequisite for bulk `V4-CATALOG` migration. Do not migrate dozens of skills into hardcoded core structures and plan to refactor later.

### Gate V4-BROWSER
Wire V4 to the real UI and prove Browser C parity on the same natural-language scenarios that exposed V3 weaknesses, including complete widget/state handling through `UIContract` metadata where applicable.

### Gate V4-CATALOG
Migrate the full 54-skill catalog to progressive/composable V4 skills and reusable capabilities through the pluginized registry. Adding each migrated skill must not change Agent Core architecture. Every factual skill must also pass the live-source-only invariant: no `/api/v1/tasks`/local-store truth or fallback.

### Gate V4-54-ABC
No-skip full catalog certification: Agent A vs independent REAL AS21 Oracle B vs real Browser C across applicable approved spaces/team identities.

### Gate V4-LEARNING
Learning Reviewer demonstrates autonomous diagnosis + generalized skill/policy modification + independent validation + persistence + rollback. A static agent cannot pass final DoD.

### Gate V4-UI
Complete UI lineage/state/interaction certification on V4.

### Gate V4-RELEASE
Security, source authority, session isolation, performance, recovery, P0=0, full DoD audit. Only this gate may set `RELEASE_READY=YES`.

### Deferred milestone — V5 analytical orchestration
`DEFERRED_TO_V5 — DO NOT IMPLEMENT DURING V4`.

GVS5H-inspired multi-agent analytical orchestration (fresh workers + typed shared ledger + verifier/A-B evaluation) is explicitly deferred until V4 is fully operational with all 54 skills and working UI/widgets. It must not expand V4 scope or delay V4 release readiness.

## 4. Anti-regression rule for future assignments

Every future owner/QA assignment must answer these questions before claiming a milestone GREEN:

- Does this move us toward skill-native composition rather than add another phrase/entity special case?
- Is source truth REAL AS21 and independently verifiable?
- Does every factual production read stay on a certified live source path, with **zero local-store fallback**?
- Is a reported `REAL_EMPTY` proven by the live authoritative source rather than by an empty local cache/store?
- Is the behavior reusable for an unseen person/sprint/space/release?
- Does it preserve progressive skill loading and typed capability governance?
- **Could the same new skill be added as a plugin without editing Agent Core/planner/runtime?**
- **Are completion and UI behavior declared in skill contracts rather than hardcoded into orchestration?**
- Does it keep the path open for Learning Reviewer to modify generalized procedural artifacts later?
- Has anything been done that would make the 54-skill A/B/C gate harder or less meaningful?

If the answer to any relevant question is no, the work must be treated as local remediation, not architectural progress.

## 5. Current status

```text
V4_ARCHITECTURE_DIRECTION = PRIMARY
V3_H1B = ROLLBACK_REFERENCE
V4_REPRESENTATIVE_POC = GREEN_A188
V4_SKILL_COMPLETION_CONTRACT = GREEN_A188
V4_DETERMINISTIC_POST_OBSERVATION_COMPLETION = PROVEN_GENERIC
V4_PLUGINIZED_SKILL_CAPABILITY_REGISTRY = GREEN_A190
V4_PLUGIN_DUMMY_55_GATE = GREEN_A190
V4_BROWSER_C = GREEN_A191
V4_LIVE_SOURCE_ONLY_INVARIANT = LOCKED_AFTER_A192
V4_CATALOG_TASK_WAVE_1_20 = GREEN_A195D
V4_EXISTING_27_SKILL_MATRIX = 20_GREEN_7_SOURCE_CONDITIONAL_0_RED_A200
V4_CLARIFICATION_CONTINUATION = GREEN_A201
V4_PRE_WAVE_S_ZERO_RED_GATE = GREEN_A201
V4_POST_GREEN_HYGIENE = GREEN_A202
V4_PRE_WAVE_S_CHECKPOINT = checkpoint/v4-pre-wave-s-a202@e580489950e5a149a6a740cb8779dfdb0351d471
V4_POST_A202_TEST_COMPAT_CLEANUP = CLOSED
V4_A204_HEALTH_DIALOG_DIAGNOSTIC = RED
V4_A204_OWNER_REMEDIATION = IMPLEMENTED_PENDING_A205
V4_A205_ATTEMPT_1 = RED_ROBUST_PLANNER_INTERFACE
V4_A205_ATTEMPT_2 = RED_PLUGINIZED_LITERAL_GUARD_INTERFACE
V4_RUNTIME_INTERFACE_PARITY_FIX = GREEN_PREFLIGHT
V4_EXISTING_SKILL_ADVERSARIAL_GATE = GREEN_A205
V4_A205_27_SKILL_MATRIX = 20_GREEN_7_SOURCE_CONDITIONAL_0_RED
V4_A205_BROWSER_C = GREEN_7_7
V4_A205_LOCAL_STORE_FACTUAL_READS = 0
V4_A205_PLUGIN_DUMMY_55 = GREEN
V4_A205_ROLLBACK_CHECKPOINT = checkpoint/v4-a205-green@1fd519105ba6612f535ad98a55cb1302f387ca43
V4_HISTORY_STATUS_SOURCE_DIAGNOSTIC = FIXABLE_RED
V4_HISTORY_STATUS_OWNER_FIX = VERIFIED_EXCEPT_STATUS_LABEL_PRESERVATION
V4_A206_REGATE_1 = RED_STATUS_LABEL_LOSS_ONLY
V4_HISTORY_SOURCE_STATUS_LABEL_FIX = GREEN_A206B
V4_A206B_ROLLBACK_CHECKPOINT = checkpoint/v4-a206b-green@f7f846dee71b676fb0fc8d1d8f0d8aa23d521eaf
V4_WAVE_S_RELEASE_SEARCH_HELPER = SOURCE_CONDITIONAL_VERSION_DIRECTORY_502
V4_WAVE_S1 = GREEN_A207
V4_WAVE_S1_ROLLBACK_CHECKPOINT = checkpoint/v4-wave-s1-green@ce64264c868afd73743d5daafdeaee767e07adef
V4_PRE_S2_MANUAL_HARDENING = GREEN_A208B
V4_A208B_ROLLBACK_CHECKPOINT = checkpoint/v4-a208b-green@2e284fdab79072d95ba0bf86058b4648f4bb9d6c
V4_BATCH_POLICY = FIVE_SKILLS_DEFAULT
V4_WAVE_S2_A209 = RED_SOURCE_TIMESTAMP_PLUMBING
V4_WAVE_S2_OWNER_REMEDIATION = VERIFIED_GREEN_A210
V4_WAVE_S2_FIVE_SKILL_BATCH = GREEN_A210
V4_WAVE_S2_ROLLBACK_CHECKPOINT = checkpoint/v4-wave-s2-green-a210
V4_RELEASE_SEARCH = GREEN_A212
V4_RELEASE_SEARCH_ROLLBACK_CHECKPOINT = checkpoint/v4-release-search-green-a212
V4_RELEASE_HEALTH_LINKAGE = SOURCE_BLOCKED_A212
V4_RELEASE_HEALTH_A213 = RED_LITERAL_GROUNDING_GUARD
V4_RELEASE_HEALTH_GUARD_FIX = GREEN_A214
V4_RELEASE_HEALTH = TERMINAL_SOURCE_CONDITIONAL_GREEN_A214
V4_RELEASE_REMEDIATION = CLOSED_A214
V4_RELEASE_HEALTH_ROLLBACK_CHECKPOINT = checkpoint/v4-release-health-source-conditional-a214
V4_FULL_54_SKILL_MIGRATION = RESUMED_POST_A214
V4_BATCH2 = GREEN_A215
V4_BATCH2_ROLLBACK_CHECKPOINT = checkpoint/v4-batch2-green-a215
V4_BATCH2_POST_GREEN_CAPACITY_UX_FIX = GREEN_A215B
V4_TEAM_CAPACITY = TERMINAL_SOURCE_CONDITIONAL_A215B
V4_TEAM_CAPACITY_REASON = REAL_AS21_TASK_ESTIMATES_UNAVAILABLE
V4_BATCH3_OWNER_IMPLEMENTATION = DONE_PAUSED_FOR_TIME_ACCOUNTING_FORENSIC
V4_TIME_ACCOUNTING_FORENSIC = GREEN_A215C_SOURCE_READY
V4_TIME_ACCOUNTING_OWNER_IMPLEMENTATION = GREEN_A215D
V4_TEAM_CAPACITY_OWNER_POLICY = GREEN_A215E
V4_TEAM_CAPACITY_PERIOD_NORMALIZATION = IMPLEMENTED_PENDING_A215F_QA
V4_TIME_ACCOUNTING_AGGREGATE_OWNER_IMPLEMENTATION = RED_A215F_REAL_EMPTY_COMPLETION
V4_ACTUAL_TIME_A215F = RED_COMPLETION_CONTRACT_REAL_EMPTY
V4_ACTUAL_TIME_REAL_EMPTY_FIX = GREEN_A215F2
V4_ACTUAL_TIME_AGGREGATION = GREEN_A215F2
V4_ACTUAL_TIME_ROLLBACK_CHECKPOINT = checkpoint/v4-actual-time-green-a215f2
V4_MEMBER_TIME_ACCOUNTING = GREEN_A215G
V4_MEMBER_TIME_ROLLBACK_CHECKPOINT = checkpoint/v4-member-time-green-a215g
V4_BATCH3 = GREEN_A216
V4_BATCH3_ROLLBACK_CHECKPOINT = checkpoint/v4-batch3-green-a216
V4_BATCH4_OWNER_IMPLEMENTATION = RED_A217_NL_ROUTING_EARLY_READY
V4_BATCH4_A217 = RED_NL_ROUTING_EARLY_READY_BYPASSES_TYPED_SC
V4_RELEASE_RESOLVER_COMPLETION_FIX = RED_A217B_DEFERRED_TURN_OVEREXTENSION
V4_BATCH4_A217B = RED_DEFERRED_TURN_OVEREXTENSION
V4_RELEASE_RESOLVER_TERMINAL_GUIDANCE_FIX = RED_A217C_ROBUST_SIGNATURE_DRIFT
V4_BATCH4_A217C = RED_ROBUST_PLANNER_SIGNATURE_DRIFT
V4_ROBUST_PLANNER_SIGNATURE_PARITY_FIX = GREEN_A217D
V4_BATCH4 = GREEN_A217D
V4_BATCH4_ROLLBACK_CHECKPOINT = checkpoint/v4-batch4-green-a217d
V4_SELF_INTROSPECTION_UX = GREEN_A218
V4_SELF_INTROSPECTION_ROLLBACK_CHECKPOINT = checkpoint/v4-self-introspection-green-a218
V4_LIVE_REGISTRY_A218 = 62_SKILLS_11_PLUGINS
V4_CANONICAL_54_COVERAGE_A218 = 48_OF_54
V4_CANONICAL_54_MISSING_A218 = release.forecast,po.attention_queue,po.daily_brief,po.status_report,po.reminder_draft,po.local_task_draft
V4_BATCH5_PO = GREEN_A219R
V4_BATCH5_PO_ROLLBACK_CHECKPOINT = checkpoint/v4-batch5-green-a219r
V4_CANONICAL_54_COVERAGE_A219R = 53_OF_54
V4_BATCH6_RELEASE_FORECAST = GREEN_A220
V4_CANONICAL_54_COVERAGE_A220 = 54_OF_54
V4_CANONICAL_54_MISSING_A220 = NONE
V4_LIVE_REGISTRY_A220 = 68_SKILLS_13_PLUGINS
V4_CANONICAL54_ROLLBACK_CHECKPOINT = checkpoint/v4-canonical54-green-a220
V4_FULL_54_ABC = RED_A221R_ROW49_TASKS_SEARCH_SPACE_ONLY
V4_A221_ROW10 = OWNER_FIX_IMPLEMENTED_PENDING_A221R
V4_A221_CERTIFIED_ROWS_1_9 = GREEN_RESUMABLE
V4_FULL_54_ABC_RESUME_FROM = ROW_10
V4_UI_WIDGET_LINEAGE = BLOCKING_REMEDIATION_AFTER_A221
V4_UI_ZERO_DEFAULT_POLICY = ZERO_ONLY_WHEN_SOURCE_PROVEN
V4_UI_NEXT_AFTER_A221 = FIX_C_FAILURES_BEFORE_LEARNING_REVIEWER
V4_FULL_54_ABC = NOT_DONE
V4_LEARNING_REVIEWER = NOT_DONE
V4_GOVERNED_SKILL_SELF_MODIFICATION = NOT_DONE
V4_FULL_UI_ACCEPTANCE = NOT_DONE
V5_GVS5H_ANALYTICAL_ORCHESTRATION = DEFERRED_TO_V5
RELEASE_READY = NO
```

## 6. Deterministic post-observation completion (Assignment 187)

V4 production reliability hardening: a typed **skill completion contract** (`agent_core_v4_completion.py`) deterministically satisfies loaded skills from validated trajectory observations, eliminating dependence on the stochastic model successfully minting a terminal `READY` JSON decision.

Key properties:
- Per-skill `CompletionRequirement` tuples declare which capability observations (with required data fields, argument bindings, and resolved-constraint coverage) prove the skill is complete.
- Evaluated only against typed trajectory state — no query text, no entity literals, no semantic prepass.
- Fails closed: not-found, ambiguous, source-failure states and uncontracted skills retain normal planner behavior.
- Runtime short-circuits to deterministic synthesis after a validated capability observation proves every loaded skill's contract is satisfied.
- `completion=runtime_contract` marker in trajectory/response distinguishes runtime-generated completion from model `planner_ready`.
- Recovery-time READY remains forbidden by the planner protocol.
- The runtime path never uses model-recovered READY text and cannot fabricate an answer without observations.
- Typed clarification continuation is part of the same Harness execution: session + clarification id restore generic loaded-skill state, validated observations and pending completion objectives.
- A clarification answer may add a confirmed constraint, but must not reset or weaken the original pending completion contract.
- Continuation state is generic control-plane state only; no skill/entity-specific branch may be added to Agent Core/API to preserve it.
- Multi-hop clarification must preserve the same original completion goal and already validated constraints across every clarification hop.
- Completed-turn conversational context may contain only source-validated canonical entities (for example space/sprint/release/person ids), is session-bounded/TTL-bounded, and must never become factual truth without source-backed observations.
- Resolver/identity-only observations must never be treated as fulfillment of a requested collection, metric or analysis deliverable.
- Catalog presence means a skill/capability is declared, not that its live source is currently available; source-dependent skills must fail closed / SOURCE_CONDITIONAL when their certified read surface is unavailable.
- Adding these generic control-plane guarantees must not require per-skill branches in Agent Core; skill-specific behavior remains in plugin contracts/handlers.
- Wave S must include a plugin-only `release.search` helper that searches/releases versions from bounded REAL AS21 source data. It must remain distinct from `task.search_release` (tasks by known release) and `release.resolve` (validation of a known release id).

V4 remains single-planner / skill-native / governed. This mechanism is a generic control-plane rule, not a query-specific fallback.

`DEFERRED_TO_V5`: GVS5H-inspired multi-agent orchestration (fresh workers + typed shared ledger + verifier) must NOT be implemented during V4.


### Five-skill batch lock
From A209 forward, owner migration should default to 5-skill batches. This changes only packaging/cadence, not architecture or evidence standards. Every batch still requires:
- registry-only skill addition;
- no Agent Core skill routing;
- explicit CompletionContract/UIContract;
- REAL AS21 authority and fail-closed source handling;
- Browser C;
- dummy-55/plugin invariant;
- rollback checkpoint after GREEN.

A SOURCE_CONDITIONAL skill does not force unrelated source-backed skills in the same batch to RED, provided the outage is independently proven and the skill fails closed without local/task-scan fabrication.

V4_A221_ROW10 = GREEN_A221R
V4_A221_CERTIFIED_ROWS_1_48 = GREEN_RESUMABLE
V4_A221R_ROW49 = OWNER_FIX_IMPLEMENTED_PENDING_A221R2
V4_FULL_54_ABC_RESUME_FROM = ROW_49

V4_A221R2_CANONICAL_MATRIX = 54_OF_54_GREEN
V4_A221R2_BROWSER_C = 54_OF_54_PASS
V4_A221R2_PHASE9 = 6_OF_6_GREEN
V4_A221R2_PHASE11 = PASS_ZERO_LOCAL_ZERO_MUTATIONS_ZERO_TENANT_WIDE
V4_A221R2_PHASE12 = P50_10_1S_P95_31_9S_ZERO_OVER_60S
V4_A221R2_PHASE13 = 13_OF_13_GREEN
V4_A221R2_PHASE8 = RED_23_OF_24_SPRINT_TO_ATTACHMENTS
V4_A221R3 = OWNER_FIX_IMPLEMENTED_PENDING_QA

V4_A221R3_FULL_FUNCTIONAL = GREEN
V4_A221R3_CANONICAL_MATRIX = 54_OF_54_GREEN
V4_A221R3_PHASE8_COMPOSITION = 24_OF_24_GREEN
V4_A221R3_BROWSER_C = 54_OF_54_PASS
V4_A221R3_SOURCE_AUDIT = ZERO_LOCAL_ZERO_MUTATIONS_ZERO_TENANT_WIDE
V4_A221R3_LATENCY = P50_10_1S_P95_31_9S_ZERO_OVER_60S
V4_A221R3_FULL_FUNCTIONAL_CHECKPOINT = checkpoint/v4-full-functional-green-a221r3@84b0ae28aa4c37b0e502f92f08738fab66dbd4f6
V4_UI_WIDGET_LINEAGE = ACTIVE_NEXT_OWNER_PHASE
V4_LEARNING_REVIEWER = BLOCKED_UNTIL_UI_GATE_GREEN

V4_TEAM_COMPETENCY_SOURCE = IMPLEMENTED_PENDING_A222_QA
V4_TEAM_COMPETENCY_SOURCE_OF_TRUTH = task-api/config/team_members.yaml
V4_TEAM_COMPETENCY_MATCH_TARGET = SOURCE_READY_AFTER_BOUNDED_REGATE
V4_TEAM_ASSIGNEE_RECOMMENDATION_TARGET = SOURCE_READY_AFTER_BOUNDED_REGATE
V4_TEAM_COMPETENCY_TENANT_WIDE_SCAN = FORBIDDEN

V4_A222 = RED_ZERO_OVERLAP_COMPLETION_AND_CASE_INSENSITIVE_LOAD_JOIN
V4_A222_OWNER_REMEDIATION = IMPLEMENTED_PENDING_A222R
V4_TEAM_COMPETENCY_TASK_SIGNALS = TITLE_DESCRIPTION_LABELS_COMPONENTS
V4_TEAM_COMPETENCY_LEVEL_INFERENCE = FORBIDDEN
V4_TEAM_COMPETENCY_RELEVANCE_SCORE = TASK_RELEVANCE_NOT_EMPLOYEE_SCORE

V4_A222R = RED_SOURCE_SIGNAL_PLUMBING_LABEL_COMPONENT
V4_A222R_OWNER_REMEDIATION = IMPLEMENTED_PENDING_A222R2
V4_TASK_SIGNAL_LABEL_MAPPING = SOURCE_BACKED
V4_TASK_SIGNAL_COMPONENT_MAPPING = SOURCE_BACKED

V4_A222R2_TEAM_COMPETENCY = GREEN
V4_TEAM_COMPETENCY_MATCH = SOURCE_READY
V4_TEAM_ASSIGNEE_RECOMMENDATION = SOURCE_READY
V4_TEAM_COMPETENCY_CHECKPOINT = checkpoint/v4-team-competency-green-a222r2@14f1842c99b6748a8e570b3311777d5573d37f3d
V4_COMPETENCY_REASONING_V2 = DEFERRED_TECH_DEBT_AFTER_UI_AND_AGENT_HARDENING
V4_UI_WIDGET_LINEAGE = ACTIVE_OWNER_PHASE

V4_UI_STATE_LINEAGE_BATCH1 = IMPLEMENTED_PENDING_A223
V4_UI_SHARED_RESULT_STATE_ADAPTER = IMPLEMENTED
V4_UI_RAW_MARKDOWN_RENDERING = REMEDIATED_PENDING_A223
V4_UI_FALSE_ZERO_POLICY = ZERO_ONLY_AFTER_SOURCE_BACKED_SUCCESS_OR_REAL_EMPTY
V4_UI_TEAM_CAPACITY_DEFAULT_40H = REMOVED
V4_UI_QUALITY_PREMATURE_REWORK = REMOVED
V4_UI_RELEASE_SOURCE_CONDITIONAL_ZEROES = REMEDIATED_PENDING_A223

V4_A223 = RED_QUALITY_DATA_SHAPE_NAN_READY
V4_A223_OWNER_REMEDIATION = IMPLEMENTED_PENDING_A223R
V4_UI_CAPABILITY_DATA_UNWRAP = SHARED_HELPER
V4_UI_NUMERIC_FINITE_GUARD = IMPLEMENTED

V4_A223R = RED_SPRINT_RISK_QUEUE_AND_THROUGHPUT_FIELD_MISMATCH
V4_A223R_OWNER_REMEDIATION = IMPLEMENTED_PENDING_A223R2
V4_UI_SPRINT_RISK_QUEUE_FIELD = queue
V4_UI_SPRINT_RISK_ROW_FIELDS = task_key_rank
V4_UI_SPRINT_THROUGHPUT_FIELD = throughput

V4_A223R2_UI_STATE_LINEAGE = GREEN
V4_UI_STATE_LINEAGE_CHECKPOINT = checkpoint/v4-ui-state-lineage-green-a223r2@e0f435d10b586fbb7bfb31c6e0e853496338e099
V4_UI_USABILITY_BATCH = IMPLEMENTED_PENDING_A224
V4_UI_OVERVIEW_INTERNAL_SCROLL = IMPLEMENTED
V4_UI_TASKS_BY_SPACES_FULL_SCOPE = IMPLEMENTED_PENDING_A224_SOURCE_PARITY
V4_UI_LOCAL_TASK_CRUD = IMPLEMENTED_PENDING_A224
V4_UI_PREDICTABILITY_EXPLANATION = IMPLEMENTED
V4_UI_RELEASE_SOURCE_LIMITATION = ACCEPTED_UNTIL_AS21_LINKAGE
V4_UI_TEAM_SPACE_SCOPE_AND_AUTO_40H_WEEK = IMPLEMENTED_PENDING_A224
V4_UI_AGING_SPACE_SCOPE = IMPLEMENTED_PENDING_A224
V4_UI_VISUAL_DESIGN = BLOCKED_UNTIL_A224_GREEN

V4_A224 = RED_P2_FULL_SPACE_COUNTS_UNAVAILABLE_PAGINATION_CAP
V4_A224_FIRST_RED = D_A224_1_SPACE_ROW_MATERIALIZATION_10K_CAP
V4_A224_OWNER_REMEDIATION = IMPLEMENTED_PENDING_A224R
V4_SPACE_TASK_COUNT_ROUTE = BOUNDED_TOTAL_ELEMENTS
V4_SPACE_TASK_COUNT_ERROR_ISOLATION = PER_SPACE_TYPED
V4_SPACE_TASK_STATUS_BREAKDOWN = SOURCE_CONDITIONAL_NOT_FABRICATED
V4_A224_FALSE_ZERO_FIX = IMPLEMENTED_PENDING_A224R
V4_UI_VISUAL_DESIGN = BLOCKED_UNTIL_A224R_GREEN

V4_A224R = RED_COUNT_ROUTE_SOURCE_METADATA_ABSENT
V4_A224R_SCOPE_CORRECTION = TEAM_ASSIGNEE_TASKS_NOT_WHOLE_SPACE
V4_OVERVIEW_SPACE_SUMMARY_SCOPE = CONFIGURED_TEAM_ASSIGNEES
V4_OVERVIEW_SPACE_SUMMARY_WHOLE_SPACE_SCAN = FORBIDDEN
V4_OVERVIEW_ATTENTION_SCROLL = FULL_QUEUE_RENDERED_IN_SCROLL_CONTAINER
V4_TASKS_AS21_STATUS_FILTER = IMPLEMENTED_PENDING_A224R2
V4_TASKS_LOCAL_STATUS_FILTER = IMPLEMENTED_PENDING_A224R2
V4_A224R2 = PENDING_QA

V4_A224R2_UI_USABILITY = GREEN
V4_UI_USABILITY_CHECKPOINT = checkpoint/v4-ui-usability-green-a224r2@612116894572f72af4f024486799458d3870d539
V4_UI_VISUAL_DESIGN = ACTIVE_OWNER_PHASE
V4_UI_RESPONSIVE_ATTENTION_OVERFLOW = NON_BLOCKING_TO_FIX_IN_DESIGN
V4_LEARNING_REVIEWER = BLOCKED_UNTIL_VISUAL_DESIGN_AND_BROWSER_UX_GREEN

V4_A225_VISUAL_DESIGN = IMPLEMENTED_PENDING_QA
V4_UI_DESIGN_SOURCE = 2026_SCHETCHIKOV_COOKBOOK
V4_UI_DISTINCT_PAGE_BACKGROUNDS = SIX
V4_UI_SHARED_GLASS_THEME = IMPLEMENTED
V4_UI_480_ATTENTION_OVERFLOW_FIX = IMPLEMENTED_PENDING_A225
V4_UI_DESIGN_BACKEND_DELTA = ZERO_EXPECTED
V4_LEARNING_REVIEWER = BLOCKED_UNTIL_A225_AND_PO_UX_ACCEPTANCE_GREEN

V4_A225_UI_VISUAL_DESIGN = GREEN
V4_UI_VISUAL_DESIGN_CHECKPOINT = checkpoint/v4-ui-visual-design-green-a225@09bcbd22d87b478396970d0ddf89cbf6d531d421
V4_A226_UI_POLISH_SNAPSHOTS = IMPLEMENTED_PENDING_QA
V4_UI_STRUCTURED_TABLE_DARK_THEME = IMPLEMENTED_PENDING_A226
V4_UI_TEAM_UTILIZATION_SOURCE = team.utilization_actual
V4_UI_TEAM_CAPACITY_ESTIMATE_SKILL = REMAINS_SOURCE_CONDITIONAL_NOT_USED_FOR_ACTUAL_UTILIZATION
V4_UI_TOPBAR_PRODUCTS = OLAP_DATAMARTS_ONLY
V4_UI_AGING_SCOPE = CONFIGURED_TEAM_ASSIGNEES_BY_SPACE
V4_UI_PAGE_SNAPSHOT_STORE = SESSION_STORAGE
V4_UI_PAGE_REFRESH_POLICY = MANUAL_NO_BACKGROUND_POLLING
V4_FINAL_BROWSER_UX = BLOCKED_UNTIL_A226_GREEN
V4_LEARNING_REVIEWER = BLOCKED_UNTIL_FINAL_PO_BROWSER_UX_GREEN

V4_A226 = RED_SOURCE_TIMESTAMP_PLUMBING
V4_A226_FIRST_RED = TEAM_AGING_ASSIGNEE_ROUTE_MISSING_CREATED_AT
V4_A226_OWNER_TIMESTAMP_REMEDIATION = IMPLEMENTED_PENDING_A226R
V4_ASSIGNEE_ROUTE_CREATED_AT = PLUMBED
V4_ASSIGNEE_ROUTE_UPDATED_AT = PLUMBED
V4_ASSIGNEE_ROUTE_DEADLINE = PLUMBED
V4_TASKS_SEARCH_CONTEXT_PERSISTENCE = IMPLEMENTED_PENDING_A226R
V4_LOCAL_TASK_DEADLINE_TAG_PRIORITY_UX = IMPLEMENTED_PENDING_A226R
V4_QUALITY_CONTEXT_PERSISTENCE = IMPLEMENTED_PENDING_A226R
V4_SPRINT_RELEASE_SINGLE_REFRESH_CONTROL = IMPLEMENTED_PENDING_A226R
V4_WORKSPACE_BRAND = PLATFORM_V
V4_DAILY_BRIEF_RICHNESS = RESTORED_PENDING_A226R
V4_A226R = PENDING_QA

V4_A226_SECOND_RED = TASK_DETAILS_PLACEHOLDER_QUERY
V4_A226_TASK_DETAILS_PLACEHOLDER_FIX = IMPLEMENTED_PENDING_A226R
V4_TASKS_UNSELECTED_INTELLIGENCE_QUERY = FORBIDDEN
V4_TASKS_PAGE_REVISIT_EXTRA_POST = ZERO_EXPECTED

V4_A226R = RED_P3_UNSCOPED_TEXT_SEARCH_SOURCE_SCALE
V4_A226R_FIRST_RED = TASK_TEXT_SEARCH_LARGE_SPACE_FANOUT
V4_TASK_TEXT_SEARCH_PER_SPACE_ISOLATION = IMPLEMENTED_PENDING_A226R2
V4_TASK_TEXT_SEARCH_COMPLETENESS_METADATA = IMPLEMENTED_PENDING_A226R2
V4_TASKS_UI_SEARCH_MODES = TEXT_ASSIGNEE_STATUS_SPRINT_RELEASE
V4_TASKS_TEXT_SEARCH_SPACE_SCOPE = EXPLICIT_UI_SELECTOR
V4_TASK_DRAWER_AGENT_LAUNCHER_OVERLAP = FIXED_PENDING_A226R2
V4_SNAPSHOT_TIMESTAMP_LOCALE = RU_RU_PENDING_A226R2
V4_PAGE_REFRESH_MAX_UI_WAIT = 65_SECONDS_PENDING_A226R2
V4_QUALITY_AGING_IDENTICAL_REFRESH = LIVE_REREAD_PENDING_A226R2
V4_SPRINT_FORENSIC_ID = DMS-SPRNT-3
V4_RELEASE_UI_EXPECTATION = HONEST_SOURCE_CONDITIONAL
V4_A226R2 = PENDING_QA

V4_A226R2 = RED_P2_SPACE_SELECTOR_AND_STATUS_SCOPE
V4_A226R2_FIRST_RED = TASKS_SPACE_SELECTOR_DROPPED_ON_SUBMIT
V4_A226R2_SECOND_RED = STATUS_SEARCH_UNSCOPED_ALL_SPACES
V4_TASKS_SEARCH_SPACE_PERSISTENCE = FIXED_PENDING_A226R3
V4_TASKS_STATUS_SEARCH_SPACE_SCOPE = REQUIRED_AND_FIXED_PENDING_A226R3
V4_TASK_QUERY_PARTIAL_TEST_ENDPOINT_ARGS = FIXED
V4_A226R3 = PENDING_QA

V4_A226R3 = GREEN
V4_A226R3_VERDICT = AGENT_CORE_V4_UI_POLISH_SNAPSHOT_GREEN_A226R3
V4_A226R3_CHECKPOINT = checkpoint/v4-ui-polish-snapshot-green-a226r3@486747298bc812bebab64a86b81585a202ab6ccc
V4_FINAL_BROWSER_UX = GREEN_A226R3_PENDING_PO_SIGNOFF
V4_TASKS_TEXT_AND_STATUS_SCOPE = SOURCE_EXACT
V4_SPRINT_FORENSIC_DMS_SPRNT_3 = GREEN
V4_RELEASE_FORENSIC = GREEN_TYPED_SOURCE_LIMITATION
V4_UI_NONBLOCKING_F1_DRAWER_X = TECH_DEBT
V4_UI_NONBLOCKING_F2_REFRESH_TIMEOUT_RACE = TECH_DEBT
V4_UI_NONBLOCKING_F3_QUALITY_SHARED_REFRESH = TECH_DEBT
V4_UI_NONBLOCKING_F4_WMB_24Q1_ROUTING = TECH_DEBT
V4_RELEASE_HARDENING = NEXT_AFTER_PO_SIGNOFF

V4_PO_SIGNOFF_A226R3 = REOPENED_BY_OWNER_FEEDBACK
V4_A227 = PENDING_QA
V4_A227_SCOPE = NATURAL_LANGUAGE_TASK_SEARCH_REFRESH_RELIABILITY_QUALITY_AGING
V4_TASKS_UI_SEARCH = SINGLE_NATURAL_LANGUAGE_FIELD
V4_TASKS_MODE_BUTTONS = REMOVED
V4_TASKS_SPACE_SELECTOR = REMOVED
V4_TASKS_QUERY_EXECUTION = AGENT_SKILL_NATIVE
V4_SNAPSHOT_REFRESH_TIMEOUT = 120_SECONDS
V4_QUALITY_AGING_REFRESH = ISOLATED_FROM_TASK_QUALITY_REFRESH
V4_PO_SIGNOFF = PENDING_A227

V4_A227 = RED_PREEXISTING_PLANNER_RELIABILITY_PERSON_COMPOSITION
V4_A227_P0 = GREEN
V4_A227_P1_OVERVIEW_REFRESH = GREEN
V4_A227_P2_TASKS_NL_UI = GREEN
V4_A227_FIRST_RED = P3_PERSON_MULTI_CONSTRAINT_PLANNER_RELIABILITY
V4_A227_FALSE_ZERO = SPRINT_DISCOVER_STATUS_LITERAL
V4_A227R_REPEATED_PROVIDER_REPAIR = CONSTRAINED_AND_DETERMINISTIC_PENDING_QA
V4_A227R_RECOVERY_READY_SHORTCUT = FORBIDDEN
V4_A227R_ATTACHMENT_STATUS_SCHEMA = IMPLEMENTED_PENDING_QA
V4_A227R_ATTACHMENT_STATUS_FILTER = IMPLEMENTED_PENDING_QA
V4_A227R_PROGRESS_STATUS_PREDICATE = STATUS_TYPE_PROGRESS_PENDING_QA
V4_A227R_REGRESSION_REPEATED_COMPOSITE_REPAIR = ADDED
V4_A227R_REGRESSION_SPRINT_PROGRESS_COLLECTION = ADDED
V4_A227R_REGRESSION_ATTACHMENT_STATUS_INTERSECTION = ADDED
V4_A227R = PENDING_QA_P3_TO_P7
V4_RELEASE_HARDENING = BLOCKED_PENDING_A227R
V4_LEARNING_REVIEWER = BLOCKED_DO_NOT_START
V4_PO_SIGNOFF = BLOCKED_PENDING_A227R

V4_A227_PRE_GATE = ACTIVE_UI_PARITY
V4_A227_EXTRA_CORE_REPAIR_FROM_OWNER_PASS = REVERTED
V4_A227_CORE_POLICY = NO_NEW_CORE_ROUTING_FOR_UI_PARITY
V4_A227_TASKS_NL_ENDPOINT = SAME_AGENT_QUERY_ENDPOINT
V4_A227_TASKS_FIND_SAME_QUERY = FORCE_ONE_LIVE_RERUN
V4_A227_TASKS_REVISIT = ZERO_AUTO_POST_EXPECTED
V4_RELEASE_FORECAST_PLUGIN = ALREADY_SOURCE_READY
V4_RELEASE_FORECAST_UI = WIRED_PENDING_PRE_GATE
V4_RELEASE_FORECAST_FALSE_METRIC = FORBIDDEN
V4_A227R = PAUSED_UNTIL_UI_PARITY_PRE_GATE_GREEN

V4_A227_SPRINT_PREDICTABILITY_DEFECT = UI_CONTRACT_FIELD_MISMATCH
V4_SPRINT_PREDICTABILITY_PLUGIN_FIELD = predictability_RATIO
V4_SPRINT_PREDICTABILITY_UI_PERCENT = RATIO_TIMES_100
V4_SPRINT_PREDICTABILITY_BASELINE = AUTHORITATIVE_COMMITTED_ONLY
V4_SPRINT_PREDICTABILITY_CURRENT_SCOPE_FALLBACK = FORBIDDEN
V4_SPRINT_PREDICTABILITY_UI = FIXED_PENDING_PRE_GATE

V4_A227_CORE_RECONCILIATION = COMPLETE
V4_A227_CORE_BASELINE = db5e35f1b378b6ffde0c10085af8b68e4bf1e6b5
V4_A227_CORE_DIFF_AGENT_CORE_V4 = ZERO
V4_A227_CORE_DIFF_RELIABLE = ZERO
V4_A227_CORE_DIFF_ROBUST = ZERO
V4_A227_CORE_DIFF_LLM_REAL = ZERO
V4_A227_CORE_TEST_DIFF_RELIABLE = ZERO
V4_A227_CORE_TEST_DIFF_ROBUST_PROTOCOL = ZERO
V4_A227_PRE_GATE = READY_FOR_RERUN_P0

V4_A227_UI_PARITY_PRE_GATE_R2 = GREEN
V4_A227_CORE_RECONCILIATION = PROVEN_ZERO_DIFF
V4_A227_TASKS_DIRECT_AGENT_PARITY = GREEN
V4_A227_SPRINT_PREDICTABILITY_UI = GREEN_TYPED_SOURCE_UNAVAILABLE
V4_A227_RELEASE_FORECAST_UI = GREEN_TYPED_SOURCE_UNAVAILABLE
V4_A227_PRE_GATE_SOURCE_AUDIT = ZERO_LOCAL_ZERO_TENANT_WIDE
V4_A227R = RESUME_P3_TO_P7
V4_PO_SIGNOFF = BLOCKED_PENDING_A227R

V4_A227R = RED_P3C_LOCALIZED_STATUS_FALSE_ZERO
V4_A227R_P3C_SPRINT_RESOLUTION = GREEN
V4_A227R_P3C_ROOT_CAUSE = STATUS_LANGUAGE_NORMALIZATION
V4_A227R2_STATUS_NORMALIZATION_SEAM = PLUGIN_BINDING
V4_A227R2_CORE_DIFF = ZERO
V4_A227R2_IN_PROGRESS_DOMAIN_NORMALIZER = IMPLEMENTED
V4_A227R2_UNKNOWN_STATUS_LITERAL_PRESERVATION = IMPLEMENTED
V4_A227R2 = PENDING_QA

V4_SPRINT_PREDICTABILITY_SINGLE_WIDGET = IMPLEMENTED
V4_SPRINT_PREDICTABILITY_NO_BASELINE_DISPLAY = N_A_WITH_EXPLICIT_REASON
V4_SPRINT_PREDICTABILITY_DUPLICATE_WIDGET = REMOVED
V4_SPRINT_PREDICTABILITY_UI_CLEANUP_CORE_DIFF = ZERO

V4_A227R2 = RED_P3B_PERSON_TEXT_PLANNER_RELIABILITY
V4_A227R2_P3C = GREEN_5_OF_5_PLUS_CONTROL
V4_A227R2_P3A = GREEN
V4_A227R2_P3D = GREEN
V4_A227R3_TEXT_PERSON_PATH = SINGLE_PLUGIN_CAPABILITY
V4_A227R3_PERSON_RESOLUTION = INSIDE_TASK_SEARCH_TEXT_HANDLER
V4_A227R3_CORE_DIFF = ZERO
V4_A227R3 = PENDING_QA

V4_PO_ACCEPTANCE = GREEN_A227R3
V4_PO_ACCEPTANCE_CHECKPOINT = checkpoint/v4-po-acceptance-green-a227r3
V4_FUNCTIONAL_SCOPE = FROZEN_POST_A227R3
V4_RELEASE_HARDENING = ACTIVE
V4_RELEASE_HARDENING_A228 = RESTART_RECOVERY
V4_LEARNING_REVIEWER = BLOCKED_UNTIL_RELEASE_HARDENING_AND_FINAL_DOD_AUDIT
RELEASE_READY = NO

V4_RELEASE_HARDENING_A228 = GREEN_RESTART_RECOVERY
V4_RELEASE_RECOVERY_CHECKPOINT = checkpoint/v4-release-recovery-green-a228
V4_RESTART_RECOVERY_LOCAL_FALLBACK = ZERO
V4_RESTART_RECOVERY_MUTATIONS = ZERO
V4_RESTART_RECOVERY_TENANT_WIDE_SCANS = ZERO
V4_RESTART_RECOVERY_SECRET_LEAKAGE = ZERO
V4_RELEASE_HARDENING_A229 = ACTIVE_LATENCY
V4_FUNCTIONAL_SCOPE = FROZEN
V4_LEARNING_REVIEWER = BLOCKED_UNTIL_RELEASE_HARDENING_AND_FINAL_DOD_AUDIT
RELEASE_READY = NO

V4_LATENCY_BASELINE_A229 = GREEN
V4_LATENCY_BASELINE_CHECKPOINT = checkpoint/v4-latency-baseline-green-a229@f1141aade7bffcd8cfd376174544d3f1172da08c
V4_A229R1_SPRINT_SINGLE_READ = IMPLEMENTED_PENDING_QA
V4_A229R1_ASSIGNEE_SPACE_TQL_PUSHDOWN = IMPLEMENTED_PENDING_QA
V4_A229R1_UI_SNAPSHOT_MAX_CONCURRENCY = TWO_PENDING_QA
V4_A229R1_CAPABILITY_STAGE_LOGGING = IMPLEMENTED_PENDING_QA
V4_A229R1_CROSS_REQUEST_FACT_CACHE = FORBIDDEN
V4_A229R1_PLANNER_TURN_REDUCTION = DEFERRED
V4_A229R1 = PENDING_QA
