# Assignment 033 — 017 V2 Exhaustive Real-Query Matrix Rerun

## Purpose

Assignment 032 reported a complete GREEN semantic/Core-8 benchmark and set:

```text
READY_TO_RERUN_017_V2 = YES
```

This assignment is the authorized rerun of the frozen Core-8 hardening gate:

`qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`

GigaCode is QA/tester only. Do not modify production code, prompts, adapters, tests, fixtures, acceptance runners, configuration, AS21/SWTR data, learning state, historical reports, or roadmap files.

## Repository

Repository:

`Sovietbear86/PO-Agent-Architecture-Review`

Branch:

`feat/core8-real-query-hardening-v2`

Expected new report:

`qa_reports/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2_RERUN_033.md`

Do not overwrite the historical report:

`qa_reports/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`

That older file is preserved as historical RED evidence. The new 033 report must explicitly state whether it supersedes the historical RED verdict.

## Mandatory Git preflight

Before starting services or tests:

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `git rev-parse HEAD` as `START_HEAD`.
4. Re-read `GIGACODE_NEXT_ACTION.md` and this assignment from `START_HEAD`.
5. Read the canonical 017 V2 assignment completely:
   `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
6. Read the detailed referenced specs completely:
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017.md`
   - `qa_assignments/CORE8_CORRECTION_LOOP_ADDENDUM_017A.md`

Verify all required ancestor commits:

```bash
git merge-base --is-ancestor 319ae1e85311f3123c44c2dd0118b843172aef4d "$START_HEAD"
git merge-base --is-ancestor 940ee44939dcbca14a7583e167b096525f0e509f "$START_HEAD"
git merge-base --is-ancestor ca1ad3ab6e86f2e464bebb27527760f83d058842 "$START_HEAD"
```

If any check fails, create the 033 report with `CORE8_REAL_QUERY_HARDENING_GREEN = NO`, `READY_TO_RESUME_GATE_E = NO`, exact mismatch evidence, and stop.

## Autonomous execution — no step-by-step confirmation

The repository owner has pre-authorized the complete QA workflow defined by this entrypoint and the active assignment. Execute it end to end without asking for confirmation after each step or before each integration call.

No additional conversational confirmation is required for read-only AS21/SWTR calls, the configured semantic LLM, local service restart/health checks, HTTP diagnostics, test runs, `git switch`, `git pull --ff-only`, Git inspection, or commit/push of the explicitly allowed QA report.

Do not pause with questions such as “continue?”, “run the integration?”, “restart the service?” or “commit the report?”. Ask only if continuing requires an unconfigured credential/permission, an unavoidable platform approval, a write outside the report allowlist, a production/source-data/configuration mutation, a destructive out-of-scope action, or a material scope expansion. Consolidate unavoidable prompts to the minimum number possible.

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

The 033 report must include old/new PIDs, ports, commands, health responses, and proof that services were restarted from `START_HEAD`.

If services cannot be restarted due to environment limits, do not report production FAIL. Report `BLOCKED`/`MANUAL_ACTION_REQUIRED` with exact restart commands and stop.

## Canonical test scope

Run `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md` completely and unchanged.

This includes:

1. Mandatory oracle/source-contract preflight O-01..O-06.
2. Every functional query from `CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017.md`:
   - task_search TS-01..TS-36;
   - task_summary SUM-01..SUM-08;
   - task_quality Q-01..Q-08;
   - sprint_health SH-01..SH-10;
   - velocity V-01..V-08;
   - team_workload TW-01..TW-10;
   - competency_match CM-01..CM-09;
   - release_health RH-01..RH-10;
   - every X-* cross-skill composition.
3. Every correction/recheck scenario CL-01..CL-15 from `CORE8_CORRECTION_LOOP_ADDENDUM_017A.md`.
4. The GOLDEN query and GOLDEN correction dialogue from 017 V2.
5. Protected regression invariants.

Do not substitute the 026 runner summary for the 017 V2 matrix. Assignment 032 GREEN is only the authorization to run 017 V2; it is not a replacement for 017 V2 evidence.

## Oracle rules

For every factual task-set result:

1. Build an independent source-backed oracle.
2. Hydrate every candidate through authoritative AS21/SWTR reads.
3. Prove assignee, product/space, sprint, status and other filters from source fields.
4. Compare exact task-key sets, not prose and not only counts.
5. Treat `COMPLETED + 0` as PASS only if the independent oracle proves the final set is empty.

Agent output must never be used as oracle evidence.

Agreement between two broken mappings is not PASS.

## Known historical pitfalls to re-check

The historical 017 V2 report claimed `ORACLE_SOURCE_CONTRACT_BROKEN` because it relied on incomplete task-api fields. Later QA evidence proved richer SWTR source paths and source-backed sprint hydration are required.

Therefore, in 033:

- do not use only task-api flattened `project`/`sprintId` fields as the source contract;
- do not use only the sprint-list facade echo as sprint proof;
- hydrate individual SWTR task units for sprint membership;
- record raw attribute paths used for assignee, product/space, status and sprint;
- preserve any genuine live-data drift as evidence, not as silent expected-output changes.

## Defect handling

For every mismatch or blocked case, record:

- original user query;
- raw semantic frame;
- semantic audit result;
- grounded frame;
- capability name;
- capability args;
- source reads used by the oracle;
- per-task authoritative relation;
- ORACLE_KEYS;
- AGENT_KEYS;
- MISSING_KEYS;
- EXTRA_KEYS;
- response status;
- trace/error code;
- defect classification from the 017 V2 ledger.

Do not fix production defects. Do not modify tests or acceptance criteria.

## Reporting

Create:

`qa_reports/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2_RERUN_033.md`

The report must include:

- branch and `START_HEAD`;
- verification of required ancestor commits;
- service restart evidence;
- production wiring evidence;
- complete oracle/source-contract preflight O-01..O-06;
- complete per-test matrix;
- exact set diffs for factual task-set queries;
- complete correction/recheck loop results CL-01..CL-15;
- protected regression results;
- defect ledger grouped by 017 V2 classifications;
- explicit comparison against the historical 017 V2 RED report;
- final gate decision.

The footer must include all original 017 V2 metrics plus the 033 wrapper metrics:

```text
ASSIGNMENT_ID = CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2_RERUN_033
CANONICAL_SPEC = qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md
CURRENT_HEAD = <sha>
ORACLE_PREFLIGHT_PASS = YES|NO
KNOWN_POSITIVE_DMS_GARANIN_ANCHORS_VERIFIED = YES|NO
TOTAL_FUNCTIONAL_TESTS = N
FUNCTIONAL_PASS = N
FUNCTIONAL_FAIL = N
CORRECTION_LOOP_PASS = x/15
CHALLENGE_TRIGGERS_SOURCE_RECHECK = YES|NO
TARGETED_CLARIFICATION_PASS = YES|NO
SESSION_CONTEXT_RETENTION_PASS = YES|NO
SESSION_MEMORY_NOT_CONFUSED_WITH_LEARNING = YES|NO
NEGATIVE_FEEDBACK_TRACE_PASS = YES|NO
LEARNING_PIPELINE_BOUNDARY_PASS = YES|NO
ORACLE_INDEPENDENCE_PASS = YES|NO
FALSE_EMPTY_HIGH_COUNT = N
FALSE_GREEN_HIGH_COUNT = N
SOURCE_CONTRACT_OR_GROUNDING_DEFECTS = N
NEW_HIGH_PRODUCTION_REGRESSIONS = N
AS21_MUTATIONS_DURING_TEST = 0
CORE8_REAL_QUERY_HARDENING_GREEN = YES|NO
READY_TO_RESUME_GATE_E = YES|NO
033_SUPERSEDES_HISTORICAL_017_V2_RED = YES|NO
```

`CORE8_REAL_QUERY_HARDENING_GREEN = YES` and `READY_TO_RESUME_GATE_E = YES` are allowed only if all final GREEN rules in the canonical 017 V2 spec are satisfied.

If not GREEN, stop after publishing the report. Do not run Gate E.

## Commit and push

Commit and push only:

`qa_reports/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2_RERUN_033.md`

Before commit:

```bash
git add -- qa_reports/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2_RERUN_033.md
git diff --cached --name-only
```

The staged file list must contain exactly the allowed 033 report.

Commit subject must start with:

`qa: CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2_RERUN_033`

After push, stop and return:

1. report commit SHA;
2. final verdict;
3. complete report contents.
