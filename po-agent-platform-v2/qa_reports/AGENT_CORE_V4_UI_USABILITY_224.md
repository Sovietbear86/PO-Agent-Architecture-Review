# A224 — UI Usability & Data Corrections Gate

**Verdict: `RED_A224`** (classification: `RED_P2_FULL_SPACE_COUNTS_UNAVAILABLE_PAGINATION_CAP`)

- **START_HEAD:** `e0f435d` (checkpoint/v4-ui-state-lineage-green-a223r2)
- **Test HEAD:** `99085d9709fbd943db0694f0aa0a01206d9893ea`
- **Date:** 2026-09-27
- **STOP rule:** first confirmed failing boundary = P2 (blocking) → P3–P8 NOT RUN, per spec.

---

## P0 — Static, tests, build, architecture: GREEN (10/10)

| # | Check | Result |
|---|-------|--------|
| 1 | Diff scope | 10 files: 1 backend plugin (`wave_batch5_po.py` +30), 1 test (+23), 5 frontend (`OverviewDashboard.tsx` +36, `Pages.tsx` +74, `QualityDashboard.tsx` +11, `TeamDashboard.tsx` +35, `OverviewDashboard.css` +1), 3 docs. **No core/planner/runtime/session/adapter/task-api changes.** |
| 2 | Backend change is a single plugin extension | `build_po_status_report` adds `by_space_tasks` via new `_space_task_summary(runtime)` (wave_batch5_po.py:95, called at :261). Only usage site in `src/`. |
| 3 | No tenant-wide scan | `_space_task_summary` calls `adapter.search_tasks(f'project = "{space}"', max_results=10000)` per space in `sorted(APPROVED_PRODUCT_SPACES)` = [CRPV, DMS, OLP, STS, WMB]. Adapter project-only path (hardened_production_task_api.py:404 → production_task_api.py:154) **always sends `space=X`** to `/api/v1/swtr-read/task-query`. Bounded per-project full-space reads only. |
| 4 | No AS21/SWTR mutations | Backend diff is read-only; frontend diff adds **only** `localStorage` reads for local tasks (`po-local-tasks`). No fetch/POST to non-local endpoints in the diff. |
| 5 | Python V4 suites | `pytest tests/ -q -k v4` → **225 passed**, 0 failed (1.71s). |
| 6 | Batch5 PO tests | `tests/test_agent_core_v4_batch5_po.py` → **7 passed** (0.34s). |
| 7 | Frontend types | `tsc --noEmit` → GREEN. |
| 8 | Frontend build | `vite build` → GREEN (268.9 kB JS / 32.9 kB CSS). |
| 9 | Agent on test HEAD | Fresh agent on 127.0.0.1:8212 @ `99085d9`, `/live` 200. |
| 10 | Fresh vite on test HEAD | Restarted on [::1]:5175 (PID 18675); old A223R2 vite killed first. |

---

## P2 (BLOCKING) — Full-space task counts: **RED — D-A224-1**

### Spec requirement
`po.status_report.by_space_tasks` must return **exact parity with a fresh independent Oracle B scan** of `WMB`, `DMS`, `OLP`, `CRPV`, `STS` (total / active / completed / blocked per space); UI block «Задачи по пространствам» must render the same data; reads must be scoped full-space (no tenant-wide).

### Root cause (proven, deterministic)

**The task-query route has a hard pagination cap: `max_pages: int = Query(100, ge=1, le=500)` with `limit=100` default → 10,000-row ceiling** (`task-api/app/routers/swtr_query.py:123`, overflow → `HTTPException(502, "AS21 task query pagination exceeded max_pages for {space}")` at :113).

Independent Oracle B probe of all 5 spaces (route `GET /api/v1/swtr-read/task-query?limit=100&max_pages=100&space=X`):

| Space | Route result | Latency |
|-------|-------------|---------|
| WMB | **2374 tasks** (complete) | 15.7s |
| DMS | **449 tasks** (complete) | 2.2s |
| OLP | **3220 tasks** (complete) | 14.1s |
| CRPV | **502 "pagination exceeded max_pages"** (>10 000 tasks) | — |
| STS | **502 "pagination exceeded max_pages"** (>10 000 tasks; even `max_pages=300` → ES 400 search error, index too large for that fetch-size strategy) | — |

**2 of 5 approved spaces are structurally impossible to count via this route.**

### Live agent proof (259.5s, fail-closed, no fabrication)

`POST /api/v1/query {"query": "дай статус-репорт по DMS"}`:
- Result: `answer = "Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат."` — typed source-unavailable. **No `results`, no `by_space_tasks`, no partial by-product data returned.**
- task-api log (lines 14891→14913): exactly 3× `GET /api/v1/swtr-read/task-query?limit=100&max_pages=100&space=CRPV → 502` (attempts 18:25:16 / 18:29:36 / 18:31:01), all other calls 200. **CRPV is first in `sorted()` order → the loop dies on the first space before DMS/OLP/STS/WMB are even attempted.**
- Artifact: `/private/tmp/qa224_p2_probe.json`.

### Defect D-A224-1 (owner, backend)

`_space_task_summary` (wave_batch5_po.py:95):
1. **No per-space error isolation** — one space's `AS21SourceUnavailable` raises through the whole `po.status_report` → the entire status report (including the previously-correct `by_product`, active/blocked aggregates) becomes unavailable. Regression vs A219/A221 parity where `po.status_report` was 9/9 exact.
2. **The counting strategy is unsound for the real source** — row-fetch-then-count via a route capped at 10 000 rows cannot count CRPV/STS, so even with per-space isolation the result can never reach the spec's 5-space exact parity.

### UI consequence (second defect, same boundary)

Playwright on Overview (`http://[::1]:5175/`, 1440×900, 45s settle): the «Задачи по пространствам» block renders

```
Задачи по пространствам
0
Источник недоступен
Источник временно недоступен. Нули не подставляются.
```

i.e. it prints a **false zero ("0")** next to the typed-unavailable text — this is the same class the A223/A223R2 lineage explicitly forbids («нет ложных нулей, — / typed state»). The "0" contradicts the adjacent «Нули не подставляются» message. Non-blocking in isolation, but part of the same failing boundary.

### Why owner unit tests pass
`test_agent_core_v4_batch5_po.py` (7 passed) uses a fake adapter that returns complete small result sets — it cannot see the 10K route cap, the CRPV/STS overflow, or the missing error isolation.

### Proposed owner fix (smallest, generic)
1. **task-api:** add a **bounded count endpoint** for space-level task counts using an ES aggregation (e.g. `GET /swtr-read/task-counts?space=X` → MCP TQL `calculateTotal`/value-count with `space` in query string), so counts are O(1) source calls and correct for any space size. No row fetching.
2. **`_space_task_summary`:** per-space `try/except AS21SourceUnavailable` → emit `{space: {status: "source_unavailable"}}` per failed space (typed, **not** zero, not omitted silently) and let the remaining spaces populate; only raise if ALL spaces fail.
3. **UI:** the space block must render `—` / typed-unavailable per space, never "0" when the source state is unavailable.
4. **Regression:** a non-mocked test that stubs the route-level 502 overflow (or asserts the count route is used) proving (a) one space failing does not sink the report and (b) the unavailable space renders typed, not zero.

---

## Phases NOT RUN (per STOP-at-first-RED)

P1 (Overview panel scroll/height — partial pre-evidence only: PO Attention marker «Показаны первые 10 из 107» present and ≤10 rows; narrow 480px viewport showed `document.scrollWidth > clientWidth` horizontal overflow — **unverified, do not treat as P1 verdict**), P3 local CRUD, P4 Sprint predictability, P5 Releases, P6 Team space selector, P7 Quality Aging queue, P8 compact smoke — all deferred to A224R after the owner fix.

## Audit window (P2 probe only)

- task-api log 14891→14913: 15 lines — 6× `spaces/*/current-sprint` 200, 2× `sprints/*/tasks` 200, **3× `task-query?space=CRPV` 502**, rest 200. **0 local-store reads, 0 mutations, 0 tenant-wide (unscoped) task-query.**
- All reads were project-scoped full-space (spec-allowed) or sprint-scoped.

## Services left running

- agent: 127.0.0.1:8212 @ `99085d9` (fresh, `/live` 200)
- task-api: 8241 (system python3, 48 tools)
- MCP-SWTR: 3000
- vite: [::1]:5175 (PID 18675, fresh on `99085d9`)
- Screenshots: `/private/tmp/qa224_browser_c/{overview_full,overview_narrow}.png`
- Probe artifact: `/private/tmp/qa224_p2_probe.json`

## Recommendation

**STOP.** Owner fix for D-A224-1 (bounded count route + per-space isolation + no-false-zero UI), then A224R re-gate: P2 full parity (5 spaces exact vs fresh Oracle B) + P1–P8 + full audit. Do not start visual design-system phase.
