# GigaCode — Current Action

## Status

`ACTIVE_QA_ASSIGNMENT_072D`

## Role boundary — mandatory

You are QA/tester only.

**DO NOT modify production code, prompts, tests, fixtures, runtime configuration, credentials, AS21/SWTR data, GIGACODE.md, PO_AGENT_HARNESS_EVOLUTION_PLAN.md, or this file.**

The current branch contains a candidate correction patch produced during the previous GigaCode run. Treat that code as an immutable candidate under owner review. Your job is to test it adversarially, not improve it.

If any production file becomes dirty during this assignment: STOP and report RED.

## Assignment 072D — correction candidate + protected Learning Loop certification

### Goal

Determine whether the current candidate patch can be accepted without damaging the Harness learning contract or dialogue/clarification behavior.

Do not start Assignment 095. Do not implement fixes.

Production mode: `task-api` + REAL AS21(SWTR). Fake/mock/frozen source data cannot be used as positive acceptance evidence.

## Phase 0 — provenance and clean start

1. Fetch/pull `feat/core8-real-query-hardening-v2`.
2. Record exact HEAD SHA.
3. Record `git status --short` and prove production worktree is clean.
4. Restart PO Agent and task-api from that exact HEAD.
5. Record production runtime provenance and REAL AS21 mode.
6. Record initial HTTP 500 count and fake/mock source-call count.

## Phase 1 — correction regression

Using three independent session IDs, repeat:

Turn 1:
`Покажи задачи Гаранина в DMS со статусом todo`

Turn 2:
`Покажи задачи Гаранина в DMS со статусом in progress`

For each run prove:
- `member_login == Garanin.R.V` after correction;
- `status_raw` is replaced by the new status, not appended beside the old one;
- product/person constraints from the prior semantic frame survive;
- no full-query prose appears in semantic slots;
- grounded execution uses the corrected slots.

Repeat the same correction pattern with a second real member from `team_members.yaml`; do not hardcode a second identity into production code or tests.

## Phase 2 — clarification regression (critical adversarial test)

The candidate patch changed pending-clarification behavior. Prove it has not broken ordinary clarification.

Create at least 6 black-box cases covering:
1. genuine short clarification answer;
2. genuine multi-word clarification answer;
3. clarification answer containing a status word;
4. clarification answer containing Russian prepositions such as `в`, `по`, `для`;
5. a full new query while clarification is pending;
6. a genuine semantic correction while clarification is pending.

For every case capture:
- pending state before request;
- dialogue act if available;
- whether the request was consumed as clarification vs interpreted as correction/new query;
- resulting semantic frame/slots;
- final response status.

A keyword heuristic accidentally classifying normal clarification as correction/new query is RED.

## Phase 3 — protected Learning Loop (mandatory)

This phase is release-critical. A correction fix is RED if this chain is broken.

Use an applicable production skill and the existing bounded learned behaviour `authoritative_recheck_on_negative`.

Prove the complete chain with exact evidence:

`negative/incorrect result`
`-> explicit user correction/negative feedback`
`-> fresh authoritative AS21 recheck`
`-> source-grounded validated result`
`-> generalized learned policy promotion`
`-> persistent policy record`
`-> different query/entity benefits from policy`
`-> cold process restart`
`-> policy reloads and still applies`
`-> rollback`
`-> policy no longer applies after rollback`

Mandatory assertions:
- learned behaviour is exactly allow-listed/generalized, not a stored answer;
- no task ID, member login, sprint ID, entity truth, correction prose or answer text is persisted as learned fact;
- `source_recheck_performed == true` where the contract requires it;
- promotion is backed by authoritative evidence;
- repeated identical correction does not create unbounded duplicate active policies;
- restart uses a genuinely new process/runtime, not the same in-memory object;
- rollback is demonstrated, not inferred;
- REAL AS21 evidence is present for authoritative validation.

If a safe production negative cannot be created without source mutation, use an already-supported QA fault-injection mechanism ONLY for the initial negative condition, while authoritative validation must still use REAL read-only AS21. Do not create or modify fixtures/source facts.

## Phase 4 — semantic/source regression matrix

Run at least 3 independent sessions each for:
- person-only;
- sprint-id;
- exact task-id;
- status-only;
- combined person+product+status;
- correction preserving prior constraints.

Use proven real identifiers from the source/team configuration. No invented IDs.

Record expected vs actual grounded slots and source result evidence.

## Phase 5 — automated tests

Run all relevant existing tests for:
- semantic core;
- semantic slot recovery;
- correction runtime;
- dialogue/clarification runtime;
- learned policy store / persistent learning;
- any existing Core-8 regression suite touching these paths.

Do not edit tests to make them pass.

Report every failure, including pre-existing failures. Distinguish pre-existing from newly introduced only with evidence from an earlier baseline/commit.

## Phase 6 — source integrity

Mandatory final counters:
- HTTP 500 count;
- HTTP 502 count, if observed;
- fake/mock/frozen source calls count;
- AS21 write calls count (must be 0);
- successful REAL AS21 read evidence.

Timeout/hang is not PASS.

## Output

Create only:

`po-agent-platform-v2/qa_reports/CORE8_SEMANTIC_CORRECTION_LEARNING_072D.md`

The report must contain:
- exact commands;
- tested HEAD SHA;
- clean-worktree proof before/after;
- correction traces ×3 plus second-member evidence;
- 6-case clarification matrix;
- complete Learning Loop trace from negative feedback through rollback;
- persisted policy record schema/content with entity facts redacted if necessary but structural fields visible;
- cold restart evidence;
- semantic/source regression matrix;
- automated-test results;
- REAL AS21 evidence;
- HTTP 500/502 counts;
- fake/mock/frozen source-call count;
- AS21 write-call count;
- remaining known failures.

Final verdict rules:

`GREEN` only if correction, clarification behavior, complete protected Learning Loop, source integrity and relevant regressions are all GREEN.

Otherwise `RED` and identify the **FIRST_FAILING_BOUNDARY**. Do not fix it.

Commit and push ONLY the QA report. Do not modify any other file.

STOP after the report. Do not start Assignment 073 or 095.