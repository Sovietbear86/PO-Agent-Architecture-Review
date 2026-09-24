# AGENT_CORE_V4_RELEASE_SOURCE_DIAGNOSTIC_211

**Assignment:** 211 — Release search / release health diagnostic (no code changes)
**Date:** 2026-09-24
**Role:** QA/adversarial diagnostic only (no production/test/config edits)
**Branch:** `feat/core8-real-query-hardening-v2`

| Field | Value |
|---|---|
| START_HEAD | `bdea0433e8c36dc6f54252438e74491fa77dd260` (docs-only over A210) |
| A210 GREEN baseline | `0ac5b98` (report) / `316d367` (code) |
| Agent under test | port 8212, HEAD `316d367` (code unchanged by A211) |
| task-api | 8241, system python3, SSE, 48 tools |
| MCP-SWTR | 3000 |
| Note | Spec references checkpoint `v4-wave-s2-green-a210`; no such tag exists in the repo (the A210 GREEN is commit `0ac5b98`). Recorded, not blocking. |

## VERDICT

**RELEASE_SOURCE_READY_FOR_OWNER_FIX**

The live MCP-SWTR `search_versions` source is **healthy and returns real release data** (WMB=3, OLP=1, STS=11004; DMS genuinely 0). The agent correctly fails closed on every natural-language release query (typed `source_unavailable`, zero fabrication). The block is **entirely in our Task API `/api/v1/swtr-read/versions` facade**, which fails to call the tool correctly. The first failing boundary is a single, bounded, owner-side fix in the task-api route; no agent/planner/core change is needed.

---

## S1 — Live `search_versions` schema (MCP descriptor = source of truth)

`tool_input_schema("search_versions")`:

```
{ "type":"object", "required":["request"], "additionalProperties":false,
  "properties": { "request": {
      "type":"object", "required":["calculatedAttributes","space"],
      "properties": {
        "space":   {type:string},
        "calculatedAttributes": {anyOf:[{type:array,items:string},{type:null}]},   // REQUIRED
        "query":   {type:string, default:""},          // TQL filter
        "page":    {type:integer, default:0},
        "size":    {type:integer, default:25},
        "attributes": {type:array, default:["code","summary","priority","assigned_to"]},
        "withArchived": {type:boolean, default:false},
        "withDeleted":  {type:boolean, default:false} } } } }
```

Key fact: the nested `request` **requires `calculatedAttributes`** (a nullable array) in addition to `space`.

## S2 — Direct source calls (MCP client, exact request → exact result)

| # | arguments | result |
|---|---|---|
| 1 | `{"request":{"space":"DMS"}}` (no calculatedAttributes) | **ToolError** (`SWTRMCPProtocolError: MCP-SWTR tool 'search_versions' failed: ToolError`) |
| 2 | `{"request":{"space":"DMS","calculatedAttributes":None}}` | **200** `{"content":[],"pageSize":25,"hasNext":false,"pageNumber":0,"totalElements":0}` |
| 3 | `{"request":{"space":"DMS","calculatedAttributes":None,"query":'code = "DMS-2.5"'}}` | **200** `totalElements:0` |
| 4 | `{"space":"DMS"}` (flat, not nested) | **ToolError** |
| 5 | WMB (`calculatedAttributes:None`) | **200** `totalElements:3` — e.g. `{"code":"7a84006f-…","name":"24Q1"}` |
| 6 | OLP | **200** `totalElements:1` |
| 7 | STS | **200** `totalElements:11004` |
| 8 | DMS `withArchived:true, withDeleted:true` | **200** `totalElements:0` |
| 9 | sanity `search_sprints(space=DMS)` | **200** DMS-SPRNT-3 (server healthy) |

Conclusion: the tool works. The **only** difference between the failing (#1) and succeeding (#2) calls is the presence of the required `calculatedAttributes` field. DMS has **no** releases in the version catalog (even archived/deleted) — a source data fact, not a fault.

## S3 — Direct source vs `/api/v1/swtr-read/versions`

| Request | Result |
|---|---|
| `GET /versions?space=DMS` | **502** `{"detail":"MCP-SWTR tool 'search_versions' failed: ToolError"}` |
| `GET /versions?space=DMS&query=2.5` | **502** (same ToolError) |
| `GET /versions` (no space) | **400** `{"detail":"space is required for search_versions"}` (intentional local fast-fail in `main.py` middleware — by design) |
| Direct MCP, same `space=DMS`, **with** `calculatedAttributes` | **200** |

The route and the direct call differ by exactly one field. **First failing boundary (D1):** the route's `_schema_aware_search_versions_arguments` (`task-api/app/routers/swtr_read.py:462`) builds `request` from declared aliases `query/space/page/limit/offset` and **never emits the required `calculatedAttributes`**. Its helper `_put_declared` (`swtr_read.py:372`) also returns early on `None`, so it cannot inject the field as-is. Result: every route call sends an incomplete `request` → MCP `ToolError` → HTTP 502.

## S4 — Task API output vs the production `release.search` adapter

Chain: agent `release.search` (`v4_plugins/wave_s1.py:272`) → `runtime.adapter.search_versions_bounded(query, space)` (`adapters/hardened_production_task_api.py:246`) → `GET /api/v1/swtr-read/versions?limit=100[&query&space]` → 502 → `AS21SourceUnavailable` → release.search fails closed.

The agent sends correct, bounded, space-scoped requests (agent log: `GET …/versions?limit=100&space=DMS` → 502). The adapter maps `_version_row(id|code|version|name, name, status)`.

**Second (latent) boundary (D2):** even after D1 is fixed, the route returns the **whole tool envelope** as `versions`:
```
# route returns
{"versions": {"content":[…], "pageSize":25, "hasNext":false, "pageNumber":0, "totalElements":0}}
```
`_parse_tool_content` (`swtr_read.py:80`) returns the parsed JSON object verbatim, and the route assigns it to `versions` (`swtr_read.py:874`). But `search_versions_bounded` (`hardened_production_task_api.py:276`) requires `isinstance(payload.get("versions"), list)` and otherwise raises `AS21SourceError("…malformed payload")`. So the route must **unwrap `content` into a list** (and surface `totalElements/hasNext`) for the agent to consume it. D2 is behind D1 and would surface immediately after D1 is fixed.

Both D1 and D2 are small, bounded, task-api-only fixes. The agent side is already correct and fail-closed.

## S5 — Natural-language release search via the agent (source works → tested)

All three fail closed with a typed `source_unavailable` warning and the anti-fabrication answer "Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат." — **zero fabricated releases**, even though the live source has data:

| Query | status | warnings |
|---|---|---|
| `релизы WMB` | FAILED | `source_unavailable` |
| `релизы в DMS` | FAILED | `source_unavailable` |
| `релизы OLP` | FAILED | `source_unavailable` |

The agent log shows bounded space-scoped `/versions` calls all returning 502 — confirming the boundary is the task-api route, not the agent or the source.

## S6 — release.health inventory

- **Skill/capability:** `release.health` is a V4 skill (`v4_plugins/core.py:95`) with procedure `space.resolve → release.search(require_single=true) → release.resolve → release.health`; completion contract `data_keys=("release_id","total")`; UIContract `release_health`. Its prerequisite, `release.search`, is currently blocked by D1/D2 — so release.health cannot be reached end-to-end today.
- **Current implementation:** legacy bridge `runtime.release_health` (`harness/runtime.py:119`) → `adapter.get_release_tasks(release_id)` → `TaskApiAS21Adapter.get_release_tasks` (`adapters/task_api.py:506`) → `search_tasks("release = <id>")` → production override (`hardened_production_task_api.py:375`) with no `project`/`sprint` → **full-tenant task-query scan** (`super().search_tasks(..., _scan_limit)`). This is the A204 "release-only = full tenant scan timeout" path — release.health is not space-scoped.
- **Live release-membership / task-by-release path (available, bounded):** `GET /api/v1/swtr-read/task-query?release=<id>&space=<space>` builds TQL `fix_version_s = "<id>"` (`app/routers/swtr_query.py:63`). This is the correct bounded building block for release.health.
- **Linkage finding (owner data item):** the version catalog identifies releases by **UUID `code`** (e.g. `7a84006f-…`), but a DMS task's raw attributes expose `fix_version`/`affects_version` (DMS-399: `fix_version` value `[]`), and the task-query release filter matches on `fix_version_s`. Live probe `task-query?release=<WMB-UUID>&space=WMB` → **200, 0 tasks**. So the release-id → task linkage is not currently resolvable by the UUID; the owner must confirm the actual identifier stored on tasks (name vs UUID vs `fix_version_s`) before release.health can compute a real denominator.

## S7 — Minimal retained regression + audit

| Check | Result |
|---|---|
| One Wave S2 metric — `cycle time спринта DMS-SPRNT-3` | COMPLETED (`sprint.resolve → sprint.cycle_time`), 32.4 s |
| `sprint.health` (DMS-SPRNT-3) | COMPLETED, 68 tasks |
| `task.lookup` DMS-380 | COMPLETED |
| person+status `Открытые задачи Жданова в DMS` | COMPLETED, `[DMS-371, DMS-1]` |
| dummy-55 plugin invariant (`pytest -k dummy_55`) | 1 passed |
| Local factual `GET /api/v1/tasks` reads (A211 segment) | **0** |
| Local `POST /api/v1/query` reads | **0** |
| Tenant-wide `swtr-read/tasks?` scans | **0** |
| `/versions` calls in A211 segment | 9, all 502 (the release.search boundary) |

No regression from A210 GREEN.

---

## First failing boundary & smallest owner fix

**First failing boundary (D1):** `task-api/app/routers/swtr_read.py` — `_schema_aware_search_versions_arguments` does not send the schema-required `calculatedAttributes` field, so the live MCP `search_versions` rejects the request (`ToolError`) and the route returns 502.

**Smallest owner fix (task-api only, no agent change):**
1. In `_schema_aware_search_versions_arguments`, emit the required field when it is declared in the live schema — in both the nested-`request` and flat branches:
   ```python
   if "calculatedAttributes" in nested_props and "calculatedAttributes" not in request:
       request["calculatedAttributes"] = None
   ```
   (and the equivalent against `top` in the flat branch). Note `_put_declared` skips `None`, so this must be set explicitly, not via the alias helper.
2. In the `GET /versions` handler (fixes latent D2), unwrap the tool envelope into a list the agent expects:
   ```python
   payload = _parse_tool_content(content)
   rows = payload.get("content", []) if isinstance(payload, dict) else (payload if isinstance(payload, list) else [])
   if not isinstance(rows, list):
       raise HTTPException(502, "search_versions content is not a list")
   return {"query":…, "space":…, "page":…, "limit":…,
           "versions": rows,
           "total_elements": payload.get("totalElements") if isinstance(payload, dict) else None,
           "has_next": payload.get("hasNext") if isinstance(payload, dict) else None}
   ```
3. Add a regression test that (a) asserts the built `request` includes `calculatedAttributes` when the schema declares it, and (b) feeds a canned envelope `{"content":[…],"totalElements":n}` through `/versions` and asserts `versions` is a list.

**Secondary owner items (do not gate the search fix):**
- release.health is not space-scoped (full-tenant scan, A204 timeout lineage); route it through the bounded `task-query?release=&space=` facade.
- Confirm the release-id → task identifier linkage (UUID `code` vs name vs `fix_version_s`) so `task-query?release=` returns real membership; without it release.health's denominator is unresolvable.
- DMS has no releases in the version catalog (0 even archived/deleted) — a source data fact for the product, not a code defect.

## Non-observations
- `search_versions` tool present (health `search_versions:true`); transport SSE healthy.
- No local factual reads, no tenant-wide scans, no fabricated releases during the diagnostic.

## Services left running
UI 5175 (55236) / 5176 (12824), agent 8212 (79214 @ `316d367`), task-api 8241 (79196, system python3, SSE 48 tools), MCP-SWTR 3000 (29268).
