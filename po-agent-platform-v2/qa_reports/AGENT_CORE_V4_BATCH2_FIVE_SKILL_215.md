# A215 — Batch 2 Five-Skill Gate (sprint.scope_change + team.workload/wip/blocked/capacity)

**Verdict:** `AGENT_CORE_V4_BATCH2_FIVE_SKILL_GREEN`

**START_HEAD:** `e98d8084d390fbafcae642d61fedd6be545e6cfd`
**Role:** QA/adversarial tester + service operator only. No production code modified.
**Date:** 2026-09-24

---

## Owner Batch 2
Five registry-discovered skills added in `v4_plugins/wave_batch2.py`:
`sprint.scope_change`, `team.workload`, `team.wip`, `team.blocked`, `team.capacity`.
Owner commits: `e0290fa` (feat), `a73e043` (test).

## Phase 0 — architecture invariant: PASS
- Diff `8900cae..e98d808` (src+tests+task-api) touches **only** `wave_batch2.py` (+302) and `test_agent_core_v4_batch2.py` (+147); plus docs (`V4_DOD_LOCK.md`). No Agent Core / planner / runtime / adapter / task-api change.
- All five skills are **plugin-registry discovered**: `discover_v4_plugins()` reports plugin id `builtin.batch2.team_current_sprint` and the five skill ids.
- No release/skill-specific planner or router branch introduced; the new capability ids are only reached through registry skill discovery.
- Every skill has a `CompletionContract` (`CompletionRequirement`) and a `UIContractV4`.
- Team metrics are bounded to one authoritative current sprint in one space (`get_current_sprint_id` + `get_sprint_tasks`); no tenant scan, no static roster inference.
- dummy-55 plugin-extensibility mechanism intact (verified via the V4 plugin-registry tests in P1).

## Phase 1 — tests
- `test_agent_core_v4_batch2.py`: 5/6 (see F1).
- `test_agent_core_v4_wave_s2.py` + `test_agent_core_v4_wave_s1.py`: 17/17.
- All V4 suites (`test_agent_core_v4*.py` + `test_v4*.py`): **159 passed / 1 failed** (the single failure is F1, a test-logic artifact — production is spec-correct, proven by direct probe).
- No unexplained failures within the V4 Batch 2 gate scope.

## Phase 2 — fresh REAL AS21 Oracle (independent, raw-source classification)
Current sprints resolved: DMS=`DMS-SPRNT-3`, OLP=`OLP-SPRNT-8` (WMB=`WMB-SPRNT-2`, STS=none).

| space | sprint | total | completed | open | WIP | blocked | unassigned(active) | members |
|-------|--------|-------|-----------|------|-----|---------|--------------------|---------|
| DMS   | DMS-SPRNT-3 | 68 | 17 | 51 | 30 | 2  | 5 | 13 |
| OLP   | OLP-SPRNT-8 | 69 |  2 | 67 | 49 | 6  | 3 | 13 |

- DMS blocked keys `[DMS-352, DMS-379]` — matches the A208 canonical blocked set (cross-check on the `status==NEED_INFO` predicate).
- OLP blocked keys `[OLP-2906, OLP-2986, OLP-3059, OLP-3118, OLP-3133, OLP-3204]`.
- **No estimate attributes** are exposed on either sprint's task rows (only `workflow_status` + `assigned_to`) → `team.capacity` can only ever fail-closed on the current source (see P6).
- No tenant-wide scan, no local factual reads (see P10).

## Phase 3 — team.workload: EXACT (5 forms, 2 spaces)
W1,W2 (DMS), W4,W5,W6 (OLP) all `COMPLETED` via `team.workload` with **exact** parity vs oracle:
sprint_id, active_tasks (=open), completed_tasks, unassigned_active_tasks, members_count, and every per-member row `{active_tasks, wip, blocked, completed}`.
DMS: active 51 / completed 17 / unassigned 5 / 13 members. OLP: active 67 / completed 2 / unassigned 3 / 13 members.
`task_count_workload_not_capacity` warning present. No capacity or employee-performance inference.

## Phase 4 — team.wip: EXACT (5 forms, 2 spaces)
I1,I2,I3b (DMS), I4,I5 (OLP) all `COMPLETED` via `team.wip` with **exact** `total_wip`, **exact task-key set parity**, and exact per-member counts. DMS WIP=30, OLP WIP=49.
**Semantics consistency proven:** Wave S1 `sprint.wip` and Batch 2 `team.wip` both return **30** for DMS-SPRNT-3 — identical certified non-terminal/backlog-exclusion semantics.

## Phase 5 — team.blocked: EXACT (5 forms, 2 spaces)
B1,B2,B3b (DMS), B4,B5 (OLP) all `COMPLETED` via `team.blocked` with **exact** `total_blocked` and **exact task-key set parity**. DMS=[DMS-352,DMS-379] (matches A208 / sprint.health predicate), OLP=6 keys. Same canonical blocked predicate (`status==NEED_INFO`) as sprint.health/risk logic.

## Phase 6 — team.capacity: fail-closed, no invented baseline
- **A) no explicit baseline** (C_A1 DMS, C_A2 OLP): `FAILED`, typed `v4_capability_unavailable` — "team.capacity requires an explicit capacity baseline". **No 40 (or any) default invented.**
- **B) explicit numeric baseline** (C_B1 "40 часов", C_B2 "30 часов"): planner forwarded the **user's exact value** (`team.capacity` args `capacity_hours='40'` / `'30'` — confirmed in trajectory) → then `FAILED`, typed `v4_capability_unavailable` — "requires source-backed estimates for every active assigned task; missing estimates: …". Source exposes no estimates, so it fails closed; **missing estimates are NOT treated as zero** and no utilization is fabricated.
- No employee scoring. No planner-invented baseline (the A/B behavioral difference proves the planner only forwards a baseline when the user supplies one).

## Phase 7 — sprint.scope_change: terminal SOURCE_CONDITIONAL, no proxy
- S1 (explicit `DMS-SPRNT-3`), S2 (period "сентябрьского спринта по DMS" → `sprints.discover`/`sprint.search` resolves a real sprint), S3 (current): all `FAILED` with typed `v4_capability_unavailable` — "sprint.scope_change requires an authoritative sprint-start commitment baseline; REAL AS21 currently exposes only the current sprint membership".
- Real sprint is validated first (`get_sprint_tasks`) before the missing-baseline failure. **No previous-sprint proxy, no fabricated percentage/count.**

## Phase 8 — Browser C (real UI 5175 → agent 8212): 5/5 clean
- C1 workload (DMS): COMPLETED, renders 51/17/5/13.
- C2 wip (DMS): COMPLETED, renders 30.
- C3 blocked (DMS): COMPLETED, renders DMS-352/DMS-379 (exact).
- C4 capacity (no baseline): NEEDS_CLARIFICATION, source-limitation visible.
- C5 scope_change (DMS-SPRNT-3): FAILED, source-limitation visible, typed error surfaced.
- Across all five: `generic_failure_visible=false`, `fake_pct=false`, `session/contract leak=false`, `stale_source_error_text=false`. SOURCE_CONDITIONAL states render explicitly, no fake metrics.
- Screenshots: `qa_215_browser_c/`.

## Phase 9 — retained regression: GREEN
- release.search: WMB `[24Q1, 24Q2, 25Q1]`, OLP `[1.6.0]` (A212 parity).
- release.health: `FAILED` typed "requires authoritative release-to-task membership" (A214 terminal SOURCE_CONDITIONAL parity).
- Wave S2 metric `sprint.cycle_time`: `{avg 206.06, median 77.7, min 0.0, max 1230.43}` (A210/A214 exact).
- `sprint.health`: 68 / 17 / 13 / 2 (A214 exact).
- `task.lookup` DMS-380: COMPLETED.
- person+status "Открытые задачи Жданова в DMS": `[DMS-371, DMS-1]` (A214 exact).
- dummy-55 plugin-extensibility mechanism retained (V4 plugin-registry tests green).

## Phase 10 — source audit: GREEN
- Local factual `/api/v1/tasks` reads (non-swtr-read): **0**.
- Unscoped tenant-wide `task-query` (no `space=`): **0**.
- Bounded current-sprint path used: **8** `/sprints/{id}/tasks?space=` calls + **36** `current-sprint` resolves.
- Exact task sets proven in P3–P5.

## Non-blocking findings
- **F1 (test-logic artifact, not a production defect):** `test_agent_core_v4_batch2.py::test_team_capacity_never_defaults_to_40_and_requires_source_estimates` fails. Its fixture task `DMS-5` (missing estimate) is **unassigned**; production correctly scopes the estimate fail-closed to active **assigned** tasks (spec: "active **assigned** tasks have source-backed estimates"), so the unassigned missing-estimate row is legitimately skipped. Direct probe confirms a missing estimate on an **assigned** active task **does** fail closed correctly. Owner may want the fixture to use an assigned task to assert the intended branch.
- **F2 (pre-existing LLM planner routing non-determinism):** two phrasings lacking the "команды/team" cue mis-route — I3 ("…WIP… в спринте DMS") → `sprint.wip` + NEEDS_CLARIFICATION; B3 ("…задачи заблокированы в спринте DMS") → `tasks.search` + NEEDS_CLARIFICATION. The clearer "команды DMS" phrasing (I3b/B3b) completes with the correct skill and **exact** data. Pre-existing class (A200/A207 lineage), not a Batch 2 defect.
- **F3 (out of gate scope):** legacy `test_skill_registry.py::test_get_active_skills` fails — a non-V4 legacy skill-registry test with **0 references** to batch2; pre-existing and outside the Batch 2 V4 gate scope.

## Service note (environmental, not a code defect)
The long-lived vite dev server (PID 55236, from A214) held a stale `http-proxy` connection pool to the killed agent and returned 500 for all `/api` proxy requests. Restarting vite fresh (PID 85296) with the agent on `127.0.0.1` (PID 60019 @ e98d808) restored the proxy (200). No frontend/config code was modified.

## Services left running
- agent 8212 (PID 60019 @ e98d808, 127.0.0.1)
- task-api 8241 (PID 30041, system python3, SSE 48 tools)
- MCP-SWTR 3000 (PID 29268)
- UI 5175 (PID 85296, fresh vite, [::1]) / 5176 (PID 12824)

## Recommendation
Freeze an immutable **Batch 2 checkpoint** (all five skills source-exact / correctly fail-closed; no fabrication; bounded current-sprint source path; retained regressions green) and proceed to owner implementation of **Batch 3**.
