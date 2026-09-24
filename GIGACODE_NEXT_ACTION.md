# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_214_RELEASE_HEALTH_REGATE

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT add skills.
Do NOT start the next five-skill batch.
Commit/push only the QA report.

## Baseline
A213 verdict:
`RELEASE_HEALTH_RED`

Sole blocker:
pre-existing generic literal-grounding guard rejected a release UUID that had just been returned by a validated `release.search` observation.

## Owner fix
Owner commits:
- `31f122af9af78d210beb366b94e7ac0187644d97`
- `18e8d4cb2255d16576069c02cbf5fde4e012755d`
- `356c5a25786676a40dd2ccaa36b618bd6f5e3a39`

Fix semantics:
- generic guard now trusts `release_id` only when byte-equivalent to an id emitted by a prior validated `release.search` observation;
- arbitrary release ids remain rejected;
- product-space-as-release-id rejection remains intact;
- no skill-specific routing branch was added;
- no source facts are memorized;
- stale Wave S1 contract assertion updated to the current plugin-owned release-health flow.

## Goal
Re-gate release.health live path and prove it reaches the bounded fail-closed handler.

## Phase 0 — architecture invariant
1. Pull branch and record START_HEAD.
2. Diff owner changes against A213 baseline.
3. Prove:
   - no release-specific planner/router branch;
   - guard change is generic trusted-observation grounding only;
   - release.health remains plugin/registry owned;
   - dummy-55 stays GREEN;
   - arbitrary release ids and product names still fail validation.

## Phase 1 — tests
Run focused reliable-runtime tests, release-health tests, Wave S1 tests, and relevant V4 suites.

Require:
- trusted release.search UUID literal passes;
- invented UUID fails;
- product space as release_id fails;
- release-health focused tests pass;
- no stale assertions remain.

## Phase 2 — live NL release.health
Run at least:
- `здоровье релиза 24Q1 в WMB`
- `здоровье релиза 1.6.0 в OLP`
- `здоровье релиза в OLP`

Expected under current source state:
1. space.resolve
2. release.search
3. release.health executes
4. bounded `task-query?space=<space>&release=<id>`
5. empty authoritative membership => typed SOURCE_CONDITIONAL / SOURCE_UNAVAILABLE
6. no generic runtime failure
7. no 0/0 fabricated health
8. no tenant-wide scan

## Phase 3 — Browser C
Real UI for WMB and OLP health requests.

Require:
- clear source-limitation result;
- no generic runtime failure;
- no fake health percentage;
- no stack/session/contract leak.

## Phase 4 — retained release.search
Re-run WMB, OLP, DMS.
Require A212 parity.

## Phase 5 — retained regression
At minimum:
- one Wave S2 metric;
- sprint.health;
- task.lookup;
- person+status search;
- dummy-55;
- local factual reads = 0;
- tenant-wide scans = 0.

## Verdict
Use exactly one:
- `RELEASE_HEALTH_SAFE_SOURCE_CONDITIONAL_GREEN`
- `RELEASE_HEALTH_RED`

If GREEN:
- recommend release remediation closure:
  - release.search = GREEN;
  - release.health = terminal SOURCE_CONDITIONAL until authoritative release-to-task membership exists;
- recommend resuming V4-CATALOG with the next five-skill batch.

STOP after report. Do not modify production code.
