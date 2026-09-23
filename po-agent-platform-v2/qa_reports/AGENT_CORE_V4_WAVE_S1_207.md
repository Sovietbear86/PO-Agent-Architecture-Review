# AGENT CORE V4 — Wave S1 (sprint-flow + release-search) — QA 207

**Assignment:** 207 — Wave S1 QA (sprint.scope, sprint.velocity, sprint.throughput, sprint.wip, release.search)
**Role:** QA / adversarial + service-operator only (no production edits, no Wave S2)
**START_HEAD:** `88df27ad4df3c3d70f05058495abe72f08970f0b` (branch `feat/core8-real-query-hardening-v2`)
**A206B checkpoint:** frozen at `checkpoint/v4-a206b-green@f7f846d`
**Services (restarted on 88df27a):** UI 5175 [::1] · agent 8212 (PID 64529) · task-api 8241 (PID 64436, system python3) · MCP-SWTR 3000
**Date:** 2026-09-23

---

## VERDICT

### **AGENT_CORE_V4_WAVE_S1_GREEN**

- 4/5 Wave S1 skills fully certified **GREEN** and **source-exact** against live REAL AS21 (sprint.scope, sprint.velocity, sprint.throughput, sprint.wip).
- 1/5 skill (**release.search**) is **SOURCE_CONDITIONAL**: the live version/release directory is down (HTTP 502, proven, pre-existing A204/A205/A206 lineage). The skill is certified at the code/boundary level (bounded adapter, no task-scan, fail-closed) and correctly **fails closed** live — no task-scan fallback, no local reads, no fabrication. Live directory search paths (match / ambiguity / no-match) require the version directory to be restored to exercise end-to-end.
- **No blocking defect.** No blocking regression. No fabrication. Zero local-store reads. No per-space/sprint/release hardcoding.
- **Recommendation:** `FREEZE_WAVE_S1_CHECKPOINT_AND_PROCEED_TO_S2_OWNER_IMPLEMENTATION` — with the scoped note that **release.search live certification is pending version-directory restoration** (re-gate 7A/7B/7C once the source is back).

Verdict is **not** `BLOCKED_BY_PROVEN_SOURCE_OUTAGE` (overall), because 4/5 skills are fully green and the one source-blocked skill fails closed by design (that is the specified SOURCE_CONDITIONAL behavior, not a block on the wave).

---

## Owner Wave S1 delta under test (`8e99679..88df27a`)

| Commit | Change |
|--------|--------|
| `2f110dc` | New registry-discovered plugin `v4_plugins/wave_s1.py` (5 skills) |
| `6a23736` | `adapters/hardened_production_task_api.py` — `search_versions_bounded` (bounded live version directory, **no** task-scan fallback) |
| `91f7e18` | `v4_plugins/core.py` — release.health contract may use release.search |
| `2a7e9ca` | `tests/test_agent_core_v4_wave_s1.py` (144 lines) |

---

## Phase 0 — Diff audit (architecture invariants) — **PASS**

| Invariant | Result |
|-----------|--------|
| New skills are registry-only plugin additions | ✅ `wave_s1.py` registered via plugin registry; no core skill table edit |
| No Agent Core / planner / runtime branch changes | ✅ diff limited to `wave_s1.py`, `core.py` (declarative), adapter, tests |
| No per-space / sprint / release hardcode | ✅ sprint skills are space-agnostic; `_WIP_BACKLOG_TYPES` is a documented generic state set |
| release.search does NOT use `_task_backed_versions` / broad task scan | ✅ uses `search_versions_bounded` → `GET /api/v1/swtr-read/versions` → MCP `search_versions`; 404→`[]`, 502/503→`AS21SourceUnavailable` (fail closed). Legacy `_task_backed_versions` only in the **old** (non-hardened) adapter's `search_versions`, unused by Wave S1 |
| release.health change is declarative only | ✅ `core.py` +12 lines: adds `release.search` to allowed capabilities + clarification guidance; completion contract unchanged |

Live confirmation (P12): release.search issues `GET /api/v1/swtr-read/versions` only (32 calls) — **not** a task scan.

## Phase 1 — Focused tests — **PASS**

| Suite | Result |
|-------|--------|
| `test_agent_core_v4_wave_s1.py` + `test_agent_core_v4_plugin_registry.py` | 19 passed |
| `test_agent_core_v4*.py` + `test_v4*.py` | 137 passed |
| `test_task_api_as21_adapter.py` + `test_domain_models.py` | 52 passed |
| `test_agent_core_v4_plugin_registry.py` (incl dummy-55) | 13 passed (P11) |

## Phase 2 — Fresh REAL AS21 oracle — **BUILT**

| Space | Sprint | total | done | start_at | finish_at | status |
|-------|--------|-------|------|----------|-----------|--------|
| DMS | DMS-SPRNT-3 | 65 | 16 | 2026-09-13T21:00Z | 2026-09-27T21:00Z | IN_PROGRESS |
| OLP | OLP-SPRNT-8 | 65 | 1 | 2026-09-21T21:00Z | 2026-10-05T21:00Z | IN_PROGRESS |

- DMS-SPRNT-3 statusType dist: progress 24 / pause 25 / done 16; unassigned 4 (DMS-421, DMS-389, DMS-104, DMS-166).
- OLP-SPRNT-8 statusType dist: progress 24 / pause 40 / done 1; unassigned 4.
- **Version directory: HTTP 502** for all spaces (DMS/OLP/WMB/STS) — `search_versions` tool outage (A204/A205/A206 lineage).

## Phase 3 — sprint.scope (5x DMS + 3x OLP) — **8/8 EXACT**

Every run executed `sprint.scope` (identity-only did **not** terminate; full metrics present).

| Run | sprint | total | completed | open | undecodable | unassigned | verdict |
|-----|--------|-------|-----------|------|-------------|------------|---------|
| DMS ×5 | DMS-SPRNT-3 | 65 | 16 | 49 | 0 | 4 | EXACT |
| OLP ×3 | OLP-SPRNT-8 | 65 | 1 | 64 | 0 | 4 | EXACT |

65/65 unique task keys each run; source `REAL_AS21`; authoritative sprint dates in the observation.

## Phase 4 — sprint.velocity (5x) — **5/5 EXACT**

- DMS ×3: velocity **16**, unit `tasks/sprint`, `story_points_available=false`.
- OLP ×2: velocity **1** (OLP-3143), unit `tasks/sprint`, `story_points_available=false`.
- Spec "must explicitly state story points are not source-backed": ✅ answer states "Story points источником не подтверждены, метрика — task count" + `story_points_available:false` in data.

## Phase 5 — sprint.throughput (5x) — **5/5 EXACT**

| Run | throughput | unit | elapsed_days | start_at |
|-----|-----------|------|--------------|----------|
| DMS ×3 | **1.682** | `completed_tasks/calendar_day` | 9.511–9.512 | 2026-09-13T21:00Z (authoritative) |
| OLP ×2 | **0.661** | `completed_tasks/calendar_day` | 1.512–1.513 | 2026-09-21T21:00Z |

- Formula `completed / max(1, elapsed_calendar_days)`; `start_at` + `measurement_end` exposed; rounded value matches independent oracle (16/9.511=1.682, 1/1.512=0.661).
- Spec "current-snapshot limitation visible": ✅ data `formula` + `measurement_end` + answer "на текущий момент".

## Phase 6 — sprint.wip (5x) — **5/5 EXACT (spec-correct formula)**

| Run | WIP | total | excluded source states |
|-----|-----|-------|------------------------|
| DMS ×3 | **29** | 65 | `Open` ×19, `Зарегистрирован` ×1 |
| OLP ×2 | **45** | 65 | `Open` ×19 |

- Spec formula = "non-terminal tasks **excluding source backlog/open/todo/registered states**". The agent excludes exactly the source `Open`/`Зарегистрирован` (backlog/open) states: DMS 49 non-terminal − 20 = **29**; OLP 64 − 19 = **45**. Verified key-by-key against live source names.
- `sprint.wip` is a strict subset of `sprint.scope.open` (49/64) — consistent.

## Phase 7 — release.search (7A/7B/7C/7D) — **SOURCE_CONDITIONAL (fail-closed proven)**

Live version directory is 502 (proven, all spaces). All runs loaded `release.search` and **failed closed** with "Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат."

| Case | Query | Result |
|------|-------|--------|
| 7A | "найди релизы DMS" ×2 | FAILED fail-closed (source 502) |
| 7B | ambiguity | **N/A** — directory down, cannot exercise |
| 7C | "найди релиз TestRelease12345 в DMS" | FAILED fail-closed (source 502) |
| 7D | unavailable | FAILED fail-closed — **correct** specified behavior |

- No task-scan, no local reads, no fabrication, no synthesized version directory. Bounded-adapter + fail-closed behavior certified at the code/boundary level (P0/P1) and confirmed live.
- **Re-gate 7A/7B/7C when the version directory is restored.**

## Phase 8 — release.health hand-off — **fail-closed (correct)**

- "здоровье релиза по DMS" ×2 → FAILED fail-closed (release.search→versions 502).
- Correctly did **not** bind the product space `DMS` as a release id (the A204-4 boundary is retained); the new `release.search` hand-off path was attempted and failed closed on the source outage.

## Phase 9 — Browser C (real UI via Playwright, vite 5175 → agent 8212) — **5/5 GREEN**

| Case | status | panel | stale-text | skills |
|------|--------|-------|-----------|--------|
| C1 scope DMS | COMPLETED | ✅ | false | sprints.discover, sprint.scope |
| C2 velocity DMS | COMPLETED | ✅ | false | sprints.discover, sprint.velocity |
| C3 WIP DMS | COMPLETED | ✅ | false | sprints.discover, sprint.wip |
| C4 release.search DMS | FAILED (fail-closed) | ✅ | false | release.search |
| C5 lookup DMS-380 | COMPLETED | ✅ | false | task.lookup |

Rendered answers are source-exact (65/16/49/4; 16 tasks/sprint "Story points не подтверждены"; WIP 29; DMS-380 Closed). Frontend `tsc --noEmit` clean. No stale "AS21 вернул некорректные данные" text.

> **Harness note (QA-side, not a product defect):** the first Browser C run showed a false 5/5 NEEDS_CLARIFICATION. Root cause: `OverviewDashboard.tsx` auto-fires 4 `useHarness` queries (`Дай обзор и риски`, `Покажи очередь внимания`, `Сделай daily brief`, `Сделай status report`) on every page mount, and the naive `waitForResponse` captured **those** (each legitimately ambiguous) instead of the test query. Fixed by matching the response to the request whose POST body carries the exact test query. See F4.

## Phase 10 — Retained regression — **GREEN**

| Probe | Result |
|-------|--------|
| DMS-380 lookup | ✅ COMPLETED, status Закрыт(Closed), assignee Семавин, component dmts |
| Person "Открытые задачи Александра Жданова в DMS" | ✅ COMPLETED, **2** open = DMS-371, DMS-1 — **EXACT** vs live ground truth (drift from A206B 7-8: DMS-103/154/6/69/71 since closed) |
| Sprint health DMS | ✅ COMPLETED, 65 total / 16 done / real in-work+blocked metrics (A204-1 retained) |
| Same-session "этот спринт" (2-turn) | ✅ t1 65 tasks; t2 inherited `sprint_id=DMS-SPRNT-3,space=DMS` from session context (D-A204-3/A205R retained) — but status-name filter returned 0 (see F2) |
| Multi-hop clarification continuation | ✅ 2/2 TRUE continuation on re-run (7/7 tasks, runtime_contract); 1/10 LLM flake in e2e (fail-closed, see F3) |
| Unassigned OLP-SPRNT-8 | ✅ COMPLETED, 4 = OLP-3333, OLP-3143, OLP-3155, OLP-3129 |
| task.history DMS-380 | ✅ 4 transitions, source labels intact (A206B retained) |
| task.time_in_status DMS-380 | ✅ 4 intervals, terminal closure not extended to now (Тестирование 255.18h) |
| task.search_attachments WMB-30000 | ✅ 5 Excel files (A193 truth retained) |
| Status search "Открытые задачи в DMS" | ✅ 87 open (live drift) |

## Phase 11 — dummy-55 / plugin invariant — **13/13 PASS**

## Phase 12 — Source / local / perf audit — **PASS**

- **Local store reads: 0** (`GET /api/v1/tasks` non-swtr = 0). No local-truth fabrication.
- **Source calls: all bounded & scoped** — `sprints/{id}/tasks?complete=true` (bounded A185-B1 loop), `spaces/{space}/sprints` (metadata), `versions` (release dir, no task-scan), `task-query`, `assignee-tasks`, `assignees/resolve`, per-task `history`/`files`. **No tenant-wide task scan.**
- release.search → `/versions` only (32 calls), confirming the bounded adapter is used live.
- Perf: sprint skills complete in 13–96s (LLM-bound); source reads bounded. No unscoped `/health` hang observed on the V4 query path this run.

---

## Findings (all non-blocking)

- **F1 — capability `warnings` dropped at the API boundary (observability gap).** Wave S1 plugins emit `warnings=["velocity_unit_tasks_not_story_points"]` / `warnings=["throughput_is_current_snapshot_rate"]` on `CapabilityResult`, but the V4 core builds its own `HarnessResponse.warnings` list and does **not** merge `CapabilityResult.warnings` → the API top-level `warnings` is `[]`. The spec's *"explicitly state"* requirement **is** met via the answer text + data (`story_points_available:false`, `formula`, `measurement_end`), so this is a structured-warnings observability gap, not a correctness defect. Pre-existing core behavior (not introduced by Wave S1).
- **F2 — raw source status-name filter returns 0 (pre-existing boundary).** Same-session t2 "задач в статусе На исправлении" returned 0 while the live source has 1 (DMS-399). `task.search`'s free-text status branch matches only `not_completed`/`completed`/normalized-`TaskStatus`-enum values; a raw source name that maps to `TaskStatus.UNKNOWN` matches nothing. Capability contract states only `not_completed` is supported. Pre-existing (A192 lineage); `task.search` unchanged in the Wave S1 diff.
- **F3 — multi-hop clarification LLM flake (1/10, fail-closed).** One e2e multi-hop run FAILED with `planner failed robust bounded repair` (ValidationError/invalid_recovery_action); 2/2 re-runs were TRUE continuations (7/7 exact). Known Qwen3.8 endpoint flakiness (A179/F3 lineage). Fail-closed, no fabrication.
- **F4 — OverviewDashboard auto-fires 4 `useHarness` queries on every page mount** (`Дай обзор и риски`, `Покажи очередь внимания`, `Сделай daily brief`, `Сделай status report`), each legitimately ambiguous → NEEDS_CLARIFICATION. Pre-existing UI behavior (not Wave S1). It caused the initial Browser C harness false-negative; the harness was fixed to match on the test query text. Worth an owner review of dashboard auto-query cost/noise.

---

## Scope guard

- **No Wave S2** started. **No new skills** added. **No production code / plugin / test / config / frontend edits** by QA.
- Committed and pushed: **only** this QA report file.
- Services left running for the next phase.
