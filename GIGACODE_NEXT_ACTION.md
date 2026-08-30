# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_099_SCOPE_CHANGE_RECERTIFICATION`

## Role boundary
QA/tester only. Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.

Owner change under test: `e1e74b3d9f9bc33ec14333c6ceb2cc882def9837`.

Assignment 098 reported one remaining issue for `sprint-scope-change`. Owner review found the base runtime already contains the fail-closed sprint baseline capability, while the source-fact guard did not normalize hyphenated `scope-change`. The owner fix now treats `scope change`, `scope-change`, and `scope_change` as the same `sprint_snapshots` requirement.

Do not rerun all 54 skills. Run only this focused recertification plus exact Learning Loop before/after proof.

## Phase 0 — fresh runtime
1. Pull current branch and record exact HEAD.
2. Confirm owner commit is in HEAD ancestry.
3. Require clean `git status --short`.
4. Fully restart the production task-api/Harness process so no pre-fix process remains.
5. Record old/new PID and start time where available.
6. Confirm REAL task-api + AS21/SWTR, fake/mock/frozen authoritative calls = 0, AS21 writes = 0.
7. Do not reuse a pre-fix checkpoint for target cases.

If a fresh process cannot be proven, stop as `QA_ENVIRONMENT_NOT_RESTARTED`.

## Phase 1 — static proof
Prove from exact HEAD:
- `sprint-carryover` skill/capability is registered;
- `sprint-scope-change` skill/capability is registered;
- `SprintBaselineCapabilities.carryover()` and `.scope_change()` exist;
- source-aware `_required_fact()` maps `scope change`, `scope-change`, `scope_change`, and Russian scope-change wording to `sprint_snapshots`;
- current task list is not used as historical baseline.

Inspect `runtime_factory.py` and `historical_wiring.py` and determine whether the Assignment 098 claim about missing registration is actually true on the fresh current HEAD. Separate a real product defect from stale runtime/checkpoint or QA diagnosis error.

## Phase 2 — focused A/B
Use a valid REAL sprint, preferably `DMS-SPRNT-2` if still valid.

Run on the fresh process:
1. `Покажи scope-change спринта DMS-SPRNT-2`
2. `Покажи scope change спринта DMS-SPRNT-2`
3. `Покажи изменение состава спринта DMS-SPRNT-2`
4. `Покажи carryover спринта DMS-SPRNT-2`

Capture PID/start time, query/session, intent/skill, status, warnings, structured data, answer, source path, elapsed.

Independent Oracle B must prove current sprint scope exists but sprint-start historical commitment baseline/snapshot remains unavailable. Therefore no exact carryover/scope-change metric is calculable.

Expected while snapshots remain unavailable:
- no invented number;
- `source_capability_unavailable`;
- explicit sprint snapshot/baseline reason;
- no `semantic_skill_unavailable`;
- no capability-not-registered error;
- no generic runtime failure.

## Phase 3 — controls
On same fresh process verify:
- `sprint-scope` exact task-key set equals Oracle B;
- carryover remains fail-closed;
- one normal exact task lookup works against REAL AS21.

## Phase 4 — Learning Loop exact before/after
Before target queries capture actual policy-store:
- total policy count;
- active policy count;
- exact active policy IDs/versions;
- file hash or equivalent immutable snapshot.

After all queries capture the same fields again.

Source-unavailable carryover/scope-change queries must not create, promote, mutate, rollback, or apply a new learning policy to compensate for missing source capability.

Do not use `N/A` or `Unknown` for before/after state.

## Phase 5 — resolve 098
State whether the sole 098 product-defect row is:
- `CLOSED_BY_OWNER_FIX`
- `098_QA_STALE_RUNTIME_OR_DIAGNOSIS_ERROR`
- `STILL_PRODUCT_DEFECT`

## Source integrity
Record HTTP 500/502, timeouts/retries, successful REAL AS21 reads, fake/mock/frozen authoritative calls = 0, AS21 writes = 0.
Use >=120 s timeout, heavy up to 180 s, retry timeout/502 up to 2 times.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/SCOPE_CHANGE_RECERTIFICATION_099.md`

Allowed final verdicts:
- `BACKEND_CERTIFICATION_CLOSED_GREEN`
- `PRODUCT_DEFECT_STILL_PRESENT`
- `098_QA_STALE_RUNTIME_OR_DIAGNOSIS_ERROR`
- `LEARNING_LOOP_REGRESSION`
- `BLOCKED_BY_ENVIRONMENT`
- `QA_ENVIRONMENT_NOT_RESTARTED`

GREEN requires correct fail-closed behavior for all scope-change variants and carryover control, clean controls, exact unchanged Learning Loop before/after state, and proof of a fresh post-fix process.

Commit/push only allowed QA artifacts, report final SHA, then STOP.