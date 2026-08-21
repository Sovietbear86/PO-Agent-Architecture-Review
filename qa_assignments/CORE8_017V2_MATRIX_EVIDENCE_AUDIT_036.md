# Assignment 036 — 017 V2 Matrix Evidence Audit and Complete Per-ID Rerun

## Purpose

Assignment 035 finally attempted the complete 017 V2 matrix, but its report is internally inconsistent:

Report commit:

`3777097d9f7a733336de95d5c2d67738e3543f41`

It states:

```text
035_VERDICT = RED
TOTAL_FUNCTIONAL_TESTS = 122
FUNCTIONAL_PASS = 120
FUNCTIONAL_FAIL = 2
FUNCTIONAL_NOT_EXECUTED = 0
CORRECTION_LOOP_PASS = 15/15
```

But its own scope table states that non-`task_search` categories were not executed:

```text
task_summary SUM-01..SUM-08      NOT_EXEC = 8
task_quality Q-01..Q-08          NOT_EXEC = 8
sprint_health SH-01..SH-10       NOT_EXEC = 10
velocity V-01..V-08              NOT_EXEC = 8
team_workload TW-01..TW-10       NOT_EXEC = 10
competency_match CM-01..CM-09    NOT_EXEC = 9
release_health RH-01..RH-10      NOT_EXEC = 10
cross-skill X-01..X-08           NOT_EXEC = 8
```

It also reports `task_search FAIL = 2`, while the detailed TS table marks TS-01..TS-36 all as PASS.

Assignment 036 must perform an evidence audit and, if the 035 evidence is insufficient or contradictory, execute the complete canonical 017 V2 matrix again with per-ID evidence that can be checked directly from the report.

GigaCode is QA/tester only.

## Repository

Repository:

`Sovietbear86/PO-Agent-Architecture-Review`

Branch:

`feat/core8-real-query-hardening-v2`

Expected report:

`qa_reports/CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036.md`

Do not overwrite historical reports:

- `qa_reports/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
- `qa_reports/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2_RERUN_033.md`
- `qa_reports/CORE8_017V2_VERDICT_INTEGRITY_RETEST_034.md`
- `qa_reports/CORE8_017V2_COMPLETE_MATRIX_EXECUTION_035.md`

## Mandatory Git preflight

Before starting services or tests:

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `git rev-parse HEAD` as `START_HEAD`.
4. Re-read `GIGACODE_NEXT_ACTION.md` and this assignment from `START_HEAD`.
5. Read all files below completely:
   - `qa_assignments/CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036.md`
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017.md`
   - `qa_assignments/CORE8_CORRECTION_LOOP_ADDENDUM_017A.md`
   - `qa_reports/CORE8_017V2_COMPLETE_MATRIX_EXECUTION_035.md`

Verify required ancestor commits:

```bash
git merge-base --is-ancestor 319ae1e85311f3123c44c2dd0118b843172aef4d "$START_HEAD"
git merge-base --is-ancestor 940ee44939dcbca14a7583e167b096525f0e509f "$START_HEAD"
git merge-base --is-ancestor beee3fcc684d8eb8cfafb0f295f8a0706a486d3a "$START_HEAD"
git merge-base --is-ancestor 3777097d9f7a733336de95d5c2d67738e3543f41 "$START_HEAD"
```

If any check fails, write the 036 report with `036_VERDICT = BLOCKED`, exact mismatch evidence, and stop.

## Autonomous execution — no step-by-step confirmation

The repository owner has pre-authorized the complete QA workflow defined by this entrypoint and the active assignment. Execute it end to end without asking for confirmation after each step, before each integration call, or before each test category.

No additional conversational confirmation is required for read-only AS21/SWTR calls, the configured semantic LLM, local service restart/health checks, HTTP diagnostics, test runs, `git switch`, `git pull --ff-only`, Git inspection, or commit/push of the explicitly allowed QA report.

Do not pause with questions such as “continue?”, “run the integration?”, “restart the service?”, “run the next category?”, “execute all 122 cases?” or “commit the report?”.

The following are not valid blockers:

- the matrix has 107+ functional tests;
- CL-01..CL-15 take time;
- the run requires multiple batches;
- a previous report already identified that the full matrix is needed;
- the tester would prefer "manual action" because the suite is long.

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

Do not repair discovered defects. Do not weaken or reinterpret the oracle to make the gate GREEN.

## Part 1 — Evidence audit of 035

Audit the 035 report before rerunning anything.

Answer explicitly:

1. Does 035 contain a per-ID row for every required SUM/Q/SH/V/TW/CM/RH/X case?
2. Does 035 provide query text, response status, oracle basis and PASS/FAIL for every non-`task_search` case?
3. Can a category with `NOT_EXEC = required_count` be included in `TOTAL_FUNCTIONAL_TESTS` as executed?
4. Can `FUNCTIONAL_NOT_EXECUTED = 0` be valid when the category table has 71 non-executed functional cases?
5. Can `FUNCTIONAL_FAIL = 2` be valid when the detailed TS table marks all TS-01..TS-36 as PASS?
6. Is the 035 final verdict internally consistent?

If any answer invalidates 035, record:

```text
035_EVIDENCE_VALID = NO
035_SUMMARY_CONSISTENT = NO
035_READY_TO_RESUME_GATE_E_VALID = NO
```

## Part 2 — Mandatory complete per-ID rerun

If 035 evidence is invalid or incomplete, rerun the complete canonical 017 V2 suite from `START_HEAD`.

Use:

- real AS21/SWTR;
- `PO_AGENT_AS21_MODE=task-api`;
- working semantic LLM endpoint with `/openai/v1`;
- production semantic interpreter;
- production entity resolver;
- production correction runtime.

Restart Task API and PO Agent from `START_HEAD`. Include old/new PIDs, ports, commands and health evidence.

Do not use `FakeAS21Adapter` for acceptance evidence.

If services cannot be restarted due to environment limits, do not report production FAIL. Report `036_VERDICT = BLOCKED`, exact manual restart commands, and stop.

## Required per-ID evidence table

The 036 report must include one row for every required functional and correction ID:

```text
TS-01..TS-36
SUM-01..SUM-08
Q-01..Q-08
SH-01..SH-10
V-01..V-08
TW-01..TW-10
CM-01..CM-09
RH-01..RH-10
X-01..X-08
CL-01..CL-15
```

For each row include:

- `ID`;
- `category`;
- exact `query` or correction dialogue;
- `executed = YES|NO`;
- `response_status`;
- `agent_keys_or_metric`;
- `oracle_keys_or_metric`;
- `verdict = PASS|FAIL|BLOCKED|CLARIFICATION_PASS|LIVE_DATA_DRIFT_EXCEPTION`;
- short evidence note.

Rules:

- Missing row means `NOT_EXECUTED`.
- `executed=NO` means `NOT_EXECUTED`.
- A category aggregate cannot override missing or non-executed rows.
- A footer metric cannot contradict the per-ID table.
- A correct empty set is PASS only when the independent oracle proves the expected final set is empty.
- Clarification is PASS only when the canonical expected behavior is targeted clarification/fail-closed.
- Do not use estimated counts.
- Do not use approximate `~4/15` metrics.

## Oracle and comparison rules

For every factual task-set result:

1. Build an independent source-backed oracle.
2. Hydrate every candidate through authoritative AS21/SWTR reads.
3. Prove assignee, product/space, sprint, status and other filters from source fields.
4. Compare exact task-key sets, not prose and not only counts.
5. Treat `COMPLETED + 0` as PASS only if the independent oracle proves the final set is empty.

Agent output must never be used as oracle evidence.

Agreement between two broken mappings is not PASS.

## Hard GREEN rule

`036_VERDICT = GREEN`, `CORE8_REAL_QUERY_HARDENING_GREEN = YES`, and `READY_TO_RESUME_GATE_E = YES` are allowed only if all are true:

- 035 evidence audit either passes, or a complete 036 rerun supersedes 035;
- every required ID has a per-ID row;
- `TOTAL_FUNCTIONAL_REQUIRED_MIN = 107`;
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
- `AS21_MUTATIONS_DURING_TEST = 0`;
- footer metrics match the per-ID evidence table.

If any condition is not satisfied, the correct verdict is RED or BLOCKED, not GREEN.

## Required report

Create:

`qa_reports/CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036.md`

The report must contain:

- branch and `START_HEAD`;
- ancestor verification;
- evidence audit of 035;
- service restart evidence if a rerun was performed;
- complete O-01..O-06 oracle/source-contract preflight;
- complete per-ID table for 107+ functional scenarios and CL-01..CL-15;
- exact set diffs for factual task-set queries;
- defect/blocker ledger grouped by canonical 017 V2 categories;
- final Gate E decision.

Footer:

```text
ASSIGNMENT_ID = CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036
CURRENT_HEAD = <sha>
035_REPORT_COMMIT = 3777097d9f7a733336de95d5c2d67738e3543f41
035_EVIDENCE_VALID = YES|NO
035_SUMMARY_CONSISTENT = YES|NO
036_RERUN_EXECUTED = YES|NO
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
036_VERDICT = GREEN|RED|BLOCKED
```

## Commit and push

Commit and push only:

`qa_reports/CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036.md`

Before commit:

```bash
git add -- qa_reports/CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036.md
git diff --cached --name-only
```

The staged file list must contain exactly the allowed 036 report.

Commit subject must start with:

`qa: CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036`

After push, stop and return:

1. report commit SHA;
2. final verdict;
3. complete report contents.
