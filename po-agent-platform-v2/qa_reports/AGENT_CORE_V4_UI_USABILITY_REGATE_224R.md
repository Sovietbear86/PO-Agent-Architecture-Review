# A224R — exact space totals + usability re-gate

**Verdict: `AGENT_CORE_V4_UI_USABILITY_RED_A224R`**
Classification: `RED_P1R_COUNT_ROUTE_SOURCE_METADATA_ABSENT`
**STOP** at first confirmed RED (spec: "If source metadata itself is missing/unreliable, RED and stop").

- Test HEAD: `0be969e105c2cb153cd106538efb34eeaa913a9f`
- Prior verdict: A224 = `RED_P2_FULL_SPACE_COUNTS_UNAVAILABLE_PAGINATION_CAP` (report commit `a939c99`)
- Owner remediation under test: `d6993d4` (task-api `/task-count`), `984a601` (adapter `get_space_task_count`), `94c41d3` (plugin isolation), `a2e866f`/`a36a2a8` (Overview UI), `5f49659`/`11fdba5` (tests)
- QA artifacts: `qa_artifacts/a224r_*` (route 502s, direct 403, agent runs, source oracle)
- Stack: MCP 3000 (PID 25954), task-api 8241 (PID 26008, system py3), agent 8212 (PID 26026 @ `0be969e`), logs `/private/tmp/qa224r_{mcp,taskapi,agent}.log`

---

## P0 — diff/build/tests — GREEN

| Check | Result |
|---|---|
| Diff scope `a939c99..0be969e` | 9 files: task-api route (+47), adapter (+20), plugin (+49), 2 frontend, 1 test, 3 docs. **No** core/planner/runtime/session/other-adapter changes |
| Count route shape (static) | one `find_units_by_filter` call, `page=0 size=1`, `space = "X"` predicate, `_ALLOWED_SPACES` guard, returns `{source, route, space, total, status_breakdown_available: false}` — no task rows |
| Adapter MRO | `EvidenceValidated → Hardened → Production` inherit `get_space_task_count`; no overrides; single GET, typed `AS21SourceUnavailable` on 502/503/504 |
| Plugin (static) | per-space `try/except AS21SourceUnavailable` → `SOURCE_UNAVAILABLE` row + continue; `total` int → `SOURCE_BACKED_TOTAL_ONLY` with `active/completed/blocked=None`, `breakdown_state=SOURCE_CONDITIONAL`; all-fail → `V4CapabilityUnavailable`; **no row materialization** (`search_tasks` no longer called) |
| UI (static) | card shows exact `total ?? '—'`; `SOURCE_UNAVAILABLE` → «Источник временно недоступен»; else «Разбивка по статусам пока не подтверждена источником»; no active/completed/blocked rows, no false 0 |
| `test_agent_core_v4_batch5_po.py` | 8/8 passed (incl. new `test_status_report_isolates_one_space_count_failure`) |
| Full V4 regression | 226/226 passed |
| task-api suite | 28F/84P — failure set **byte-identical** to A224 baseline `a939c99` (read-only worktree A/B; all pre-existing/environmental: local-store CRUD, live-service integration, freshness preflight). Zero new failures |
| frontend | `tsc --noEmit` GREEN, `vite build` GREEN (268.8 kB JS) |

## P1R — task-count route exactness — **RED (first failing boundary)**

### Observed

`GET /api/v1/swtr-read/task-count?space=X` → **502 for 5/5 spaces**, deterministic, 180–245 ms each:

```
WMB  502 {"detail":"AS21 task count metadata unavailable for WMB"}   244 ms
DMS  502 {"detail":"AS21 task count metadata unavailable for DMS"}   181 ms
OLP  502 {"detail":"AS21 task count metadata unavailable for OLP"}   183 ms
CRPV 502 {"detail":"AS21 task count metadata unavailable for CRPV"}  197 ms
STS  502 {"detail":"AS21 task count metadata unavailable for STS"}   197 ms
```

Exact total parity: **0/5**. CRPV/STS not merely "slow" — they never return a total at any size.

### Root cause (proven at three levels)

1. **Raw MCP probe** of the route's exact request shape (`find_units_by_filter`, `calculatedAttributes:[]`, `attributes:["code"]`, `page:0 size:1`) — response envelope contains **only** `content/hasNext/pageNumber/pageSize`; **no `totalElements`**. Re-probed with 3 request variants (`calculatedAttributes:null`, full task-query attribute list, size=25): none carries a total.
2. **SWTR API contract** (`mcp-swtr/api-docs.json`): `POST /rest/api/unit/v3/find/tql` is documented as «Постраничный запрос на поиск юнитов с помощью TQL **без вычисления кол-ва записей**» (slice schema `QLResponseDtoSliceV3`, no total). The owner fix's premise — "one-page `totalElements` metadata" from this endpoint — does not exist in the source contract.
3. **MCP passthrough**: `mcp_server.py::find_units_by_filter` returns `response.text` verbatim (no stripping) — the absence is source-side, not MCP-side.

The route correctly fails closed on missing metadata (502, not fabricated 0) — the defect is the endpoint choice, not the guard.

### Proven alternative source path (for the owner fix)

MCP tool `find_units` (v2, `POST /rest/api/unit/v2/find/tql`) **does return `totalElements`** and scopes correctly via its dedicated `spaces` parameter (its `query` field is NOT TQL — a `query:'space = "DMS"'` probe returned tenant-wide rows/total, do not use it):

| space | `totalElements` | first row | latency |
|---|---|---|---|
| DMS | **449** | DMS-442 | 208 ms |
| WMB | **2374** | WMB-26931 | 208 ms |
| OLP | **3220** | OLP-3339 | 208 ms |
| CRPV | **150129** | CRPV-160503 | 208 ms |
| STS | **460452** | STS-542370 | 208 ms |

- Request: `{"request": {"page":0, "size":1, "attributes":["code"], "calculatedAttributes":null, "properties":{}, "spaces":["X"], "timeZone":"Europe/Moscow"}}`
- DMS/WMB/OLP totals are **exact parity** with the A224 full-row-materialization oracle (449/2374/3220), proving same counting universe; CRPV/STS now exact (both >10k, previously unquantifiable).
- Also documented: the dedicated `POST /rest/api/unit/v3/count/tql` (int64, O(1)) exists in the SWTR API but (a) is not exposed as an MCP tool (48 tools enumerated, none count), and (b) returns **403** via direct REST under the current token (RBAC/gateway) — `qa_artifacts/a224r_count_v3_direct_403.json`.

**Minimal owner fix** (task-api only, route body unchanged otherwise): in `count_live_tasks`, replace the `find_units_by_filter` call with the v2 `find_units` tool + `spaces:[normalized_space]` (page 0, size 1), read `totalElements` via the existing `_page_meta`. Keep the `status_breakdown_available=false` contract and all plugin/UI/tests as-is — they are verified correct at unit level and their end-to-end fail-closed path is sound (below). Add a non-mocked regression asserting `totalElements`-derived totals for at least one >10k space (CRPV or STS) so a future slice-vs-page envelope regression cannot pass.

## P2R — po.status_report isolation — partial (safety verified; parity impossible)

Two live agent runs (`"дай статус-репорт по DMS"`, `"статус-репорт по всем продуктам"`):

| Property | Result |
|---|---|
| Terminal state | 2/2 `FAILED` typed: «Необходимая возможность не подтверждена источником данных и не выполняется.» (all-spaces-failed → `V4CapabilityUnavailable`), 28.7 s / 27.4 s |
| Fabrication / false zero | none — `results_n=0`, no `by_space_tasks`, no `by_product` exposed, no 0-rows |
| Boundedness | task-api log: 5 spaces × 3 `_get_resilient` retries = 15 single-page count calls; **0 `task-query` full-space row scans**; only other reads = person-scoped `task-query?assignee=Kalachanov.V.V` (200) + current-sprint routes (200) |
| Per-space isolation | exercised live: loop continued through all 5 failures (CRPV first, A224's failure point, no longer sinks the loop) — but since **all** spaces fail, the all-fail branch fires and the whole report fails closed |
| by_product / A219-A221 compatibility | current-sprint collection executed (CRPV/DMS/OLP/STS/WMB current-sprint + complete sprint tasks, all 200) but discarded with the report — **not verifiable** until at least one space count succeeds |
| Injected single-space failure | not re-testable live (all spaces fail); owner's unit regression `test_status_report_isolates_one_space_count_failure` passes (8/8) |

The isolation/fail-closed machinery is proven; the gate requirement "each SOURCE_READY row has exact total" is unsatisfiable while the route is 0/5.

## P3R–P9R — NOT RUN

Per spec STOP rule (first confirmed RED at P1R). Notes for re-gate:

- P3R (Overview): while the capability fails closed, «Задачи по пространствам» renders the `ResultStatePanel` (typed), not the new exact-total cards — card rendering, «Показаны первые 10 из M», scroll and narrow-viewport checks all pending route fix.
- P4R–P9R (local CRUD, sprint predictability, releases, team, quality aging, retained smoke/audit): deferred to A224R2 unchanged from A224's deferral list.

## Retained safety audit (window of this run)

- 0 AS21 mutations (all GET/POST-read calls)
- 0 local `/api/v1/tasks` reads
- 0 tenant-wide scans (all calls space- or person-scoped)
- 0 fabricated totals / false zeros

## Next

Owner fix per P1R (v2 `find_units` + `spaces` in `/task-count`, non-mocked >10k regression), then A224R2: P1R parity 5/5 (expect exact 449/2374/3220/150129/460452 at run time, drift-tolerant), P2R full (incl. by_product A219/A221 compatibility + injected single-space failure), then P3R–P9R.
