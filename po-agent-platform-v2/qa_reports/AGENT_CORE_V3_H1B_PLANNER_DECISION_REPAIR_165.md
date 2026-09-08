# Assignment 165 — H1B Planner Decision Repair Retest

## Verdict

**`H1B_PLANNER_DECISION_REPAIR_RED`**

## Summary

The planner repair mechanism (commit `97081ac`) is correctly implemented and executes 3 bounded
attempts per planner decision. However, Qwen 3.8 continues to return empty/non-executable planner
objects (`action="", capability_id=""`) on **60% of runs**, exhausting the full 3-attempt budget and
failing with `V3_PROCESSOR_UNAVAILABLE`.

**Result: 2/5 COMPLETED (acceptance requires 5/5).**

Stopped at Phase 2 per assignment instructions. Phases 3–8 not executed.

---

## Environment

| Field | Value |
|-------|-------|
| Branch | `feat/core8-real-query-hardening-v2` |
| HEAD | `6ee7f490cdb8dc7b704309ee092d9018d521550c` |
| Owner commits verified | `97081ac`, `ffe218c`, `f2bced2` (all ancestors) |
| PO Agent v3 | healthy, `agent_core_v3_enabled=true`, `semantic_mode=qwen-llm`, `source_status=healthy` |
| Task API | healthy |
| MCP-SWTR | SSE transport, 48 tools connected |
| Frontend | port 5175, status 200 |
| Model | Qwen 3.8 (Qwen/Qwen3.8-27B) |
| Date | 2026-09-08 |

---

## Phase 1 — Unit/Static Safety Gate

### Unit tests: **23/23 PASS**

```
pytest -q tests/test_agent_core_v3_foundation.py tests/test_agent_core_v3_registry.py \
         tests/test_agent_core_v3_loop.py tests/test_agent_core_v3_h1b_grounding.py
→ 23 passed in 0.44s
```

### Static proof: **7/7 verified**

| # | Property | Status |
|---|----------|--------|
| 1 | Non-executable JSON does NOT end retry loop (3 bounded attempts) | ✅ |
| 2 | Subsequent attempts use explicit repair prompt (`REPAIR` constant) | ✅ |
| 3 | Empty action + valid capability_id → normalized to `call_capability` | ✅ |
| 4 | Empty action + no capability + no final_answer → fail-closed | ✅ |
| 5 | Semantic pre-pass is advisory in H1B (does not suppress loop) | ✅ |
| 6 | Human display name cannot reach task-search executor | ✅ |
| 7 | max_steps=4, duplicate blocking, `$obs` safety intact | ✅ |

---

## Phase 2 — Planner Repair Focused Probe (STOPPING PHASE)

Query: `Покажи DMS-380` — 5 fresh sessions, concurrency=1.

| Run | Session | Status | Elapsed | Attempts | All attempts | Failure |
|-----|---------|--------|---------|----------|--------------|---------|
| 1 | `165-phase2-probe-1-a3f83740` | **FAILED** | 86.6s | 3/3 | all `action="", capability_id=""` | `V3_PROCESSOR_UNAVAILABLE` |
| 2 | `165-phase2-probe-2-26c138fe` | **FAILED** | 123.6s | 3/3 | all `action="", capability_id=""` | `V3_PROCESSOR_UNAVAILABLE` |
| 3 | `165-phase2-probe-3-649b930e` | COMPLETED | 85.6s | — | — | — |
| 4 | `165-phase2-probe-4-945256ef` | **FAILED** | 79.5s | 3/3 | all `action="", capability_id=""` | `V3_PROCESSOR_UNAVAILABLE` |
| 5 | `165-phase2-probe-5-268f3d45` | COMPLETED | 105.6s | — | — | — |

### Success cases (Runs 3, 5)

Both successful runs completed with:
- `architecture_stage = H1B_AGENT_LOOP`
- 1 loop step: `task-lookup-v3` with `constraints={'task_key': 'DMS-380'}`
- `planner_class = AgentLoopPlannerV3`
- Grounded: `{'task_key': 'DMS-380', 'product': 'DMS'}`
- Correct task data returned (DMS-380, Lineager mTLS auth issue, status=Testing/QA)

### Failure pattern analysis

All 3 failed runs show **identical failure signature**:
- Attempt 1: `action="", capability_id="", has_final_answer=false`
- Attempt 2 (repair turn 1): `action="", capability_id="", has_final_answer=false`
- Attempt 3 (repair turn 2): `action="", capability_id="", has_final_answer=false`

The model is producing parseable JSON but with all fields empty. The repair mechanism correctly:
1. Appends the failed candidate as assistant message
2. Sends the `REPAIR` instruction as a new user message
3. Changes the response format constraint

However, Qwen 3.8 consistently "gives up" after the first empty response and produces empty
objects on all subsequent repair turns as well.

### Root cause assessment

The repair logic in commit `97081ac` is **correctly implemented**. The problem is **model
reliability**: Qwen 3.8 has a ~60% probability of returning empty planner objects for simple
single-step queries like "Покажи DMS-380". This is the same root cause identified in
Assignments 163 and 164 — the model's planner decision reliability is the blocker, not the
loop mechanics, normalization, or repair turn logic.

The successful runs (3/5) show the system works correctly when the model does produce an
executable planner decision.

---

## Phases 3–8

**Not executed.** Per assignment instructions: "If 5/5 does not pass, STOP with
`H1B_PLANNER_DECISION_REPAIR_RED`; do not waste time on later phases."

---

## Conclusion

The planner decision repair mechanism (3 bounded attempts with explicit repair turns) is
functionally correct. The remaining blocker is **Qwen 3.8 model reliability** — the model
returns empty/non-executable planner JSON on ~60% of attempts, and the empty response pattern
persists across all repair turns within a single request. This is consistent with Assignments
163 and 164 findings and is not addressable by the current normalization/repair logic.

Potential next steps (for owner, not QA):
1. Switch to a different model with better instruction-following reliability
2. Add a deterministic fallback: if the query contains a bare task key pattern (e.g., `DMS-380`),
   bypass the planner LLM and directly select `task-lookup-v3`
3. Increase repair turn count (currently 2, max 3 total)
4. Add a "hint" in the repair prompt with the expected capability catalog

## Verdict

**`H1B_PLANNER_DECISION_REPAIR_RED`**