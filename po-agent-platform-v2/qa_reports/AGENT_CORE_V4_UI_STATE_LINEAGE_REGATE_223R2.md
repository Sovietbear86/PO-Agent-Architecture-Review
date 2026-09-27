# A223R2 — Sprint Widget Field Re-gate

**Date:** 2026-09-27
**START_HEAD:** `970f15f` (owner A223R2 fix)
**A223R report base:** `995d607` (AGENT_CORE_V4_UI_STATE_LINEAGE_RED_A223R)
**Backend frozen at:** `17fdacb` (A222R2 GREEN) — unchanged, agent PID 29982
**Branch:** `feat/core8-real-query-hardening-v2`
**Verdict:** `AGENT_CORE_V4_UI_STATE_LINEAGE_GREEN_A223R2`

---

## Scope

Owner fix `b069550` (SprintPage only) closing the A223R blockers:
- `rd.risks` → `rd.queue`
- `row.key` → `row.task_key`, `row.risk_score` → `row.rank`
- `td.throughput_tasks` → `td.throughput`

Production delta (995d607..970f15f) = **`Pages.tsx` only** (SprintPage leaf accessors). 2 docs + 0 backend/Core/planner/runtime/session. ✓

Services: agent 8212 (PID 29982 @ 17fdacb), task-api 8241 (48 tools, connected), MCP 3000, fresh vite 5175 (PID 98030, [::1]).

---

## P0 — static/build — GREEN

| Check | Result |
|-------|--------|
| production delta SprintPage-only | ✓ (`Pages.tsx` only) |
| `tsc --noEmit` | GREEN (exit 0) |
| `vite build` | GREEN (100 modules, exit 0) |

---

## P1 — blocking Sprint re-gate (DMS-SPRNT-3) — GREEN, A223R blockers CLOSED

Backend source (independent, unchanged from A223R): health `total=73/completed=19/blocked=2/26%`, velocity `19 tasks/sprint`, throughput `1.385 completed_tasks/calendar_day`, WIP `31`, risks `count=38` / `queue`=[38 rows] (`{task_key,title,status,assignee,blocked,overdue_days,age_days,reasons,rank}`).

**Browser C (fresh frontend):**

| Metric | Rendered | Source | |
|--------|----------|--------|---|
| Scope | **73** | 73 | ✓ |
| Completed | **19** | 19 | ✓ |
| Velocity | **19 tasks/sprint** | 19 | ✓ |
| Predictability | **—** | `v4_capability_unavailable` (SC) | ✓ |
| WIP (insight) | **31** | 31 | ✓ |
| Готовность (insight) | **26%** | 26.0 | ✓ |
| **Throughput (insight)** | **1.385** | 1.385 | ✓ (was "—" in A223R) |
| **Risk Queue title** | **38** | count=38 | ✓ |
| **Risk Queue body** | **38 rows** | queue=[38] | ✓ |

**Risk rows render real source fields** (no contradiction): `DMS-352 · Заполнение карточки DataMarts в Karma · blocked, aging:38d · rank 1`, `DMS-379 · [doc] API healthcheck · blocked, aging:25d · rank 2`, `DMS-64 · … · aging:165d · rank 3`, `DMS-86 · … · aging:152d · rank 4`. muted = **null** (NO "риски не выявлены" while count=38).

**D-A223R-1 (risk queue) and D-A223R-2 (throughput) from A223R are CLOSED.** 0 NaN. Exact parity with the captured backend capData (`throughput=1.385`, `count=38`, `queue_len=38`).

---

## P2 — Sprint regression — GREEN

| Case | Result | |
|------|--------|---|
| Non-empty risk sprint (DMS-SPRNT-3) | 38 rows, count=38, stays non-empty | ✓ |
| **Source-proven empty risk sprint (WMB-SPRNT-2)** | count=**0**, 0 rows, queue=[] COMPLETED → "риски не выявлены" shown **only** because source proves zero (correct REAL_EMPTY); cards Scope 1 / Completed 1 / Velocity 1 tasks/sprint | ✓ |
| Source-limited case (DMS-SPRNT-3 predictability) | `v4_capability_unavailable` → "—", not 0/no-risks | ✓ |
| health/WIP/velocity unchanged | 73/19, 31, 19 tasks/sprint | ✓ |

"риски не выявлены" appears **only** when the source proves count=0 (WMB-SPRNT-2), never when count>0 (DMS-SPRNT-3).

---

## P3 — finish retained UI gate (P5–P8 from A223R on new code) — GREEN

### Releases (P5)
OLP 1.6.0 (source-conditional): all 5 backend queries `FAILED v4_capability_unavailable` → **3 SOURCE_UNAVAILABLE state panels**, all 4 metric cards **"—"** (Scope/Completed/Blocked/Готовность), `muted=[]`. No fake 0/empty, no "none" blockers, no 0/0 dependencies, no pseudo-forecast. ✓

### Team (P6)
- All 4 metric cards **"—"** including **Capacity baseline = "—" (not 40h)**; 2 NEEDS_CLARIFICATION panels (bare team queries → `v4_ready_without_source_observation`, pre-existing LLM space-ambiguity on frozen backend). No '40' in any card value.
- Competency note retained in source (`Competency match и рекомендация исполнителя SOURCE_READY…`).
- Field mapping for scoped data verified (unchanged `TeamDashboard.tsx`): scoped `Покажи нагрузку команды DMS` → `workload:[{member,active_tasks,wip,blocked,completed}]` = exactly the fields the UI reads. (Team page sends bare queries, so scoped rows aren't shown in the UI — pre-existing UI scoping limitation, non-blocking.)

### Tasks (P7)
- **list-mode non-empty (sprint DMS-SPRNT-3):** **73 task cards** rendered from the unwrapped `tasks` array (backend parity `tasks_len=73`, `task_keys_len=73`). Sample: `DMS-415/Resolved/…`, `DMS-434/Open/…Моисеев Андрей Н`, `DMS-357/In progress/…`. ✓
- **clarification (Найди login):** NEEDS_CLARIFICATION state panel, 0 cards. ✓
- **typed-empty (Найди zzzqqqxyz123):** typed **ERROR** panel (fail-closed), 0 cards, no fake grid. ✓
- (single-key `Найди <key>` → `task.lookup` single `task` vs grid `data.tasks` remains the acknowledged non-blocking UX finding.)

### Chat (P8)
- **daily brief:** 0 raw-markdown (##/**/|---|), 2 tables, 4 headings, evidence + feedback present. ✓
- **competency (DMS-380):** 0 raw-markdown, 1 table, evidence + feedback present. ✓

---

## P4 — compact Quality smoke (WMB-102) — GREEN

| Metric | Rendered | |
|--------|----------|---|
| Quality score | **85/100** | ✓ |
| Acceptance | **0/100** | ✓ |
| Пробелы | **1** | ✓ |
| Решение PO | **REWORK** / «Вернуть на доработку» | ✓ |
| NaN | **0** | ✓ |

Absent-score control (WMB-999999) → all "—", NOT RUN, 0 NaN. Retained from A223R.

---

## P9 — audit

task-api log delta from baseline 14361 (248 lines during the gate; +248 from the final repro probes):

| Check | Count |
|-------|-------|
| Mutations (POST/PUT/DELETE to swtr) | **0** |
| Local factual fallback reads (`GET /api/v1/tasks` non-swtr) | **0** |
| ×500 (source errors) | 0 (agent-side) — see F-A223R2-1 for 2 502 task-queries |
| SprintPage (under test) source calls | all `sprints/DMS-SPRNT-3/tasks` / `sprints/WMB-SPRNT-2/tasks` — **space-scoped, 0 unscoped** |

**F-A223R2-1 (non-blocking, pre-existing):** 2 bare `task-query?limit=100&max_pages=100` (no space, no assignee) attempts occurred (task-api lines 14468/14469, back-to-back), both **502 Bad Gateway** (fail-closed, no data returned). Root cause forensics:
- They are immediately preceded by a **portfolio-wide all-spaces burst** (current-sprint + sprint-tasks across WMB/STS/OLP/DMS) — the signature of a portfolio PO capability (daily brief / status report / attention queue).
- Targeted repro did NOT reproduce it: Overview page loaded 3× → **0** bare task-query; direct probes of `Дай обзор и риски` / `Покажи очередь внимания` / `Сделай daily brief` / `Сделай status report` / all 6 bare team queries / `Найди …` → **0** bare task-query each.
- ⇒ A **rare LLM-nondeterministic** extra bare scan issued by a portfolio PO capability; **fail-closed (502)**, no data, no mutation.
- **Not introduced by the A223R2 change:** the production delta is SprintPage-only (read-only field accessors on already-fetched capability data) and its source calls were exclusively space-scoped `sprints/{id}/tasks`. The SprintPage change cannot affect which source calls a portfolio PO capability makes.

This is a **pre-existing latent tenant-wide-scan attempt** in the portfolio PO path (frozen backend 17fdacb), surfaced by LLM non-determinism, and fail-closed. It does not meet the P9 "introduced by UI [change]" bar. **Owner recommendation (separate, out of A223R2 scope):** harden portfolio PO capabilities so a bare `task-query` (no space/assignee) is never attempted — scope it to approved-product current sprints or fail-closed without the source attempt.

---

## Findings summary

| ID | Severity | Description |
|----|----------|-------------|
| **D-A223R-1 / D-A223R-2** | **CLOSED** | A223R sprint risk-queue + throughput field mismatches — fixed by `b069550`, verified GREEN (38 rows, throughput 1.385, no contradiction). |
| F-A223R2-1 | Non-blocking (pre-existing) | 2 bare `task-query` (no space/assignee) 502'd during a portfolio PO query — rare LLM-nondeterministic, fail-closed, NOT introduced by the SprintPage change. |
| F-A223R2-2 | Non-blocking (pre-existing) | Team page sends bare (space-less) team queries → NEEDS_CLARIFICATION; scoped rows verified correct at the capability level. |
| F-A223R2-3 | Non-blocking (pre-existing) | Single-key `Найди <key>` → `task.lookup` single `task` vs grid `data.tasks` (list modes render correctly, 73 cards). |

All A223R2-specific gates (P0, P1 blocking, P2, P3/P5, P3/P6, P3/P7, P3/P8, P4) are **GREEN**. No RED boundary found.

---

## Verdict

**`AGENT_CORE_V4_UI_STATE_LINEAGE_GREEN_A223R2`**

The A223R blockers are closed: Sprint DMS-SPRNT-3 now shows throughput **1.385** (not "—") and a risk queue with **count 38 = 38 rendered rows** by `task_key`/`reasons`/`rank` (no "38 рисков / риски не выявлены" contradiction). All retained UI gates (Releases SC, Team no-40h, Tasks list-mode 73 cards, Chat 0-raw-MD) and the Quality WMB-102 smoke (85/100, 0/100, 1, REWORK, 0 NaN) are GREEN. Audit clean for the change (0 mutations, 0 local fallback, SprintPage 0 unscoped). One pre-existing, fail-closed, non-introduced finding (F-A223R2-1) documented.

**Recommendation:** checkpoint `v4-ui-state-lineage-green-a223r2`. Next owner phase = visual design system + slide-derived page backgrounds. Do NOT start Learning Reviewer yet. (Separate owner item: F-A223R2-1 portfolio bare `task-query` hardening.)

**Preserved artifacts:** `qa_artifacts/a223r2_sprint.json` (P1/P2 capData + DOM), `qa_artifacts/a223r2_pages.json` (P5/P6/P7/P8), `qa_artifacts/a223r_p2_quality.json` (P4 smoke re-run), screenshots `qa_223r2_browser_c/{p1_dms3,p2_wmb2,p5_release_olp160,p6_team,p7_tasks_sprint,p7_tasks_clarify,p7_tasks_typed_empty,chat__daily_brief,chat__DMS-380}.png`.

**Services left running:** agent 8212 (PID 29982 @ 17fdacb), task-api 8241, MCP 3000, vite 5175 (PID 98030, [::1]).
