# Assignment 072 — CORE8 Semantic Correction Production Fix

## Goal
Localize and fix correction-state corruption in the production `task-api` path. Do not redesign the system. Prove the first failing boundary before changing production code, then make only the minimal evidence-backed fix.

## Production context
- Branch: `feat/core8-real-query-hardening-v2`
- Baseline completed stage: Assignment 071 / `4382330`
- Production mode: `task-api` + REAL AS21(SWTR), never fake/mock/frozen for final verification.
- Production runtime chain:
  `RecoveringLLMFirstSemanticInterpreter -> ConversationAwareSemanticInterpreter -> FailClosedIntentPreservingDialogueHarnessRuntime -> SemanticCorrectionRuntimeV2 -> ObservedHarnessRuntime`
- Production correction runtime is `SemanticCorrectionRuntimeV2`, not the legacy `CorrectionAwareHarnessRuntime`.

The branch may already contain candidate changes from a previous, unsuccessful Assignment 072 attempt. Do not assume those changes are correct merely because they are committed. Do not blindly revert them either. Establish evidence first.

A1/A2 fixes from Assignment 071 must not be reverted without proven regression evidence.

## Known bug to reproduce
Turn 1:
`Покажи задачи Гаранина в DMS со статусом todo`

Turn 2 correction:
`Покажи задачи Гаранина в DMS со статусом in progress`

Previously observed corruption included:
- `member_login` becoming the full correction query instead of authoritative login;
- `status_raw` remaining `todo` instead of changing to `in progress`.

Expected authoritative member identity for the known Garanin case is the identity resolved from configured/real grounding; do not hard-code it in production code.

## Phase 0 — Freeze and baseline
1. Do not change code.
2. Fetch/pull the current branch.
3. Record branch, HEAD, `git status`, and commits from `4382330` to HEAD.
4. Record production-file diff after `4382330` and identify already-present candidate fixes.
5. Start fresh/current-checkout PO Agent and Task API processes.
6. Run runtime freshness and REAL SWTR health preflight.
7. If the environment is unhealthy, classify it precisely. Do not switch to fake/frozen to obtain a pass.

## Phase 1 — Reproduce ×3 before any new code change
Use 3 independent `session_id` values and execute the exact two-turn scenario above.

For every repetition capture semantic state at these boundaries:

A. semantic interpretation output of Turn 1;
B. cached previous semantic frame immediately before correction;
C. `classify_dialogue_act` / `SemanticCorrectionRuntimeV2._classify()` result;
D. semantic state immediately before `rechecked = self.inner.process(previous.query, ...)`;
E. semantic frame produced by that internal recheck;
F. conversation semantic cache immediately AFTER recheck and BEFORE current correction processing;
G. semantic frame produced for the current correction query;
H. frame entering `ProductionEntityResolverV2` / grounding;
I. grounded slots immediately before execution.

At every boundary record at least:
- `person_raw`
- `member_login`
- product/sprint selector
- `status_raw`
- `status_semantic`
- `dialogue_act`
- `canonical_query`

Do not modify production code until all three pre-fix traces are complete.

## Phase 2 — FIRST_FAILING_BOUNDARY
Determine the first failing boundary separately for:

### member_login invariant
Expected: authoritative grounded login derived from real/configured identity.
Forbidden: full correction query or arbitrary prose.

### status_raw invariant
Expected after Turn 2: literal `in progress`.
Forbidden: stale `todo`.

Name the exact function/boundary where each value first becomes wrong. Do not use a generic root cause such as “LLM problem” without concrete input/output evidence.

### Mandatory hypothesis check
Explicitly test this hypothesis, but do not assume it is true:

`SemanticCorrectionRuntimeV2.process()` performs an internal recheck of `previous.query` before processing the current correction, while `ConversationAwareSemanticInterpreter.interpret()` mutates `_last[session]` on every interpretation. Determine whether that internal recheck becomes an unintended semantic conversation turn and contaminates the context used for the correction query.

If evidence disproves this hypothesis, follow the evidence to the actual first failing boundary.

## Phase 3 — Minimal fix only after proof
After FIRST_FAILING_BOUNDARY is proven:
1. Fix the first actual failing production boundary only.
2. No formatter/output workaround.
3. No fake/frozen runtime changes.
4. No hard-coded `Garanin.R.V`, person names, exact query strings, sprint IDs, or arbitrary domain status mappings.
5. Do not broaden scope into unrelated architecture cleanup.
6. Preserve unrelated slots from the previous semantic frame.
7. A new explicit status must replace the old status, not coexist with it.
8. If the proven cause is internal recheck mutation of semantic conversation state, prevent that mutation/contamination at the appropriate production boundary rather than masking corrupted slots downstream.

## Phase 4 — Post-fix correction trace ×3
Repeat the same correction scenario in 3 independent sessions and capture the same A-I boundaries.

Required invariants after Turn 2:
- person constraint preserved;
- authoritative `member_login` preserved/grounded correctly;
- DMS/product constraint preserved;
- `status_raw = in progress`;
- stale `todo` is replaced, not retained alongside the new value;
- `status_semantic` is not full-query prose;
- no unrelated slot corruption;
- no silent broadening of source execution.

Any repeat failure => RED.

## Phase 5 — Regression matrix
Run every scenario ×3 in independent sessions:
1. Person-only: `Покажи задачи Гаранина`
2. Sprint-id: use a real, proven AS21 sprint.
3. Exact task-id: use a real, proven AS21 task.
4. Status query: `Покажи задачи со статусом todo`
5. Combined person+product+status: `Покажи задачи Гаранина в DMS со статусом todo`
6. Correction scenario from this assignment.
7. Independent second member from `team_members.yaml`: test person-only and a correction flow. Record configured identity and actual grounded login. The production fix must not be specific to Garanin.

For status tests, preserve raw user status literally at the surface layer. Any canonical/business status semantics must be supported by downstream AS21/domain evidence, never arbitrary parser hardcode.

## Phase 6 — Real AS21 proof
From logs/traces prove:
- `HTTP_500_COUNT = 0`
- `FAKE_MOCK_SOURCE_CALLS = 0`
- positive live probes actually invoke REAL AS21/SWTR.

Timeout is not PASS. If AS21/SWTR instability prevents completion of the mandatory matrix, verdict must be RED / ENVIRONMENT_BLOCKED with evidence, not GREEN.

## Phase 7 — Automated tests
Run at minimum:
- `tests/test_semantic_core_v2.py`
- `tests/test_semantic_slot_recovery.py`
- all tests covering `SemanticCorrectionRuntimeV2`
- semantic conversation-state tests, if present
- production entity-grounding tests relevant to the proven boundary.

Do not weaken assertions to obtain PASS.

## Phase 8 — Report and STOP
Create exactly:

`qa_reports/CORE8_SEMANTIC_CORRECTION_072.md`

The report must include:
- exact commands;
- branch;
- commit SHA before;
- already-present candidate changes at start;
- correction traces BEFORE ×3;
- A-I boundary state evidence;
- `FIRST_FAILING_BOUNDARY` for `member_login`;
- `FIRST_FAILING_BOUNDARY` for `status_raw`;
- root cause;
- minimal diff description;
- commit SHA after fix;
- correction traces AFTER ×3;
- regression matrix with all repetitions;
- second-member evidence;
- real AS21 evidence;
- HTTP 500 count;
- fake/mock calls count;
- automated test results;
- remaining known failures;
- `FINAL VERDICT: GREEN` or `RED`.

GREEN is allowed only when correction invariants pass 3/3, the mandatory regression matrix passes, real AS21 calls are proven, HTTP 500 count is zero, and fake/mock source calls are zero.

Commit/push the required fix/tests/report as appropriate, report the final SHA, and STOP.

Do NOT start Assignment 073.
Do NOT start a full rerun automatically.