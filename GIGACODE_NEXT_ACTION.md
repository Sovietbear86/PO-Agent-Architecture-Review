# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_143_AGENT_CORE_V3_H1A_FOUNDATION`

## Mission
Owner Stage H1A for the Hermes-inspired Agent Core v3 foundation has been committed. Certify the new additive foundation WITHOUT modifying production code and WITHOUT broad skill regression.

Owner commits to verify in branch ancestry:
- `d2a4db2e52e5f27d3782d62fa3a02def9e46f257` — new `agent_core_v3.py` contracts/guards/validator/routing seam
- `62461c84ecc22a0909466e1c7b6224f3dde7fdbd` — runtime factory wires the v3 seam disabled by default
- `d4508af3343b786f0a67187f9ab0b4cf05243d95` — focused H1A unit tests

This assignment is architecture certification only. The v3 processor is NOT active yet; legacy runtime must remain behaviorally unchanged while the seam is disabled.

## Absolute rules
- QA/tester only. DO NOT change production/backend/frontend code.
- Pull `feat/core8-real-query-hardening-v2`; record exact HEAD and clean/dirty state.
- Do NOT run 54-skill marathon.
- Do NOT enable v3 for production/browser traffic.
- REAL AS21 only for protected live regressions; no local DB/sync/fake/frozen truth for live acceptance.
- Concurrency=1; normal timeout 180s, source calls 300s; retry transient transport errors twice with 30s backoff.
- A test failure must be localized; do not patch it yourself.

# PHASE 0 — provenance and code inspection
1. Prove all three owner commits are ancestors of HEAD.
2. Inspect `po-agent-platform-v2/src/po_agent/harness/agent_core_v3.py` and `runtime_factory.py` read-only.
3. Confirm `build_runtime_bundle(... agent_core_v3_enabled=False)` is the default and the wrapper delegates legacy traffic when disabled.
4. Confirm `AgentCoreV3RoutingSeam` preserves `adapter/router/capabilities/skills` expected by `ObservedHarnessRuntime`.

# PHASE 1 — focused unit gate
Run at minimum:
```bash
pytest -q tests/test_agent_core_v3_foundation.py
```
All tests must pass.

Additionally prove directly (small QA script is allowed, production edit is not):
- `SessionEnvelope.new_conversation()` creates distinct `conversation_id`, `runtime_session_id`, `turn_id`;
- `.next_turn()` preserves conversation/runtime IDs, rotates `turn_id`, and sets parent lineage;
- `AcceptedTurnContract` copies/freeze-protects its constraints from later source-dict mutation;
- removing requested `space` raises typed `CONSTRAINT_LOSS`;
- capability lacking requested `space` raises `UNSUPPORTED_CONSTRAINT`;
- executor args lacking requested `space` raises `CONSTRAINT_LOSS`.

# PHASE 2 — result postcondition safety gate
Use synthetic rows only to test the validator itself (this phase is contract-unit behavior, not source truth):

Contract:
```text
intent=task_search
assignee=Kalachanov.V.V
space=WMB
requested_constraints={assignee,space}
```

Cases:
A. Task `WMB-TEST` with assignee `Kalachanov.V.V`, `swtr_space=WMB` -> validator PASS.
B. Task `DMS-243` with assignee `Kalachanov.V.V`, `swtr_space=DMS` -> typed `RESULT_CONTRACT_VIOLATION` BEFORE any rendering/synthesis.
C. Matching WMB task but wrong assignee -> typed `RESULT_CONTRACT_VIOLATION`.

Capture failure code and details. This proves the exact class of UI failure observed earlier (WMB request rendering DMS evidence) is structurally blockable by v3.

# PHASE 3 — disabled seam legacy non-regression
Build runtime normally with the v3 flag OMITTED/default false. Prove the inner observed runtime contains `AgentCoreV3RoutingSeam(enabled=False)` and that requests still follow legacy path.

Run focused protected REAL A/B only:
1. existing `DMS-380` -> correct point-read/task key;
2. nonexistent `DMS-999999999` -> authoritative NOT_FOUND, never source unavailable;
3. `Задачи Гаранина` -> compare exact task-key set with fresh direct REAL MCP Oracle B;
4. `Задачи Гаранина в DMS` -> exact key set vs fresh Oracle B.

The H1A commit is RED if the disabled seam changes these legacy results.

# PHASE 4 — routing fail-closed behavior
Do NOT enable v3 in the production service. In an isolated QA/unit construction only:
- instantiate `AgentCoreV3RoutingSeam(enabled=True, processor=None, pilot_selector=lambda _: True)` around a harmless stub/legacy runtime;
- prove a selected request raises typed `V3_PROCESSOR_UNAVAILABLE`, rather than silently falling back to legacy;
- prove non-selected request still delegates legacy even if seam.enabled=True.

# PHASE 5 — architecture observability inventory
Report which H1A artifacts are now directly serializable/observable:
- SessionEnvelope fields;
- AcceptedTurnContract.to_dict();
- ValidationResult.to_dict();
- typed failure code/details.

Also explicitly record what is NOT implemented yet and must not be claimed GREEN:
- real v3 LLM semantic draft/grounding integration;
- capability registry runtime selection;
- v3 deterministic task executor;
- browser routing to v3;
- Learning Reviewer;
- A/B/C v3 pilot.

# FINAL REPORT
Write:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1A_FOUNDATION_143.md`

Allowed verdicts:
- `AGENT_CORE_V3_H1A_GREEN`
- `AGENT_CORE_V3_CONTRACT_RED`
- `AGENT_CORE_V3_VALIDATOR_RED`
- `AGENT_CORE_V3_SEAM_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

`AGENT_CORE_V3_H1A_GREEN` requires:
- focused H1A unit tests all PASS;
- constraint-loss/unsupported/result-violation typed behavior proven;
- disabled seam produces no protected legacy regression;
- no v3 production traffic enabled;
- no production modifications by QA.

Commit/push QA report only and STOP.

## Start now
Execute Assignment 143 completely.