# A230R2.2-SOURCE-AUDIT — Worklogs by person and date range (READ-ONLY QA)

**Verdict: AGENT_CORE_V4_A230R2_2_WORKLOG_SOURCE_AUDIT_GREEN (audit completeness; source endpoint availability = YES at raw AS21 level, NO at MCP/task-api/agent level)**

## Identity

| Field | Value |
|-------|-------|
| TESTED_HEAD | `bee679ad99ee58e01ffe1d48357c934bfeded1a4` |
| REPORT_COMMIT | _(this commit)_ |
| Date | 2026-10-23 (server-local MSK ~09:20–09:40) |
| Branch | `feat/core8-real-query-hardening-v2` |
| Role | QA/source-oracle only — **zero** production/test/runtime/config/Core/API modifications (git-verified: no tracked changes except this report) |
| Services | agent 8004 (PID 97110, code @6708883 ≡ bee679a code, flags ALL OFF), task-api 8241 (PID 78133, MCP SSE 48 tools), MCP-SWTR 3000 (PID 78067) |

### P0 — Frozen Core (re-verified at TESTED_HEAD)

Core 6/6 **byte-identical** to `6fb335d`: `agent_core_v4.py` 52100ca1, `agent_core_v4_robust.py` 3bdb4d09, `agent_core_v4_reliable.py` 1f7562dc, `agent_core_v4_completion.py` cf75a6d6, `v4_plugin_registry.py` d82929d1, `llm/real.py` 1cc10e12. `git diff 14a16ea..HEAD -- po-agent-platform-v2/src task-api` = empty (bee679a is docs-only). All goal flags OFF.

---

## P1 — Proven read-side API contracts (the core finding)

### 1.1 Raw AS21 timesheet API (from `mcp-swtr/api-docs.json`, 1111 endpoints; live-confirmed)

**`POST /rest/api/timesheet/v1/report` — server-filtered worklog report. This is the endpoint the audit is about.**

- Request `SwtrTimesheetPageRq`:
  ```json
  { "filter": { "users": ["Garanin.R.V"], "spaces": ["DMS"], "units": ["DMS-472"],
                "range": { "from": "2026-10-01", "to": "2026-10-23" } },
    "page": { "page": 0, "size": 50 } }
  ```
- Response `SwtrTimesheetPageRs`: `{ content: WorkLogInfo[], pageNumber, pageSize, hasNext }`.
- `WorkLogInfo`: `{ id (UUID), date (YYYY-MM-DD), unit, comment, time {temporalUnit, time, duration ISO-8601}, time_spent, type {code,name,description}, user {externalId, firstName, lastName, middleName} }`.
- Auth: same Bearer token plane as all other SWTR reads (probes used the running MCP's own credentials; token never printed). Spec documents 400/401/403 error shapes.

**Live proof (bounded, size ≤ 100, ≤ few pages each; redacted):**

| Probe | Filter | Result |
|-------|--------|--------|
| **users + range (the C3 shape)** | `users=[Garanin.R.V]`, `range 01.10→23.10.2026` | **200, 14 rows, hasNext=False, 0.1s** — all dates in range, all author=Garanin.R.V |
| users + wide range | `users=[Garanin.R.V]`, `range 01.01.2025→23.10.2026` | 200, 60 rows, hasNext=False, min date 2026-03-01 (person's full lifetime = 60 entries) |
| users, **no range** | `users=[Garanin.R.V]` | 200, 20 rows, min 2026-09-23 — **implicit server default window ≈ last 30 days** (pitfall; see §4) |
| spaces + range | `spaces=[DMS]`, `range 01.10→23.10` | 200, 50 rows, hasNext=True (8 distinct authors — filter server-side, not client) |
| units + range | `units=[DMS-380]`, `range 01.09→30.09` | 200, 6 rows — authors Garanin.R.V **and** Semavin.M.M (multi-author task; author ≠ assignee pattern, A215G parity) |
| units, no range | `units=[DMS-472]` / `units=[DMS-380]` | 6 rows / **0 rows** — 0 explained by the 30-day default window (DMS-380 entries 06–07.09 fall outside); NOT a filter defect |
| empty filter (bounded, size 1, 1 page) | `{}` | 1 row + hasNext=True — **no filter = tenant-wide stream; never use** |

- Latency: 0.0–0.1 s per bounded page. Pagination: `page/size/hasNext` (size up to 1000 on the per-unit route; 100 proven on the POST route).
- Redacted sample row (Garanin, 16.10.2026): `{"id":"6e53b313-****","date":"2026-10-16","unit":"DMS-472","time":{"temporalUnit":"MILLIS","time":28800000,"duration":"PT8H"},"type":{"code":"61","name":"2Р_Кодирование"},"user":{"externalId":"Garanin.R.V","name":"***"}}`.

### 1.2 MCP-SWTR (48 live tools) — worklog read surface

- `get_work_report(unit_code, page, size≤1000)` → `GET /rest/api/timesheet/v1/report/{unit}` (per-unit, pagination, hasNext)
- `get_work_sum(unit_code)` → `GET .../report/{unit}/sum` (proven: DMS-380 = PT48H = 6×8h, consistent with its 6 entries)
- `get_work_log(work_log_id)` → `GET /rest/api/timesheet/v1/worklog/{id}` (point read)
- `get_work_types()` → 31 work types (bounded reference)
- **No MCP tool wraps `POST /rest/api/timesheet/v1/report` — the only server-side person/date/spaces/units filtered query is UNREACHABLE from the agent today.** (Mutation tools `create/update/delete_work_log` exist in MCP but are out of audit scope; not called.)

### 1.3 Task API

- `GET /api/v1/swtr-read/tasks/{task_code}/work-logs` (swtr_read.py:944) = per-unit only (MCP `get_work_report` + `get_work_sum`, `complete` flag, convention 8h/day 5d/week). **No person/date route exists.**

## P2 — Agent capability surface (handler definitions, code-exact)

| Capability | Required args | Source path | Attribution / date semantics |
|-----------|--------------|-------------|------------------------------|
| `task.worklogs` | `task_key` | adapter `get_task_worklogs` → task-api per-unit route | row: id, date, **user_external_id (worklog author)**, work_type, duration_hours, comment; `complete` mandatory |
| `task.time_spent` | `task_key` | same; cross-checks `total_hours` == sum(entries) | REAL_AS21, fail-closed on incomplete/mismatch |
| `member.time_spent` / `member.worklogs` / `member.utilization_actual` | `member_login` + **`space`** + **`sprint_id`** (typed `V4NeedsClarification` when absent) | complete sprint collection → bounded per-task worklog fan-out (semaphore) → **client-side** date filter `_within(start, finish)` on the sprint window, author filter `external_id.casefold()` | `attribution: worklog_author_external_id` (deliberately NOT current assignee); utilization denominator = OWNER_POLICY |

**Plugin docstring states the design intent explicitly:** *"Arbitrary rolling-period aggregation is intentionally not implemented because the current source exposes worklogs only through bounded per-task reads. A source-backed sprint provides the required bounded task universe."* — this premise is now **factually outdated**: the raw source exposes a server-filtered person+date query (§1.1). Person + arbitrary date + no sprint/task = no mapped capability → C3.

## P3 — Bounded live probe evidence

All probes in `/private/tmp/qa230r22/` (`probe_report.py/json`, `probe_report2.py/json` + inline follow-ups). Safety: bounded filters (one user / one unit / one space), size ≤ 100, ≤ 2 pages each except the single-row empty-filter control; **0 mutations, 0 source writes, 0 unscoped multi-page scans, no credentials printed**.

Key proven facts (repeated from §1.1): person+range = 14 rows @23.10.2026; lifetime = 60; implicit 30-day default window; multi-author per unit; 0.0–0.1 s latency.

## P4 — One real request: «покажи списания Гаранина с 01.10.2026 по сегодня»

- Result: **NEEDS_CLARIFICATION**, wall 86.1 s, `clarification_id` issued, options=[].
- Trajectory: turn 1 `load_skill member.worklogs` (intent correctly understood: "списания … for a person … over a date range") → turn 2 `member.resolve("Гаранин")` → **Garanin.R.V** (REAL_AS21, 200) → turn 3+: bounded repair exhausted → `_promote_planner_failure_to_clarification`.
- **First failed boundary:** `member.worklogs` cannot be called — it hard-requires `space`+`sprint_id` (neither given, neither implied by a worklog query) and no person+date capability exists. The terminal question is the **generic task-search filter hint** («исполнитель, пространство, статус, тип задачи, **период создания** и/или спринт»; recommended format «Открытые задачи … созданные с \<дата\>») — **wrong surface** (task-creation filters for a worklog question; A230R1 C3 defect class, still open).
- **LLM vs capability separation:** agent log for this request = 7 LLM POSTs **all 200**, 1 task-api GET (200), **0×429, 0 ReadTimeout, 0 ConnectError** → the failure is **pure capability absence**, not endpoint degradation.
- No fabrication, no false zero, 0 worklog calls executed — safe fail-closed, but not typed UNSUPPORTED-for-worklogs.

## P5 — Recommended minimal implementation (non-Core, for owner)

**Chain (follows the existing certified architecture agent → task-api → MCP → SWTR):**

1. **MCP (read-only tool, `mcp-swtr/mcp_server.py`):** `get_work_report_filter(request)` wrapping `POST /rest/api/timesheet/v1/report` with `SwtrTimesheetFilters {users[], spaces[], units[], range{from,to}}` + `SwtrTimesheetPage {page,size}`. No mutation surface added.
2. **Task API route:** `GET /api/v1/swtr-read/work-logs/report?user=&from=&to=&space=&unit=&page=&size=` — **always** forwards an explicit `range` (never omit it — §4 pitfall), validates `user` against the approved identity (reuse `_resolve_external_id`), caps `size ≤ 100`, `max_pages ≤ 50`, returns `{entries[], total_hours, count, complete, pages_read, source:"REAL_AS21"}` with the same `complete`-flag contract as the per-unit route; 502 on transport/pagination exhaustion, 403/401 → typed error, 400 on invalid dates.
3. **New plugin capability `member.worklogs_period`** (own plugin file, e.g. `time_accounting_member_period.py`; registration-only surface, zero Core/planner changes):
   - **Inputs (typed):** `member_login` (canonical externalId from `member.resolve`), `from`/`to` (YYYY-MM-DD, inclusive; `to ≤ today`; span ≤ 366d guard), optional `space` (bounding), optional `unit`.
   - **Output:** `{member_login, from, to, worklog_count, total_hours, entries:[{id,date,unit,type_code,type_name,duration_hours,user_external_id,comment}], complete, source:"REAL_AS21", attribution:"worklog_author_external_id", date_semantics:"logged_on_date_not_created"}`.
   - **Normalization:** `time.time` MILLIS → hours (duration cross-check); type name from source.
   - **Completion:** `CompletionRequirement("member.worklogs_period", data_keys=("worklog_count",))` — scalar REAL_EMPTY-safe key (A215F2 precedent) so a genuine 0-entries window completes.
   - **Provenance/safety:** source-backed entries only; missing/incomplete → `V4CapabilityUnavailable`/`AS21SourceUnavailable` fail-closed; 403 → typed «недостаточно прав на отчет по списаниям»; never fall back to `task.search_created` or per-task fan-out.
   - **Procedure (planner text):** "Person + worklogs/списания + explicit date window (no sprint) → `member.worklogs_period`. Do NOT reinterpret the period as task creation (`task.search_created`) and do NOT require space/sprint for a worklog question. If no window is given, ask for an explicit date range."
   - **UI contract:** `member_worklogs_period` widget, required_fields `(worklog_count, total_hours, entries)`.
4. **Tests (non-mocked, A222R masking class avoided):**
   - SSE-mock of the proven `SwtrTimesheetPageRs` shape: user+range happy path (14-row fixture), 0-entries REAL_EMPTY, `hasNext=True` multi-page, `complete=false` → fail-closed, 403 → typed, transport error → 502.
   - Route regression: range always forwarded (assert request body contains explicit `range` even when caller omits — fail closed instead), size/max_pages caps, invalid dates 400.
   - Live parity regression (optional gate): person=Гаранин, 01.10→today vs raw probe (14 rows @23.10.2026 baseline; drift-tolerant, rebuild oracle at run time as in A230R2.1).
   - Existing member/task worklog suites unchanged (no regression: new capability is additive).

**Do not** implement: assignee-based worklog filtering (source filters by author only), creation-date filtering (no such field), tenant-wide report reads, mutation tools.

## P6 — Safety & open items

- No credential printing, no mutation, no source writes, no unscoped reads (empty-filter control was single-row/single-page by design).
- Remote/multi-user session auth/ownership remains OPEN (client-chosen session_id) — unchanged deployment blocker.
- Coverage gaps: (a) worklog rows expose **logged-on `date` only** — no created/updated timestamp, so «созданные за период» vs «списанные за период» are distinct and only the latter is source-backed; the capability contract must state this; (b) `user` = worklog **author** (recorder), not unit assignee — correct fit for «списания <человека>», but multi-author rows on one unit must be preserved (proven: DMS-380 has 2 authors); (c) implicit 30-day default window when `range` omitted — must never be relied upon; (d) `units` filter proven but not required by the recommended capability; (e) 403 not separately probed (same token plane as all proven reads; spec documents it).

**This is a source audit, NOT implementation GREEN. STOP — no implementation performed.**
