# Assignment 052 — Full 017 V2 Clean-Oracle Rerun

## Purpose

Assignment 051 is accepted as GREEN for the bounded oracle unblock:

```text
CLEAN_TREE_GUARD = PASS
ORACLE_PATH_PROVEN = YES
CASE_GARANIN_DMS_SPRINT2_EXACT_SET = PASS
LLM_TIMEOUT_COUNT = 0
READY_TO_RERUN_017_V2 = YES
```

This assignment resumes the full 017 V2/Core-8 real-query hardening rerun on clean source evidence.

The purpose is to decide whether the project can resume Gate E. Do not run a partial matrix and declare GREEN. Do not repeat the 033/035 evidence problems.

## Repository

`Sovietbear86/PO-Agent-Architecture-Review`

## Branch

`feat/core8-real-query-hardening-v2`

## Allowed output

Commit and push only:

`qa_reports/CORE8_017V2_FULL_CLEAN_ORACLE_RERUN_052.md`

Do not commit JSON, helper scripts, runner changes, wrapper changes, `.env`, credentials, logs, screenshots, historical reports, roadmap edits, production changes, prompts, tests, fixtures, local configuration or AS21/SWTR data.

## Fixed role

You are QA/tester only.

- Do not modify production code, prompts, adapters, tests, fixtures, QA runners, acceptance runners, repository/local configuration, AS21/SWTR data, historical reports, roadmap files or learning state.
- Do not repair discovered production defects.
- Do not weaken, skip, reword or replace existing 017 V2/026/029 acceptance cases.
- Do not compare counts only when an exact oracle is required.
- Do not run full tenant-wide task sync.
- Do not use PO Agent output as oracle.
- Never print, commit or paste token values.

## Autonomous execution

The repository owner pre-authorizes this QA batch. Do not ask for confirmation after each routine step, integration call, local service restart, read-only AS21/SWTR query, MCP-SWTR diagnostic, Task API diagnostic, HTTP diagnostic, test command, allowed report commit or allowed report push.

Ask only if continuing requires a missing credential, unavoidable platform approval, write outside the report allowlist, production/source-data/config mutation, destructive out-of-scope action or scope expansion.

## Mandatory preflight

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `START_HEAD = git rev-parse HEAD`.
4. Read this assignment and `GIGACODE_NEXT_ACTION.md` from `START_HEAD`.
5. Verify the active assignment is 052 and the allowed report path is exactly:
   `qa_reports/CORE8_017V2_FULL_CLEAN_ORACLE_RERUN_052.md`
6. Read:
   - `qa_reports/CORE8_ORACLE_CLEAN_TREE_EXACT_SET_RETEST_051.md`
   - `qa_reports/CORE8_BOUNDED_SWTR_ORACLE_ACCESS_UNBLOCK_RETEST_050.md`
   - `qa_reports/CORE8_BOUNDED_SWTR_ORACLE_ACCESS_PROOF_049.md`
   - `qa_reports/CORE8_017V2_MATRIX_EVIDENCE_AUDIT_036.md` if present
   - the current 017 V2 / 026 V2 runner or checklist files used by the repository.
7. Verify no prohibited files are staged.

## Phase 0 — Clean tracked tree guard

Before starting services, run:

```bash
git status --short
git diff --name-only
git diff --cached --name-only
```

Rules:

- If any tracked production/config/test/runner/prompt/roadmap/wrapper file is modified or staged, stop.
- Write the allowed 052 report with `052_VERDICT = BLOCKED`, include the exact changed file list, set `LOCAL_TRACKED_RUNTIME_PATCH_PRESENT = YES`, commit only that report and stop.
- Untracked `.env` or ignored secret files may exist but must not be printed or committed.
- Untracked helper scripts/wrappers inside this repository must not be used as runtime dependencies.
- External MCP-SWTR runtime files outside this repository may be used as environment setup evidence only with secret values redacted.

## Phase 1 — Start clean-head runtime

Start Task API and PO Agent from `START_HEAD` only.

Required:

- Task API uses `SWTR_MCP_TRANSPORT=stdio` and direct `SWTR_TOKEN` in Task API environment;
- PO Agent uses `PO_AGENT_AS21_MODE=task-api`;
- PO Agent uses a working LLM endpoint for production semantic interpretation;
- expected package root and expected git head checks are set for PO Agent;
- no fake AS21 adapter for acceptance outputs;
- no full task sync.

Record PIDs, ports, package roots, expected/loaded git heads and redacted env shape.

## Phase 2 — Production preflight

Run and record:

```bash
curl -s http://127.0.0.1:8003/health
curl -s http://127.0.0.1:8003/api/v1/swtr-read/health
curl -s http://127.0.0.1:8004/health
curl -s http://127.0.0.1:8004/api/v1/ops/as21-diagnostics
```

Required:

- Task API healthy;
- MCP-SWTR transport connected;
- required MCP tools present;
- PO Agent adapter is `task-api`;
- semantic mode is production LLM, not deterministic phrase routing;
- Task API route contract remains `SWTR_READ`;
- no secrets in responses.

If preflight fails, report BLOCKED with exact evidence. Do not run the full matrix on a degraded runtime.

## Phase 3 — Oracle availability smoke

Before the full matrix, re-run the bounded oracle smoke from 051:

```text
GET /api/v1/swtr-read/sprints/DMS-SPRNT-2/tasks?space=DMS&complete=true
POST /api/v1/query: Покажи задачи Гаранина в спринте DMS-SPRNT-2
POST /api/v1/query: Покажи задачи Гаранина в спринте DMS-SPRNT-999999
```

Required:

```text
ORACLE_PATH_PROVEN = YES
CASE_GARANIN_DMS_SPRINT2_EXACT_SET = PASS
UNPROVEN_SPRINT_FAILCLOSED = YES
```

If this regresses, stop and report RED/BLOCKED. Do not run the full matrix.

## Phase 4 — Full 017 V2 real-query matrix

Execute the complete current 017 V2 real-query matrix as defined in the repository. The run must include every required functional case and every correction-loop case.

Known historical scope from prior reports is at least:

```text
TOTAL_FUNCTIONAL_TESTS >= 122
CORRECTION_LOOP_TOTAL = 15
```

If the current repository defines a different exact count, record the source file and explain the count. Do not silently reduce scope.

For every case ID record:

- case id;
- category;
- exact query text;
- expected behavior;
- response status;
- capability/skill;
- key filters preserved;
- oracle type used;
- expected key set where applicable;
- agent key set where applicable;
- missing/extra keys;
- PASS/FAIL/BLOCKED/NOT_EXECUTED;
- trace id or error code.

At minimum cover and summarize these groups when present in the canonical matrix:

- task search / task intelligence;
- summaries;
- task quality;
- sprint health;
- velocity / flow metrics;
- team workload;
- competency match;
- release health;
- cross-skill / explicit identifier / ambiguity / fail-closed cases;
- correction loop CL-01..CL-15.

## Phase 5 — Required protected checks

The report must explicitly state results for:

- production architecture preflight;
- Core-8 real-data smoke;
- B1-B8 paraphrase invariance;
- person/product/status robustness;
- multi-filter preservation;
- explicit identifier safety;
- correction/recheck loop CL-01..CL-15;
- ambiguity and fail-closed;
- focused semantic regression tests;
- full relevant regression suite if feasible.

If a required command cannot be executed due environment/runtime limits, report BLOCKED with exact command, timeout/dependency and partial evidence. Do not infer PASS.

## Phase 6 — Evidence consistency audit

Before committing the report, self-audit it for the failures seen in 033/035:

- aggregate totals must equal the sum of per-case rows;
- no category may be marked executed if its per-case rows are missing;
- no GREEN verdict while any required case is FAIL, BLOCKED or NOT_EXECUTED;
- `CORRECTION_LOOP_PASS` must be out of 15 if CL-01..CL-15 is the active scope;
- `READY_TO_RESUME_GATE_E = YES` only if all final GREEN criteria are met.

## Verdict rules

052 is GREEN only if:

- clean tracked tree guard passes;
- production preflight passes;
- oracle smoke from 051 still passes;
- full 017 V2 matrix is fully executed;
- every required case has per-ID evidence;
- functional fail count is zero;
- functional not-executed count is zero;
- correction loop is 15/15;
- false green count is zero;
- silent slot drop count is zero;
- query HTTP 500 count is zero;
- no semantic crutches/keyword phrase routing are introduced;
- no full tenant sync is used;
- evidence consistency audit passes.

052 is BLOCKED if:

- clean tree fails;
- runtime/preflight cannot be made healthy without production changes;
- LLM/source dependency is unavailable;
- complete matrix cannot finish within available execution window and no false PASS is claimed.

052 is RED if:

- any fully executed required functional case fails;
- exact-set oracle disproves an agent result;
- constraints are silently dropped;
- source errors are wrapped as successful task data;
- HTTP 500/internal traceback occurs in query path;
- unproven sprint returns arbitrary tasks or `COMPLETED + empty` without independent empty oracle;
- report tries to claim GREEN with inconsistent evidence.

## Required footer

```text
ASSIGNMENT_ID = CORE8_017V2_FULL_CLEAN_ORACLE_RERUN_052
START_HEAD = <sha>
REPORT_COMMIT = <sha-or-pending-before-commit>
CLEAN_TREE_GUARD = PASS|FAIL
LOCAL_TRACKED_RUNTIME_PATCH_PRESENT = YES|NO
PRODUCTION_PREFLIGHT = x/y
MCP_SWTR_TRANSPORT = stdio|sse|other
MCP_SWTR_TRANSPORT_CONNECTED = YES|NO
TASK_API_ROUTE_CONTRACT = SWTR_READ|OTHER
ORACLE_PATH_PROVEN = YES|NO
ORACLE_SMOKE_EXACT_SET = PASS|FAIL|BLOCKED
UNPROVEN_SPRINT_FAILCLOSED = YES|NO
017V2_FULLY_EXECUTED = YES|NO
TOTAL_FUNCTIONAL_TESTS = n
FUNCTIONAL_PASS = n
FUNCTIONAL_FAIL = n
FUNCTIONAL_NOT_EXECUTED = n
CORRECTION_LOOP_PASS = x/15
CORE8_REAL_DATA = x/8
PARAPHRASE_INVARIANCE = x/8
MULTIFILTER_PRESERVATION = x/y
FALSE_GREEN_COUNT = n
SILENT_SLOT_DROP_COUNT = n
SEMANTIC_CRUTCH_COUNT_PRODUCTION = n
QUERY_HTTP_500_COUNT = n
INTERNAL_KEYERROR_COUNT = n
FULL_TASK_SYNC_RUN = NO|YES
EVIDENCE_CONSISTENCY_AUDIT = PASS|FAIL
052_VERDICT = GREEN|RED|BLOCKED
READY_TO_RESUME_GATE_E = YES|NO
READY_FOR_FRONTEND_FINALIZATION = YES|NO
```

`READY_TO_RESUME_GATE_E = YES` is allowed only when `052_VERDICT = GREEN`, the full matrix is executed, evidence consistency audit passes, all required functional/correction criteria are GREEN and no false green/silent slot drop/HTTP 500 remains.

`READY_FOR_FRONTEND_FINALIZATION` remains `NO` until Gate E acceptance is complete.

## Completion

Commit and push only the allowed report file. Then stop and return:

- report commit SHA;
- concise verdict;
- full report text.
