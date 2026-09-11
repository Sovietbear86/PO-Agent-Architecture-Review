# Assignment 177 — Agent Core v4 Reliability POC Retest

**Report:** `AGENT_CORE_V4_RELIABILITY_POC_177.md`
**Date:** 2026-09-11
**Branch:** `feat/core8-real-query-hardening-v2`
**Test base HEAD:** `6d1c9b2`
**Verdict:** **`V4_CURRENT_SPRINT_RED`**

**Role:** QA/tester only. No production/backend/frontend/test code, prompts, model
config, registry contracts, committed `.env`, or learning data modified. The only file
changed by this assignment is this report.

---

## Mission recap

Continue the Agent Core v4 skill-native POC after generalized owner fixes. Phase 0
(build/static architecture gate) is already complete and its evidence is retained:
V4 focused tests 8/8 PASS; `ReliableAgentCoreV4Runtime` instantiated by the production
factory; `semantic_prepass_used=false`; no hardcoded person/sprint/task IDs; owner
commits/provenance verified.

Owner commits under test — all verified present as ancestors of HEAD `6d1c9b2`:
- `de75115` — V4 reliability overlay: team-scoped source validation, trusted-observation literal binding, source-backed current sprint
- `a8b8d63` — wire `ReliableAgentCoreV4Runtime` in production V4 runtime factory
- `57e9bcd` — focused reliability tests
- `9241f4e` — contextual identity resolution inside authoritative sprint/task context
- `0a934d9` — corrected fixtures + contextual identity regression test

---

## Phase 0 — Build / architecture gate — GREEN (checkpoint evidence)

Retained from pre-crash checkpoint (not re-executed per instructions):
- `tests/test_agent_core_v4_skill_native.py` → 8/8 PASS
- `tests/test_agent_core_v4_reliable.py` → 8/8 PASS
- `ReliableAgentCoreV4Runtime` confirmed instantiated in production factory
  (`runtime_factory.py:83`)
- `/query-v4` bypasses legacy semantic/correction runtime
- `_agent_core_v4.semantic_prepass_used == false`
- No hardcoded person/sprint/task IDs in V4 catalog/prompts
- All five owner commits verified as ancestors

---

## Critical pre-Phase 1 finding — `sprint.current` source backing — RED

Before restarting runtime services and proceeding to Phase 1, a mandatory check was
performed: **does `sprint.current` use REAL AS21/MCP-SWTR as the authoritative source?**

### Call chain (traced in source, deterministic)

```
ReliableAgentCoreV4Runtime._sprint_current_source_backed({"product": "DMS"})
  (agent_core_v4_reliable.py:319)
  → self.adapter.search_tasks('project = "DMS"', max_results=10000)
    → EvidenceValidatedProductionTaskApiAS21Adapter.search_tasks
      → HardenedProductionTaskApiAS21Adapter.search_tasks
        (hardened_production_task_api.py:279)
        # JQL parsed: project_space="DMS", sprint=None, assignee=None
        # branch: project set, no sprint, no assignee → else branch (line 303)
        → TaskApiAS21Adapter.search_tasks(self, "", max_results=self._scan_limit)
          (task_api.py:321, base class)
          # _parse_query("") → no filters, no free text → needs_local_filtering=False
          # fetch_limit = min(10000, _scan_limit)
          → self._fetch_tasks(limit=fetch_limit)
            (task_api.py:282)
            → self._client.get("/api/v1/tasks", params={"limit": ..., "offset": 0})
              → Task API route: app/routers/tasks.py list_tasks
                → TaskService.get_tasks → TaskRepository.find_all
                  → ~/.task-tracker/tasks.json (local JSON file)
```

### What the data path actually reads

`TaskRepository` (`task-api/app/repositories/task_repository.py:11`) is an **in-memory
repository with file persistence** at `~/.task-tracker/tasks.json`. It does **not** call
MCP-SWTR or any real AS21 endpoint. The file is populated only by a manual/triggered
sync process (`/api/v1/swtr/sync*`).

### Current state of the local file

```
$ ls -la ~/.task-tracker/tasks.json
-rw-r--r--  1 kalachanov.v.v  SBERTECH\Domain Users  2 Sep  1 20:27 ...
$ wc -l ~/.task-tracker/tasks.json
0
```

The file is **empty** (2 bytes = `[]`). Therefore `_sprint_current_source_backed` will
always return `sprint_id=None` with `warnings=["current_sprint_not_found"]` for every
space, regardless of the actual AS21 state.

### Contrast with the correct source path

The adapter already has a method that uses REAL AS21 via MCP-SWTR:

```python
# production_task_api.py (ProductionTaskApiAS21Adapter.get_current_sprint)
response = await self._client.get(
    f"/api/v1/swtr-read/spaces/{normalized}/current-sprint"
)
```

This endpoint (`task-api/app/routers/swtr_read.py:316`) calls
`SWTRMCPClient.call_tool("get_current_sprint", {"space": ...})` → MCP-SWTR → REAL AS21.

Assignment 176 Oracle B confirmed: DMS current sprint = **`DMS-SPRNT-1`**.

### Why the other handlers are unaffected

All other V4 handlers use the `swtr-read` endpoints (REAL AS21 via MCP-SWTR):

| Handler | Path | Source |
|---------|------|--------|
| `_resolve_source_login` | `GET /api/v1/swtr-read/assignees/resolve` | REAL AS21 |
| `_resolve_identity_in_task_context` | `adapter.get_sprint_tasks` → `GET /api/v1/swtr-read/sprints/{sprint}/tasks` | REAL AS21 |
| `_task_search` (assignee) | `adapter.search_tasks(assignee=...)` → `GET /api/v1/swtr-read/assignee-tasks` | REAL AS21 |
| `_task_search` (sprint) | `adapter.get_sprint_tasks` → `GET /api/v1/swtr-read/sprints/{sprint}/tasks` | REAL AS21 |
| **`_sprint_current_source_backed`** | **`adapter.search_tasks(project=...)` → `GET /api/v1/tasks` → local JSON file** | **LOCAL CACHE** |

### First failing boundary

**Function:** `ReliableAgentCoreV4Runtime._sprint_current_source_backed`
**File:** `po-agent-platform-v2/src/po_agent/harness/agent_core_v4_reliable.py`, line 319
**Defect:** Calls `self.adapter.search_tasks(f'project = "{product}"', max_results=10000)`
which routes through the legacy local-file task cache instead of the authoritative
`self.adapter.get_current_sprint(product)` endpoint (which goes through MCP-SWTR to REAL AS21).

**Raw call chain:**
```
_sprint_current_source_backed
  → adapter.search_tasks('project = "DMS"')
    → HardenedProductionTaskApiAS21Adapter.search_tasks (project branch)
      → TaskApiAS21Adapter.search_tasks (base, no assignee/sprint)
        → _fetch_tasks → GET /api/v1/tasks
          → TaskRepository.find_all → ~/.task-tracker/tasks.json (empty)
```

**Expected source truth:** `DMS-SPRNT-1` (confirmed by direct MCP-SWTR in Assignment 176)
**Actual result:** `sprint_id=None`, `warnings=["current_sprint_not_found"]`
**Smallest generalized owner fix:** Replace the `search_tasks` call in
`_sprint_current_source_backed` with `self.adapter.get_current_sprint(product)` (or an
equivalent `swtr-read` call), so the handler reads the current sprint from the
authoritative real source rather than the local task file.

---

## Phases 1–7 — NOT EXECUTED

Per assignment instructions: *"если ReliableAgentCoreV4Runtime._sprint_current_source_backed()
фактически получает collection через local cache path, зафиксируй первую точную boundary,
raw call chain и STOP RED согласно assignment. Не предлагай sync и не модифицируй код."*

The defect is confirmed. STOP.

---

## Conclusions

- The V4 skill-native architecture is sound for the key/space/sprint/identity paths
  (all use `swtr-read` endpoints → MCP-SWTR → REAL AS21).
- **`sprint.current` is the sole V4 handler that reads from the local task cache**
  (`/api/v1/tasks` → `~/.task-tracker/tasks.json`) instead of the real source.
- The local file is currently empty, so `sprint.current` will deterministically fail
  for every space.
- This is a **source-adapter wiring defect**, not a planner, skill-loading,
  capability-binding, or safety issue.
- **Not** a semantic-prepass problem (absent), **not** a build/runtime problem
  (Phase 0 GREEN), **not** a safety problem.
- Verdict: **`V4_CURRENT_SPRINT_RED`**

After the owner fix (wire `sprint.current` to the `swtr-read` current-sprint endpoint),
re-run Phases 1–7 in full.