# A217C — Agent Core v4 Batch 4 Standalone-Release-Identity Re-Gate

**Verdict:** `AGENT_CORE_V4_BATCH4_ROUTING_RED_A217C`
**Classification:** `RED_ROBUST_PLANNER_SIGNATURE_DRIFT`
**START_HEAD / test base:** `eaed29c8351cac3d19f1d18b9793896eff810490`
**Date:** 2026-09-26

**STOP at Phase 1.** First failing boundary: robust-runtime completion-contract tests
RED + 100% of live V4 queries fail with a deterministic `TypeError`. Phases 2–7 are not
executable — the agent cannot run any V4 query.

---

## Baseline

A217B verdict `AGENT_CORE_V4_BATCH4_ROUTING_RED_A217B`
(`RED_DEFERRED_TURN_OVEREXTENSION`): standalone singular release identity
("релиз 1.6.0 в OLP") over-extended on the deferred turn into release.scope/release.health.
A217 original blocker (analytics terminating at release.search) was CLOSED.

## Owner fix under test

Commits `08e8f96` (deferred resolver turn guidance), `3e483d6` (standalone identity
terminal in resolver procedure), `68c6d98` (metadata test). Diff vs A217B `40d781b`
touches: `agent_core_v4.py`, `wave_s1.py`, `test_agent_core_v4_batch4.py` (+ docs).

## Phase 0 — architecture invariant: design GREEN, but a shipped defect is present

Design genericity VERIFIED from the diff:
- No phrase router / semantic pre-pass added.
- No hard-coded release.progress/release.health branch in Agent Core.
- `runtime_guidance` is a generic one-turn planner-payload field populated ONLY when a
  declaratively non-autocomplete resolver contract is source-satisfied
  (`completion_satisfied and not runtime_autocomplete_allowed`), carrying
  `satisfied_loaded_skills` + a generic instruction; reset after one planner turn.
- Loaded skill detail exposes `runtime_autocomplete` metadata (generic).
- release.search procedure change is the resolver's own procedure text (allowed).
- dummy-55 / plugin registry invariant: `test_agent_core_v4_plugin_registry.py` **13/13 GREEN**.

However, the fix ships a production-breaking signature drift (see D-A217C-1).

## Phase 1 — tests: RED (8 failed, 185 passed)

`tests/test_agent_core_v4*.py` + `tests/test_v4*.py` = **8 RED / 185 GREEN**.

Seven failures are the robust-runtime completion-contract set, all failing with the SAME
deterministic error (`v4_runtime_failure`, ~10 ms, no LLM/source call):

```
RobustSkillNativePlannerV4.next_decision() got an unexpected keyword argument 'runtime_guidance'
```

- test_runtime_completes_lookup_then_assignee_without_model_ready
- test_runtime_completion_cannot_fabricate_without_observations
- test_premature_model_ready_is_rejected_until_contract_is_satisfied
- test_zero_row_search_is_a_legitimate_source_completion
- test_person_collection_completes_at_search_with_exact_keys
- test_missing_resolved_constraint_is_injected_before_terminal_call
- test_runtime_contract_completion_marker_and_prepass_flag

These are the EXACT same 7 tests that were RED when A205 shipped the original
`session_context` drift (GIGACODE-PO-AGENT-205). The owner again shipped with this set RED.

The 8th failure is the owner's own new A217C test (see F1).

## Live proof (first failing boundary)

Fresh agent on `eaed29c` (port 8212), two independent live queries:

```
status=FAILED  dt=0.15s  warnings=['v4_runtime_failure']
v4.error="RobustSkillNativePlannerV4.next_decision() got an unexpected keyword argument 'runtime_guidance'"
answer="Agent Core v4 не смог безопасно завершить траекторию."
```

100% of V4 queries die on the first planner turn. Zero LLM calls, zero source calls.

## D-A217C-1 (blocking, first failing boundary)

**Signature drift between the base planner and the production robust override.**

- A217C added `runtime_guidance` to the base
  `SkillNativePlannerV4.next_decision` (`agent_core_v4.py:345`) and the runtime call site
  passes it (`agent_core_v4.py:1190`, `runtime_guidance=deferred_completion_guidance`).
- The production planner `RobustSkillNativePlannerV4.next_decision`
  (`agent_core_v4_robust.py:149`) was NOT updated — its signature is
  `(self, *, user_query, catalog, loaded_skills, observations, session_context=None)` with no
  `runtime_guidance` and no `**kwargs`, and its payload (`agent_core_v4_robust.py:155-161`)
  omits `runtime_guidance`.
- The production chain installs `self.planner = RobustSkillNativePlannerV4(...)`
  (`agent_core_v4_robust.py:227`), so the inherited `process` loop's
  `self.planner.next_decision(..., runtime_guidance=...)` raises `TypeError` every turn.

Same defect class as **A205-1** (base added `session_context`, robust override not updated →
100% `v4_runtime_failure`) and **A205B** (pluginized override dropped a parameter). It is the
third occurrence; the recurring root cause is the absence of a signature-parity contract test
that constructs the PRODUCTION (robust/pluginized) runtime through `process()` and asserts the
planner call succeeds.

**Owner fix (both required, mirroring A205B):**
1. Add `runtime_guidance: Mapping[str, Any] | None = None` to
   `RobustSkillNativePlannerV4.next_decision` (`agent_core_v4_robust.py:149`) AND include
   `"runtime_guidance": dict(runtime_guidance or {})` in its payload (so the deferred guidance
   actually reaches the robust planner, not just that the call stops crashing).
2. Add a non-mocked regression that drives the production robust/pluginized runtime through
   `process()` with a capability call and asserts no `TypeError` (this is the test that would
   have caught all three occurrences).
Then full A217C re-gate (Phases 0–7).

## F1 (non-blocking, owner test-logic bug)

`test_agent_core_v4_batch4.py::test_release_search_loaded_detail_exposes_deferred_runtime_contract_metadata`
fails in isolation and in the suite:

```
catalog = registry.catalog
AttributeError: 'V4PluginRegistry' object has no attribute 'catalog'
```

`V4PluginRegistry` (`v4_plugin_registry.py:103`) exposes `.plugin_ids` and `.skills()` — not
`.catalog`. The owner's new metadata test references a non-existent attribute, so it does not
pass as shipped (A215-F1 / A196-F1 test-logic class). The underlying production behavior the
test targets (skill detail exposing `runtime_autocomplete=False`) is otherwise sound.

## Not executed (STOP rule)

Phases 2 (standalone identity), 3 (analytics non-regression), 4 (runtime-guidance trajectory),
5 (source-scope hardening), 6 (Browser C), 7 (retained regression) and the audit are not run:
every V4 query terminates in `v4_runtime_failure` before any skill load or source call, so no
phase can be evaluated. No local-factual reads, tenant scans, or mutations occurred (agent
dies pre-source; the only task-api contact is the health/readiness probe).

## Verdict

`AGENT_CORE_V4_BATCH4_ROUTING_RED_A217C` — STOP. No Batch 5.

The A217C runtime-guidance design is correct and generic, but it shipped with the production
robust planner override missing the new `runtime_guidance` parameter (D-A217C-1), so 100% of
V4 queries fail with a deterministic `TypeError` (7 robust-runtime tests RED + live proof).
Secondarily, the owner's own new metadata test is broken (F1). Owner fix is a bounded
signature-parity change to `agent_core_v4_robust.py` (+ a production-path regression test),
then full A217C re-gate.
