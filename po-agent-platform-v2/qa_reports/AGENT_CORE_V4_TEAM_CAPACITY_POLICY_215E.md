# A215E — team.capacity Owner 2026 Capacity Policy Gate

**Verdict:** `TEAM_CAPACITY_POLICY_GREEN_A215E`

**START_HEAD:** `0093adebba4bdd8e6bdad3a063f421e8a7d675b8`
**Role:** QA/adversarial tester only. No production code modified.
**Date:** 2026-09-25

---

## Owner implementation (3 commits)
- `b2435d4` — `harness/capacity_policy.py`: new standalone policy module (247 RU 2026 working days, 0.87 availability factor, 40h week ⇒ 8h day, 143.26h/month/person default, `source=OWNER_POLICY`).
- `db12bde` — `v4_plugins/wave_batch2.py`: `team.capacity` now applies the policy default **only after** the source-estimate guard; explicit user baseline still overrides.
- `1e1ccf6` — `tests/test_agent_core_v4_batch2.py`: owner 2026 capacity baseline coverage (also fixed the A215B F1 fixture artifact).

## Phase 0 — architecture invariant: PASS
- Diff `5e641bd..0093ade` (src+tests+task-api) = exactly `capacity_policy.py` (+44), `wave_batch2.py` (+27/−17), `test_agent_core_v4_batch2.py` (+21/−5) + docs. **No Agent Core / planner / runtime change.**
- Policy lives outside Agent Core (standalone `capacity_policy.py`, imported only by the `wave_batch2` plugin).
- Batch 2 remains plugin-owned; dummy-55 / plugin-registry tests 13/13.

## Phase 1 — formula + metadata: GREEN
- Independent verification: 247/12 = 20.583333… × 0.87 = 17.9075 × 8h = **143.26h/person/month** (round 2dp).
- `default_monthly_capacity()` exposes all required fields: `working_days_2026=247`, `availability_factor=0.87`, `weekly_hours=40.0`, `daily_hours=8.0`, `available_working_days_per_month=17.9075`, `available_capacity_hours_per_month=143.26`, `source=OWNER_POLICY`, `policy_id=RU_2026_AVG_WORKDAYS_X_0_87_40H_WEEK`.
- All V4 suites: **172 passed / 0 failed** (A215B known test-logic artifact now fixed by owner).

## Phase 2 — source-estimate guard on live DMS: GREEN
Under current REAL AS21 DMS (active assigned task estimates not source-backed), both cases terminate terminal `v4_capability_unavailable` on **missing estimates** — the 143.26h default does NOT make the metric appear calculable when the numerator is absent:
- `утилизация команды DMS` (no baseline) → FAILED "active assigned tasks do not expose source-backed estimates"; `team.capacity` args `{space: DMS}`; no members computed; no 143.26 in answer.
- `утилизация команды DMS с capacity 40 часов` → same typed failure; args `{space: DMS, capacity_hours: '40'}`; explicit baseline preserved in trajectory but estimate guard fires first.
- (2 attempts each, 4/4.)

## Phase 3 — controlled positive fixture (complete estimates): GREEN
| branch | capacity_source | cap/member | policy metadata | alice (12h) | bob (16h) |
|--------|-----------------|-----------|-----------------|-------------|-----------|
| A) no baseline | `owner_policy_default` | 143.26 | present, `source=OWNER_POLICY` | 8.4% | 11.2% |
| B) explicit 40h | `explicit_user_baseline` | 40.0 | absent | 30.0% | 40.0% |
- Exact utilization math; correct `capacity_source` + `warnings` (`capacity_baseline_owner_policy` vs `capacity_baseline_user_supplied`) in each branch.

## Phase 4 — time-accounting separation: GREEN (3 independent proofs)
1. `wave_batch2.py` (team.capacity) has **zero** references to `worklog`/`get_task_worklogs`/`time_spent` — it reads only `task.estimate_hours`.
2. `get_task_worklogs` is called **only** by `v4_plugins/time_accounting.py` (task.time_spent / task.worklogs remain the actual-time metrics).
3. Empirical: adapter with a rich 48h worklog source + missing estimate → `team.capacity` still raises on missing estimate and `get_task_worklogs` is called **0** times — worklogs are **not** silently substituted for estimates.
- Actual utilization (worklog numerator) correctly remains a separate, not-yet-implemented skill.

## Phase 5 — retained smoke: GREEN
- `task.time_spent` DMS-380: COMPLETED **48.0h, n=6** (A215D actual-time parity retained).
- team.workload DMS: COMPLETED 54 active / 18 completed / 5 unassigned / 13 members (live drift, internally consistent).
- release.search WMB: `[24Q1, 24Q2, 25Q1]` (A212 parity).
- dummy-55 / plugin-registry: 13/13.
- Source audit (post-restart task-api window): **local factual `/api/v1/tasks` reads = 0; unscoped tenant-wide scans = 0.**

## Non-blocking observations
- **F1 (policy granularity)** the 143.26h figure is a **monthly** capacity applied to a **current-sprint** utilization; the sprint is not normalized to a calendar month. Acceptable as an owner-chosen baseline, but worth documenting so the ratio isn't misread as a strict calendar-month utilization.
- **F2** policy is a product baseline (`OWNER_POLICY`), correctly surfaced as metadata — it is never presented as a REAL AS21 fact.

## Services left running
- agent 8212 (PID 2716 @ 0093ade, 127.0.0.1)
- task-api 8241 (PID 81954, system python3, SSE 48 tools)
- MCP-SWTR 3000 (PID 29268)
- UI 5175 (PID 85296, [::1]) / 5176 (PID 12824)

## Recommendation
Adopt the **capacity policy checkpoint** (owner 2026 baseline wired as a metadata-tagged, non-source denominator that never masks missing source estimates). Next: implement actual-time aggregation (sprint/team `time_spent`) or resume **A216 / Batch 3 QA** per owner priority.
