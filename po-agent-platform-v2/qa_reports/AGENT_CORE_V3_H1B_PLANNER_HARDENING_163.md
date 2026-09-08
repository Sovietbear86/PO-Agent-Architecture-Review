# Assignment 163 — H1B Planner Hardening Retest

**Verdict: `H1B_PLANNER_RELIABILITY_RED`**

**Date:** 2026-09-08  
**HEAD:** `399ba65a2ed0241eb68d21e0196b9e9381cbb43a`  
**Branch:** `feat/core8-real-query-hardening-v2`  
**QA Role:** Tester only — no production code modified

---

## Executive Summary

The loop-first H1B processor correctly routes all v3 requests through the bounded planner. Server logs prove 2 source-backed capability executions (DMS-380 lookup → assignee search) with observation propagation working mechanically. However, the LLM planner's **re-plan call after any observation consistently returns `action: ""`** (empty string) instead of `"final"`, causing every query to fail with `UNSUPPORTED_CONSTRAINT`. The new robust JSON extraction and strict structured-output schema did not fix the underlying model reliability issue. Additionally, the loop-first path bypasses semantic grounding, causing person names to be sent to the source as raw constraints (HTTP 409).

**Impact:** ALL v3 queries fail. Playwright H0 regression: 1/5 (was 5/5 pre-H1B).

---

## Phase 0 — Provenance & Preflight ✅

| Check | Result |
|-------|--------|
| HEAD | `399ba65a2ed0241eb68d21e0196b9e9381cbb43a` |
| Commit `de77bb1` (robust JSON + strict schema) | ✅ ancestor |
| Commit `95b1da5` (loop-first processor) | ✅ ancestor |
| Commit `5f8a2d3` (production runtime wiring) | ✅ ancestor |
| Commit `09453e8` (regression tests) | ✅ ancestor |
| PO Agent `/health` | ✅ v3=true, qwen-llm, source=healthy |
| Task API | ✅ connected, 48 tools |
| Frontend (port 5175) | ✅ HTTP 200 |

---

## Phase 1 — Unit/Static Gate ✅

**Tests:** `17 passed in 0.33s`

**Static audit:**

| Rule | Status | Evidence |
|------|--------|----------|
| Production uses `AgentCoreV3H1BProcessor` | ✅ | `runtime_factory.py` line: `processor=AgentCoreV3H1BProcessor(...)` |
| Loop-first: no single-shot before planner | ✅ | `AgentCoreV3H1BProcessor.process()` calls `_run_agent_loop` directly |
| Robust JSON extraction | ✅ | `_extract_json_object` handles `think`, markdown, embedded JSON |
| Strict structured output schema | ✅ | `_response_schema()` with `json_schema` type + 3 fallback attempts |
| Capability registry from H1A | ✅ | `registry.compact_catalog(family="tasks")` |
| `$obs` resolution intact | ✅ | `resolve_observation_reference` unchanged |
| max_steps=4 | ✅ | Constructor enforces `max(2, int(max_steps))` |
| Duplicate blocking | ✅ | `seen_calls` set in `_run_agent_loop` |

---

## Phase 2 — Multi-step Challenge A

**Query:** `Проверь DMS-380 и затем покажи задачи его исполнителя`

### Oracle B

| Step | Source | Result |
|------|--------|--------|
| 1 | `GET /api/v1/swtr-read/tasks/DMS-380` | Assignee: `semavin.m.m` (Semavin.M.M) |
| 2 | `GET /api/v1/swtr-read/assignee-tasks?assignee=semavin.m.m&space=DMS` | **136 tasks**, REAL_AS21 |

### Agent A (3 attempts, all identical failure pattern)

**Status: FAILED** — `failure_code: UNSUPPORTED_CONSTRAINT`, `details: {"action": ""}`

**Server log proof (attempt 3, 09:40:07):**
```
09:39:56 POST chat/completions (planner step 1) → 200 OK
09:39:58 GET DMS-380/files (step 1: task-lookup executed)
09:40:07 POST chat/completions (planner step 2) → 200 OK
09:40:09 GET assignee-tasks?assignee=semavin.m.m (step 2: task-search executed)
09:40:24 POST chat/completions (planner step 3: should be "final") → 200 OK
09:40:24 Request completed → FAILED (action="")
```

### Analysis

| Requirement | Status |
|-------------|--------|
| Loop executes ≥2 capabilities | ✅ (2 source reads in logs) |
| Observation propagation (assignee from step 1) | ✅ (`assignee=semavin.m.m` in step 2 URL) |
| REAL AS21 authoritative | ✅ |
| Planner re-plan/final completes | ❌ `action: ""` |
| Status = COMPLETED | ❌ FAILED |
| Oracle parity | ❌ Cannot assess (Agent A not COMPLETED) |

### Root Cause

The Qwen 3.8 model consistently returns `{"action": "", ...}` for the re-plan call after 2 observations. The strict JSON schema (`json_schema` with `strict: true`) does not appear to be enforced by the model endpoint — the model returns valid JSON that parses successfully but with an empty `action` field. This is a **model-level structured output reliability issue** that cannot be fixed by parser improvements alone.

**Planner call count per query:** 3 LLM calls (step 1, step 2, step 3-fail)  
**Total latency:** ~34s per attempt

---

## Phase 3 — Loop-first Challenge B

**Query:** `Найди задачи Гаранина в DMS и затем покажи подробности DMS-380`

**Status: FAILED** — unhandled `AS21SourceUnavailable` (HTTP 409)

**Server log:**
```
POST assignee-tasks?assignee=%D0%93%D0%B0%D1%80%D0%B0%D0%BD%D0%B8%D0%BD (assignee=Гаранин)
→ HTTP 409 Conflict
```

### Root Cause

The loop-first processor **bypasses semantic grounding**. In the old H1A path, the semantic interpreter + grounder resolved "Гаранин" → login "Garanin.R.V" before execution. In the new loop-first path, the planner receives raw user text and proposes `assignee: "Гаранин"` as a literal constraint (passes `_literal_is_source_safe` because "Гаранин" IS in the query). The source expects a login, not a person name.

This is a **missing grounding step** in the loop-first architecture.

Additionally, the unhandled exception (409 → `AS21SourceUnavailable`) is not caught in `_run_agent_loop`, resulting in a generic 500-style error rather than a typed failure response.

---

## Phase 4 — Silent Truncation

**Query:** `Проверь DMS-380 и затем покажи историю его статусов`

**Result:** FAILED with `UNSUPPORTED_CONSTRAINT`, `details: {"action": ""}`

**Assessment:** The silent truncation check technically PASSES (not COMPLETED), but for the **wrong reason** — the planner is broken, not because the system correctly identified that status-history is unsupported. The planner fails before it can even attempt the second operation.

**Verdict: Cannot prove silent-truncation safety in a meaningful way** — the planner never reaches the point where it would decide to skip or fail on the unsupported capability.

---

## Phase 5 — Single-step Regression through Loop-first

| Query | Status | Failure |
|-------|--------|---------|
| `Задачи Гаранина` | FAILED | Planner re-plan: `action: ""` |
| `Покажи DMS-380` | FAILED | Planner re-plan: `action: ""` |

Both single-step queries also fail because the loop-first processor routes them through the planner, and the planner cannot produce a valid "final" action after the first observation.

**Impact: Complete regression of all v3 single-step functionality.**

---

## Phase 6 — Playwright H0 Regression

**Result: 1/5 PASS, 4/5 FAIL**

| Test | Result |
|------|--------|
| H0 workspace basic | ✅ PASS |
| v3 browser pilot: Задачи Гаранина | ❌ FAIL |
| v3 browser pilot: Задачи Гаранина в DMS | ❌ FAIL |
| v3 browser pilot: Задачи Калачанова в WMB | ❌ FAIL |
| v3 browser pilot: Покажи DMS-380 | ❌ FAIL |

All 4 v3 browser pilot tests fail with the same planner `action: ""` error visible in the browser console.

---

## Phase 7 — Browser C Multi-step

**Cannot be evaluated** — the backend planner is broken for all queries, so no multi-step proof is possible. The Playwright failures already demonstrate this.

---

## Summary of Defects

| # | Defect | Severity | Location |
|---|--------|----------|----------|
| 1 | Planner re-plan returns `action: ""` after any observation | **CRITICAL** | `AgentLoopPlannerV3.next_action` + Qwen 3.8 model |
| 2 | Loop-first path bypasses semantic grounding (name→login) | **HIGH** | `AgentCoreV3H1BProcessor.process` → `_run_agent_loop` (no grounding step) |
| 3 | Unhandled `AS21SourceUnavailable` in `_run_agent_loop` (409 not caught) | **MEDIUM** | `agent_core_v3_pilot.py:317` |

### Why the fix didn't work

The commit `de77bb1` improved JSON **extraction** (handling think tags, markdown, embedded objects) and added a strict **schema** declaration. However:
- The model IS returning valid JSON — the extraction works
- The model IS following the schema shape — but with `"action": ""`
- The issue is that Qwen 3.8 does not reliably produce `"action": "final"` in its structured output. The schema constraint appears to not be enforced at the inference level.

### Suggested fix direction

1. Add a **grounding pre-pass** in `AgentCoreV3H1BProcessor.process()` before the loop starts (resolve person names → logins using the grounder)
2. Handle the "final" case more robustly: if the planner returns a non-call action with observations available, treat it as an implicit final and compose the answer from observations
3. Add `AS21SourceUnavailable` handling in `_run_agent_loop`
4. Consider: if `step_budget_remaining` reaches the minimum and the planner hasn't finalized, auto-compose a final from the last observation

---

## Environment Notes

- PO Agent: restarted with code at `399ba65`
- PO_AGENT_AGENT_CORE_V3_ENABLED=true, PO_AGENT_QA_FAULT_INJECTION=0
- LLM: Qwen/Qwen3.8-27B via `https://api.ai.sbt/openai/v1`
- Frontend: Vite on port 5175, proxying `/api` to 8004
- Task API: SSE transport, 48 tools, healthy

---

## Files Not Modified

No production, backend, frontend, or test code was modified. Only this QA report was created.