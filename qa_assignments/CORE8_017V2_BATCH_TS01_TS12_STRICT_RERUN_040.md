# Assignment 040 — Strict TS-01..TS-12 Rerun After Invalid 039

## Purpose

Rerun the first timeout-safe batch of the canonical 017 V2 matrix after Assignment 039 was invalidated.

Assignment 039 is not accepted as evidence because it modified `qa_026_test_runner_v2.py`, committed an unauthorized JSON result, omitted the required per-ID exact key-set table, and declared `GREEN` despite internally reporting Section D `0/6`, Section E `0/4`, and Section F `1/6`.

This assignment is a strict QA-only rerun. It is not a production-fix assignment.

## Repository

`Sovietbear86/PO-Agent-Architecture-Review`

## Branch

`feat/core8-real-query-hardening-v2`

## Production commit under test

`2c0e8aa7f105452e7d7e9efc53ce49344533acfa`

## Allowed output

Commit and push only:

`qa_reports/CORE8_017V2_BATCH_TS01_TS12_STRICT_RERUN_040.md`

Do not commit JSON, temporary scripts, runner changes, config changes, logs, `.env`, credentials, or historical report edits.

## Fixed role

You are QA/tester only.

Forbidden:

- modifying production code;
- modifying prompts;
- modifying adapters;
- modifying tests;
- modifying fixtures;
- modifying QA runners or acceptance runners;
- modifying local or repository configuration;
- modifying AS21/SWTR data;
- modifying historical reports;
- modifying roadmap/plan files;
- weakening the oracle;
- changing query wording;
- converting failed or missing evidence into GREEN.

If a helper or runner cannot parse a valid response, do not edit the helper or runner. Record `QA_INFRA_BLOCKED` with exact raw response shape and stop or continue manually without modifying source files.

## Autonomous execution

The repository owner pre-authorizes this QA batch.

Do not ask for confirmation after each step, integration call, TS case, local service restart, read-only AS21/SWTR query, HTTP diagnostic, test command, commit of the allowed report, or push of the allowed report.

Ask only if continuing requires:

- a missing credential;
- a platform approval that cannot be avoided;
- a write outside the report allowlist;
- a production/source-data/configuration mutation;
- a destructive out-of-scope action;
- a material scope expansion beyond this assignment.

## Mandatory preflight

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `START_HEAD = git rev-parse HEAD`.
4. Verify the following commits are ancestors of `START_HEAD`:

```bash
git merge-base --is-ancestor 2c0e8aa7f105452e7d7e9efc53ce49344533acfa "$START_HEAD"
git merge-base --is-ancestor 1035004f615a4db9e5859440c07f3f4f9a7e383b "$START_HEAD"
```

5. Verify no prohibited files are already staged.
6. Verify the runner was restored to the production-owned version. `git diff -- qa_026_test_runner_v2.py` must be empty before the run.
7. Read this assignment completely from `START_HEAD`.
8. Read:
   - `GIGACODE_NEXT_ACTION.md`
   - `qa_reports/CORE8_017V2_BATCH_TS01_TS12_RETEST_039.md`
   - `qa_assignments/CORE8_017V2_BATCH_TS01_TS12_RETEST_039.md`
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017.md`

If any preflight check fails, write the allowed 040 report with `040_VERDICT = BLOCKED`, include exact evidence, commit only that report, push, and stop.

## Runtime configuration

Restart and verify services from `START_HEAD`:

- Task API on port `8003`;
- PO Agent on port `8004`;
- real AS21/SWTR source;
- `PO_AGENT_AS21_MODE=task-api`;
- `PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8003`;
- configured semantic LLM endpoint;
- production semantic interpreter;
- no FakeAS21Adapter for acceptance evidence.

Record in the report:

- service PIDs;
- ports;
- health check URLs/statuses;
- effective environment values excluding secrets;
- evidence that fake mode was not used.

If services cannot be restarted due to environment limits, do not declare production FAIL. Report `040_VERDICT = BLOCKED` and include exact manual command required.

## Scope

Execute exactly canonical TS-01..TS-12 from the 017 V2 matrix.

Do not run the full 42-case matrix for this assignment. The objective is to restore valid evidence for the first timeout-safe batch only.

## Oracle requirements

Use an independent source-backed oracle. Agent output must not be used as oracle.

For every TS case:

1. Resolve expected source truth from AS21/SWTR independently of the PO Agent result.
2. Hydrate candidate tasks from authoritative SWTR units where relevant.
3. Apply source-backed constraints for person/product/status/sprint/current sprint exactly as the query requires.
4. Compare exact task-key sets, not counts and not answer text only.
5. Classify clarification/fail-closed only when backed by source evidence and the semantic frame did not silently drop required constraints.

## Required per-ID evidence table

The report must contain one row for every TS-01..TS-12 with at least:

| Field | Required content |
|-------|------------------|
| TS_ID | TS-01..TS-12 |
| Query | exact canonical query |
| Response status | COMPLETED / NEEDS_CLARIFICATION / FAILED / HTTP error |
| Raw semantic frame | raw frame or trace pointer |
| Grounded constraints | assignee/product/status/sprint/current-sprint as applicable |
| Capability | production capability invoked |
| Capability args | exact args passed |
| Oracle keys | exact sorted key set |
| Agent keys | exact sorted key set |
| Missing keys | exact sorted key set |
| Extra keys | exact sorted key set |
| Foreign keys | exact keys violating product/sprint/person/status source constraints |
| Verdict | PASS / FAIL / CLARIFICATION_PASS / BLOCKED |
| Evidence pointer | trace/log/source evidence pointer |

If any field cannot be collected, mark the row `BLOCKED` or `FAIL` with exact reason. Do not omit the row.

## Special checks

Explicitly report:

- whether any required semantic slot was silently dropped;
- whether any foreign product/sprint task was returned;
- whether any empty COMPLETED result was treated as PASS without an independent empty oracle;
- whether any response was HTTP 500;
- whether any runner/helper had to be bypassed without modification;
- whether AS21/SWTR token/access was valid during execution.

## Acceptance

040 is GREEN only if all of the following are true:

- all TS-01..TS-12 rows are present;
- each row has required per-ID evidence;
- every non-clarification expected exact key set matches;
- every clarification/fail-closed result is source-backed and semantically correct;
- `FALSE_GREEN_COUNT = 0`;
- `FALSE_EMPTY_COUNT = 0`;
- `SILENT_SLOT_DROP_COUNT = 0`;
- `FOREIGN_TASK_COUNT = 0`;
- `QUERY_HTTP_500_COUNT = 0`;
- no production/runner/test/config/source-data/historical-report file was modified;
- only the allowed Markdown report is committed.

If any condition is false, 040 is RED or BLOCKED. Do not mark GREEN.

`READY_TO_RESUME_GATE_E` must remain `NO` in this assignment. Gate E can only resume after a later valid full rollup explicitly authorizes it.

## Required footer

Include this footer verbatim with actual values:

```text
ASSIGNMENT_ID = CORE8_017V2_BATCH_TS01_TS12_STRICT_RERUN_040
START_HEAD = <sha>
REPORT_COMMIT = <sha_after_commit_or_PENDING_BEFORE_COMMIT>
PRODUCTION_FIX_UNDER_TEST = 2c0e8aa7f105452e7d7e9efc53ce49344533acfa
PREVIOUS_INVALID_REPORT_COMMIT = 1035004f615a4db9e5859440c07f3f4f9a7e383b
TS_REQUIRED = 12
TS_EXECUTED = x/12
TS_PASS = x/12
TS_FAIL = x
TS_CLARIFICATION_PASS = x
TS_BLOCKED = x
REQUIRED_PER_ID_TABLE_PRESENT = YES|NO
RUNNER_MODIFIED = NO
PRODUCTION_MODIFIED = NO
UNAUTHORIZED_FILES_COMMITTED = NO
ORACLE_PREFLIGHT_PASS = YES|NO|BLOCKED
ORACLE_INDEPENDENCE_PASS = YES|NO|BLOCKED
FOREIGN_TASK_COUNT = n
FALSE_GREEN_COUNT = n
FALSE_EMPTY_COUNT = n
SILENT_SLOT_DROP_COUNT = n
QUERY_HTTP_500_COUNT = n
QA_INFRA_BLOCKED_COUNT = n
AS21_ACCESS_VALID = YES|NO
040_VERDICT = GREEN|RED|BLOCKED
READY_TO_RESUME_GATE_E = NO
```

## Commit and stop

Before commit:

```bash
git status --short
git add -- qa_reports/CORE8_017V2_BATCH_TS01_TS12_STRICT_RERUN_040.md
git diff --cached --name-only
```

The staged file list must contain exactly:

```text
qa_reports/CORE8_017V2_BATCH_TS01_TS12_STRICT_RERUN_040.md
```

Commit subject:

`qa: CORE8_017V2_BATCH_TS01_TS12_STRICT_RERUN_040`

Push to the same branch.

Return:

1. commit SHA;
2. final verdict;
3. complete report contents.

Then stop.
