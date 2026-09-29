# A226R2 — Text-search scale + final UX re-gate

**Verdict: `AGENT_CORE_V4_UI_POLISH_SNAPSHOT_RED_A226R2`**
**Classification: `RED_P2_SPACE_SELECTOR_INERT_PLUS_STATUS_TENANT_SCAN`**
**START_HEAD:** `d99307633fcdc5686f8d7aedaee683aa5dc0c4cd` (branch `feat/core8-real-query-hardening-v2`)
**Base (A226R report):** `c93e7eb` · **Date:** 2026-09-29 · **Role:** QA only

Owner fixes under test: per-space isolation for unscoped phrase search (task-api), completeness
metadata propagation (task.search_text), 5-mode Tasks UI, explicit text-space selector (default WMB),
launcher hidden while task drawers open, ru-RU snapshot timestamps, 65s bounded page refresh,
identical-Aging-criteria live re-read, LOCAL-NNNN retention.

---

## P0 — build / diff: GREEN (with 1 owner test-logic bug)

- Diff `c93e7eb..d993076`: `task-api/app/routers/swtr_query.py` (+32),
  `po-agent-platform-v2/src/po_agent/harness/v4_plugins/_task_live_handlers.py` (+35),
  4 frontend files (Pages.tsx / QualityDashboard.tsx / pageSnapshot.tsx / workspace.css),
  1 new task-api test. No Agent Core/planner/runtime architecture changes. ✓
- `tsc --noEmit` clean; `vite build` clean.
- Focused po-agent suites: 22/22 (team aging, task search source status, task-api adapter);
  V4-wide: 228/228.
- task-api full suite: **30 failed / 85 passed** vs baseline `c93e7eb` **28 failed / 85 passed**
  (read-only worktree comparison). Delta = exactly the 2 new tests in
  `task-api/tests/test_swtr_task_query_partial.py`, which are structurally broken: they call the
  FastAPI route function directly, so `space` arrives as a default `Query(None)` object and
  `space.upper()` raises `AttributeError`. Owner shipped them RED (CI-gap class seen in A215/A196).
  **Production logic independently verified 10/10** via QA probe
  (`qa_226r2_probe_partial.py`, explicit params): unscoped isolation (source_complete=false,
  incomplete_spaces={CRPV,STS}, completed={DMS,OLP,WMB}, healthy matches retained), scoped strict
  502, all-fail aggregate 502, all-healthy source_complete=true.
- The other 28 failures are pre-existing environment-dependent suites (legacy local-store CRUD,
  integration), identical at baseline.

## P1 — Text search blocker (WMB / «БП 2027» + per-space isolation): **GREEN**

**Independent Oracle B** (direct task-api scoped read, 37.5s): 99 WMB tasks,
`source_complete=true`; 73 of 99 are description matches (phrase not in title) —
description search retained.

**Agent API** (exact UI query string `Найди задачи по тексту "БП 2027" в названии и описании в
пространстве WMB`): COMPLETED 31.5s, `task.search_text` with `space=WMB` bound by the planner,
**99/99 exact key parity** with Oracle B, `source_complete=true`, completion=runtime_contract.

**Browser** (Tasks → Текстовый поиск → WMB → БП 2027, fresh mount auto-query):
- 99 cards, panel `Задачи AS21 99/99`, **99/99 exact parity** (post_0 vs Oracle B).
- task-api access log: the browser request issued exactly
  `task-query?limit=100&max_pages=100&phrase=БП 2027&space=WMB` — **no reads of other spaces**.
- Away → Overview → back: **0 new POSTs**, 99/99 snapshot preserved.
- Page-level Обновить: exactly **1 new POST with the identical WMB+text query**, 99/99 retained.
- Snapshot label ru-RU: `29.09.2026, 09:01` (P4 timestamp requirement pre-confirmed).

**Direct unscoped task-api phrase probe** (231s wall, live):
- HTTP **200** (was 502 in A226R — D-A226R-1 fix works);
- `source_complete=false`; `incomplete_spaces=[CRPV 502, STS 502]` with
  `pagination exceeded max_pages` details; `completed_spaces=[DMS, OLP, WMB]`;
- healthy-space matches retained: all **99 WMB keys** present (DMS/OLP legitimately 0 for this phrase);
- no fake exactness, no fake zero.

## P2 — Tasks UX: **RED** (first boundary — STOP)

Mode audit: exactly 5 buttons `Текстовый поиск / Исполнитель / Статус / Спринт / Релиз`,
no attachment/Excel/PDF/MSG buttons. ✓
Smoke: Text WMB ✓ (above) · Assignee `Kalachanov.V.V` COMPLETED **2869/2869** (single bounded
person-scoped read) ✓ · Sprint `DMS-SPRNT-3` COMPLETED **74/74** ✓ · Release `OLP 1.6.0`
→ typed `v4_capability_unavailable` after resolving the canonical release
(`versions?space=OLP&query=1.6.0` → uuid `20ba588e-…`, then scoped
`task-query?space=OLP&release=20ba588e-…`, membership 0 rows) — honest typed state,
no generic clarification, no fake zero ✓.

### D-A226R2-1 (BLOCKING, functional) — text space selector is inert

User selects **DMS** in `.task-space-select` and submits «БП 2026» → the submitted query is
`Найди задачи по тексту "БП 2026" в названии и описании в пространстве **WMB**` (payload captured;
task-api log confirms `phrase=БП 2026&space=WMB`; 20 WMB tasks returned). The selection is ignored.

Root cause (code-verified): `Pages.tsx:283` submit handler calls
`setSubmitted({ mode, value: search.trim() })` **without `textSpace`**, while the query builder uses
`submitted.textSpace || 'WMB'` (`Pages.tsx:228`). After any user submit, `submitted.textSpace` is
`undefined` → the selector is cosmetic and every text search runs in WMB regardless of selection.
Introduced by `8f81ce3`/`c9568d3` (selector added; submit handler not updated).

Owner fix: pass the selected space through — `setSubmitted({ mode, value: search.trim(),
textSpace: mode === 'text' ? textSpace : undefined })` (or merge into submitted) + a non-mocked
regression asserting a non-default space reaches the submitted query.

### D-A226R2-2 (BLOCKING, tenant-wide scan) — Status mode has no space and scans the whole tenant

Status mode sends `Покажи задачи в статусе В работе` (no space). `task.search_status`
(`_task_live_handlers.py:253`) with no space/assignee calls `_live_query` with **no filter** →
bare `task-query?limit=100&max_pages=100` over all 5 spaces. Live repro (clean, no contention):
**FAILED after 283.0s**, `warnings=[source_unavailable]`, trajectory `[load_skill, call]` —
the adapter client timeout kills the multi-minute full-tenant scan (CRPV→DMS→OLP→STS→WMB, each up
to 100 pages; STS ≈460k rows, CRPV ≈150k). The UI's 65s page timeout shows an error first; the
server-side scan is aborted on client disconnect. This violates the P2 requirement
"no tenant-wide fallback scan". Pre-existing backend behavior newly one-click-reachable through the
new UI (same source-scale lineage as A226R-1, now via status).

Owner fix options: (a) add the space selector to Status mode as well (consistent with Text), and/or
(b) harden `task.search_status` to require/derive a space scope (fail-closed typed clarification
when absent), mirroring the text-search scoping.

**STOP applied per spec — P3 (local drawer), P4 (Overview refresh), P5 (Aging), P6 (Sprint
forensic), P7 (Release forensic), P8 (retained smoke) not executed.**

## Secondary observations (non-blocking)

- **F1 (owner test bug):** `test_swtr_task_query_partial.py` both tests structurally RED
  (direct route call with `Query()` defaults) — fix by passing all params explicitly or via TestClient.
- **F2 (launch env):** po-agent auto-loads `.env` via pydantic-settings; a bash `source .env`
  corrupts it (line 7 `TEAM_CONFIG_PATH` has an unquoted path with spaces; line 12 `LLM_API_KEY`
  JWT executed as a command). Agent must be started with explicit
  `PO_AGENT_AGENT_CORE_V4_ENABLED=true` (absent from `.env`; default false → queries silently route
  to `legacy_harness`, which then fails closed after ~273s unscoped scans).
- **F3 (drift, source-proven):** Kalachanov.V.V 2858→2869; DMS-SPRNT-3 scope 74 retained;
  WMB «БП 2027» 99 retained (A226R parity).
- **F4:** release page identity path healthy (uuid resolution + scoped membership query);
  membership still unpopulated in source (A220 state) → typed SC is the correct terminal.

## Audit (executed portion)

- 0 local `/api/v1/tasks` reads; 0 mutations on task-api (0 non-GET requests).
- No tenant-wide scans except the D-A226R2-2 bare status scan (aborted client-side).
- All bounded reads: 1 scoped WMB phrase (×3: oracle/API/browser), 1 unscoped phrase probe,
  1 person-scoped assignee, 1 sprint-complete, 1 versions + 1 release-scoped.

## Services left running

agent 8004 (PID 46866 @ d993076, V4 enabled, 13 plugins), task-api 8241 (PID 41311, system py3),
MCP 3000 (PID 25954), vite [::1]:5175 (PID 42752).

## Next owner action

Fix D-A226R2-1 (submit must carry `textSpace`) + D-A226R2-2 (status scoping) + F1 test fix →
A226R3 re-gate: P2 full (all 5 mode smokes + selector with non-default space), then P3–P8 as specced.
