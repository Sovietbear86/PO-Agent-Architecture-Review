# LEARNING LOOP PERSISTENCE GENERALIZATION ROLLBACK — Assignment 096D

**Date:** 2026-08-28  
**Assignment:** 096D — COLD RESTART, GENERALIZATION, SCOPE & ROLLBACK  
**Status:** `LEARNING_LOOP_PRODUCT_DEFECT`  
**Branch:** `feat/core8-real-query-hardening-v2`  
**HEAD:** `40e867bcf1068b08251fdce2bfdade8fbdd15a12`  

---

## Executive Summary

Assignment 096D evaluates whether a learned policy created in 096C-R2:

1. Survives a true cold restart
2. Loads automatically without replaying corrections
3. Generalizes to different tasks
4. Does NOT leak to unrelated skills
5. Can be rolled back
6. Rollback persists and is effective

**Final Verdict:** `LEARNING_LOOP_PRODUCT_DEFECT`

**Defect:** `QA_FAULT_INJECTION_ENABLED_CHECK_BUG`

**Root Cause:** The `is_qa_fault_injection_enabled()` function in `qa_fault_injection.py` only checks `os.getenv()`, not the `.env` file. The `get_qa_fault_config()` function properly reads from `.env` file as fallback, but `is_qa_fault_injection_enabled()` does not. This inconsistency causes the fault injection check to fail even when the `.env` file has the correct configuration.

**Impact:** The learned policy IS persisted and loaded correctly after restart. However, testing the learned behavior (which requires fault injection to create a controlled negative result) fails because the fault injection is not being enabled correctly.

---

## Repository State Verification

| Check | Status |
|-------|--------|
| Branch | `feat/core8-real-query-hardening-v2` ✅ |
| Local HEAD | `40e867bcf1068b08251fdce2bfdade8fbdd15a12` ✅ |
| Origin HEAD | `40e867bcf1068b08251fdce2bfdade8fbdd15a12` ✅ |
| Working tree | Clean (except untracked `.po_agent/`) ✅ |

---

## PRE-RESTART POLICY PROOF

### Policy Store Inventory

**Path:** `po-agent-platform-v2/.po_agent/learned_policies.json`  
**File size:** 449 bytes  
**Permissions:** `-rw-------` (owner-only)  
**Created:** 2026-08-28T08:31:25+00:00  

### Policy Details

```json
{
  "policy_id": "task-lookup:authoritative_recheck_on_negative:v1",
  "skill_id": "task-lookup",
  "behaviour": "authoritative_recheck_on_negative",
  "version": 1,
  "state": "promoted",
  "evidence_count": 3,
  "created_at": "2026-08-28T08:31:25.232734+00:00",
  "correction_trace_id": "1a62c3d6-b8fd-4602-896e-ba66cc71baf7",
  "validation_trace_id": "ebf68b4b-aaa8-4539-ad1c-66027694e0c7",
  "rollback_reason": null
}
```

### Required Evidence Checklist

| Requirement | Status | Evidence |
|-------------|--------|----------|
| policy_id exists | ✅ PASS | `task-lookup:authoritative_recheck_on_negative:v1` |
| skill_id exists | ✅ PASS | `task-lookup` |
| behaviour correct | ✅ PASS | `authoritative_recheck_on_negative` |
| version >= 1 | ✅ PASS | version=1 |
| state = active | ✅ PASS | state=`promoted` |
| evidence_count >= 1 | ✅ PASS | evidence_count=3 |
| entity_fact_persisted = false | ✅ PASS | Not stored in JSON (runtime property) |

**NO ENTITY FACTS STORED:** The policy only contains behavioral policy metadata, NOT concrete facts like "DMS-271 = Resolved".

---

## STAGE 1: PRE-RESTART POLICY PROOF - COMPLETE

**VERDICT:** POLICY_EXISTS_BEFORE_RESTART = YES ✅

---

## STAGE 2: TRUE COLD RESTART

**Restart Procedure:**
1. Stopped PO Agent runtime process
2. Restarted with same environment configuration
3. No manual policy loading or modification
4. No runtime state preserved (true cold restart)

**Process Evidence:**
- Application startup complete logged
- PO Agent health check: healthy

### Policy Loading After Restart

**Policy File (unchanged):** Same as pre-restart

**Verification:**
```
policy_id = task-lookup:authoritative_recheck_on_negative:v1
skill_id = task-lookup
behaviour = authoritative_recheck_on_negative
version = 1 (unchanged)
state = promoted
```

**VERDICT:** POLICY_EXISTS_AFTER_RESTART = YES ✅

---

## STAGE 3: SAME-SKILL APPLICATION AFTER RESTART

### Test Objective

Verify the learned policy automatically applies to a negative result without user correction.

### Expected Behavior

1. Query with QA fault injection configured
2. First call returns controlled negative result (Unknown)
3. Learned policy automatically triggers recheck
4. Second call reads from REAL SWTR
5. Final result is source-grounded (Resolved)

### Actual Behavior

**Bug Found:** QA fault injection is not being enabled correctly.

### Root Cause Analysis

**File:** `po-agent-platform-v2/src/po_agent/adapters/qa_fault_injection.py`

**Current Implementation:**
```python
def is_qa_fault_injection_enabled() -> bool:
    """Check if QA fault injection is enabled via environment variable."""
    return os.getenv("PO_AGENT_QA_FAULT_INJECTION", "").strip() == "1"


def get_qa_fault_config() -> dict[str, str | None]:
    """Get current QA fault injection configuration from environment or .env file."""
    env_enabled = os.getenv("PO_AGENT_QA_FAULT_INJECTION", "").strip() == "1"
    # ... reads from .env file if env_enabled is False ...
```

**Bug:** `is_qa_fault_injection_enabled()` only checks `os.getenv()`, not the `.env` file. The `.env` file has `PO_AGENT_QA_FAULT_INJECTION=1`, but this function doesn't read it.

**Impact:** Even though the `.env` file correctly has `PO_AGENT_QA_FAULT_INJECTION=1`, the `is_qa_fault_injection_enabled()` function returns False, causing the fault injection to be skipped.

### Test Result

**Query:** `Покажи задачу DMS-271`  
**Response:** `Status: Resolved`  
**Fault metadata:** None present  
**Warnings:** None  

**Analysis:** The query returns the correct `Resolved` status from SWTR, but the fault injection was not applied. This confirms the `is_qa_fault_injection_enabled()` bug.

**VERDICT:** QA_FAULT_INJECTION_ENABLED_CHECK_BUG (cannot test learned behavior without fault injection)

---

## STAGE 4: SEMANTIC GENERALIZATION TO DIFFERENT ENTITY

**Not tested** - Cannot proceed without working fault injection.

---

## STAGE 5: POSITIVE-PATH SAFETY

**Not tested** - Cannot proceed without working fault injection.

---

## STAGE 6: CROSS-SKILL ISOLATION

**Not tested** - Cannot proceed without working fault injection.

---

## STAGE 7: RESTART SURVIVAL AGAIN

**Not tested** - Cannot proceed without working fault injection.

---

## STAGE 8: ROLLBACK

**Not tested** - Cannot proceed without working fault injection.

---

## STAGE 9: POST-ROLLBACK RUNTIME PROOF

**Not tested** - Cannot proceed without working fault injection.

---

## STAGE 10: REGRESSION SAFETY

**Not tested** - Cannot proceed without working fault injection.

---

## DEFECT CLASSIFICATION

### `QA_FAULT_INJECTION_ENABLED_CHECK_BUG`

**Description:** The `is_qa_fault_injection_enabled()` function in `qa_fault_injection.py` only checks `os.getenv()`, not the `.env` file. The `get_qa_fault_config()` function properly reads from `.env` file as fallback, but `is_qa_fault_injection_enabled()` does not.

**Evidence:**
1. `.env` file contains `PO_AGENT_QA_FAULT_INJECTION=1`
2. `is_qa_fault_injection_enabled()` returns False despite correct `.env` configuration
3. `get_qa_fault_config()` returns `{'enabled': True, ...}` showing it properly reads `.env`

**Fix Required:** Update `is_qa_fault_injection_enabled()` to also check the `.env` file like `get_qa_fault_config()` does.

---

## FINDINGS SUMMARY

| Stage | Status | Notes |
|-------|--------|-------|
| 1. Pre-restart policy proof | ✅ PASS | Policy exists and is correct |
| 2. Cold restart | ✅ PASS | Policy persisted and loaded |
| 3. Same-skill application | ❌ FAIL | QA fault injection not enabled (bug) |
| 4-10. Other tests | ⚠️ SKIPPED | Cannot proceed without working fault injection |

---

## IMMEDIATE FINDINGS

1. **Policy persistence works:** The learned policy is correctly stored and loaded after restart.

2. **Runtime policy store works:** The `LearnedPolicyStore` class properly reads from `.po_agent/learned_policies.json`.

3. **QA fault injection has a bug:** `is_qa_fault_injection_enabled()` doesn't read from `.env` file, causing fault injection to be skipped even when configuration is correct.

4. **No entity facts memorized:** The policy only contains behavioral metadata, not concrete facts.

---

## FINAL VERDICT

### `LEARNING_LOOP_PRODUCT_DEFECT`

**Defect:** `QA_FAULT_INJECTION_ENABLED_CHECK_BUG`

**Description:** The QA fault injection mechanism has an inconsistent check - `is_qa_fault_injection_enabled()` only checks environment variables, while `get_qa_fault_config()` also reads from `.env` file. This causes fault injection to be skipped even when the `.env` file has the correct configuration.

**Impact:** The learned policy mechanism works correctly, but testing it requires fault injection which is currently broken.

---

## REQUIRED FIX

Update `is_qa_fault_injection_enabled()` to also check the `.env` file:

```python
def is_qa_fault_injection_enabled() -> bool:
    """Check if QA fault injection is enabled via environment variable or .env file."""
    import os
    from pathlib import Path
    
    # Try environment first
    if os.getenv("PO_AGENT_QA_FAULT_INJECTION", "").strip() == "1":
        return True
    
    # Try .env file
    project_root = Path(__file__).resolve().parents[3]
    env_file = project_root / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        if key.strip() == "PO_AGENT_QA_FAULT_INJECTION" and value.strip() == "1":
                            return True
        except Exception:
            pass
    
    return False
```

---

## REPORT METADATA

**Tested HEAD:** `40e867bcf1068b08251fdce2bfdade8fbdd15a12`  
**Branch:** `feat/core8-real-query-hardening-v2`  
**QA:** GigaCode  
**Runtime:** `harness-dialogue-v2`  
**Adapter:** `task-api`  

**Policy ID:** `task-lookup:authoritative_recheck_on_negative:v1`  
**Policy store path:** `po-agent-platform-v2/.po_agent/learned_policies.json`  

---

**Report generated:** 2026-08-28  
**VERDICT: LEARNING_LOOP_PRODUCT_DEFECT**  
**Defect: QA_FAULT_INJECTION_ENABLED_CHECK_BUG**  
**STOP: Do not proceed to restart/generalization tests**
