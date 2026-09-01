# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_118_SCOPED_SEMANTIC_INTERPRETER_RECOVERY`

## Why 117R is not sufficient
Assignment 117R proved a real Browser/Harness failure at semantic interpretation for the exact query `Задачи Гаранина`, but its Oracle/control-member evidence is NOT accepted as authoritative correctness evidence:
- it used `Антонов`, who is outside the owner-approved PO team scope;
- Oracle `get_my_tasks(assignee="Гаранин")` and `get_my_tasks(assignee="Антонов")` returned the same 50 CORESUP tasks, which strongly suggests the tool/filter semantics were misunderstood or the assignee filter was not actually applied;
- CORESUP is outside the owner-approved product spaces for this project.

The first task is therefore to recover the semantic interpreter and establish a scoped, valid Oracle. Do NOT investigate assignee extraction, synchronization, local DB population, frontend widgets, or unrelated spaces/users in this assignment.

## Owner-approved scope — absolute
Only these AS21 spaces may be used for task evidence or Oracle results:
- `WMB`
- `STS`
- `OLP`
- `DMS`
- `CRPV`

Only team members defined in the repository/project team data files are allowed as member-query subjects or controls. Before testing, read the authoritative team data files and write the resulting allowed member/login list into the QA report. Do NOT invent or discover arbitrary AS21 users. `Антонов` and any other user not present in those team files are forbidden test subjects.

If a tool returns tasks from any other space (for example `CORESUP`), those rows MUST be excluded from owner-scope truth and MUST trigger `ORACLE_SCOPE_VIOLATION` until the correct server-side or deterministic scoped filtering is proven.

## Role boundary
You are QA / forensic executor only.
DO NOT modify production/backend/frontend code, prompts, skills, semantic implementation, Task API, MCP-SWTR, team data, AS21 data, testing rules, or this file.
Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`.

## Absolute prohibitions
- NO task synchronization/population utilities.
- NO local DB refresh/population.
- NO local DB/cache as authoritative source or Oracle.
- NO fake/mock/frozen data.
- NO AS21 writes.
- NO arbitrary users outside repository team data.
- NO spaces outside WMB/STS/OLP/DMS/CRPV.
- NO `Антонов` control.
- NO speculative production fix.
- Do not declare Oracle success from counts alone.

## Goal
Recover the exact reason why the previously working natural-language query `Задачи Гаранина` now fails at semantic interpretation, prove whether this is runtime/model/configuration drift or a code regression, and then re-run a correctly scoped Browser/Harness/REAL-AS21 comparison.

## Phase 0 — exact provenance and allowed scope
1. Fetch/pull `feat/core8-real-query-hardening-v2`; record exact HEAD and clean worktree.
2. Record PID, port, command line, start time and relevant non-secret environment/config identity for Frontend, Harness and Task API.
3. Locate/read the repository/project team data used by the application. Record the exact allowed team member names/logins. Use only this list for member tests.
4. Hard-limit all Oracle/task evidence to WMB/STS/OLP/DMS/CRPV.
5. Verify MCP-SWTR health and one REAL read in DMS or OLP.
6. Sync/population counters must stay zero.

## Phase 1 — semantic interpreter health forensic
Reproduce exactly through Direct Harness with fresh session IDs:
- `Задачи Гаранина`
- one exact task lookup such as a known DMS task key
- `Задачи спринта DMS-SPRNT-2`
- one simple non-member query that previously worked

For each capture:
- HTTP status;
- Harness result/warnings;
- semantic model/provider identifier if exposed;
- raw exception class/message from Harness logs (redact secrets);
- model response body or parse fragment when safe and available;
- whether failure is MODEL_CALL, TIMEOUT, HTTP/provider error, empty output, malformed JSON, schema validation, or post-parse semantic validation;
- elapsed time.

Do not stop at the generic warning `semantic_interpretation_failure`. Find the exact FIRST_FAILING_BOUNDARY.

Allowed semantic boundaries:
- `SEMANTIC_MODEL_PROCESS_NOT_RUNNING`
- `SEMANTIC_MODEL_ENDPOINT_UNREACHABLE`
- `SEMANTIC_MODEL_AUTH_OR_CONFIG`
- `SEMANTIC_MODEL_TIMEOUT`
- `SEMANTIC_MODEL_HTTP_ERROR`
- `SEMANTIC_MODEL_EMPTY_RESPONSE`
- `SEMANTIC_MODEL_MALFORMED_JSON`
- `SEMANTIC_SCHEMA_VALIDATION`
- `SEMANTIC_POST_PARSE_LOGIC`
- `SEMANTIC_CODE_REGRESSION`

`SEMANTIC_MODEL_UNAVAILABLE / LLM_JSON_PARSE_FAILURE` without exact evidence is not a sufficient final boundary.

## Phase 2 — compare with last known working state without modifying current code
Use git history/read-only inspection to identify the last known commit/report where `Задачи Гаранина` was actually executed successfully through Agent/Harness (not merely Oracle/direct AS21).
Compare only the semantic-interpreter-related files/config/startup contract between that known-working state and current HEAD.

Report:
- changed files/commits relevant to semantic interpretation;
- runtime/provider/config drift even if git code did not change;
- whether rollback baseline itself contains the failure;
- most likely exact regression boundary.

Do NOT checkout/reset/cherry-pick or change production code during this QA assignment.

## Phase 3 — establish a VALID scoped Oracle for Garanin
The Oracle must prove tasks for `Garanin.R.V` only within WMB/STS/OLP/DMS/CRPV.

Do not assume `get_my_tasks(assignee="Гаранин")` filters correctly. First validate tool semantics.

Requirements:
1. Inspect the live MCP tool schema/documentation for the candidate member-search tool(s).
2. Use exact identity/login supported by the tool, preferring repository team login such as `Garanin.R.V` when supported.
3. Prove assignee filtering by inspecting returned `assigned_to` source attributes for sample rows.
4. Prove every returned row belongs to WMB/STS/OLP/DMS/CRPV.
5. If server-side filtering cannot enforce both member and space, deterministically filter the complete REAL AS21 result in QA memory only; do not persist/sync anything.
6. Read all pages required for completeness.
7. Record exact task-key set, not only count.

If the candidate tool returns the same unrelated rows for two different users or returns out-of-scope spaces, classify `ORACLE_TOOL_FILTER_NOT_PROVEN` and choose another valid MCP mechanism before using Oracle results.

## Phase 4 — allowed control member
Choose exactly one additional member ONLY from the authoritative team data file and only if Oracle independently proves a non-empty scoped task set for that member.
Do not use arbitrary AS21 people.

## Phase 5 — three-way retest only after semantic path is understood
Run exact `Задачи Гаранина`:
A1. Browser UI, fresh session.
A2. Direct Harness, fresh session.
B. Valid scoped REAL AS21 Oracle from Phase 3.

Capture exact task-key sets and path/elapsed/status.

If semantic interpretation still fails, A1/A2 may have no task keys; report the semantic boundary and do NOT invent a downstream routing conclusion that was never reached.

If semantic interpretation succeeds, continue tracing actual downstream route and compare:
`Browser keys == Direct Harness keys == scoped Oracle keys`.

## Phase 6 — guardrail regression
Verify these explicit behavioral guardrails:
- Query `Задачи Гаранина` must never invent a sprint.
- User-facing text must be Russian.
- No team member outside authoritative team data may appear as an automatically chosen control/entity.
- No tasks outside WMB/STS/OLP/DMS/CRPV may be used as positive evidence for PO-team task queries.
- No local DB/sync may be used to make results pass.

## Mandatory counters
Report actual values:
- Browser natural-language requests >= 1
- Direct Harness natural-language requests >= 4
- valid scoped Oracle REAL AS21 reads >= 1
- out-of-scope Oracle rows observed (count)
- arbitrary/non-team member test subjects = 0
- sync/population runs = 0
- local DB authoritative reads = 0
- fake/mock/frozen reads = 0
- AS21 writes = 0

## Output
Primary report:
`po-agent-platform-v2/qa_reports/SCOPED_SEMANTIC_INTERPRETER_RECOVERY_118.md`

Optional evidence prefix:
`SCOPED_SEMANTIC_INTERPRETER_RECOVERY_118_`

Allowed final verdicts:
- `SEMANTIC_RUNTIME_OR_CONFIG_DEFECT_PROVEN`
- `SEMANTIC_CODE_REGRESSION_PROVEN`
- `SEMANTIC_INTERPRETER_RECOVERED_OR_HEALTHY`
- `SEMANTIC_AND_ORACLE_DEFECTS_PROVEN`
- `ORACLE_TOOL_FILTER_NOT_PROVEN`
- `BLOCKED_BY_ENVIRONMENT`

## Finish
Commit/push only QA report/evidence, provide full SHA, then STOP.

## Start now
Execute Assignment 118 autonomously. Do not ask for confirmation between phases. Do not change production code. Do not synchronize/populate local task data.