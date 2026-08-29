# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly:

`qa_assignments/CORE8_SEMANTIC_SLOT_070_TRIAGE_071.md`

## Context

Assignment 070 ended `RED_PRODUCT_DEFECT`, but its result is contaminated because QA modified production code in commit `ac17b2035e9c83e77b19d9b1fe1765d8759fb93e` despite the QA-only rule. The 070 report also contains unresolved/inconsistent evidence: 32/36 aggregate semantic constraints, a separate `status_semantic 0/9` line, partial DMS/OLP grounding, and a genuine-correction defect.

Assignment 071 must separate evidence from implementation, classify each unauthorized production hunk, reconstruct the clean owner baseline, explain the exact four failed constraints, and locate the correction failure boundary.

## Role

QA/tester only.

Do not modify production code, prompts, tests, fixtures, credentials, wrappers, runtime configuration or AS21/SWTR data. Do not revert/amend `ac17b20`; analyze it only.

## Mandatory rules

1. Fetch/pull `feat/core8-real-query-hardening-v2` and record START_HEAD.
2. Execute Assignment 071 exactly as written.
3. Use REAL AS21/SWTR for live positive probes; no fake/mock positive data.
4. Run fresh-runtime and SWTR health preflight.
5. Analyze A1/A2/A3 production hunks independently; do not assume `todo == open` without real domain/runtime evidence.
6. Reconstruct/test the clean owner baseline separately from `ac17b20` without changing production code on the working branch.
7. Produce an explicit 36-constraint ledger and explain the exact four failures and any metric inconsistency.
8. Reproduce genuine correction ×3 and identify FIRST_FAILING_BOUNDARY.
9. Commit/push only `qa_reports/CORE8_SEMANTIC_SLOT_070_TRIAGE_071.md`.
10. Do not start 060/062/072 automatically. STOP.

## Required completion summary

Report at minimum:
- START_HEAD and tested SHAs;
- runtime/SWTR preflight;
- A1/A2/A3 verdicts;
- clean-baseline vs `ac17b20` comparison;
- exact 36-constraint ledger + four failures;
- metric consistency verdict;
- correction trace ×3 + FIRST_FAILING_BOUNDARY;
- compact real probe matrix ×3;
- HTTP 500 and fake/mock counts;
- READY_FOR_OWNER_FIX YES/NO;
- READY_FOR_060_FULL_RERUN YES/NO;
- final 071 verdict and report commit SHA.

STOP after Assignment 071.