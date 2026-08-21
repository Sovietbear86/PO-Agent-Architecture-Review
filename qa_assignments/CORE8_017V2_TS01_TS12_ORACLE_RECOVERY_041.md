# Assignment 041 — Source Oracle Recovery and TS-01..TS-12 Exact-Set Rerun

## Purpose

Assignment 040 executed TS-01..TS-12 without modifying production or runners, but did not produce valid acceptance evidence because the independent source-backed oracle was blocked and the required exact key-set table was missing.

Assignment 041 must first prove an independent read-only source oracle path, then rerun TS-01..TS-12 exact-set comparison. If the oracle path cannot be proven, stop with BLOCKED evidence.

## Repository

`Sovietbear86/PO-Agent-Architecture-Review`

## Branch

`feat/core8-real-query-hardening-v2`

## Production commit under test

`2c0e8aa7f105452e7d7e9efc53ce49344533acfa`

## Allowed output

Commit and push only:

`qa_reports/CORE8_017V2_TS01_TS12_ORACLE_RECOVERY_041.md`

Do not commit JSON, temporary scripts, runner changes, config changes, logs, `.env`, credentials, historical reports, roadmap edits, or production changes.

## Fixed role

You are QA/tester only.

Forbidden:

- modifying production code;
- modifying prompts;
- modifying adapters;
- modifying tests;
- modifying fixtures;
- modifying QA runners or acceptance runners;
- modifying repository or local configuration;
- modifying AS21/SWTR data;
- modifying historical reports;
- modifying roadmap/plan files;
- weakening the oracle;
- changing canonical query wording;
- declaring GREEN without exact oracle-vs-agent key-set evidence.

If a helper or runner cannot parse a valid response, do not edit the helper or runner. Record `QA_INFRA_BLOCKED` with exact raw response shape.

## Autonomous execution

The repository owner pre-authorizes this QA batch.

Do not ask for confirmation after each step, integration call, TS case, local service restart, read-only AS21/SWTR query, HTTP diagnostic, test command, allowed report commit, or allowed report push.

Ask only if continuing requires:

- a missing credential;
- an unavoidable platform approval;
- a write outside the report allowlist;
- a production/source-data/configuration mutation;
- a destructive out-of-scope action;
- a material scope expansion beyond this assignment.

## Mandatory Git preflight

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `START_HEAD = git rev-parse HEAD`.
4. Verify the following commits are ancestors of `START_HEAD`:

```bash
git merge-base --is-ancestor 2c0e8aa7f105452e7d7e9efc53ce49344533acfa "$START_HEAD"
git merge-base --is-ancestor a2705315e924cb58fb9ee8c2a15ba71562f97603 "$START_HEAD"
```

5. Verify no prohibited files are staged.
6. Verify `git diff -- qa_026_test_runner_v2.py` is empty.
7. Read this assignment completely from `START_HEAD`.
8. Read:
   - `GIGACODE_NEXT_ACTION.md`
   - `qa_reports/CORE8_017V2_BATCH_TS01_TS12_STRICT_RERUN_040.md`
   - `qa_assignments/CORE8_017V2_BATCH_TS01_TS12_STRICT_RERUN_040.md`
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
   - `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017.md`

If any preflight check fails, write the allowed 041 report with `041_VERDICT = BLOCKED`, include exact evidence, commit only that report, push, and stop.

## Runtime configuration

Restart and verify services from `START_HEAD`:

- Task API on port `8003`;
- PO Agent on port `8004`;
- MCP-SWTR on its configured port if used;
- real AS21/SWTR source;
- `PO_AGENT_AS21_MODE=task-api`;
- `PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8003`;
- configured semantic LLM endpoint;
- production semantic interpreter;
- no FakeAS21Adapter for acceptance evidence.

Record service PIDs, ports, health check URLs/statuses, effective environment values excluding secrets, and evidence that fake mode was not used.

## Phase 1 — prove independent oracle path

Before running TS cases, prove one independent source-backed oracle path.

Allowed oracle sources:

1. Direct SWTR/Jira REST reads, if accessible.
2. MCP-SWTR read-only calls, if they hydrate authoritative SWTR units.
3. Task API `/api/v1/swtr-read/*` endpoints, only if used directly for source hydration and not derived from PO Agent query output.

Not allowed as oracle:

- PO Agent `/api/v1/query` output;
- generated answer text;
- counts only;
- cached previous report data without current source hydration;
- guessed expected sets;
- regex extraction from answer text as source truth.

Oracle proof must include:

- exact endpoint/tool used;
- exact non-secret request shape;
- sample raw response shape;
- at least one hydrated known task unit with key, assignee, status, product/space and sprint attributes where present;
- explanation why this source is independent of PO Agent output.

If no independent oracle path can be proven, do not run TS cases as acceptance. Write `041_VERDICT = BLOCKED`, include exact 403/error responses and manual action required, commit only the allowed report, push, and stop.

## Phase 2 — TS-01..TS-12 exact-set rerun

Execute exactly canonical TS-01..TS-12 from the 017 V2 matrix.

Do not run the full 42-case matrix for this assignment.

For each TS case:

1. Capture raw PO Agent response status.
2. Capture raw semantic frame or trace pointer.
3. Capture grounded constraints.
4. Capture capability name and exact capability args.
5. Build `ORACLE_KEYS` from the proven independent source-backed oracle.
6. Extract `AGENT_KEYS` from structured PO Agent response data, not from answer text unless explicitly marked as fallback evidence.
7. Compare exact sorted sets.
8. Record `MISSING_KEYS`, `EXTRA_KEYS`, and `FOREIGN_KEYS`.
9. Classify PASS/FAIL/CLARIFICATION_PASS/BLOCKED.

Clarification is acceptable only if source evidence shows the query is genuinely ambiguous or ungroundable and no required slot was silently dropped.

## Required per-ID evidence table

The report must contain one row for every TS-01..TS-12 with these fields:

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

If any field cannot be collected, mark the row `BLOCKED` or `FAIL` with exact reason. Do not omit rows.

## Special checks

Explicitly report:

- whether any required semantic slot was silently dropped;
- whether any foreign product/sprint/person/status task was returned;
- whether any empty COMPLETED result was treated as PASS without an independent empty oracle;
- whether any response was HTTP 500;
- whether any runner/helper had to be bypassed without modification;
- whether AS21/SWTR token/access was valid through the selected oracle path.

## Acceptance

041 is GREEN only if all of the following are true:

- independent source-backed oracle path is proven;
- all TS-01..TS-12 rows are present;
- every row has required per-ID evidence;
- every non-clarification exact key set matches;
- every clarification/fail-closed result is source-backed and semantically correct;
- `FALSE_GREEN_COUNT = 0`;
- `FALSE_EMPTY_COUNT = 0`;
- `SILENT_SLOT_DROP_COUNT = 0`;
- `FOREIGN_TASK_COUNT = 0`;
- `QUERY_HTTP_500_COUNT = 0`;
- no production/runner/test/config/source-data/historical-report file was modified;
- only the allowed Markdown report is committed.

If any condition is false, 041 is RED or BLOCKED. Do not mark GREEN.

`READY_TO_RESUME_GATE_E` must remain `NO` in this assignment. Gate E can only resume after a later valid full rollup explicitly authorizes it.

## Required footer

Include this footer with actual values:

```text
ASSIGNMENT_ID = CORE8_017V2_TS01_TS12_ORACLE_RECOVERY_041
START_HEAD = <sha>
REPORT_COMMIT = <sha_after_commit_or_PENDING_BEFORE_COMMIT>
PRODUCTION_FIX_UNDER_TEST = 2c0e8aa7f105452e7d7e9efc53ce49344533acfa
PREVIOUS_040_REPORT_COMMIT = a2705315e924cb58fb9ee8c2a15ba71562f97603
ORACLE_PATH_PROVEN = YES|NO
ORACLE_PATH_TYPE = DIRECT_SWTR|MCP_SWTR|TASK_API_SWTR_READ|NONE
TS_REQUIRED = 12
TS_EXECUTED = x/12
TS_PASS = x/12
TS_FAIL = x
TS_CLARIFICATION_PASS = x
TS_BLOCKED = x
REQUIRED_PER_ID_TABLE_PRESENT = YES|NO
EXACT_SET_COMPARISON_PRESENT = YES|NO
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
041_VERDICT = GREEN|RED|BLOCKED
READY_TO_RESUME_GATE_E = NO
```

## Commit and stop

Before commit:

```bash
git status --short
git add -- qa_reports/CORE8_017V2_TS01_TS12_ORACLE_RECOVERY_041.md
git diff --cached --name-only
```

The staged file list must contain exactly:

```text
qa_reports/CORE8_017V2_TS01_TS12_ORACLE_RECOVERY_041.md
```

Commit subject:

`qa: CORE8_017V2_TS01_TS12_ORACLE_RECOVERY_041`

Push to the same branch.

Return:

1. commit SHA;
2. final verdict;
3. complete report contents.

Then stop.
