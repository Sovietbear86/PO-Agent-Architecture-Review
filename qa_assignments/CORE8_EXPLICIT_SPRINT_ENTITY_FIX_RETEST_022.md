# QA Assignment 022 — Explicit Sprint Entity Preservation + Correction Retest

GigaCode is TESTER ONLY. Do not modify production code, tests, fixtures, configuration, AS21/SWTR, roadmap files, or skill definitions. Publish only the QA report.

## Purpose
Close the remaining blocker from `CORE8_AS21_CONTRACT_SEMANTIC_RETEST_019_RERUN.md` before the full 017_V2 rerun.

Observed defect:
- user says `DMS-SPRNT-1` / `DMS-SPRNT-2`;
- provider/runtime degraded the explicit sprint identifier to `SPRNT-1` / `SPRNT-2` and treated it as a task key;
- valid sprint searches failed with `entity_not_found`.

Developer fixes under test:
- `Core8SemanticPrecisionInterpreter` now preserves any explicit `<SPACE>-SPRNT-<N>` token atomically and repairs accidental task-lookup classification for task-list requests;
- `FailClosedIntentPreservingDialogueHarnessRuntime` no longer enriches the `SPRNT-N` suffix inside an explicit sprint ID as a task key;
- regression tests cover DMS and a non-DMS example to prove no hardcoding.

## A. Restart from current HEAD
Restart Task API and PO Agent from CURRENT branch HEAD. Record HEAD and service health. HTTP 500 count must be zero.

## B. Focused developer tests
Run:
- `tests/test_explicit_sprint_id_precision.py`
- relevant semantic/dialogue/entity-grounding tests;
- source-readiness regression tests.

Required: new focused tests all pass.

## C. Explicit sprint production queries
Run all of these through real `/api/v1/query` with fresh sessions unless specified:

1. `Покажи задачи Гаранина в DMS-SPRNT-1`
2. `Покажи задачи Гаранина в DMS-SPRNT-2`
3. `Покажи задачи Гаранина по DMS в спринте DMS-SPRNT-1`
4. `Покажи задачи в DMS-SPRNT-1`
5. one equivalent explicit sprint query using another real space/sprint if source-backed and available.

For each record:
- semantic intent;
- `sprint_id` slot after precision layer;
- any `task_key` slot;
- grounded sprint id;
- response status;
- returned task keys/count;
- warnings.

Hard requirements:
- exact `DMS-SPRNT-1`/`DMS-SPRNT-2` must survive unchanged;
- no `task_key=SPRNT-1` or `SPRNT-2` may appear;
- no `entity_not_found` caused by sprint-id degradation;
- source-grounded empty result is allowed only if independently verified empty.

## D. Raw source oracle
For DMS-SPRNT-1 and DMS-SPRNT-2 independently obtain the complete live sprint task sets from SWTR and compare production query output where filters are equivalent. Do not use the agent result as its own oracle.

For the Garanin queries, resolve assignee through raw/canonical assignee identifiers and report `MISSING_KEYS` and `EXTRA_KEYS`.

## E. Golden correction scenario
Same session:
1. `Покажи открытые задачи Гаранина в последнем спринте по DMS`
2. `Ты не прав, проверь ещё раз`

Required:
- turn 1 is non-500 and grounded;
- turn 2 reopens/rechecks evidence, not a new unrelated query;
- targeted clarification is produced if `open` / `last sprint` semantics remain unresolved;
- previous query context is retained;
- persistent skill mutation = 0.

Then answer the clarification explicitly and verify execution uses the original assignee/product context.

## F. Task-key non-regression
Verify ordinary exact task lookup still works for at least:
- one DMS task key such as `DMS-348` if source-backed;
- one OLP/WMB task key.

The sprint fix must not disable real task-key enrichment.

## G. Status-normalization regression classification
The previous report listed:
`test_normalize_unknown_status` expected `TaskStatus.OPEN`, while production now returns `TaskStatus.UNKNOWN`.

Do not label this simultaneously as both `NEW_HIGH_PRODUCTION_REGRESSION=1` and `not a regression`.
Classify exactly one:
- `STALE_TEST_EXPECTATION` if fail-closed UNKNOWN is the intentional current contract and no Core-8 behavior is broken;
- `PRODUCTION_REGRESSION` only if repository/spec evidence proves unknown statuses must map to OPEN.

Provide evidence for the classification. Do not change the test.

## H. Protected smoke
Run protected Core-8 smoke sufficient to detect regressions. AS21 mutations must remain 0.

## Decision
GREEN requires:
- exact sprint IDs preserved;
- no suffix-as-task-key defect;
- raw source comparison acceptable;
- correction flow retained;
- exact task lookup retained;
- no unresolved HIGH production regression;
- HTTP 500 = 0.

Publish `qa_reports/CORE8_EXPLICIT_SPRINT_ENTITY_FIX_RETEST_022.md` with footer:

```text
ASSIGNMENT_ID = CORE8_EXPLICIT_SPRINT_ENTITY_FIX_RETEST_022
CURRENT_HEAD = <sha>
FOCUSED_TESTS_PASS = x/y
QUERY_HTTP_500_COUNT = N
DMS_SPRNT_1_PRESERVED = YES|NO
DMS_SPRNT_2_PRESERVED = YES|NO
SPRINT_SUFFIX_AS_TASK_KEY_COUNT = N
EXPLICIT_SPRINT_QUERY_PASS = x/5
RAW_ORACLE_MATCH_PASS = x/y
GOLDEN_QUERY_PASS = YES|NO
CHALLENGE_TRIGGERS_FRESH_RECHECK = YES|NO
TARGETED_CLARIFICATION_PASS = YES|NO
SESSION_CONTEXT_RETENTION_PASS = YES|NO
PERSISTENT_SKILL_MUTATION_FROM_CORRECTION = 0
EXACT_TASK_LOOKUP_NONREGRESSION = YES|NO
UNKNOWN_STATUS_CLASSIFICATION = STALE_TEST_EXPECTATION|PRODUCTION_REGRESSION
NEW_HIGH_PRODUCTION_REGRESSIONS = N
CORE8_SMOKE_PASS = <result>
AS21_MUTATIONS_DURING_TEST = 0
READY_TO_RERUN_017_V2 = YES|NO
```

If GREEN, stop and report `READY_TO_RERUN_017_V2 = YES`. Do not run 017_V2 in this assignment.