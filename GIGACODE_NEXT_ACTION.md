# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_213_RELEASE_HEALTH_FAIL_CLOSED_REGATE

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT add skills.
Do NOT start the next five-skill batch.
Commit/push only the QA report.

## Baseline
A212 verdict:
`RELEASE_SEARCH_GREEN_HEALTH_LINKAGE_BLOCKED`

Release search is GREEN end-to-end.

Source fact proven by A212:
- release catalog is live and healthy;
- WMB/OLP releases exist;
- DMS has authoritative 0 releases;
- task-side `fix_version_s` / version linkage is unpopulated, so authoritative release-to-task membership cannot currently be established.

## Owner hardening
Owner did NOT invent membership.

Owner commits:
- `4c81342ae90c0c3745f4438d7c99b60c1170a855`
- `9f973f72dc16c37d08de9feabbf5cbbc4f8597cd`

Changes are plugin-only + focused tests:
- release.health no longer uses the legacy tenant-wide scan bridge;
- it requires source-backed release id + space;
- it reads only bounded space-scoped release membership via the adapter;
- if membership is empty/unavailable under the current source contract, it fails closed as capability unavailable;
- no 0/0 fabricated health;
- no Agent Core/planner/runtime changes.

## Goal
Certify that release.health is safe and architecture-compliant under the current source limitation.

## Phase 0 — architecture invariant
1. Pull branch and record START_HEAD.
2. Diff owner commits against A212 baseline.
3. Prove:
   - no Agent Core/planner/runtime changes;
   - release.health remains registry/plugin discovered;
   - binding is plugin-owned, not legacy runtime-owned;
   - dummy-55 invariant remains GREEN;
   - no hardcoded release ids/spaces/tasks.

## Phase 1 — focused tests
Run the new release-health focused tests plus relevant V4 suites.

Require:
- bounded space-scoped membership call;
- successful metric only when tasks are source-backed;
- empty membership => typed fail-closed, never 0/0;
- no legacy runtime release-health scan path.

## Phase 2 — live natural-language release.health
Use real source-backed catalog releases from WMB/OLP.

Representative forms:
- `здоровье релиза 24Q1 в WMB`
- `здоровье релиза 1.6.0 в OLP`
- product-only form where exactly one release exists, if applicable.

Expected under current source state:
- release.search resolves exact real release;
- release.health attempts bounded space-scoped membership;
- source membership limitation produces typed SOURCE_CONDITIONAL/SOURCE_UNAVAILABLE;
- no tenant-wide scan;
- no fabricated total/completion percent;
- no product-as-release confusion.

## Phase 3 — Browser C
Real UI for at least WMB and OLP release-health requests.

Require:
- clear source-limitation message;
- no 0/0 health card presented as fact;
- no stack/session/contract leak;
- release search/list still renders correctly.

## Phase 4 — retained release.search
Re-run:
- releases WMB;
- releases OLP;
- releases DMS.

Require A212 parity remains GREEN.

## Phase 5 — retained regression and audit
At minimum:
- one Wave S2 metric;
- sprint.health;
- task.lookup;
- person+status task search;
- dummy-55;
- local factual /api/v1/tasks reads = 0;
- tenant-wide scans = 0.

## Verdict
Use exactly one:
- `RELEASE_HEALTH_SAFE_SOURCE_CONDITIONAL_GREEN`
- `RELEASE_HEALTH_RED`

If GREEN:
- recommend closing release remediation for V4 as:
  - release.search = GREEN;
  - release.health = terminal SOURCE_CONDITIONAL until authoritative release membership exists;
- recommend resuming the next five-skill catalog batch.

STOP after report. Do not modify code.
