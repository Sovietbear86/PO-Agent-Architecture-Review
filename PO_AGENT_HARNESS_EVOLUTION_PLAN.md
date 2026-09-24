# PO Agent — Authoritative Evolution Plan

**Status:** ACTIVE / Hermes-style architecture cutover approved  
**Current branch:** `feat/core8-real-query-hardening-v2`  
**Last reviewed:** 2026-09-10  
**Current baseline:** H1B is in final certification/closure after Assignments 143–174; source plane, typed CALL/FINAL loop, identity grounding, full-collection retrieval and Browser C multi-step are proven in focused gates, while routing/clarification consistency is being closed by Assignment 175.  
**Architecture decision:** stop broad point-fixing of legacy orchestration; preserve proven REAL AS21/source components and replace the upper Harness orchestration incrementally with a Hermes-inspired Agent Core.  
**Reference observations:** Hermes Agent is the architectural target pattern; PVM Guru is a behavioral/reference implementation only, not a codebase to copy.  
**Frontend status:** UI is part of acceptance truth; Harness-only GREEN is insufficient.  
**Purpose:** evolve PO Agent into a source-grounded, session-safe, contract-driven, tool-using, self-improving agent without throwing away the proven AS21 integration work.

> Historical QA GREEN is evidence, not product acceptance. A live browser counterexample reopens the affected gate. GigaCode remains QA-only. Production architecture and code changes are owner work.

---

## 0. Non-negotiable principles

1. REAL AS21/SWTR is authoritative for business facts.
2. Fixtures, local task DB, sync snapshots, fake/mock/frozen data and historical counts are never acceptance truth for live answers.
3. Natural-language understanding and planning remain LLM-first; deterministic code grounds entities, retrieves source data, applies filters/calculations and validates results.
4. Requested constraints are **immutable after semantic acceptance**. A constraint such as `space=WMB` may be canonicalized, but must never silently disappear before execution.
5. Every factual result must satisfy postconditions before it is released to the user. Example: a WMB query may not return DMS tasks.
6. Exact task-key-set equality against independent REAL AS21 Oracle B outranks counts/prose.
7. Browser/UI is an independent acceptance path C. Harness/API cannot impersonate UI.
8. New UI conversations, QA sessions and long-term memory scopes must be isolated.
9. Learning generalizes procedure/policy; it never memorizes task IDs, people-specific counts or source answers as truth.
10. Runtime learning cannot arbitrarily rewrite Python, source data, credentials or silently mutate capability contracts.
11. Ambiguity fails closed; source unavailability is never represented as a legitimate empty result.
12. GigaCode is QA/adversarial reviewer only and does not change production code.
13. Preserve proven lower-layer components instead of full rewrite.
14. Migrate by strangler pattern: new Agent Core runs alongside legacy Harness until capability families are certified and switched over.
15. A/B/C certification is required for every migrated capability family before legacy routing is retired.
16. **Reasoning freedom is allowed; execution freedom is bounded.** The LLM may compose multi-step trajectories dynamically, but every external action must pass through registered typed capabilities with explicit source, constraints, safety and postconditions.
17. **No code-generation-as-runtime-control-plane.** Unlike the observed PVM Guru pattern, PO Agent must not solve normal user requests by writing ad-hoc local Python scripts that carry credentials or call arbitrary endpoints. Generated code may be used only in isolated development/sandbox workflows, never as the production source-of-truth execution mechanism.
18. **The 54 skills are a capability library, not 54 phrase routers.** They must be progressively discoverable/composable and ultimately certified across the approved spaces and team identities.

---

## 1. Architecture decision and lessons from reference agents

Assignment 142 proved that the lower live assignee/source path can return fresh Oracle-parity data. Real browser tests then showed semantically wrong behavior despite backend GREEN. The dominant remaining risk therefore moved from MCP/source integration to orchestration-state, routing, constraint propagation and agent decision reliability.

Decision:

```text
DO NOT rewrite everything from zero.
DO preserve the proven source/data plane.
DO replace the upper orchestration plane incrementally.
DO use Hermes-style plan -> act -> observe -> re-plan behavior.
DO use PVM Guru as a behavioral benchmark, not as a production architecture template.
```

### Preserve

```text
REAL AS21
MCP-SWTR transport
Task API live read facades
canonical source normalization
point-read + NOT_FOUND semantics
server-side assignee/sprint/source routes
source evidence primitives
deterministic business calculations that pass certification
```

### Replace / evolve

```text
session/runtime ownership
semantic-state propagation
constraint handling
skill/capability resolution
result/postcondition validation
Learning Loop orchestration
progressive skill loading
heavy multi-step orchestration
legacy phrase/skill selectors
```

### PVM Guru observations locked into the plan — 2026-09-10

Observed useful behavior:
- the model can inspect a compact procedural skill/tool set and dynamically compose a multi-step source investigation;
- it can inspect source results, decide that another source call is required, and continue until it can answer;
- this feels more agentic than a fixed `intent -> one executor` pipeline and is the behavior PO Agent must reproduce;
- local procedural skill files are a useful mental model for **progressive procedural memory**.

Observed weaknesses that PO Agent must **not** copy:
- ad-hoc local Python generation/modification as the ordinary execution path;
- direct credential/environment handling inside arbitrary generated scripts;
- endpoint/schema knowledge embedded procedurally without a governed capability contract;
- no visible immutable accepted turn contract;
- no mandatory deterministic result/postcondition validation;
- no independent A/B Oracle gate before accepting a factual answer;
- risk of prose/count inconsistencies even when source rows are present.

Therefore the target is deliberately the middle ground:

```text
PVM Guru/Hermes reasoning flexibility
        +
PO Agent enterprise execution governance
        =
LLM plans freely over a governed capability toolbox,
while source truth, identity grounding, constraints, execution and validation remain deterministic/auditable.
```

Target remains an incremental preserve/evolve migration, not a greenfield rewrite.

---

## 2. Target Hermes-inspired architecture

The old one-shot picture is no longer sufficient. The target runtime is an explicit agent loop:

```text
Browser / API / other channels
          |
          v
+--------------------------+
| Session Manager          |
| conversation_id          |
| runtime_session_id       |
| memory_scope_id          |
+------------+-------------+
             |
             v
+--------------------------+
| LLM Semantic/Goal Pass   |
| user goal + raw facts    |
+------------+-------------+
             |
             v
+--------------------------+
| Grounding Layer          |
| canonical source IDs     |
+------------+-------------+
             |
             v
+--------------------------+
| Immutable Turn Contract  |
| goal + constraints       |
| required postconditions  |
+------------+-------------+
             |
             v
+--------------------------+
| Progressive Skill Index  |
| compact metadata only    |
+------------+-------------+
             |
             v
+--------------------------+
| LLM Planner              |
| typed CALL or FINAL      |
+------------+-------------+
             |
        CALL | FINAL
             |
             +----------------------+
             |                      |
             v                      v
+--------------------------+   +--------------------------+
| Capability Registry      |   | Response Synthesizer     |
| typed contract           |   | final user answer        |
+------------+-------------+   +--------------------------+
             |
             v
+--------------------------+
| Deterministic Executor   |
+------------+-------------+
             |
             v
+--------------------------+
| REAL Source Plane        |
| Task API -> MCP -> AS21  |
+------------+-------------+
             |
             v
+--------------------------+
| Observation Normalizer   |
| compact authoritative obs|
+------------+-------------+
             |
             v
+--------------------------+
| Result/Postcond Validator|
+------------+-------------+
             |
             +----> back to LLM Planner for another CALL
```

Key rule: the planner may choose **multiple sequential capabilities**. It does not have to know a dedicated hardcoded skill for every compound phrase. A request such as `Открытые задачи <человека> в спринте <SPRINT>` may naturally become:

```text
resolve/ground person
 -> inspect/validate sprint
 -> task search with assignee+sprint+status
 -> validate exact source rows
 -> FINAL
```

No surname router, no phrase-specific Python script.

Separate learning plane:

```text
User feedback / detected mismatch
    |
    v
Learning Reviewer
    |
    +--> immutable previous-turn trajectory snapshot
    +--> independent REAL AS21 recheck
    +--> mismatch proof / first failing boundary
    +--> generalized policy/skill candidate
    +--> sandbox/replay + independent A/B/C where applicable
    +--> versioned approve/promote or reject
    +--> rollback metadata
```

---

## 3. Core invariant: Immutable Turn Contract

After initial interpretation + grounding the runtime creates exactly one accepted contract:

```yaml
turn_id: <uuid>
goal: task_search
constraints:
  assignee: Kalachanov.V.V
  space: WMB
requested_constraints:
  - assignee
  - space
postconditions:
  - every_task.assignee == Kalachanov.V.V
  - every_task.space == WMB
source_authority: REAL_AS21
```

Rules:
- downstream planner steps may enrich metadata but cannot delete requested constraints;
- every selected capability must declare support for the constraints it receives;
- unsupported constraint -> typed clarification/unsupported result before unsafe execution;
- source result violating a postcondition -> fail closed and never show contradictory data in UI;
- multi-step execution carries the same accepted constraints/lineage through all observations;
- trace contains goal, grounding, selected skills, typed calls, source observations, validations and final synthesis.

This invariant is specifically intended to make `WMB query -> DMS evidence` and similar route drift impossible.

---

## 4. Architecture Evolution stages

### STAGE H1 — Agent Core + Session/Constraint Contract + typed loop — P0

Create additive `agent_core_v3` foundations alongside legacy Harness.

Deliverables:
- explicit `conversation_id`, `runtime_session_id`, `memory_scope_id`;
- immutable accepted turn contract;
- typed `CALL | FINAL` planner protocol;
- bounded plan -> execute -> observe -> re-plan cycle;
- requested-constraint preservation audit;
- source-backed entity grounding independent from LLM formatting reliability;
- compact authoritative observations;
- postcondition validation before response;
- full trace from raw frame -> grounded values -> contract -> capability -> observation -> validation;
- no correction state inherited by a fresh conversation;
- feature flag / routing seam so legacy and v3 can coexist during strangler migration.

Pilot scenarios include:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи задачу DMS-380`
5. `Открытые задачи <человек> в <space>`
6. `Проверь DMS-380 и затем покажи задачи его исполнителя`

Exit: all H1 pilot/routing scenarios A/B/C GREEN, requested constraints survive end-to-end, and equivalent task queries do not randomly split between legacy and v3 behavior.

### STAGE H2 — Capability Registry v1 — P0

Replace implicit skill/capability assumptions with explicit contracts.

Each capability declares:

```yaml
id: task-search
version: ...
summary: ...
required_slots: []
optional_slots: [assignee, space, status, sprint, release]
supported_constraints: [...]
source_authority: REAL_AS21
production_route: ...
oracle_contract: ...
availability_requirements: ...
postconditions: ...
latency_budget: ...
side_effects: none
read_only: true
last_certification_sha: ...
```

Exit: migrated families are routed only through Registry; no silent fallback to another internal label and no arbitrary endpoint/code execution outside registered capabilities.

### STAGE H3 — Progressive Skills + Agentic composition + deterministic executors — P0/P1

This stage absorbs the strongest behavior observed in Hermes/PVM Guru while retaining PO Agent safety.

Required design:
- the model initially sees a **compact skill/capability index**, not all detailed instructions for all 54 skills;
- full procedural instructions/contracts are loaded only for selected candidates;
- skills are procedural memory over capabilities, not phrase classifiers;
- related task/sprint/team/release skills reuse a smaller set of deterministic executors;
- planner may compose several skills/capabilities in one trajectory and use observations to decide the next call;
- simple factual queries should remain one or very few calls; complex queries may legitimately loop;
- no generated local Python as the ordinary production execution strategy;
- isolated subagents only for genuinely independent multi-domain work where they improve correctness, never as a default chain.

Initial compact catalog should expose capability families similar to:

```text
task.lookup
task.search
member.resolve
sprint.inspect
release.inspect
team.inspect
quality.analyze
velocity.analyze
carryover.analyze
portfolio.analyze
...
```

Exact catalog is registry-driven, not hardcoded in prompts.

Mandatory behavioral benchmark added from PVM Guru observation:
- `Открытые задачи <человека> в спринте <SPRINT>`;
- variants for current/finished sprints, spaces and multiple real team members;
- agent must construct a valid trajectory from capabilities rather than require a dedicated phrase router;
- returned facts must still match independent REAL AS21 Oracle B exactly.

Exit: migrated skill families show zero semantic regression, dynamic multi-step composition works, route choice is entity-independent, and context/latency are measurably improved over loading the full catalog.

### STAGE H4 — Learning Reviewer 2.0 / governed self-improvement — P0

Move learning out of the main dialogue execution path while retaining autonomous diagnosis.

Required flow:

```text
answer/trajectory -> feedback or detected validation problem
 -> independent reviewer
 -> authoritative source recheck
 -> prove mismatch/no mismatch
 -> locate first failing boundary
 -> generalized policy/skill candidate
 -> sandbox/replay
 -> independent A/B/C validation
 -> versioned promote/reject
 -> rollback available
```

Learning must not require the user to diagnose the bug. If source/validation proves a mismatch, reviewer should identify it. If no mismatch is provable, ask a targeted clarification and learn nothing.

Important distinction from PVM Guru local-file behavior:
- learning may produce a **versioned procedural skill/policy candidate**;
- it must not silently edit arbitrary production Python, credentials, endpoints or source data;
- promoted artifacts carry provenance, evidence, certification SHA/version and rollback metadata;
- learned artifacts describe procedures/selection/validation rules, never current business facts.

Exit: feedback scenarios demonstrate autonomous mismatch detection, generalized learning, persistence where supported, rollback and zero entity-fact memorization.

### STAGE H5 — Family-by-family strangler migration — P0/P1

Migration order:
1. exact-task + task search/assignee/product/status;
2. sprint/current-sprint factual skills supported by live source;
3. team/competency;
4. release factual skills supported by live source;
5. portfolio/PO aggregations;
6. history-dependent skills only where authoritative historical source contracts exist.

A family switches from legacy to v3 only after focused A/B/C GREEN. No person-name-dependent selector may decide legacy vs v3 once a family is migrated.

### STAGE H6 — Full 54-skill backend + browser recertification — P0

After migration, discover and certify the full production catalog. The known target is **all 54 user-facing skills**; if registry discovery finds a different count, reconcile it explicitly rather than silently changing scope.

Certification matrix must cover applicable combinations of:
- approved spaces: `WMB`, `STS`, `OLP`, `DMS`, `CRPV`;
- configured team members/identities from the authoritative team roster;
- exact-task, collection, status, sprint, release, team and analytical families as source support allows;
- normal, empty, not-found, ambiguous and source-unavailable states.

For every applicable factual scenario:
- A = new Agent Core;
- B = independent REAL AS21 Oracle;
- C = real browser/UI;
- compare normalized business facts and exact key sets;
- no surrogate C through Harness API;
- source-unavailable/history-unavailable capabilities are terminally classified with live proof, not skipped or fabricated.

Long runs are checkpointed/resumable; timeout never permits silently skipping a case. Concurrency remains conservative against SWTR.

Exit: every one of the 54 skills is terminally classified and every source-supported skill is A/B/C GREEN.

### STAGE H7 — Full UI Data Wiring & Acceptance — P0 release gate

Large independent UI stage after architecture migration. Inventory every route/widget/action and map:

```text
UI element -> frontend -> API -> Agent Core capability/trajectory -> source -> Oracle
```

Required UI states:
`LOADING`, `REAL_EMPTY`, `PARTIAL_DATA`, `SOURCE_UNAVAILABLE`, `ERROR`, `SUCCESS_WITH_DATA`, and where relevant `NOT_FOUND`.

Exit:
- 100% screen/widget/action inventory;
- 100% data lineage;
- zero unexplained empty/zero widgets;
- real-data A/B/C parity;
- all filters/pagination/drill-down/refresh/feedback/session behaviors GREEN;
- runtime/path metadata visible enough for QA to distinguish legacy vs Agent Core during migration.

### STAGE H8 — Release hardening

Security/read-only guarantee, secrets, packaging, restart/recovery, latency, capability governance and release-readiness certification.

---

## 5. Source and Oracle contract

Production factual path after migration:

```text
UI -> Agent Core v3 -> Progressive Skill Index -> Capability Registry
 -> deterministic executor -> Task API -> MCP-SWTR -> REAL AS21
```

Oracle B is independently built from direct authoritative source operations and cannot reuse Agent output or the same capability calculation.

Production task spaces remain `WMB`, `STS`, `OLP`, `DMS`, `CRPV`.

For task collections:

```text
set(A.task_keys) == set(B.task_keys)
set(C.task_keys) == set(B.task_keys)
set(A.task_keys) == set(C.task_keys)
```

Counts alone are insufficient. Every claimed count must also equal the cardinality of the underlying validated collection unless the capability explicitly declares a true-total/top-N contract.

---

## 6. What we still point-fix before/around migration

Point-fixes are allowed only when they unblock or protect the target Agent Core architecture:
- MCP schema/transport compatibility;
- canonical source parsing/mapping;
- pagination/full-collection semantics;
- point-read/NOT_FOUND/source-error semantics;
- authoritative source routes;
- entity grounding/safety that is shared by v3;
- accepted-turn constraint propagation;
- typed planner/observation protocol defects;
- proven deterministic calculation defect shared with v3.

Do **not** spend cycles broadly patching legacy:
- phrase/intent heuristics;
- surname-specific routing;
- multiple overlapping semantic recovery layers;
- correction-state orchestration;
- skill-label routing inconsistencies;
- learning behavior that will be replaced by Learning Reviewer;
- UI-specific workarounds hiding broken constraint propagation;
- ad-hoc scripts that bypass capability governance.

Once H1 is closed, new behavioral breadth belongs in H2/H3, not another pile of H1 phrase fixes.

---

## 7. Session and trajectory contract

Three identities are explicit and independent:

```text
conversation_id     # one visible chat/conversation
runtime_session_id  # transient dialogue/trajectory state
memory_scope_id     # durable reusable learning scope
```

Rules:
- New Chat => new conversation_id + runtime_session_id;
- QA case => unique runtime_session_id per case;
- browser and QA never share transient state;
- memory_scope does not imply previous-turn correction state;
- concurrent sessions are isolated;
- each multi-step trajectory has an explicit turn/step lineage;
- observations belong only to the runtime session/turn that produced them;
- parent/fork lineage is explicit if introduced later.

---

## 8. Learning contract

Learning artifacts are procedural policy/skill versions, never source facts.

Allowed candidate example:

```text
For an assignee+sprint task query, resolve/validate both entities, use a capability
that preserves both constraints, and validate every returned row before FINAL.
```

Forbidden learned artifact:

```text
Kalachanov has 2823 tasks.
Garanin has 16 tasks.
DMS-380 belongs to Garanin.
Goncharov has no tasks in OLP-SPRNT-5.
```

Promotion requires authoritative recheck, reproducible mismatch, independent validation and rollback metadata. Learning can change **how the agent solves a class of requests**, not what the current source answer supposedly is.

---

## 9. Performance track

Measure separately:
- semantic/goal interpretation;
- grounding;
- progressive skill discovery/loading;
- planner decision(s);
- capability resolution;
- Task API;
- MCP-SWTR/AS21;
- deterministic calculation;
- observation normalization;
- response synthesis.

Optimize by progressive disclosure, compact observations, minimal source calls, avoiding duplicate reads and safe metadata caching. Never trade authoritative truth for speed.

Explicit target after functional GREEN: ordinary factual single-step requests must return in practical interactive latency measured in seconds/tens of seconds, not minutes. Multi-step latency is budgeted per source call and must remain observable.

---

## 10. Ordered roadmap — authoritative stage order

Assignment numbers have already split substantially during H1 defect discovery; **stage order, not historical assignment number, is authoritative**.

| Stage | Work | Exit condition |
|---|---|---|
| **H1A–H1B** | Agent Core v3, sessions, immutable turn contract, typed CALL/FINAL loop, grounding, observations, postconditions | Current closure gate: Assignment 175; task pilot/routing/browser cases must be A/B/C GREEN |
| **H2** | Capability Registry v1 + governed tool contract | Pilot capabilities use explicit source/oracle/constraint/postcondition/read-only contracts; arbitrary endpoint/code execution excluded |
| **H3A** | Progressive skill disclosure | Compact capability index; selected skill contracts loaded lazily; no full 54-skill prompt dump |
| **H3B** | Agentic composition + executor consolidation | Dynamic plan->act->observe trajectories, including person+sprint benchmark; task first, then sprint/team/release |
| **H4A** | Learning Reviewer implementation | Isolated reviewer + source recheck + autonomous mismatch proof |
| **H4B** | Learning governance | skill/policy candidate validation, versioning, persistence, rollback; no entity-fact learning |
| **H5** | Family-by-family strangler migration | Legacy routing retired only per certified family; no surname-dependent route splits |
| **H6** | Full **54-skill** no-skip A/B/C catalog certification | 54/54 terminally classified across applicable approved spaces/team identities; every source-supported case GREEN |
| **H7A** | Full UI inventory/data-lineage matrix | 100% screens/widgets/actions mapped to Agent Core trajectory/source |
| **H7B** | UI REAL-data/state/interaction certification + remediation | Zero unexplained empty/wrong widgets; complete matrix GREEN |
| **H8** | Full browser E2E, session/feedback/restart/failure, security/performance/release hardening | Release candidate |
| **Final** | Release readiness | `RELEASE_READY=YES` |

Stages cannot be skipped. A proven defect may create additional focused assignments, but it does not change the architectural destination.

---

## 11. Immediate next action

**Finish H1B closure via Assignment 175.**

If 175 is GREEN:
1. freeze H1B task behavior except P0 shared-source regressions;
2. move immediately to H2/H3 progressive capability/skill selection;
3. add the PVM Guru behavioral benchmark `Открытые задачи <человека> в спринте <SPRINT>` and variants as an H3 agentic-composition acceptance scenario;
4. eliminate entity-dependent legacy/v3 selector behavior through family-level registry/progressive routing;
5. do not add new surname/phrase-specific patches to H1B.

GigaCode remains QA-only throughout.

---

## 12. Current gate values

```text
SOURCE_DATA_PLANE = FOCUSED_GREEN_REAL_AS21
LEGACY_HARNESS_PRODUCT_ACCEPTANCE = NOT_RELEASE_TRUTH
ARCHITECTURE_CUTOVER_DECISION = APPROVED
NEW_AGENT_CORE_V3 = H1B_FINAL_CERTIFICATION
SESSION_ISOLATION = FOCUSED_GREEN
IMMUTABLE_CONSTRAINT_CONTRACT = IMPLEMENTED_AND_UNDER_CONTINUOUS_CERTIFICATION
TYPED_AGENT_LOOP = IMPLEMENTED
POSTCONDITION_VALIDATION = IMPLEMENTED
SOURCE_BACKED_IDENTITY_GROUNDING = IMPLEMENTED
CAPABILITY_REGISTRY = PARTIAL_FOUNDATION / H2_NEXT
PROGRESSIVE_SKILLS = H3_NEXT
AGENTIC_MULTI_STEP_COMPOSITION = H1B_PILOTED / H3_GENERALIZATION_REQUIRED
LEARNING_REVIEWER = H4_PLANNED
STRANGLER_MIGRATION = H5_PLANNED
FULL_54_SKILL_ABC_RECERTIFICATION = H6_MANDATORY
UI_DATA_WIRING_ACCEPTANCE = H7_MANDATORY_RELEASE_GATE
PVM_GURU_REFERENCE_LESSONS = LOCKED_IN_PLAN
RELEASE_READY = NO
CURRENT_NEXT_ACTION = ASSIGNMENT_175_THEN_H2_H3
```

---

## 13. Definition of Done

Release-ready requires:
- REAL AS21/source contracts fail closed and remain read-only;
- all requested semantic constraints survive to execution or trigger typed clarification;
- planner can dynamically compose registered capabilities through plan->act->observe without phrase/surname routing;
- postcondition validator blocks contradictory result rows/counts;
- UI/API share the intended Agent Core semantics;
- browser/QA/session/memory/trajectory scopes are isolated;
- LLM-first understanding/planning is observable without heuristic replacement;
- capability contracts declare supported constraints, source, Oracle, availability, side effects and postconditions;
- progressive disclosure prevents loading all detailed skill instructions by default;
- Learning Reviewer autonomously rechecks feedback and learns only generalized evidence-backed procedure;
- learning promotion is versioned, independently validated and rollback-safe;
- **all 54 production user-facing skills** are terminally classified in the no-skip A/B/C matrix across applicable `WMB`, `STS`, `OLP`, `DMS`, `CRPV` spaces and configured team identities;
- every UI data element has authoritative lineage and explicit state semantics;
- zero unexplained empty/zero/wrong-space widgets;
- full browser E2E GREEN;
- no ordinary production request requires ad-hoc local code generation or direct arbitrary credential-bearing endpoint calls;
- P0 defects = 0;
- unauthorized AS21 writes = 0;
- secret leakage = 0;
- final release-readiness gate GREEN.

---

## 14. V4 execution amendment — plugin extensibility lock (2026-09-13)

This section is authoritative for the current V4 execution order and **supersedes any older roadmap wording that would allow bulk skill migration before plugin extensibility is proven**.

### 14.1 Hard architectural invariant

**Adding a new V4 skill MUST NOT require changes to Agent Core, planner logic, or runtime orchestration.**

The remaining 54-skill migration must use a pluginized/declarative extension model. Agent Core must remain domain-agnostic: it orchestrates discovery, planning, governed execution, observations, completion and synthesis, but it must not accumulate concrete `task.*`, `sprint.*`, `release.*`, team or portfolio wiring.

The stable extension surface must provide the semantics of:

```text
SkillSpec
CapabilitySpec
CapabilityHandler
CompletionContract
UIContract
```

Names may vary, but responsibilities must remain separated and registry-driven.

Required behavior:
- skill discovery/registration is dynamic and produces the compact progressive catalog;
- capability handlers are resolved through a governed capability registry, not a hardcoded Agent Core `_handlers` map;
- procedures/steps belong to the skill artifact;
- completion conditions belong to `CompletionContract`, not `if skill_id == ...` branches in runtime;
- UI/widget/state metadata belongs to `UIContract`, so frontend rendering needs can evolve without changing orchestration core;
- adding/removing a plugin must not alter planner architecture or core execution flow;
- source authority, typed constraints, postconditions and fail-closed rules remain mandatory for every plugin.

### 14.2 Mandatory extensibility acceptance test

Before progressive bulk migration of the remaining catalog, add a synthetic **55th dummy skill** using only the extension/plugin surface.

It must pass all of the following with **zero edits to Agent Core/planner/runtime code**:

```text
plugin artifact added
 -> registry discovers it
 -> compact catalog exposes it
 -> planner can load/select it
 -> registered capability executes
 -> completion contract terminates correctly
 -> UI contract is propagated to the presentation layer
```

If this requires editing `agent_core_v4.py` or equivalent core orchestration, the plugin gate is RED and 54-skill migration must not begin.

### 14.3 Current V4 priority order

The current implementation order is:

```text
1. V4 representative reliability GREEN
2. Pluginized Skill/Capability Registry + dummy-55 extensibility gate
3. Browser/UI integration with all required states and working widgets
4. Progressive migration of all 54 production user-facing skills in domain waves
5. Full 54-skill Agent A / REAL Oracle B / Browser C certification
6. Full UI/widget E2E + release hardening
7. RELEASE_READY=YES only after complete DoD
```

UI work may proceed in parallel where it does not couple the frontend to hardcoded skills, but **bulk 54-skill migration is blocked until step 2 is GREEN**.

### 14.4 V5 milestone — explicitly deferred

`DEFERRED_TO_V5 — DO NOT IMPLEMENT DURING V4`.

GVS5H-inspired analytical orchestration is recorded as a V5 research/POC milestone only: fresh workers, typed shared ledger, verifier, and A/B evaluation against V4 on complex analytical PO scenarios. It must not expand V4 scope or delay delivery of the fully working V4 agent with all 54 skills and all UI widgets.

V4 remains focused on a stable single-agent skill-native architecture, complete catalog coverage, source correctness and production UI readiness.


---

## 15. Authoritative V4 execution snapshot — 2026-09-24

This section is authoritative for the current execution state and supersedes the stale values in §12 where they conflict with the V4 plan/DoD.

### 15.1 Current architecture state

```text
ACTIVE_BRANCH = feat/core8-real-query-hardening-v2
CURRENT_HEAD_AT_UPDATE = 950041f9fc1b9cb3cc9ba6223777d133eb9111b2
ARCHITECTURE = V4_SINGLE_PLANNER_SKILL_NATIVE_HARNESS
PLUGIN_REGISTRY = GREEN
DUMMY_55_EXTENSIBILITY = GREEN
BROWSER_C = GREEN_FOR_CERTIFIED_EXISTING_AND_S1_SCENARIOS
REAL_AS21 = AUTHORITATIVE_FACT_SOURCE
LOCAL_TASK_STORE_FACTUAL_READS = FORBIDDEN
SEMANTIC_PREPASS = FALSE
ENTITY_PHRASE_ROUTING = FORBIDDEN
GIGACODE_ROLE = QA_ONLY
GVS5H_MULTI_AGENT = DEFERRED_TO_V5
RELEASE_READY = NO
```

Hard invariant remains unchanged: **adding a skill must not require Agent Core/planner/runtime business-logic edits**. New skills are introduced through registry-discovered plugin artifacts with `SkillSpec / CapabilitySpec / CapabilityHandler / CompletionContract / UIContract`.

### 15.2 Proven rollback checkpoints

Keep these immutable recovery points:

```text
A205_GREEN = checkpoint/v4-a205-green@1fd519105ba6612f535ad98a55cb1302f387ca43
A206B_HISTORY_STATUS_GREEN = checkpoint/v4-a206b-green@f7f846dee71b676fb0fc8d1d8f0d8aa23d521eaf
WAVE_S1_GREEN = checkpoint/v4-wave-s1-green@ce64264c868afd73743d5daafdeaee767e07adef
A208B_PRE_S2_GREEN = checkpoint/v4-a208b-green@2e284fdab79072d95ba0bf86058b4648f4bb9d6c
```

Rollback rule: if a later wave introduces an architectural regression that cannot be bounded quickly, return to the latest GREEN checkpoint and re-apply only proven generic fixes.

### 15.3 Closed gates before S2

The following are now certified:

- existing 27-skill V4 catalog: no code RED in the A205 adversarial matrix;
- history/status route: REAL MCP `get_task_history`, exact source status labels, exact history ordering/timestamps, fail-closed;
- `task.time_in_status`: terminal statuses stop at closure, revisits preserved;
- person + status search: explicit `not_completed/completed` constraints retained;
- raw source status filtering: authoritative `status_raw/status_type` supported without per-status hardcode;
- blocked task drill-down: uses the same canonical `task.is_blocked` predicate as sprint-health logic;
- Wave S1: `sprint.scope`, `sprint.velocity`, `sprint.throughput`, `sprint.wip` GREEN;
- short/current/period sprint resolution for S1 metrics GREEN;
- compact-observation completion contracts aligned and GREEN;
- Browser C representative regression GREEN;
- factual local `/api/v1/tasks` reads = 0.

Known source-conditional item:
- `release.search` is implemented but live certification remains `SOURCE_CONDITIONAL` while the authoritative version/release directory returns HTTP 502. This is visible in manual UI as `V4 SOURCE_UNAVAILABLE` and must not be "fixed" with task-scan or local-cache inference.

### 15.4 Active gate

```text
CURRENT_GATE = POST_A214_CATALOG_MIGRATION_RESUMED
WAVE_S2 = GREEN_A210
RELEASE_SEARCH = GREEN_A212
RELEASE_HEALTH = TERMINAL_SOURCE_CONDITIONAL_GREEN_A214
RELEASE_REMEDIATION = CLOSED
NEXT_OWNER_BATCH = BATCH_2_FIVE_SKILLS
GIGACODE_ROLE = QA_ONLY
```

A214 closed the release remediation block. The release directory is live and certified; `release.health` is intentionally terminal `SOURCE_CONDITIONAL` until REAL AS21 exposes authoritative release-to-task membership. This source limitation must not block unrelated catalog migration.

Next owner batch:
- `sprint.scope_change`
- `team.workload`
- `team.wip`
- `team.blocked`
- `team.capacity`

The Harness/Core remains frozen as a platform. These skills must be introduced through registry-discovered plugins/contracts only. If one skill exposes a generic Harness defect, repair only that generic boundary and re-gate the same batch before moving on.

### 15.5 Accelerated batch policy and current schedule through end of September

Calendar target remains: complete V4 catalog migration and major certification work by **2026-09-30**, without weakening rollback/source/evidence gates.

Default packaging remains **five skills per owner batch**.

Current execution calendar from the A214 GREEN baseline on **2026-09-24**:

| Date | Owner work | Independent QA / exit |
|---|---|---|
| **Sep 24 evening – Sep 25** | **Batch 2:** `sprint.scope_change`, `team.workload`, `team.wip`, `team.blocked`, `team.capacity` | GigaCode A/B/C + Browser C; GREEN checkpoint before Batch 3 |
| **Sep 25 – Sep 26** | **Batch 3:** `team.competency_match`, `team.assignee_recommendation`, `team.bottlenecks`, `team.distribution`, `release.scope` | QA + source-conditional classification where source contracts are absent |
| **Sep 26 – Sep 27** | **Batch 4:** `release.progress`, `release.blockers`, `release.dependencies`, `release.risk_queue`, `portfolio.overview` | QA; release-derived analytics must inherit the A214 membership limitation rather than fabricate data |
| **Sep 27 – Sep 28** | **Batch 5:** `po.attention_queue`, `task.search_product`, `release.forecast`, `po.daily_brief`, `po.status_report` | QA + representative UI; no hidden local/task-scan fallback |
| **Sep 28** | **Batch 6 / catalog tail:** `po.reminder_draft`, `po.local_task_draft` + reconcile every still-unmigrated/uncertified catalog item | Produce authoritative 54-skill inventory with every skill terminally classified |
| **Sep 29** | **H6 full 54-skill A/B/C certification** across applicable WMB / STS / OLP / DMS / CRPV scenarios | No-skip matrix, exact Oracle parity for source-backed facts, SOURCE_CONDITIONAL with live proof where unsupported |
| **Sep 30** | **H7/H8 release-candidate pass:** UI/widget lineage, Browser E2E, session/restart/failure recovery, security/read-only, latency/performance and rollback rehearsal | P0=0 and final release-readiness decision |

This is an aggressive target, not permission to skip gates. A RED batch consumes the next slot until it is GREEN; later dates slide rather than allowing known defects into the next batch.

Planned catalog sequence remains:

1. **S2 — CLOSED GREEN A210:** `sprint.cycle_time`, `sprint.lead_time`, `sprint.carryover`, `sprint.predictability`, `sprint.risk_queue`.
2. **Release remediation — CLOSED A214:** `release.search` GREEN; `release.health` terminal SOURCE_CONDITIONAL.
3. **Batch 2 — NEXT:** `sprint.scope_change`, `team.workload`, `team.wip`, `team.blocked`, `team.capacity`.
4. **Batch 3:** `team.competency_match`, `team.assignee_recommendation`, `team.bottlenecks`, `team.distribution`, `release.scope`.
5. **Batch 4:** `release.progress`, `release.blockers`, `release.dependencies`, `release.risk_queue`, `portfolio.overview`.
6. **Batch 5:** `po.attention_queue`, `task.search_product`, `release.forecast`, `po.daily_brief`, `po.status_report`.
7. **Batch 6 / final catalog tail:** `po.reminder_draft`, `po.local_task_draft` plus every remaining item discovered by registry-vs-authoritative-catalog reconciliation.
8. **H6:** full 54-skill A/B/C no-skip certification.
9. **H7:** full UI/widget/data-lineage acceptance.
10. **H8:** security, operability, restart/recovery, latency and final release hardening.

A batch may be larger than five only when the skills share the same proven source/handler surface and the QA matrix remains bounded. A batch should be smaller only for real dependency/source-risk reasons.

### 15.5.1 Verdict terminology

QA verdicts and capability availability are separate dimensions.

- `GREEN` on an assignment means the implementation behaves exactly according to its contract, including safe fail-closed behavior.
- It does **not** mean that every capability is currently executable from REAL AS21.
- A capability whose required authoritative source field is absent must be recorded explicitly as `TERMINAL_SOURCE_CONDITIONAL`, even when its QA gate is GREEN.
- UI/product summaries must not call such a capability "working"; they should say that the skill is implemented but unavailable with the current source contract.

Current example:
`team.capacity = TERMINAL_SOURCE_CONDITIONAL_A215B` because current REAL AS21 sprint task rows do not expose source-backed estimates required for utilization.

### 15.6 Mandatory gate for every accelerated batch

Speed does not alter the quality bar. Every batch must still prove:

1. registry-only extension; no core skill routing;
2. focused unit/contract tests;
3. fresh REAL AS21 Oracle immediately before factual live cases;
4. exact fact/key parity where applicable;
5. fail-closed behavior for absent source surfaces;
6. Browser C representative coverage;
7. local factual reads = 0 and no tenant-wide fallback scan;
8. dummy-55/plugin invariant retained;
9. independent GigaCode QA;
10. new immutable checkpoint after GREEN.

A `SOURCE_CONDITIONAL` skill does not block unrelated skills if the outage/source gap is independently proven and the implementation fails closed without fabrication.

### 15.7 Endgame after catalog migration

After all 54 production skills are terminally classified:

```text
FULL_54_AGENT_A_REAL_ORACLE_B_BROWSER_C = REQUIRED
FULL_UI_WIDGET_E2E = REQUIRED
SOURCE_CONDITIONAL_REPROBES = REQUIRED
ROLLBACK_REHEARSAL = REQUIRED
P0_DEFECTS = 0
UNAUTHORIZED_WRITES = 0
RELEASE_READY = YES only after all mandatory gates are GREEN
```

V5 multi-agent/GVS5H work remains explicitly deferred until V4 is complete.
