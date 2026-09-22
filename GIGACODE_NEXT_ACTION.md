# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_206_HISTORY_STATUS_SOURCE_DIAGNOSTIC`

## Role lock
GigaCode is **QA/source-diagnostic tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT start Wave S.
Do NOT add skills.
Do NOT convert SOURCE_UNAVAILABLE into empty history.

## Context
A205 is GREEN and frozen at:
`checkpoint/v4-a205-green@1fd519105ba6612f535ad98a55cb1302f387ca43`

Current catalog status:
- ordinary task status filtering/search is GREEN;
- `task.history` and `task.time_in_status` remain SOURCE_CONDITIONAL;
- current V4 path is:
  `task.history/time_in_status -> TaskIntelligenceCapabilities -> adapter.get_task_history() -> GET /api/v1/swtr-read/tasks/{task}/history -> MCP get_unit_change_history`;
- the Task API history route builds arguments dynamically from the live MCP tool schema via `_schema_aware_task_history_arguments`;
- observed live behavior for DMS-380/DMS-399 is HTTP 502 / typed SOURCE_UNAVAILABLE.

The goal of A206 is to determine whether this is:
A. wrong tool name;
B. wrong argument schema / identifier alias;
C. MCP wrapper/tool implementation defect;
D. AS21 upstream failure/permission issue;
E. payload parsing/field-code mismatch;
F. a genuinely unavailable source feature.

Wave S remains paused until this is classified.

## Phase 0 — pull / baseline
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record exact START_HEAD; tracked worktree clean.
3. Confirm A205 checkpoint still exists and no new production changes after A205 except docs/spec for A206.
4. Keep UI/Agent/Task API/MCP running.

## Phase 1 — live MCP tool inventory
Query the **actual live MCP-SWTR tool descriptors**, not repository assumptions.

Capture:
- full tool list;
- whether `get_unit_change_history` exists;
- exact inputSchema for it;
- exact required fields;
- whether schema is flat, nested `request`, or string;
- any alternative history/changelog/audit tools exposed by MCP, including names containing:
  `history`, `change`, `audit`, `changelog`, `timeline`, `transition`, `event`.

Do not infer. Persist raw descriptor evidence in the QA report.

## Phase 2 — argument-builder verification
For DMS-380 and DMS-399:
1. Call/inspect `_schema_aware_task_history_arguments` against the live descriptor.
2. Record the exact arguments produced.
3. Compare them field-for-field with the live MCP schema.
4. If the schema exposes multiple aliases, test only schema-declared variants in a bounded way.

Classify:
- builder correct;
- builder incomplete;
- builder sends wrong identifier field;
- builder uses wrong nesting;
- tool descriptor itself is inconsistent.

No production edits.

## Phase 3 — direct MCP history probes
Call the history tool directly through the same MCP transport used by Task API.

Use:
- DMS-380
- DMS-399
- one additional known real task whose exact task lookup is GREEN.

For each:
- exact tool name;
- exact arguments;
- transport mode;
- raw success/error class;
- normalized MCP `isError` if present;
- text payload/errorType/uiErrorMessage/exceptionUUID if present;
- latency.

Do not expose secrets/tokens in report.

If direct MCP fails, prove whether failure is:
- transport;
- validation/schema;
- authorization;
- upstream AS21 exception;
- not-found;
- unsupported tool implementation.

## Phase 4 — Task API route comparison
Call:
- `GET /api/v1/swtr-read/tasks/DMS-380/history`
- `GET /api/v1/swtr-read/tasks/DMS-399/history`

Compare with Phase 3.

Require:
- Task API preserves the true MCP failure class;
- no local fallback;
- 404 only for proven not-found;
- 502/503 only for actual protocol/upstream/transport failure.

If direct MCP succeeds but Task API fails => Task API integration defect.
If both fail identically => source/MCP-side defect unless argument builder is wrong.

## Phase 5 — raw payload / workflow field semantics
If any history call succeeds, inspect the raw payload before canonical conversion.

Determine:
- event container key(s): `content`, `events`, list, other;
- actual status field code(s);
- whether status changes use `workflow_status` exactly or another code;
- old/new value shape: string/id/object;
- timestamp field shape/timezone;
- actor field shape;
- ordering guarantee.

Then compare current Task API parser:
- `fieldCode/field_code`;
- `oldValue/old_value`;
- `newValue/new_value`;
- `changedAt/changed_at`;
- `actor`.

Any mismatch that would silently drop real history => RED_IMPLEMENTATION_DEFECT.

## Phase 6 — task.history end-to-end
Run at least 5x each:
- `покажи историю статусов задачи DMS-380`
- `покажи историю статусов задачи DMS-399`

If source works:
- `task.history` must execute;
- timeline length and transition order exact vs raw Oracle;
- evidence count matches status-transition events;
- no invented events.

If source remains unavailable:
- typed SOURCE_UNAVAILABLE/SOURCE_CONDITIONAL;
- no empty-history success;
- no fabricated timeline.

## Phase 7 — task.time_in_status end-to-end
Run at least 5x:
- `сколько времени DMS-399 провела в каждом статусе?`

If history works, independently compute Oracle durations from raw timestamps.

Verify:
- transitions sorted by authoritative timestamp;
- each interval ends at next transition;
- final open interval ends at current time only when task is still open;
- for terminal tasks, do NOT incorrectly extend the terminal status to current time if the source exposes terminal completion timestamp;
- timezone handling is consistent/offset-aware;
- no negative durations;
- repeated visits to same status are either kept as intervals or aggregated explicitly/consistently.

If current implementation cannot prove correct terminal interval semantics, classify RED even if history route works.

## Phase 8 — ordinary status regression
Prove status search itself is not affected:
- active/not_completed person query;
- completed/closed query;
- one exact encoded-status source case;
- current sprint status query.

Require fresh source parity and no regression from A205.

## Phase 9 — capability honesty
Query:
- `Ты умеешь показывать историю задачи?`
- `Ты умеешь определять время задачи в статусах?`

Expected wording must distinguish:
- skill/capability is defined;
- live authoritative history source availability may be unavailable.

If source is down, agent must not claim unconditional live availability.

## Phase 10 — alternative live read surface
Only if `get_unit_change_history` is broken/unavailable, inspect the live MCP inventory for an **authoritative read-only alternative**.

An alternative is acceptable only if it:
- is live REAL AS21;
- returns authoritative change/status timestamps;
- is bounded by task identity;
- requires no local cache/sync;
- does not infer history from updated_at/current status.

Document candidate route/tool and exact schema.
Do NOT implement it in A206.

## Phase 11 — decision
Classify exactly one primary outcome:

### `FIXABLE_IN_OUR_CODE`
Use only when evidence proves builder/parser/Task API/adapter defect.
Report exact minimal owner fix boundary.

### `MCP_TOOL_DEFECT_OR_UPSTREAM_AS21`
Use when our invocation is schema-correct but live MCP/upstream fails.
Keep skills SOURCE_CONDITIONAL; no code fabrication.

### `SUPPORTED_VIA_ALTERNATIVE_LIVE_ROUTE`
Use when current tool is broken but another authoritative live bounded source route is proven.
Report proposed owner integration boundary.

### `HISTORY_SOURCE_GREEN`
Use when current route actually works and E2E history/time-in-status both pass exact Oracle.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_HISTORY_STATUS_SOURCE_GREEN`
- `AGENT_CORE_V4_HISTORY_STATUS_SOURCE_FIXABLE_RED`
- `AGENT_CORE_V4_HISTORY_STATUS_SOURCE_EXTERNAL_BLOCKED`

Do not call overall GREEN merely because fail-closed works. GREEN means the source-backed history/time-in-status feature is actually usable and correct.

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_HISTORY_STATUS_SOURCE_DIAGNOSTIC_206.md`

Report must include:
- live MCP tool inventory evidence;
- history tool schema;
- generated arguments;
- direct MCP result;
- Task API result;
- parser field mapping;
- E2E history/time-in-status results;
- ordinary status regression;
- classification and minimal next step.

Leave UI/backend/Task API/MCP running.
Return verdict, START_HEAD, report commit, source classification, URLs/PIDs/health.
Then stop.
