# Assignment 050 — Bounded SWTR Oracle Access Unblock Retest

## Purpose

Assignment 049 proved that the Harness code path and the adjacent known-good `MyTestProject_1` MCP-SWTR filter both failed with the same `SWTR_ACCESS_DENIED_ERROR`, so the project was blocked on SWTR token/role/runtime access rather than a proven production defect.

The repository owner now reports that the MCP-SWTR token passthrough issue was fixed locally and that the direct filtered MCP-SWTR path for `DMS-SPRNT-2` returns real task keys.

This assignment verifies that unblock with a bounded hydrated oracle. Do **not** run the full 017 V2 matrix until this assignment proves:

```text
ORACLE_PATH_PROVEN = YES
CASE_GARANIN_DMS_SPRINT2_EXACT_SET = PASS
READY_TO_RERUN_017_V2 = YES
```

## Repository

`Sovietbear86/PO-Agent-Architecture-Review`

## Branch

`feat/core8-real-query-hardening-v2`

## Allowed output

Commit and push only:

`qa_reports/CORE8_BOUNDED_SWTR_ORACLE_ACCESS_UNBLOCK_RETEST_050.md`

Do not commit JSON, helper scripts, runner changes, wrapper changes, `.env`, credentials, logs, screenshots, historical reports, roadmap edits or production changes.

## Fixed role

You are QA/tester only.

- Do not modify production code, prompts, adapters, tests, fixtures, QA runners, acceptance runners, repository/local configuration, AS21/SWTR data, historical reports, roadmap files or learning state.
- Do not copy MCP-SWTR source into this repository.
- Do not run full tenant-wide task sync.
- Do not run bulk task synchronization as an oracle substitute.
- Do not repair discovered production defects.
- Never print, commit or paste token values.

If your local runtime fix requires an uncommitted wrapper or `.env` change that already exists on the owner machine, you may use it as environment setup evidence, but you must not commit it and must redact all secrets.

## Autonomous execution

The repository owner pre-authorizes this QA batch. Do not ask for confirmation after each routine step, integration call, local service restart, read-only AS21/SWTR query, MCP-SWTR diagnostic, Task API diagnostic, HTTP diagnostic, test command, allowed report commit or allowed report push.

Ask only if continuing requires a missing credential, unavoidable platform approval, write outside the report allowlist, production/source-data/config mutation, destructive out-of-scope action or scope expansion.

## Mandatory preflight

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `START_HEAD = git rev-parse HEAD`.
4. Read this assignment and `GIGACODE_NEXT_ACTION.md` from `START_HEAD`.
5. Verify the active assignment is 050 and the allowed report path is exactly:
   `qa_reports/CORE8_BOUNDED_SWTR_ORACLE_ACCESS_UNBLOCK_RETEST_050.md`
6. Read:
   - `qa_reports/CORE8_BOUNDED_SWTR_ORACLE_ACCESS_PROOF_049.md`
   - `qa_assignments/CORE8_BOUNDED_SWTR_ORACLE_ACCESS_PROOF_049.md`
   - `qa_reports/CORE8_SWTR_READ_SCHEMA_AWARE_SPRINT_ORACLE_RETEST_048.md`
7. Verify no prohibited files are staged.

If preflight fails, write the allowed 050 report with `050_VERDICT = BLOCKED`, include exact mismatch evidence, commit only that report, push and stop.

## Phase 1 — Focused regression tests

Run:

```bash
cd task-api
python3 -m pytest tests/test_swtr_mcp_client.py tests/test_swtr_read_facade.py -q
```

Record exact result. If dependencies are missing, record the missing dependency and continue to integration phases if services can run.

## Phase 2 — Start bounded read-only runtime

Use the same adjacent MCP-SWTR installation and local wrapper/env setup that now proves token passthrough. Redact all secret values.

Start Task API from `START_HEAD` with stdio MCP-SWTR configuration. Start PO Agent with `PO_AGENT_AS21_MODE=task-api` and `PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8003`.

Record:

- PIDs and ports;
- redacted env shape;
- `SWTR_MCP_TRANSPORT=stdio`;
- `SWTR_MCP_STDIO_CWD` location shape;
- no token values.

## Phase 3 — Health and direct access proof

Call:

```bash
curl -s http://127.0.0.1:8003/api/v1/swtr-read/health
curl -s http://127.0.0.1:8004/api/v1/ops/as21-diagnostics
```

Required:

- `transport = stdio`;
- required MCP tools present;
- Task API route contract remains `SWTR_READ`;
- runtime identity proof passes;
- no secrets in responses.

Then prove the direct known-good bounded source path without full sync:

```text
Known-good MCP-SWTR tool/filter:
  get_sprint_tasks("DMS-SPRNT-2")
  TQL: scrum_board_plugin_sprint = "DMS-SPRNT-2"
```

Record:

- tool/function name;
- argument names;
- exact redacted command shape;
- task key count;
- exact task key set returned;
- whether the result is real task data, empty, access denied or error.

Required to proceed:

```text
KNOWN_GOOD_FILTER_DIRECT_RESULT = TASK_KEYS
KNOWN_GOOD_FILTER_TASK_COUNT > 0
```

If direct known-good MCP-SWTR still returns access denied/error/no source keys, report `050_VERDICT = BLOCKED`, commit the report and stop.

## Phase 4 — Harness bounded candidate source parity

Call:

```bash
curl -i "http://127.0.0.1:8003/api/v1/swtr-read/tasks/DMS-261"
curl -i "http://127.0.0.1:8003/api/v1/swtr-read/tasks/DMS-248"
curl -i "http://127.0.0.1:8003/api/v1/swtr-read/sprints/DMS-SPRNT-2/tasks?space=DMS&complete=true"
```

If `DMS-261` or `DMS-248` no longer exists in source truth, replace it with two task keys returned by the direct bounded `DMS-SPRNT-2` source path and record the substitution.

For the sprint candidate call, record:

- HTTP status;
- task key count;
- exact task key set;
- whether payload is real data or fail-closed error;
- whether `errorType` appears under a successful `tasks` object;
- whether HTTP 500 or traceback occurred.

Compare exact candidate key sets:

```text
DIRECT_MCP_SPRINT2_KEYS == HARNESS_SPRINT2_KEYS
```

If direct MCP-SWTR returns bounded keys but Harness cannot expose an equivalent bounded source, report `050_VERDICT = RED` with `KNOWN_GOOD_FILTER_PARITY = FAIL`.

## Phase 5 — Hydrated SWTR oracle

Use only the bounded `DMS-SPRNT-2` candidate keys from Phase 3/4.

For every candidate task key:

1. Call `GET /api/v1/swtr-read/tasks/<TASK_KEY>`.
2. Extract:
   - task key;
   - assignee/login;
   - status;
   - space/product;
   - `scrum_board_plugin_sprint`.
3. Include the task in `ORACLE_DMS_SPRINT2_KEYS` only if the individually read task unit has `scrum_board_plugin_sprint == DMS-SPRNT-2`.
4. Build `ORACLE_GARANIN_DMS_SPRINT2_KEYS` by applying the assignee filter for `Garanin.R.V` only from source identity evidence.

Agent result cannot be used as oracle. Do not compare counts only; compare exact key sets.

If the candidate source returns tasks but individual `read_unit` cannot expose `scrum_board_plugin_sprint`, report `050_VERDICT = RED` unless source evidence proves the attribute is absent from SWTR itself.

## Phase 6 — PO Agent exact-set check

Run fresh-session PO Agent query:

```text
Покажи задачи Гаранина в спринте DMS-SPRNT-2
```

Record:

- raw semantic frame;
- semantic audit result if available;
- grounded frame;
- capability name;
- capability args;
- response status;
- exact agent task keys;
- trace/error code;
- whether assignee and sprint_id survived semantic interpretation, grounding and capability args.

Compare:

```text
AGENT_KEYS == ORACLE_GARANIN_DMS_SPRINT2_KEYS
```

Also run a fail-closed guard:

```text
Покажи задачи Гаранина в спринте DMS-SPRNT-999999
```

Allowed: clarification or fail-closed. Not allowed: arbitrary tasks, tasks from another sprint, or completed empty result pretending the sprint was source-confirmed.

## Phase 7 — No-full-sync proof

Explicitly verify and record:

```text
FULL_TASK_SYNC_RUN = NO
FULL_TASK_SYNC_REQUIRED_BY_QA = NO
BOUNDED_ORACLE_ONLY = YES
```

Do not run full tenant-wide sync.

## Verdict rules

050 is GREEN only if all are true:

- focused tests pass or dependency skip is justified;
- stdio MCP transport is connected;
- direct known-good MCP-SWTR filter returns bounded `DMS-SPRNT-2` task keys;
- Harness bounded candidate endpoint returns compatible bounded `DMS-SPRNT-2` task keys;
- every candidate key is individually hydrated via SWTR read unit;
- `scrum_board_plugin_sprint` is verified per task;
- exact-set comparison for `Покажи задачи Гаранина в спринте DMS-SPRNT-2` passes;
- `DMS-SPRNT-999999` fails closed or clarifies;
- `FALSE_GREEN_COUNT = 0`;
- `SILENT_SLOT_DROP_COUNT = 0`;
- `INTERNAL_KEYERROR_COUNT = 0`;
- `QUERY_HTTP_500_COUNT = 0`;
- `FULL_TASK_SYNC_RUN = NO`.

050 is BLOCKED if direct source access is still unavailable due credentials/platform/runtime despite healthy code.

050 is RED if source access works but Harness/PO Agent drops constraints, cannot expose bounded source keys, wraps source errors as data, returns HTTP 500/internal traceback, uses full sync as oracle, or fails exact key-set comparison.

## Required report contents

The report must contain:

- branch and `START_HEAD`;
- service PIDs/ports;
- redacted production wiring evidence;
- focused test result;
- direct known-good MCP-SWTR filter evidence;
- Harness bounded source evidence;
- hydrated per-task SWTR relation table;
- exact key-set diffs;
- semantic/capability preservation evidence;
- fail-closed guard result;
- all mismatch traces;
- final verdict and footer.

## Required footer

```text
ASSIGNMENT_ID = CORE8_BOUNDED_SWTR_ORACLE_ACCESS_UNBLOCK_RETEST_050
START_HEAD = <sha>
REPORT_COMMIT = <sha-or-pending-before-commit>
FOCUSED_TESTS = PASS|FAIL|SKIPPED
MCP_SWTR_TRANSPORT = stdio|other
MCP_SWTR_TRANSPORT_CONNECTED = YES|NO
TASK_API_ROUTE_CONTRACT = SWTR_READ|OTHER
KNOWN_GOOD_FILTER_DIRECT_RESULT = TASK_KEYS|ACCESS_DENIED|ERROR|EMPTY|BLOCKED
KNOWN_GOOD_FILTER_TASK_COUNT = n
KNOWN_GOOD_FILTER_PARITY = PASS|FAIL|BLOCKED
HARNESS_SPRINT2_TASK_COUNT = n
HYDRATED_TASK_COUNT = n
ORACLE_PATH_PROVEN = YES|NO
CASE_GARANIN_DMS_SPRINT2_EXACT_SET = PASS|FAIL|BLOCKED
AGENT_KEY_COUNT = n
ORACLE_KEY_COUNT = n
MISSING_KEYS = [...]
EXTRA_KEYS = [...]
FOREIGN_SPRINT_TASK_COUNT = n
UNPROVEN_SPRINT_FAILCLOSED = YES|NO
FULL_TASK_SYNC_RUN = NO|YES
FULL_TASK_SYNC_REQUIRED_BY_QA = NO|YES
BOUNDED_ORACLE_ONLY = YES|NO
FALSE_GREEN_COUNT = n
SILENT_SLOT_DROP_COUNT = n
INTERNAL_KEYERROR_COUNT = n
QUERY_HTTP_500_COUNT = n
050_VERDICT = GREEN|RED|BLOCKED
READY_TO_RERUN_017_V2 = YES|NO
READY_TO_RESUME_GATE_E = NO
```

`READY_TO_RERUN_017_V2 = YES` is allowed only when `050_VERDICT = GREEN`, `ORACLE_PATH_PROVEN = YES`, exact-set PASS, no false greens, no silent slot drops and no HTTP 500.

`READY_TO_RESUME_GATE_E` remains `NO` in this assignment even if 050 is GREEN. Gate E resumes only after the subsequent full 017 V2/benchmark gate passes.

## Completion

Commit and push only the allowed report file. Then stop and return:

- report commit SHA;
- concise verdict;
- full report text.
