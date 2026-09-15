# Assignment 189 — V4 Plugin Registry Owner Implementation

## Status

`OWNER_IMPLEMENTED / INDEPENDENT_QA_REQUIRED`

Assignment 188 remains the certified pre-plugin behavior baseline. This change intentionally modifies only the registration/extension seam; planner strategy, REAL AS21 source behavior, identity governance, B1/B2 collection logic, robust recovery, and deterministic completion are not redesigned.

## Rollback checkpoint

Permanent pre-plugin reference:

- commit: `0f03fca14fe078c86dca961362915e10cc985401`
- branch: `checkpoint/v4-poc-green-a188`
- proof: `AGENT_CORE_V4_COMPLETION_CONTRACT_REGATE_188.md`

Any unbounded regression must be compared against this checkpoint before further changes are stacked.

## Owner implementation

Added:

- `harness/v4_plugin_registry.py`
  - trusted-package discovery only;
  - deterministic ordering;
  - typed `V4SkillPlugin`, `CapabilityBindingV4`, `UIContractV4`;
  - duplicate skill/capability/plugin/UI rejection;
  - malformed/missing handler fail-closed;
  - registry-to-runtime handler binding;
  - controlled `with_plugin()` extension surface for bounded tests.
- `harness/v4_plugins/core.py`
  - A188 catalog expressed declaratively outside Agent Core;
  - existing capability descriptions, procedures and completion requirements retained;
  - reliable source-backed `task.lookup` / `sprint.current` handlers retained by binding;
  - optional UI metadata carried outside orchestration.
- `harness/agent_core_v4_pluginized.py`
  - thin production overlay over the A188-certified robust runtime;
  - swaps only registration after the certified lower-layer runtime has initialized;
  - exposes UI contracts without coupling Browser implementation to Agent Core.
- `runtime_factory.py`
  - production V4 entrypoint now builds `PluginizedRobustReliableAgentCoreV4Runtime`.
- `tests/test_agent_core_v4_plugin_registry.py`
  - built-in discovery/order;
  - binding completeness;
  - synthetic dummy-55 extension;
  - compact catalog/full contract/handler/completion/UI proof;
  - duplicate/malformed/missing-handler/trusted-namespace fail-closed cases.

## Compatibility strategy

This is deliberately a **strangler/extraction**, not a rewrite. The existing A188 runtime remains the lower-layer implementation and is initialized first; the active production registration seam is then atomically replaced by the trusted plugin registry.

This minimizes risk while satisfying the primary extensibility invariant: a new skill/plugin can be introduced through the plugin contract without editing `agent_core_v4.py`, `agent_core_v4_reliable.py`, `agent_core_v4_robust.py`, planner strategy, or runtime trajectory/completion logic.

The old hardcoded catalog remains physically present in the checkpoint-compatible parent implementation for rollback safety, but it is not the active production registration source after the pluginized runtime cutover. Removal of that dead compatibility path is intentionally deferred until the independent plugin gate and Browser regression are GREEN; deleting it now would increase rollback/regression risk without improving extension semantics.

## Dummy-55 proof encoded by owner tests

The test-only synthetic skill verifies:

```text
registry extension
 -> compact catalog visibility
 -> full skill contract load
 -> typed handler binding
 -> deterministic CompletionRequirement declaration
 -> UIContract availability
```

No Agent Core/planner/runtime trajectory source change is required for the dummy skill.

## Test status

Owner-side repository mutation was performed through the GitHub connector; the execution environment used for this change does not have the private repository/runtime mounted, so no local pytest or REAL-AS21 result is claimed here.

**No test result is fabricated.** Assignment 190 is the independent executable QA gate and must run focused/full pytest plus fresh REAL AS21 A188 regression before V4-PLUGIN can be marked GREEN.

## Next gate

`Assignment 190 — QA-only V4 Plugin Registry Re-Gate`

GigaCode must discard its cancelled local A189 implementation work, synchronize to the owner remote HEAD, make no production changes, and commit only the QA report.

V4-BROWSER may begin only after `AGENT_CORE_V4_PLUGIN_GATE_GREEN`.
