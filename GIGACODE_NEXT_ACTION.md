# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_142_ASSIGNEE_TRANSFORM_IDENTITY_AB`

## Mission
Assignment 141 proved two concrete assignee defects:
1. REAL MCP `find_units_by_filter` returns nested rows shaped as `{unit:{...}, attributes:[...]}`, while `_canonical_row()` looked only at flat row fields and discarded all source tasks.
2. Natural Russian surname forms such as `Калачанова` can fail source identity search even though the configured/source canonical identity is `Kalachanov.V.V`.

Owner commits:
- `b43b88deb1dcdb7cb0bfe8223385f7075b9eeaf2` — normalize nested MCP `unit` rows and nested attribute descriptors; allow unique authoritative search-result code fallback.
- `44499605934725c1750aa32db5ae3cc90439b0f2` — conservative Russian masculine-genitive surname retry (`...а` -> nominative candidate) only when the first authoritative search returns zero rows; final identity must still resolve to exactly one unique source code.

Your job is focused REAL A/B certification. QA/test executor only. Do not modify production/backend/frontend code.

## Absolute rules
- Pull `feat/core8-real-query-hardening-v2`; record exact HEAD and prove both owner commits are ancestors.
- Hard restart Task API and Harness from HEAD.
- REAL AS21/MCP-SWTR only; no local DB/sync/fake/mock/frozen truth.
- Oracle B must independently call direct MCP `search_users` + `find_units_by_filter` using the live `request` schemas.
- Exact task-key-set equality is mandatory; counts alone are insufficient.
- Fresh session per Agent A case; concurrency=1; normal timeout 180s, paginated calls 300s, transient retry 2 with 30s backoff.
- Do not broaden to sprint/release or full catalog.

# PHASE 0 — provenance/source/schema
1. Record HEAD/worktree/PIDs/restart commands.
2. Prove `search_users` and `find_units_by_filter` current request schemas.
3. Prove two known-good direct `read_unit` calls from different approved spaces.

# PHASE 1 — Oracle B exact truth
Fresh direct REAL MCP:
- Garanin.R.V all tasks and DMS subset;
- Kalachanov.V.V all tasks.
Read all pages. Normalize approved spaces WMB/STS/OLP/DMS/CRPV.
Persist exact keys, per-space counts and total approved set. Do not reuse Assignment 141 numbers as truth.

# PHASE 2 — transformation certification
Call Task API:
- `/api/v1/swtr-read/assignee-tasks?assignee=Garanin.R.V`
- same with `space=DMS`
- `/api/v1/swtr-read/assignee-tasks?assignee=Kalachanov.V.V`

For representative rows prove:
- nested `unit.code` becomes `source_id`;
- nested `unit.summary` becomes title;
- nested `unit.space.code` becomes `source_data.swtr_space`;
- nested attribute descriptor `{attribute:{code:...},value:...}` is normalized;
- approved-space filtering retains legitimate rows.

Require exact Task API key-set equality vs Oracle B for all three cases.

# PHASE 3 — identity resolution certification
Test Task API identity forms independently:
- `Garanin.R.V`
- `Garanin`
- `Kalachanov.V.V`
- `Kalachanov`
- `Калачанов`
- `Калачанова`

For each capture search attempt(s), canonical resolved code, HTTP result, and ambiguity behavior.

Acceptance safety rules:
- exact code/login works;
- a unique authoritative source result may resolve to its unique code;
- Russian genitive retry is allowed only after zero initial results and only if the retry yields exactly one unique canonical code;
- zero or multiple unique canonical codes must still fail closed (409), never guess.

Include one negative/ambiguous identity control if the source can produce it safely. If no naturally ambiguous search is available, inspect resolver behavior and mark `AMBIGUOUS_CASE_NOT_OBSERVED`, not fake it.

# PHASE 4 — Agent A natural-language parity
Fresh unique sessions, execute ALL:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова`

Capture interpreter class, `LLM_USED`, raw frame, grounded frame, capability args, source route, status, exact task keys and answer.

Require:
- no first-turn correction contamination;
- Russian answer;
- no source-unavailable wording on healthy source;
- Agent A exact key set equals fresh Oracle B for each corresponding query.

# PHASE 5 — protected exact-task regression
- `DMS-380` exists: Task API 200 and Agent exact key.
- `DMS-999999999`: Task API 404 and Agent says task not found, never source unavailable.

# PHASE 6 — anti-surrogate/source integrity
Prove:
- no local task DB/sync used as acceptance truth;
- direct live route is `search_users -> find_units_by_filter`;
- all pages consumed;
- no AS21 writes.

# FINAL REPORT
Write:
`po-agent-platform-v2/qa_reports/ASSIGNEE_TRANSFORM_IDENTITY_AB_142.md`

Allowed verdicts:
- `ASSIGNEE_TRANSFORM_IDENTITY_GREEN`
- `ASSIGNEE_TRANSFORM_PARITY_RED`
- `ASSIGNEE_IDENTITY_RED`
- `ASSIGNEE_AGENT_PARITY_RED`
- `PROTECTED_EXACT_TASK_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN is forbidden unless all three Agent A natural-language cases match fresh independent Oracle B exact task-key sets and the Task API transformation no longer drops nested source rows.

Commit/push QA report only and STOP.

## Start now
Execute Assignment 142 completely.