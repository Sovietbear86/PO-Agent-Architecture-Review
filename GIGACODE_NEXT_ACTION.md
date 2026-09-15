# GigaCode — Current Action

## Status
`ACTIVE_OWNER_ASSIGNMENT_189_V4_PLUGIN_REGISTRY_EXTRACTION`

## Mission
Assignment 188 closed the representative backend POC with verdict:

`AGENT_CORE_V4_REPRESENTATIVE_POC_GREEN`

The next milestone is **V4-PLUGIN**: make skills/capabilities plug-in/discoverable **without changing the already-proven V4 behavior**.

This is an extraction/refactoring milestone, **not a rewrite of the planner/runtime**.

## Mandatory rollback checkpoint
Before doing anything, read:

`V4_POC_GREEN_CHECKPOINT.md`

The exact known-good pre-plugin baseline is:

- commit: `0f03fca14fe078c86dca961362915e10cc985401`
- rollback/reference branch: `checkpoint/v4-poc-green-a188`
- QA proof: `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_COMPLETION_CONTRACT_REGATE_188.md`

**If this assignment causes an unbounded regression, STOP and compare against that checkpoint. Do not stack speculative fixes.**

## Mandatory pre-read
```bash
git pull --ff-only origin feat/core8-real-query-hardening-v2
git rev-parse HEAD
```

Read:
- `V4_POC_GREEN_CHECKPOINT.md`
- `V4_DOD_LOCK.md`
- `AGENT_CORE_V4_SKILL_NATIVE_SPEC.md`
- `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`
- `po-agent-platform-v2/src/po_agent/harness/agent_core_v4.py`
- `po-agent-platform-v2/src/po_agent/harness/agent_core_v4_completion.py`
- existing V4 tests
- A188 QA report

Record `START_HEAD`.

## Non-negotiable principle

> Adding a new V4 skill must not require changing Agent Core orchestration, planner logic, or runtime trajectory code.

Preserve the current working flow:

```text
raw user query
→ progressive skill selection/loading
→ governed typed capability
→ REAL AS21 observation
→ deterministic completion contract
→ result
```

Do **not** redesign this flow.

## Required target contracts
Introduce/refine stable plugin-facing contracts equivalent to:

```text
SkillSpec
CapabilitySpec
CapabilityHandler
CompletionContract
UIContract
```

Names may differ if the existing code has better canonical names, but the separation of responsibilities must be explicit and typed.

### SkillSpec
Must carry at least:
- stable skill id/version
- compact discovery summary
- procedural instructions/steps
- required/optional capabilities
- completion contract reference/declaration
- optional UI contract reference

### CapabilitySpec
Must carry at least:
- stable capability id/version
- argument/constraint contract
- source authority / read-only semantics
- handler binding
- postcondition/evidence metadata where applicable

### CapabilityHandler
- existing proven handlers should be reused/wrapped, not behaviorally rewritten;
- handler lookup must come from registry, not a central Agent Core hardcoded map.

### CompletionContract
- keep the A187/A188 generic deterministic completion mechanism;
- completion remains structural/typed and entity-agnostic;
- do not reintroduce stochastic terminal READY dependence;
- do not add query/entity-specific completion branches.

### UIContract
Provide a stable optional metadata contract for later Browser/UI work, e.g. preferred widget/type, result shape, required fields/state hints.
Do **not** build/redesign the Browser UI in this assignment.

## Architecture requirement — registry/discovery
Create a trusted V4 plugin registry/discovery layer outside Agent Core.

Required properties:
- Agent Core consumes a registry interface; it does not enumerate concrete task/sprint/release skill ids itself.
- Existing V4 skills/capabilities are registered through that layer.
- Existing handlers are registered through that layer.
- New trusted skill plugin can be added under the approved V4 plugin namespace/path and discovered without editing Agent Core.
- Discovery is bounded to trusted application/plugin locations; do not load arbitrary user filesystem code.
- Duplicate skill/capability ids fail closed at startup with an explicit error.
- Invalid plugin schema/contract fails closed and identifies the offending plugin.
- deterministic ordering for catalog/discovery.

## Critical compatibility rule
Do the **smallest possible extraction** around the A188-certified runtime.

Forbidden in Assignment 189:
- rewriting `RobustSkillNativePlannerV4` strategy;
- changing the model;
- semantic prepass;
- phrase/surname/entity routers;
- new task/sprint business semantics;
- changing REAL AS21/source behavior;
- altering B1/B2 logic;
- changing identity governance;
- changing completion semantics beyond the minimum wiring needed to obtain contracts from registry;
- Browser/UI feature implementation;
- GVS5H/multi-agent/V5 work;
- fixing `Задачи Семавина` with entity-specific logic.

The known Cyrillic issue remains a separate generic reliability/catalog regression item.

## Phase 1 — Inventory current registration seams
Before editing, document in the final report:
- where current `SkillSpecV4` instances are created;
- where capability specs are declared;
- where `_handlers`/handler mapping is built;
- how completion requirements are attached;
- which pieces can move behind registry without changing behavior.

Do not start with a broad rewrite.

## Phase 2 — Implement V4 plugin registry
Implement a minimal production registry/discovery layer.

Expected shape (adapt to repository conventions):

```text
v4_plugins/
  __init__.py
  registry.py
  contracts.py
  builtins/
    tasks.py
    sprints.py
    releases.py
    ...
```

A different layout is acceptable if cleaner, but Agent Core must depend on registry abstractions rather than concrete plugin modules.

Migrate the **existing V4 catalog only**. Do not add the remaining 54 skills yet.

## Phase 3 — Preserve existing semantics
After extraction, prove that existing V4 behavior is unchanged:
- same skill ids exposed;
- same compact catalog semantics;
- same handler/capability arguments;
- same completion requirements;
- same source authority;
- same fail-closed behavior;
- same observation/result shape for existing tests unless a purely internal metadata field is added.

Where practical, add compatibility assertions comparing pre-extraction fixture/catalog snapshots with registry-produced output.

## Phase 4 — Mandatory 55th dummy-skill proof
Add a **test-only** dummy plugin proving extensibility.

The test must demonstrate that a new 55th-style skill can be:
1. placed in/configured through the supported plugin discovery mechanism;
2. discovered by the registry;
3. included in compact skill metadata;
4. loaded as a full skill contract;
5. bound to a typed test capability/handler;
6. satisfy its completion contract;
7. expose optional UI metadata;

**without changing any Agent Core source file.**

This is the hard acceptance criterion for V4-PLUGIN extensibility.

Do not ship the dummy as a real production business skill.

## Phase 5 — Regression tests
Add focused tests for:
- built-in skill discovery;
- capability discovery;
- handler resolution;
- completion contract preservation;
- UI contract metadata;
- duplicate id rejection;
- malformed plugin rejection;
- deterministic ordering;
- trusted-path/namespace boundary;
- 55th dummy skill no-Agent-Core-change proof.

Run at minimum:

```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4_completion_contract.py -v
python -m pytest tests/ -k "v4" -v
python -m pytest tests/ -q
```

No new failures beyond the A188 baseline are allowed.

## Phase 6 — Live owner smoke against fresh REAL AS21
Do a bounded owner verification after tests. This is **not** the independent QA gate.

Refresh Oracle B live and run at minimum one fresh successful case from each retained family:
- lookup → assignee → tasks (DMS-380 or another live-valid case);
- person collection;
- person + space + status;
- current-sprint tasks;
- period → sprint;
- plural active sprints;
- source-backed non-roster identity;
- invented entity fail-closed.

For factual collections compare exact key sets, not only counts.

Mandatory invariants:
- `semantic_prepass_used=false`;
- REAL AS21 authoritative;
- deterministic completion still `runtime_contract` where contracted;
- zero new hardcode;
- no planner strategy change;
- no fabricated facts.

If an A188-certified path regresses, do not call V4-PLUGIN complete. Diagnose first failing boundary and compare to `checkpoint/v4-poc-green-a188`.

## Phase 7 — Documentation / plan status
Update architecture docs only as needed to reflect the implemented registry contracts and plugin discovery mechanism.

Preserve these plan facts:
- A188 checkpoint remains permanent rollback/reference state;
- V4-PLUGIN precedes Browser/UI and broad 54-skill migration;
- current goal is all 54 skills + full working UI/widgets + E2E;
- GVS5H/multi-agent is deferred to V5.

## Deliverables
Production/test changes for V4-PLUGIN plus a concise implementation report:

`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_PLUGIN_REGISTRY_OWNER_189.md`

Report must include:
- START_HEAD / END_HEAD;
- file/change inventory;
- before/after registration architecture;
- proof Agent Core no longer enumerates concrete built-in skill/handler map;
- 55th dummy-skill proof;
- test results and baseline delta;
- bounded live REAL-AS21 smoke results;
- explicit regression comparison to A188;
- known issues;
- recommendation for independent QA.

## Prepare next QA assignment, do not execute it
At the end, replace this file with **Assignment 190 — QA-only V4-PLUGIN re-gate**.

A190 must independently verify:
- plugin discovery/contracts;
- no Agent Core edit required for a dummy/new skill;
- exact retained A188 regression parity against fresh REAL AS21;
- no new full-suite regressions;
- no semantic-prepass/entity hardcode/planner rewrite;
- completion contract remains deterministic;
- duplicate/malformed plugin fail-closed;
- recommendation to proceed to V4-BROWSER only if GREEN.

Do **not** execute Assignment 190.

## STOP
After production changes, tests, bounded live smoke, report, commit/push, and preparation of Assignment 190 in `GIGACODE_NEXT_ACTION.md`, STOP and return the result.
