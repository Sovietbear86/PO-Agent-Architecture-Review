# QA Assignment — Learning Loop 012 Controlled E2E

## Role
GigaCode is TESTER ONLY. Do not modify production code, tests, fixtures, skill definitions, configuration, AS21 data, or promotion state.

## Objective
Prove the first closed learning loop on top of the accepted Core-8 baseline without autonomous production mutation:

`real failure/feedback -> improvement candidate -> baseline/candidate evidence -> promotion gate -> human approval boundary`

## Pre-check
1. Checkout/pull `feat/learning-loop-012-v1` and record exact HEAD.
2. Confirm branch contains the accepted Core-8 baseline ancestry and Learning Loop 012 files.
3. Restart Task API and PO Agent from this HEAD.
4. Re-run the accepted Core-8 production matrix against real AS21. Required: 8/8.
5. AS21 mutations must remain 0.

## Test A — Developer tests
Run at minimum:
- `tests/test_learning_loop.py`
- `tests/test_learning_orchestrator.py`
- `tests/test_learning_eval_bridge.py`

Required: all pass.

## Test B — Controlled degraded candidate
Create test evidence only (do not edit source) representing the SAME 8 comparable Core-8 cases where baseline is 8/8 and candidate is 7/8.

Feed both snapshots through `ControlledLearningOrchestrator` / `LearningLoop`.

Required:
- decision = `reject`
- reason includes pass-rate regression
- candidate cannot promote even when `human_approved=True`
- SkillRegistry active skill/version count remains unchanged
- no production files/state are changed

## Test C — False-green candidate
Evaluate an 8/8 candidate snapshot with `false_green_count=1` against clean 8/8 baseline.

Required:
- decision = `reject`
- reason explicitly identifies false-green
- no promotion possible

## Test D — Insufficient evidence
Evaluate baseline and candidate with fewer than 8 comparable cases.

Required:
- decision = `insufficient_evidence`
- explicit human approval must NOT override insufficient evidence

## Test E — Equal/green candidate and human boundary
Evaluate clean baseline 8/8 vs clean candidate 8/8 on the same case set.

Required:
- gate decision = `recommend`
- `requires_human_approval = true`
- `can_promote(..., human_approved=False) = false`
- `can_promote(..., human_approved=True) = true`
- IMPORTANT: even after this check, no SkillRegistry promotion is executed automatically. This only proves the authorization predicate.

## Test F — Existing evolution pipeline integration
Create/obtain a normal `SkillImprovementCandidate` through the existing evolution layer and register it with `ControlledLearningOrchestrator`.

Required:
- evaluation artifact binds candidate_id, skill_id, skill_version, baseline, candidate, decision and evidence
- `request_human_approval()` returns evidence only
- it does NOT call `approve_candidate`, `implement_improvement`, `register_new_version`, or `promote_candidate`

## Test G — Evaluation bridge
Run an existing `EvalRunner` case set and convert the resulting `EvalReport` using `snapshot_from_eval_report`.

Required:
- total/passed counts preserved
- run_id/timestamp preserved in metadata
- explicit false-green/error counters preserved

## Test H — Full regression and Core-8 invariants
Run full pytest and re-check:
- Core-8 = 8/8
- false-green production matrix remains green
- real AS21 current-sprint/source behavior unchanged
- WMB-30000 attachments unchanged (5 XLSX unless proven live drift)
- no automatic production promotion
- AS21 mutations = 0

Known stale expectations from the accepted 011K baseline must be classified as stale, not reintroduced as product behavior.

## Final gate
Set `LEARNING_LOOP_012_CONTROLLED_E2E = PASS` only iff:
- Core-8 stays 8/8
- developer learning-loop tests pass
- degraded candidate rejected
- false-green candidate rejected
- insufficient evidence fails closed
- clean candidate only reaches RECOMMEND
- human approval remains mandatory
- no automatic SkillRegistry mutation/promotion occurs
- new HIGH production regressions = 0
- AS21 mutations = 0

## Report
Publish and push:
`qa_reports/LEARNING_LOOP_012_QA.md`

Footer:
```text
ASSIGNMENT_ID = LEARNING_LOOP_012_CONTROLLED_E2E
CURRENT_HEAD = <sha>
CORE8_AGENT_E2E_PASS = x/8
LEARNING_LOOP_DEV_TESTS_PASS = YES|NO
DEGRADED_CANDIDATE_REJECTED = YES|NO
FALSE_GREEN_CANDIDATE_REJECTED = YES|NO
INSUFFICIENT_EVIDENCE_FAIL_CLOSED = YES|NO
GREEN_CANDIDATE_RECOMMEND_ONLY = YES|NO
HUMAN_APPROVAL_BOUNDARY_PASS = YES|NO
AUTOMATIC_SKILL_REGISTRY_MUTATIONS = N
NEW_HIGH_PRODUCTION_REGRESSIONS = N
AS21_MUTATIONS_DURING_TEST = N
LEARNING_LOOP_012_CONTROLLED_E2E = PASS|FAIL
READY_FOR_LEARNING_LOOP_013 = YES|NO
```

After publishing STOP. Do not implement fixes and do not start 013.