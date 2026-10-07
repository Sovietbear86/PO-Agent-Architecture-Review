# Assignment A229S1R — Task Semantics + Hierarchy Owner-Fix Re-gate

**Verdict:** `AGENT_CORE_V4_TASK_SEMANTICS_HIERARCHY_RED_A229S1R`
**Classification:** RED_P2_GET_UNIT_LINKS_DTO_MISMATCH
**START_HEAD:** `56024b94187c11121d7efc4d20d903f924ffafba`
**Previous verdict:** `AGENT_CORE_V4_TASK_SEMANTICS_HIERARCHY_RED_A229S1` (commit 0136125)
**Date:** 2026-10-07

Stopped at the first product RED (P2). P1, P3, P4, P5 not executed per stop rule.

---

## P0 — Integrity / Regression — **GREEN**

| Check | Result |
|-------|--------|
| Core/planner/runtime/session byte identity vs `checkpoint/v4-task-details-richtext-green-a229u2r` (be5131c) | ✅ 6/6 zero diff (agent_core_v4, robust, reliable, completion, plugin_registry, llm/real) |
| Canonical 54 | ✅ 54/54; registry 72 (54 canonical + 18 extra); both new skills present and extra |
| Focused V4 tests (task_catalog + semantics_hierarchy + adapter) | ✅ 34/34 (A229S1 test-logic false positive fixed by owner) |
| task-api focused (swtr_assignee_canonical + task_relations) | ✅ 17/17 |
| Full V4 blast | ✅ 247/247 |
| Frontend build | ✅ exit 0 |
| Delta scope | plugin handler + task-api routers + adapter/models only; 0 core files |

Owner's A229S1 item 3 (false-positive unit test) verified fixed: the "10 hierarchy levels" substring test no longer fails; no production rule of 10 was introduced (safety cap remains 20).

---

## P2 — Relations Facade Re-gate — **RED (BLOCKING, first boundary)**

### D-A229S1R-1: `_get_unit_links_complete` sends a DTO that the live `get_unit_links` tool rejects

**Symptom:** `GET /api/v1/swtr-read/tasks/{key}/relations` returns **HTTP 502** for real tasks (verified live on DMS-253).

**A/B probe (same live MCP, same task, back-to-back) — `qa_229s1r_p2_abprobe.py`:**

```
A (flat): OK, rows=14, total=14
B (owner nested): FAILED SWTRMCPProtocolError: MCP-SWTR tool 'get_unit_links' failed: ToolError
```

- **Shape A (works):** `{"request": {"unit_code": "DMS-253", "link_types": [], "page": 0, "size": 100}}`
- **Shape B (owner's `swtr_read.py:_get_unit_links_complete`):** `{"request": {"type": [], "unitId": "DMS-253", "page": {"page": {"page": 0, "size": 100}}}}`

**Root cause:** the MCP-SWTR `get_unit_links` tool takes a `GetUnitLinksRequest` dataclass (`mcp-swtr/models/unit.py:59`) with fields **`unit_code: str`, `link_types: List[str]`, `page: int`, `size: int`** (from `BasePageSizeRequest`, `models/common.py:24`). The owner's request DTO uses `unitId` (not a field), a nested `page: {page: {page, size}}` structure (collides with the flat `page: int` field), and omits `link_types`/`unit_code`. FastMCP parameter validation raises `ToolError` → `SWTRMCPProtocolError` → route 502.

**Why tests didn't catch it:** the owner's new tests (`test_swtr_task_relations.py`, 4 tests) exercise only the pure `_task_link_facts(rows)` parser with hand-built rows. No test drives `_get_unit_links_complete` — or the route — through a mock MCP that validates the `get_unit_links` arguments against the real `GetUnitLinksRequest` schema. The live-proven DTO from A229S1 (shape A) was not carried into the production request builder.

**What IS proven correct (at unit level, pre-RED):**
- `_task_link_facts` semantics match the A229S1 source contract: `decomposition` source=parent/destination=child; `realized_in` source→destination=epic; other types (incl. source spelling `dependend`) → related; structural nodes excluded from generic related set; `deleted` rows skipped; empty complete response → `schema_proven=True` (proven empty, not unknown).
- Pagination loop with `hasNext` + `max_pages=20` fails closed (HTTP 502) rather than returning a partial set.
- `read_unit` used only for `suit` (task type), no longer as relation authority; response adds `relation_source: "mcp:get_unit_links"`.

**Owner fix (minimal):** in `_get_unit_links_complete` (task-api/app/routers/swtr_read.py) send the flat live-proven DTO:

```python
arguments = {
    "request": {
        "unit_code": task_code,
        "link_types": [],
        "page": page,
        "size": page_size,
    }
}
```

+ a non-mocked regression that asserts the `get_unit_links` arguments equal that shape (e.g. a fake `SWTRMCPClient.call_tool` recording `arguments`, or a unit that constructs the real `GetUnitLinksRequest(**arguments["request"])` and asserts it validates).

### Parity matrix NOT executable

Because the route 502s before returning any facts, the required parity on `DMS-253` / `CRPV-90180` / `DMS-267` (source/destination, link type, parent/epic/related candidates, direction) and the root/no-parent control could not be produced. The direct MCP oracle side remains available: DMS-253 = 14 rows total (14, hasNext=false) — same as A229S1; expected structural facts: parent `CRPV-90180` (incoming decomposition), children in related set `{DMS-453, DMS-403, DMS-331, DMS-348, DMS-337, DMS-336, DMS-275, DMS-267, DMS-266, DMS-265, DMS-264}`, related `CRPV-154341` via `dependend` (on CRPV-90180's own links); DMS-267 single incoming decomposition from DMS-253 (leaf).

### Pagination

The guard logic (fail closed on `hasNext` after max_pages) is present in code but unreachable while the request DTO is rejected. Re-verify after fix.

---

## P1 — task.type_analysis re-gate — **NOT RUN (STOP)**

Code review note (non-judgmental, for the next gate): `_bounded_composable_tasks` now routes person-scoped queries through `_live_assignee_rows` → `GET /api/v1/swtr-read/assignee-tasks?assignee=&space=&limit=100&max_pages=100` (cap 10,000 rows), with status/type/period/phrase applied client-side; non-person scopes keep the bounded `_live_query` path. Space-only scopes still use the task-query route (no change).

## P3 / P4 / P5 — **NOT RUN (STOP)**

---

## Services left running

| Service | Port | PID | Notes |
|---------|------|-----|-------|
| MCP-SWTR | 3000 | 14998 | reused from A229S1 (unchanged code) |
| task-api | 8241 | 39170 | restarted on 56024b9 |
| agent (V4) | 8004 | 39343 | restarted on 56024b9, /live 200 |

QA probes: `qa_229s1r_p2_oracle.py` (parity runner, ready for re-gate), `qa_229s1r_p2_abprobe.py` (A/B DTO proof); oracle dump `/private/tmp/qa229s1r_p2_oracle.json` partial (A-side only).

**Recommendation:** owner fixes the `get_unit_links` request DTO (flat shape) + adds an argument-shape regression, then full A229S1R re-gate from P0 (P0 already certified GREEN at this HEAD — only the route + regression need re-checking, then P1→P5).
