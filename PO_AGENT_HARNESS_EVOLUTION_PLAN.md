# PO Agent — Authoritative Evolution Plan

**Status:** ACTIVE / Hermes-style architecture cutover approved  
**Current branch:** `feat/core8-real-query-hardening-v2`  
**Last reviewed:** 2026-09-26  
**Current baseline:** V4 Batch 4 is GREEN after A217D. Production robust runtime is restored; release identity vs analytics routing is certified, portfolio overview is source-exact, time-accounting/member analytics are GREEN, and release analytics remain intentionally SOURCE_CONDITIONAL where REAL AS21 lacks release→task linkage.
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

### UI product usability remediation after A223R2

**Status:** ACTIVE before visual redesign.

A223R2 closed the shared state/lineage gate GREEN. Before visual styling, the product UI must close the following owner-observed usability/data issues so design does not freeze incorrect behavior.

1. **Overview height / scrolling**
   - PO attention queue and Daily Brief must have comparable visual height.
   - Long collections use internal scrolling.
   - Attention queue initially renders at most 10 highest-ranked tasks and explicitly shows "first N of total".
   - Downstream blocks such as task-by-space summary must stay visible without page-length explosion.

2. **Tasks by spaces**
   - Rename "Статус продуктов" to **"Задачи по пространствам"**.
   - Do not use current-sprint membership as the full-space task count.
   - Add bounded project-scoped REAL AS21 counts for each approved space (WMB, DMS, OLP, CRPV, STS) with no tenant-wide scan.
   - Show total / active / completed / blocked.
   - Cross-check exact counts independently in QA; suspiciously tiny current-sprint counts must not be presented as full-space totals.

3. **Local task CRUD**
   - Local browser task supports priority, labels and status on creation.
   - Status is editable after creation.
   - Local task can be deleted from browser/local storage.
   - Existing old localStorage rows migrate safely to defaults.
   - No AS21 write is introduced.

4. **Sprint predictability**
   - Keep fail-closed behavior while source lacks an authoritative sprint-start commitment baseline.
   - UI must explain why predictability is unavailable rather than showing an unexplained dash.
   - Do not fabricate predictability from current scope.

5. **Releases**
   - Release page remains intentionally source-limited until AS21 provides reliable release-to-task/sprint linkage.
   - Preserve explicit SOURCE_CONDITIONAL/UNAVAILABLE panels and no pseudo forecast.
   - This is not a UI blocker for the next phase.

6. **Team**
   - Remove manual capacity-baseline input and "Пересчитать" button.
   - Add product-space selector so team skills are always issued with a bounded space and do not fall into bare-query clarification.
   - Default UI policy: 40-hour work week per person; period/availability normalization is automatic through owner policy.
   - Workload/WIP/blocked/bottlenecks/distribution must populate for the selected source-ready space.
   - Capacity may still be SOURCE_CONDITIONAL when task estimates are absent; show the limitation instead of fake utilization.

7. **Quality / Aging queue**
   - Aging requests must be explicitly bounded by a selected space.
   - Threshold refresh must issue a source-backed space + threshold query.
   - Proven-empty may render zero; unscoped/source-limited must not look like an empty queue.

Only after this usability/data remediation is GREEN should the slide-derived visual redesign start.



### A224 pagination-cap finding

A224 proved that materializing all tasks per space is not a valid counting strategy for CRPV/STS because the live task-query route is capped by pagination. The remediation therefore changes the contract for the Overview "Задачи по пространствам" block:

- **Total task count** is source-ready and must come from authoritative source pagination metadata (`totalElements`) via a one-page bounded count route.
- **Active/completed/blocked full-space breakdown** remains SOURCE_CONDITIONAL until a verified source-side aggregation/filter-count contract exists. UI must show this limitation explicitly and must not derive the breakdown from truncated rows.
- Per-space failures are isolated; one unavailable space must not sink the whole PO status report.
- No space may render a false zero when the source is unavailable.


### A224R scope correction — team-owned tasks, not whole spaces

**Decision:** the Overview block **"Задачи по пространствам"** must represent the work of the configured product team, not the complete historical corpus of WMB/DMS/OLP/CRPV/STS.

Reason:
- CRPV/STS contain hundreds of thousands of unrelated tasks, so full-space totals are not meaningful for the PO workspace;
- the project already has a canonical team directory in `task-api/config/team_members.yaml`;
- the live assignee search path is already certified and works for logins such as `Kalachanov.V.V`.

Target source contract:
1. Load canonical member logins from `team_members.yaml`.
2. For each configured login, perform the certified bounded REAL AS21 assignee read.
3. Group returned tasks by approved space.
4. Deduplicate by canonical task key.
5. Compute exact team-owned total / active / completed / blocked per space.
6. Never perform whole-space corpus scans for this widget.
7. If any member source read fails, mark the space summary SOURCE_PARTIAL and do not present the partial count as exact.
8. If all member reads fail, fail closed.

UI:
- keep title **"Задачи по пространствам"**;
- explicitly state that counts are tasks assigned to configured team members;
- no fabricated totals from complete space size.

Additional owner UX changes in the same gate:
- PO Attention must render the full queue inside an internal scroll container; do not slice the dataset to the first 10 rows;
- Tasks page gets separate status filters for AS21 results and local tasks;
- status filters are presentation filters and must not mutate AS21 data.


### A224R2 closure — UI usability GREEN

A224R2 closed the pre-design usability/data-correctness gate GREEN.

Certified:
- team-scoped task summary exact against REAL AS21 for all five approved spaces;
- PO Attention renders the full 107-row queue inside a bounded scroll container;
- AS21/local status filters work independently;
- local task CRUD persists and remains read-only toward AS21;
- Sprint predictability fails closed with explicit source limitation;
- Releases remain honestly source-limited;
- Team space selector and automatic 40h/week policy work;
- Quality Aging is scoped by space + threshold and source-exact;
- 0 AS21 mutations, 0 local factual fallback, 0 tenant-wide scans.

Checkpoint:
`checkpoint/v4-ui-usability-green-a224r2@612116894572f72af4f024486799458d3870d539`

Non-blocking responsive finding to absorb into visual redesign:
- at 480px, long PO Attention rows can overflow horizontally by ~14–75 px due to title + score badge composition.

**Current owner phase: visual design system + slide-derived page backgrounds.**
Learning Reviewer remains blocked until visual redesign and Browser C UX acceptance are GREEN.


### A225 visual design implementation

**Status:** IMPLEMENTED_PENDING_QA.

Owner implemented the cookbook-derived visual layer after A224R2 GREEN.

Artifacts:
- six abstract slide-derived SVG backgrounds under `frontend/public/design/`;
- route-specific page theme classes;
- shared dark navy / cyan glass design tokens in `workspace.css`;
- dark sidebar/topbar/navigation treatment;
- glass metric/content/task cards;
- dark agent/task drawers;
- cookbook-aligned typed source-state panels;
- responsive fix for the known 480px PO Attention title/score overflow;
- `UI_VISUAL_DESIGN_2026_SPEC.md` as the design acceptance contract.

The implementation is presentation-only:
- no Agent Core/planner/runtime/source/business-calculation changes;
- no new dependency;
- no AS21 mutation;
- existing A224R2 state/lineage and usability semantics must remain unchanged.

A225 must be GREEN before Browser UX/PO acceptance is frozen.


### A225 closure — visual design GREEN

A225 certified the cookbook-derived visual system GREEN:
- six distinct page backgrounds;
- one shared dark navy/cyan glass system;
- typed V4 states remained readable;
- 1440px + 480px responsive checks GREEN;
- PO Attention overflow closed;
- 0 mutations / 0 extra source reads caused by styling.

Checkpoint:
`checkpoint/v4-ui-visual-design-green-a225@09bcbd22d87b478396970d0ddf89cbf6d531d421`

### A226 — final owner UI polish + page snapshots

**Status:** IMPLEMENTED_PENDING_QA.

This owner batch incorporates PO visual/behavioral feedback before final Browser UX acceptance.

1. **Dark structured data surfaces**
   - remove remaining white legacy surfaces from V4 structured-result panels and Daily Brief/rich tables;
   - keep readable cyan/white text over dark glass.

2. **Team actual utilization**
   - Team UI now uses certified `team.utilization_actual`, not estimate-based `team.capacity`;
   - numerator = REAL AS21 worklogs;
   - denominator = owner policy normalized to sprint period (40h/week baseline);
   - estimate-based `team.capacity` remains source-conditional and is not used for this widget;
   - expose per-member worklog count alongside actual hours / available capacity / utilization.

3. **Top-right product chips**
   - keep only `OLAP` and `DataMarts`;
   - remove `DTMS`.

4. **Team-scoped Aging queue**
   - `task.aging` gains explicit `team_scope=true`;
   - UI asks for old tasks of the configured team in the selected space;
   - source reads are bounded by configured member logins and space;
   - deduplicate by task key;
   - any missing member read fails closed instead of presenting partial aging as exact.

5. **Stable page snapshots + manual refresh**
   - every main page loads live data on first open in a browser session;
   - successful responses are cached in `sessionStorage`;
   - route navigation/back does not automatically re-query AS21 when a page-context snapshot exists;
   - each page has a manual `Обновить` control and timestamp;
   - manual refresh keeps the previous snapshot visible while requests run;
   - refresh failure preserves the old snapshot and shows a stale/error indicator;
   - context-specific keys isolate Team space, Quality task/aging threshold, Sprint id, Release id, Tasks search/filter;
   - no background polling.

A226 must be GREEN before the final PO/Browser UX checkpoint.


### A226 RED closure / A226R owner remediation

A226 stopped at P4 with `RED_SOURCE_TIMESTAMP_PLUMBING`.

Root cause:
- team-scoped `task.aging` correctly reused the live assignee route;
- the assignee route did not request or surface source creation timestamps;
- therefore the capability correctly failed closed instead of fabricating aging.

Owner remediation:
- task-api assignee TQL now requests `created_at/createdAt/updated_at/updatedAt/deadline/dueDate`;
- canonical assignee rows now expose `created_at`, `updated_at`, `deadline`;
- timestamp preservation regression added;
- A226R must verify WMB:7 and DMS:15 exact live parity through the real assignee route.

A226R also consolidates final PO UX feedback before final Browser acceptance:
1. Tasks text search is explicit title+description search, with separate attachment/Excel/PDF/MSG modes.
2. Tasks search mode/value/submitted criteria/status filters persist in session; `Найти` changes criteria, page `Обновить` re-runs the last submitted criteria.
3. Local tasks add user-facing Russian priority labels, tag suggestions, deadline and show tags/priority/deadline in the list.
4. Quality task/aging input + submitted values persist in session.
5. Sprint/Release duplicate header refresh buttons removed; existing entity toolbar owns refresh, shows last update date+time and refreshes current submitted entity.
6. Workspace brand label changed from `WORKS` to `Platform V`.
7. Daily Brief again renders completed + attention count + top-attention tasks + current sprint breakdown while staying internally scrollable.

A226R must close P4 first, then the deferred A226 P1/P5/P6/P8 gates and these UX acceptance cases.


### A226R RED closure / A226R2 owner remediation

A226R stopped at P3 with:
`RED_P3_UNSCOPED_TEXT_SEARCH_SOURCE_SCALE`.

Independent QA proved:
- WMB contains 99 real matches for "БП 2027";
- DMS/OLP are source-proven empty for that phrase;
- STS/CRPV exceed the bounded row-materialization cap;
- one large-space failure previously sank the whole unscoped phrase search.

Owner remediation for A226R2:
1. task-api unscoped phrase search isolates failures per space and returns completed-space rows plus explicit `incomplete_spaces` / `source_complete=false` metadata instead of discarding healthy-space results.
2. task.search_text propagates that completeness metadata and warning; partial source coverage is never silently presented as exact.
3. Main Tasks UI is simplified back to five search modes only:
   - Текстовый поиск
   - Исполнитель
   - Статус
   - Спринт
   - Релиз
4. UI text search is explicitly scoped by product-space selector (WMB/DMS/OLP/CRPV/STS); the mandatory "БП 2027" case defaults to WMB and therefore uses a bounded exact source query rather than an all-space corpus scan.
5. Floating PO Agent launcher is hidden while task/local-task drawers are open, closing the A226R submit-button overlap.
6. Snapshot timestamp uses ru-RU date+time formatting.
7. Page refresh has a 65s UI completion bound so a slow child query cannot leave the button in "Обновляем…" indefinitely; stale snapshot is preserved on timeout.
8. Aging "Обновить" with unchanged criteria now forces a live re-read.

PO observations to re-gate in the same batch:
- Overview refresh must leave loading state and show the new date/time;
- Sprint must be verified with the correct source-backed id `DMS-SPRNT-3` (not the observed typo `DMS-DPRNT-3`);
- Sprint risk queue and predictability require independent source parity;
- Release page must be verified on source-backed release identities (for example 1.6.0 / 24Q1) and preserve honest SOURCE_CONDITIONAL when release-to-task membership is unavailable.

A226R2 must be GREEN before the final PO Browser UX acceptance checkpoint.


### A226R2 RED closure / A226R3

A226R2 closed P1 GREEN:
- WMB "БП 2027" exact source parity;
- scoped UI request touched WMB only;
- unscoped API probe retained healthy WMB rows and exposed CRPV/STS as incomplete.

P2 found two UI/source-scope defects:
1. Tasks submit handler dropped the selected space, so a visible DMS selection could still submit the WMB fallback.
2. Status mode supplied no source space and therefore expanded into an all-approved-spaces task scan.

Owner remediation:
- Tasks now persists a generic `searchSpace` and copies it into submitted state for Text and Status modes;
- Text and Status queries both include the explicit product space;
- snapshot cache identity includes the submitted space;
- status mode displays the same bounded space selector;
- direct task-api partial-search tests now pass concrete FastAPI endpoint arguments rather than Query() defaults.

A226R3 resumes at P2, then completes the deferred P3-P8 forensic/UX checks:
local drawer hit testing, Overview refresh completion, Aging re-read, Sprint DMS-SPRNT-3, Releases source-contract behavior, retained smoke/audit.


### A226R3 closure — final UI polish GREEN

Verdict: `AGENT_CORE_V4_UI_POLISH_SNAPSHOT_GREEN_A226R3`

Checkpoint: `checkpoint/v4-ui-polish-snapshot-green-a226r3@486747298bc812bebab64a86b81585a202ab6ccc`

Certified: Tasks Text/Status source scoping exact; 5-mode Tasks UX; local-task CRUD with LOCAL-NNNN/deadline/tags/priority/edit/reload; Overview refresh/stale preservation; Quality Aging re-read; Sprint DMS-SPRNT-3 forensic including Risk Queue; Releases typed source limitation; six-page responsive/design audit; zero local factual reads, zero tenant-wide scans, zero mutations.

Carry as non-blocking tech debt: F1 drawer close X under sticky topbar at 1366x768; F2 65s Overview timeout race with slow source; F3 Quality shared refreshNonce; F4 WMB 24Q1 quarter-like release phrasing may route to sprints.discover.

Next sequence: PO final Browser UX sign-off; optional small non-blocking cleanup if requested; release hardening/security/restart/latency/rollback rehearsal; Learning Reviewer 2.0 only after the release gate is intentionally opened.


### A227 — PO acceptance corrections

Owner review after A226R3 GREEN found three product-level issues that must be closed before PO sign-off.

1. **Overview refresh reliability**
   - A226R3 proved a 65s client/source latency race.
   - Snapshot request timeout increased to 120s so legitimate 60–70s source reads do not surface as false refresh failures.
   - Stale snapshot remains visible during refresh and on genuine failure.

2. **Tasks becomes a Google-like natural-language search surface**
   - Remove mode buttons for assignee/status/sprint/release.
   - Remove explicit product-space selector from the search UI.
   - Keep one natural-language input + Find + Local Task.
   - The raw submitted query goes to Agent Core V4 so skill discovery/composition chooses the correct task/sprint/release/attachment/risk capabilities.
   - Examples to support include:
     - "Открытые задачи Калачанова с вложениями в пространстве WMB"
     - "Задачи Семавина по рискам"
     - "Задачи в работе в сентябрьском спринте по DMS"
     - "Спринты в DMS"
   - Task collections render as task cards; non-task results render as the grounded agent answer.
   - Search input/submitted query/snapshot persist on navigation; refresh repeats the same submitted natural-language query.
   - No automatic search occurs on first page open.
   - Local-task status filter remains local to the Local Tasks block only.

3. **Quality refresh / Aging**
   - Quality task-analysis refresh and Aging refresh are isolated.
   - Top page refresh re-runs only quality/missing/acceptance.
   - Aging's own Refresh re-runs only the persisted space+threshold aging query.
   - Aging must populate from REAL AS21 for source-ready cases such as DMS > 7 / 15 days.
   - No one-widget refresh should fan out all four Quality queries.

A227 is the final PO UX correction gate before release hardening. Learning Reviewer remains blocked.


### A227 RED closure / A227R

A227 P0-P2 and P3-D are GREEN. First blocking boundary is P3 multi-constraint natural-language composition.

Confirmed A227 root causes:
1. **Repeated planner transport/schema failure:** after valid source-backed resolver steps, the provider/client can repeatedly emit the same schema-invalid composite decision. The old robust loop consumed all four attempts without changing the action boundary.
2. **Attachment intersection schema gap:** `task.search_attachments` (and specialized attachment variants) could not express a requested status predicate, forcing stochastic multi-skill composition for person + space + status + attachments.
3. **Sprint + in-progress false zero:** `В работе` / `In Progress` must resolve to the authoritative REAL AS21 typed predicate `status_type=progress`, not a literal localized label comparison.

A227R owner remediation:
- RobustSkillNativePlannerV4 now detects repeated identical provider failures and switches to a constrained action-only recovery prompt instead of replaying the primary prompt.
- After a repeated identical provider failure, an additional deterministic fallback is allowed only when the most recently loaded skill has exactly one pending governed capability. Arguments may come only from prior typed observations plus conservative generic status enums; READY is never synthesized and no source facts are invented.
- `task.search_attachments`, Excel/PDF/MSG attachment capabilities now accept/preserve an optional typed `status` constraint.
- Attachment handlers apply the same semantic status contract as generic task search before file fan-out, so attachment filtering never drops open/completed/blocked/in-progress constraints.
- Generic task.search now treats normalized `progress` as the source predicate `status_type=progress`; period-sprint discovery therefore carries `space + sprint_id + status` to the terminal task collection without literal-label false zero.
- Regression coverage added for repeated provider ValidationError recovery, attachment + status intersection, and sprint + typed in-progress task collection.

Architectural invariants preserved:
- no phrase/surname/space-specific router;
- no tenant-wide fallback scan;
- no local-store factual fallback;
- no fake metrics/source rows;
- simple/single-constraint planner trajectories remain unchanged unless transport recovery is actually triggered.

A227R QA starts at P3. Re-run P3-A, P3-B and P3-C repeatedly against independent REAL AS21 oracles; after GREEN continue P4-P7. In P6 refresh the live DMS >7 / >15 Aging oracles rather than trusting A227's historical 77/68 counts.

If A227R is GREEN:
- create checkpoint `checkpoint/v4-po-acceptance-green-a227r`;
- open release hardening: restart/recovery, latency, security, rollback rehearsal;
- do **not** start Learning Reviewer 2.0 yet.


### A227 pre-gate PO correction — UI parity before A227R

Manual PO verification showed that the direct PO Agent dialogue already handles the target task query acceptably, while the Tasks page could appear not to search at all. The boundary is UI snapshot behavior, not a reason to extend stable Agent Core.

Owner correction:
- the extra A227 repair changes made in `agent_core_v4_robust.py` / `agent_core_v4_reliable.py` during this owner pass were reverted;
- this correction introduces no new Harness/Core routing logic;
- plugin-level attachment status composition remains the preferred extension seam;
- Tasks continues to send the raw natural-language query to the same `/api/v1/query` Agent Core entry;
- pressing **Найти** with the same submitted query now forces one fresh live POST instead of silently reusing the persisted snapshot;
- page revisit without pressing Find still preserves the snapshot and makes zero automatic POSTs.

Release manual verification also found an integration gap:
- canonical `release.forecast` already exists as a plugin skill;
- ReleasesPage did not call it and instead rendered a static "Forecast not activated" note;
- ReleasesPage now queries `release.forecast` through the normal Agent endpoint and renders a Predictability / Forecast panel;
- insufficient release membership/history must surface as SOURCE_CONDITIONAL / SOURCE_UNAVAILABLE, never as a fake forecast or blank metric.

Run the focused UI/source parity pre-gate before A227R. Only after it is GREEN should the remaining A227R P3-P7 acceptance gate resume.
