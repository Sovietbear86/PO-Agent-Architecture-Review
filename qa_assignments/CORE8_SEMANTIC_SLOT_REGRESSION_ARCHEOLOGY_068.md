# ASSIGNMENT 068 — CORE8 Semantic Slot Regression Archaeology

## Purpose

Before any production fix for the Assignment 060 RED result, determine whether semantic slot extraction worked in an earlier known-good revision, identify the first revision where it stopped working, and prove the exact regression boundary.

This is a historical/diagnostic assignment. Do **not** modify production code.

## Current failure from Assignment 060

Assignment 060 reports:
- semantic unit tests: 7/7 PASS;
- source/oracle: PASS;
- new regressions: 0 outside this defect;
- 19 product failures remain;
- representative live queries produce `slots: {}` where constraints are expected.

Examples:
- `Покажи задачи Гаранина` → expected `person_raw`;
- `Покажи задачи в DMS` → expected `product`;
- `Покажи задачи со статусом todo` → expected `status_raw`;
- compound/multi-filter query → expected all independently expressed slots.

Relevant production commit already suspected by 060:
`9ba842e49ed5406e8f456893f2e533edf0a7f258` — `fix(core8): enforce semantic slot contract and repair invalid frames`.
Its parent is:
`3b683ae5dc776a0245ed632d049e1e19d1f6f4ed`.

## Goal

Answer, with evidence:

1. Did the same semantic slot scenarios work before?
2. What is the last known-good commit?
3. What is the first known-bad commit?
4. Is `9ba842e` the regression introduction point, or did the defect exist earlier?
5. At which exact stage do slot values disappear in GOOD vs BAD revisions?

## Mandatory method

### 1. Preserve current branch

- fetch/pull `feat/core8-real-query-hardening-v2`;
- record current HEAD;
- verify clean worktree;
- do not rewrite branch history;
- do not commit any production/test changes.

Use detached worktrees/temporary checkouts for historical execution where necessary.

### 2. Establish the historical candidate boundary

At minimum inspect/test:

- current failing HEAD from Assignment 060;
- `9ba842e49ed5406e8f456893f2e533edf0a7f258`;
- parent `3b683ae5dc776a0245ed632d049e1e19d1f6f4ed`.

If parent is also bad, continue backwards using git history until a proven GOOD revision is found or evidence is exhausted.

If parent is GOOD and `9ba842e` is BAD, regression boundary is established.

### 3. Use the same controlled semantic probes on every revision

Run the same four representative queries against the semantic interpreter path:

A. `Покажи задачи Гаранина`
Expected semantic constraint: `person_raw` non-empty.

B. `Покажи задачи в DMS`
Expected semantic constraint: `product` non-empty.

C. `Покажи задачи со статусом todo`
Expected semantic constraint: `status_raw` or equivalent raw semantic status non-empty.

D. One existing Assignment 060 multi-filter query.
Expected: all independently expressed filters retained.

Do not weaken expected semantics to fit historical output. Record exact frame shape used by that revision.

### 4. Trace slot lifecycle

For GOOD and BAD revisions capture, without permanently editing production files if avoidable:

- raw first LLM semantic response;
- parsed candidate frame;
- candidate slots before audit;
- audited frame/slots;
- contract issues detected, if the revision has contract checking;
- contract-repair response, if present;
- slots after contract repair;
- slots after fail-safe/drop logic;
- final SemanticFrame delivered to planner/runtime.

If a stage does not exist in an older revision, mark `N/A`.

The purpose is to find the **first stage where a previously non-empty constraint becomes empty or disappears**.

### 5. Distinguish model variance from deterministic regression

For each revision/query run enough repetitions to determine whether the behavior is deterministic enough to classify.

Minimum: 3 identical runs for each representative probe on the candidate GOOD and BAD revisions.

Classify each revision as:
- `GOOD_STABLE`
- `BAD_STABLE`
- `MODEL_VARIANCE`
- `ENVIRONMENT_BLOCKED`

Do not call a commit bad from one anomalous LLM response if repeated behavior contradicts it.

### 6. Compare production code

If a GOOD→BAD boundary is proven, inspect the diff and identify only changes capable of affecting semantic slots.

Pay special attention to:
- extraction/audit prompts;
- `_slot_contract_issues`;
- `_repair_slot_contract`;
- `_drop_unsafe_slots`;
- merge/order of extraction → audit → repair → normalization;
- conditions under which a repair response replaces a candidate frame;
- behavior when the repair/audit returns a valid intent but empty `slots`.

Do not propose a fix until the regression boundary and disappearing stage are proven.

### 7. Historical evidence

Search existing QA reports/tests/commit messages for prior evidence that person/product/status filtering worked.

Historical evidence is supporting evidence only; the historical runtime replay above is the primary proof.

## Required report

Create:

`qa_reports/CORE8_SEMANTIC_SLOT_REGRESSION_ARCHEOLOGY_068.md`

Include:

- CURRENT_HEAD
- revisions tested
- exact environment/model used
- probe matrix per revision
- 3x repeatability result
- LAST_KNOWN_GOOD
- FIRST_KNOWN_BAD
- REGRESSION_BOUNDARY_PROVEN = YES/NO
- first slot-loss stage
- relevant diff/function(s)
- whether `9ba842e` introduced the regression
- confidence: HIGH/MEDIUM/LOW

## Final verdict

Return exactly one:

`REGRESSION_BOUNDARY_PROVEN`

`DEFECT_PREDATES_9BA842E`

`MODEL_VARIANCE_NOT_CODE_REGRESSION`

`INSUFFICIENT_HISTORICAL_EVIDENCE`

`ENVIRONMENT_BLOCKED`

## Rules

- QA/diagnostic only.
- No production fix.
- No test expectation changes.
- No credential/config changes unless required only to reproduce the exact historical runtime and documented.
- No secrets in report.
- Do not start Assignment 062.
- Do not resume Assignment 060 certification yet.
- Commit/push only the allowed QA report.

STOP after the report and verdict.