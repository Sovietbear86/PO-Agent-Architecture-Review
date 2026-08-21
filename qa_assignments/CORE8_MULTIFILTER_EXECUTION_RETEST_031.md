# QA Assignment 031 — Multi-filter Execution and Sprint Fail-closed Retest

## Purpose

Verify production commit `319ae1e85311f3123c44c2dd0118b843172aef4d`, created after Assignment 030 reported that `sprint_id` was preserved semantically but silently lost when `task_search_assignee` executed.

The fix must prove two execution invariants:

1. every task-search intent with two or more independent filters executes through `task.search.composite` with all grounded constraints;
2. any `sprint_id` is source-revalidated at the final execution boundary, so an unproven sprint cannot return `COMPLETED + empty`.

Do not weaken or replace the Assignment 030 oracle.

## QA-only role and autonomous authorization

GigaCode is tester only. Do not modify production code, prompts, adapters, tests, fixtures, runners, configuration, `.env`, AS21/SWTR data or learning state. Do not repair defects.

The owner pre-authorizes the entire in-scope QA workflow: read-only AS21/SWTR and LLM calls, local service restarts, HTTP diagnostics, tests, Git pull/inspection, and commit/push of the allowed report. Execute continuously without asking for confirmation after each step or integration. Ask only for genuinely missing authority/credentials, unavoidable platform approval, destructive or out-of-scope action, external write beyond the report, or material scope expansion. Batch unavoidable approval prompts.

## Mandatory preflight

1. Switch to `feat/core8-real-query-hardening-v2`.
2. Run `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
3. Record `START_HEAD=$(git rev-parse HEAD)`.
4. Re-read `GIGACODE_NEXT_ACTION.md` and this file from `START_HEAD`.
5. Confirm `319ae1e85311f3123c44c2dd0118b843172aef4d` is an ancestor of `START_HEAD`.
6. Confirm active assignment 031 and report target `qa_reports/CORE8_MULTIFILTER_EXECUTION_RETEST_031.md`.

If a check fails, write a BLOCKED 031 report with exact evidence and stop. Never fall back to Assignment 030 or another historical assignment.

## Prove a fresh runtime

Assignment 030 did not record process identity strongly enough. Before stopping services, record listeners/PIDs for ports 8003 and 8004. Stop them and prove both ports are free. Start Task API and PO Agent from `START_HEAD`, then record:

- new PID for each service;
- listening port;
- process start time and command line;
- process working directory;
- imported path of `po_agent.harness.dialogue_runtime`;
- proof that old and new PIDs differ, or proof there was no old listener.

Use real AS21/SWTR, `PO_AGENT_AS21_MODE=task-api`, the working `/openai/v1` LLM endpoint and production semantic interpreter. FakeAS21Adapter cannot support acceptance conclusions.

If restart is impossible, report `MANUAL_ACTION_REQUIRED` with exact commands. Do not test a stale process and do not call that a production failure.

## Independent hydrated oracle

For every sprint query:

1. obtain candidate keys from the sprint-list facade;
2. read every candidate via the individual SWTR task unit;
3. extract key, assignee/login, product/space, status and `scrum_board_plugin_sprint`;
4. retain only exact authoritative sprint membership;
5. apply assignee and other filters after hydration;
6. exhaust pagination and compare exact key sets.

Never use facade echo, agent output, response prose or counts as the oracle.

## Narrow cases

For each case capture raw semantic frame, semantic audit, grounded frame, selected skill, executed capability ID, complete capability args, source oracle, response status and exact key diff.

### Case A — specialized assignee intent plus sprint

Query: `Покажи задачи Garanin.R.V в DMS-SPRNT-1`

Required:

- `member_login/assignee=Garanin.R.V` survives;
- `sprint_id=DMS-SPRNT-1` survives;
- `product=DMS`, if produced by semantic grounding, survives;
- executed capability is `task.search.composite` even if selected skill is `task-search-assignee`;
- capability args contain every grounded constraint;
- `AGENT_KEYS == ORACLE_KEYS`;
- every returned task has authoritative `scrum_board_plugin_sprint=DMS-SPRNT-1`;
- foreign sprint count is zero.

### Case B — absent assignee plus sprint

Query: `Покажи задачи Moiseev.A.N. в DMS-SPRNT-2`

Apply the same invariants. If the identity or exact result is absent in source truth, require source-backed clarification/fail-closed or exact empty result only when both identity and sprint have independently been proven. Never return OLP tasks.

### Case C — unproven sprint

Query: `Покажи задачи в DMS-SPRNT-999999`

Required: `NEEDS_CLARIFICATION` or source-backed `FAILED`, with `unproven_sprint` or equivalent trace. `COMPLETED + empty`, facade echo and arbitrary tasks are forbidden.

### Case D — focused regression proof

Run at minimum:

```bash
cd po-agent-platform-v2
python3 -m pytest \
  tests/test_harness_dialogue_runtime.py::test_grounded_composite_search_applies_all_filters_not_only_first_one \
  tests/test_harness_dialogue_runtime.py::test_specific_assignee_intent_with_sprint_uses_composite_execution \
  tests/test_harness_dialogue_runtime.py::test_final_execution_boundary_rejects_unproven_sprint \
  tests/test_explicit_sprint_id_precision.py::test_echoed_invalid_sprint_fails_closed_without_source_corpus \
  tests/test_explicit_sprint_id_precision.py::test_echoed_valid_sprint_with_source_corpus_is_preserved -q
```

Classify all broader regression failures against the known baseline. Do not mix missing local credentials/services with production regressions.

## Gate and full benchmark

031 narrow gate is GREEN only if Cases A–D pass, `FOREIGN_SPRINT_TASK_COUNT=0`, `FALSE_GREEN_COUNT=0`, `SILENT_SLOT_DROP_COUNT=0` and `QUERY_HTTP_500_COUNT=0`.

If narrow gate is not GREEN, do not run the full benchmark. Publish the 031 report and stop.

If narrow gate is GREEN, execute the complete unchanged Assignment 029/026 V2 benchmark: Core-8 real-data, B1–B8 paraphrase invariance, person/product/status robustness, multi-filter preservation, explicit identifier safety, correction loop F1–F6, ambiguity/fail-closed, architecture preflight and relevant regressions. Do not tune prompts, queries, oracle or acceptance criteria.

## Report and metrics

Create only:

`qa_reports/CORE8_MULTIFILTER_EXECUTION_RETEST_031.md`

Report these metrics exactly:

```text
031_NARROW_GATE = GREEN|RED|BLOCKED
031_CASE_A_EXACT_SET = PASS|FAIL|BLOCKED
031_CASE_B_EXACT_SET = PASS|FAIL|BLOCKED
031_COMPOSITE_DISPATCH = PASS|FAIL|BLOCKED
031_UNPROVEN_SPRINT_FAILCLOSED = PASS|FAIL|BLOCKED
FRESH_RUNTIME_PROVEN = YES|NO
FOREIGN_SPRINT_TASK_COUNT = n
026_FULLY_EXECUTED = YES|NO
CORE8_REAL_DATA = x/8
PARAPHRASE_INVARIANCE = x/8
CORRECTION_LOOP = x/6
MULTIFILTER_PRESERVATION = x/y
FALSE_GREEN_COUNT = n
SILENT_SLOT_DROP_COUNT = n
SEMANTIC_CRUTCH_COUNT_PRODUCTION = n
QUERY_HTTP_500_COUNT = n
NEW_HIGH_PRODUCTION_REGRESSIONS = n
READY_TO_RERUN_017_V2 = YES|NO
```

`READY_TO_RERUN_017_V2=YES` requires full GREEN, complete 026 execution, zero false greens and zero silent slot drops.

Stage by exact path, verify `git diff --cached --name-only`, commit with subject beginning `qa: CORE8_MULTIFILTER_EXECUTION_RETEST_031`, push the report only, return commit SHA/verdict/full report and stop.
