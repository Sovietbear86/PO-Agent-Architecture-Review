# QA 026 v4 — Targeted Retest Report

**Date:** 2026-08-24  
**Target commit:** 44c0bb108588a5075d96124bef582ae63b5c6ea3  
**Branch:** feat/core8-real-query-hardening-v2  
**QA role:** Tester only - NO production code modifications

---

## Executive Summary

**Production commit 44c0bb1** modified `semantic_core_v2.py` to update the semantic constraint extraction contract, but **did not fix** the underlying issue: LLM Semantic Interpreter is not extracting person_raw, status_raw, and product filters correctly.

### Root Cause

**LLM Semantic Interpreter bug:** The interpreter returns the **entire user query** in `sprint_raw` and `status_raw` instead of just the identifiers:

```
Query: "Покажи задачи со статусом todo"
Expected: {"status_raw": "todo"}
Actual:   {"status_raw": "Покажи задачи в DMS SPRNT-2", "sprint_raw": "Покажи задачи со статусом todo SPRNT-2"}
```

This is a **semantic interpretation bug** in the production code, not a test issue.

---

## Test Results Summary

| Category | Pass | Fail | Total |
|----------|------|------|-------|
| PERSON_CLUSTER (12 cases) | 0 | 12 | 12 |
| STATUS_CLUSTER (4 cases) | 0 | 4 | 4 |
| PRODUCT_CLUSTER (3 cases) | 0 | 3 | 3 |
| **TOTAL** | **0** | **19** | **19** |
| SOURCE_ORACLE | FAIL | - | 2/2 |
| NEW_REGRESSIONS | 0 | - | - |
| **READY_FOR_FULL_QA026** | **NO** | - | - |

---

## Detailed Findings

### PRODUCTION BUG #1: Semantic Frame Contains Full Query

**Component:** `po-agent-platform-v2/src/po_agent/harness/semantic_core_v2.py`

**Evidence:**

```
Query: "Покажи задачи со статусом todo"
Response semantic_frame:
{
  "sprint_raw": "Покажи задачи со статусом todo SPRNT-2",
  "status_raw": "Покажи задачи в DMS SPRNT-2",
  "task_key": "SPRNT-2"
}
```

**Expected:** `{"status_raw": "todo"}`
**Actual:** Full query in fields meant for identifiers

**Impact:** ALL 19 PRODUCT_FAIL cases fail because filters are not extracted.

---

### PRODUCTION BUG #2: Person Raw Not Extracted

**Component:** `po-agent-platform-v2/src/po_agent/harness/semantic_core_v2.py`

**Evidence:**

```
Query: "Покажи задачи Гаранина"
Response semantic_frame: {}
```

**Expected:** `{"person_raw": "Гаранина"}`
**Actual:** Empty `{}`

**Impact:** All queries requiring person extraction (12 cases) fail.

---

### PRODUCTION BUG #3: Semantic Frame Incorrectly Uses `member_login`

**Component:** `po-agent-platform-v2/src/po_agent/harness/semantic_core_v2.py`

**Evidence:**

```
Query: "Покажи задачи Гаранина в DMS-SPRNT-1"
Response:
{
  "intent": "task_search_sprint",
  "semantic_frame": {
    "member_login": "Garanin.R.V",
    "product": "DMS",
    "sprint_id": "DMS-SPRNT-1"
  }
}
```

**Issue:** Uses `member_login` (resolved login) instead of `person_raw` (user's raw reference).
**Issue:** Missing `person_raw` slot entirely.

**Impact:** Semantic interpretation contract violated - `person_raw` should be preserved, not resolved.

---

## Root Cause Classification

| Root Cause | FAIL Count | AFFECTED_TESTS | COMPONENT |
|------------|------------|----------------|-----------|
| Semantic interpreter returns full query in sprint_raw/status_raw | 12 | D1-D6, I1, I3, I4, I5, I6, J1, J5, G1, G2, G4 | semantic_core_v2.py (LLM prompt/implementation) |
| Semantic interpreter does not extract person_raw | 12 | D1-D6, I1, I6, J1, G1, G2, G4 | semantic_core_v2.py (LLM prompt/implementation) |
| Semantic interpreter incorrectly resolves person to member_login | 3 | B1, I2, J2 | semantic_core_v2.py (LLM prompt/implementation) |
| **TOTAL** | **19** | All PRODUCT_FAIL tests | — |

---

## Regression Analysis

**No new regressions detected** - all previously PASS cases continue to work as expected.

---

## Source Oracle Verification

| Oracle Check | Status |
|--------------|--------|
| DMS-SPRNT-1 contains tasks | FAIL (timeout/clarification) |
| DMS-SPRNT-2 contains tasks | FAIL (timeout/clarification) |

**SOURCE_ORACLE: FAIL**

---

## Recommendations

### Immediate Action (Production Fix Required)

**Fix semantic_core_v2.py LLM prompt:**

```python
# Add explicit examples to SYSTEM prompt:
"""
Example 1:
Input: "Покажи задачи Гаранина в DMS-SPRNT-1"
Output: {
  "intent_hint": "task_search",
  "slots": {
    "person_raw": "Гаранина",
    "sprint_raw": "DMS-SPRNT-1"
  }
}

Example 2:
Input: "Покажи задачи со статусом todo"
Output: {
  "intent_hint": "task_search",
  "slots": {
    "status_raw": "todo"
  }
}

Example 3:
Input: "Покажи задачи в DMS"
Output: {
  "intent_hint": "task_search",
  "slots": {
    "product": "DMS"
  }
}
"""
```

### Verification Steps

1. Run full QA 026 test suite after fix
2. Verify all 19 PRODUCT_FAIL cases now PASS
3. Verify no new regressions in PASS cases

---

## Files Modified (QA Only)

| File | Action | Description |
|------|--------|-------------|
| `qa_026_test_runner_v4.py` | Created | Targeted retest runner |
| `qa_reports/CORE8_QA_026_V4_TARGETED_RETEST_RESULTS.json` | Created | Detailed test results |
| `qa_reports/CORE8_QA_026_V3_ROOT_CAUSE_ANALYSIS.md` | Created | Root cause analysis |

---

## Git Status

```
36655dd Merge remote-tracking branch 'origin/feat/core8-real-query-hardening-v2'
44c0bb1 fix(core8): harden semantic constraint extraction contract (PRODUCTION)
eb1ce92 qa: CORE8_QA_026_V3_ROOT_CAUSE_ANALYSIS
7b663fd qa: CORE8_REAL_DATA_SEMANTIC_ARCHITECTURE_ACCEPTANCE_026_V3_COMPLETE
```

**HEAD:** 36655dd (after merge with origin)  
**Production commit:** 44c0bb1 (semantic_core_v2.py changes)

---

## Final Metrics

```
PERSON_CLUSTER: 0/12 PASS
STATUS_CLUSTER: 0/4 PASS  
PRODUCT_CLUSTER: 0/3 PASS
TOTAL_RECOVERED: 0/19
NEW_REGRESSIONS: 0
SOURCE_ORACLE: FAIL
READY_FOR_FULL_QA026: NO
```

---

**QA Report generated by GigaCode Tester**  
**Production code: UNCHANGED**  
**Status: BLOCKED - Semantic interpreter bug in production commit 44c0bb1**
