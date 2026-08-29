# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly:

`qa_assignments/CORE8_SEMANTIC_SLOT_REGRESSION_ARCHEOLOGY_068.md`

## Why this assignment is active

Assignment 060 completed RED and found 19 remaining product failures: representative real semantic queries return empty `slots: {}` although person/product/status/multi-filter constraints are expected.

Before any production fix, we must prove whether this behavior worked in an earlier revision and identify the exact GOOD→BAD regression boundary.

Historical code evidence makes commit `9ba842e49ed5406e8f456893f2e533edf0a7f258` especially important because it introduced semantic slot-contract enforcement/repair. Its parent is `3b683ae5dc776a0245ed632d049e1e19d1f6f4ed`.

Do not assume that `9ba842e` is guilty; prove or disprove it by historical replay.

## Role

QA / diagnostic tester only.

Do not modify production code or test expectations.

## Mandatory rules

1. Fetch/pull current branch first and record current HEAD.
2. Preserve the current branch; use detached worktrees/checkouts for historical revisions as needed.
3. Execute Assignment 068 exactly as written.
4. Test the same representative semantic probes on current HEAD, `9ba842e`, and its parent; continue backwards if necessary until a proven GOOD revision is found or evidence is exhausted.
5. Use repeated runs to distinguish deterministic code regression from LLM/model variance.
6. Trace the semantic slot lifecycle and identify the first stage where slots disappear.
7. Do not implement a fix even if the cause becomes obvious.
8. Do not start Assignment 062 and do not resume 060 yet.
9. Commit/push only the allowed Assignment 068 QA report, then STOP.

## Required completion summary

Report:
- CURRENT_HEAD
- LAST_KNOWN_GOOD
- FIRST_KNOWN_BAD
- REGRESSION_BOUNDARY_PROVEN = YES/NO
- whether `9ba842e` introduced the regression
- first slot-loss stage
- repeatability classification
- final 068 verdict
- QA report path
- commit SHA

STOP after Assignment 068.