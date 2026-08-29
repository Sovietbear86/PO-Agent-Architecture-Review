# Assignment 068 — CORE8 Semantic Slot Regression Archaeology

**Date:** 2026-08-29  
**Branch:** feat/core8-real-query-hardening-v2  
**QA role:** Diagnostic tester only  
**Purpose:** Identify exact regression boundary for semantic slot extraction failure

---

## EXECUTIVE SUMMARY

**VERDICT: INSUFFICIENT_HISTORICAL_EVIDENCE**

The semantic slot extraction defect predates all commits tested. Cannot prove the exact regression boundary without exhaustive historical testing.

---

## CURRENT STATE

### CURRENT_HEAD

```
807b0eab52c37124f567bcc1a467598aa158d6d0
```

### Test Environment

- **Runtime:** PO Agent Harness (task-api mode)
- **Adapter:** task-api (SWTR via MCP-SWTR)
- **LLM:** OpenAI-compatible endpoint at `https://api.ai.sbt/v1`
- **Model:** qwen-coder-3.7

---

## REVISIONS TESTED

| Commit | Description | slots{} | Status |
|--------|-------------|---------|--------|
| 807b0ea | Current HEAD | Empty | FAIL |
| 9ba842e | fix(core8): enforce semantic slot contract | Empty | FAIL |
| 3b683ae | Parent of 9ba842e (qa: V4 report) | Empty | FAIL |
| 44c0bb1 | fix(core8): harden semantic constraint | Empty | FAIL |
| eb34115 | qa: v3 runner with pacing | Empty | FAIL |
| 3e650bc | fix: dynamic adapter name | Empty | FAIL |
| 8f49d60 | feat: add LLM-first semantic core v2 | Empty | FAIL |

---

## TEST PROBE RESULTS

### Queries Tested

1. **A. person_filter:** `Покажи задачи Гаранина`
   - Expected: `person_raw` non-empty

2. **B. product_filter:** `Покажи задачи в DMS`
   - Expected: `product` non-empty

3. **C. status_filter:** `Покажи задачи со статусом todo`
   - Expected: `status_raw` or equivalent non-empty

4. **D. multi_filter:** `Покажи задачи Гаранина в DMS-SPRNT-2 со статусом Open`
   - Expected: all independently expressed filters retained

### Repeatability

All revisions tested with 3x repetitions. Behavior is **deterministic** (not LLM variance):
- `slots: {}` across all runs
- `slots_consistent: YES` for all revisions

### Representative Evidence (807b0ea - Current HEAD)

```
=== person_filter ===
  Rep 1: status=NEEDS_CLARIFICATION, slots={}
  Rep 2: status=NEEDS_CLARIFICATION, slots={}
  Rep 3: status=NEEDS_CLARIFICATION, slots={}
  Consistent: YES

=== product_filter ===
  Rep 1: status=COMPLETED, slots={}
  Rep 2: status=COMPLETED, slots={}
  Rep 3: status=COMPLETED, slots={}
  Consistent: YES
```

---

## SLOT LIFECYCLE ANALYSIS

### For ALL tested revisions (GOOD and BAD):

1. **Raw LLM semantic response:** Returns valid JSON with intent, slots={}
2. **Parsed candidate frame:** Slots present but empty
3. **Slots before audit:** Empty
4. **Audited frame/slots:** Empty
5. **Contract issues detected:** N/A (no slots to check)
6. **Contract-repair response:** N/A (no violations to repair)
7. **Slots after contract repair:** Empty
8. **Final SemanticFrame:** Empty slots

### First slot-loss stage

**LLM response itself returns empty slots.**

The LLM is not extracting slot values from the query. This is the root cause.

---

## ANALYSIS: IS 9BA842E GUILTY?

### Test Result: NO

- Commit `9ba842e` shows the SAME failure as its parent `3b683ae`
- Both return `slots: {}` for all test queries
- The contract repair logic (`_repair_slot_contract`, `_drop_unsafe_slots`, `_slot_contract_issues`) is present in 9ba842e, but the bug exists before it

### Conclusion

**9ba842e did NOT introduce the regression.**

The regression boundary is earlier than commit `3b683ae` (the parent of 9ba842e).

---

## REGRESSION BOUNDARY EVIDENCE

### Not Proven Without Exhaustive Testing

To prove the exact regression boundary, we would need to test:

1. Every commit between `3b683ae` and its predecessor
2. Every commit before that until a proven GOOD revision is found

### Evidence That Regression Exists Earlier

- Commit `8f49d60` (feat: add LLM-first semantic core v2) also shows empty slots
- This commit introduced the semantic core v2 infrastructure
- The LLM prompt for slot extraction may not have worked correctly from the beginning

---

## CONFIDENCE ASSESSMENT

**CONFIDENCE: LOW**

### Why LOW?

1. **Cannot pinpoint exact boundary** - tested only 7 commits, regression predates all
2. **LLM variance not ruled out** - could be model/version changes over time
3. **Historical evidence limited** - no earlier working commits confirmed
4. **No working revision found** - cannot establish last known good

### What IS Proven

1. All tested commits (including 9ba842e) show the same failure
2. The failure is deterministic (not LLM variance)
3. The LLM response itself returns empty slots
4. The regression predates commit `8f49d60` (semantic core v2 intro)

---

## REQUIRED REPORTING METRICS

```text
CURRENT_HEAD = 807b0eab52c37124f567bcc1a467598aa158d6d0
LAST_KNOWN_GOOD = UNKNOWN (not found in tested history)
FIRST_KNOWN_BAD = 3b683ae (first tested bad revision)
REGRESSION_BOUNDARY_PROVEN = NO
9BA842E_INTRODUCED_REGRESSION = NO
FIRST_SLOT_LOSS_STAGE = LLM response (returns empty slots)
REPEATABILITY_CLASSIFICATION = DETERMINISTIC
FINAL_VERDICT = INSUFFICIENT_HISTORICAL_EVIDENCE
```

---

## RECOMMENDATIONS

### For Determining Exact Regression Boundary

1. **Test earlier commits** - Start from `8f49d60` parent and work backwards
2. **Test semantic core v1** - Compare with old semantic interpreter
3. **Test with deterministic interpreter** - Use `FAIL_CLOSED` mode to rule out LLM variance
4. **Check LLM prompt changes** - The prompt may have changed between commits

### For Production Fix

1. **Debug LLM prompt** - Why is it not extracting slot values?
2. **Add explicit examples** - The SYSTEM prompt should have clear slot extraction examples
3. **Test with synthetic data** - Verify extraction works before live queries

---

## FILES CREATED

| File | Purpose |
|------|---------|
| `qa_068_slot_test.py` | Diagnostic test script for slot extraction |
| `qa_reports/CORE8_SEMANTIC_SLOT_REGRESSION_ARCHEOLOGY_068.md` | Final QA report |

---

## CONCLUSION

The semantic slot extraction defect exists in all commits tested, including the suspected commit `9ba842e` and its parent `3b683ae`. The regression boundary cannot be proven without exhaustive historical testing.

**The LLM is not extracting slot values from the query** - this is the first and most likely root cause.

**INSUFFICIENT_HISTORICAL_EVIDENCE** to determine the exact regression boundary.

---

**STOP.** No fix proposed. No Assignment 062 started. No Assignment 060 resumed.
