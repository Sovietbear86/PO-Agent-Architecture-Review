# QA Assignment — Learning Loop 013: task_search measurable self-improvement

## Role boundary
GigaCode is TESTER ONLY. Do not edit production code, repository tests, skill definitions, configuration, AS21 data, or committed fixtures. Temporary `/tmp` scripts are allowed only to build an isolated in-memory candidate evaluator; do not commit them.

## Purpose
Prove Gate C1 from `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`: the system must turn failure evidence into a bounded candidate proposal and demonstrate measurable `task_search` improvement in shadow evaluation on an identical frozen corpus, with zero production mutation.

## Pre-check
1. Checkout/pull `feat/learning-loop-013-v1` and record HEAD.
2. Read `PO_AGENT_HARNESS_EVOLUTION_PLAN.md` and `PO_AGENT_HARNESS_EVOLUTION_PLAN_STATUS_013.md`.
3. Run existing 012 tests and new `tests/test_learning_loop_013.py`.
4. Restart Task API and PO Agent only if required for the Core-8 regression check. Confirm AS21 remains read-only.

## Test A — automatic failure -> proposal synthesis
Create a controlled `task_search` failure corpus from real/reproducible query semantics. Prefer a natural Russian synonym/phrase variant that the legacy deterministic task router does not recognize while the intended intent is unambiguously `task_search` (for example a `карточка/отыщи` task lookup variant). Do not manufacture AS21 facts.

Record failure entries with trace IDs/category/query/error. Feed them to `LearningCycle013.build_proposal()`.

Required:
- deterministic failure clustering occurs;
- proposal kind is appropriate (`routing_alias` for routing confusion; entity/source/prompt categories map to their bounded types);
- proposal retains trace/evidence IDs;
- `proposal.executable == False`;
- `requires_sandbox == True`;
- `requires_human_approval == True`;
- no production file/skill/registry mutation.

## Test B — frozen task_search corpus
Build a bounded frozen corpus of at least 8 `task_search` queries, including:
- exact key lookup;
- ordinary task search phrase;
- assignee filter wording;
- sprint wording;
- project/space wording;
- empty/nonexistent case;
- at least one synonym/phrase responsible for the controlled baseline weakness;
- one protected negative/unsupported control where applicable.

Store only safe IDs/expected semantic intent and hashes in the QA report. Compute a stable `case_set_sha256` and use one `corpus_id` for both baseline and candidate.

Required: baseline and candidate snapshots contain identical `corpus_id` and `case_set_sha256`.

## Test C — isolated candidate application
Without editing repository files, create an in-memory/test-only candidate router/evaluator that applies ONLY the proposal produced in Test A. It may wrap/subclass the current deterministic router in a temporary script and add the proposed alias/rule in memory.

This is a candidate sandbox, not production.

Required:
- baseline uses current behavior;
- candidate uses only the synthesized bounded change;
- no Git diff from candidate application;
- no active SkillRegistry mutation;
- no AS21 mutation.

## Test D — measurable shadow improvement
Evaluate baseline and candidate on exactly the frozen corpus from Test B and convert results into `EvaluationSnapshot`s with the same corpus metadata. Run `LearningCycle013.run_shadow()`.

Target outcome for the controlled weakness:
- baseline is weaker (for example 7/8);
- candidate improves the target metric (for example 8/8);
- decision = `RECOMMEND` only;
- `production_mutations = 0`;
- `can_promote(..., human_approved=False) == False`.

If baseline is already 8/8 for the chosen wording, choose another legitimate unrecognized task-search synonym from a bounded adversarial set; do NOT damage production or alter expected semantics just to force a failure.

## Test E — frozen-corpus attacks
Prove the cycle rejects/raises when:
1. baseline/candidate `corpus_id` differ;
2. `case_set_sha256` differs;
3. case count differs;
4. candidate adds a false-green result;
5. candidate regresses a previously green case.

Required: no scenario reaches promotable recommendation.

## Test F — source-contract anti-learning rule
Feed a source/adapter failure cluster (AS21 unavailable/mapping/source-contract class) to proposal synthesis.

Required:
- it is classified as source-contract/evidence review, not a routing/prompt alias;
- proposal remains non-executable;
- no attempt is made to "learn around" broken source facts.

## Test G — real Core-8 protected regression
Re-run the accepted real-AS21 Core-8 pack from 011K/012.

Required:
- Core-8 = 8/8;
- false-green production controls remain GREEN;
- sprint completeness remains GREEN;
- WMB-30000 Office attachments remain visible unless proven live-data drift;
- AS21 mutations = 0.

## Test H — full regression
Run the full suite and compare with 012 baseline:
- 1176 passed
- 6 failed (known classified debt)
- 11 errors (known environment/legacy debt)

New HIGH production regressions must be zero. New 013 tests must pass.

## Authorization for C2 / Learning Loop 014
Set `READY_FOR_LEARNING_LOOP_014 = YES` iff ALL are true:
- automatic failure clustering/proposal synthesis PASS;
- proposal is non-executable and sandbox-only;
- baseline/candidate use identical frozen corpus/hash;
- candidate demonstrates measurable `task_search` improvement;
- shadow decision is RECOMMEND only;
- human approval boundary remains enforced;
- frozen-corpus mismatch/false-green/regression attacks fail closed;
- source-contract failures are not learned around;
- real Core-8 remains 8/8;
- new HIGH production regressions = 0;
- automatic production mutations = 0;
- AS21 mutations = 0.

## Report
Publish and push:
`qa_reports/LEARNING_LOOP_013_TASK_SEARCH_SELF_IMPROVEMENT.md`

Footer:

```text
ASSIGNMENT_ID = LEARNING_LOOP_013_TASK_SEARCH_SELF_IMPROVEMENT
CURRENT_HEAD = <sha>
AUTO_FAILURE_CLUSTERING_PASS = YES|NO
AUTO_PROPOSAL_SYNTHESIS_PASS = YES|NO
PROPOSAL_NON_EXECUTABLE_PASS = YES|NO
FROZEN_CORPUS_ID = <id>
FROZEN_CASE_SET_SHA256 = <sha256>
BASELINE_TASK_SEARCH_SCORE = <x/y>
CANDIDATE_TASK_SEARCH_SCORE = <x/y>
MEASURABLE_IMPROVEMENT_PASS = YES|NO
SHADOW_DECISION = RECOMMEND|REJECT|INSUFFICIENT_EVIDENCE
HUMAN_APPROVAL_BOUNDARY_PASS = YES|NO
FROZEN_CORPUS_ATTACKS_PASS = YES|NO
SOURCE_CONTRACT_ANTI_LEARNING_PASS = YES|NO
CORE8_AGENT_E2E_PASS = x/8
FALSE_GREEN_CONTROLS_PASS = YES|NO
NEW_HIGH_PRODUCTION_REGRESSIONS = N
AUTOMATIC_PRODUCTION_MUTATIONS = N
AS21_MUTATIONS_DURING_TEST = N
READY_FOR_LEARNING_LOOP_014 = YES|NO
```

After publishing, STOP. Do not start C2/014 and do not promote a candidate.