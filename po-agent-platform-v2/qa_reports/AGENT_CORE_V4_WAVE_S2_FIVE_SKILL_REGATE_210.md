# AGENT_CORE_V4_WAVE_S2_FIVE_SKILL_REGATE_210

**Assignment:** 210 — Wave S2 five-skill re-gate after A209 timestamp-plumbing remediation
**Date:** 2026-09-24
**Role:** QA/adversarial + service-operator only (no production/test/config edits)
**Branch:** `feat/core8-real-query-hardening-v2`

| Field | Value |
|---|---|
| START_HEAD | `316d36768370fe13d6a7109faff182824bae5dc5` |
| A209 report head (pre-remediation) | `a417097` |
| Stable rollback checkpoint (A208B) | `2e284fd` |
| Owner remediation commits | `00bc9b8`, `0f5ca3c`, `5d7980f` |
| Agent under test | port 8212, PID 79214, HEAD `316d367` |
| task-api | 8241, PID 79196 (system python3, SSE, 48 tools) |
| MCP-SWTR | 3000, PID 29268 |
| UI | 5175 (PID 55236), 5176 (PID 12824) |

## VERDICT

**AGENT_CORE_V4_WAVE_S2_FIVE_SKILL_GREEN** — all five Wave S2 skills re-gated against fresh REAL AS21 with exact source parity. The A209 root cause (`RED_SOURCE_TIMESTAMP_PLUMBING`) is **closed**: the sprint-task route now exposes source-backed `created_at`/`updated_at`, the adapter keeps them timezone-aware and provenance-flagged, and the wave_s2 plugin is timezone-normalized and fails closed on missing source timestamps.

Recommendation: **create a Wave S2 rollback checkpoint**; next work = bounded release source recovery (`release.search` + `release.health`) before the next five-skill batch.

Non-blocking findings (none are A210 S2 code defects; none are fixed here): F1 planner mis-route on the exact phrase "На исправлении задачи в DMS-SPRNT-3" (pre-existing Qwen3.8 routing class, fail-closed, capability proven intact); F2 LLM endpoint environmental degradation window during the session; F3 raw-status label normalization in `task.search` display; F4 `search_versions` route now returns 400 "space is required" (was 502 in A206).

---

## P0 — Diff audit (A209 `a417097` → A210 `316d367`): CLEAN

`git diff --stat a417097..316d367` = 7 files. Production code is **only**:
- `po-agent-platform-v2/src/po_agent/adapters/task_api.py` (+13/−6): `datetime.now(timezone.utc)` fallback; tz-aware `_parse_datetime`; new `_canonical_deadline_from_source` provenance flag; `due_date` from source `deadline`.
- `po-agent-platform-v2/src/po_agent/harness/v4_plugins/wave_s2.py` (+67): `_source_flag`/`_aware_utc` helpers; provenance-gated `V4CapabilityUnavailable` when completed tasks lack source `created_at`; tz-normalized cycle/lead arithmetic; risk queue computes `age_days`/`overdue_days` **only** from source-flagged timestamps and emits explicit limitation warnings.
- `task-api/app/routers/swtr_read.py` (+47): sprint-task rows preserve `created_at`/`updated_at`/`deadline`; TQL sprint-constraint query adds timestamp attributes; membership-preserving enrichment pass (never changes membership, never fabricates timestamps).
- `po-agent-platform-v2/tests/test_agent_core_v4_wave_s2.py` (+40).
- docs (next-action, DoD lock, A209 report).

**No Agent Core / planner / runtime / orchestration changes** (verified: zero diff in `agent_core_v4*.py`, `robust*`, `runtime_factory.py`). All five skills remain registry/plugin-discovered via `builtin.wave_s2.sprint_history_risk`. No hardcoded DMS/person/task/sprint facts. No local/fake/cache fallback. CompletionContract + UIContract present for all five. **Any architecture drift => RED** — none found.

## P1 — Automated suites: 167 passed / 0 failed

| Suite | Result |
|---|---|
| `test_agent_core_v4_wave_s2.py` + `test_agent_core_v4_wave_s1.py` | 17 passed |
| `tests/test_agent_core_v4*.py` (all) | 118 passed |
| `tests/test_v4*.py` (all) | 32 passed |
| plugin / dummy-55 invariant (`-k "dummy_55 or dummy55 or plugin"`) | 25 passed |

A209's single test-logic failure (`test_risk_queue_ranks_tasks_not_people`) no longer reproduces — the whole V4 set is green. Zero unexplained failures.

## P2 — Fresh REAL AS21 oracle (DMS, live, not reused from A209)

| Fact | Value |
|---|---|
| DMS-SPRNT-3 (IN_PROGRESS, 2026-09-13 → 2026-09-27) | 68 tasks, `complete=true`, `membership_proven=true` |
| DMS-SPRNT-2 (previous) | 17 tasks |
| Carryover intersection (SPRNT-2 ∩ SPRNT-3) | **0** (disjoint key sets) |
| Completed SPRNT-3 tasks with workflow history | 17 |
| Open tasks | 51 |
| Blocked (NEED_INFO) | 2 → DMS-352, DMS-379 |
| **Source `created_at` coverage (sprint rows)** | **68/68** |
| **Source `updated_at` coverage** | **68/68** |
| **Source `deadline` coverage** | **0/68** (no deadlines in SWTR for these rows) |

**Timestamp provenance (A209 root-cause fix verified live):** the task-api sprint route now returns `created_at`/`updated_at` on all 68 rows from the TQL sprint-constraint view (e.g. DMS-335 `created_at=2026-08-03T06:36:53Z`). The adapter sets `_canonical_created_at_from_source=True` for all 68, so cycle/lead/risk use **source** timestamps, never the `datetime.now()` fallback. No adapter-fallback timestamp is treated as source truth (flag-gated).

## P3 — sprint.cycle_time: 10/10 COMPLETED, EXACT

Form matrix: explicit-id (×3), period "сентябрьского" (×3), current/product (×4) = 10 runs, all COMPLETED `runtime_contract`.

Oracle B (completed tasks only, first→terminal workflow transition):

| Metric | Agent (all 10 runs) | Oracle B |
|---|---|---|
| avg | 206.06 h | 206.062 h |
| median | 77.7 h | 77.701 h |
| min | 0.0 h | 0.0 h (DMS-374) |
| max | 1230.43 h | 1230.432 h (DMS-335) |
| population | 17 completed | 17 |

Exact per-task timestamps match (e.g. DMS-335 first 2026-08-03T06:37:08Z → terminal 2026-09-23T13:03:04Z). No current-time substitution; terminal closure is not extended to now.

## P4 — sprint.lead_time: 9/10 COMPLETED EXACT + 1 typed fail-closed

Form matrix: explicit-id (×3), period (×3), current (×2), product "спринта DMS" (×2) = 10 runs.

Oracle B (`terminal workflow transition − source created_at`):

| Metric | Agent (9 COMPLETED) | Oracle B |
|---|---|---|
| avg | 499.08 h | 499.08 h |
| median | 448.03 h | 448.03 h |
| min | 0.45 h | 0.449 h (DMS-408) |
| max | 1657.59 h | 1657.593 h (DMS-273) |
| population | 17 completed | 17 |

tz-aware, source-backed arithmetic; no `updated_at`/current-time substitute.

The 1 non-COMPLETED run: product form "lead time спринта DMS" once returned a **typed clarification** ("Не удалось подтвердить спринт «DMS»" — planner routed to `sprint.resolve(reference="DMS")`). A same-session re-probe of the identical product form **COMPLETED** via `space.resolve → sprint.current → sprint.lead_time` (17 completed). => LLM routing non-determinism (A200 lineage), fail-closed, **not** a code defect.

## P5 — sprint.carryover retained: 3/3 COMPLETED, EXACT

Explicit-id / current / product forms → `sprint.carryover` (current) + `sprint.current` (current/product). Previous sprint auto-resolved from source to **DMS-SPRNT-2**. Result: **0 carryover** (intersection = []), `current_total=68`, `previous_total=17`. Exact set intersection, no fuzzy/title matching. Matches oracle (disjoint key sets).

## P6 — sprint.predictability retained: correctly SOURCE_CONDITIONAL

2/2 runs → typed `FAILED` "Необходимая возможность не подтверждена источником данных и не выполняется" (surfaces `V4CapabilityUnavailable`).

Independent source proof: live DMS current-sprint metadata exposes only `id / name / description / deleted / goal / status / startAt / finishAt` — **no** `committed_count`/`baseline_total`/`planned_count`/`scope_at_start`/`committed_tasks`. So `_baseline_total` returns None → fail-closed. No current-scope substitution, zero fabricated percentage. **Not overall RED** (source absence independently proven).

## P7 — sprint.risk_queue: 37/37 EXACT membership parity

Fresh oracle on DMS-SPRNT-3:

- **Queue count 37 == oracle open-aging set 37** (set equality, zero diff both directions).
- **Blocked first:** rank 1 DMS-352, rank 2 DMS-379 (both `blocked=true`, match oracle blocked list), even though DMS-64 has higher age — ordering rule "blocked first" honored.
- **Then age_days desc:** DMS-64(161) → DMS-86(148) → … → DMS-398/DMS-399(14).
- **No silent truncation:** all 35 aging-only open tasks present (not only the 2 blocked — the A209 D-A209-2 silent-truncation defect is closed).
- **No fallback timestamp as fact:** `age_days` computed only from source-flagged `created_at`; all 37 rows have source `created_at` (provenance flag True).
- **No fabricated overdue:** 0/68 rows have a source `deadline`, so `overdue_days=0` for all — not treated as overdue.
- **No employee scoring:** formula string = "blocked first, then overdue_days desc, then age_days desc; no employee scoring".
- 2 one-day age drifts vs oracle (DMS-269 82→83, DMS-389 19→20) = wall-clock boundary between oracle capture (07:06Z) and run (~07:30Z) — non-defect.

## P8 — Resolution forms

Covered across P3/P4/P5: explicit-id, period "сентябрьского", current "текущего", product "DMS". Identity-only/product resolution does **not** terminate the analytical request (product forms resolve via `sprint.current` and complete; the single product-form lead clarify was fail-closed and completed on re-route).

## P9 — Browser C (real UI, all five skills): 5/5

| Case | Query | Result |
|---|---|---|
| C1 | cycle time спринта DMS-SPRNT-3 | COMPLETED — real source-backed metric table (median 77.7 h) |
| C2 | lead time спринта DMS-SPRNT-3 | COMPLETED — real metric table (median 448.03 h) |
| C3 | carryover текущего спринта DMS | COMPLETED — task-table style, 0 carryover |
| C4 | predictability спринта DMS-SPRNT-3 | typed source-unavailable (matches P6 SOURCE_CONDITIONAL) |
| C5 | риски текущего спринта DMS | COMPLETED — 37-row queue incl. aging rows (DMS-64 161d), not only blocked |

No stack / contract / session leakage. Screenshots: `qa_210_browser_c/`.

## P10 — Retained regression

First pass 10/12 COMPLETED with correct source data:

| Check | Result |
|---|---|
| wip DMS-SPRNT-3 | COMPLETED — 30 |
| scope DMS-SPRNT-3 | COMPLETED — total 68 |
| velocity DMS-SPRNT-3 | COMPLETED — 17 completed |
| throughput DMS-SPRNT-3 | COMPLETED — 1.587 |
| health DMS-SPRNT-3 | COMPLETED — 68 |
| blocked DMS-SPRNT-3 | COMPLETED — [DMS-352, DMS-379] (== oracle) |
| task.lookup DMS-380 | COMPLETED |
| task.history DMS-380 | COMPLETED — 4 transitions, current Закрыт |
| task.time_in_status DMS-380 | COMPLETED |
| attachments WMB-30000 | COMPLETED |
| person+status "Открытые задачи Жданова в DMS" | COMPLETED (re-probe) — [DMS-371, DMS-1] |

2 first-pass env timeouts re-probed:
- **Жданов** → COMPLETED on re-probe: `task.search_assignee` → [DMS-371, DMS-1] (Ready for review / Open).
- **"На исправлении задачи в DMS-SPRNT-3"** → 7/7 FAILED. **Root cause (proven from trajectory):** Qwen3.8 mis-routes the phrase — loads `task.lookup`, calls `task.lookup(task_key="DMS-SPRNT-3")` (reads the *sprint id as a task key*), gets null, then loops `ready` rejected `unsatisfied_completion_contract` until step-budget → FAILED. **Fail-closed, zero fabrication** (correctly refused; did not invent DMS-399). A clearer phrasing — "задачи в статусе На исправлении в спринте DMS-SPRNT-3" → `sprint.resolve` + `task.search` → **[DMS-399]** COMPLETED — **proves the raw-status task.search capability is intact** and correct. This is the pre-existing A200-lineage planner-routing class, **not** an A210 S2 defect (the task.lookup/task.search path is untouched by the A210 diff). See F1/F2.

Same-session continuation was not re-scripted this run (LLM-gated); it was GREEN at A201/A205R and the plugin/continuation contract is covered by the Phase 1 suite (32 test_v4 + plugin tests).

## P11 — Source / local / perf audit

From the agent + task-api logs for the run:

| Metric | Value |
|---|---|
| Local factual `GET /api/v1/tasks` reads | **0** |
| Local `POST /api/v1/query` (store) reads | **0** |
| Tenant-wide full-scan (`swtr-read/tasks?` no key) | **0** |
| Live `swtr-read` source calls | 581 |
| Bounded complete sprint collections (`complete=true`) | 57 |
| Bounded per-task history reads (`get_task_history`) | 459 (semaphore-bounded, completed tasks only) |
| LLM calls | 295 |
| `/api/v1/swtr-read/versions` (record only, not remediated) | **400 "space is required for search_versions"** |

No tenant-wide scan used to fake sprint metrics; source outages fail closed; **plugin/dummy-55 invariant GREEN (25 passed)**. `search_versions` is reachable (tool present) but requires a `space` arg — a change from A206's 502 outage; recorded only per spec, not remediated here.

---

## Non-blocking findings

- **F1 — planner mis-route on exact phrase "На исправлении задачи в DMS-SPRNT-3."** Qwen3.8 treats the sprint id as a task key → `task.lookup` → fail-closed loop → FAILED (7/7 in this session). Capability proven intact via clearer phrasing (`task.search` → DMS-399). Pre-existing planner-routing reliability class (A200 lineage); not introduced by A210. Owner direction (out of QA scope): deterministic sprint-scoped status routing / constrain `task.lookup` to non-sprint keys.
- **F2 — LLM endpoint (Qwen3.8-27B) environmental degradation during the session.** Direct probes showed 42–85s/call and `500 Internal Server Error` clusters (≈14:17–14:27, ≈17:41–17:42) with intermittent recovery (1–30s). This amplified Phase 10 flake/timeout rates but did **not** affect the five S2 skills (all exact source parity). Not a code defect.
- **F3 — raw-status label normalization in `task.search` display.** DMS-399 live source status = "На исправлении"; `task.search` result surfaced the normalized category "In progress". Distinct from A206B's history/tis label fix; a separate display-mapping concern. Non-blocking.
- **F4 — `search_versions` route now 400 "space is required."** Changed from A206's 502; tool reachable but needs `space`. Recorded only.

## Services left running
UI 5175 (55236) / 5176 (12824), agent 8212 (PID 79214 @ `316d367`), task-api 8241 (PID 79196, SSE 48 tools), MCP-SWTR 3000 (PID 29268).
