# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_190_V4_PLUGIN_REGISTRY_REGATE`

## Role lock
GigaCode is **QA/adversarial tester only**.

Do NOT implement, refactor, fix, or improve production code, prompts, adapters, tests, config, architecture docs, or plugin code. The owner has implemented the V4-PLUGIN changes independently.

## Mandatory local cleanup before testing
Assignment 189 is cancelled as a GigaCode implementation task.

1. Stop any A189 work/processes.
2. Run `git status --short`.
3. If the worktree contains only changes created by GigaCode for cancelled Assignment 189, discard those local tracked/untracked A189 changes.
4. If there is any local change that may pre-date A189 or belongs to the user/owner, **STOP and report it instead of deleting it**.
5. Fetch the owner branch and reset/sync the worktree to the remote owner HEAD of:
   `feat/core8-real-query-hardening-v2`.
6. Record `git rev-parse HEAD` as `START_HEAD` and do not change production files afterwards.

The permanent pre-plugin rollback/reference point remains:
- commit `0f03fca14fe078c86dca961362915e10cc985401`
- branch `checkpoint/v4-poc-green-a188`

## Mission
Independently re-gate the owner's V4 pluginized Skill/Capability Registry and prove two things simultaneously:

1. a new skill can be connected through the plugin extension surface without editing Agent Core/planner/runtime trajectory code;
2. all A188-certified behavior remains regression-safe against fresh REAL AS21.

## Files to inspect, not modify
- `V4_POC_GREEN_CHECKPOINT.md`
- `V4_DOD_LOCK.md`
- `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`
- `po-agent-platform-v2/src/po_agent/harness/v4_plugin_registry.py`
- `po-agent-platform-v2/src/po_agent/harness/v4_plugins/`
- `po-agent-platform-v2/src/po_agent/harness/agent_core_v4_pluginized.py`
- `po-agent-platform-v2/src/po_agent/harness/runtime_factory.py`
- `po-agent-platform-v2/tests/test_agent_core_v4_plugin_registry.py`
- A188 report

## Phase 0 — diff and architecture audit
Compare `START_HEAD` with `0f03fca14fe078c86dca961362915e10cc985401`.

Verify:
- planner strategy is not rewritten;
- model is unchanged (`Qwen/Qwen3.8-27B`);
- no semantic prepass is introduced;
- source/identity/B1/B2/completion logic is not behaviorally rewritten;
- production runtime entrypoint uses the pluginized robust runtime;
- plugin discovery is limited to the trusted application namespace;
- duplicate/malformed plugin contracts fail closed;
- discovery/catalog ordering is deterministic;
- handler bindings are registry-driven at the active production runtime seam;
- no surname/person/task/sprint/query-phrase hardcode was added.

If any architecture invariant is violated, report bounded RED; do not fix it.

## Phase 1 — build and regression suites
Run:

```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4_plugin_registry.py -v
python -m pytest tests/test_agent_core_v4_completion_contract.py -v
python -m pytest tests/ -k "v4" -v
python -m pytest tests/ -q
```

Acceptance:
- plugin registry focused tests GREEN;
- completion contract remains 20/20 GREEN;
- all V4 tests GREEN;
- no NEW full-suite failures/errors beyond A188 baseline (`16 failed + 11 errors`, pre-existing classes only).

Any import/syntax/runtime construction failure is immediate RED.

## Phase 2 — real dummy-55 extensibility proof
Independently prove a synthetic 55th-style skill can be introduced using only the supported plugin contract/registry surface.

Required chain:

```text
plugin added/injected through supported extension surface
 -> registry accepts/discovers it
 -> compact catalog exposes it
 -> full skill contract loads
 -> typed capability handler resolves
 -> completion contract is available/satisfied structurally
 -> UIContract metadata is exposed
```

Hard rule: this proof must require **zero edits** to:
- `agent_core_v4.py`
- `agent_core_v4_reliable.py`
- `agent_core_v4_robust.py`
- planner logic
- runtime trajectory/completion logic

Do not commit the dummy business skill to production.

## Phase 3 — A188 retained REAL-AS21 regression
Start fresh Task API and PO Agent on fresh ports. Refresh Oracle B from REAL AS21 immediately before the cases.

Re-run at minimum:
- 10x `Покажи DMS-380 и затем задачи его исполнителя` (or source-current same key if still valid): exact key-set parity, `runtime_contract`;
- 5x second lookup→assignee→tasks family discovered live;
- 5x person collection;
- 5x person + space + `not_completed`;
- 3x current-sprint task collection;
- 3x human-period → sprint;
- 2x plural active-sprint list;
- 2x source-backed non-roster identity;
- B1 complete sprint collection (prefer a >100 live sprint if available; otherwise document source state);
- B2 source-accurate open/terminal classification;
- invented task/person/sprint and ambiguous identity negative controls.

For factual collections compare **exact key sets**, not counts only.

Mandatory all-run invariants:
- `semantic_prepass_used=false`;
- REAL AS21 authoritative;
- contracted successful trajectories finish with `completion=runtime_contract`;
- no post-satisfaction repair loop;
- zero fabricated facts;
- fail-closed on ambiguity/source failure.

## Phase 4 — regression safety / checkpoint comparison
Explicitly answer:
- Did any A188 GREEN scenario regress after V4-PLUGIN?
- Is there any behavior that works at checkpoint `0f03fca...` but fails at owner `START_HEAD`?
- Are differences registration/metadata-only, or did runtime semantics change?

If a regression exists, identify the first failing boundary and report RED. Do not patch it.

Retain the known pre-existing generic model issue (`Задачи Семавина` unscoped Cyrillic mutation) as a tracked item; do not introduce entity-specific fixes.

## Allowed output
Create/commit/push **only**:

`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_PLUGIN_REGISTRY_REGATE_190.md`

Do not modify anything else.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_PLUGIN_GATE_GREEN`
- `AGENT_CORE_V4_PLUGIN_GATE_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires all mandatory architecture, focused test, dummy-55, and retained REAL-AS21 gates to pass with no new regression.

If GREEN, recommendation:
**Proceed to V4-BROWSER/UI; keep checkpoint/v4-poc-green-a188 permanently; then migrate 54 skills progressively through the plugin surface.**

## STOP
After committing/pushing the QA report, stop. Do not start Browser/UI or any next assignment.