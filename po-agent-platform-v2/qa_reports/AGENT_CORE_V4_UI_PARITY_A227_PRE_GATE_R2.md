# A227 UI Parity Pre-Gate R2 — QA Report

**Verdict:** `AGENT_CORE_V4_UI_PARITY_GREEN_A227_PRE_GATE_R2`
**START_HEAD:** `cb90f479c34fc37684d89592ada97855b0d821a0`
**A227 baseline:** `db5e35f1b378b6ffde0c10085af8b68e4bf1e6b5`
**Branch:** `feat/core8-real-query-hardening-v2`
**Date:** 2026-09-30
**Role:** QA/tester only. No production/frontend/backend/plugin/test/config code was modified.

**Recommendation:** resume A227R P3–P7.

---

## P0 — build + Core integrity: GREEN

### P0.1 worktree
- `git pull --ff-only` clean. Tracked worktree clean (one transient `GIGACODE.md` memory line,
  restored with `git checkout` before testing).

### P0.2 exact zero diff vs A227 baseline — PROVEN
`git diff db5e35f..cb90f47` over the 6 files is **empty**; per-file blob hashes identical:

| File | blob (db5e35f = cb90f47) |
|---|---|
| `src/po_agent/harness/agent_core_v4.py` | `52100ca1ea2a…` |
| `src/po_agent/harness/agent_core_v4_reliable.py` | `1f7562dcfe2c…` |
| `src/po_agent/harness/agent_core_v4_robust.py` | `3bdb4d092096…` |
| `src/po_agent/llm/real.py` | `1cc10e12921a…` |
| `tests/test_agent_core_v4_reliable.py` | `28c1236a269a…` |
| `tests/test_agent_core_v4_robust_protocol.py` | `6e8e8cd90087…` |

Net owner code diff `db5e35f..cb90f47` is therefore limited to:
`frontend/src/recovery/Pages.tsx` (+56), `v4_plugins/_task_live_handlers.py` (+44),
`v4_plugins/task_catalog.py` (+16), `tests/test_agent_core_v4_attachment_sprint_scope.py` (+36).

### P0.3 build
- `tsc --noEmit` → exit 0. `vite build` → exit 0 (101 modules, 279.29 kB JS / 89.63 kB gzip).

### P0.4 focused tests — 48/48 passed
`test_agent_core_v4_attachment_sprint_scope.py`, `test_harness_attachment_skills.py`,
`test_agent_core_v4_wave_s2.py` (predictability), `test_harness_sprint_intelligence.py`,
`test_agent_core_v4_batch6_release_forecast.py`, `test_agent_core_v4_reliable.py`,
`test_agent_core_v4_robust_protocol.py` — the two A227P REDs are gone with the reconciliation
(the broken tests were deleted; the stable-baseline tests pass).

### P0.5 full V4 blast radius — 229/229 passed
`tests/test_agent_core_v4*.py tests/test_v4*.py` — 229 passed in 1.24 s, 0 failed.

---

## P1 — Tasks UI parity with direct PO Agent: GREEN

Query (exact): `Найди открытые задачи Калачанова с вложениями в пространстве WMB`

### Direct agent run (fresh dialogue, `/api/v1/query` on 8004)
- `status=COMPLETED`, `runtime=agent_core_v4`, `semantic_prepass_used=false`,
  `completion=runtime_contract`, 57.5 s, trace `bcd0cbfe-2d26-42ca-ab9f-45acd25e0c53`.
- Trajectory: load `tasks.search` → `space.resolve(WMB)` → `member.resolve(Калачанов, WMB)`
  → load `task.search_attachments` → `task.search_attachments(space=WMB, reference=Kalachanov.V.V,
  status=not_completed)` → ready(runtime_contract).
- Result: `count=0, results=[], source=REAL_AS21, status=not_completed`;
  answer: «В пространстве **WMB** не найдено открытых задач с вложениями, назначенных на
  **Kalachanov.V.V.** (0 результатов)»; UI contract `result_kind=attachment_collection`,
  `preferred_widget=attachment_table`, states include `REAL_EMPTY`.

**Source ground truth (live):** `assignee-tasks?assignee=Kalachanov.V.V&space=WMB` → 5 tasks,
**all terminal** (3× closed «Закрыт», 2× resolved «Решен»). A227 previously proved attachments
exist on 3 of them (WMB-30000×5, WMB-29995×10, WMB-29890×1). So “attachments exist but open
intersection is empty” is the correct source state — the grounded REAL_EMPTY answer is the honest one.

### Browser (Задачи, `/tasks`)
| Check | Result |
|---|---|
| fresh mount | **0 automatic POSTs** |
| first Найти | **exactly 1 POST**, HTTP 200; payload `{"query":"Найди открытые задачи Калачанова с вложениями в пространстве WMB"}` — **byte-identical** to the raw text (char-code audit, 64/64) |
| parity with direct | COMPLETED / agent_core_v4 / prepass=false / runtime_contract; terminal `task.search_attachments(space=WMB, reference=Калачанов, status=not_completed)`; `count=0, source=REAL_AS21`; same grounded answer phrasing (person named «Калачанова (Kalachanov.V.V)» — factual parity, LLM wording) |
| honest empty intersection | `.search-answer` renders the grounded «…не найдено открытых задач с вложениями…»; **no** error panel, **no** «не удалось получить корректный результат» |
| press Найти again (unchanged) | **exactly 1 new POST**, fresh trace (`af115bb9…` vs `ba11dbcc…`), same raw query |
| navigate away/back | re-verified on the **real** `/team` page: **0 POSTs with the P1 query** (team page fires its own 6 team queries — its own design, different payloads); snapshot preserved: answer text + «Снимок · обновлено 30.09.2026» + input value intact |
| Refresh (Обновить) | **exactly 1 new POST**, repeats the last submitted raw query, COMPLETED, fresh trace |
| no client router | all 3 POST payloads byte-identical to the raw NL text |

Artifacts: `/private/tmp/qa227r2_p1/` (post_0..2.json, run.log, screenshots),
`/private/tmp/qa227r2_p1b/` (away/back on /team), `/private/tmp/qa227r2_p1_direct.json`.

---

## P2 — Sprint Predictability: GREEN (typed SOURCE_UNAVAILABLE path)

Source check first: `DMS-SPRNT-3` is the valid current DMS sprint (IN_PROGRESS, 2026-09-13→27);
`spaces/DMS/sprints` rows carry only `code/name/status/start_at/finish_at/deleted` — **no
committed-baseline field** (`committed_count`/`baseline_total`/`planned_count`/`scope_at_start`/
`committed_tasks` all absent). Per the wave_s2 contract, predictability without a committed
baseline must fail typed, never substitute current scope.

- **Direct** (`Покажи predictability DMS-SPRNT-3`): `agent_core_v4`, prepass=false,
  trajectory load `sprint.predictability` → `sprint.resolve` → `sprint.predictability
  (sprint_id=DMS-SPRNT-3, space=DMS)` → typed `v4_capability_unavailable`,
  «Необходимая возможность не подтверждена источником данных и не выполняется.»,
  trace `e9c40a3f-2cc8-4cf3-bb70-302515d9f9d9`.
- **Browser** (`/sprint`, submit `DMS-SPRNT-3`): the exact query `Покажи predictability DMS-SPRNT-3`
  goes through `/api/v1/query`; content-matched response body (trace `5106c464-98e9-4b0b-9732-24de90ef33f9`)
  shows terminal capability `sprint.predictability` with the same typed unavailable result.
- **UI surface**: Predictability insight card renders `data-state="SOURCE_UNAVAILABLE"` —
  «Источник временно недоступен. Нули не подставляются.»; MetricCard shows `—` with hint
  «нужен source-backed committed baseline старта спринта»; **no fabricated percent**
  (regex scan), current-scope 79-task count **not** substituted. UI panel trace `5106c464`
  matches the body trace.
- The happy path (baseline present → `predictability * 100`, `completed / baseline_committed`)
  is proven at unit level in P0 (`test_predictability_requires_and_uses_authoritative_baseline`,
  ratio 0.4) and the UI reads the primary plugin contract field `predictability` first
  (`Pages.tsx:368-371`), never a nonexistent `predictability_percent` as primary.

Note: the `/sprint` grid fires 6 snapshot POSTs per submitted sprint (page design); with
concurrent POSTs, response bodies were matched by trajectory content, not request order.

---

## P3 — Release Forecast: GREEN (typed SOURCE_UNAVAILABLE path)

- **Direct** (`Покажи прогноз завершения релиза WMB 24Q1`): `agent_core_v4`, prepass=false,
  trajectory → `space.resolve(WMB)` → `release.search(space=WMB, query=24Q1, require_single=True)`
  → `release.forecast(space=WMB, release_id=7a84006f-7823-4052-ae46-b94f5165518e)` (canonical UUID
  bound from the observation) → typed `v4_capability_unavailable`.
- **Browser** (`/releases`, submit `WMB 24Q1`): exact query `Покажи прогноз завершения релиза WMB 24Q1`
  through `/api/v1/query`; content-matched body (trace `60422027-0905-4e40-8507-a20db9793b7a`) has
  terminal capability `release.forecast`, typed unavailable; UI «Predictability / Forecast» panel
  renders `data-state="SOURCE_UNAVAILABLE"`, UI trace `60422027` matches.
- **No fabricated date/percentage** (panel scans: `anyDate=false, anyPercent=false`),
  **no updated_at-as-completion proxy** (typed unavailable, nothing rendered as completion).
- The sufficient-history path (forecast date/days) is proven at unit/fixture level (P0 batch6 tests,
  A220 independent probe: 10d/0.2/10.0 exact; `updated_at`-only → raise); live WMB 24Q1 stays
  `release_linkage_unpopulated` (A220 state) → honest typed SC.

---

## P4 — architecture audit: GREEN

| Requirement | Evidence |
|---|---|
| six reconciled Core/Core-test files zero diff vs A227 | P0.2 blob hashes |
| Tasks raw query unchanged | 3/3 UI POST payloads byte-identical (char-code audit) |
| attachment status extension plugin-owned | diff confined to `v4_plugins/_task_live_handlers.py` (`_matches_requested_status` + typed status filter in `build_task_search_attachments`, `status_raw`/`status_type` in `_task_dict`) and `task_catalog.py` (capability arg + skill procedure); Core untouched |
| zero phrase-specific routers | static scan of `frontend/src`: no surname/space/phrase branching in the query path; UI sends the raw NL text |
| zero direct AS21 calls from frontend | axios client uses relative `/api` (vite proxy → agent) only; the single `portal.works.prod.sbt` reference is a pre-existing user-click deep link (`window.open`, TaskCard), not a data call |
| zero local-store factual reads | agent log: 0 `GET /api/v1/tasks` (non-swtr) reads across the whole session |
| zero tenant-wide scans | task-api log: 9/9 `task-query` calls carry `space=` (5× `space=WMB&assignee=Kalachanov.V.V`, 4× `space=WMB&release=UUID`); 10/10 `/versions` carry `space=`; sprint routes bounded (`limit=100&max_pages=500`); identity via bounded `assignees/resolve` point lookups |

---

## Non-blocking notes

1. **Happy-path live coverage:** P2 committed-baseline and P3 sufficient-history render paths cannot
   be exercised live (source has no committed baseline; WMB release linkage unpopulated since A220).
   Both are certified at unit/fixture level (P0) and the UI read paths were code-verified against the
   plugin contracts.
2. **Page defaults:** `/sprint` (WMB-SPRNT-1) and `/releases` (WMB-2024-Q3) fire their 6-snapshot
   grids on mount by design; snapshots are sessionStorage-cached and are not re-fired on revisit.
3. **Direct vs UI wording:** the LLM names the person slightly differently between the direct and UI
   runs («Kalachanov.V.V» vs «Калачанова (Kalachanov.V.V)»); all factual fields (capability,
   constraints, count, source, completion) are identical.
4. QA harness quirk (not product): with 6 concurrent snapshot POSTs, response bodies must be matched
   by trajectory content, not request order (FIFO assignment is unreliable).

## Services left running
agent 8004 (PID 15107 @ cb90f47, `PO_AGENT_AGENT_CORE_V4_ENABLED=true`), task-api 8241 (PID 15039,
system python3, 48 MCP tools over SSE), MCP-SWTR 3000 (PID 25954, reused — code unchanged),
vite `[::1]:5175` (PID 15200/15218, proxy `/api` → 8004).
