# Assignment 037 — 017 V2 Batch TS-01..TS-12 Evidence Run

## Purpose

Assignment 036 correctly found that the full 122-case 017 V2 matrix cannot be executed reliably inside the current single-run timeout window. The next step is to execute the canonical 017 V2 matrix in small, evidence-complete batches.

Assignment 037 covers only:

```text
task_search TS-01..TS-12
```

This is a batch-level QA run, not a Gate E release decision. Even if this batch is GREEN, `READY_TO_RESUME_GATE_E` remains `NO` until all 017 V2 batches are complete and a final rollup accepts the full matrix.

GigaCode is QA/tester only.

## Repository

Repository:

`Sovietbear86/PO-Agent-Architecture-Review`

Branch:

`feat/core8-real-query-hardening-v2`

Expected report:

`qa_reports/CORE8_017V2_BATCH_TS01_TS12_037.md`

Do not overwrite historical reports.

## Mandatory Git preflight

Before starting services or tests:

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `git rev-parse HEAD` as `START_HEAD`.
4. Re-read `GIGACODE_NEXT_ACTION.md` and this assignment from `START_HEAD`.
5. Read all files below completely:
   - `qa_assignments/CORE8_017V2_BATCH_TS01_TS12_037.md`
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017.md`
   - `qa_reports/CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036.md`

Verify required ancestor commits:

```bash
git merge-base --is-ancestor 319ae1e85311f3123c44c2dd0118b843172aef4d "$START_HEAD"
git merge-base --is-ancestor 940ee44939dcbca14a7583e167b096525f0e509f "$START_HEAD"
git merge-base --is-ancestor 14ba376e7cdcb90cae812a03b05ccb6e9bb97609 "$START_HEAD"
```

If any check fails, write the 037 report with `037_BATCH_VERDICT = BLOCKED`, exact mismatch evidence, and stop.

## Autonomous execution — no step-by-step confirmation

The repository owner has pre-authorized this QA batch. Execute it end to end without asking for confirmation after each step, before each integration call, or before each test.

No additional conversational confirmation is required for read-only AS21/SWTR calls, configured semantic LLM calls, local service restart/health checks, HTTP diagnostics, test runs, Git inspection, or commit/push of the explicitly allowed QA report.

Do not pause with questions such as “continue?”, “run the integration?”, “restart the service?”, “run the next TS case?” or “commit the report?”.

Ask only if continuing requires an unconfigured credential/permission, an unavoidable platform approval, a write outside the report allowlist, a production/source-data/configuration mutation, a destructive out-of-scope action, or a material scope expansion.

## Fixed role and prohibitions

Do not modify:

- production code;
- prompts;
- adapters;
- tests;
- fixtures;
- acceptance runners;
- configuration;
- AS21/SWTR data;
- learning state;
- historical reports;
- roadmap files.

Do not repair discovered defects. Do not weaken or reinterpret the oracle to make the batch GREEN.

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

The 037 report must include old/new PIDs, ports, commands, health responses, and proof that services were restarted from `START_HEAD`.

If services cannot be restarted due to environment limits, do not report production FAIL. Report `037_BATCH_VERDICT = BLOCKED`, exact manual restart commands, and stop.

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

Do not change query wording. Do not substitute different people, products or statuses unless the canonical assignment explicitly contains a placeholder. These 12 do not contain placeholders.

## Oracle and verdict rules

For each TS case:

1. Build an independent source-backed oracle.
2. Hydrate every candidate through authoritative AS21/SWTR reads.
3. Prove assignee, product/space, sprint, status and other filters from source fields when relevant.
4. Compare exact task-key sets for task-list results.
5. Treat `COMPLETED + 0` as PASS only if the independent oracle proves the final set is empty.
6. Treat `NEEDS_CLARIFICATION` as `CLARIFICATION_PASS` only when the selector is genuinely ambiguous or unsupported by the approved source/status convention and the clarification is targeted.
7. Agent output must never be used as oracle evidence.

Agreement between two broken mappings is not PASS.

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
- `verdict = PASS|FAIL|BLOCKED|CLARIFICATION_PASS|LIVE_DATA_DRIFT_EXCEPTION`;
- short evidence note.

Missing row means `NOT_EXECUTED`.

## Batch GREEN rule

`037_BATCH_VERDICT = GREEN` only if all are true:

- all 12 TS cases have per-ID rows;
- `TS_EXECUTED = 12/12`;
- `TS_FAIL = 0`;
- `TS_NOT_EXECUTED = 0`;
- every empty result is proven by independent oracle;
- every clarification pass is targeted and justified;
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

`qa_reports/CORE8_017V2_BATCH_TS01_TS12_037.md`

Footer:

```text
ASSIGNMENT_ID = CORE8_017V2_BATCH_TS01_TS12_037
CURRENT_HEAD = <sha>
036_REPORT_COMMIT = 14ba376e7cdcb90cae812a03b05ccb6e9bb97609
BATCH_SCOPE = TS-01..TS-12
TS_REQUIRED = 12
TS_EXECUTED = x/12
TS_PASS = n
TS_FAIL = n
TS_NOT_EXECUTED = n
TS_CLARIFICATION_PASS = n
ORACLE_PREFLIGHT_PASS = YES|NO
ORACLE_INDEPENDENCE_PASS = YES|NO
FALSE_EMPTY_HIGH_COUNT = n
FALSE_GREEN_HIGH_COUNT = n
SOURCE_CONTRACT_OR_GROUNDING_DEFECTS = n
NEW_HIGH_PRODUCTION_REGRESSIONS = n
AS21_MUTATIONS_DURING_TEST = 0
037_BATCH_VERDICT = GREEN|RED|BLOCKED
READY_TO_RESUME_GATE_E = NO
```

`READY_TO_RESUME_GATE_E` must remain `NO` in this batch report.

## Commit and push

Commit and push only:

`qa_reports/CORE8_017V2_BATCH_TS01_TS12_037.md`

Before commit:

```bash
git add -- qa_reports/CORE8_017V2_BATCH_TS01_TS12_037.md
git diff --cached --name-only
```

The staged file list must contain exactly the allowed 037 report.

Commit subject must start with:

`qa: CORE8_017V2_BATCH_TS01_TS12_037`

After push, stop and return:

1. report commit SHA;
2. final verdict;
3. complete report contents.
