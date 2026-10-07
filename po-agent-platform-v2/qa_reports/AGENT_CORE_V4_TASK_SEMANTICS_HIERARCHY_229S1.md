# Assignment A229S1 — Task Type + Hierarchy Plugin Gate

**Verdict:** `AGENT_CORE_V4_TASK_SEMANTICS_HIERARCHY_RED_A229S1`  
**Classification:** RED_P2_RELATIONS_FACADE_WRONG_SOURCE  
**START_HEAD:** `00c6064d19ab5f1cec58b31f360a11f158df0a20`  
**Certified checkpoint:** `be5131c83b7fd666c79af0e69e1b5cefd0961e62`  
**Date:** 2026-10-07

---

## P0 — Integrity / Build / Focused Regressions — **GREEN**

| Check | Result |
|-------|--------|
| Core byte identity vs checkpoint | ✅ 4/4 files (agent_core_v4.py, robust, reliable, completion, plugin_registry) zero diff |
| Canonical 54 | ✅ 54/54 unchanged; 2 new skills (`task.type_analysis`, `task.hierarchy`) are extra, not canonical |
| Registry total | 72 skills (54 canonical + 18 extras including 2 new) |
| Focused tests | 33 passed, 1 failed (test-logic), 16 task-api passed |
| Full V4 blast | 246 passed, 1 failed (same test) |
| Frontend build | ✅ exit 0 |
| Core/planner changes | ✅ 0 (plugin/adapter only: 5 files, +644/-2) |

**Single test failure (non-blocking):**  
`test_task_semantics_hierarchy_skills_are_extra_plugin_skills_not_canonical54_rows` asserts `"10 hierarchy levels" not in procedure_text`. The procedure correctly states "Never assume that AS21 has exactly 10 hierarchy levels" — the naive substring match catches the phrase in negation context. Production code is correct: `max_depth: int = 20` (safety cap), `max_depth_assumption: None`.

---

## P1 — REAL AS21 Task-Type Source Contract — **PARTIALLY VERIFIED**

### Source Discovery (MCP-direct)

| Task | unit.suit.code | unit.suit.name |
|------|---------------|----------------|
| DMS-380 | `bug` | `Дефект` |
| DMS-253 | `epic` | `Эпик` |
| DMS-379, DMS-355, DMS-104 (16 tasks) | `task` | `Задача` |
| WMB-29995, WMB-30000 (4 tasks) | `task_wmb_v3` | `Task (Управленческие задачи)` |

**Conclusions:**
1. ✅ `unit.suit` IS the authoritative task-type field (present at unit top level, confirmed by raw read_unit)
2. Type inventory observed: `bug/Дефект`, `epic/Эпик`, `task/Задача`, `task_wmb_v3/Task (Управленческие задачи)`
3. Story type NOT observed in bounded sample (DMS + WMB) — recorded as corpus evidence
4. `find_units_by_filter` rows include suit (confirmed via task-api assignee-tasks route: `task_type_code` + `task_type_name` + `source_data.swtr_suit` all present)

### Agent Live Test

- `task.type_analysis` capability loaded correctly (trajectory proves: turn 1 load_skill, turn 2 call with `reference=Калачанов, space=DMS`)
- **Live execution FAILED** with `source_unavailable` — the `_bounded_composable_tasks` path uses task-query which 502s on DMS (pre-existing A227/A229 lineage: full-space scan timeout)
- The assignee-tasks route (which `_live_query` should ideally use for person+space) returns `task_type_code`/`task_type_name` correctly (verified: Zhdanov DMS 7/7 tasks carry type)
- **Classification:** Not a new defect — pre-existing task-query unscoped scan limitation. The type_analysis handler architecture is correct; the data plumbing is sound.

---

## P2 — REAL AS21 Hierarchy/Relation Source Discovery — **RED (BLOCKING)**

### D-A229S1-1: Relations Facade Uses Wrong Data Source

**Root cause proven:**

The owner's `GET /api/v1/swtr-read/tasks/{key}/relations` route (swtr_read.py:716) calls `_task_relation_facts(unit)` (swtr_read.py:228) which:
1. Scans top-level unit fields (excluding "attributes") for names matching relation keywords
2. Scans unit attribute codes for names matching relation keywords
3. Extracts task codes from matching field values

**The real source does NOT put relations in unit attributes.** Relations exist ONLY in a separate API:
- **MCP tool:** `get_unit_links`  
- **REST endpoint:** `POST /rest/api/unit/v1/link/find`  
- **Request:** `{"type": [], "unitId": "<code>", "page": {"page": {"page": 0, "size": 50}}}`  
- **Response shape:** `{"content": [{"source": "<code>", "destination": "<code>", "type": "<link_type>", "deleted": false}], "pageSize": N, "hasNext": bool, "pageNumber": N, "totalElements": N}`

**Evidence (live, MCP-direct):**

DMS-253 (Epic "Создание MCP-сервера DataMarts") has **14 real links:**

| source | destination | type |
|--------|------------|------|
| DMS-253 | DMS-453 | `decomposition` |
| DMS-253 | DMS-349 | `realized_in` |
| DMS-253 | DMS-403 | `decomposition` |
| DMS-253 | DMS-331 | `decomposition` |
| CRPV-90180 | DMS-253 | `realized_in` |
| DMS-253 | DMS-348 | `decomposition` |
| DMS-253 | DMS-337 | `decomposition` |
| DMS-253 | DMS-336 | `decomposition` |
| DMS-253 | DMS-275 | `decomposition` |
| DMS-253 | DMS-267 | `decomposition` |
| DMS-253 | DMS-266 | `decomposition` |
| DMS-253 | DMS-265 | `decomposition` |
| DMS-253 | DMS-264 | `decomposition` |
| CRPV-90180 | DMS-253 | `decomposition` |

**Owner's relations route returns for DMS-253:**
```json
{
  "parent_key": null,
  "parent_candidates": [],
  "epic_key": null,
  "epic_candidates": [],
  "related_keys": [],
  "relations": [],
  "source_fields_seen": ["attribute:external_link", "attribute:epic_type_soc"]
}
```
→ All empty. The `external_link` field matched "link" keyword but its value is `null`.

**CRPV-90180 links (proving parent chain):**
- CRPV-90180 → DMS-253 (`decomposition`) — DMS-253 is a CHILD of CRPV-90180
- CRPV-90180 → DMS-253 (`realized_in`)
- CRPV-90180 → CRPV-154341 (`dependend`) — dependency

**Leaf verification (DMS-267, child of DMS-253):**
- DMS-267's only link: `DMS-253 → DMS-267 (decomposition)` — confirms no further children

### Link Type Semantics (source-observed)

| type | Meaning | Direction |
|------|---------|-----------|
| `decomposition` | Parent decomposes into child | source = parent, destination = child |
| `realized_in` | Task realized in epic/parent | source = task, destination = epic |
| `dependend` | Dependency (source typo: "dependend" not "dependent") | source → destination |

### Hierarchy Depth

- **DEEPEST_OBSERVED_DEPTH = 3** (CRPV-90180 → DMS-253 → DMS-267)
- **AUTHORITATIVE_MAX_DEPTH = MAX_HIERARCHY_DEPTH_UNPROVEN** (no schema/metadata/validation constraint found in MCP tool definition or source documentation)
- Production safety cap in code: `max_depth: int = 20` (operational guard, correctly not presented as business maximum)

### Unit Attribute Scan Result

All 35 attributes of DMS-253 (Epic) checked. NO attribute contains parent/child/epic/related task keys. The fields present are: assigned_to, estimate, watchers, story_points, due_date, sprint, workflow_status, label, rank, resolution, affects_version, fix_version, external_issue_ID, component, external_link (null), contract, epic_type_soc, priority, reporter, client, etc.

### WMB Verification

WMB-29995, WMB-30000, WMB-29890, WMB-30001: relations route returns empty `source_fields_seen: []` (no relation-like fields in unit payload at all).

### Classification

The real relation field **exists** (in `get_unit_links` / POST `/rest/api/unit/v1/link/find`) but the owner parser does not use it. The parser (`_task_relation_facts`) only inspects `read_unit` unit fields/attributes, which NEVER contain relation data in the AS21 source.

**Owner fix needed:** The `swtr_read.py` relations route must call `get_unit_links` (via the existing SWTRMCPClient) and parse the `content[].source/destination/type` rows into the canonical parent/epic/related structure. The current field-name heuristic on `read_unit` is architecturally incapable of finding real relations.

### P2 Verdict: RED STOP

Per spec: "If the real relation field exists but the owner parser does not recognize it, classify the exact missing field and RED STOP."

**Missing source:** `get_unit_links` tool (POST `/rest/api/unit/v1/link/find`) — the ONLY source for parent/epic/linked relations.

---

## P3 — Exact Parent/Related-Task Skill — **NOT RUN (STOP at P2 RED)**

## P4 — Group by Epics — **NOT RUN (STOP at P2 RED)**

## P5 — Architecture Audit — **PARTIAL**

Items verifiable before P2 RED:
- ✅ Canonical 54 unchanged
- ✅ Exactly 2 extra skills added (`task.type_analysis`, `task.hierarchy`)
- ✅ 0 Agent Core/planner/runtime/session changes
- ✅ Task type authority = REAL AS21 `unit.suit` (confirmed in source + adapter)
- ✅ No fixed list limiting valid source types (handler reads from source, no hardcoded type list)
- ❌ Hierarchy authority: code claims "REAL AS21 point reads" but uses wrong source (`read_unit` fields instead of `get_unit_links`)
- ✅ 0 phrase-specific routing
- ✅ 0 person/product/task-key hardcodes
- ❌ No fake relations — but the relations facade returns empty (not fake, just wrong source)
- ✅ No tenant-wide scans in new code
- ✅ Hierarchy traversal safety cap 20 (not presented as AS21 business maximum)
- ✅ Public/community repo not updated

---

## P6 — Retained Regression — **NOT RUN (STOP at P2 RED)**

---

## Services Left Running

| Service | Port | PID |
|---------|------|-----|
| MCP-SWTR | 3000 | 14998 |
| task-api | 8241 | 16048 |
| agent (V4 enabled) | 8004 | 16338 |

---

## Owner Fix Recommendation

1. **Primary (P2 RED):** In `swtr_read.py`, the `get_task_relations` route must call `SWTRMCPClient.call_tool("get_unit_links", {"request": {"unit_code": code, "link_types": [], "page": 0, "size": 100}})` and parse the returned `content[]` rows:
   - `type == "decomposition"`: source→destination means source is parent of destination
   - `type == "realized_in"`: source is realized in destination (destination is epic/parent)
   - Other types: treat as `related`
   - Build `parent_key`, `epic_key`, `related_keys` from the parsed links
   - Keep the existing `read_unit` scan as a secondary signal (for cases where unit attributes DO carry link info in other spaces)

2. **Non-blocking (P1):** The `task.type_analysis` handler's `_bounded_composable_tasks` uses `_live_query` which hits the 502-prone task-query route for person+space. Consider routing through the already-working `assignee-tasks` route when a resolved person + space is available (precedent from A227R2/A229F2R2).

3. **Test fix:** The failing test (`test_task_semantics_hierarchy_skills_are_extra_plugin_skills_not_canonical54_rows`) uses naive substring matching that catches "10 hierarchy levels" inside "Never assume that AS21 has exactly 10 hierarchy levels". Fix: assert the phrase is not present as a POSITIVE claim (e.g., check that the text doesn't say "AS21 has 10 levels" without the "Never assume" negation), or simply check that "exactly 10" is not stated as a fact.
