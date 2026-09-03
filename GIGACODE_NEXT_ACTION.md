# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_138_ASSIGNEE_409_FOCUSED_FORENSIC`

## Mission
Assignment 137 proved the exact-task / NOT_FOUND cluster GREEN for the owner fixes: existing exact task point-read works end-to-end and explicit MCP not-found is now mapped to HTTP 404 rather than source unavailable.

However, the same run could not complete protected assignee regressions because `/api/v1/swtr-read/assignee-tasks` returned HTTP 409 for Garanin and Kalachanov queries. Historical GREEN showed these same live assignee paths working. Before moving to sprint/release semantics and then Hermes architecture evolution, localize this 409 precisely.

You are QA/test executor only. Do NOT modify production/backend/frontend code, prompts, adapters, team config, AS21 data, source contracts or testing rules. Commit/push QA evidence only.

## Absolute rules
- REAL AS21/MCP-SWTR only. No local DB/sync/fake/mock/frozen truth.
- Do not call the 409 an environment issue without proving the first failing boundary.
- Do not modify production code.
- Use current branch `feat/core8-real-query-hardening-v2` and record exact HEAD.
- Hard restart Task API and Harness from current HEAD before testing.
- Concurrency=1; normal timeout 180s; transient transport retries 2 with 30s backoff.
- Do not run a full skill marathon.

# PHASE 0 — provenance and source health
1. Pull current branch and record exact HEAD + `git status --porcelain`.
2. Restart Task API and Harness from HEAD; record PIDs/start commands.
3. Prove REAL MCP-SWTR healthy with two known-good `read_unit` calls from different approved spaces.
4. Prove `search_users` and `find_units_by_filter` tools are present in the current MCP tool catalog.

# PHASE 1 — direct identity resolution forensic
For each person below, call REAL MCP `search_users` directly and preserve the complete sanitized response shape:
- `Garanin.R.V`
- `Гаранин Родион`
- `Kalachanov.V.V` if this is the configured login/external ID; otherwise derive the exact configured user identity from repository team config and record it
- `Калачанов`

For every result record all available identity fields (`code`, `login`, `externalId`, display/FIO/name fields, etc.) and pagination/container shape.

Answer explicitly:
- Does `search_users` return the canonical identifier in `code`, `login`, `externalId`, or another field?
- Does the current response differ from the assumption in `task-api/app/routers/swtr_assignee.py::_resolve_external_id()`?
- Does the resolver currently discard valid exact matches because it only accepts `code/login` and returns `code`?

# PHASE 2 — reproduce Task API 409 with raw detail
Call the live endpoint directly for:
- `/api/v1/swtr-read/assignee-tasks?assignee=Garanin.R.V`
- same with `space=DMS`
- Kalachanov canonical identifier

Capture:
- HTTP status;
- complete sanitized response body;
- exact `detail.assignee` and `detail.matches` from the 409;
- whether 409 occurs before `find_units_by_filter` is invoked.

If 409 is emitted by `_resolve_external_id`, prove which exact branch causes it:
```text
search_users rows
 -> candidates considered
 -> exact[] constructed
 -> len(exact)
 -> 409
```

# PHASE 3 — independent Oracle B
Bypass the Task API resolver and use the authoritative identifier actually returned/proven by MCP.

Execute direct REAL MCP `find_units_by_filter` with:
`assigned_to = "<AUTHORITATIVE_ID>"`

For Garanin and Kalachanov:
- read all pages;
- normalize exact task-key sets;
- partition by approved spaces WMB/STS/OLP/DMS/CRPV;
- record counts and exact keys;
- no historical counts reused.

This establishes whether the source itself works while Task API returns 409.

# PHASE 4 — production Agent A trace
With fresh session IDs run:
- `Задачи Гаранина`
- `Задачи Гаранина в DMS`
- `Задачи Калачанова`

Capture:
```text
INTERPRETER_CLASS
LLM_USED
RAW_SEMANTIC_FRAME
GROUNDED_FRAME
RESOLVED_SKILL
CAPABILITY_ARGS
TASK_API_REQUEST
TASK_API_STATUS/BODY
FINAL_AGENT_STATUS/ANSWER
```

Prove whether the first failing boundary is identity resolution, semantic grounding, adapter, or MCP/source.

# PHASE 5 — compatibility analysis
Inspect current production code read-only and compare the observed MCP identity schema with:
- `task-api/app/routers/swtr_assignee.py::_resolve_external_id()`
- production adapter `search_tasks()` assignee route
- team/member grounding output

Required conclusion format:
```text
LAST_CORRECT_ARTIFACT = ...
FIRST_INCORRECT_ARTIFACT = ...
FIRST_FAILING_BOUNDARY = ...
EXACT_FILE = ...
EXACT_FUNCTION = ...
EXACT_EXPRESSION/ASSUMPTION = ...
MINIMAL_OWNER_FIX_SCOPE = ...
```

Do not propose fallback to local DB or sync.

# PHASE 6 — protected exact-task regression
Confirm the just-fixed cluster remains GREEN:
- existing `DMS-380` point-read -> 200 / Agent exact key;
- nonexistent `DMS-999999999` -> Task API 404 / Agent "не найдена".

# Final report
Write:
`po-agent-platform-v2/qa_reports/ASSIGNEE_409_FOCUSED_FORENSIC_138.md`

Allowed verdicts:
- `ASSIGNEE_IDENTITY_BOUNDARY_PROVEN_OWNER_FIX_READY`
- `ASSIGNEE_SOURCE_OUTAGE_PROVEN`
- `ASSIGNEE_SEMANTIC_BOUNDARY_PROVEN`
- `ASSIGNEE_409_NOT_REPRODUCED`
- `MORE_FORENSIC_REQUIRED`

The report must include current live Oracle task-key sets for Garanin and Kalachanov where source permits, exact 409 cause, source-vs-product classification, and no production changes.

Commit/push QA artifacts only and STOP.

## Start now
Execute Assignment 138 autonomously.