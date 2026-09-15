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

3. **REAL AS21/SWTR remains authoritative.**
   - No local DB, sync snapshot, cache, fixture, fake/frozen source, remembered count or previous answer can become production truth or Oracle B.
   - Source unavailable is explicit and never converted to an empty result.
   - Collections require exact task-key parity, not only count/prose parity.

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

Rules:
- V3/H1B remains a rollback/reference path until V4 proves the full 54-skill A/B/C gate.
- V4 is the primary architectural direction because it removes the mandatory semantic-prepass bottleneck.
- A RED in an individual V4 capability is not by itself a reason to return to V3; first distinguish a bounded implementation defect from failure of the skill-native architecture.
- If V4 repeatedly cannot satisfy unseen-entity composition, exact source parity, governed execution, or progressive skill loading after bounded architectural fixes, pause migration and review against this checkpoint before further investment.
- Do not delete the rollback point or legacy reference path before V4 full-catalog certification.

### POC reliability stop-rule
Assignment 181 moved the mandatory `task -> assignee -> tasks` benchmark to 8/10 exact REAL-AS21 parity and proved the previous fail-open recovery defect closed. The remaining failure boundary is planner attention being distracted by an unbounded source description.

Therefore the next generalized observation-hygiene change is the **last focused POC reliability fix before an architecture/model decision gate**:
- allowed: entity-agnostic bounding/compaction of planner-facing unstructured observation fields while preserving exact structured source identity/status/sprint/count values;
- forbidden: DMS-380-specific logic, surname/phrase routers, deterministic trajectory routing, semantic-prepass reintroduction, or capability-specific next-step hardcode;
- after that fix, run a mixed reliability gate rather than another narrow endless sequence of the same benchmark;
- if the mixed gate is stable/GREEN, stop backend POC remediation and proceed to `V4-PLUGIN`, then `V4-BROWSER`, then `V4-CATALOG`;
- if a new fundamental planner/control-plane reliability defect of the same class remains, STOP focused patching and explicitly review planner model/tool-calling strategy (including whether the current Qwen planner is suitable) before any further Assignment 18x remediation.

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
Migrate the full 54-skill catalog to progressive/composable V4 skills and reusable capabilities through the pluginized registry. Adding each migrated skill must not change Agent Core architecture.

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

Every future owner/QA assignment after the current V4 POC must answer these questions before claiming a milestone GREEN:

- Does this move us toward skill-native composition rather than add another phrase/entity special case?
- Is source truth REAL AS21 and independently verifiable?
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
V4_REPRESENTATIVE_POC = OWNER_VERIFICATION_A187_IN_PROGRESS
V4_SKILL_COMPLETION_CONTRACT = IMPLEMENTED_A187
V4_DETERMINISTIC_POST_OBSERVATION_COMPLETION = PROVEN_GENERIC
V4_POC_FOCUSED_FIX_BUDGET = BOUNDED_RELIABILITY_ONLY
V4_PLUGINIZED_SKILL_CAPABILITY_REGISTRY = REQUIRED_BEFORE_54_SKILL_MIGRATION
V4_PLUGIN_DUMMY_55_GATE = NOT_DONE
V4_BROWSER_C = NOT_YET_WIRED
V4_FULL_54_SKILL_MIGRATION = NOT_DONE
V4_FULL_54_ABC = NOT_DONE
V4_LEARNING_REVIEWER = NOT_DONE
V4_GOVERNED_SKILL_SELF_MODIFICATION = NOT_DONE
V4_FULL_UI_ACCEPTANCE = NOT_DONE
V5_GVS5H_ANALYTICAL_ORCHESTRAION = DEFERRED_TO_V5
RELEASE_READY = NO
```

## 6. Deterministic post-observation completion (Assignment 187)

V4 production reliability hardening: a typed **skill completion contract**
(`agent_core_v4_completion.py`) deterministically satisfies loaded skills from
validated trajectory observations, eliminating dependence on the stochastic
model successfully minting a terminal `READY` JSON decision.

Key properties:
- Per-skill `CompletionRequirement` tuples declare which capability observations
  (with required data fields, argument bindings, and resolved-constraint
  coverage) prove the skill is complete.
- Evaluated only against typed trajectory state — no query text, no entity
  literals, no semantic prepass.
- Fails closed: not-found, ambiguous, source-failure states and uncontracted
  skills retain normal planner behavior.
- Runtime short-circuits to deterministic synthesis after a validated capability
  observation proves every loaded skill's contract is satisfied.
- `completion=runtime_contract` marker in trajectory/response distinguishes
  runtime-generated completion from model `planner_ready`.
- Recovery-time READY remains forbidden by the planner protocol.
- The runtime path never uses model-recovered READY text and cannot fabricate
  an answer without observations.

V4 remains single-planner / skill-native / governed. This mechanism is a
generic control-plane rule, not a query-specific fallback.

`DEFERRED_TO_V5`: GVS5H-inspired multi-agent orchestration (fresh workers +
typed shared ledger + verifier) must NOT be implemented during V4.
