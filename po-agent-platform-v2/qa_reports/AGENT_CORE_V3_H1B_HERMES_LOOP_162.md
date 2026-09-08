# Assignment 162 — H1B Hermes Agent Loop Certification

**Verdict: `H1B_PLANNER_SELECTION_RED`**

**Date:** 2026-09-07  
**HEAD:** `5ee39708025281c42e35ff308441835c4d86ec9a`  
**Branch:** `feat/core8-real-query-hardening-v2`  
**QA Role:** Tester only — no production code modified

---

## Executive Summary

The H1B bounded agent loop code is present and architecturally sound. Server logs prove the loop executed **2 real capability calls** (task-lookup DMS-380 → task-search assignee-tasks) with **observation propagation** (step 2's assignee `semavin.m.m` derived from step 1's source-backed observation). However, the LLM planner's 3rd call (re-planning after 2 observations) returned invalid JSON, causing `V3_PROCESSOR_UNAVAILABLE` and a FAILED response. The loop never produced a `COMPLETED` status for either multi-step challenge.

Additionally, the single-step path in `AgentCoreV3PilotProcessor.process()` intercepts most compound queries before the loop can engage, because `_requested_fields` classifies any query containing a task key as `task_lookup` regardless of the LLM's semantic intent.

---

## Phase 0 — Provenance & Runtime Preflight ✅

| Check | Result |
|-------|--------|
| HEAD | `5ee39708025281c42e35ff308441835c4d86ec9a` |
| Owner commit `9da9b05` (bounded planner) | ✅ ancestor |
| Owner commit `1c68d05` (multi-step loop) | ✅ ancestor |
| Owner commit `c315c87` (production wiring) | ✅ ancestor |
| Owner commit `50837d8` (safety contract tests) | ✅ ancestor |
| Assignment 161 report exists | ✅ |
| `/health` v3=true | ✅ |
| `/health` semantic_mode=qwen-llm | ✅ |
| `/health` source_status=healthy | ✅ |

---

## Phase 1 — Unit/Safety Gate ✅

**Tests:** `15 passed in 0.65s` (foundation + registry + loop)

**Static audit:**

| Rule | Status | Evidence |
|------|--------|----------|
| Planner catalog from `CapabilityRegistryV3` | ✅ | `registry.compact_catalog(family="tasks")` in `AgentLoopPlannerV3.next_action` |
| No entity facts in planner code | ✅ | System prompt contains no task keys, logins, spaces |
| `$obs.<step>.<path>` resolved deterministically | ✅ | `resolve_observation_reference()` walks observation data tree |
| Literal task keys/spaces source-safe | ✅ | `_literal_is_source_safe()` checks value present in user query |
| Max step bound = 4 | ✅ | `max_steps=4`, enforced by `range(1, max_steps+1)` |
| Duplicate identical calls blocked | ✅ | `seen_calls` set with `(contract.id, sorted_constraints)` key |

---

## Phase 2 — Multi-step Challenge A

**Query:** `Проверь DMS-380 и затем покажи задачи его исполнителя`

### Oracle B (independent REAL AS21 reads)

| Step | Source Call | Result |
|------|------------|--------|
| 1 | `GET /api/v1/swtr-read/tasks/DMS-380` | Assignee: `Semavin.M.M` (login: `semavin.m.m`) |
| 2 | `GET /api/v1/swtr-read/assignee-tasks?assignee=semavin.m.m&space=DMS` | 136 tasks, `source=REAL_AS21`, `pages_read=4` |

**Oracle task-key set (136):** DMS-120, DMS-144, DMS-17, DMS-175, DMS-176, DMS-178, DMS-179, DMS-18, DMS-180 … DMS-380, DMS-388, DMS-44, DMS-47, DMS-51, DMS-66, DMS-74, DMS-75

### Agent A

**Status: FAILED** — `failure_code: V3_PROCESSOR_UNAVAILABLE`

**Server log evidence (proves loop executed 2 steps):**

```
23:40:21 POST chat/completions (planner step 1)
23:40:22 GET /api/v1/swtr-read/tasks/DMS-380/files (step 1 execution: task-lookup)
23:40:32 POST chat/completions (planner step 2)
23:40:43 POST chat/completions (planner step 2 retry/fallback)
23:40:46 GET /api/v1/swtr-read/assignee-tasks?assignee=semavin.m.m&limit=100&max_pages=100 (step 2 execution: task-search)
23:41:24 POST chat/completions (planner step 3 — FAILED to return valid JSON)
23:41:46 POST chat/completions (planner step 3 retry — also failed)
23:41:46 Request completed → FAILED
```

### Analysis

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `architecture_stage == H1B_AGENT_LOOP` | ✅ | Response metadata confirms |
| `loop_step_count >= 2` | ⚠️ | Logs prove 2 steps executed, but trace lost on exception |
| First capability = `task-lookup-v3` DMS-380 | ✅ | Log shows DMS-380 point-read |
| Second capability = `task-search-v3` | ✅ | Log shows assignee-tasks call |
| Second step assignee from observation | ✅ | `assignee=semavin.m.m` matches step 1 source data |
| Status = COMPLETED | ❌ | FAILED due to planner step 3 JSON failure |
| Oracle parity | ❌ | Cannot assess — Agent A did not complete |

### Root Cause

The LLM planner (Qwen 3.8) failed to return valid JSON on the 3rd call (re-planning after 2 observations). The `AgentLoopPlannerV3.next_action` method tries 2 LLM calls (with and without `response_format`), both failed to produce parseable JSON within the timeout window. Total request latency: 201s.

---

## Phase 3 — Multi-step Challenge B

**Query:** `Найди задачи Гаранина в DMS и затем покажи подробности DMS-380`

### Oracle B

| Step | Result |
|------|--------|
| Garanin DMS tasks | 7: DMS-243, DMS-248, DMS-262, DMS-326, DMS-328, DMS-36, DMS-93 |
| DMS-380 point-read | Found, assignee Semavin.M.M |

### Agent A

**First run (old runtime, pre-pull):** FAILED — `UNSUPPORTED_CONSTRAINT` on `task-lookup-v3` with `unsupported: ["assignee", "space"]`. Loop planner was None (old code without H1B wiring).

**Second run (new runtime):** Same `V3_PROCESSOR_UNAVAILABLE` pattern as Phase 2 — the loop engages but the planner's final call fails.

### Analysis

The single-step path classifies this as `task_lookup` (because DMS-380 is present), which then fails with `UNSUPPORTED_CONSTRAINT` because the task-lookup contract doesn't support `assignee`/`space` constraints. This triggers the loop fallback, which then fails on planner reliability.

---

## Phase 4 — Negative Safety

| Case | Query | Result | Assessment |
|------|-------|--------|------------|
| 1: Out-of-registry capability | "Проверь DMS-380 и затем покажи историю его статусов" | COMPLETED (single-step lookup only) | ⚠️ Silent truncation — "история" part ignored |
| 3: No duplicate loop | "Покажи DMS-380" | COMPLETED (single-step, 1 capability) | ✅ No duplicate |
| 4: Bounded steps | (implicit from Phase 2) | Loop max 4 steps enforced | ✅ Code bound confirmed |

**Note:** Cases 2 (unavailable assignee in observation) could not be independently tested because the loop never reached the point where an observation-dependent constraint would be unresolved. The code path exists (`resolve_observation_reference` raises `UNRESOLVED_CONSTRAINT` on missing data).

---

## Phase 5 — Single-Step Regression

| Query | Status | Capability | Result |
|-------|--------|-----------|--------|
| `Задачи Гаранина` | COMPLETED | `task-search-v3` | 16 tasks (7 DMS + 9 OLP) — matches Oracle B for DMS subset |
| `Покажи DMS-380` | COMPLETED | `task-lookup-v3` | DMS-380 found, correct assignee |

**Single-step regression: PASS** — no degradation from H1B code.

### Playwright H0

**Cannot execute.** Frontend (port 5173) not available. `Connection refused`.

Per assignment rules: *"If Browser C cannot be executed due to tooling/environment, verdict cannot be GREEN."*

---

## Phase 6 — Browser C H1B Multi-step Proof

**Cannot execute.** Frontend unavailable (connection refused on 5173). No Playwright Chromium session possible.

---

## Architectural Findings

### What Works

1. **Loop mechanism is real** — Server logs prove 2 sequential capability executions with source-backed observations
2. **Observation propagation works** — Step 2's `assignee=semavin.m.m` was derived from step 1's DMS-380 point-read, not invented
3. **Source authority is REAL_AS21** — All tool calls go through live SWTR endpoints
4. **Single-step path unaffected** — No regression in H0/H1A behavior
5. **Static safety controls present** — Duplicate blocking, source-safe literal check, max_steps bound

### What's Broken

1. **Planner reliability (PRIMARY DEFECT)** — Qwen 3.8 LLM takes 10–40s per call and fails to return valid JSON on the 3rd loop iteration. The 2-attempt retry within `next_action` is insufficient for a model this slow.
2. **Single-step path intercepts compound queries** — `_requested_fields` + intent override in `_semantic_contract` classifies any query with a task key as `task_lookup`, preventing the loop from engaging on the primary intended path. The loop only triggers as a fallback when the single-step contract fails.
3. **Trace loss on exception** — When the loop fails mid-execution, `trace_steps` and `observations` (which DID execute) are lost. The response shows `loop_steps: []` and `observations: []` despite the server having performed real source reads.

### First Failing Boundary

`AgentLoopPlannerV3.next_action()` — the LLM planner call for step 3 (re-planning after 2 observations) returns non-JSON content or times out. Both retry attempts fail.

---

## Verdict Justification

**`H1B_PLANNER_SELECTION_RED`** — The planner is the first and primary failure point. The loop mechanism, observation propagation, and source authority are all proven to work. The LLM planner cannot reliably complete the bounded 4-step cycle within practical time bounds. Additionally, the single-step intent classification bypasses the loop for most compound queries, making the planner's selection mechanism architecturally insufficient.

---

## Environment Notes

- PO Agent restarted to pick up H1B loop code (old process pre-dated the pull)
- `PO_AGENT_QA_FAULT_INJECTION=0` explicitly set (`.env` had fault injection for DMS-271)
- LLM: Qwen/Qwen3.8-27B via `https://api.ai.sbt/openai/v1`
- Task API: healthy, SSE transport, 48 tools
- Frontend: NOT AVAILABLE (port 5173 connection refused)

---

## Files Not Modified

No production, backend, frontend, or test code was modified. Only this QA report was created.