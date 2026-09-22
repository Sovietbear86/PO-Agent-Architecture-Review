# A206 — Agent Core V4 History / Status Live-Source Diagnostic

**Verdict:** `AGENT_CORE_V4_HISTORY_STATUS_SOURCE_FIXABLE_RED`
**Primary classification:** `FIXABLE_IN_OUR_CODE` (tool-name + parser, both proven in task-api; a working authoritative live route `get_task_history` exists on the same MCP server — satisfies `SUPPORTED_VIA_ALTERNATIVE_LIVE_ROUTE` criteria and is the proposed integration boundary).
**Secondary finding:** P8 RED — planner drops the `not_completed` status constraint for person+status queries in 2/3 identical runs (false «открытых» labeling), completion gate accepts uncovered constraint.

| Field | Value |
|---|---|
| Branch | `feat/core8-real-query-hardening-v2` |
| START_HEAD | `7d505dc2e3204ae66942af83117f80b3fe62447a` |
| Delta vs A205 (`1fd5191`) | docs/spec only (`GIGACODE_NEXT_ACTION.md`, `V4_54_SKILL_MIGRATION_PLAN.md`, `V4_DOD_LOCK.md`); production diff `1fd5191..7d505dc` over `po-agent-platform-v2/src task-api/app mcp-swtr` = ∅ |
| A205 checkpoint | `refs/heads/checkpoint/v4-a205-green` → `1fd5191` (verified on remote) |
| Agent | 8212 (PID 84446) /live 200 |
| Task API | 8241 (PID 30041, system python3) /health 200 |
| MCP-SWTR | 3000 (PID 29268, own .venv) |
| UI | 5175 (`[::1]`, PID 55236) 200 |

---

## Phase 1 — live MCP tool inventory (raw evidence in `qa_206_mcp_inventory.json`)

Live `tools/list` over SSE (`http://127.0.0.1:3000/sse`, fastmcp 3.4.2, same client class as production): **48 tools**, inventory latency 0.58s.

- **`get_unit_change_history`: NOT PRESENT.** No tool with that name exists on the live server.
- **`get_task_history`: PRESENT.** Description: *«Get task history (status and assignee transitions)»*. Exact inputSchema (verbatim):
  ```json
  {
    "additionalProperties": false,
    "properties": {
      "task_code": {"description": "Task code like DMS-271", "type": "string"}
    },
    "required": ["task_code"],
    "type": "object"
  }
  ```
  Flat schema, single required string field. No `request` nesting, no aliases.
- Other history-ish names (`history|change|audit|changelog|timeline|transition|event`): **only `get_task_history`** matches. No alternative/second history surface.
- Full 48-tool list captured raw (read_unit, get_unit_types_by_space, find_units, find_units_by_filter, get_tql_properties, create_*, get_unit_comments, search_link_types, get_unit_links, get_unit_attributes, search_users, search_versions, search_sprints, get_current_sprint, get_sprint_tasks, get_current_sprint_tasks, search_wiki_pages, read_wiki_page, create_wiki_page, search_test_cases, …, get_work_report, get_work_sum, get_unit_files, download_unit_file, get_my_tasks, get_task, search_tasks, get_task_history).

## Phase 2 — argument-builder verification

Production builder `_schema_aware_task_history_arguments` (`task-api/app/routers/swtr_read.py:405`):

- It is genuinely schema-aware (flat / nested `request` object / `request` string forms; alias priority `unit_code, unitCode, task_code, taskCode, code, id`).
- **But it is called with tool name `get_unit_change_history`, which does not exist on the live server**, so `tool_input_schema()` raises before any argument is built:
  ```
  app.services.swtr_mcp_client.SWTRMCPProtocolError: MCP-SWTR tool 'get_unit_change_history' is not available
  ```
  (reproduced deterministically for DMS-380, DMS-399, WMB-30000).
- Classification: **builder logic correct; the route passes a wrong (non-existent) tool name.** With the correct name `get_task_history`, the existing alias tuple already contains `task_code`, so the schema-aware builder would produce `{"task_code": "DMS-380"}` with no further logic changes.

## Phase 3 — direct MCP history probes (SSE, same transport as Task API)

| Task | `get_task_history` (real) | `get_unit_change_history` (route's name) |
|---|---|---|
| DMS-380 | **OK**, is_error=False, 0.20s | `SWTRMCPProtocolError` (prod normalization); raw server: `ToolError: Unknown tool: 'get_unit_change_history'` |
| DMS-399 | **OK**, is_error=False, 0.14s | same |
| WMB-30000 | **OK**, is_error=False, 0.14s | same |

Failure class of the route's tool name is **protocol-level unknown tool** (server-side), not transport, not authorization, not upstream AS21: the call reaches the server and the server answers «Unknown tool». Raw payloads persisted to `/tmp/qa206_raw_get_task_history_{task}.json` (no secrets; token scrubbed).

## Phase 4 — Task API route comparison

- `GET /api/v1/swtr-read/tasks/DMS-380/history` → **502** `{"detail":"MCP-SWTR tool 'get_unit_change_history' is not available"}` (0.08s)
- `GET /api/v1/swtr-read/tasks/DMS-399/history` → **502** identical (0.05s)

Requirements met: true MCP failure class preserved (502 = protocol/tool mismatch), **no local fallback**, no 404 for this case, no fake events. Both sides agree the only difference is the tool name — direct MCP to the *real* tool succeeds.

## Phase 5 — raw payload / workflow field semantics (source WORKS)

Top level: `{"content": [...], "hasNext": false, "pageNumber": 1, "pageSize": 100, "totalElements": N}` (paginated; all 3 probe tasks single-page complete).

Event shape (real fields):

| Semantic | Real field | Example (DMS-380) |
|---|---|---|
| status/field identity | `entity.code` | `workflow_status`, `assigned_to` |
| timestamp | `createdAt` (ISO-8601 UTC, microseconds) | `2026-09-17T10:51:55.272677Z` |
| actor | `user.externalId` (+ firstName/lastName) | `Semavin.M.M` |
| old value | `oldValue` — object: status `{code,name,style,statusType}` or user `{externalId,login,…}` or null | `{name:"Тестирование",statusType:"progress"}` |
| new value | `newValue` — same shapes | `{name:"Закрыт",statusType:"done"}` |
| event kind | `type` / `action` | `ATTRIBUTE` / `UPDATE` (also `CREATE`) |
| meta | `meta.masked` | `false` |

**Proven real timelines:**
- DMS-380 (6 events, terminal): Зарегистрирован(pause) → Открыт(pause) 09-06T19:38:34.054 → На исправлении(progress) 19:38:39.897 → Тестирование(progress) 19:41:12.646 → **Закрыт(done) 09-17T10:51:55.273** (+ assignee CREATE/Garanin→Semavin events).
- DMS-399 (2 events, open): Зарегистрирован → Открыт 09-10T20:19:07.208 → **На исправлении(progress) 09-10T20:19:16.516** (current, open).
- WMB-30000 (4 events, terminal): Открыт → Escalated 07-10T09:00:47.373 → В работе 07-20T12:15:48.860 → **Escalated again** 12:20:09.671 (revisit) → Закрыт 07-28T08:58:09.991.

**Parser field mapping — RED_IMPLEMENTATION_DEFECT (latent, proven by simulation).** Current production parser (`swtr_read.py:852-873`) reads `fieldCode|field_code`, `changedAt|changed_at`, `actor` and coerces values with `str()`. Applied to the real payload (deterministic simulation):

- `field_code` → `""` for **all** events (real field is `entity.code`) — status transitions become indistinguishable;
- `changed_at` → `datetime.now()` for **all** events (real field is `createdAt`) — **all source timestamps destroyed**; time_in_status would be garbage;
- `actor` → `None` (real field is `user` object);
- `oldValue`/`newValue` keys match, but values are objects coerced to `str(dict)` blobs instead of structured `name`/`statusType`/`externalId`;
- event container `content` ✓ matches.

=> Even with the tool name fixed, the parser would silently emit an empty-fielded, now-timestamped, actor-less history — a silent data corruption, not a usable feature.

## Phase 6 — task.history end-to-end (5× each)

10/10 runs `FAILED` (6.3–14.2s) with the exact typed message `Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат.`, `loaded_skills=['task.history']`, **0 evidence, no empty-history success, no fabricated timeline** — correct fail-closed behavior on the broken route.

## Phase 7 — task.time_in_status end-to-end (5×)

5/5 runs `FAILED` typed source-unavailable (7.5–17.0s), 0 evidence — correct fail-closed. Independent Oracle durations from raw timestamps (for the post-fix gate):

- DMS-399 (open): Открыт 9.31s (20:19:07.208→20:19:16.516); На исправлении open interval 20:19:16.516→now (open-task extension correct only while task is open).
- DMS-380 (terminal): Открыт 5.84s; На исправлении 152.75s; Тестирование 10d 15h 10m 42.6s; Закрыт from 09-17T10:51:55.273 — **must not extend to current time** (terminal completion timestamp present in source).
- WMB-30000 (terminal, status revisit): Escalated #1 10d 3h 15m 1.5s; В работе 4m 20.8s; Escalated #2 7d 20h 38m 0.3s; Закрыт from 07-28T08:58:09.991. Revisits must be kept as separate intervals (or explicitly aggregated).

## Phase 8 — ordinary status regression

| Case | Result |
|---|---|
| P8c «Открытые задачи в DMS» (open, space) | **88/88 exact** vs fresh oracle (24.7s) |
| P8d «список задач в текущем спринте DMS и их статусы» | **65/65 exact** (DMS-SPRNT-3, 46.9s) |
| P8b «Закрытые задачи в DMS» (encoded/terminal status) | **142/142 exact** = full terminal set (statusType ∈ done/closed/cancelled); documented semantics: «закрытые» → terminal (answer: «статус «completed»»). Self-consistent, no fabricated keys |
| P8a «Открытые задачи Родиона Гаранина в DMS» (active person) | **RED — non-deterministic constraint drop (2/3 identical runs)** |

**P8a detail (localization):**
- Run 1/3 (batch) + Run A (re-probe): planner → `task.search(assignee=Garanin.R.V, space=DMS, status=not_completed)` → **8/8 exact** active set. Correct.
- Runs 2/3 (batch) + B (re-probe): planner → `task.search_assignee(reference="Родион Гаранин", space="DMS")` — **no status argument (capability cannot express it)** → returns all 11 tasks **including 3 terminal (DMS-248, DMS-262, DMS-36)** and the answer falsely labels them **«11 открытых задач»**.
- «Активные задачи…» variant: same drop (11 tasks, label softened to «11 задач»).
- First failing boundary: planner skill selection for person+status queries; the completion frontier accepts `task.search_assignee` whose satisfied contract does not cover the query-derived `not_completed` constraint (A199-F3/A200 «completion-gate hole» class, now demonstrated on the person+status shape). No regression for the shapes certified in A205 (space-open, sprint, terminal-set all exact).

## Phase 9 — capability honesty (2/2)

- «Ты умеешь показывать историю задачи?» → «Да, у меня есть capability «task.history»… **Однако это зависит от того, exposes ли авторитетный источник … историю** для конкретной задачи» — capability defined + availability-conditional. Honest, no unconditional live claim. ✓
- «Ты умеешь определять время задачи в статусах?» → same pattern («зависит от фактической доступности» источника). ✓
- Cosmetic: both answered as `NEEDS_CLARIFICATION` without options (text in `question` field) — known A205-A7c shape variance, not a safety issue.

## Phase 10 — alternative live read surface

`get_task_history` (same MCP server, same transport) meets **all** acceptance criteria:
- live REAL AS21 ✓ (direct source, 0.14–0.2s);
- authoritative change/status timestamps ✓ (`createdAt` per transition + statusType transitions, incl. assignee changes);
- bounded by task identity ✓ (`task_code` only, `additionalProperties: false`);
- no local cache/sync ✓ (stateless MCP call);
- does not infer from updated_at/current status ✓ (explicit transition events).

Proposed owner integration boundary (NOT implemented in A206): route + builder switch to `get_task_history`/`task_code`; parser remap per Phase 5; optional `hasNext`/`totalElements` pagination loop for >100-event tasks (pageSize=100; all probes single-page complete).

## Phase 11 — decision

**Primary: `FIXABLE_IN_OUR_CODE`.** Evidence proves two our-side defects on the history chain:
1. **Tool name** — `task-api/app/routers/swtr_read.py` history route + builder request `get_unit_change_history`, which does not exist on the live MCP server (server: «Unknown tool»); the live server exposes `get_task_history` with flat `{"task_code": string}`. Minimal fix: rename tool at the route/builder call (the existing schema-aware alias logic already handles `task_code`).
2. **Parser field mapping** — remap to real payload: `field_code ← entity.code`, `changed_at ← createdAt` (offset-aware), `actor ← user.externalId`, structured `oldValue/newValue` (status: `name`+`statusType`; user: `externalId`), keep `content` container; add pagination if `hasNext`.

Without both fixes the feature cannot be GREEN (parser would silently corrupt real history).

**Secondary (independent) RED — P8a planner constraint drop:** query-derived status constraint must be covered by the finally executed capability's arguments (reject READY / fail closed otherwise) — minimal fix at the completion-constraint coverage seam (same mechanism class as A199 resolved-constraint coverage); no person/space hardcoding.

## Verdict

`AGENT_CORE_V4_HISTORY_STATUS_SOURCE_FIXABLE_RED` — the history/time-in-status source is real and authoritative (`get_task_history` proven 3/3), current V4 behavior is safely fail-closed (15/15 typed, 0 evidence, no fabrication), ordinary status search has no A205 regression except the P8a person+status planner constraint drop; blocking defects are in our code (task-api tool name + parser; completion constraint coverage) with exact minimal fix boundaries above. Keep `task.history`/`task.time_in_status` SOURCE_CONDITIONAL until fixed and re-gated with the Phase 7 Oracle durations.

QA artifacts (untracked, repo root): `qa_206_p1p3_mcp.py`, `qa_206_p3p4.py`, `qa_206_oracle.py`, `qa_206_e2e.py`, `qa_206_mcp_inventory.json`, `qa_206_p3_results.json`, `qa_206_oracle.json`; raw payloads `/tmp/qa206_raw_get_task_history_{DMS-380,DMS-399,WMB-30000}.json`; logs `/tmp/qa206_*.log`; E2E runs `/tmp/qa206_e2e.jsonl`.
