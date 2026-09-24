# A215C — Time-Accounting Source Forensic (DMS-380, "Учет времени")

**Verdict:** `TIME_ACCOUNTING_SOURCE_READY_FOR_OWNER_IMPLEMENTATION`

**START_HEAD:** `e278b6cf0b5958363c258d1c2c9328af3b30b5e7` (docs-only over A215B `ae4a503`; prod diff `ae4a503..e278b6c` for src+task-api = 0 lines, so the running agent @ ae4a503 is production-equivalent)
**Role:** QA/source-forensic only. No code modified. A215B GREEN and Batch 3 pending state preserved.
**Date:** 2026-09-24

---

## Phase 1 — live MCP tool contract (48 tools enumerated)

Time-accounting capabilities exist in MCP-SWTR (read-only contract):

| tool | args | purpose |
|------|------|---------|
| `get_work_sum` | `{unit_code}` | **cumulative aggregate** per unit |
| `get_work_report` | `{unit_code, page, size=1000}` | **individual worklog entries** per unit, paginated (`content`, `hasNext`) |
| `get_work_log` | `{work_log_id}` | single entry by UUID |
| `get_work_types` | `{}` | work-type dictionary (code/name/description) |
| mutation (out of QA scope) | — | `create_work_log`, `create_work_log_range`, `update_work_log`, `delete_work_log` |

Time-value envelope everywhere: `{"temporalUnit": "MILLIS", "time": <int ms>, "duration": "<ISO-8601>"}`.

TQL (`get_tql_properties`, 627 filterable properties) exposes `estimate`, `residual_estimate`, `story_points`, `businesspoints`, `timetracking_originalestimate`, `timetracking_remainingestimate` — but **no worklog/time-spent property**: worklogs are only reachable per-unit through the `get_work_*` tools.

## Phase 2 — raw DMS-380 source proof: **case C — BOTH**

**`get_work_sum("DMS-380")`:**
```json
{"sum": {"temporalUnit": "MILLIS", "time": 172800000, "duration": "PT48H"}}
```
172,800,000 ms = **48 hours**.

**`get_work_report("DMS-380", page=0)`:** 6 entries, `hasNext=false` (complete):

| work_log_id (UUID) | date | user (externalId) | type | duration |
|---|---|---|---|---|
| `1b75d8eb-…` | 2026-09-07 | Garanin.R.V (Родион Гаранин) | 2Р_Кодирование (code 61) | PT8H (28,800,000 ms) |
| `c56ba94a-…` | 2026-09-06 | Garanin.R.V | 2Р_Кодирование | PT8H |
| `93d51f46-…` | 2026-09-05 | Garanin.R.V | 2Р_Кодирование | PT8H |
| `d39bb689-…` | 2026-09-04 | Garanin.R.V | 2Р_Кодирование | PT8H |
| `e3655c59-…` | 2026-09-02 | Semavin.M.M (Михаил Семавин) | 4Р_Тестирование компонента (code 44) | PT8H |
| `325ab6d1-…` | 2026-09-01 | Semavin.M.M | 4Р_Тестирование компонента | PT8H |

Entries sum to 6 × 8h = **48h = exactly `get_work_sum`** (internal consistency proven).

**Per-field contract:**
- source fields: `id` (UUID), `date` (date-only, `YYYY-MM-DD`, no time of day), `unit`, `user.{externalId,firstName,lastName,middleName}`, `comment`, `type.{code,name,description}`, `time` + `time_spent` (identical values),
- raw unit: milliseconds + ISO-8601 duration; normalized: hours = ms / 3600000,
- attribution: **per-user** (`user.externalId`, canonical login, matches the team-directory identity format),
- date window scoping: **yes** (entry `date` allows window filtering; sprint window = sprint start/end dates from `search_sprints`/`get_current_sprint`),
- deleted/edited worklogs: **cannot be distinguished** — no tombstone, no created/updated/audit fields in the entry payload,
- work-type dictionary: 5+ types observed (`1Р_Аналитика`, `2Р_Кодирование`, `3Р_Код Ревью`, `4Р_Тестирование компонента`, `5Р_…`).

## Phase 3 — UI parity for DMS-380: **EXACT proven**

UI "Затрачено 1н. 1д." (1 week + 1 day) vs raw 48h:
- source-proven quantum: every entry is exactly **PT8H** (28,800,000 ms) — 8h is a source fact, not an assumption;
- 48h ÷ 8h = **6 worklog-days**;
- 6 working days = 1 week (5 days) + 1 day = "1н. 1д." — the display decomposition matches the entry count **exactly**.

**Convention established (source-proven): 1 день = 8 ч, 1 неделя = 5 рабочих дней.** Parity is exact, not approximate. (No secret/token exposure in this report.)

## Phase 4 — production path inventory: first missing boundaries

1. **task-api (first boundary for worklogs):** no `swtr-read` route exposes the `get_work_*` MCP tools — worklog data is unreachable from the production source path. A new bounded endpoint is required, e.g. `GET /api/v1/swtr-read/tasks/{task_code}/work-logs` → `get_work_sum` + `get_work_report` (both unit-scoped, bounded, no tenant scan).
2. **adapter (first boundary for estimates):** `TaskApiAS21Adapter._map` (adapters/task_api.py) extracts status/assignee/timestamps/sprint/release from unit attributes but **never maps `estimate` / `residual_estimate` / `story_points` / `businesspoints`** → `Task.estimate_hours` is always None even when the source has a value (grep: 0 matches for estimate in the adapter).
3. task-api `GET /api/v1/swtr-read/tasks/{key}` **already passes through** all 38 raw unit attributes incl. `estimate` (null for DMS-380; the task-detail path needs no new route for estimates).
4. Sprint membership rows (`/sprints/{id}/tasks?complete=true`) carry only `workflow_status` + `assigned_to` attributes — no estimate; sprint-scoped planned metrics would need either per-task detail reads (bounded fan-out) or a sprint-route attribute extension.
5. `read_unit` (full unit detail) is the only place estimate + worklog-adjacent attributes are visible; worklogs are not in unit detail at all — they live exclusively in the `get_work_*` tools.

## Phase 5 — utilization feasibility matrix

| # | metric | classification | rationale |
|---|--------|----------------|-----------|
| 1 | task actual time ("сколько времени списано на DMS-380") | **SOURCE_READY** | `get_work_sum`/`get_work_report` are direct, unit-scoped, bounded, authoritative; DMS-380 proven 48h + 6 entries |
| 2 | member actual time ("сколько списал Иванов") | **SOURCE_PARTIAL** | entries carry `user.externalId`, but the endpoint is per-unit only → requires bounded fan-out over a task set (e.g. sprint membership); no direct per-user worklog endpoint |
| 3 | sprint actual spent | **SOURCE_PARTIAL** | entry `date` allows window scoping + membership defines the unit set → computable via bounded fan-out; no direct endpoint |
| 4 | team actual utilization (spent ÷ capacity) | **SOURCE_BLOCKED** | numerator partial (as #2/#3); **no authoritative capacity denominator in REAL AS21** (A215/A215B proven); only an explicit user-supplied baseline could serve as denominator (A215B pattern) |
| 5 | planned utilization (estimate ÷ capacity) | **SOURCE_BLOCKED** | estimates exist and are TQL-filterable but **sparse and unmapped**: DMS = 7 tasks with `estimate > 0` (DMS-406=3, DMS-351=3, DMS-398=8, DMS-379=1, DMS-331=2, DMS-332=2, DMS-274=2), OLP = 37 (values 1–40); `estimate` is `non_negative_int` with **no unit metadata in the source** (unit must be owner-defined, plausibly man-hours); adapter drops the field entirely; no capacity denominator |

Guards honored: cumulative totals alone are not used for person/sprint attribution (entries are what enable it); spent-alone is not treated as utilization (no denominator); task-count workload is not substituted for hours anywhere.

## Phase 6 — recommended plugin-only contracts (not implemented)

**Implement now (source-ready):**
- **`task.time_spent`** — "сколько времени списано на <task>": task-api route `GET /swtr-read/tasks/{code}/work-logs` (bounded `get_work_sum`+`get_work_report`) → adapter maps `Task.time_spent_hours` → plugin skill (CompletionContract `task_key` + `time_spent_hours`; UIContract analysis widget).
- **`task.worklogs`** — entries with date/user/type/duration: same route; only justified because the source exposes real entries (case C).

**SOURCE_CONDITIONAL now (bounded fan-out needed first):**
- **`sprint.time_spent`** / **`team.time_spent`** — require the task-level route + bounded fan-out over sprint membership (≈68 units for DMS-SPRNT-3) with per-member grouping by `user.externalId`; gate on fan-out budget like the A185 B1 contract.

**SOURCE_BLOCKED (do not implement until source grows):**
- **`team.utilization_actual`** — blocked on an authoritative capacity denominator; if the owner later accepts an explicit user baseline (A215B pattern), it becomes a variant of `team.capacity` with a spent-numerator.
- **planned utilization** — additionally blocked on estimate coverage (7 of 427 live DMS units), the adapter estimate mapping, and the source unit contract for `estimate`.

**Enabling fixes (owner, minimal):**
1. task-api bounded work-log route (first boundary);
2. adapter `estimate`→`estimate_hours` mapping from unit attributes (second boundary) + owner decision on the `estimate` unit (man-hours?);
3. optional: sprint-route estimate attribute passthrough to avoid per-task fan-out for planned metrics.

## Phase 7 — retained smoke: GREEN

- prod diff `ae4a503..e278b6c` (src+task-api) = 0 lines (running agent is production-equivalent to START_HEAD).
- team.workload DMS: COMPLETED 51 active / 17 completed / 5 unassigned / 13 members — A215 parity.
- team.capacity DMS: FAILED typed "cannot be calculated … active assigned tasks do not expose source-backed estimates" — A215B fail-closed retained.
- release.search WMB: `[24Q1, 24Q2, 25Q1]` — A212 parity.
- plugin registry (dummy-55 extensibility) 13/13; batch2 focused 5/6 (1 = A215B F1 known test-logic artifact, production proven correct).
- source audit: **local factual `/api/v1/tasks` reads = 0; unscoped `task-query` = 0.** All forensic reads were unit/bounded (DMS-380 unit + its worklogs, 2 TQL bounded counts, 627-property dictionary).

## Forensic read budget (bounded)
`read_unit` ×1 (DMS-380), `get_work_sum` ×1, `get_work_report` ×1, `get_work_log` ×1, `get_work_types` ×1, `get_tql_properties` ×1, `find_units_by_filter` ×~5 (estimate>0 DMS/OLP + dialect probes), `tools/list` ×4. No tenant-wide scans, no local-store reads, no mutation calls.

## Recommendation
Source contract for time-accounting is **real, authoritative, and detailed** (aggregate + dated, user-attributed, typed worklog entries; exact DMS-380 UI parity). Owner should implement the minimal bundle (work-log route + adapter estimate mapping + `task.time_spent`/`task.worklogs` skills) before or alongside Batch 3; sprint/team time metrics follow behind a bounded fan-out gate; utilization stays blocked pending an authoritative capacity source.
