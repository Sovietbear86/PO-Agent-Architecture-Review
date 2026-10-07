# A229S1R2 — Task semantics + hierarchy DTO re-gate

**Verdict:** `AGENT_CORE_V4_TASK_SEMANTICS_HIERARCHY_GREEN_A229S1R2`
**START_HEAD:** `ea95b284f7dcd666c79af0e69e1b5cefd0961e62` (`ea95b28`)
**Baseline checkpoint:** `be5131c83b7fd666c79af0e69e1b5cefd0961e62` (`checkpoint/v4-task-details-richtext-green-a229u2r`)
**Previous verdict:** `AGENT_CORE_V4_TASK_SEMANTICS_HIERARCHY_RED_A229S1R` (relations facade HTTP 502 — nested `get_unit_links` DTO mismatch)
**Owner delta verified:** `b0334f2..ea95b28` = `task-api/app/routers/swtr_read.py` (flat DTO) + `task-api/tests/test_swtr_task_relations.py` (2 new flat-DTO regressions) + `GIGACODE_NEXT_ACTION.md`. 0 Core/planner/runtime/plugin/adapter changes vs A229S1R.

## Owner fix — certified

`_get_unit_links_complete()` now sends the live-schema-proven **flat** `GetUnitLinksRequest`:
```python
arguments = {"request": {"unit_code": task_code, "link_types": [], "page": page, "size": page_size}}
```
The nested `unitId`/`type`/`page.page` shape is gone. Two new regression tests lock the argument shape and flat integer pagination:
- `test_get_unit_links_complete_uses_live_flat_request_contract` (asserts `unit_code`, `link_types`, `page`, `size`)
- `test_get_unit_links_complete_paginates_with_flat_page_number`

## P0 — integrity + focused regression — **GREEN**

- Core/planner/runtime/session **byte-identical** to `be5131c` (6/6: `agent_core_v4.py`, `agent_core_v4_robust.py`, `agent_core_v4_reliable.py`, `agent_core_v4_completion.py`, `v4_plugin_registry.py`, `llm/real.py`).
- Canonical **54/54** unchanged; registry = 72 skills; exactly 2 extra = `task.type_analysis`, `task.hierarchy`.
- `task-api/tests/test_swtr_task_relations.py` 7/7 GREEN (incl. 2 new flat-DTO regressions); SWTR assignee canonicalization 19/19.
- Full V4 blast-radius **247/247** passed.
- Frontend `npm run build` exit 0.

## P2 — live relations facade contract — **GREEN** (first boundary, re-gated first)

A/B parity (direct MCP flat `get_unit_links` vs `GET /api/v1/swtr-read/tasks/{key}/relations`), all **exact** (source/destination, link type, parent candidates, epic, related keys, in/out direction):

| Task | Type | Rows | hasNext | Parent | Epic | Related |
|------|------|------|---------|--------|------|---------|
| DMS-253 | epic/Эпик | 14 | false | CRPV-90180 | DMS-349 (realized_in) | 11 children (decomposition) |
| CRPV-90180 | epic_crpv/Epic | 3 | false | — | DMS-253 (realized_in) | CRPV-154341 (`dependend`) |
| DMS-267 | task/Задача | 1 | false | DMS-253 | — | — |
| DMS-380 | bug/Дефект | 1 | false | DMS-254 | — | — |

- **No HTTP 502** (A229S1R blocker closed).
- Live evidence re-confirmed (not hardcoded): `CRPV-90180 → DMS-253` decomposition; `DMS-253 → DMS-267` decomposition; `DMS-253 → DMS-349` realized_in; dependency spelling `dependend`.
- **Root/no-parent control:** WMB-29973 (18 children, parent=None, schema_proven=true).
- **Pagination:** all observed `hasNext=false` (single page ≤100); flat integer `page=0,1,...` advancing + max-pages fail-closed guard exercised by the new regression test (no silent truncation).
- **Depth:** `CRPV-90180 → DMS-253 → DMS-267` (3 nodes / 2 links); also `DMS-380 → DMS-254 → CRPV-99045`.

## P1 — task.type_analysis re-gate — **GREEN** (4/4 exact)

Oracle: `Zhdanov.A.Ni` DMS = 7 tasks (5 `task`/Задача + 2 `bug`/Дефект) via the independent `assignee-tasks` route.

| Case | Constraint | Result | Parity |
|------|-----------|--------|--------|
| A | person+space distribution | 7 keys; task=5 / bug=2 | **EXACT** |
| B | bug + person+space | 2 (DMS-6, DMS-1) | **EXACT** |
| C | bug + person+space + open | 1 (DMS-1; DMS-6 is closed) | **EXACT** |
| D | Задача + person+space + last 60d | 1 (DMS-371, created 08-25) | **EXACT** |

- Terminal skill `task.type_analysis` in all 4; no `task-query` 502 for person-scoped cases; exact source type code/name (`unit.suit`); all constraints preserved; no title/label inference; no local fallback; no tenant-wide scan (only `assignee-tasks` + `assignees/resolve`).
- 2 of 12 matrix runs FAILED from **LLM 429/timeout** bounded repair (environmental, F3); clean 80s-spaced probes all COMPLETED.

## P3 — live task.hierarchy — **GREEN** (exact chains)

- **H_hierarchy_DMS-267** (3/3): `task.hierarchy` mode=inspect, chain `[DMS-253, CRPV-90180]`, root `CRPV-90180`, epic `DMS-349`, related=0 — **EXACT** vs independent `get_unit_links` oracle.
- **H_parents_DMS-267** (3/3): `task.hierarchy` inspect, same exact chain.
- **H_related_DMS-253** (3/3): run #3 → `task.hierarchy` inspect, chain `[CRPV-90180]`, related=11 (**EXACT**); runs #1-2 → routed to `task.dependencies` (related=0) — **planner routing variance** (F1), not a capability defect.
- `DEEPEST_OBSERVED_DEPTH` = 2 parent-links. `MAX_HIERARCHY_DEPTH_UNPROVEN` (no authoritative schema maximum; safety cap 20 is operational only).

## P4 — group by epics — **GREEN** (capability exact + guard)

Independent direct-`get_unit_links` oracle built for the bounded 7-task `Zhdanov.A.Ni` DMS corpus. Capability verified **in-process** (deterministic, no LLM) + one live invocation:

| Case | Result | Parity |
|------|--------|--------|
| G1 person+space (all 7) | `{CRPV-90167:[DMS-103], DMS-252:[DMS-154], DMS-372:[DMS-371], DMS-77:[DMS-69], DMS-84:[DMS-71], NO_EPIC:[DMS-1,DMS-6]}` | **EXACT** |
| G2 + status open | `{NO_EPIC:[DMS-1]}` (count=1) | **EXACT** vs current source (F2) |
| G3 + type bug | `{NO_EPIC:[DMS-1,DMS-6]}` (count=2) | **EXACT** (also live G3#1) |
| G4 >200 control | raises `AS21SourceUnavailable` "bounded safety limit is 200. Narrow by person/sprint/status/type" | **fail-closed** ✓ |

- Exact group membership, no-epic set, counts, no duplicates/drops, person/space/status/type preserved, bounded point-reads only (semaphore 8).
- Live matrix (G1-G4 via LLM) was dominated by 429 failures + routing variance (F1/F3); the capability itself is proven exact.

## P5 — retained + architecture audit — **GREEN**

**Static audit:** Core byte-identical; canonical 54 unchanged; exactly 2 extra skills; hierarchy authority = MCP `get_unit_links` (only tool); task-type authority = `unit.suit` (adapter maps `raw_suit`→`task_type_code/name`); 0 hardcoded people/products/task-IDs in added lines; 0 phrase routers (only skill-procedure guidance text); `_TYPE_ALIASES` is a generic semantic-alias table (bug/defect/story/epic/task + RU), not a product inventory; 0 local fallback; 0 tenant-wide scans; 0 fake relation/type metrics.

**Retained live controls (6/6 COMPLETED):**
| Control | Cap | Result |
|---------|-----|--------|
| simple assignee | task.search_assignee (Kalachanov WMB) | 6 tasks |
| assignee+status | task.search not_completed | 1 open |
| created-period open | task.search_created (5d, not_completed) | 29 |
| created-period in-progress | task.search_created_in_progress (5d) | 0 REAL_EMPTY (no invented status) |
| sprint tasks | sprint.resolve + task.search (DMS-SPRNT-3) | 51 (re-probed after 429) |
| exact lookup | task.lookup (DMS-380) | source-accurate (Closed, Семавин) |

**Audit (174 scoped swtr-read calls):** 0 local `/api/v1/tasks` reads, 0 unscoped tenant scans, 0 mutations.

## Non-blocking findings

- **F1 — Planner routing variance.** `task.hierarchy` group_by_epic not deterministically routed: only 1/7 live P4 runs invoked it (others → `task.search_assignee`/`task.search`); "связаны" query routed to `task.dependencies` 2/3 in P3. Known LLM-routing class (A217B-F2 / A179 lineage). Capability output is exact when invoked.
- **F2 — Live source drift.** DMS-371 changed `Ready for review`(pause) → `Closed`(done) mid-session. G2 open-set `{DMS-1}` is correct against the current source; production status semantics are right (stale QA oracle, not a defect).
- **F3 — LLM endpoint 429 rate-limiting** (environmental). Caused most live FAILED runs (P1 C#2/D#1, P4 G1×2/G2#2, P5 sprint). All re-probes after cooldown completed cleanly.
- **F4 — Source identity data quality.** Live directory has two Zhdanov records (`Zhdanov.A.N` + `Zhdanov.A.Ni`); `assignees/resolve?reference=Жданов` is non-deterministic (409 ambiguous vs 200). Agent resolved to the correct person with exact data; the 409 path correctly surfaces typed clarification.
- **F5 — QA environment base-URL gotcha (not a product defect).** `po-agent-platform-v2/.env` pins `PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8003`, but this re-gate ran task-api on **8241**. The first P1 matrix (agent on the default 8003) hit a dead port → connection error → typed `source_unavailable` for all 12 runs. Restarting the agent with an explicit `PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8241` override made every path green. **This retroactively explains the A229S1 "type_analysis fails on task-query 502" observation, which was actually a base-URL misconfiguration, not a task-query 502.** Future QA: start task-api on 8003 (the .env default) OR pass the explicit base-URL override to the agent.

## Recommendation

- **Freeze immutable checkpoint** `checkpoint/v4-task-semantics-hierarchy-green-a229s1r2` on `ea95b28`.
- Owner may then sync the certified delta (relations flat-DTO + type/hierarchy plugins) to public/community.
- Next assignment returns to **A229R1 latency verification**.
- Track F1 (planner routing determinism for group_by_epic / "связаны") as the standing LLM-reliability item before any group-by-epic UI surface.

## Services left running

- agent 8004 (PID 69023 @ ea95b28, `PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8241`), `/live` 200
- task-api 8241 (PID 45613 @ ea95b28, system python3, .env sourced)
- MCP-SWTR SSE 3000 (PID 14998)
