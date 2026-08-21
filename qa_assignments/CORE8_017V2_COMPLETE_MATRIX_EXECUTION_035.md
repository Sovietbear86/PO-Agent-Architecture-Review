# Assignment 035 — Complete 017 V2 Matrix Execution

## Purpose

Assignment 034 correctly invalidated Assignment 033's GREEN verdict, but did not execute the required complete 017 V2 rerun. It reported:

```text
034_VERDICT = BLOCKED
033_GREEN_VERDICT_VALID = NO
033_READY_TO_RESUME_GATE_E_VALID = NO
034_RERUN_EXECUTED = NO
CORE8_REAL_QUERY_HARDENING_GREEN = NO
READY_TO_RESUME_GATE_E = NO
```

Report commit:

`beee3fcc684d8eb8cfafb0f295f8a0706a486d3a`

Assignment 035 is the mandatory full execution of the canonical 017 V2 matrix. The size of the matrix is not a blocker. The repository owner has already authorized this full QA run.

GigaCode is QA/tester only.

## Repository

Repository:

`Sovietbear86/PO-Agent-Architecture-Review`

Branch:

`feat/core8-real-query-hardening-v2`

Expected report:

`qa_reports/CORE8_017V2_COMPLETE_MATRIX_EXECUTION_035.md`

Do not overwrite historical reports:

- `qa_reports/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
- `qa_reports/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2_RERUN_033.md`
- `qa_reports/CORE8_017V2_VERDICT_INTEGRITY_RETEST_034.md`

## Mandatory Git preflight

Before starting services or tests:

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `git rev-parse HEAD` as `START_HEAD`.
4. Re-read `GIGACODE_NEXT_ACTION.md` and this assignment from `START_HEAD`.
5. Read all files below completely:
   - `qa_assignments/CORE8_017V2_COMPLETE_MATRIX_EXECUTION_035.md`
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017.md`
   - `qa_assignments/CORE8_CORRECTION_LOOP_ADDENDUM_017A.md`
   - `qa_reports/CORE8_017V2_VERDICT_INTEGRITY_RETEST_034.md`

Verify required ancestor commits:

```bash
git merge-base --is-ancestor 319ae1e85311f3123c44c2dd0118b843172aef4d "$START_HEAD"
git merge-base --is-ancestor 940ee44939dcbca14a7583e167b096525f0e509f "$START_HEAD"
git merge-base --is-ancestor 7a46762fd02cf43633e4fb5c18af2582941d5366 "$START_HEAD"
git merge-base --is-ancestor beee3fcc684d8eb8cfafb0f295f8a0706a486d3a "$START_HEAD"
```

If any check fails, write the 035 report with `035_VERDICT = BLOCKED`, exact mismatch evidence, and stop.

## Autonomous execution — no step-by-step confirmation

The repository owner has pre-authorized the complete QA workflow defined by this entrypoint and the active assignment. Execute it end to end without asking for confirmation after each step, before each integration call, or before each test category.

No additional conversational confirmation is required for:

- read-only AS21/SWTR calls;
- configured semantic LLM calls;
- local service restart/health checks;
- HTTP diagnostics;
- test runs;
- `git switch`;
- `git pull --ff-only`;
- Git inspection;
- commit/push of the explicitly allowed QA report.

Do not pause with questions such as “continue?”, “run the integration?”, “restart the service?”, “run the next category?”, “execute all 122 cases?” or “commit the report?”.

Ask only if continuing requires an unconfigured credential/permission, an unavoidable platform approval, a write outside the report allowlist, a production/source-data/configuration mutation, a destructive out-of-scope action, or a material scope expansion. Consolidate unavoidable prompts to the minimum number possible.

The following are not valid blockers:

- the matrix has 107+ functional tests;
- CL-01..CL-15 take time;
- the run requires multiple batches;
- a previous report already identified that the full matrix is needed;
- the tester would prefer "manual action" because the suite is long.

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

Do not repair discovered defects. Do not weaken or reinterpret the oracle to make the gate GREEN.

## Required runtime

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

The 035 report must include old/new PIDs, ports, commands, health responses, and proof that services were restarted from `START_HEAD`.

If services cannot be restarted due to environment limits, do not report production FAIL. Report `035_VERDICT = BLOCKED`, exact manual restart commands, and stop.

## Mandatory complete scope

Execute the canonical 017 V2 suite completely and unchanged:

- `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
- `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017.md`
- `qa_assignments/CORE8_CORRECTION_LOOP_ADDENDUM_017A.md`

The required functional scope is at least:

```text
task_search TS-01..TS-36 = 36
task_summary SUM-01..SUM-08 = 8
task_quality Q-01..Q-08 = 8
sprint_health SH-01..SH-10 = 10
velocity V-01..V-08 = 8
team_workload TW-01..TW-10 = 10
competency_match CM-01..CM-09 = 9
release_health RH-01..RH-10 = 10
cross-skill X-01..X-08 = 8
TOTAL_FUNCTIONAL_REQUIRED_MIN = 107
```

The required correction/recheck scope is:

```text
CL-01..CL-15 = 15
```

Each required ID must be accounted for individually as one of:

- PASS;
- FAIL;
- BLOCKED;
- CLARIFICATION_PASS, only when clarification is the expected safe behavior and the question is targeted;
- LIVE_DATA_DRIFT_EXCEPTION, only with explicit source evidence and justification.

Do not use estimated counts. Do not use approximate `~4/15` metrics. Do not report GREEN with any unexecuted required ID.

## Oracle and comparison rules

For every factual task-set result:

1. Build an independent source-backed oracle.
2. Hydrate every candidate through authoritative AS21/SWTR reads.
3. Prove assignee, product/space, sprint, status and other filters from source fields.
4. Compare exact task-key sets, not prose and not only counts.
5. Treat `COMPLETED + 0` as PASS only if the independent oracle proves the final set is empty.

Agent output must never be used as oracle evidence.

Agreement between two broken mappings is not PASS.

## Failure handling

If a production defect is found, do not fix it. Record:

- original query;
- response status;
- raw semantic frame;
- semantic audit result;
- grounded frame;
- capability name;
- capability args;
- source reads;
- ORACLE_KEYS;
- AGENT_KEYS;
- MISSING_KEYS;
- EXTRA_KEYS;
- trace/error code;
- defect classification.

Then continue the remaining matrix when safe. A failing case is not a reason to stop the run unless it prevents subsequent independent execution.

## Hard GREEN rule

`035_VERDICT = GREEN`, `CORE8_REAL_QUERY_HARDENING_GREEN = YES`, and `READY_TO_RESUME_GATE_E = YES` are allowed only if all are true:

- all required functional IDs are accounted for;
- `TOTAL_FUNCTIONAL_TESTS >= 107`;
- `FUNCTIONAL_FAIL = 0`;
- `FUNCTIONAL_NOT_EXECUTED = 0`;
- every CL-01..CL-15 is accounted for;
- `CORRECTION_LOOP_PASS = 15/15`;
- `ORACLE_PREFLIGHT_PASS = YES`;
- `KNOWN_POSITIVE_DMS_GARANIN_ANCHORS_VERIFIED = YES`;
- `ORACLE_INDEPENDENCE_PASS = YES`;
- `FALSE_EMPTY_HIGH_COUNT = 0`;
- `FALSE_GREEN_HIGH_COUNT = 0`;
- `SOURCE_CONTRACT_OR_GROUNDING_DEFECTS = 0`;
- `NEW_HIGH_PRODUCTION_REGRESSIONS = 0`;
- `AS21_MUTATIONS_DURING_TEST = 0`.

If any condition is not satisfied, the correct verdict is RED or BLOCKED, not GREEN.

## Required report

Create:

`qa_reports/CORE8_017V2_COMPLETE_MATRIX_EXECUTION_035.md`

The report must contain:

- branch and `START_HEAD`;
- ancestor verification;
- service restart evidence;
- complete O-01..O-06 oracle/source-contract preflight;
- complete per-ID scope accounting for 107+ functional scenarios;
- complete CL-01..CL-15 accounting;
- exact set diffs for factual task-set queries;
- defect/blocker ledger grouped by canonical 017 V2 categories;
- explicit comparison against 033 and 034;
- final Gate E decision.

Footer:

```text
ASSIGNMENT_ID = CORE8_017V2_COMPLETE_MATRIX_EXECUTION_035
CURRENT_HEAD = <sha>
034_REPORT_COMMIT = beee3fcc684d8eb8cfafb0f295f8a0706a486d3a
035_RERUN_EXECUTED = YES|NO
TOTAL_FUNCTIONAL_REQUIRED_MIN = 107
TOTAL_FUNCTIONAL_TESTS = N
FUNCTIONAL_PASS = N
FUNCTIONAL_FAIL = N
FUNCTIONAL_NOT_EXECUTED = N
CORRECTION_LOOP_PASS = x/15
ORACLE_PREFLIGHT_PASS = YES|NO
KNOWN_POSITIVE_DMS_GARANIN_ANCHORS_VERIFIED = YES|NO
ORACLE_INDEPENDENCE_PASS = YES|NO
FALSE_EMPTY_HIGH_COUNT = N
FALSE_GREEN_HIGH_COUNT = N
SOURCE_CONTRACT_OR_GROUNDING_DEFECTS = N
NEW_HIGH_PRODUCTION_REGRESSIONS = N
AS21_MUTATIONS_DURING_TEST = 0
CORE8_REAL_QUERY_HARDENING_GREEN = YES|NO
READY_TO_RESUME_GATE_E = YES|NO
035_VERDICT = GREEN|RED|BLOCKED
```

## Commit and push

Commit and push only:

`qa_reports/CORE8_017V2_COMPLETE_MATRIX_EXECUTION_035.md`

Before commit:

```bash
git add -- qa_reports/CORE8_017V2_COMPLETE_MATRIX_EXECUTION_035.md
git diff --cached --name-only
```

The staged file list must contain exactly the allowed 035 report.

Commit subject must start with:

`qa: CORE8_017V2_COMPLETE_MATRIX_EXECUTION_035`

After push, stop and return:

1. report commit SHA;
2. final verdict;
3. complete report contents.
