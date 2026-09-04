# Agent Core v3 H1A Capability Registry — Assignment 158

**Date:** 2026-09-04
**Branch:** `feat/core8-real-query-hardening-v2`
**HEAD:** `38f8ca5199b3e578d1244441b662c5b4dc769723`
**Status:** `H1A_RUNTIME_REGRESSION_RED`

## Mission Summary

Certify H1A of the Hermes re-architecture: Agent Core v3 now uses a reusable self-registering Capability Registry instead of the pilot-local hard-coded capability table.

**QA Only. Do not modify production/backend/frontend/test source code.**

## Required Owner Commits Verified

| Commit | Purpose | Status |
|--------|---------|--------|
| `4b45864c71a1b02758608a3227fc39ad9e4f5a6f` | New `agent_core_v3_registry.py` with reusable registry/catalog | ✅ Ancestor verified |
| `9798faa350eeb593c30a797169b88526f26ddd59` | H1 task pilot consumes the registry and exposes registry metadata | ✅ Ancestor verified |
| `0b643d7e6bf7a4dcef2b4df939f81f4ea558b8d1` | Registry unit tests | ✅ Ancestor verified |

H0 Browser baseline is already certified by Assignment 157.

## Phase 0 — Provenance/Build ✅

### 1. Pull & HEAD
```
Branch: feat/core8-real-query-hardening-v2
HEAD: 38f8ca5199b3e578d1244441b662c5b4dc769723
Status: UP TO DATE
```

### 2. Owner Commit Ancestry
```
4b45864c71a1b02758608a3227fc39ad9e4f5a6f - is ancestor ✅
9798faa350eeb593c30a797169b88526f26ddd59 - is ancestor ✅
0b643d7e6bf7a4dcef2b4df939f81f4ea558b8d1 - is ancestor ✅
```

### 3. Assignment 157 Report Verified
```
File: po-agent-platform-v2/qa_reports/PLAYWRIGHT_H0_ROUTED_REQUEST_FINAL_157.md
Verdict: PLAYWRIGHT_BROWSER_HARNESS_GREEN_H0_CERTIFIED
```

### 4. Old Hard-Coded Registry Removed

**File:** `po-agent-platform-v2/src/po_agent/harness/agent_core_v3_pilot.py`

**Verification:**
- No `PilotCapabilityRegistryV3` class found
- No hard-coded capability table found
- Pilot now imports and uses `build_h1_task_registry()`

### 5. Build/Import Smoke Gate ✅
```
pytest import check: PASS
```

## Phase 1 — Registry Unit/Contract Gate ✅

### Test Execution
```bash
pytest -q tests/test_agent_core_v3_registry.py tests/test_agent_core_v3_foundation.py -v
```

### Results: 10 passed ✅

### Explicit Evidence

#### Registry Size
```
Registry size = 2 (for current certified task family)
```

#### Intent Resolution
```
task_lookup -> task-lookup-v3 ✅
task_search -> task-search-v3 ✅
```

#### Duplicate Rejection Tests
```
Duplicate capability id rejected ✅
Duplicate intent owner rejected ✅
Unknown intent rejected ✅
```

#### Compact Catalog Properties
```
Stable across repeated reads ✅
Contains no executor_id ✅
Contains no oracle_id ✅
Contains no entity facts (no names, task IDs, counts) ✅
Source authority = REAL_AS21 ✅
```

### Test Evidence Summary

**File:** `po-agent-platform-v2/tests/test_agent_core_v3_registry.py`

| Test | Purpose | Status |
|------|---------|--------|
| `test_h1_registry_contains_only_reusable_task_capabilities` | Registry size=2, intents correct, no entity facts | ✅ PASS |
| `test_registry_rejects_duplicate_capability_id` | Duplicate capability rejected | ✅ PASS |
| `test_registry_rejects_duplicate_intent_owner` | Duplicate intent rejected | ✅ PASS |
| `test_registry_fails_closed_for_unknown_intent` | Unknown intent fails closed | ✅ PASS |
| `test_compact_catalog_is_stable_and_does_not_expose_executor_internals` | Catalog stable, no internals exposed | ✅ PASS |

**File:** `po-agent-platform-v2/tests/test_agent_core_v3_foundation.py`

| Test | Purpose | Status |
|------|---------|--------|
| `test_capability_contract_creation` | Contract creation with all fields | ✅ PASS |
| `test_capability_contract_validation` | Constraint validation | ✅ PASS |
| `test_capability_contract_postconditions` | Postcondition validation | ✅ PASS |
| `test_agent_core_v3_failure_code` | Failure codes defined | ✅ PASS |
| `test_agent_core_v3_source_authority` | Source authority constants | ✅ PASS |

## Phase 2 — Focused Runtime Registry Proof ⚠️

### Runtime Status
```
Backend v3 (8004): HEALTHY
  - agent_core_v3_enabled: False
  - semantic_mode: qwen-llm
  - source_status: degraded
  - source_error: AS21SourceUnavailable
```

### Blocker
The backend `agent_core_v3_enabled: False` means the new registry-based routing is not active.
The `PO_AGENT_AGENT_CORE_V3_ENABLED` environment variable is not set in the runtime `.env` file.

**Owner Action Required:** Set `PO_AGENT_AGENT_CORE_V3_ENABLED=true` in `po-agent-platform-v2/.env` and restart the backend.

### Runtime Registry Evidence (if v3 were enabled)

The registry contract is verified at unit level:
- Registry size = 2
- task-lookup-v3 registered with intent `task_lookup`
- task-search-v3 registered with intent `task_search`
- Compact catalog contains only metadata (no executor_id, oracle_id, or entity facts)

## Phase 3 — Fresh A/B Exact Parity ⚠️

### Blocker
Backend v3 not enabled, so Agent A cannot use the registry-based routing.

**Owner Action Required:** Enable `agent_core_v3_enabled` and restart backend.

### Expected A/B Comparison (once v3 enabled)

| Query | Agent A (Registry) | Oracle B (REAL AS21) | Expected |
|-------|-------------------|---------------------|----------|
| Задачи Гаранина | Registry-routed task_search | Direct MCP task search | Exact key set parity |
| Покажи DMS-380 | Registry-routed task_lookup | Direct MCP read | Exact key set parity |

## Phase 4 — H0 Browser C Protected Regression ❌

### Test Execution
```bash
npm run e2e:h0
```

### Results: 0/5 PASS

### Failure Analysis

All 5 tests failed with the same error:
```
Error: expect(locator).toBeVisible() failed
Locator: getByText(/Agent Core v3/).first()
Expected: visible
Timeout: 30000ms
```

### Root Cause
The frontend expects "Agent Core v3" text to be visible in the UI, which is rendered only when:
1. `agent_core_v3_enabled: True` in backend settings, AND
2. The capability registry is active and routing requests through v3

Since `agent_core_v3_enabled: False`, the UI shows the Legacy Harness instead of Agent Core v3.

### Browser Test Evidence

| Test | Expected | Actual | Reason |
|------|----------|--------|--------|
| session isolation | Agent Core v3 text visible | Legacy Harness shown | v3 not enabled |
| v3 browser pilot: Задачи Гаранина | Agent Core v3 text visible | Legacy Harness shown | v3 not enabled |
| v3 browser pilot: Задачи Гаранина в DMS | Agent Core v3 text visible | Legacy Harness shown | v3 not enabled |
| v3 browser pilot: Задачи Калачанова в WMB | Agent Core v3 text visible | Legacy Harness shown | v3 not enabled |
| v3 browser pilot: Покажи DMS-380 | Agent Core v3 text visible | Legacy Harness shown | v3 not enabled |

### H0 Baseline (Assignment 157)
```
Verdict: PLAYWRIGHT_BROWSER_HARNESS_GREEN_H0_CERTIFIED
All 5 tests passed with H1B architecture
```

## Root Cause Summary

### Issue: Backend v3 Not Enabled

**Symptom:** All H0 browser tests fail because "Agent Core v3" text not visible.

**Root Cause:** 
1. Backend `agent_core_v3_enabled` setting is `False`
2. `PO_AGENT_AGENT_CORE_V3_ENABLED` environment variable not set in `.env`
3. Registry-based routing not active in runtime

**Assignment 158 Contribution:**
- ✅ Registry contract verified at unit level
- ✅ All 10 registry tests pass
- ❌ Cannot verify runtime behavior without v3 enabled
- ❌ Cannot verify H0 browser tests without v3 enabled

### Architectural Verification

The new `agent_core_v3_registry.py` is correctly implemented:
1. Single reusable registry abstraction (no hard-coded tables)
2. Intent ownership is unique and duplicate registration fails closed
3. Unknown intents fail closed
4. Registry metadata contains NO entity facts
5. Compact catalog is deterministic and contains discovery metadata only
6. Current task pilot resolves `task_lookup` and `task_search` through registry
7. Source authority remains REAL_AS21

## Verdict

**H1A_RUNTIME_REGRESSION_RED**

### What Works

```
✅ Registry contract implementation verified at unit level
✅ Registry size = 2 for certified task family
✅ task_lookup -> task-lookup-v3 resolves correctly
✅ task_search -> task-search-v3 resolves correctly
✅ Duplicate capability id rejected (test verified)
✅ Duplicate intent owner rejected (test verified)
✅ Unknown intent fails closed (test verified)
✅ Compact catalog stable across repeated reads
✅ Compact catalog contains no executor_id/oracle_id
✅ Compact catalog contains no entity facts (names, task IDs, counts)
✅ All 10 registry unit tests PASS
✅ Old hard-coded PilotCapabilityRegistryV3 removed from pilot
✅ Source authority remains REAL_AS21 in registry
```

### What Fails

```
❌ Backend v3 not enabled (agent_core_v3_enabled: False)
❌ H0 browser tests fail (Agent Core v3 text not visible)
❌ Cannot verify runtime registry proof without v3 enabled
❌ Cannot verify A/B parity without v3 enabled
❌ Cannot verify H0 browser regression without v3 enabled
```

### Required Owner Action

**Enable Agent Core v3:**

1. Edit `po-agent-platform-v2/.env`:
```bash
PO_AGENT_AGENT_CORE_V3_ENABLED=true
```

2. Restart the backend:
```bash
pkill -f "uvicorn po_agent.main"
# Or use your preferred restart mechanism
```

3. Verify backend health:
```bash
curl http://127.0.0.1:8004/health
# Expect: agent_core_v3_enabled: true
```

4. Re-run Assignment 158 to complete runtime and browser verification

### Next Steps

After owner enables v3:

1. Run Phase 2: Focused runtime registry proof (2 pilot queries)
2. Run Phase 3: Fresh A/B exact parity
3. Run Phase 4: H0 Browser C protected regression
4. If all PASS: `AGENT_CORE_V3_H1A_REGISTRY_GREEN`
5. If H0 tests fail due to v3 version change: Report exact mismatch, do NOT edit tests

## Files Generated

**Assignment 158:**
- `po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1A_CAPABILITY_REGISTRY_158.md` - This report

**No production code changes by QA.**

---

**QA Role:** QA/tester only

### Registry Contract Verification
✅ Agent Core v3 capability registry contract implemented correctly
✅ No hard-coded capability tables in pilot
✅ Registry is self-registering and reusable
✅ Intent ownership unique, duplicates rejected
✅ Unknown intents fail closed
✅ Compact catalog contains only metadata
✅ Source authority = REAL_AS21

### Runtime Verification
❌ Backend v3 not enabled - cannot verify runtime behavior
❌ H0 browser tests fail because v3 not active

### Browser Verification
❌ All 5 H0 tests fail (Agent Core v3 text not visible)
❌ H0 baseline from Assignment 157 confirmed GREEN

### Recommendation
**BLOCKED:** Backend v3 needs to be enabled via `PO_AGENT_AGENT_CORE_V3_ENABLED=true` environment variable.

Once enabled, re-run Assignment 158 to complete runtime and browser verification.
