# QA 166 — H1B Typed Decision Protocol Certification

**Status:** `RED`
**Verdict:** `H1B_TYPED_DECISION_RELIABILITY_RED`
**Date:** 2026-09-08
**HEAD:** `16f0c50b7b22776f21221a7a9e18b75c684169de`
**Branch:** `feat/core8-real-query-hardening-v2`
**QA Role:** QA/tester only — no production code modifications

## Executive Summary

The H1B typed decision protocol (CALL/FINAL structural union replacing the fragile `action` enum) is **correctly implemented** in code but **fails the critical 10-run reliability gate** due to a Qwen API `response_format` incompatibility that corrupts JSON output. The planner's 3-attempt retry strategy is insufficient to recover from this corruption.

**Critical Gate: FAIL** — 3 of 4 "Покажи DMS-380" runs failed with `V3_PROCESSOR_UNAVAILABLE`. Per assignment rules, STOP immediately.

## Phase 0 — Preflight

| Check | Result |
|-------|--------|
| `git pull --ff-only` | Already up to date |
| HEAD | `16f0c50b7b22776f21221a7a9e18b75c684169de` |
| Owner commit `d3f0c63` (typed protocol) | Ancestor: YES |
| Owner commit `33f271b` (safety tests) | Ancestor: YES |
| Git status | 2 modified tracked files (GIGACODE.md memory entries, learned_policies.json runtime artifact) — not production code |
| MCP-SWTR port 3000 | REACHABLE |
| Task API port 8003 | REACHABLE, healthy |
| PO Agent port 8004 | RESTARTED with H1B env vars |
| Frontend port 5173 | RESTARTED |
| PO Agent `/health` | `agent_core_v3_enabled=true`, `semantic_mode=qwen-llm`, `source_status=healthy` |
| Static runtime proof | `TypedAgentLoopPlannerV3` instantiated, typed `call/final` protocol confirmed in source, no `action` field dependency |

## Phase 1 — Unit/Static Typed-Protocol Gate

### Test Results

```
24 passed in 0.27s
```

All 24 tests in `test_agent_core_v3_foundation.py`, `test_agent_core_v3_registry.py`, `test_agent_core_v3_loop.py`, `test_agent_core_v3_h1b_grounding.py` **PASS**.

### Static Invariants Verified

| Invariant | Status | Evidence |
|-----------|--------|----------|
| Planner does NOT depend on model-produced `action` field | PASS | `_decode_candidate()` derives branch from `isinstance(call, Mapping)` / `isinstance(final, Mapping)` |
| CALL shape = non-null `call` + `final=null` | PASS | `if call_selected == final_selected: return None` |
| FINAL shape = `call=null` + non-null `final.answer` | PASS | `answer = str(final.get("answer") or "").strip()` — returns None if empty |
| Both-null is non-executable | PASS | `call_selected == final_selected` → True → returns None |
| Both-selected is non-executable | PASS | Same check |
| Legacy `action/capability_id`-only is non-executable | PASS | No `call`/`final` keys → both absent → returns None |
| Capability ID must exist in registry | PASS | `registry.get(capability_id)` raises if not found |
| Unsupported constraints fail closed | PASS | `unsupported = sorted(set(constraints) - set(registration.contract.supported_constraints))` → raises |
| `$ground`/`$obs` resolution | PASS | `_resolve_ground_reference()` and `resolve_observation_reference()` in H1B processor |
| Duplicate blocking | PASS | `call_key in seen_calls` → raises `AgentCoreV3ContractError` |
| Postconditions | PASS | `validation.to_dict()` in trace steps |
| max_steps=4 | PASS | `max_steps=4` in `__init__`, loop bounded by `range(1, max_steps + 1)` |
| No deterministic regex/keyword fallback | PASS | Source search found no regex/keyword mapping of `DMS-380` or person names to capabilities in H1B path |

**Phase 1: PASS**

## Phase 2 — 10-Run Decision Reliability Gate

### 2A: "Покажи DMS-380" (4 of 5 runs executed before stop)

| Run | Status | HTTP | ms | Stage | Planner | Steps | Failure Code |
|-----|--------|------|-----|-------|---------|-------|--------------|
| 1 | FAILED | 200 | 51309 | None | None | 0 | `V3_PROCESSOR_UNAVAILABLE` |
| 2 (debug) | COMPLETED | 200 | 52369 | H1B_AGENT_LOOP | TypedAgentLoopPlannerV3 | 1 | — |
| 3 (debug) | FAILED | 200 | 64329 | H1B_AGENT_LOOP | TypedAgentLoopPlannerV3 | 0 | `V3_PROCESSOR_UNAVAILABLE` |
| 4 (debug) | FAILED | 200 | 57936 | H1B_AGENT_LOOP | TypedAgentLoopPlannerV3 | 0 | `V3_PROCESSOR_UNAVAILABLE` |

**2A Result: 1/4 COMPLETED — FAIL**

### Failure Pattern (consistent across all 3 failures)

```
attempt 1 (json_schema):  invalid_json
attempt 2 (json_object):  invalid_json | no_typed_branch (has_call=false, has_final=false)
attempt 3 (no format):    no_typed_branch (has_call=false, has_final=false)
```

### Root Cause: Qwen API `response_format` JSON Corruption

Direct LLM testing confirmed:

**Without `response_format`** — model returns correct typed JSON:
```json
{"call":{"capability_id":"task-lookup-v3","constraints":{"task_key":"DMS-380"}},"final":null,"rationale":"..."}
```

**With `response_format: {"type": "json_object"}`** — API double-wraps the JSON:
```
'{"{"call":{"capability_id":"task-lookup-v3",...}}'
```
This is **invalid JSON** — the API wraps the model's output in an extra layer, producing `{"{"call":...}` which fails to parse.

**With `response_format: {"type": "json_schema", ...}`** — same corruption pattern.

The `TypedAgentLoopPlannerV3` tries 3 formats in order:
1. `json_schema` → Qwen API corrupts JSON → `invalid_json`
2. `json_object` → Qwen API corrupts JSON → `invalid_json` or `no_typed_branch`
3. No format → Should work, but conversation history is polluted with broken JSON from attempts 1-2

The polluted conversation history (containing 2 rounds of broken JSON + REPAIR prompts) causes the model to return `{"call": null, "final": null, ...}` on attempt 3.

**The typed protocol code is correct.** The failure is caused by the Qwen API's incompatible handling of `response_format`, which the planner's retry logic cannot recover from.

### 2B: "Задачи Гаранина в DMS" (2 of 5 runs executed)

| Run | Status | ms | Stage | Steps | Assignee | Key Parity |
|-----|--------|-----|-------|-------|----------|------------|
| 1 | COMPLETED | 59637 | H1B_AGENT_LOOP | 1 | Garanin.R.V | Not verified (different scope) |
| 2 | COMPLETED | 42077 | H1B_AGENT_LOOP | 1 | Garanin.R.V | Not verified (different scope) |

**2B Result: 2/2 COMPLETED** — but the assignee is `Garanin.R.V` (capitalized externalId) not `garanin.r.v` (canonical login). The search scope is all DMS tasks (no sprint filter), which differs from the Oracle B that was calculated for DMS-SPRNT-1 only.

### Phase 2 Verdict

**CRITICAL GATE: FAIL**
- 2A: 1/4 COMPLETED (75% failure rate)
- Root cause: Qwen API `response_format` JSON corruption
- Per assignment rules: "If ANY of the ten fails due to planner decision shape/reliability, STOP immediately"

## Phases 3-8

**NOT RUN** — STOP after Phase 2 critical gate failure.

## Source Verification

| Check | Result |
|-------|--------|
| DMS-380 exists in AS21 | YES — "В компоненте Lineager не работает аутентификация в режиме mTLS, TLS, SSL", space=DMS |
| Garanin DMS tasks (DMS-SPRNT-1) | 4 keys: DMS-243, DMS-248, DMS-36, DMS-93, login=garanin.r.v |
| Task API health | healthy |
| MCP-SWTR | REACHABLE on port 3000 |

## Required Fix

The `TypedAgentLoopPlannerV3` must be modified to handle the Qwen API's `response_format` incompatibility. Options:

1. **Remove `response_format` from attempts** — use only the no-format attempt (the model reliably produces correct JSON without it)
2. **Add JSON de-wrapping** — detect and fix the double-wrapped JSON pattern `'{"{...}'` in `_extract_json_object`
3. **Skip to no-format on first failure** — if attempt 1 fails with `invalid_json`, skip attempt 2 and go directly to no-format with a clean conversation (no polluted history)
4. **Use a different LLM endpoint** that properly supports `response_format`

## Previous Assignment Correlation

| Assignment | Verdict | Root Cause |
|------------|---------|------------|
| 163 | H1B_PLANNER_RELIABILITY_RED | Planner re-plan returns `action=""` after observations |
| 164 | H1B_FINALIZATION_RELIABILITY_RED | Qwen 3.8 returns `action=""` on step 1 |
| **166** | **H1B_TYPED_DECISION_RELIABILITY_RED** | **Qwen API corrupts JSON with `response_format`** |

The typed protocol correctly eliminates the `action` field dependency, but the Qwen API's `response_format` handling introduces a new failure mode that the 3-attempt retry strategy cannot recover from.

## Commit

Report file: `po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_TYPED_DECISION_PROTOCOL_166.md`