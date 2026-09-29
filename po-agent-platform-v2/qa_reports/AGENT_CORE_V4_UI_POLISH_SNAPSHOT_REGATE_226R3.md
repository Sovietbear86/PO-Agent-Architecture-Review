# A226R3 — Tasks space-scoping re-gate + full retained P3–P8 sweep

**Verdict: `AGENT_CORE_V4_UI_POLISH_SNAPSHOT_GREEN_A226R3`**
**Classification: `GREEN_P1_P8_ALL_PASS`**
**START_HEAD:** `5af0f320078237ce739e42de5f011b1a8d3e11d2` (branch `feat/core8-real-query-hardening-v2`)
**Base (A226R2 report):** `fc2487c` · **Date:** 2026-09-29 · **Role:** QA only

Owner fixes under test (diff `fc2487c..5af0f32`): Tasks space selector now persisted and
drives the submitted query (`searchSpace`), Status mode query appends «в пространстве {space}»,
space selector shown for both Text and Status modes, snapshot key includes the space,
plus task-api test/docs touch-ups. No Agent Core / planner / runtime / adapter changes.

Both A226R2 blocking defects (D-A226R2-1 inert text space selector, D-A226R2-2 Status tenant
scan) are **CLOSED and source-proven below**. No new blocking defect found in P1–P8.

---

## P0 — build / diff: **GREEN**

- `git pull --ff-only` at `5af0f32`; diff vs `fc2487c` = `frontend/src/recovery/Pages.tsx`
  (searchSpace persistence, Status space suffix, selector for text+status, snapshot key with
  space), `task-api/tests/test_swtr_task_query_partial.py`, docs. No core/planner/runtime drift. ✓
- `tsc --noEmit` clean; `vite build` clean. Focused po-agent V4 suites green.
- Services restarted on START_HEAD: agent 8004 (V4 enabled), task-api 8241, MCP 3000,
  vite [::1]:5175. Logs: `/tmp/qa226r3_{agent,taskapi,vite}.log`.

## P1 — A226R2 blockers (space selector + Status scoping): **GREEN**

**Text mode (D-A226R2-1 regression surface):**
- **DMS** selection + «БП 2027» → submitted payload
  `Найди задачи по тексту "БП 2027" в названии и описании в пространстве **DMS**`,
  task-api line exactly `task-query?limit=100&max_pages=100&phrase=БП 2027&space=DMS`,
  COMPLETED **0/0** honest zero, 0 cards. The D-A226R2-1 failure mode (DMS selection
  submitting a WMB query) is gone.
- **WMB** selection + «БП 2027» → **99/99 exact** (A226R parity), cards 99,
  `task.search_text`, completion=runtime_contract.
- Away → back: **0 new POSTs**, space selector still WMB, search still «БП 2027», 99/99 retained.
- Page refresh: exactly 1 new POST, query `…в пространстве WMB`, 99/99 retained.

**Status mode (D-A226R2-2 regression surface):**
- **WMB** + «открытые» → payload `Покажи задачи в статусе открытые в пространстве WMB`,
  scoped read(s) `space=WMB` only, COMPLETED **281/281 exact** vs direct task-api oracle,
  completion=runtime_contract. No unscoped `task-query` issued — the A226R2 ~280s
  full-tenant scan / `source_unavailable` is gone.
- **DMS** + «открытые» → **83/83 exact** (drift from A226R2 83: consistent), single
  `space=DMS` read.
- Space selector is **visible in Status mode** (A226R2: text-only).

**Audit:** 9 POSTs in the whole P1 run; every `task-query` line carried `space=`. No
all-space scan. **D-A226R2-1 and D-A226R2-2: CLOSED (source-proven).**

## P2 — Tasks UX retained: **GREEN**

- Exactly 5 modes (`Текстовый поиск / Исполнитель / Статус / Спринт / Релиз`), no
  attachment/Excel/PDF/MSG buttons. ✓
- Text WMB 99/99 ✓ (above) · Status WMB 281/281 ✓ · Status DMS 83/83 ✓
- Assignee `Kalachanov.V.V` → COMPLETED **2876/2876 exact** (drift +7 vs A226R2 2869,
  live source growth), single person-scoped read.
- Sprint `DMS-SPRNT-3` → COMPLETED **75/75 exact** (drift +1 vs A226R2 74).
- Release `OLP 1.6.0` → typed `v4_capability_unavailable` after canonical release
  resolution, honest state, no fake zero, no generic clarification. ✓

## P3 — Local drawer hit-testing: **GREEN** (F1 non-blocking)

- 1440×900: create → `LOCAL-0001` with title/priority HIGH/labels QA+Регресс/deadline
  15.10.2026 persisted to localStorage (`po-local-tasks`); drawer closes on submit.
- Edit → title updated, localStorage follows; reload → `LOCAL-0001` re-rendered;
  delete → 0 rows, 0 new POSTs.
- 1366×768: launcher (below fold) becomes reachable when the drawer is closed
  (`elementFromPointAtLauncher` = brand-block, not the launcher); create works
  (`LOCAL-0001`, launcher hidden while drawer open — `body.task-drawer-active`).
- AS21 task drawer (`WMB-30004` card) → `body.task-drawer-active`, launcher `display:none`,
  hit-test at launcher position returns brand-block (no interception).
- Audit: 1 POST total (agent query only), **0 AS21/local-store writes**, 0 non-GET.
- **F1 (non-blocking):** the AS21 drawer close (X) button sits under the sticky topbar at
  1366×768 and is not hit-testable at its rendered position (Escape / outside-click work).

## P4 — Overview refresh completion: **GREEN** (F2 non-blocking)

- Fresh mount: 4 snapshot POSTs (overview/attention/brief/status), label ru-RU
  `данные на 29.09.2026, 18:56`.
- Refresh with source slow: button `Обновляем…`, **stale data kept** during wait; on success
  metrics updated to **119 / 40 / 7** (active/completed/blocked), 4 new POSTs, label bumped
  `18:57`.
- Injected 500: stale data kept + `snapshot-state-error` label «Не удалось обновить ·
  данные на …», button returns to `Обновить` (retry available).
- Long refresh: button returned after **63.1s** with stale kept (F2 below).
- Away → back: 3/3 cached snapshots preserved, no re-POST of settled snapshots.

## P5 — Quality Aging (DMS >15 days): **GREEN** (F3 non-blocking)

- «Покажи старые задачи команды DMS старше 15 дней» → COMPLETED **38/38 key-exact** vs
  independent task-api oracle (`space=DMS`, team scope, threshold 15): DMS-1 (217d) …
  DMS-401 (19d); panel 38 rows, first rows DMS-1/DMS-30/DMS-64/DMS-73/DMS-86.
- Re-press with identical criteria: live re-read (not cache reuse) — new POST, COMPLETED,
  panel 38/38 identical (no source drift in window).
- Control WMB >7: typed 0 (no WMB team-scope rows >7d) — no leak of DMS data into WMB
  criteria.
- **F3 (non-blocking):** the shared Quality `refreshNonce` re-fires all 4 Quality snapshot
  queries (wmb-102 quality/acceptance + aging) on any single refresh (4 POSTs observed);
  correct, just not per-widget scoped.

## P6 — Sprint forensic DMS-SPRNT-3: **GREEN**

- Harness correlated 6 DMS-scoped posts (all HTTP 200):
  - **Scope 75 · Completed 27 · completion 36% · Velocity 27 · Throughput 1.929**
    (completed / 14.0 calendar days) · **WIP 28** — all exact vs capability-exact
    `qa_226r3_p6_oracle.py` (WIP = open ∧ status_type ∉ {open,todo,backlog,registered} ∧
    category ≠ backlog; status_type {done 27, progress 24, pause 24}).
  - RiskQueue **36 = 1 blocked** (DMS-427, source status «Need info»/statusType pause,
    rank 1) **+ 35 aging** (DMS-64 167d … DMS-405 14d) — fully source-grounded.
  - `sprint.predictability` → typed `v4_capability_unavailable`
    («requires committed/baseline scope from REAL AS21; current scope is a not substitute»):
    verified `current-sprint` source payload carries only id/name/goal/status/startAt/finishAt
    — no committed/baseline fields, so the typed SC is the correct source-grounded answer.
  - All completions = `runtime_contract`; no planner_ready.

## P7 — Releases forensic: **GREEN** (F4 non-blocking)

- OLP 1.6.0 → canonical uuid resolved; all metric requests
  (`scope/progress/blockers/dependencies/risk_queue`) execute `release.*` and terminate
  typed `v4_capability_unavailable` (release→task membership absent in source) —
  no fake zero, no generic clarification, no pseudo-forecast.
- WMB 24Q1 → canonical uuid resolved; most metrics typed SC as above.
- **F4 (non-blocking, pre-existing planner-routing class):** WMB 24Q1 «область/прогресс/
  блокеры релиза» route to `sprints.discover` → generic NEEDS_CLARIFICATION instead of the
  typed SC (OLP 1.6.0 routes correctly 5/5). One transient `v4_runtime_failure`
  (empty skill list = LLM endpoint blip), re-runs clean. No data fabrication in any variant.

## P8 — Retained design / brand / audit: **GREEN**

- **Overflow:** `scrollW == clientW` (false) on all 6 pages (overview/tasks/sprint/releases/
  team/quality) at both **1440×900 and 480×800**.
- **Brand:** `.works-logo` = «Platform V», `.brand-subtitle` = «DB Tribe»,
  `.topbar-actions` chips = `OLAP`, `DataMarts`. ✓
- **Daily Brief (overview):** rendered rich and GROUNDED — «119 активных задач · 7
  заблокировано · 8 без исполнителя · 40 завершено», «Точек внимания: 101», real top-5 table
  (OLP-2897 kuznetsov.m.se 153d заблокирована >14дн …) — exact parity with direct
  `Сделай daily brief` API probe (COMPLETED 20.9s, `po.daily_brief`, same numbers).
  First-mount render occasionally hits the 65s snapshot timeout under 4-snapshot concurrent
  load (see F2); retry / later render is correct.
- **Team utilization:** 9 `.capacity-row` rows, real worklog-based values
  (Semavin.M.M — 133.1% OVER, then 124.6% / 113.2% …), OVER/OK badges rendered.
- **Attention panel:** 101 items, real tasks (OLP-2897, OLP-2906, …, DMS-427).

**Final audit (whole A226R3 run, task-api access log, 2085 HTTP lines):**
- local-store (`GET /api/v1/tasks`) reads: **0**
- `task-query` lines: 682 — without `space=` AND without `assignee=` (tenant scan): **0**
  (all space-scoped: WMB 164, DMS 128, OLP 17, plus assignee-scoped person reads)
- non-GET requests (mutations): **0**

---

## Findings (all non-blocking)

| ID | Sev | Description |
|----|-----|-------------|
| F1 | low | AS21 drawer close (X) under sticky topbar at 1366×768, not hit-testable at rendered position (Escape/outside-click work) |
| F2 | low | Overview snapshot 65s client timeout vs ~63–65s+ source latency race: long refreshes show «Не удалось обновить» while stale data is kept; retry succeeds (direct probes 20.9–63s) |
| F3 | low | Quality shared `refreshNonce` re-fires all 4 Quality snapshots on any refresh (correct, not per-widget) |
| F4 | low | Pre-existing planner routing: quarter-looking WMB 24Q1 scope/progress/blockers → `sprints.discover` generic clarification instead of typed `v4_capability_unavailable` (OLP 1.6.0 correct); 1 transient LLM-blip `v4_runtime_failure` (re-run clean) |

Source drift vs A226R2 (live growth, consistent): Kalachanov 2869→2876,
DMS-SPRNT-3 74→75.

## Verdict

`AGENT_CORE_V4_UI_POLISH_SNAPSHOT_GREEN_A226R3` — A226R2 blocking defects D-A226R2-1/2
closed and source-proven; P1–P8 all pass; no local fallback, no tenant scan, no mutations;
only 4 non-blocking findings.
