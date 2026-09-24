# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_215B_TEAM_CAPACITY_UX_REGATE

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT start A216 / Batch 3.
Commit/push only the QA report.

## Baseline
A215 Batch 2 is GREEN.

Post-GREEN owner UX hardening commits:
- `54b4c6ed0081e6eb1e7df3899620fb77cb2f4ba8`
- `1141938dd68c36765d18cd4911d9c25fe77f61a4`
- `2931cf1d1f645e487811e8a07244f3f9cd2e6e1b`

The fix is plugin-only. Agent Core/planner/runtime architecture must remain unchanged.

## Defect being re-gated
Before the fix, `team.capacity` could first ask the user for a capacity baseline even when REAL AS21 had already proven that source-backed task estimates were absent. After the user supplied e.g. 40h, the capability then failed anyway.

Required behavior now:
1. Resolve space/current sprint.
2. Check source estimate coverage first.
3. If active assigned tasks do not expose source-backed estimates:
   - fail closed immediately;
   - do NOT ask for capacity baseline;
   - do NOT suggest that adding 40/32/etc. would make calculation possible.
4. Only if source estimates are complete and the user omitted baseline may the agent ask for capacity_hours.
5. If both estimates and explicit baseline exist, calculation may proceed.
6. Never invent a 40h default.

## Phase 0 — architecture invariant
1. Pull branch and record START_HEAD.
2. Diff only the three owner fix commits.
3. Prove no Agent Core/planner/runtime routing changes.
4. Prove Batch 2 remains registry/plugin-owned.
5. dummy-55 remains GREEN.

## Phase 1 — focused tests
Run:
- `tests/test_agent_core_v4_batch2.py`
- relevant reliable/runtime/plugin tests

Expected:
- source-estimate absence is checked before baseline clarification;
- typed clarification occurs only in a fixture where estimates are complete and baseline is omitted;
- explicit baseline + missing estimates still fails closed;
- no implicit 40h path.

## Phase 2 — live REAL AS21 DMS
Run exactly these representative cases:

A. `утилизация команды в DMS`
B. `утилизация команды в DMS с базовой емкостью 40 часов`
C. `capacity команды DMS 32 часа`

Under the current proven DMS source state (no estimates), all three should terminate on the SAME source prerequisite:
- typed SOURCE_CONDITIONAL / capability unavailable;
- reason = task estimates are not exposed by REAL AS21;
- A must NOT be NEEDS_CLARIFICATION asking for capacity;
- B/C must preserve the supplied baseline in trajectory but must not calculate utilization.

## Phase 3 — Browser C
Repeat A and B in the real UI.

Require:
- no misleading request for capacity when estimates are already absent;
- no fake utilization;
- no generic runtime error;
- source limitation readable to the user.

## Phase 4 — retained Batch 2 smoke
Re-run:
- team.workload DMS
- team.wip DMS
- team.blocked DMS
- sprint.scope_change DMS-SPRNT-3

Require A215 parity / expected SOURCE_CONDITIONAL.

## Phase 5 — source audit
Require:
- local factual reads = 0;
- tenant-wide scans = 0;
- current-sprint bounded source path only.

## Verdict
Use exactly one:
- `TEAM_CAPACITY_UX_GREEN_A215B`
- `TEAM_CAPACITY_UX_RED_A215B`

If GREEN:
- recommend retaining A215 Batch 2 checkpoint plus post-green UX fix;
- recommend resuming Assignment 216 / Batch 3 QA.

If RED:
- identify first failing boundary and STOP.

Do not modify production code.
