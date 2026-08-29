# GigaCode — Current Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Role boundary — mandatory

You are QA/tester only.

**DO NOT modify production code, prompts, tests, fixtures, runtime configuration, credentials or AS21/SWTR data.**
Do not implement a fix even if the root cause looks obvious. The owner will make all production-code changes after your evidence is reviewed.

## First: discard your unfinished local production edits

The previous GigaCode session started editing these files locally and stopped mid-fix:
- `po-agent-platform-v2/src/po_agent/harness/semantic_core_v2.py`
- `po-agent-platform-v2/src/po_agent/harness/semantic_correction_runtime_v2.py`

Those unfinished edits are NOT owner-approved and must not be tested.

1. Record `git status` and `git diff` for evidence.
2. Fetch the current branch from origin.
3. Restore ONLY the two production files above from `origin/feat/core8-real-query-hardening-v2`.
4. Pull/fetch so the worktree matches the current remote branch.
5. Prove the two files are clean before testing.
6. If any OTHER production file is dirty, STOP and report it; do not clean or modify unrelated files.

## Assignment 072 — boundary proof only

Goal: prove the correction-state corruption boundary on the current owner baseline. Do **not** fix it.

Production mode: task-api / REAL AS21(SWTR). No fake/mock/frozen positive evidence.

### Reproduce ×3

Use 3 independent `session_id` values. In each session run:

Turn 1:
`Покажи задачи Гаранина в DMS со статусом todo`

Turn 2:
`Покажи задачи Гаранина в DMS со статусом in progress`

For every repetition capture these boundaries:

A. semantic interpretation result of Turn 1;
B. cached `ConversationAwareSemanticInterpreter._last[session]` before Turn 2;
C. `classify_dialogue_act` result;
D. semantic cache immediately before the internal recheck of `previous.query`;
E. semantic frame produced by that internal recheck;
F. semantic cache immediately AFTER recheck and BEFORE interpreting the correction query;
G. semantic frame produced from the correction query;
H. frame entering production entity grounding;
I. grounded slots immediately before execution.

Record at every boundary where available:
- `person_raw`
- `member_login`
- `product` / sprint selector
- `status_raw`
- `status_semantic`
- `dialogue_act`
- `canonical_query`

### Mandatory hypothesis check

Explicitly test, but do not assume, this hypothesis:

`SemanticCorrectionRuntimeV2.process()` internally re-executes `previous.query`; that execution passes through `ConversationAwareSemanticInterpreter.interpret()` and may overwrite `_last[session]`, so the subsequent correction is interpreted against the recheck frame rather than the intended prior user turn.

Determine separately:
- `FIRST_FAILING_BOUNDARY_MEMBER_LOGIN`
- `FIRST_FAILING_BOUNDARY_STATUS_RAW`

Do not write vague conclusions such as "LLM issue". Name the first concrete function/boundary where the value becomes wrong and show before/after state.

## Minimal regression sanity checks

Without changing code, also run once each on the same current owner baseline:
- person-only;
- status-only;
- combined person+product+status;
- exact task-id if a proven real ID is available;
- sprint-id if a proven real sprint is available.

Record real AS21 evidence, HTTP 500 count and fake/mock source-call count.

A timeout is not PASS.

## Output

Create/update only:

`qa_reports/CORE8_SEMANTIC_CORRECTION_072.md`

The report must contain:
- exact commands;
- remote commit SHA tested;
- proof unfinished local production edits were discarded;
- correction traces ×3;
- boundaries A-I;
- both FIRST_FAILING_BOUNDARY values;
- root-cause evidence (no fix);
- sanity regression results;
- real AS21 evidence;
- HTTP 500 count;
- fake/mock calls count;
- remaining failures;
- `FINAL_VERDICT: RED` if the corruption is reproduced, otherwise explain why not reproduced.

Commit and push ONLY the QA report. Do not modify `GIGACODE_NEXT_ACTION.md`.

STOP after the report. Do not start Assignment 073 and do not implement any production fix.