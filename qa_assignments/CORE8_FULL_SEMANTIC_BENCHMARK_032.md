# Assignment 032 — Full Core-8 Semantic Benchmark

## Purpose

Complete the full unchanged Assignment 029 / Assignment 026 V2 real-data acceptance after Assignment 031 proved the narrow multi-filter and source-backed sprint-membership gate GREEN.

Assignment 031 is narrow-gate evidence only. Its GREEN verdict does not replace this benchmark and does not authorize `READY_TO_RERUN_017_V2 = YES`.

## Fixed role and autonomous execution

GigaCode is QA/tester only. Execute this assignment end to end without asking the repository owner to confirm each step or integration call.

The complete workflow below is pre-authorized, including read-only AS21/SWTR calls, use of the configured semantic LLM, local service restart and health checks, HTTP diagnostics, test execution, Git inspection, and commit/push of the one allowed report.

Ask only if continuing requires an unconfigured credential or permission, an unavoidable platform approval, a write outside the report allowlist, a production/source-data/configuration mutation, a destructive out-of-scope action, or a material scope expansion. Consolidate unavoidable platform approval prompts.

Do not modify production code, prompts, adapters, skills, tests, fixtures, acceptance runners, configuration, learning state, AS21/SWTR data, `.env`, or historical QA reports/results. Do not repair defects and do not weaken the oracle.

## 1. Git and runtime preflight

1. Switch to and pull `feat/core8-real-query-hardening-v2` with `--ff-only`.
2. Record `START_HEAD = git rev-parse HEAD`.
3. Verify that both commits are ancestors of `START_HEAD`:
   - production commit `319ae1e85311f3123c44c2dd0118b843172aef4d`;
   - Assignment 031 report commit `b5ac573`.
4. Read this assignment, Assignment 029, and Assignment 026 completely.
5. Restart Task API and PO Agent from `START_HEAD`. Record old and new PIDs, executable paths, commands, ports, health checks, and the HEAD used by the running processes.
6. Use:
   - real read-only AS21/SWTR;
   - `PO_AGENT_AS21_MODE=task-api`;
   - working semantic LLM endpoint with `/openai/v1`;
   - production semantic interpreter;
   - no `FakeAS21Adapter` for any acceptance verdict.

If services cannot be restarted because of an environment restriction, do not claim a production failure. Publish a `BLOCKED` report containing the exact manual action required.

## 2. Mandatory architecture preflight

Re-run all six Assignment 026 production architecture checks and preserve evidence from the actual running process/import graph:

1. `EvidenceValidatedProductionTaskApiAS21Adapter` is active.
2. `LLMFirstSemanticInterpreter` wrapped by `ConversationAwareSemanticInterpreter` is active.
3. `ProductionEntityResolverV2` is active.
4. `SemanticCorrectionRuntimeV2` is active.
5. `Core8SemanticPrecisionInterpreter`, `deterministic_core8_frame`, and legacy `DeterministicRouter` are not the task-api natural-language path.
6. Semantic LLM unavailability fails closed and does not return a regex-routed business result.

A failed preflight makes the final gate RED, but evidence collection continues when safe.

## 3. Execute the unchanged benchmark

Run without editing:

- the focused tests required by Assignment 029;
- `qa_026_test_runner_v2.py`;
- every original query and scenario from Assignment 026 sections A through J;
- every focused invariant from Assignment 029;
- the full relevant regression suite.

Do not change query wording, expected semantics, sessions, source selectors, pass criteria, runner code, fixtures, or test code.

The runner may overwrite its historical machine-readable result path locally. That generated modification is test output only: do not stage or commit it, and do not modify the runner to redirect it.

## 4. Independent hydrated oracle is authoritative

Runner PASS flags are advisory and cannot determine the final verdict. For every factual task query in sections A–J and the Core-8 smoke:

1. Derive candidate task keys from the complete relevant source facade, exhausting pagination.
2. Read every candidate task key individually from the authoritative SWTR task unit.
3. Extract source-backed task key, assignee identity/login, raw and normalized status, space/product, sprint relation, and every other requested selector.
4. Apply every requested constraint to those individually hydrated facts.
5. Compare exact sets:
   - `ORACLE_KEYS`;
   - `AGENT_KEYS`;
   - `MISSING_KEYS = ORACLE_KEYS - AGENT_KEYS`;
   - `EXTRA_KEYS = AGENT_KEYS - ORACLE_KEYS`.

Never use the agent result, answer prose, HTTP 200, count equality, a previous agent result, sprint-facade attributes, or an echoed identifier as oracle evidence.

`COMPLETED + empty` is PASS only when the independently hydrated complete oracle is empty. Any task violating one requested selector is a false green. Any requested selector lost before capability execution is a silent slot drop even if returned keys happen to match.

## 5. Required benchmark coverage

Execute all original Assignment 026 cases exactly:

- A1–A4 current source anchors;
- B1–B8 paraphrase invariance;
- C1–C5 person/product/status robustness;
- D1–D6 multi-filter preservation;
- E1–E4 explicit identifier safety;
- F1–F6 correction/recheck loop using the required same-session behavior;
- G1–G5 typo/reorder robustness;
- H1–H5 ambiguity and fail-closed;
- at least two materially different real queries for each of the eight Core-8 skills;
- focused and full regression suites from section J and Assignment 029.

For each query record:

- exact original query and session id;
- raw semantic frame and semantic audit result;
- grounded frame;
- capability name and complete capability args;
- response status and trace/error code;
- candidate facade keys and authoritative per-task hydrated relation;
- `ORACLE_KEYS`, `AGENT_KEYS`, `MISSING_KEYS`, and `EXTRA_KEYS`;
- source evidence required for analytical Core-8 results.

For F1–F6 also record previous trace, correction/recheck trace, preserved/changed slots, `source_recheck_performed`, and `persistent_skill_mutation`.

If space prevents placing every raw payload inline, include a compact per-query table plus reproducible evidence paths/trace identifiers. Do not omit exact-set diffs.

## 6. Regression classification

Classify each failure into exactly one category:

- `NEW_PRODUCTION_REGRESSION`;
- `STALE_TEST_EXPECTATION`;
- `TEST_INFRA/MOCK_DEFECT`;
- `PRE_EXISTING_NONPRODUCTION_DEBT`.

Investigate `test_conversation_context_is_supplied_to_next_semantic_turn` separately if it fails. Do not let a stale/mock classification erase a failure in the real correction benchmark, and do not let a mock-only failure falsify a production gate without evidence.

## 7. Hard acceptance gate

`032_FULL_BENCHMARK = GREEN` and `READY_TO_RERUN_017_V2 = YES` are permitted only when all are true:

- production architecture preflight = 6/6;
- the complete Assignment 026/029 benchmark was actually executed;
- paraphrase invariance = 8/8;
- person/product/status = 5/5;
- multi-filter = 6/6;
- explicit identifiers = 4/4;
- correction loop = 6/6;
- typo/reorder = 5/5;
- fail-closed = 5/5;
- Core-8 real-data smoke = 8/8;
- every factual task verdict uses exact equality to the independent hydrated oracle;
- `FALSE_GREEN_COUNT = 0`;
- `SILENT_SLOT_DROP_COUNT = 0`;
- `QUERY_HTTP_500_COUNT = 0`;
- `NEW_HIGH_PRODUCTION_REGRESSIONS = 0`;
- no acceptance verdict depends on `FakeAS21Adapter` or a new phrase/regex route.

If any required case was not executed, set `026_FULLY_EXECUTED = NO`, `032_FULL_BENCHMARK` to `RED` or `BLOCKED` as evidence warrants, and `READY_TO_RERUN_017_V2 = NO`.

## 8. Report

Create only:

`qa_reports/CORE8_FULL_SEMANTIC_BENCHMARK_032.md`

The report must contain:

- branch, `START_HEAD`, service PIDs/ports/process paths;
- production wiring and real-source evidence;
- all architecture preflight evidence;
- execution commands and completion evidence;
- the complete per-case result table and hydrated oracle evidence;
- every exact key-set diff and mismatch trace;
- correction-loop traces;
- Core-8 source/formula evidence;
- regression failure classification;
- final hard-gate table.

End with these metrics exactly:

```text
032_FULL_BENCHMARK = GREEN|RED|BLOCKED
PRODUCTION_PREFLIGHT = x/6
026_FULLY_EXECUTED = YES|NO
CORE8_REAL_DATA = x/8
PARAPHRASE_INVARIANCE = x/8
PERSON_PRODUCT_STATUS = x/5
MULTIFILTER_PRESERVATION = x/6
STRUCTURAL_ID_INTEGRITY = x/4
CORRECTION_LOOP = x/6
TYPO_REORDER_ROBUSTNESS = x/5
FAIL_CLOSED = x/5
FALSE_GREEN_COUNT = n
SILENT_SLOT_DROP_COUNT = n
SEMANTIC_CRUTCH_COUNT_PRODUCTION = n
QUERY_HTTP_500_COUNT = n
NEW_HIGH_PRODUCTION_REGRESSIONS = n
READY_TO_RERUN_017_V2 = YES|NO
```

## 9. Git allowlist and stop rule

Commit and push only:

`qa_reports/CORE8_FULL_SEMANTIC_BENCHMARK_032.md`

Do not stage or commit the runner-generated historical 026 JSON, historical reports, logs, production files, tests, fixtures, configuration, `.env`, or any other path.

Before commit:

```bash
git add -- qa_reports/CORE8_FULL_SEMANTIC_BENCHMARK_032.md
git diff --cached --name-only
```

The staged list must contain exactly one path: the 032 report. The commit subject must start with:

`qa: CORE8_FULL_SEMANTIC_BENCHMARK_032`

After push, stop and return the report commit SHA, final verdict, and complete report text.
