# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_136_EXACT_TASK_LIVE_POINT_READ_AB`

## Mission
Owner fix `dbbdb2f0d1dcd2951e4d77076e95789803d9a6c9` changes production exact-task lookup to use the REAL SWTR point-read route `/api/v1/swtr-read/tasks/{code}` instead of scanning the local `/api/v1/tasks` cache. Assignment 135 proved the previous exact-task path could return `COMPLETED+0` for a task that REAL MCP `read_unit` could read.

You are QA/test executor only. Do not modify production/backend/frontend code, prompts, skills, adapters, source data or test rules. Commit/push QA evidence only.

## Absolute rules

- Pull branch `feat/core8-real-query-hardening-v2` and prove HEAD contains owner commit `dbbdb2f0d1dcd2951e4d77076e95789803d9a6c9`.
- Hard restart Task API and Harness from that HEAD.
- REAL AS21/MCP-SWTR only. No local DB/sync/fake/mock/frozen truth.
- Oracle B must call independent REAL MCP-SWTR `read_unit` directly, not Harness and not the production adapter.
- Use fresh unique session IDs.
- Normal timeout 180s; retry transient transport timeout twice with 30s backoff.
- Do not broaden this into a 54-skill marathon.

## Phase 0 — source health

Prove MCP-SWTR healthy with two direct reads from approved spaces. Record raw tool names/routes, normalized keys and timestamps.

## Phase 1 — known real exact task

Use `DMS-380` only if direct Oracle B `read_unit` proves it currently exists. If it does not, select a fresh real task from DMS using Oracle B and record why the replacement was chosen.

For the same real task execute Agent A through normal production natural-language routing:

1. `Покажи задачу <KEY>`
2. `Сводка по <KEY>`
3. `Покажи статус задачи <KEY>` if supported by normal production semantics

For every case capture:

```text
USER_QUERY
INTERPRETER_CLASS
LLM_USED
RAW_SEMANTIC_FRAME
GROUNDED_FRAME
RESOLVED_SKILL
CAPABILITY_ARGS
SOURCE_ROUTE
FINAL_STATUS
TASK_KEYS / EXACT_KEY
ANSWER
```

Acceptance: Agent A must preserve the exact Oracle B key and must not return `COMPLETED+0`/empty evidence for an existing task.

## Phase 2 — direct adapter proof

Instantiate/use the production adapter path as deployed and call `get_task(<KEY>)`. Prove:

- source route is `/api/v1/swtr-read/tasks/<KEY>`;
- returned canonical `Task.key == <KEY>`;
- title is non-empty and corresponds to Oracle B summary/title;
- no `/api/v1/tasks` local scan is used for this exact lookup.

If the live MCP unit shape differs from the owner normalization assumptions, capture the complete sanitized shape and classify the exact first failing boundary. Do not patch it.

## Phase 3 — NOT_FOUND semantics

While source health remains proven, choose a guaranteed nonexistent syntactically valid key in an approved space, e.g. `WMB-999999999`, and run:

- direct Oracle B `read_unit`;
- production adapter `get_task`;
- Agent A `Покажи задачу WMB-999999999`.

The agent must distinguish authoritative NOT_FOUND from source unavailable. If the Task API live facade converts MCP not-found into 502/503, localize that boundary precisely and mark `NOT_FOUND_MAPPING_STILL_RED`; do not call the exact-task fix fully green.

## Phase 4 — protected regressions

Fresh REAL A/B only:

- `Задачи Гаранина` — exact key-set parity;
- `Задачи Гаранина в DMS` — exact key-set parity;
- one Kalachanov assignee query with current Oracle B;
- one second approved-space task query;
- Russian response remains Russian;
- no unexpected correction/session state on first turn.

These must remain unchanged by the exact-task fix.

## Final report

Write `po-agent-platform-v2/qa_reports/EXACT_TASK_LIVE_POINT_READ_AB_136.md`.

Mandatory verdicts:

- `EXACT_TASK_POINT_READ_GREEN_NOT_FOUND_GREEN`
- `EXACT_TASK_POINT_READ_GREEN_NOT_FOUND_MAPPING_RED`
- `EXACT_TASK_POINT_READ_RED`
- `PROTECTED_REGRESSION_RED`
- `BLOCKED_BY_ENVIRONMENT`

Report exact A/B key parity, exact source routes, NOT_FOUND behavior, protected regressions, full HEAD SHA and first failing boundary for any RED.

Commit/push QA artifacts only and STOP. Do not modify production code.

## Start now
Execute Assignment 136 autonomously.