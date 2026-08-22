# Assignment 051 — Clean-Tree Oracle Exact-Set Retest

## Purpose

Assignment 050 proved a major unblock: bounded SWTR access for `DMS-SPRNT-2` now returns real task keys. However the 050 GREEN verdict is not accepted as the final gate because its evidence has gaps:

- it started from `START_HEAD = 3e363271`, before the clean-tree guard commit;
- the screenshot showed a tracked local modification in `po-agent-platform-v2/src/po_agent/main.py` during the run;
- the PO Agent exact-set query timed out and was inferred rather than executed;
- the footer mixed total oracle count (`22`) with the filtered Garanin oracle count (`0`);
- per-task hydration must be proven from individual SWTR task reads, not only from the sprint-list candidate response.

This assignment is a narrow corrective retest. Do not run the full 017 V2 matrix here.

## Repository

`Sovietbear86/PO-Agent-Architecture-Review`

## Branch

`feat/core8-real-query-hardening-v2`

## Allowed output

Commit and push only:

`qa_reports/CORE8_ORACLE_CLEAN_TREE_EXACT_SET_RETEST_051.md`

Do not commit JSON, helper scripts, runner changes, wrapper changes, `.env`, credentials, logs, screenshots, historical reports, roadmap edits or production changes.

## Fixed role

You are QA/tester only.

Do not modify production code, prompts, adapters, tests, fixtures, QA runners, acceptance runners, repository/local configuration, AS21/SWTR data, historical reports, roadmap files or learning state.

## Autonomous execution

The repository owner pre-authorizes this QA batch. Do not ask for confirmation after routine read-only calls, local service restarts, diagnostics, tests, allowed report commit or allowed report push.

Ask only if continuing requires a missing credential, unavoidable platform approval, write outside the report allowlist, production/source-data/config mutation, destructive out-of-scope action or scope expansion.

## Mandatory preflight

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `START_HEAD = git rev-parse HEAD`.
4. `START_HEAD` must include the clean-tree guard commit `e3c9b3850208bb3287a42d421de1a04b87c90661`.
5. Read this assignment and `GIGACODE_NEXT_ACTION.md` from `START_HEAD`.
6. Verify the active assignment is 051 and the allowed report path is exactly:
   `qa_reports/CORE8_ORACLE_CLEAN_TREE_EXACT_SET_RETEST_051.md`

## Phase 0 — Clean tracked tree guard

Before starting services, run:

```bash
git status --short
git diff --name-only
git diff --cached --name-only
```

Rules:

- If any tracked production/config/test/runner/prompt/roadmap/wrapper file is modified or staged, stop.
- Write the allowed 051 report with `051_VERDICT = BLOCKED`, include the exact changed file list, set `LOCAL_TRACKED_RUNTIME_PATCH_PRESENT = YES`, commit only that report and stop.
- Untracked `.env` or ignored secret files may exist but must not be printed or committed.
- Untracked helper scripts/wrappers inside this repository must not be used as runtime dependencies. If the runtime depends on an untracked repo-local wrapper, stop with `UNTRACKED_RUNTIME_DEPENDENCY_USED = YES`.
- External MCP-SWTR runtime files outside this repository may be used as environment setup evidence only with secret values redacted.

## Phase 1 — Focused regression tests

Run:

```bash
cd task-api
python3 -m pytest tests/test_swtr_mcp_client.py tests/test_swtr_read_facade.py -q
```

Record exact result.

## Phase 2 — Start clean-head runtime

Start Task API and PO Agent from `START_HEAD` only.

Required:

- `SWTR_MCP_TRANSPORT=stdio`;
- `PO_AGENT_AS21_MODE=task-api`;
- `PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8003`;
- working LLM endpoint for the PO Agent semantic interpreter;
- redacted process/env evidence;
- no fake AS21 adapter for acceptance outputs.

Record PIDs, ports, package roots and expected/loaded git heads.

## Phase 3 — Health and bounded source proof

Call:

```bash
curl -s http://127.0.0.1:8003/api/v1/swtr-read/health
curl -s http://127.0.0.1:8004/api/v1/ops/as21-diagnostics
curl -i "http://127.0.0.1:8003/api/v1/swtr-read/sprints/DMS-SPRNT-2/tasks?space=DMS&complete=true"
```

Record:

- transport kind;
- required MCP tools;
- Task API route contract;
- task key count;
- exact DMS-SPRNT-2 candidate key set;
- absence of SWTR access denied, wrapped errors, HTTP 500 and tracebacks.

## Phase 4 — Individual SWTR task hydration

For every candidate key returned for `DMS-SPRNT-2`, call:

```text
GET /api/v1/swtr-read/tasks/<TASK_KEY>
```

For every individually read task unit, extract source-backed:

- task key;
- assignee/login;
- status;
- space/product;
- `scrum_board_plugin_sprint`.

Build:

```text
ORACLE_DMS_SPRINT2_KEYS = all individually hydrated keys whose scrum_board_plugin_sprint == DMS-SPRNT-2
ORACLE_GARANIN_DMS_SPRINT2_KEYS = subset where source assignee/login == Garanin.R.V
```

Do not use the PO Agent response as oracle. Do not use only the sprint candidate response as proof of final membership. Do not compare counts only.

If individual `read_unit` cannot expose `scrum_board_plugin_sprint`, report `051_VERDICT = RED` unless source evidence proves the attribute is unavailable in SWTR itself.

## Phase 5 — Real PO Agent exact-set execution

Run fresh-session PO Agent query with the real semantic interpreter:

```text
Покажи задачи Гаранина в спринте DMS-SPRNT-2
```

Record:

- response status;
- raw semantic frame;
- grounded frame;
- capability name;
- capability args;
- exact agent task keys;
- trace/error code;
- whether `assignee` and `sprint_id` survived to capability execution.

Compare:

```text
AGENT_KEYS == ORACLE_GARANIN_DMS_SPRINT2_KEYS
```

If `ORACLE_GARANIN_DMS_SPRINT2_KEYS` is empty, `COMPLETED + empty` is acceptable only when the independent hydrated oracle proves the empty set.

LLM timeout, semantic model unavailable, or inferred/expected PO Agent result is not a PASS. It is `BLOCKED`.

## Phase 6 — Unproven sprint fail-closed guard

Run fresh-session query:

```text
Покажи задачи Гаранина в спринте DMS-SPRNT-999999
```

Allowed:

- clarification;
- fail-closed source-backed error;
- source-backed message that the sprint cannot be confirmed.

Not allowed:

- arbitrary tasks;
- tasks from another sprint;
- `COMPLETED + empty` pretending the sprint was source-confirmed.

## Verdict rules

051 is GREEN only if:

- clean tracked tree guard passes;
- focused tests pass or skip is justified;
- clean-head runtime identity is proven;
- bounded source returns DMS-SPRNT-2 candidate keys;
- every candidate key is individually hydrated;
- sprint membership is confirmed from individual task reads;
- real PO Agent exact-set query executes without LLM timeout;
- exact set matches the filtered hydrated oracle;
- unproven sprint fails closed or clarifies;
- no full sync was run;
- no false green, silent slot drop, HTTP 500 or internal traceback.

051 is BLOCKED if:

- local tracked runtime patch is present;
- LLM endpoint/semantic interpreter is unavailable;
- credentials/platform prevent source reads despite clean code;
- runtime cannot be started from clean branch HEAD.

051 is RED if:

- source access works but Harness/PO Agent drops filters, misroutes capabilities, wraps source errors as data, returns HTTP 500/internal traceback, uses full sync as oracle, or fails exact key-set comparison.

## Required footer

```text
ASSIGNMENT_ID = CORE8_ORACLE_CLEAN_TREE_EXACT_SET_RETEST_051
START_HEAD = <sha>
REPORT_COMMIT = <sha-or-pending-before-commit>
CLEAN_TREE_GUARD = PASS|FAIL
LOCAL_TRACKED_RUNTIME_PATCH_PRESENT = YES|NO
UNTRACKED_RUNTIME_DEPENDENCY_USED = YES|NO
FOCUSED_TESTS = PASS|FAIL|SKIPPED
MCP_SWTR_TRANSPORT = stdio|sse|other
MCP_SWTR_TRANSPORT_CONNECTED = YES|NO
TASK_API_ROUTE_CONTRACT = SWTR_READ|OTHER
HARNESS_SPRINT2_TASK_COUNT = n
HYDRATED_TASK_COUNT = n
ORACLE_PATH_PROVEN = YES|NO
ORACLE_DMS_SPRINT2_KEY_COUNT = n
ORACLE_GARANIN_DMS_SPRINT2_KEY_COUNT = n
AGENT_KEY_COUNT = n
CASE_GARANIN_DMS_SPRINT2_EXACT_SET = PASS|FAIL|BLOCKED
MISSING_KEYS = [...]
EXTRA_KEYS = [...]
FOREIGN_SPRINT_TASK_COUNT = n
UNPROVEN_SPRINT_FAILCLOSED = YES|NO
FULL_TASK_SYNC_RUN = NO|YES
FALSE_GREEN_COUNT = n
SILENT_SLOT_DROP_COUNT = n
INTERNAL_KEYERROR_COUNT = n
QUERY_HTTP_500_COUNT = n
LLM_TIMEOUT_COUNT = n
051_VERDICT = GREEN|RED|BLOCKED
READY_TO_RERUN_017_V2 = YES|NO
READY_TO_RESUME_GATE_E = NO
```

`READY_TO_RERUN_017_V2 = YES` is allowed only when `051_VERDICT = GREEN`, `ORACLE_PATH_PROVEN = YES`, exact-set PASS, no LLM timeout, no false greens, no silent slot drops and no HTTP 500.

Gate E remains `NO` here. Gate E resumes only after the subsequent full 017 V2/benchmark rerun passes.

## Completion

Commit and push only the allowed report file. Then stop and return:

- report commit SHA;
- concise verdict;
- full report text.
