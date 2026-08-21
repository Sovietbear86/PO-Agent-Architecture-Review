# Assignment 039 — 017 V2 Batch TS-01..TS-12 Retest After Task-Search Boundary Fix

## Purpose

Assignment 038 retested `task_search TS-01..TS-12` and remained RED.

Key 038 defects to verify:

1. atomic `task.search_*` capabilities can bypass hardened source-backed filtering;
2. foreign-product/foreign-sprint tasks can appear in task-search results;
3. product/person/status/current-sprint slots can be lost or converted into clarification/failure despite source-backed oracle evidence;
4. `COMPLETED + empty` and `NEEDS_CLARIFICATION` must not hide a non-empty oracle set.

This assignment retests the exact same TS-01..TS-12 batch after the latest production task-search boundary fix at `START_HEAD`.

This is still a batch-level QA run, not a Gate E release decision. Even if this batch is GREEN, `READY_TO_RESUME_GATE_E` remains `NO` until all 017 V2 batches are complete and a final rollup accepts the full matrix.

GigaCode is QA/tester only.

## Repository

Repository:

`Sovietbear86/PO-Agent-Architecture-Review`

Branch:

`feat/core8-real-query-hardening-v2`

Expected report:

`qa_reports/CORE8_017V2_BATCH_TS01_TS12_RETEST_039.md`

Do not overwrite historical reports.

## Mandatory Git preflight

Before starting services or tests:

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `git rev-parse HEAD` as `START_HEAD`.
4. Re-read `GIGACODE_NEXT_ACTION.md` and this assignment from `START_HEAD`.
5. Read all files below completely:
   - `qa_assignments/CORE8_017V2_BATCH_TS01_TS12_RETEST_039.md`
   - `qa_reports/CORE8_017V2_BATCH_TS01_TS12_RETEST_038.md`
   - `qa_assignments/CORE8_017V2_BATCH_TS01_TS12_RETEST_038.md`
   - `qa_assignments/CORE8_017V2_BATCH_TS01_TS12_037.md`
   - `qa_reports/CORE8_017V2_BATCH_TS01_TS12_037.md`
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017.md`
   - `qa_reports/CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036.md`

Verify required ancestor commits:

```bash
git merge-base --is-ancestor 319ae1e85311f3123c44c2dd0118b843172aef4d "$START_HEAD"
git merge-base --is-ancestor 940ee44939dcbca14a7583e167b096525f0e509f "$START_HEAD"
git merge-base --is-ancestor 14ba376e7cdcb90cae812a03b05ccb6e9bb97609 "$START_HEAD"
git merge-base --is-ancestor 0a604d956418ebec2941aadec0511a70ac9d1478 "$START_HEAD"
git merge-base --is-ancestor 6cb0ad7fa175863f8c8d0807a1504fe1e35bd6aa "$START_HEAD"
git merge-base --is-ancestor efece8d4e82dea6082d80f005fe13511db7397c7 "$START_HEAD"
```

If any check fails, write the 039 report with `039_BATCH_VERDICT = BLOCKED`, exact mismatch evidence, and stop.

Record:

```text
PRODUCTION_FIX_UNDER_TEST = <START_HEAD>
```

## Autonomous execution — no step-by-step confirmation

The repository owner has pre-authorized this QA batch. Execute it end to end without asking for confirmation after each step, before each integration call, before each TS case, before local service restart, or before commit/push of the allowed report.

No additional conversational confirmation is required for:

- read-only AS21/SWTR calls;
- configured semantic LLM calls;
- local service restart/health checks;
- HTTP diagnostics;
- test runs;
- Git inspection;
- `git switch`;
- `git pull --ff-only`;
- commit/push of the explicitly allowed QA report.

Do not pause with questions such as:

- “continue?”;
- “run the integration?”;
- “restart the service?”;
- “run the next TS case?”;
- “apply this QA-helper change?”;
- “commit the report?”.

Ask only if continuing requires an unconfigured credential/permission, an unavoidable platform approval, a write outside the report allowlist, a production/source-data/configuration mutation, a destructive out-of-scope action, or a material scope expansion.

## Fixed role and prohibitions

Do not modify or commit:

- production code;
- prompts;
- adapters;
- tests;
- fixtures;
- QA runners / acceptance runners;
- configuration;
- AS21/SWTR data;
- learning state;
- historical reports;
- roadmap files.

If a local helper/runner cannot parse the current response shape, record `QA_INFRA_BLOCKED` or the exact helper limitation in the report. Do not commit helper changes. Do not repair discovered production defects.

Do not weaken or reinterpret the oracle to make the batch GREEN.

## Runtime

Restart both services from `START_HEAD`:

- Task API;
- PO Agent.

Use:

- real AS21/SWTR;
- `PO_AGENT_AS21_MODE=task-api`;
- working semantic LLM endpoint with `/openai/v1`;
- production semantic interpreter;
- production entity resolver;
- production correction runtime.

Do not use `FakeAS21Adapter` for acceptance evidence.

The 039 report must include old/new PIDs, ports, commands, health responses, and proof that services were restarted from `START_HEAD`.

If services cannot be restarted due to environment limits, do not report production FAIL. Report `039_BATCH_VERDICT = BLOCKED`, exact manual restart commands, and stop.

## Exact batch scope

Execute exactly these canonical queries from `CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017.md`:

```text
TS-01 `Покажи задачи Гаранина.`
TS-02 `Покажи задачи Калачанова.`
TS-03 `Покажи задачи по DMS.`
TS-04 `Покажи задачи по OLP.`
TS-05 `Покажи задачи текущего спринта DMS.`
TS-06 `Покажи задачи текущего спринта OLP.`
TS-07 `Покажи задачи со статусом Open в DMS.`
TS-08 `Покажи закрытые задачи Гаранина.`
TS-09 `Покажи задачи Гаранина по DMS.`
TS-10 `Покажи задачи Гаранина по OLP.`
TS-11 `Покажи задачи Калачанова по WMB.`
TS-12 `Покажи открытые задачи Гаранина.`
```

Do not change query wording. Do not substitute different people, products or statuses.

## Oracle and verdict rules

For each TS case:

1. Build an independent source-backed oracle.
2. Hydrate every candidate through authoritative AS21/SWTR reads.
3. Prove assignee, product/space, sprint, status and other filters from source fields when relevant.
4. Compare exact task-key sets for task-list results.
5. Treat `COMPLETED + 0` as PASS only if the independent oracle proves the final set is empty.
6. Treat `NEEDS_CLARIFICATION` as `CLARIFICATION_PASS` only when the selector is genuinely ambiguous or unsupported by approved source/status convention and the clarification is targeted.
7. Agent output must never be used as oracle evidence.

Agreement between two broken mappings is not PASS.

## Required targeted checks

- `TASK_SEARCH_ATOMIC_BOUNDARY = PASS` only if `task.search`, `task.search_assignee`, `task.search_status`, `task.search_sprint`, `task.search_release`, and `task.search_product` all preserve and apply provided task filters.
- `FOREIGN_TASK_COUNT = 0` across all 12 cases.
- `CURRENT_SPRINT_RESOLUTION = PASS` only if TS-05/TS-06 resolve current sprint from source-backed current-sprint evidence or correctly fail closed when source cannot prove it.
- `STATUS_OPEN_GROUNDING = PASS` only if TS-07 handles exact `Open` according to source/status ontology.
- `STATUS_CLOSED_COMPLETED_GROUNDING = PASS` only if TS-08 maps `закрытые` to source-backed completed/terminal semantics and exact oracle set.
- `OPEN_TASK_SET_GROUNDING = PASS` only if TS-12 maps `открытые` to source-backed not-completed/open-task semantics and exact oracle set.
- `PERSON_PRODUCT_GROUNDING = PASS` only if TS-09/TS-10/TS-11 preserve both person and product constraints.

## Required per-ID evidence table

The report must include one row for every TS-01..TS-12 case with:

- `ID`;
- exact `query`;
- `executed = YES|NO`;
- `response_status`;
- `raw semantic frame` or trace reference;
- `grounded constraints`;
- `capability`;
- `capability_args`;
- `agent_keys`;
- `oracle_keys`;
- `missing_keys`;
- `extra_keys`;
- `foreign_keys`;
- `verdict = PASS|FAIL|BLOCKED|CLARIFICATION_PASS|LIVE_DATA_DRIFT_EXCEPTION`;
- short evidence note.

Missing row means `NOT_EXECUTED`.

## Batch GREEN rule

`039_BATCH_VERDICT = GREEN` only if all are true:

- all 12 TS cases have per-ID rows;
- `TS_EXECUTED = 12/12`;
- `TS_FAIL = 0`;
- `TS_NOT_EXECUTED = 0`;
- every empty result is proven by independent oracle;
- every clarification pass is targeted and justified;
- `TASK_SEARCH_ATOMIC_BOUNDARY = PASS`;
- `FOREIGN_TASK_COUNT = 0`;
- `CURRENT_SPRINT_RESOLUTION = PASS`;
- `STATUS_OPEN_GROUNDING = PASS`;
- `STATUS_CLOSED_COMPLETED_GROUNDING = PASS`;
- `OPEN_TASK_SET_GROUNDING = PASS`;
- `PERSON_PRODUCT_GROUNDING = PASS`;
- `ORACLE_PREFLIGHT_PASS = YES`;
- `ORACLE_INDEPENDENCE_PASS = YES`;
- `FALSE_EMPTY_HIGH_COUNT = 0`;
- `FALSE_GREEN_HIGH_COUNT = 0`;
- `SOURCE_CONTRACT_OR_GROUNDING_DEFECTS = 0`;
- `NEW_HIGH_PRODUCTION_REGRESSIONS = 0`;
- `AS21_MUTATIONS_DURING_TEST = 0`;
- footer metrics match the per-ID table.

If any condition is not satisfied, the correct verdict is RED or BLOCKED, not GREEN.

## Required report

Create:

`qa_reports/CORE8_017V2_BATCH_TS01_TS12_RETEST_039.md`

Footer:

```text
ASSIGNMENT_ID = CORE8_017V2_BATCH_TS01_TS12_RETEST_039
CURRENT_HEAD = <sha>
PRODUCTION_FIX_UNDER_TEST = <START_HEAD>
PREVIOUS_038_REPORT_COMMIT = efece8d4e82dea6082d80f005fe13511db7397c7
BATCH_SCOPE = TS-01..TS-12
TS_REQUIRED = 12
TS_EXECUTED = x/12
TS_PASS = n
TS_FAIL = n
TS_NOT_EXECUTED = n
TS_CLARIFICATION_PASS = n
TASK_SEARCH_ATOMIC_BOUNDARY = PASS|FAIL|BLOCKED
FOREIGN_TASK_COUNT = n
CURRENT_SPRINT_RESOLUTION = PASS|FAIL|BLOCKED
STATUS_OPEN_GROUNDING = PASS|FAIL|BLOCKED
STATUS_CLOSED_COMPLETED_GROUNDING = PASS|FAIL|BLOCKED
OPEN_TASK_SET_GROUNDING = PASS|FAIL|BLOCKED
PERSON_PRODUCT_GROUNDING = PASS|FAIL|BLOCKED
ORACLE_PREFLIGHT_PASS = YES|NO
ORACLE_INDEPENDENCE_PASS = YES|NO
FALSE_EMPTY_HIGH_COUNT = n
FALSE_GREEN_HIGH_COUNT = n
SOURCE_CONTRACT_OR_GROUNDING_DEFECTS = n
NEW_HIGH_PRODUCTION_REGRESSIONS = n
AS21_MUTATIONS_DURING_TEST = 0
039_BATCH_VERDICT = GREEN|RED|BLOCKED
READY_TO_RESUME_GATE_E = NO
```

`READY_TO_RESUME_GATE_E` must remain `NO` in this batch report.

## Commit and push

Commit and push only:

`qa_reports/CORE8_017V2_BATCH_TS01_TS12_RETEST_039.md`

Before commit:

```bash
git add -- qa_reports/CORE8_017V2_BATCH_TS01_TS12_RETEST_039.md
git diff --cached --name-only
```

The staged file list must contain exactly the allowed 039 report.

Commit subject must start with:

`qa: CORE8_017V2_BATCH_TS01_TS12_RETEST_039`

After pushing the report, stop and return:

1. report commit SHA;
2. final verdict;
3. complete report contents.
