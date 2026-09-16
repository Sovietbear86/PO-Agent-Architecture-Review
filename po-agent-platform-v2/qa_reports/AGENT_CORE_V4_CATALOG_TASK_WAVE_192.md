# A192 — V4 Catalog Task Wave (#1–20) QA Report

**Verdict:** `AGENT_CORE_V4_CATALOG_TASK_WAVE_RED`

**Test base HEAD:** `66a8c10bf67fccae23b4efe179c31e05d2084ac9`  
**Branch:** `feat/core8-real-query-hardening-v2`  
**Date:** 2026-09-16  
**Services:** task-api 8211, PO Agent 8212 (V4 enabled, plugins: `builtin.catalog.tasks`, `builtin.core.a188`)  
**Source:** REAL AS21 via task-api → MCP-SWTR (SSE, live)  
**Concurrency:** 1  
**Oracle B:** independent live task-api queries at test time

---

## Summary

The first V4-Catalog Task Wave (15 new SkillSpecs beyond the 5 already in `builtin.core.a188`) is architecturally clean, plugin-registry compliant, and UI-contract correct. 10 of 20 canonical Task rows are `GREEN_SOURCE_SUPPORTED`, 7 are `SOURCE_CONDITIONAL` (source genuinely lacks the needed surface), and **3 are RED** due to capability-path defects:

| RED Row | Root Cause |
|---------|-----------|
| #2 `task.search_text` | Legacy capability scans empty local store (`GET /api/v1/tasks` = []) instead of live SWTR read routes; phrase literally exists in DMS-380 title but returns 0 |
| #7 `task.search_assignee` | `member.resolve` returns 409 for natural-language names; only exact canonical login works; skill procedure dead-ends |
| #8 `task.search_status` | V4 core `task.search` handler (agent_core_v4.py:889) rejects status-only queries without assignee/sprint_id |

No A188/A190/A191 regression detected. All GREEN rows produce correct, source-backed, deterministic results with `runtime_contract` completion and `semantic_prepass_used=false`.

---

## Phase 0 — Architecture / Static Audit

**GREEN.** Verified at service startup:
- Plugin `builtin.catalog.tasks` loaded with 15 SkillSpecs + 15 capabilities + 15 bindings + 15 UI contracts
- `builtin.core.a188` unchanged (provides #1 task.lookup, #11 task.summary, #12 task.quality, #14 task.acceptance, #19 task.blockers)
- No edit to agent_core_v4.py / agent_core_v4_reliable.py / agent_core_v4_robust.py / planner / runtime trajectory
- No surname/person/task/sprint/release/query-phrase hardcode in production
- Fixed binding arguments (attachment_type=excel/pdf/msg) are generic extension-surface behavior
- Registry ordering/duplicate/malformed: fail-closed (proven by A190 dummy-55 test, retained)
- Browser UI remains presentation-only (V4ResultPanel.tsx renders from response, no capability selection)

---

## Phase 1 — Build / Contract Gates

**GREEN** (from prior session, services started cleanly at HEAD 66a8c10):
- `test_agent_core_v4_task_catalog.py`: GREEN
- `test_agent_core_v4_plugin_registry.py`: GREEN
- `test_agent_core_v4_completion_contract.py`: GREEN
- `test_v4_browser_api_contract.py`: GREEN
- `pytest -k "v4"`: no new failures
- `frontend npm run build`: GREEN (TypeScript + Vite)

---

## Phase 2 — Fresh REAL AS21 Oracle Discovery

Live source facts at test time:
- **DMS-380**: code=DMS-380, summary="В компоненте Lineager не работает аутентификация в режиме mTLS, TLS, SSL", assignee=Semavin.M.M, status=QA, description 6137 chars, files=[], no dependencies
- **Semavin.M.M**: 311 tasks (live assignee-tasks route)
- **Zhdanov.A.Ni**: 10 tasks (CRPV-110524, DMS-1, DMS-103, DMS-154, DMS-371, DMS-6, DMS-69, DMS-71, STS-227529, WMB-29909)
- **DMS-SPRNT-3** (current sprint): 52 tasks
- **History route**: unavailable (502 from MCP-SWTR)
- **Versions/releases route**: unavailable (502)
- **Local store** (`GET /api/v1/tasks`): **empty** (0 tasks)
- **Sprint task fields**: source_id, title, status, source, source_data (no date fields)

---

## Phase 3 — Agent A / Oracle B Task #1–20 Certification

### 20-Row Classification Table

| # | Skill | Query | Status | Completion | Oracle Parity | Classification |
|---|-------|-------|--------|------------|---------------|----------------|
| 1 | task.lookup | Покажи задачу DMS-380 | COMPLETED | runtime_contract | DMS-380, Semavin.M.M, QA ✓ | **GREEN_SOURCE_SUPPORTED** |
| 2 | task.search_text | Найди задачи по слову аутентификация | COMPLETED (0) | runtime_contract | DMS-380 HAS phrase in title ✗ | **RED** |
| 3 | task.search_attachments | Какие задачи имеют вложения | COMPLETED (0) | runtime_contract | DMS-380 files=[] ✓ | **SOURCE_CONDITIONAL** |
| 4 | task.search_excel | Найди задачи с вложениями Excel | COMPLETED (0) | runtime_contract | type=excel fixed ✓ | **SOURCE_CONDITIONAL** |
| 5 | task.search_pdf | Найди задачи с вложениями PDF | COMPLETED (0) | runtime_contract | type=pdf fixed ✓ | **SOURCE_CONDITIONAL** |
| 6 | task.search_msg | Найди задачи с вложениями MSG | COMPLETED (0) | runtime_contract | type=msg fixed ✓ | **SOURCE_CONDITIONAL** |
| 7 | task.search_assignee | Задачи Андрея Жданова | NEEDS_CLARIFICATION | — | Zhdanov.A.Ni=10 tasks ✗ | **RED** |
| 8 | task.search_status | Покажи открытые задачи в DMS | NEEDS_CLARIFICATION | — | Open tasks exist in DMS ✗ | **RED** |
| 9 | task.search_sprint | Покажи задачи в спринте DMS-SPRNT-3 | COMPLETED (52) | runtime_contract | 52/52 exact ✓ | **GREEN_SOURCE_SUPPORTED** |
| 10 | task.search_release | Покажи задачи по релизу DMS 2026.09 | NEEDS_CLARIFICATION | — | versions 502 | **SOURCE_CONDITIONAL** |
| 11 | task.summary | Суммаризируй задачу DMS-380 | COMPLETED | runtime_contract | Source fields ✓ | **GREEN_SOURCE_SUPPORTED** |
| 12 | task.quality | Оцени качество постановки задачи DMS-380 | COMPLETED (85/100) | runtime_contract | Deterministic ✓ | **GREEN_SOURCE_SUPPORTED** |
| 13 | task.missing_requirements | Какие требования отсутствуют в задаче DMS-380 | COMPLETED | runtime_contract | acceptance_expectations ✓ | **GREEN_SOURCE_SUPPORTED** |
| 14 | task.acceptance | Проанализируй критерии приёмки задачи DMS-380 | COMPLETED (0/100) | runtime_contract | No criteria in source ✓ | **GREEN_SOURCE_SUPPORTED** |
| 15 | task.dependencies | Какие зависимости есть у задачи DMS-380 | COMPLETED (0) | runtime_contract | No deps in source ✓ | **GREEN_SOURCE_SUPPORTED** |
| 16 | task.history | Покажи историю задачи DMS-380 | FAILED | — | History 502 | **SOURCE_CONDITIONAL** |
| 17 | task.time_in_status | Сколько времени задача DMS-380 провела в статусах | FAILED | — | History 502 | **SOURCE_CONDITIONAL** |
| 18 | task.aging | Покажи стареющие задачи старше 7 дней | COMPLETED (0) | runtime_contract | No date fields in source | **SOURCE_CONDITIONAL** |
| 19 | task.blockers | Что блокирует задачу DMS-380 | COMPLETED | runtime_contract | Not blocked, 0 deps ✓ | **GREEN_SOURCE_SUPPORTED** |
| 20 | task.similar | Найди похожие задачи на DMS-380 | COMPLETED (0) | runtime_contract | token_jaccard_v1, empty corpus | **SOURCE_CONDITIONAL** |

### RED Root Causes

**#2 task.search_text — wrong data source (silent empty scan)**

The binding `CapabilityBindingV4("task.search_text", legacy_capability_id="task.search")` routes to `PortfolioCapabilities.task_search` (runtime.py:77). This legacy handler calls `adapter.search_tasks("")` with no max_results → base adapter defaults to `GET /api/v1/tasks?limit=50` (local SQLite store). The local store is **empty** (0 tasks confirmed via Oracle B: `GET /api/v1/tasks?limit=10000` → `[]`). Meanwhile DMS-380 IS accessible via the live route `GET /api/v1/swtr-read/tasks/DMS-380` and its title literally contains "аутентификация". The capability scans the wrong (empty) source and returns 0 — a silent-truncation/wrong-source defect, not a source unavailability.

**#7 task.search_assignee — member.resolve dead-end for NL names**

The skill procedure instructs: "Resolve the human reference with member.resolve; never invent a login." The planner correctly loads the skill and calls `member.resolve` with `reference="Андрей Жданов"`. The task-api endpoint `/api/v1/swtr-read/assignees/resolve` returns:
- `"Андрей Жданов"` → **409 Conflict**
- `"Жданов"` → **409 Conflict**
- `"Zhdanov"` → **409 Conflict**
- `"Zhdanov.A.Ni"` → **200** (works)

The source route only resolves exact canonical logins or returns 409 for ambiguous partial matches. The team directory grounding that works in the semantic layer (proven in A188: Zhdanov 11/11) is NOT leveraged by this skill's procedure. The result is NEEDS_CLARIFICATION with "Не удалось однозначно определить пользователя".

**#8 task.search_status — core handler rejects status-only**

The skill procedure says "Call task.search with the requested status." The planner calls `task.search` with `{"status": "not_completed", "space": "DMS"}`. The V4 core handler (agent_core_v4.py:889) has a fail-closed guard:
```python
if not any((assignee, sprint_id)):
    raise V4NeedsClarification("Для skill-native POC task.search нужен исполнитель и/или спринт; уточните фильтр.")
```
Status-only queries without assignee/sprint are structurally rejected. The skill is declared but cannot fulfill its stated purpose.

### Invariant Checks (all GREEN rows)

For every successful contracted run:
- `semantic_prepass_used=false` ✓ (all 20 rows)
- REAL AS21 authoritative (source="REAL_AS21" in evidence) ✓
- `completion=runtime_contract` ✓ (all COMPLETED rows)
- Zero fabricated source facts ✓
- Dedicated canonical SkillSpec loaded and reachable ✓ (all 20 rows show correct `loaded_skills`)

### Fixed Attachment Type Verification (#4, #5, #6)

- #4: `attachment_type="excel"` in step data ✓
- #5: `attachment_type="pdf"` in step data ✓
- #6: `attachment_type="msg"` in step data ✓

The planner passed no arguments (`{}`); the fixed type came from the plugin binding. Correct.

### Dedicated Skill Reachability

All 20 canonical SkillSpecs are explicitly loaded by the planner for their natural-language queries. No canonical row is shadowed by a helper (each query loads exactly its dedicated skill id).

---

## Phase 4 — Browser C / UIContract

**GREEN.** All via public `/api/v1/query`, runtime confirmed as "Agent Core v4".

| Case | Query | Status | UI result_kind | UI preferred_widget | Notes |
|------|-------|--------|----------------|---------------------|-------|
| P4-1 | Покажи задачи в спринте DMS-SPRNT-3 | COMPLETED | task_collection | task_table | 52 tasks, runtime_contract |
| P4-2 | Покажи задачу DMS-380 | COMPLETED | task | task_detail | From core plugin, runtime_contract |
| P4-3 | Какие зависимости есть у задачи DMS-380 | COMPLETED | analysis | task_dependencies | runtime_contract |
| P4-4 | Найди похожие задачи на DMS-380 | COMPLETED | similar_task_collection | similar_task_list | runtime_contract |
| P4-5 | Какие задачи имеют вложения | COMPLETED | attachment_collection | attachment_table | REAL_EMPTY (0 results) |
| P4-6 | Покажи задачу DMS-99999 | COMPLETED | task | task_detail | planner_ready, "not found" (fail-closed) |
| P4-7 | Покажи стареющие задачи старше 7 дней | COMPLETED | task_collection | task_table | REAL_EMPTY (0 results) |

Verified:
- `ui.result_kind` / `preferred_widget` match task_catalog.py UIContract definitions exactly ✓
- `runtime` = "Agent Core v4" in all responses ✓
- `semantic_prepass_used=false` in all ✓
- No local `/tasks`, MCP/SWTR, fake route, or client-side capability selection ✓
- REAL_EMPTY (P4-5, P4-7) correctly distinguished from ERROR/SOURCE_UNAVAILABLE ✓
- P4-6 (invented task): fail-closed with "not found" message, no fabrication ✓

---

## Phase 5 — Retained A191/A190 Regression

**GREEN. No regression detected.**

| Case | Query | Status | Count | Oracle | Match |
|------|-------|--------|-------|--------|-------|
| P5-1 | Покажи DMS-380 и затем задачи его исполнителя | COMPLETED | 311 | 311 | ✓ |
| P5-2 | (same x2) | COMPLETED | 311 | 311 | ✓ |
| P5-3 | (same x3) | COMPLETED | 311 | 311 | ✓ |
| P5-4 | Покажи задачи в текущем спринте DMS | COMPLETED | 52 | 52 | ✓ |
| P5-5 | (same x2) | COMPLETED | 52 | 52 | ✓ |
| P5-6 | Открытые задачи Жданова в DMS | COMPLETED | 2 | DMS-371, DMS-1 | ✓ |
| P5-7 | (same x2) | COMPLETED | 2 | DMS-371, DMS-1 | ✓ |
| P5-8 | Задачи Несторова В.Х. | FAILED | 0 | — | fail-closed ✓ |
| P5-9 | Покажи задачи в спринте DMS-SPRNT-99 | NEEDS_CLARIFICATION | 0 | — | fail-closed ✓ |

All A188/A190/A191 scenarios retained:
- DMS-380 multistep (lookup→assignee→search): 3/3 exact 311/311, runtime_contract ✓
- Current sprint collection: 2/2 exact 52/52 ✓
- Person+space+open (Zhdanov DMS): 2/2 exact 2/2 ✓
- B2 open-status classification: Zhdanov DMS correctly filters open (2 of 10) ✓
- Negative controls: fail-closed, 0 keys, no fabrication ✓
- Plugin registry gate: structurally GREEN (services started, plugins loaded) ✓

---

## Phase 6 — Final Classification

| # | Skill | Terminal Classification |
|---|-------|------------------------|
| 1 | task.lookup | GREEN_SOURCE_SUPPORTED |
| 2 | task.search_text | **RED** |
| 3 | task.search_attachments | SOURCE_CONDITIONAL |
| 4 | task.search_excel | SOURCE_CONDITIONAL |
| 5 | task.search_pdf | SOURCE_CONDITIONAL |
| 6 | task.search_msg | SOURCE_CONDITIONAL |
| 7 | task.search_assignee | **RED** |
| 8 | task.search_status | **RED** |
| 9 | task.search_sprint | GREEN_SOURCE_SUPPORTED |
| 10 | task.search_release | SOURCE_CONDITIONAL |
| 11 | task.summary | GREEN_SOURCE_SUPPORTED |
| 12 | task.quality | GREEN_SOURCE_SUPPORTED |
| 13 | task.missing_requirements | GREEN_SOURCE_SUPPORTED |
| 14 | task.acceptance | GREEN_SOURCE_SUPPORTED |
| 15 | task.dependencies | GREEN_SOURCE_SUPPORTED |
| 16 | task.history | SOURCE_CONDITIONAL |
| 17 | task.time_in_status | SOURCE_CONDITIONAL |
| 18 | task.aging | SOURCE_CONDITIONAL |
| 19 | task.blockers | GREEN_SOURCE_SUPPORTED |
| 20 | task.similar | SOURCE_CONDITIONAL |

**Totals:** 10 GREEN_SOURCE_SUPPORTED, 7 SOURCE_CONDITIONAL, 3 RED

---

## Known Issues (tracked separately)

- **Cyrillic identity mutation** ("Задачи Семавина" → "Семанин"): pre-existing Qwen3.8-27B tokenization, not a completion contract defect. Not the first failing boundary of any tested canonical skill in this wave.

---

## Owner Fix Recommendations

### RED #2 — task.search_text
The legacy `PortfolioCapabilities.task_search` (runtime.py:77) calls `adapter.search_tasks("")` which hits the empty local store. Options:
1. **Preferred:** Route `task.search_text` to a live SWTR read path (e.g., fetch all tasks from the space via sprint/assignee routes and filter client-side, or add a TQL text-search endpoint to task-api).
2. **Alternative:** Bind to the V4 core `_task_search` with a `phrase` argument that triggers a bounded live scan.
3. **Minimum:** Fail-closed when the local store is empty (return SOURCE_UNAVAILABLE instead of silent 0).

### RED #7 — task.search_assignee
The skill procedure should leverage team directory grounding before calling member.resolve. Options:
1. **Preferred:** Modify the skill procedure to: "Ground the person reference against the team directory; if a unique canonical login is found, call task.search directly with that assignee. If grounding is ambiguous, call member.resolve as a secondary check."
2. **Alternative:** Extend task-api `member.resolve` to accept team directory lookups (surname/first+last matching against the configured roster).
3. **Minimum:** Document the limitation and require the user to provide the canonical login.

### RED #8 — task.search_status
The V4 core `task.search` guard at agent_core_v4.py:889 blocks status-only queries. Options:
1. **Preferred:** Allow status-only queries when a space is provided, with a bounded result cap (e.g., max 1000) and explicit "showing top N" in the answer.
2. **Alternative:** Route status-only to the sprint route (fetch current sprint tasks, filter by status client-side) as a bounded approximation.
3. **Minimum:** Document the limitation in the skill spec ("requires assignee or sprint context").

---

## Verdict Justification

**`AGENT_CORE_V4_CATALOG_TASK_WAVE_RED`** because:
- GREEN requires "all source-supported canonical Task rows #1–20 GREEN"
- Rows #2, #7, #8 are source-supported (the data exists in REAL AS21) but the capability path cannot reach it
- No A188/A190/A191 regression (Phase 5 GREEN)
- Architecture/plugin gate GREEN (Phase 0-1 GREEN)
- Browser C / UIContract GREEN (Phase 4 GREEN)
- 7 SOURCE_CONDITIONAL rows are correctly proven and fail-closed (acceptable)

**NOT** `BLOCKED_BY_PROVEN_SOURCE_OUTAGE` because the source IS available (healthy, responding); the failures are capability-path defects, not source outages.
