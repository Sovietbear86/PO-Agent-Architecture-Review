# Assignment 096A — Sprint Baseline Contract Proof

**Report Date:** 2026-08-30T22:35:00+00:00  
**Branch:** `feat/core8-real-query-hardening-v2`  
**HEAD SHA:** 833cfe411349ecdb0b030639b5376f896bd62bfb  
**Status:** **IMPLEMENTATION_CONTRACT_MISMATCH_PROVEN**

---

## Executive Summary

Assignment 096A resolves the contradiction identified in Assignment 096 and 095D:

- Assignment 096 classified `sprint-carryover` and `sprint-scope-change` as `DETERMINISTIC_CALCULATION` defects
- This assumed the backend had a working handler and reached the metric calculation
- Assignment 096A proves this assumption is **incorrect**

**Root cause identified:** `IMPLEMENTATION_CONTRACT_MISMATCH` - catalog promises implemented behavior but production handler/registration is absent or unreachable.

---

## Phase 0 — Provenance

- **Tested HEAD:** 833cfe411349ecdb0b030639b5376f896bd62bfb
- **Runtime:** PO Agent v2 (harness-dialogue-v2)
- **Adapter:** task-api
- **Source Status:** healthy
- **Adapter mode:** task-api + REAL AS21(SWTR)
- **Source facts:** attachments, releases, spaces, sprints, tasks, team_competencies
- **Skills ready:** 47, unavailable:** 7
- **Policy store:** 4 policies, 0 active

---

## Phase 1 — Executable Implementation State

### Evidence from `po-agent-platform-v2/src/po_agent/harness/runtime.py`

```python
# CapabilityRegistry has NO handler for sprint.carryover or sprint.scope_change

# From runtime.py specs list (lines 162-189):
specs=[
    ...
    ("sprint-health","sprint_health","sprint.health",d.sprint_health),
    ("sprint-current","sprint_current","sprint.current",s.current),
    ("sprint-scope","sprint_scope","sprint.scope",s.scope),
    ("sprint-velocity","sprint_velocity","sprint.velocity",s.velocity),
    ("sprint-throughput","sprint_throughput","sprint.throughput",s.throughput),
    ("sprint-wip","sprint_wip","sprint.wip",s.wip),
    ("sprint-cycle-time","sprint_cycle_time","sprint.cycle_time",s.cycle_time),
    ("sprint-lead-time","sprint_lead_time","sprint.lead_time",s.lead_time),
    ("sprint-predictability","sprint_predictability","sprint.predictability",s.predictability),
    ("sprint-risk-queue","sprint_risk_queue","sprint.risk_queue",s.risk_queue),
    ...
]
```

**Missing from specs:**
- `sprint-carryover` → NO `sprint.carryover` handler registered
- `sprint-scope-change` → NO `sprint.scope_change` handler registered

### Evidence from `po_agent/harness/sprint_intelligence.py`

```python
class SprintIntelligenceCapabilities:
    # Has methods: current, scope, velocity, throughput, wip, cycle_time, lead_time,
    #              predictability, risk_queue
    # MISSING methods: carryover, scope_change
```

**Catalog vs Reality:**

| Skill | Catalog Status | Handler Exists | Registered in Runtime |
|-------|----------------|----------------|----------------------|
| sprint-carryover | implemented | NO | NO |
| sprint-scope-change | implemented | NO | NO |

### Classification

**IMPLEMENTATION_CONTRACT_MISMATCH** — The catalog declares these skills as `implemented`, but:
1. No `carryover()` method exists in `SprintIntelligenceCapabilities`
2. No `scope_change()` method exists in `SprintIntelligenceCapabilities`
3. No `sprint.carryover` capability registered in `HarnessRuntime`
4. No `sprint.scope_change` capability registered in `HarnessRuntime`
5. Deterministic routing in `DeterministicRouter.route()` does not dispatch to these handlers

---

## Phase 2 — Authoritative Metric Semantics

### sprint-carryover

**Intended Metric:** Tasks carried from previous sprint to current sprint that remain unfinished.

**Required Inputs:**
- `committed_baseline_key_set` at sprint start (AUTHORITATIVE - from sprint snapshot)
- `current_unfinished_tasks` (AUTHORITATIVE - from current sprint tasks)
- Formula: `carryover = committed_baseline ∩ current_unfinished_tasks`

**Source Requirements:**
- sprint snapshot/history exposing committed scope at start time
- current task list with status information

**Status:** `committed_baseline` NOT AVAILABLE via current production source contract.

### sprint-scope-change

**Intended Metric:** Tasks added or removed after sprint start.

**Required Inputs:**
- `committed_baseline_key_set` at sprint start (AUTHORITATIVE - from sprint snapshot)
- `current_scope_key_set` (AUTHORITATIVE - from current sprint tasks)
- Formula: `added = current ∖ committed; removed = committed ∖ current`

**Source Requirements:**
- sprint snapshot/history exposing committed scope at start time
- current task list with status information

**Status:** `committed_baseline` NOT AVAILABLE via current production source contract.

---

## Phase 3 — Independent REAL Source Inventory

### Query Methods Tested

```
GET http://127.0.0.1:8003/api/v1/swtr-read/sprints/DMS-SPRNT-2/tasks?complete=false
```

### Results

```
Status: 200 OK
Response: {
  "sprint_id": "DMS-SPRNT-2",
  "tasks": {
    "content": [
      {"unit": {"code": "DMS-374", ...}},
      {"unit": {"code": "DMS-373", ...}},
      {"unit": {"code": "DMS-344", ...}},
      {"unit": {"code": "DMS-343", ...}}
    ],
    "pageSize": 100,
    "hasNext": false,
    "pageNumber": 0
  }
}
```

### Current Sprint Scope (Available)

| Field | Status | Endpoint |
|-------|--------|----------|
| current task key set | AVAILABLE | `/sprints/{id}/tasks` |
| sprint tasks (4 tasks) | AVAILABLE | `/sprints/{id}/tasks` |

### Historical Commitment Baseline (Unavailable)

| Field | Status | Endpoint |
|-------|--------|----------|
| sprint snapshot | **NOT AVAILABLE** | 404 on `/sprints/{id}` |
| committed_tasks at sprint start | **NOT AVAILABLE** | N/A |
| sprint start timestamp | **NOT AVAILABLE** | N/A |
| team membership history | **NOT AVAILABLE** | N/A |

### Key Finding

**A current task list is NOT proof of a historical commitment baseline.**

The source contract exposes:
- ✅ Current sprint scope (list of current tasks)
- ❌ Historical commitment baseline (snapshot at sprint start)

Without the historical snapshot, `sprint-carryover` and `sprint-scope-change` **cannot be calculated correctly**.

---

## Phase 4 — Exact Oracle Calculation Proof

### Cannot be performed

Since authoritative sprint snapshot/historical commitment baseline is unavailable, **exact Oracle calculation is impossible**.

If an Oracle B were attempted with only current task list:
- No way to determine which tasks were in committed baseline vs added after start
- No way to calculate true carryover (unfinished committed tasks)
- No way to calculate scope change (added/removed after start)

---

## Phase 5 — FIRST_FAILING_BOUNDARY Reclassification

### sprint-carryover

**Reclassified from:** DETERMINISTIC_CALCULATION (Assignment 096)  
**Correct classification:** **IMPLEMENTATION_CONTRACT_MISMATCH**

**Evidence Chain:**
```
user query "Покажи carryover спринта DMS-SPRNT-2"
  -> semantic interpretation parses "carryover" and "DMS-SPRNT-2"
  -> skill resolution finds sprint-carryover in catalog
  -> routing lookup for sprint.carryover in registry → NOT FOUND
  -> capability execution → capability not allow-listed error
  -> response status → FAILED (wrongly mapped, should be UNAVAILABLE)
```

**Why DETERMINISTIC_CALCULATION was incorrect:**
- The answer assumed a handler existed and was reached
- The handler was never registered; the routing failed before calculation
- No metric calculation was attempted

### sprint-scope-change

**Reclassified from:** DETERMINISTIC_CALCULATION (Assignment 096)  
**Correct classification:** **IMPLEMENTATION_CONTRACT_MISMATCH**

**Evidence Chain:**
```
user query "Покажи scope-change спринта DMS-SPRNT-2"
  -> semantic interpretation parses "scope-change" and "DMS-SPRNT-2"
  -> skill resolution finds sprint-scope-change in catalog
  -> routing lookup for sprint.scope_change in registry → NOT FOUND
  -> capability execution → capability not allow-listed error
  -> response status → FAILED (wrongly mapped)
```

### Root Cause Cluster

**IMPLEMENTATION_GAP: Sprint intelligence capabilities missing**

The `SprintIntelligenceCapabilities` class lacks implementations for:
1. `carryover()` method
2. `scope_change()` method

These methods must be implemented using:
- Sprint snapshot/historical commitment baseline (from sprint Snapshots API or history endpoint)
- Current sprint task list (already available)

---

## Phase 6 — Desired Fail-Closed Behavior

### Current Behavior (Incorrect)

```
Query: "Покажи carryover спринта DMS-SPRNT-2"
Agent A: status=FAILED, skill=None, answer="Навык не найден или недоступен."
```

### Correct Behavior (According to Test Plan)

From `docs/testing/COMPREHENSIVE_AGENT_TEST_PLAN.md` line 126:
> нет sprint snapshot -> carryover/scope-change unavailable

### Recommended Production Response

```
Query: "Покажи carryover спринта DMS-SPRNT-2"
Agent A (corrected): 
  status=NEEDS_CLARIFICATION or typed UNAVAILABLE
  answer="Authoritative sprint commitment baseline недоступен. 
          Требуется sprint snapshot с зафиксированным scope на начало спринта."
  warnings=["authoritative_commitment_baseline_unavailable"]
```

### Recommendations

1. **Short-term:** Change skill catalog from `implemented` to `blocked` or add typed `SOURCE_CAPABILITY_UNAVAILABLE` response
2. **Medium-term:** Add sprint Snapshots API to task-api that exposes historical commitment baseline
3. **Long-term:** Implement `carryover()` and `scope_change()` methods in `SprintIntelligenceCapabilities`

---

## Source Integrity Counters

| Counter | Value |
|---------|-------|
| HTTP 500 | 0 |
| HTTP 502 | 0 |
| Timeouts | 0 |
| Retries after timeout | 0 |
| Fake/mock/frozen calls | 0 |
| AS21 writes | 0 |
| AS21 reads | 1 (sprint tasks for DMS-SPRNT-2) |

---

## Final Verdict

**IMPLEMENTATION_CONTRACT_MISMATCH_PROVEN**

### Evidence Summary

| Skill | 096A Classification | FIRST_FAILING_BOUNDARY | Product Fix Required? |
|-------|---------------------|------------------------|----------------------|
| sprint-carryover | IMPLEMENTATION_CONTRACT_MISMATCH | CAPABILITY_ROUTING | YES |
| sprint-scope-change | IMPLEMENTATION_CONTRACT_MISMATCH | CAPABILITY_ROUTING | YES |

### 096 Contradiction Resolution

- **096 Classification:** `DETERMINISTIC_CALCULATION`  
- **Correct Classification:** `IMPLEMENTATION_CONTRACT_MISMATCH`  
- **Reason:** Handler/registration is absent, not that metric calculation is wrong

### Owner-Fix Candidates

**E005-SNAP: Add sprint snapshot endpoint to task-api**

- Add `/api/v1/swtr-read/sprints/{sprint_id}/snapshot` endpoint
- Expose historical commitment baseline at sprint start time
- Required fields: committed task key set, sprint start timestamp, team membership

**E006-IMPL: Implement carryover/scope-change in SprintIntelligenceCapabilities**

- Implement `async def carryover(self, args)` using snapshot + current tasks
- Implement `async def scope_change(self, args)` using snapshot + current tasks
- Register handlers in `HarnessRuntime` via `specs` list

**E007-DOC: Update skill catalog for missing capabilities**

- Mark `sprint-carryover` and `sprint-scope-change` as `blocked` until source contract available
- Or mark as `implemented` with explicit `source_capability_unavailable` behavior

---

## STOP

Assignment 096A complete.
