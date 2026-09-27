# A224R2 — Team-scoped overview + task status filters + attention scrolling

**Role:** QA/adversarial tester (no code changes)
**Branch:** `feat/core8-real-query-hardening-v2`
**Test HEAD:** `dbd829ddb0100843d47c3d58ab29a92dd5e2e84b`
**Prior state:** A224R report `967ca34` (RED_P1R_COUNT_ROUTE_SOURCE_METADATA_ABSENT)
**Date:** 2026-09-27
**Verdict:** `AGENT_CORE_V4_UI_USABILITY_GREEN_A224R2`

---

## Scope correction (supersession)

The A224/A224R full-space counting requirement is **SUPERSEDED** by owner commits
`051d340..dbd829d` (docs `1fe2a70`, `bed6477`, `dbd829d`). The product requirement is now:
**"Задачи по пространствам" = tasks assigned to configured team members
(`task-api/config/team_members.yaml`, 16 logins), grouped by space, deduplicated by task key.**
Full-space totals (150129/460452 etc.) are no longer a product requirement and were NOT re-verified.

## Owner changes under test

- `051d340` plugin `wave_batch5_po.py`: `_team_task_summary` — per-configure-login bounded
  `search_tasks('assignee = "<login>"', max_results=10000)`; union by key; group by approved
  space; total/active/completed/blocked from those team-assigned tasks; one failed member →
  `SOURCE_PARTIAL` (all rows), zero available members → `V4CapabilityUnavailable`.
- `7b1ad93` Overview: attention queue renders the full queue (no `slice(0,10)`); label
  "Всего N задач · прокрутите список".
- `7a9f57d` Tasks page: separate "Статус AS21" and "Статус локальных" filters.
- `15f6b23`, `fca148b`, `6869c9b`, `62ec292`: partial-state metadata, UI fail-closed note,
  obsolete combined count removed, tests.

## P0 — build / architecture: **GREEN**

- Diff `967ca34..dbd829d`: 7 files (plugin +106, OverviewDashboard +17, Pages +35, test +63,
  3 docs). No Agent Core/planner/runtime/session change.
- `wave_batch5_po.py` no longer calls `get_space_task_count` or any `project = "…"` full-space
  search; the only task read in the widget path is
  `search_tasks(f'assignee = "{login}"', max_results=10000)` per configured login.
- Tests: `test_agent_core_v4_batch5_po.py` **8/8** (incl. new `test_status_report_marks_team_space_summary_partial_when_one_member_source_fails`
  and team-scoped aggregation assertions); V4 suites **226/226**; `tsc --noEmit` GREEN;
  `vite build` GREEN (270.21 kB js / 33.02 kB css).

## P1 — team-scoped summary exactness: **GREEN**

Independent Oracle B (`qa_artifacts/qa_224r2_oracle_b.json`): 16 canonical logins read through
the certified REAL AS21 assignee route (`GET /swtr-read/task-query?assignee=<login>`), raw rows
mapped with the certified adapter `_map`, unioned by key, grouped by space, computed
total/active/completed/blocked independently of the plugin aggregation.

| space | total | active | completed | blocked | agent `by_space_tasks` |
|-------|-------|--------|-----------|---------|------------------------|
| WMB   | 6     | 0      | 6         | 0       | 6 / 0 / 6 / 0 EXACT    |
| DMS   | 313   | 189*   | 124*      | 2       | 313 / 189 / 124 / 2 EXACT |
| OLP   | 398   | 199    | 199       | 5       | 398 / 199 / 199 / 5 EXACT |
| CRPV  | 510   | 249    | 261       | 8       | 510 / 249 / 261 / 8 EXACT |
| STS   | 3201  | 663    | 2538      | 0       | 3201 / 663 / 2538 / 0 EXACT |

\* live source drift during the session (one DMS task completed between the two reads; see F3).

- Union = 4428 unique keys; **0** keys returned by more than one login (no double-counting).
- **Kalachanov.V.V included**: 2870 tasks, present in WMB/DMS/OLP/CRPV/STS wherever source
  says (e.g. CRPV-102738, …).
- 16/16 member reads source-ready; state `SOURCE_BACKED`, `missing_members=[]` for all rows.
- **All-member failure fail-closed**: throwaway agent (port 8213) against a dead task-api port
  → `FAILED` "Источник AS21 временно недоступен…" in 8.0 s, 0 results, no fabricated
  `by_space_tasks` (`qa_artifacts/qa_224r2_p1_allfail.json`).
- **Single-member failure → SOURCE_PARTIAL**: covered by owner's non-mocked stub regression
  (`test_status_report_marks_team_space_summary_partial_when_one_member_source_fails`, P0 green);
  UI renders the partial state as "Часть данных участников команды недоступна · без ложных итогов"
  (no numeric values shown).
- `by_product` (current-sprint) unchanged / A219-A221 compatible: DMS-SPRNT-3 73, OLP-SPRNT-8 74,
  CRPV/STS/WMB NO_CURRENT_SPRINT null-preserved.

## P2 — Overview Browser C: **GREEN**

- Block title exactly "Задачи по пространствам" (5 cards).
- Explanatory note present: "Только задачи, назначенные участникам команды из
  team_members.yaml; одинаковые задачи дедуплицируются по ключу."
- Cards show exact total/active/completed/blocked (DOM text vs Oracle B: 5/5 spaces exact at
  capture time; DMS active/completed = 188/125 due to the same live drift as P1 — a fresh
  backend call returned the identical 188/125, proving UI == backend, `qa_224r2_p2_fresh_agent.json`).
- **No 150129 / 460452** (or any giant full-space total) anywhere in the panel.
- WMB = 6 (real, source-proven) — no false zero.

## P3 — PO Attention full scroll: **GREEN**

- Queue state with 107 attention items (>10): **107 `.attention-row` in DOM** (no first-10 slice).
- Bounded panel: `.overview-scroll-body` client height 360 px, scroll height 9182 px;
  internal vertical scroll reaches item 11 and the final row
  (first `DMS-352` → last `OLP-3333`; mid-scroll top=4591).
- Label: "Всего 107 задач · прокрутите список" + "Scoring: po_attention_v1".
- Daily Brief visible height comparable (360 px); page scroll height 1402 px — no page-length
  explosion; downstream "Задачи по пространствам" block reachable.

## P4 — Tasks AS21 status filter: **GREEN**

- Result set: assignee `Semavin.M.M` → 340 tasks, 7 distinct source statuses
  (Cancelled 2, Closed 7, Open 3, QA 4, Ready for QA 10, Resolved 82, Unknown 232).
- "Статус AS21" selector lists exactly the source statuses present in the current result
  (options == API counts keys).
- ALL = 340/340; each status filters cards **exactly** (DOM count == expected for all 7,
  header shows `n/340`), case-insensitive; reselecting ALL returns 340.
- Changing the display filter triggers **0** AS21 requests (pure client-side) → no mutation.
- Backend explicit "Статус" search mode not broken: scoped "Покажи задачи в статусе In progress
  в DMS" → `task.search_status` COMPLETED, 17 DMS rows all "In progress". Unscoped variant is a
  pre-existing boundary: typed NEEDS_CLARIFICATION in browser / 502-fail-closed source_unavailable
  in one API re-probe (both safe, no data, no fabrication) — pre-existing A224/A224R lineage,
  not introduced by A224R2.

## P5 — local task status filter + CRUD: **GREEN**

- Created 4 local tasks (TODO/HIGH/2 labels/owner, IN_PROGRESS, BLOCKED, DONE) via the drawer.
- "Статус локальных" filters exact: ALL=4, TODO=1, IN_PROGRESS=1, BLOCKED=1, DONE=1.
- Status transitions move rows between filtered views immediately:
  TODO→IN_PROGRESS (TODO 1→0, IN_PROGRESS 1→2), IN_PROGRESS→DONE (DONE 1→2).
- Card fields render: owner "QA-Owner", priority "HIGH", labels "alpha, beta" (field re-probe).
- Reload: all 4 persist in UI and `localStorage['po-local-tasks']` (titles/statuses/priorities/labels intact).
- Delete removes from UI and localStorage (4→3).
- Old-schema row (no priority/status/labels) safely defaults to **MEDIUM / TODO / []** and renders.
- **0 AS21 writes** during the whole P5 (request audit: writes=[], reads=0 on the Tasks page).

## P6 — deferred A224 usability checks: **GREEN**

- **Local CRUD full flow** — covered by P5 (create/persist/status-change/delete).
- **Sprint predictability (DMS-SPRNT-3)**: Predictability = "—" with hint
  "нужен source-backed baseline старта спринта" — honest source limitation, **no fake
  percentage**, no "current scope baseline" fallback. Retained metrics GREEN: Scope 73,
  Completed 19, Velocity 19 tasks/sprint, WIP 31, Готовность 26%, Throughput 1.375 (F4 drift),
  Risk Queue 38 rows (A223R2 parity).
- **Releases (24Q1 WMB / 1.6.0 OLP)**: panels resolve to typed `SOURCE_UNAVAILABLE` (scope,
  progress, blockers/dependencies) + `NEEDS_CLARIFICATION` (release risks, pre-existing
  release-risk routing); metrics all "—", **no fake zero**, "Forecast не активирован" note
  present — honest sparse behavior accepted.
- **Team**: no manual capacity-baseline input, no "Пересчитать" button; visible
  "40 ч/чел. … owner policy" note + "Рабочая неделя: 40 ч (автоматический owner policy)".
  Space selector works: DMS (active 54 / WIP 31 / blocked 2 / 13 members) → OLP
  (72 / 53 / 6 / 13 members) — values change on switch (no stale leak); workload/WIP/blocked/
  bottlenecks (9→10)/distribution (13) populate; Capacity panel typed `SOURCE_UNAVAILABLE`
  (estimates missing in source — accepted SOURCE_CONDITIONAL behavior).
- **Quality**: WMB-102 = **85/100**, Acceptance **0/100**, Пробелы **1**, decision **REWORK
  ("Вернуть на доработку")** — A223R2 parity retained.
- **Quality Aging**: space+threshold requests; vs production-semantics Oracle B
  (`is_open` + source `created_at`): WMB ≥7 = **265/265 EXACT** (top WMB-87 579d),
  DMS ≥15 = **72/72 EXACT** (top DMS-1 215d), DMS ≥220 = **0** with honest empty note
  "Источник подтвердил: задач старше выбранного порога нет." (source-proven empty, not
  source-unavailable).
- **Retained smoke**: chat rich rendering (rich-answer with tables + headings, no raw markdown,
  evidence + feedback rows); competency recommendation responds (rich answer + V4 panel,
  no fabrication); release source limitation as above.

## P7 — responsive layout: **GREEN** (1 non-blocking finding)

- Desktop 1440px: all controls usable; Overview internal scroll usable (360 px panel).
- 480px: Overview internal scroll usable (107 rows, 360 px panel); Tasks filter controls
  usable, no overflow (scrollWidth == 480).
- **F-A224R2-1 (non-blocking):** at 480px the PO Attention queue rows (long task titles +
  score `<em>` badge) cause minor horizontal overflow (doc 14–75 px depending on rendered
  rows). The core deliverable `.product-status-card` does **not** overflow; all content is
  reachable (horizontal scroll engaged, `scrollLeft` up to 75 px). Per spec this is a recorded
  finding, not a RED.

## P8 — audit: **GREEN**

Live task-api access-log audit (`qa_artifacts/qa_224r2_p8_audit.txt`, 687 HTTP lines):
- **0 AS21 mutations** (no POST/PUT/PATCH/DELETE besides chat `/api/v1/query`).
- **0 local factual fallback** reads (`GET /api/v1/tasks` = 0).
- **0 tenant-wide/whole-space corpus scans in the Overview by-space widget** — the widget path
  issued exactly the 16 configured-login assignee reads; all `assignee=` values are configured
  team logins (**0 non-configured**).
- 5 unscoped `task-query` calls in the log are all **502 fail-closed** and originate from the
  pre-existing unscoped status-mode/overview probes (not the team-scoped widget) — pre-existing
  A224/A224R boundary, out of A224R2 scope.
- 51 `task-count` calls in the log belong to the superseded A224R route (same accumulating
  log); the A224R2 team-scoped path never calls it.
- Frontend: single `localStorage.setItem('po-local-tasks', …)` — localStorage writes only for
  LOCAL tasks.

## Findings (non-blocking)

- **F-A224R2-1:** 480px Overview — attention-queue score badge rows overflow horizontally by
  ~14–75 px; core space cards unaffected; content reachable (see P7).
- **F-A224R2-2 (context, pre-existing):** unscoped status-mode/overview task-query calls fail
  closed 502 (pagination cap, A224/A224R lineage); team-scoped widget is clean.
- **F-A224R2-3:** DMS active/completed drift 189/124 → 188/125 between P1 oracle and UI capture
  (one task completed live); fresh backend call matched the UI exactly.
- **F-A224R2-4:** sprint throughput 1.385 → 1.375 live drift (sprint task set changed);
  risk queue 38 unchanged.

## Verdict

**`AGENT_CORE_V4_UI_USABILITY_GREEN_A224R2`**

All P0–P8 gates pass with exact source parity for the new team-scoped summary, full attention
scroll, independent AS21/local status filters, and the deferred A224 usability checks.

**Recommendation:**
- Freeze checkpoint `checkpoint/v4-ui-usability-green-a224r2` on `dbd829d`.
- Next owner phase = **visual design system + slide-derived page backgrounds**.
- Do NOT start Learning Reviewer yet.

## Services left running

- agent 127.0.0.1:8212 (PID 36208 @ dbd829d)
- task-api 127.0.0.1:8241 (PID 26008, system python3 — unchanged code)
- MCP-SWTR 127.0.0.1:3000 (PID 25954)
- vite 5175 [::1] (PID 36357)

## QA artifacts

- `qa_artifacts/qa_224r2_oracle_b.json` — Oracle B (16 logins, union 4428, per-space counts, Kalachanov keys)
- `qa_artifacts/qa_224r2_p1_agent.json` — agent `po.status_report` (COMPLETED, 51.7 s)
- `qa_artifacts/qa_224r2_p2_fresh_agent.json` — fresh backend re-probe (drift proof)
- `qa_artifacts/qa_224r2_p1_allfail.json` — all-member-failure fail-closed (8.0 s)
- `qa_artifacts/qa_224r2_browser/` — P2/P3, P4/P5 (+reprobes/fieldcheck), P6a, P6b2, P6c/P7, P7 overflow probe + screenshots
- `qa_artifacts/qa_224r2_p8_audit.txt` — P8 access-log audit
- QA scripts (untracked, repo root/frontend): `qa_224r2_restart.sh`, `qa_224r2_oracle_b.py`,
  `qa_224r2_aging_oracle.py`, `qa_224r2_p8_audit.py`, `po-agent-platform-v2/frontend/qa_224r2_*.mjs`
