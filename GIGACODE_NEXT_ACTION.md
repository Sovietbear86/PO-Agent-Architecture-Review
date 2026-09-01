# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_121_RAW_MCP_RESPONSE_CONTRACT_FORENSIC`

## Why Assignment 120 is not accepted as source-data proof
Assignment 120 concluded that `DMS-SPRNT-1` dropped from 100 tasks to 1 task. That conclusion is NOT trusted yet.

The report itself states that `get_sprint_tasks` returned Python type `list` and then treated `len(result) == 1` as one business task. MCP/FastMCP commonly returns an outer content-envelope list whose single element contains serialized JSON/text for many business rows. Therefore `1 outer content item` MUST NOT be interpreted as `1 task` until the inner payload is decoded and counted.

Until the raw MCP response contract is proven, do not claim:
- AS21 data changed;
- sprint contains 1 task;
- assignee data disappeared;
- MCP tool is broken;
- Oracle recipe is broken.

## Role boundary
You are QA / forensic executor only.
Do NOT modify production/backend/frontend code, prompts, skills, adapters, Task API, MCP-SWTR, team data, AS21 data, testing rules, or this file.
Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`.

## Absolute prohibitions
- NO task synchronization/population utilities.
- NO local DB refresh/population.
- NO local DB/cache as truth or Oracle.
- NO fake/mock/frozen data.
- NO AS21 writes.
- NO Harness/Agent as Oracle.
- NO functional 54-skill marathon in this assignment.
- NO conclusions from `len(call_tool_result)` before decoding the actual MCP payload.
- NO claims about task counts without decoded business rows.

## Goal
Prove the exact live MCP-SWTR response envelope and payload contract for the read tools currently used in QA, then determine whether Assignment 120 miscounted an MCP content envelope as one task.

This assignment is intentionally technical and narrow. Do not test product business logic until the MCP response contract is understood.

## Phase 0 — exact provenance and source health
1. Pull current `feat/core8-real-query-hardening-v2`; record exact HEAD and clean worktree.
2. Record MCP-SWTR launch command/wrapper, transport, tool count and relevant client library/version if observable.
3. Record Harness/Task API PIDs only for provenance; do not use them for Oracle.
4. Verify REAL AS21 connectivity with one known point read.
5. Retry temporary 5xx/timeout up to 2 times with 20–30 sec backoff; timeout >=120 sec.

## Phase 1 — inspect raw `get_sprint_tasks` result for DMS-SPRNT-1
Call the live MCP tool directly through the same MCP client path used by GigaCode QA:
`get_sprint_tasks` for exact sprint `DMS-SPRNT-1`.

Before any parsing or counting, capture:
- exact Python type of the call result;
- `len(result)` only as OUTER envelope length;
- for every outer item: exact Python type;
- `repr()` or safe truncated repr of each outer item;
- available attributes/fields such as `type`, `text`, `content`, `data`, `structuredContent`, `meta` where present;
- whether the outer item is a FastMCP/MCP `TextContent`, content block, dict, Pydantic object, tuple, or other envelope.

Secrets/tokens must not be printed.

## Phase 2 — decode the inner business payload
For the `DMS-SPRNT-1` result:
1. Extract the actual inner payload from the MCP envelope without modifying source data.
2. If payload is string/text, show the first and last safe fragments and parse JSON only if it is valid JSON.
3. If FastMCP prepends headers/prefix lines, document them and identify where the actual JSON begins.
4. Record decoded business object type: dict/list/etc.
5. Locate the task collection field(s) or actual task rows.
6. Count BUSINESS TASK ROWS only after decoding.
7. Record pagination fields (`totalElements`, `pageNumber`, `pageSize`, `hasNext`, cursor, etc.) if present.
8. Follow every page/cursor required to prove completeness if the tool itself paginates.
9. Record at least 5 representative task keys/codes from decoded rows when available.
10. Record whether decoded rows include raw attributes/`assigned_to` and where exactly those fields live.

Explicitly distinguish:
- outer envelope count;
- content-block count;
- decoded page count;
- decoded business task count.

## Phase 3 — repeat contract proof on two controls
Repeat the same raw-envelope + decoded-payload inspection for:
1. `get_sprint_tasks` on `DMS-SPRNT-2`;
2. one known REAL point-read tool for a known DMS task, preferably `DMS-78` or another existing DMS task if the exact current point-read contract requires a different identifier.

For point read, capture the same layers:
`call_tool result -> outer MCP envelope -> inner payload -> decoded business object`.

If the exact point-read tool/parameter names differ, inspect live tool schema first; do not guess.

## Phase 4 — compare with Assignment 109/120 parsing behavior
Mandatory forensic comparison:
- explain how Assignment 109 obtained 100 business tasks;
- explain exactly how Assignment 120 obtained `1`;
- determine whether 120 counted an outer MCP envelope instead of decoded rows;
- identify any different MCP client helper, `.content`, `.text`, JSON extraction, or wrapper parsing used between the two assignments if evidence exists in reports/scripts/logs;
- do NOT attribute divergence to AS21 data change unless decoded current source rows prove it.

## Phase 5 — raw assignee evidence if present
If the decoded sprint rows expose assignee information:
- capture representative raw rows showing the exact location/value of `assigned_to` or authoritative equivalent;
- check whether historical Garanin keys from Assignment 109 (`DMS-243`, `DMS-248`, `DMS-78`, `DMS-79`, `DMS-80`, `DMS-81`, `DMS-82`, `DMS-83`, `DMS-86`, `DMS-93`) appear in the decoded current sprint payload;
- do not infer current ownership from history; inspect current raw values only.

If decoded rows genuinely omit assignee, state that narrowly. Do not claim AS21 itself lacks assignee unless a lower-level authoritative read proves it.

## Phase 6 — verdict
Allowed verdicts only:
- `MCP_ENVELOPE_MISPARSE_PROVEN` — Assignment 120 counted wrapper/content envelope instead of business rows.
- `MCP_PAYLOAD_CONTRACT_DRIFT_PROVEN` — live MCP payload shape materially changed and prior parser is incompatible.
- `CURRENT_AS21_DATA_CHANGE_PROVEN` — decoded complete current REAL AS21 payload truly proves the sprint/business data changed.
- `BLOCKED_BY_ENVIRONMENT` — source/tool unavailable after retries.

Do not emit GREEN product certification from this assignment.

## Mandatory evidence table
Include a table with at least:

| Tool/case | Outer Python type | Outer len | Content item type | Inner payload type | Business task rows | Pagination | Assignee field location |
|---|---|---:|---|---|---:|---|---|
| DMS-SPRNT-1 | ... | ... | ... | ... | ... | ... | ... |
| DMS-SPRNT-2 | ... | ... | ... | ... | ... | ... | ... |
| DMS point read | ... | ... | ... | ... | n/a | n/a | ... |

## Output
Primary report:
`po-agent-platform-v2/qa_reports/RAW_MCP_RESPONSE_CONTRACT_FORENSIC_121.md`

Optional raw evidence prefix:
`RAW_MCP_RESPONSE_CONTRACT_FORENSIC_121_`

## Finish
Commit/push only QA artifacts, provide full SHA, then STOP.

## Start now
Execute Assignment 121 autonomously. Do not ask for confirmation. Do not modify production code. Do not synchronize or populate task data.