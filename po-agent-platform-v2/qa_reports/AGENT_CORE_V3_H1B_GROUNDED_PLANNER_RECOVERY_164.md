# Assignment 164 — H1B Grounded Planner Recovery

**Verdict:** `H1B_FINALIZATION_RELIABILITY_RED`

**Date:** 2026-09-08T10:46Z
**HEAD:** `32eebaac368509a9991fae12b760e269ec7b84fc`
**Branch:** `feat/core8-real-query-hardening-v2`
**Role:** QA only — no production code modified

---

## Owner Commits Verified

| Commit | Description | Ancestor |
|--------|-------------|----------|
| `444929f` | ground planner inputs and normalize explicit final shape | ✅ |
| `31c4817` | restore semantic grounding before loop execution | ✅ |
| `db79fe9` | cover grounded reference safety tests | ✅ |

---

## Phase 0 — Preflight

- `git pull --ff-only` — Already up to date.
- HEAD: `32eebaa` (clean working tree, only untracked QA scripts).
- PO Agent v3: `/health` → `agent_core_v3_enabled=true`, `source_status=healthy`, `semantic_mode=qwen-llm`.
- Task API: `/health` → healthy.
- MCP-SWTR: SSE transport, 48 tools connected.
- Frontend: port 5175, responding 200.

## Phase 1 — Unit/Safety Gate

**Result: 19 PASS / 0 FAIL** (0.42s)

```
pytest -q tests/test_agent_core_v3_foundation.py tests/test_agent_core_v3_registry.py \
  tests/test_agent_core_v3_loop.py tests/test_agent_core_v3_h1b_grounding.py
→ 19 passed
```

### Static Proof

| # | Claim | Verdict | Evidence |
|---|-------|---------|----------|
| 1 | Planner catalog from H1A registry only | ✅ VERIFIED | `agent_core_v3_pilot.py:58` `self.registry = build_h1_task_registry()`; registry contains exactly `task-lookup-v3` + `task-search-v3` (v3.1.0-h1a) |
| 2 | `$obs` authoritative observation binding | ✅ VERIFIED | `agent_core_v3_loop.py:resolve_observation_reference()` validates step, traverses path, raises on missing |
| 3 | `$ground.member_login` only from grounder | ✅ VERIFIED | `agent_core_v3_h1b.py:_resolve_ground_reference()` looks up `grounded_values`, raises `UNRESOLVED_CONSTRAINT` if empty; additional guard: literal must match `person_raw` before substituting `member_login` |
| 4 | Empty action → final ONLY with `final_answer` + no capability/constraints | ✅ VERIFIED | `agent_core_v3_loop.py`: `if not action and observations and not capability_id and not constraints and final_answer: action = "final"` |
| 5 | Empty/ambiguous without final_answer fails closed | ✅ VERIFIED | Falls through to `if action != "call_capability": raise UNSUPPORTED_CONSTRAINT` |
| 6 | max_steps=4, duplicate blocking intact | ✅ VERIFIED | `AgentLoopPlannerV3.__init__`: `max_steps: int = 4`; `seen_calls` set blocks duplicate `(capability_id, constraints)` |

---

## Phase 2 — REAL Challenge A

**Query:** `Проверь DMS-380 и затем покажи задачи его исполнителя`

### Oracle B (REAL AS21 via MCP-SWTR)

- **DMS-380:** key=DMS-380, title="В компоненте Lineager не работает аутентификация в режиме mTLS, TLS, SSL", status=qa (Тестирование), space=DMS, assignee=`semavin.m.m` (Михаил Семавин, code=Semavin.M.M)
- **Semavin.M.M DMS tasks:** 136 tasks (DMS-120, DMS-144, DMS-17, … DMS-380, DMS-388, DMS-44, …)

### Agent A Results (3 attempts)

| Attempt | Status | Architecture | Failure | Details |
|---------|--------|--------------|---------|---------|
| 1 | FAILED | H1B_AGENT_LOOP | UNSUPPORTED_CONSTRAINT | `{"action": "", "has_final_answer": false}` — planner returned empty action, step 1, no observations |
| 2 | NEEDS_CLARIFICATION | H1A_REGISTRY | — | Semantic pre-pass produced clarification: "Уточните, какой результат PO Agent должен получить." |
| 3 | NEEDS_CLARIFICATION | H1A_REGISTRY | — | Same clarification as attempt 2 |
| 4 | FAILED | H1B_AGENT_LOOP | UNSUPPORTED_CONSTRAINT | `{"action": "", "has_final_answer": false}` — same as attempt 1 |

**Root causes identified:**

1. **Planner empty-action on step 1:** When the H1B loop does start (attempts 1 & 4), Qwen 3.8 returns `action=""` with no `final_answer` on the very first planner call. The normalization fix in `444929f` only handles the case where `final_answer` is present AND observations exist — it does NOT help when the planner fails to produce any valid action on step 1.

2. **Semantic pre-pass flakiness:** When the H1B loop doesn't start (attempts 2 & 3), the semantic interpreter (`_semantic_contract`) produces a clarification because the LLM returns `intent: null` for the compound query. The H1B agent loop is never reached.

**Requirement check:**

| Requirement | Result |
|-------------|--------|
| COMPLETED | ❌ FAILED / NEEDS_CLARIFICATION |
| H1B_AGENT_LOOP | ❌ (when loop starts) or H1A_REGISTRY (clarification) |
| lookup DMS-380 → observation → assignee task-search | ❌ Never reached |
| Second-step assignee = source-backed login | ❌ N/A |
| ≥2 and ≤4 capability calls | ❌ 0 capability calls |
| Every postcondition PASS | ❌ N/A |
| Exact task-key-set parity with Oracle B | ❌ N/A |
| No planner empty-action failure | ❌ **Planner empty-action failure confirmed** |

**Phase 2 verdict: RED**

---

## Phase 3 — REAL Challenge B (Grounded Human Name)

**Query:** `Найди задачи Гаранина в DMS и затем покажи подробности DMS-380`

### Oracle B (REAL AS21 via MCP-SWTR)

- **"Гаранин" search:** 5 users match (Garanin.R.V, Garanin.D.G, Garanin.D.V, DGennaGaranin, SP-Garanin.D.G)
- **Garanin.R.V DMS tasks (page 0):** 7 tasks (DMS-243, DMS-248, DMS-262, DMS-326, DMS-328, DMS-36, DMS-93)
- **DMS-380:** same as above

### Agent A Results (2 attempts)

| Attempt | Status | Architecture | Failure | Details |
|---------|--------|--------------|---------|---------|
| 1 | FAILED | H1B_AGENT_LOOP | UNSUPPORTED_CONSTRAINT | `{"action": "", "has_final_answer": false}` |
| 2 | FAILED | H1B_AGENT_LOOP | UNSUPPORTED_CONSTRAINT | `{"action": "", "has_final_answer": false}` |

**Requirement check:**

| Requirement | Result |
|-------------|--------|
| Semantic pre-pass resolves human to login | ❌ Never reached (planner fails before execution) |
| AS21 receives canonical login, NOT raw name | ❌ N/A |
| One task-search-v3 + one task-lookup-v3 | ❌ 0 capability calls |
| Both outcomes preserved | ❌ N/A |
| Exact search key parity + point-read parity | ❌ N/A |
| COMPLETED | ❌ FAILED |
| No HTTP 409 from raw human name | ✅ (no 409 observed, but no search executed) |

**Phase 3 verdict: RED** (same root cause as Phase 2)

---

## Phase 4 — Final-Shape and Safety Controls

| # | Control | Result | Evidence |
|---|---------|--------|----------|
| 1 | Empty action + nonempty final_answer + no capability/constraints → normalized as final | ✅ PASS | Unit test `test_agent_core_v3_loop.py` covers this; code verified in `agent_core_v3_loop.py` |
| 2 | Empty action without final_answer → fails closed | ✅ PASS | Code: falls through to `UNSUPPORTED_CONSTRAINT` raise; confirmed by all 8+ real API calls |
| 3 | Invented `$ground.member_login` when grounder has no value → fails closed | ✅ PASS | `_resolve_ground_reference()` raises `UNRESOLVED_CONSTRAINT` if `grounded_values.get(field)` is empty |
| 4 | Invented `$obs` path → fails closed | ✅ PASS | `resolve_observation_reference()` raises on missing step or path |
| 5 | Duplicate capability+constraints blocked; no >4 calls | ✅ PASS | `seen_calls` set; `max_steps=4` in `AgentLoopPlannerV3.__init__` |
| 6 | Unsupported compound (`история его статусов`) must NOT silently return only lookup | ✅ PASS | Returns FAILED with `UNSUPPORTED_CONSTRAINT` (empty action). Does NOT silently succeed with partial result. |

**Phase 4 verdict: PASS** (all safety controls hold)

---

## Phase 5 — Protected Single-Step Recovery

| # | Query | Status | Architecture | Failure |
|---|-------|--------|--------------|---------|
| 1 | `Задачи Гаранина` | FAILED | H1B_AGENT_LOOP | `V3_PROCESSOR_UNAVAILABLE` — planner did not return valid JSON |
| 2 | `Задачи Гаранина в DMS` | FAILED | H1B_AGENT_LOOP | `UNSUPPORTED_CONSTRAINT` — `{"action": "", "has_final_answer": false}` |
| 3 | `Задачи Калачанова в WMB` | FAILED | H1B_AGENT_LOOP | `UNSUPPORTED_CONSTRAINT` — `{"action": "", "has_final_answer": false}` |
| 4 | `Покажи DMS-380` | FAILED | H1B_AGENT_LOOP | `UNSUPPORTED_CONSTRAINT` — `{"action": "", "has_final_answer": false}` |

**4/4 single-step queries FAILED.** The H1B agent loop is not functional for ANY query type — not just compound/multi-step. The Qwen 3.8 planner consistently fails to produce a valid `action` field.

**Phase 5 verdict: RED**

---

## Phase 6 — Browser C Regression (Playwright H0)

**Command:** `npm run e2e:h0` (with `PO_AGENT_E2E_EXTERNAL_FRONTEND=1`)

| Test | Result | Error |
|------|--------|-------|
| Session isolation | PENDING (not in failed list) | — |
| v3 browser pilot: Задачи Гаранина | **FAILED** | `Expected: "COMPLETED" Received: "FAILED"` |
| v3 browser pilot: Задачи Гаранина в DMS | **FAILED** | `Expected: "COMPLETED" Received: "FAILED"` |
| v3 browser pilot: Задачи Калачанова в WMB | **FAILED** | `Expected: "COMPLETED" Received: "FAILED"` |
| v3 browser pilot: Покажи DMS-380 | **FAILED** | `Expected: "COMPLETED" Received: "FAILED"` |

**Result: 1/5 PASS** (session isolation) — all 4 pilot tests failed with the same root cause: the H1B agent loop fails at the planner level before any capability is executed.

**Phase 6 verdict: RED** (was 5/5 before the defect; now 1/5)

---

## Phase 7 — Browser C Multi-Step

**Not executed** — Phase 2 and Phase 3 already proved RED at the API level. The multi-step challenges cannot complete because the planner fails on the first step. Browser C multi-step would produce the same failure.

---

## Root Cause Analysis

The owner fix in `444929f` addressed a specific edge case: when the planner returns an empty `action` but the shape is "unambiguously final" (final_answer present, no capability/constraints, observations exist). This fix is correct and verified in unit tests.

However, the **actual failure mode in production** is different: Qwen 3.8 returns `action=""` with **no** `final_answer` on the **first** planner call (step 1, no observations). This is not the "unambiguously final" case — it's a plain planner failure. The normalization guard correctly does NOT normalize this (it would be wrong to guess a final answer from nothing), and the system correctly fails closed.

The fundamental issue is **Qwen 3.8 planner reliability**: the model does not consistently produce a valid `action` field from the JSON schema. This is the same defect identified in Assignment 163 (`H1B_PLANNER_RELIABILITY_RED`) and remains unresolved.

**Additional finding:** The semantic pre-pass (`_semantic_contract`) intermittently produces clarifications for compound queries, preventing the H1B agent loop from starting. This is a secondary reliability issue that compounds the planner problem.

---

## Summary

| Phase | Verdict |
|-------|---------|
| 0 — Preflight | ✅ PASS |
| 1 — Unit/Safety | ✅ PASS (19/19) |
| 2 — REAL Challenge A | ❌ RED |
| 3 — REAL Challenge B | ❌ RED |
| 4 — Safety Controls | ✅ PASS (6/6) |
| 5 — Single-Step Recovery | ❌ RED (0/4) |
| 6 — Playwright H0 | ❌ RED (1/5) |
| 7 — Browser C Multi-Step | ⏭️ N/A (blocked by Phases 2/3) |

## Final Verdict

**`H1B_FINALIZATION_RELIABILITY_RED`**

The H1B agent loop is non-functional for all query types. Qwen 3.8 consistently returns empty `action` fields from the planner, causing the system to fail closed at step 1. The owner's normalization fix is correct but addresses a different edge case than the one occurring in production. The single-step H0 regression (5/5 → 1/5) confirms this is a blocking defect.

**Blocking for:** All H1B agent-loop features, H0 browser regression, multi-step capabilities.
**Not blocking:** Safety controls, unit test suite, semantic grounding logic (verified correct in isolation).

---

*Report generated by GigaCode QA. No production code, prompts, tests, or configuration was modified.*