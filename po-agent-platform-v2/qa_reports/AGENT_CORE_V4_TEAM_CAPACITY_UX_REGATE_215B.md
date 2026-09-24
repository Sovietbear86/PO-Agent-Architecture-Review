# A215B — team.capacity UX Re-Gate (source-estimate check before baseline clarification)

**Verdict:** `TEAM_CAPACITY_UX_GREEN_A215B`

**START_HEAD:** `ae4a503fd8a5fbcbbe235793f6f7749e164add5b`
**Role:** QA/adversarial tester + service operator only. No production code modified.
**Date:** 2026-09-24

---

## Owner fix (3 commits)
- `54b4c6e` fix(v4): avoid futile capacity clarification when estimates are unavailable — `wave_batch2.py` (+13/−12): estimate-coverage check moved **before** the baseline check; when active assigned tasks lack source-backed estimates → immediate typed `V4CapabilityUnavailable`; the typed baseline clarification (`V4NeedsClarification`) now fires only when source estimates are complete and the user omitted `capacity_hours`; skill procedure text updated accordingly.
- `1141938` test(v4): cover capacity source check before clarification — `test_agent_core_v4_batch2.py`.
- `2931cf1` test(v4): type capacity clarification precisely — same test file.

## Phase 0 — architecture invariant: PASS
- Diff of the three fix commits touches **only** `v4_plugins/wave_batch2.py` and `tests/test_agent_core_v4_batch2.py`. No Agent Core / planner / runtime / adapter / task-api change.
- Batch 2 remains registry/plugin-owned: `discover_v4_plugins()` reports `builtin.batch2.team_current_sprint` with all five skill ids; plugin-registry tests 13/13 (incl. dummy-55 extensibility).
- No implicit 40h default introduced (the fix path raises before any computation; baseline is only read from `args["capacity_hours"]`).
- Context: owner published Batch 3 plugin (`wave_batch3.py`, commit `44cf860`) below the fix on the branch; it is present in the registry but **out of scope** for this re-gate (A216 explicitly gated behind A215B).

## Phase 1 — focused tests: 165/166 (single failure = test-logic artifact, production proven correct)
- `test_agent_core_v4_batch2.py`: 5/6.
- All V4 suites (`test_agent_core_v4*.py` + `test_v4*.py`): **165 passed / 1 failed**.
- The single failure — `test_team_capacity_fails_on_source_estimates_before_asking_for_baseline` — is the **same fixture artifact class as A215 F1**: the shared `FakeAdapter`'s only missing-estimate task (`DMS-5`) is **unassigned**, and production correctly scopes the estimate check to active **assigned** tasks (spec: "active assigned tasks have source-backed estimates"). For that fixture the correct behavior is `V4NeedsClarification` (all active *assigned* tasks do carry estimates), which is exactly what production does.
- Direct probe proves the fix logic correct on all four scenarios:
  1. assigned + missing estimate, no baseline → `V4CapabilityUnavailable` ("do not expose source-backed estimates") — **does not ask for baseline** ✓
  2. complete estimates, no baseline → `V4NeedsClarification` (asks baseline) ✓
  3. complete estimates + explicit baseline → computes utilization ✓
  4. assigned + missing estimate + explicit baseline → `V4CapabilityUnavailable` (no calculation) ✓

## Phase 2 — live REAL AS21 DMS (3 spec cases × 2 attempts = 6/6): GREEN
Under the proven DMS source state (no estimate attributes on sprint rows):

| case | query | result (both attempts) |
|------|-------|------------------------|
| A | `утилизация команды в DMS` | `FAILED`, typed `v4_capability_unavailable`, `team.capacity` args `{space: DMS}` — **no NEEDS_CLARIFICATION, no baseline ask** |
| B | `утилизация команды в DMS с базовой емкостью 40 часов` | `FAILED`, same typed error; trajectory `team.capacity` args `{space: DMS, capacity_hours: '40'}` — baseline preserved, **no utilization calculated** |
| C | `capacity команды DMS 32 часа` | `FAILED`, same typed error; trajectory `team.capacity` args `{space: DMS, capacity_hours: '32'}` — baseline preserved, **no utilization calculated** |

All six runs terminate on the **same source prerequisite**: "team.capacity cannot be calculated from REAL AS21 because active assigned tasks do not expose source-backed estimates; an explicit capacity baseline alone is insufficient". Answer text is the honest typed failure; zero fabricated utilization percentages; the pre-fix defect (A → baseline clarification → then fail) is gone.

## Phase 3 — Browser C (real UI 5175 → agent 8212): 2/2 GREEN
- A (no baseline): `FAILED`, no misleading baseline request, no fake utilization, no generic runtime error, source limitation readable, no session/contract leak.
- B (40h): same typed source-limitation result; baseline not asked for, not calculated.
- Screenshots: `qa_215b_browser_c/`.

## Phase 4 — retained Batch 2 smoke: A215 parity GREEN
- team.workload DMS: `COMPLETED` 51 active / 17 completed / 5 unassigned / 13 members — per-member rows **exact** vs A215 oracle.
- team.wip DMS: `COMPLETED` total 30 — **exact task-key set parity**.
- team.blocked DMS: `COMPLETED` total 2 — **exact keys** `[DMS-352, DMS-379]`.
- sprint.scope_change DMS-SPRNT-3: `FAILED` typed "requires an authoritative sprint-start commitment baseline" — expected SOURCE_CONDITIONAL.

## Phase 5 — source audit: GREEN
- Local factual `/api/v1/tasks` reads: **0**.
- Unscoped tenant-wide `task-query` (no `space=`): **0**.
- Bounded current-sprint path only: current-sprint resolves 53 (cumulative A215+A215B) + 8 `/sprints/{id}/tasks?space=` calls.

## Non-blocking finding
- **F1 (test-logic artifact, not a production defect):** the new owner test `test_team_capacity_fails_on_source_estimates_before_asking_for_baseline` fails against the shared fixture for the same reason A215 F1 did (unassigned missing-estimate task is spec-correctly excluded from the estimate check). Production behavior is proven correct by the 4-scenario probe (Phase 1). Owner may want a dedicated fixture with an **assigned** missing-estimate task to assert the intended branch.

## Services left running
- agent 8212 (PID 93035 @ ae4a503, 127.0.0.1)
- task-api 8241 (PID 30041, system python3, SSE 48 tools)
- MCP-SWTR 3000 (PID 29268)
- UI 5175 (PID 85296, fresh vite, [::1]) / 5176 (PID 12824)

## Recommendation
Retain the A215 Batch 2 checkpoint **plus** the post-green capacity UX fix (54b4c6e) and resume **Assignment 216 / Batch 3 QA**.
