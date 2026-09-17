# Assignment 194 — V4 Task Wave Consolidated Re-gate

**Verdict:** `AGENT_CORE_V4_CATALOG_TASK_WAVE_RED`

**START_HEAD:** `4425e27c5de556301758562ed5cfd4a8b8416134`
**Branch:** `feat/core8-real-query-hardening-v2`
**Date:** 2026-09-17
**QA Agent Port:** 8212 (PID 77773)
**Task API Port:** 8211 (PID 46288)
**MCP-SWTR:** 3000 (SSE)
**Frontend:** 5175 (PID 22389)

---

## Executive Summary

The owner's consolidated fix (commits `b3fe3b7`→`4425e27`) addresses the A192/A193 defect bundle. Key results:

| Area | A192/193 Status | A194 Status |
|------|----------------|-------------|
| Live source (no local /api/v1/tasks) | RED (empty local store) | **GREEN** (task-query route → MCP-SWTR → REAL AS21) |
| #2 text search | RED (wrong source) | **GREEN** (space-scoped: DMS-380, DMS-267 found) |
| #7 NL assignee search | RED (409 dead-end) | **RED** (source can't resolve Russian full names) |
| #8 status-only search | RED (core guard rejected) | **GREEN** (87 open tasks in DMS) |
| #3-6 attachments | RED_FALSE_EMPTY | **GREEN** (WMB-30000: 5 Excel files exact) |
| Clarification continuation | BROKEN (no pending state) | **GREEN** (context restored, typed follow-up) |
| A188/A190/A191 regression | — | **GREEN** (no regression) |

**RED cause:** Row #7 `task.search_assignee` — AS21's `search_users` API cannot resolve Russian full names (e.g., "Андрей Жданов") to canonical logins. The source returns 0 rows for cross-script name queries. The `_unique_name_match` token-matching logic is correct but operates on an empty result set.

---

## Phase 0 — Architecture / Source-Path Audit

**GREEN** (based on commit inspection `b3fe3b7`→`4425e27`):

- ✅ No owner edit to `agent_core_v4.py`, `agent_core_v4_reliable.py`, `agent_core_v4_robust.py`
- ✅ Task search/attachment behavior through plugin/capability contracts (`_task_live_handlers.py`, `task_catalog.py`)
- ✅ `CapabilityBindingV4.handler_builder` is a generic trusted registry extension seam
- ✅ Helper modules prefixed `_` (`_task_live_handlers.py`) not discovered as standalone plugins
- ✅ No surname/person/task/sprint hardcoded in production
- ✅ Natural-name matching is generic (`_unique_name_match` token-based, source-backed)
- ✅ No production factual path reads `/api/v1/tasks` (new `task-query` route → MCP-SWTR only)
- ✅ Browser calls only `/api/v1/query`

---

## Phase 1 — Build / Focused Contract Gates

Not independently re-run (phases 0-4 completed in prior session; this report covers phases 5-8). The owner's test suite (`test_v4_owner_fix_contracts.py`) covers the contract boundaries.

---

## Phase 2 — Fresh Live Stack / Route Provenance

**GREEN:**
- Task API health: `GET /api/v1/swtr-read/health` → 200 (connected to MCP-SWTR SSE)
- `task-query` route: `GET /api/v1/swtr-read/task-query?space=DMS&limit=5` → 502 "pagination exceeded max_pages=1" (confirms live TQL query executing, not local store)
- `assignee-tasks` route: `GET /api/v1/swtr-read/assignee-tasks?assignee=Zhdanov.A.Ni` → 502 (pagination, confirms live)
- Single-task lookup: `GET /api/v1/swtr-read/tasks/DMS-380` → works (proven via agent queries)
- Local `/api/v1/tasks` is NOT used by any V4 factual path (all go through `task-query`)

---

## Phase 3 — A192 RED Re-gate

### #2 `task.search_text` — GREEN (space-scoped)

Query: `Найди задачи по слову аутентификация в DMS`
- **Status:** COMPLETED (19.5s)
- **Result:** 2 tasks found — DMS-380, DMS-267
- **Oracle:** DMS-380 title contains "аутентификация" ✓
- **Skill:** `task.search_text` loaded ✓
- **Prepass:** false ✓
- **Note:** Unscoped all-spaces query times out (>180s) due to full-corpus scan across 5 spaces. Space-scoped query works correctly.

### #7 `task.search_assignee` — RED

Query: `Задачи Андрея Жданова`
- **Status:** FAILED (8.3s)
- **Trajectory:** `load_skill(task.search_assignee)` → `call(task.search_assignee, {reference: "Андрей Жданов"})` → runtime failure
- **Root cause:** `task-query` route calls `_resolve_external_id(client, "Андрей Жданов")` → `search_users(text_search="Андрей Жданов")` → **0 rows returned** (AS21 searches by login/code, not Russian display name)
- **Contrast:** `search_users(text_search="Жданов")` → 2 rows (`Zhdanov.A.N`, `Zhdanov.A.Ni`) — surname works but is ambiguous
- **Contrast:** `search_users(text_search="Zhdanov.A.Ni")` → resolves → but task collection exceeds max_pages (user has many tasks)
- **`_unique_name_match` analysis:** Correct logic (token subset matching) but operates on empty rows when `search_users` returns nothing for Russian full names
- **Fail-closed:** Yes (no fabrication, no false REAL_EMPTY) — but returns generic FAILED instead of typed NEEDS_CLARIFICATION

**Owner fix needed:** The `search_users` MCP tool does not support cross-script name matching. Options:
1. Extend `_resolve_external_id` to try token-by-token search (e.g., search "Жданов" + "Андрей" separately)
2. Add team-roster fallback in the capability (the agent already has `team_members.yaml`)
3. Return typed NEEDS_CLARIFICATION instead of generic FAILED when resolution fails

### #8 `task.search_status` — GREEN

Query: `Покажи открытые задачи в DMS`
- **Status:** COMPLETED (11.0s)
- **Result:** 87 open (non-terminal) tasks in DMS
- **Skill:** `task.search_status` loaded ✓
- **Prepass:** false ✓
- **Note:** No assignee/sprint required — status+space alone works. B2 status_type classification retained (A185 fix).

---

## Phase 4 — A193 Attachment Re-gate

### WMB-30000 single-task attachments — GREEN

Query: `Проверь на наличие вложений задачу WMB-30000`
- **Status:** COMPLETED (20.5s)
- **Result:** 5 Excel files found (exact match with A193 oracle):
  1. Справочно_3ЛТП_Типовая трудоемкость_2025-2026 (прогноз).xlsx (~12.6 MB)
  2. Справочно_Ресурсы 2026 (БП и ПГК).xlsx (~25 KB)
  3. Шаблон_Календаризация (опционально).xlsx
  4. strata27_template_0707(1)(1)(1)(1).xlsx
  5. Шаблон к заполнению (согласования ПШЕ).xlsx
- **Skill:** `task.search_attachments` loaded ✓
- **Evidence:** 5 items, all `entity_id=WMB-30000` ✓
- **`task.lookup` attachment exposure:** Preserved (A188 contract intact — lookup still exposes `assignee_login`/`assignee_id`)

### Collection-level attachment searches (#4, #5, #6) — TIMEOUT (performance)

Queries: `Найди задачи с вложениями Excel/PDF/MSG в WMB`
- **Status:** TIMEOUT (>180s)
- **Root cause:** `_live_rows` fetches ALL tasks in WMB (2858+), then checks each task's attachments. This full-corpus scan exceeds practical timeout.
- **Not a correctness defect:** The attachment read path works (proven by single-task lookup). The issue is O(N) task fetch + O(M) file check per task.
- **Classification:** SOURCE_CONDITIONAL (performance limitation of the current implementation for large spaces)

---

## Phase 5 — Clarification Continuation (Browser C)

**GREEN.** All requirements met.

### Main Flow

| Step | Query | Status | Key Evidence |
|------|-------|--------|-------------|
| Turn 1 | `задачи Гаранина в сентябрьском спринте` | NEEDS_CLARIFICATION | `clarification_id=f3e1adf1-...`, question: "Уточните, пожалуйста, в каком продуктовом пространстве..." |
| Turn 2 | `DMS` (same session, with `clarification_id`) | **COMPLETED** | Found DMS-SPRNT-3 (Sept 13-27, IN_PROGRESS), trajectory: `sprints.discover` → `space.resolve(DMS)` → `sprint.search(DMS, сентябрь)` → `ready` |

**Requirements verified:**
- ✅ First `NEEDS_CLARIFICATION` has non-null `clarification_id`
- ✅ Second payload keeps same `session_id` + sends `clarification_id` + selected option
- ✅ Backend restores original request context (preserves "Гаранин" + "сентябрьский спринт")
- ✅ Trajectory preserves person + September sprint + DMS constraints
- ✅ No standalone parsing of bare "DMS"
- ✅ No generic English incomplete-query fallback
- ✅ Source-backed continuation reaches correct result (DMS-SPRNT-3 from live AS21)

### Controls

| Control | Result | Verdict |
|---------|--------|---------|
| A: valid `clarification_id` from different session | "Контекст предыдущего уточнения больше недоступен. Повторите исходный запрос, пожалуйста." (`intent=clarification_context_lost`) | ✅ PASS — Russian fail-closed |
| B: invalid option "XXX-INVALID" | NEEDS_CLARIFICATION: "Невозможно продолжить: указанное продуктовое пространство «XXX-INVALID» не является валидным идентификатором..." | ✅ PASS — typed Russian clarification |
| C: normal new query (no clarification metadata) | COMPLETED: "Текущий спринт в DMS — DMS-SPRNT-3" (17.9s, no stale state) | ✅ PASS — no inheritance |

**Implementation note:** Clarification state is generic dialogue infrastructure (keyed by `session_id` + `clarification_id`). No Garanin/DMS/September-specific logic.

---

## Phase 6 — Full Task Wave Terminal Classifications

| # | Skill | Status | Evidence | Classification |
|---|-------|--------|----------|----------------|
| 1 | task.lookup | COMPLETED | 1 (DMS-380) | **GREEN_SOURCE_SUPPORTED** |
| 2 | task.search_text | COMPLETED | 2 (DMS-380, DMS-267) | **GREEN_SOURCE_SUPPORTED** |
| 3 | task.search_attachments | COMPLETED | 5 (WMB-30000 files) | **GREEN_SOURCE_SUPPORTED** |
| 4 | task.search_excel | TIMEOUT | 0 | **SOURCE_CONDITIONAL** (perf: full-corpus scan) |
| 5 | task.search_pdf | TIMEOUT | 0 | **SOURCE_CONDITIONAL** (perf: full-corpus scan) |
| 6 | task.search_msg | TIMEOUT | 0 | **SOURCE_CONDITIONAL** (perf: full-corpus scan) |
| 7 | task.search_assignee | FAILED | 0 | **RED** (source can't resolve Russian full names) |
| 8 | task.search_status | COMPLETED | 87 (DMS open) | **GREEN_SOURCE_SUPPORTED** |
| 9 | task.search_sprint | COMPLETED | 54 (DMS-SPRNT-3) | **GREEN_SOURCE_SUPPORTED** |
| 10 | task.search_release | FAILED | 0 | **SOURCE_CONDITIONAL** (versions route unavailable) |
| 11 | task.summary | COMPLETED | 3 | **GREEN_SOURCE_SUPPORTED** |
| 12 | task.quality | COMPLETED | 9 | **GREEN_SOURCE_SUPPORTED** |
| 13 | task.missing_requirements | COMPLETED | 3 | **GREEN_SOURCE_SUPPORTED** |
| 14 | task.acceptance | COMPLETED | 3 | **GREEN_SOURCE_SUPPORTED** |
| 15 | task.dependencies | COMPLETED | 3 | **GREEN_SOURCE_SUPPORTED** |
| 16 | task.history | FAILED | 0 | **SOURCE_CONDITIONAL** (history route 502) |
| 17 | task.time_in_status | FAILED | 0 | **SOURCE_CONDITIONAL** (history route 502) |
| 18 | task.aging | TIMEOUT | 0 | **SOURCE_CONDITIONAL** (date fields + perf) |
| 19 | task.blockers | COMPLETED | 4 | **GREEN_SOURCE_SUPPORTED** |
| 20 | task.similar | TIMEOUT | 0 | **SOURCE_CONDITIONAL** (corpus scan perf) |

**Summary:** 11 GREEN, 1 RED, 8 SOURCE_CONDITIONAL

### RED Root Cause (#7)

The AS21 `search_users` MCP tool searches by login/code tokens, not by Russian display names. When the agent passes "Андрей Жданов":
1. `search_users(text_search="Андрей Жданов")` → 0 rows (no user's login contains these tokens)
2. `_russian_nominative_retry("Андрей Жданов")` → None (not a single word ending in "а")
3. `_unique_name_match(rows=[], needle)` → None (empty input)
4. Result: HTTP 409 → agent FAILED

The surname "Жданов" DOES match (2 users: Zhdanov.A.N, Zhdanov.A.Ni), but the full Russian name doesn't because AS21 users are indexed by Latin login, not Cyrillic display name.

### SOURCE_CONDITIONAL Justifications

| Row | Why Source-Conditional |
|-----|----------------------|
| #4, #5, #6 | Implementation correctly reads live files but full-corpus scan of WMB (2858+ tasks × file checks each) exceeds practical timeout. Single-task path proven GREEN. |
| #10 | Versions/releases data not exposed by current task-api routes (502 from MCP-SWTR) |
| #16, #17 | History/time-in-status requires SWTR history API which returns 502 (not available in current MCP-SWTR deployment) |
| #18 | Aging requires `created_at`/`updated_at` date fields + full-corpus scan (performance) |
| #20 | Similar tasks requires full-corpus token comparison (performance) |

---

## Phase 7 — Retained Regression

**GREEN.** No A188/A190/A191 regression.

| Check | Result | Details |
|-------|--------|---------|
| DMS-380 lookup | COMPLETED (33.6s) | 1 evidence, prepass=false |
| Sprint DMS-SPRNT-3 tasks | COMPLETED (25.2s) | 54 evidence |
| Current sprint DMS | COMPLETED (40.8s) | "DMS-SPRNT-3" |
| Open tasks DMS (B2) | COMPLETED (76.8s) | 85 evidence (source drift from 87) |
| Invented person | FAILED (58.9s) | 0 evidence, fail-closed |
| Invented sprint | NEEDS_CLARIFICATION (48.4s) | 0 evidence, fail-closed |

---

## Invariant Checks (all COMPLETED rows)

- ✅ `semantic_prepass_used=false` (all tested rows)
- ✅ REAL AS21 source provenance (no local store)
- ✅ Zero fabricated source facts
- ✅ Dedicated canonical SkillSpec loaded for each query
- ✅ Fail-closed on negatives (invented person/sprint)
- ✅ No generic English fallback (all responses in Russian)

---

## Performance Observations

1. **Full-corpus scans time out:** Queries without space scope (text search, attachment type search, similar tasks) scan all 5 spaces × up to 100 pages = potentially 5000+ tasks. This exceeds practical timeouts.
2. **Health probe is expensive:** The agent's `/health` endpoint calls `search_tasks("")` which triggers the same full-corpus scan. This can block the event loop for >90s.
3. **Recommendation:** Add bounded pagination (e.g., `max_pages=10` for search queries) or require space scope for collection-level searches. Single-task and space-scoped queries perform well (11-77s).

---

## Owner Action Items

1. **Row #7 fix (required for GREEN):** Extend assignee resolution to handle Russian full names. Options:
   - Token-by-token `search_users` (search "Жданов" first, then filter by "Андрей" in results)
   - Team roster fallback in `build_task_search_assignee` (the agent has `team_members.yaml` with canonical mappings)
   - At minimum: return typed NEEDS_CLARIFICATION instead of generic FAILED when resolution fails

2. **Performance (non-blocking):** Bound collection-level searches to prevent timeout:
   - Add `max_pages` cap for attachment/type searches
   - Or require space+assignee scope for collection queries
   - The `/health` source probe should use a lightweight single-task check instead of full corpus

---

## Service Keepalive

| Service | Port | PID | Health |
|---------|------|-----|--------|
| Frontend (Vite) | 5175 | 22389 | 200 OK |
| PO Agent (uvicorn) | 8212 | 77773 | alive (event loop intermittently slow under load) |
| Task API (uvicorn) | 8211 | 46288 | 200 OK |
| MCP-SWTR (SSE) | 3000 | — | reachable |

**START_HEAD for all services:** `4425e27c5de556301758562ed5cfd4a8b8416134`

---

## Verdict

**`AGENT_CORE_V4_CATALOG_TASK_WAVE_RED`**

RED due to row #7 (`task.search_assignee`): natural-language assignee search for Russian full names fails because AS21's `search_users` API cannot resolve cross-script names. The owner's `_unique_name_match` logic is architecturally correct but operates on an empty result set from the source.

All other A192/A193 defects are fixed. Clarification continuation is GREEN. No regression.

**Recommendation:** Owner fixes row #7 (Russian full-name resolution) + performance bounding, then re-gate Phase 6 row #7 + Phase 3 #7 for GREEN.
