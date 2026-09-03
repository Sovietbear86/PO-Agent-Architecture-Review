# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_137_NOT_FOUND_MAPPING_FOCUSED_AB`

## Mission
Assignment 136 proved owner fix `dbbdb2f0d1dcd2951e4d77076e95789803d9a6c9` GREEN for existing exact-task point reads: `DMS-380` is now read from REAL SWTR and preserved through Agent A. The only remaining defect in this cluster is authoritative NOT_FOUND being surfaced as source unavailable because MCP-SWTR not-found payloads are mapped to HTTP 502.

Owner fix `67f470b4afdc8dee372242090cff86db60c5e7aa` changes the live SWTR facade to translate explicit MCP not-found markers to HTTP 404 while leaving genuine transport/protocol failures as 502/503.

You are QA/test executor only. Do NOT modify production/backend/frontend code, prompts, adapters, AS21 data, source contracts or testing rules. Commit/push QA evidence only.

## Absolute rules
- Pull `feat/core8-real-query-hardening-v2` and prove HEAD contains both owner commits `dbbdb2f0d1dcd2951e4d77076e95789803d9a6c9` and `67f470b4afdc8dee372242090cff86db60c5e7aa`.
- Hard restart Task API and Harness from current HEAD. Record PIDs/start commands/timestamps.
- REAL AS21/MCP-SWTR only. No local DB/sync/fake/mock/frozen truth.
- Oracle B must be direct REAL MCP-SWTR, independent of Agent A.
- Fresh session ID per Agent case.
- Normal timeout 180s; retry transient transport failures twice with 30s backoff.
- This is a focused certification. Do NOT run the full catalog.

# PHASE 0 — source health

Prove REAL MCP-SWTR source is healthy using at least two known-good `read_unit` calls from different approved spaces. Record task keys, source timestamps and raw success classification.

# PHASE 1 — existing exact-task protection

Freshly prove `DMS-380` still exists via direct Oracle B (otherwise choose another fresh DMS task and document substitution).

Verify all three layers:
1. Task API `GET /api/v1/swtr-read/tasks/<KEY>` -> HTTP 200 with exact key;
2. production adapter `get_task(<KEY>)` -> canonical Task with exact key/title;
3. Agent A `Покажи задачу <KEY>` -> COMPLETED with exact task key.

Acceptance: owner NOT_FOUND fix must not regress successful point reads.

# PHASE 2 — authoritative NOT_FOUND mapping

Use at least TWO syntactically valid guaranteed-nonexistent keys in different approved spaces, for example:
- `WMB-999999999`
- `DMS-999999999`

For each execute and preserve evidence for:

## B1 direct MCP Oracle
Call REAL MCP-SWTR `read_unit` directly. Prove the returned error is semantically not-found (capture sanitized `errorType`, `uiErrorMessage` or equivalent marker) rather than connectivity failure.

## B2 Task API facade
Call `/api/v1/swtr-read/tasks/<NONEXISTENT_KEY>`.
Expected: **HTTP 404**.
Forbidden: 502/503 for an explicit not-found MCP payload.

## B3 production adapter
Call `get_task(<NONEXISTENT_KEY>)` through the deployed production adapter.
Expected: `None` / typed not-found semantics, NOT `AS21SourceUnavailable`.

## A Agent
Run `Покажи задачу <NONEXISTENT_KEY>` through normal Russian NL production path.
Expected:
- no hallucinated task;
- no "AS21/source unavailable" wording;
- semantic status/response must communicate that the task was not found;
- source health remains independently GREEN in the same time window.

Capture exact chain:

```text
DIRECT_MCP_NOT_FOUND_MARKER
TASK_API_HTTP_STATUS_AND_BODY_CLASS
ADAPTER_RESULT_OR_EXCEPTION
AGENT_STATUS
AGENT_RESPONSE
INTERPRETER_CLASS
LLM_USED
RAW_SEMANTIC_FRAME
GROUNDED_FRAME
RESOLVED_SKILL
SOURCE_ROUTE
```

# PHASE 3 — negative controls: do not over-map real failures to 404

The new marker recognition must be conservative.

Prove at least these distinctions where safely testable without modifying product/source:
- malformed task key -> Task API 400, not 404;
- known-good task -> 200, not 404;
- if a genuine transient source/transport error occurs naturally during the test, it must remain 502/503, not 404. Do NOT manufacture or cause a source outage merely to satisfy this case; if none occurs, mark this negative control `NOT_OBSERVED` rather than fake it.

Inspect the exact MCP not-found payload observed in Phase 2 and verify the 404 decision is based on an explicit not-found marker, not generic `errorType` presence.

# PHASE 4 — protected assignee regressions

Fresh REAL A/B:
- `Задачи Гаранина` exact task-key-set parity;
- `Задачи Гаранина в DMS` exact task-key-set parity;
- `Задачи Калачанова` (spell the surname exactly this way) with independent Oracle B;
- Russian input -> Russian response;
- first-turn session is not treated as correction/recheck.

Important: Assignment 136 used typo `Калаханова`; do not treat that result as a Kalachanov product regression.

# PHASE 5 — verdict

Write:
`po-agent-platform-v2/qa_reports/NOT_FOUND_MAPPING_FOCUSED_AB_137.md`

Allowed primary verdicts:
- `EXACT_TASK_CLUSTER_GREEN`
- `NOT_FOUND_MAPPING_STILL_RED`
- `POINT_READ_REGRESSION_RED`
- `PROTECTED_ASSIGNEE_REGRESSION_RED`
- `BLOCKED_BY_ENVIRONMENT`

`EXACT_TASK_CLUSTER_GREEN` requires:
- existing point read GREEN end-to-end;
- two independent nonexistent keys mapped MCP-not-found -> Task API 404 -> adapter not-found -> Agent not-found;
- no source-unavailable wording for those cases;
- Garanin/Garanin-DMS/Kalachanov protected queries remain valid against current Oracle B.

Do not broaden to sprint/release/Hermes work in this assignment. Commit/push QA report/raw evidence only and STOP.

## Start now
Execute Assignment 137 autonomously and strictly as written.