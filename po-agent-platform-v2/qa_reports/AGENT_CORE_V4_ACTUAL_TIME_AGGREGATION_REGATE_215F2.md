# A215F2 — REAL_EMPTY Re-gate (actual time aggregation: sprint/team/release + actual utilization)

**Verdict: `ACTUAL_TIME_AGGREGATION_GREEN_A215F2`**

- **START_HEAD:** `2c42d7604a43b0227368debaa8df4d539adf7b1b`
- **Owner fix under test:** `52cc061` (fix(v4): allow REAL_EMPTY time aggregation completion) + `103ef33` (test: REAL_EMPTY regression), docs `b0d27bf`/`2c42d76`
- **Supersedes:** A215F RED (`cc8b89a`, verdict `ACTUAL_TIME_AGGREGATION_RED_A215F`, defect `RED_COMPLETION_CONTRACT_REAL_EMPTY`)
- **Date:** 2026-09-25
- **Services:** agent 8212 (PID 39686 @ 2c42d76), task-api 8241 (PID 81954), MCP-SWTR 3000 (PID 29268), fresh vite UI 5175 (PID 47416, proxy → 8212), LLM endpoint healthy throughout

---

## A215F defect: CLOSED

**Fix diff (verified):** plugin-only, `time_accounting_aggregate.py` only — exactly the proposed shape:
- `sprint.time_spent` contract: `("sprint_id", "total_hours", "by_member")` → **`("sprint_id", "worklog_count")`**
- `team.time_spent` contract: `("space", "sprint_id", "total_hours", "by_member")` → **`("space", "sprint_id", "worklog_count")`**
- `team.utilization_actual` contract: `("space", "sprint_id", "members", "capacity_policy")` → **`("space", "sprint_id", "worklog_count", "capacity_policy")`**
- `team.utilization_actual` data payload now includes `worklog_count` (was missing).
- All new keys are scalar/dict and non-empty even for zero worklogs → `_nonempty`-safe → deterministic completion reachable in the REAL_EMPTY case.
- No Agent Core/planner/runtime changes; `release.time_spent` contract untouched (already scalar-safe).
- 2 new regression tests: `test_zero_worklog_sprint_is_a_legitimate_source_completion_shape` (all 3 skills, 0h/0 count/empty collections) and `test_time_aggregation_completion_contracts_are_real_empty_safe` (contract shape via registry).

## Phase 1 — focused tests: PASS

- Focused trio (time_accounting_aggregate + time_accounting + batch2): **19/19 passed** (17 A215F + 2 new REAL_EMPTY).
- `tests/test_agent_core_v4*.py tests/test_v4*.py`: **179/179 passed** (177 A215F + 2 new).
- Plugin registry suite (incl. dummy-55 `test_dummy_55_can_be_added_without_agent_core_change`): **13/13 passed**.

## Phase 2 — REAL_EMPTY OLP re-test: 6/6 PASS (defect class closed on all 3 skills)

Fresh oracle (bounded, concurrency 8): OLP-SPRNT-8 still REAL_EMPTY — 69 tasks, **lifetime worklogs 0.0h / 0 entries** (source fact, not outage), period 2026-09-21 → 2026-10-05 (15 cal days).

| Case | Skill | Status | Completion | Turns | Rejected READYs | Data |
|---|---|---|---|---|---|---|
| olp_sprint_1 | sprint.time_spent | COMPLETED | runtime_contract | 5 | 0 | 0h, count=0, all collections empty, task_count=69, REAL_AS21 |
| olp_sprint_2 | sprint.time_spent | COMPLETED | runtime_contract | 5 | 0 | identical |
| olp_team_1 | team.time_spent | COMPLETED | runtime_contract | 4 | 0 | 0h, count=0, by_member=[] |
| olp_team_2 | team.time_spent | COMPLETED | runtime_contract | 4 | 0 | identical |
| olp_util_1 | team.utilization_actual | COMPLETED | runtime_contract | 4 | 0 | 0h, count=0, members=[], capacity 70.65, provenance labels |
| olp_util_2 | team.utilization_actual | COMPLETED | runtime_contract | 4 | 0 | identical |

All spec criteria met: completion (not generic failure), 0 hours, `worklog_count=0`, empty member collections accepted, **no planner loop** (4-5 turns, deterministic `runtime_contract` READY, zero rejections — vs A215F's 8/8 turns with 4-5 rejections). Answers are honest ("69 задач, но ни одна из них не имеет записей о затраченном времени"; "Записей в worklog на данный момент нет").

## Phase 3 — non-empty DMS parity (all 3 skills): 6/6 EXACT

Fresh DMS-SPRNT-3 oracle: 72 tasks, 428.5h / 65 entries in range, period 09-13 → 09-27 (15 cal days), by_member Garanin 72.0 / Semavin 64.0 / Zhdanov 64.0 / Kondratchikova 52.5 / Alekseev 48.0 / Moiseev 48.0 / Agataeva 40.0 / Galtsov 40.0.

- `sprint.time_spent` ×2: **EXACT** — sprint_id, period, task_count 72, 428.5h, 65 entries, by_member/by_task/by_type/by_date all identical, `runtime_contract`.
- `team.time_spent` ×2: **EXACT** — current-sprint resolution, 428.5h/65, by_member identical.
- `team.utilization_actual` ×2: **EXACT** — capacity 70.65 (= 15 × 1719.12/365, independently computed), 8/8 per-member math exact (Garanin 101.9% `over_capacity`, no clipping), `numerator_source=REAL_AS21_WORKLOGS`, `denominator_source=OWNER_POLICY`.

A215F values retained exactly (428.5/65/72/70.65) — no parity drift from the fix.

## Phase 4 — release.time_spent SOURCE_CONDITIONAL: retained

"Сколько времени списано по релизу 24Q1 в WMB" → typed `release.time_spent requires authoritative release-to-task membership; the current REAL AS21 source does not expose populated release linkage`. Trajectory bounded (`space.resolve → release.search → release.time_spent`), 0 tenant scans, no 0h fabrication.

## Phase 5 — Browser C (fresh UI): 2/2 PASS

- **C1 (non-empty DMS):** "Сколько времени списано в спринте DMS-SPRNT-3 по DMS" → COMPLETED `runtime_contract`, UI renders the full breakdown (by_type 224.0/64.0/52.5/50.0/38.0, by_date 09-14…09-25, 428.5, members visible), 27.3s.
- **C2 (REAL_EMPTY OLP):** "Сколько времени списано в спринте OLP-SPRNT-8 по OLP" → COMPLETED `runtime_contract`, UI renders honest zero state ("В OLP-SPRNT-8 списано 0 ч по 0 списаниям", task_count 69, empty collections), **no generic failure text**, no fabricated members, 41.9s.
- Both: no generic "не смог безопасно завершить", no stale-source error text, no session/trace id leaks. Screenshots: `qa_215f2_browser_c/`.

## Phase 6 — audit: PASS

Agent log over the full A215F2 session (1134 HTTP lines):
- local factual `GET /api/v1/tasks` reads: **0**
- mutations (POST to swtr-read): **0**
- unscoped tenant-wide scans: **0** (single `task-query` call was space-scoped: `space=WMB&release=<uuid>`, from the release path)
- worklog route calls: **989**, all HTTP 200; bounded per-task fan-out, code-enforced `asyncio.Semaphore(8)`; max 9 completions in any 500 ms window (completion-timestamp clustering artifact, not in-flight count — same as A215F)
- route census: sprint membership ×22 (complete=true), sprint directories ×14, current-sprint ×10, versions ×2 (WMB), 1 scoped task-query, LLM POSTs ×94

## Phase 7 — retained smoke: PASS

- DMS-380 `task.time_spent`: COMPLETED, **48 часов / 6 записей** (route probe: 48.0h, 6 entries, complete=true; A215D truth: Garanin 4×8h 09-04..07 + Semavin 2×8h 09-01/02)
- team.workload: COMPLETED (54 active / 18 completed / 5 unassigned / 2 blocked — live source, blocked = DMS-352/DMS-379)
- team.capacity source-estimate guard: retained — typed fail-closed "active assigned tasks do not expose source-backed estimates"
- release.search: retained — WMB = 24Q1/24Q2/25Q1 (A212 truth)
- dummy-55 plugin extensibility: 13/13 registry suite green

## Non-blocking findings

- **F1:** "Покажи списания времени по задаче DMS-380" routes to `task.time_spent` (aggregate) rather than `task.worklogs` — pre-existing A215D F2 planner-routing quirk; answer is source-accurate (48h/6), worklog route itself verified directly.
- **F2:** utilization answer sometimes omits the member table when empty (OLP) — renders policy + zero total only; data payload carries the full structure. Cosmetic.

## Services left running

UI 5175 (PID 47416, fresh vite, proxy → 8212), agent 8212 (PID 39686 @ 2c42d76), task-api 8241 (PID 81954), MCP-SWTR 3000 (PID 29268).

## Recommendation

**GREEN.** Recommend:
1. Immutable time-aggregation checkpoint (A215D + A215E + A215F2 bundle: task/time-accounting, capacity policy + period normalization, worklog aggregation with REAL_EMPTY-safe contracts).
2. Next: **A215G member time accounting / continuation hardening**, then A216 / Batch 3 QA.
