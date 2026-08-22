# Assignment 055 — Test Cleanup Verification and 017 V2 Rerun

**Repository:** `Sovietbear86/PO-Agent-Architecture-Review`  
**Branch:** `feat/core8-real-query-hardening-v2`  
**Execution Date:** 2026-08-22  
**QA Role:** Tester only (no production code modifications)

---

## Executive Summary

**VERDICT: BLOCKED** - Test cleanup verification failed with 3 test failures. The test cleanup committed in 0a7ac739 is incomplete and does not address all production API requirements used by the runtime.

---

## Preflight Evidence

| Item | Value |
|------|-------|
| Branch | `feat/core8-real-query-hardening-v2` |
| HEAD | `74a4ad7e480ae2636546933e28c23f871aef40d5` |
| Clean Tree | ✅ PASS (working tree clean) |
| Service Ports | 8003 (Task API), 8004 (PO Agent) |
| AS21 Mode | `task-api` |
| Semantic Interpreter | Production (not fake) |

### Recent Commits (Since Assignment 054)

```
74a4ad7 docs: point GigaCode to test cleanup and 017 V2 rerun 055
7e40a4d qa: add test cleanup and 017 V2 rerun assignment 055
b38fd8c test: execute extracted task key with existing fake task
dbd98e8 test: update dialogue interpreter on wrapped runtime
0a7ac73 test: use valid task-api mocks for architecture regressions
```

---

## Test Cleanup Commit Evidence

**Commit:** `0a7ac73985a40bd7e4309361b9310e6549ebc8bc`  
**Message:** `test: use valid task-api mocks for architecture regressions`

### What Was Fixed

- Added `task_payload()` helper function for consistent test data
- Updated `test_runtime_factory_runtime_records_production_execution_history` to return task list instead of empty array
- Updated `test_portfolio_overview_never_labels_task_api_data_as_fake` to return task list instead of empty array
- Added special handling for `attachments` case in `test_source_dependent_request_cannot_be_reinterpreted_when_fact_is_missing`

### What Was NOT Fixed

1. **Missing `/api/v1/swtr-read/versions` endpoint mock** - The runtime's `LiveEntityGrounding` requires this endpoint for version information during semantic context construction
2. **Response data format mismatch** - `test_dialogue_executes_with_extracted_task_key` expects `"task_key"` in response data, but actual response contains `"task"` with nested `"key"`

---

## Production Wiring Evidence

The runtime's `LiveEntityGrounding.semantic_context()` method calls:
- `search_versions()` → `/api/v1/swtr-read/versions`
- This is required before any task search or portfolio operations

**Evidence:**
```
po_agent/harness/production_entity_grounding_v2.py:67
  → po_agent/harness/live_entity_grounding.py:75
    → po_agent/adapters/production_task_api.py:157
      → self._client.get("/api/v1/swtr-read/versions", params=params)
```

---

## Targeted Cleanup Retest Output

### Command Executed

```bash
python3 -m pytest \
  tests/test_domain_models.py::TestNormalizeTaskStatus::test_normalize_unknown_status \
  tests/test_final_architecture_regressions.py::test_runtime_factory_runtime_records_production_execution_history \
  tests/test_final_architecture_regressions.py::test_portfolio_overview_never_labels_task_api_data_as_fake \
  tests/test_final_architecture_regressions.py::test_source_dependent_request_cannot_be_reinterpreted_when_fact_is_missing \
  tests/test_harness_dialogue_learning.py::test_conflicting_definition_never_silently_replaces_active_semantics \
  tests/test_harness_dialogue_runtime.py::test_dialogue_executes_with_extracted_task_key \
  -q
```

### Results

```
.FF......F                                                               [100%]
=================================== FAILURES ===================================
3 failed, 7 passed in 7.94s
```

### Failure Details

| Test | Status | Classification | Root Cause |
|------|--------|----------------|------------|
| `test_runtime_factory_runtime_records_production_execution_history` | FAIL | Test/Env | Mock handler raises `AssertionError` for `/api/v1/swtr-read/versions` |
| `test_portfolio_overview_never_labels_task_api_data_as_fake` | FAIL | Test/Env | Mock handler raises `AssertionError` for `/api/v1/swtr-read/versions` |
| `test_dialogue_executes_with_extracted_task_key` | FAIL | Test | Response contains `task.key` but test expects `task_key` at top level |

### Failure Analysis

**Test/Env Classifications:**

1. **`test_runtime_factory_runtime_records_production_execution_history`**
   - **Error:** `AssertionError: unexpected request: GET http://task-api/api/v1/swtr-read/versions?limit=100`
   - **Cause:** The mock transport handler only accepts `/api/v1/tasks`, but production runtime requires `/api/v1/swtr-read/versions` to build semantic context
   - **Classification:** Test infrastructure missing production endpoint mock

2. **`test_portfolio_overview_never_labels_task_api_data_as_fake`**
   - **Error:** `AssertionError: unexpected request: GET http://task-api/api/v1/swtr-read/versions?limit=100`
   - **Cause:** Same as above - missing versions endpoint in mock
   - **Classification:** Test infrastructure missing production endpoint mock

3. **`test_dialogue_executes_with_extracted_task_key`**
   - **Error:** `AssertionError: assert 'task_key' in response.data`
   - **Actual Response Data:**
     ```python
     {
       'task': {
         'key': 'WMB-101',
         'id': 'task-001',
         'title': 'Implement user authentication',
         'description': 'Add OAuth2 support...',
         'assignee': 'Ivanov.I.I',
         'status': 'In progress'
       },
       'session_id': 'extract',
       'trace_id': 'd4646ed8-5f2f-4874-9bdc-b6f4b9a2bfa6',
       'status': 'COMPLETED',
       'feedback_prompt': 'Ответ помог? Что бы вы хотели улучшить?',
       'dialogue_state': 'answered',
       'llm_used': True
     }
     ```
   - **Cause:** Test assertion expects `task_key` at top level, but response structure uses nested `task.key`
   - **Classification:** Test assertion mismatch with production response schema

---

## Oracle Smoke Guard

**Status:** SKIPPED  
**Reason:** Targeted cleanup did not pass (`055_TARGETED_CLEANUP_PASS ≠ YES`)

Oracle smoke testing was not executed because the targeted cleanup tests failed. Running oracle smoke with broken tests would not provide valid evidence.

---

## Full 017 V2 Rerun

**Status:** SKIPPED  
**Reason:** Targeted cleanup did not pass

Full 017 V2 matrix execution was not performed because the targeted cleanup tests failed. Running full matrix with broken tests would not provide valid evidence.

---

## Failure Classifications Summary

| Category | Count |
|----------|-------|
| Test/Env Issues | 3 |
| Production Code Issues | 0 |
| Configuration Issues | 0 |
| Credential/Connection Issues | 0 |
| Source Data Issues | 0 |

**Total Failures:** 3

---

## Required Footer

```text
ASSIGNMENT_ID = CORE8_TEST_CLEANUP_AND_017V2_RERUN_055
START_HEAD = 74a4ad7e480ae2636546933e28c23f871aef40d5
REPORT_COMMIT = PENDING
CLEAN_TREE_GUARD = PASS
PRODUCTION_CODE_MODIFIED_BY_QA = NO
055_TARGETED_CLEANUP_PASS = NO
055_ORACLE_SMOKE_PASS = BLOCKED
017V2_FULLY_EXECUTED = NO
ORACLE_PREFLIGHT_PASS = BLOCKED
ORACLE_INDEPENDENCE_PASS = BLOCKED
FUNCTIONAL_TOTAL = 0
FUNCTIONAL_PASS = 0
FUNCTIONAL_FAIL = 0
CORRECTION_LOOP_PASS = 0/15
TARGETED_CLARIFICATION_PASS = BLOCKED
SESSION_CONTEXT_RETENTION_PASS = BLOCKED
NEGATIVE_FEEDBACK_TRACE_PASS = BLOCKED
FALSE_GREEN_COUNT = 0
SILENT_SLOT_DROP_COUNT = 0
QUERY_HTTP_500_COUNT = 0
NEW_HIGH_PRODUCTION_REGRESSIONS = 0
READY_TO_RESUME_GATE_E = NO
READY_FOR_FRONTEND_FINALIZATION = NO
055_VERDICT = BLOCKED
```

---

## QA Notes

### Why This is BLOCKED

The test cleanup commit (`0a7ac739`) addressed only part of the required mock infrastructure. The production runtime requires:

1. `/api/v1/tasks` - for task listing (fixed in commit)
2. `/api/v1/swtr-read/versions` - for version info (NOT fixed in commit)

Without the versions endpoint mock, any runtime test using `task-api` mode will fail during semantic context construction.

### What Developer Must Fix

1. **Update mock handlers** to include `/api/v1/swtr-read/versions` endpoint returning valid version data
2. **Update test assertion** in `test_dialogue_executes_with_extracted_task_key` to check `response.data["task"]["key"]` instead of `response.data["task_key"]`

### Next Assignment Recommendation

After test infrastructure is fixed, run Assignment 055 again with:
- Clean test environment
- Valid mock endpoints for all production API calls
- Corrected test assertions matching production response schemas

---

*Report generated by GigaCode QA/tester on 2026-08-22*
