# GigaCode — Current Action

## ACTIVE: Assignment A229S1R3 — manual regression: Overview KPIs + sprint/type composition

Role: QA/source-forensics/browser tester only. **Do not modify production code.**

Context:
A229S1R2 was backend/capability GREEN, but manual UI testing found two regressions before checkpoint freeze:

1. Overview top KPIs `Активно / Завершено / Заблокировано` rendered as `—`.
2. Complex task query with person + latest/current sprint + status + task type returned `source_unavailable`, while the same sprint/person query without task type worked.

Owner fixes are now on current `feat/core8-real-query-hardening-v2`.

### Root cause / owner delta to verify

#### A. Overview KPI regression
Historical trace:
- `OverviewDashboard.tsx` itself had not changed since 2026-09-28.
- A226R3 previously showed top KPI values `119 / 40 / 7`, identical to the certified PO status/daily-brief payload.
- The page nevertheless depended on the ambiguous natural-language snapshot `Дай обзор и риски` for those 3 KPI fields.
- After catalog growth, planner routing can legitimately select `portfolio.overview`, whose top-level payload does not expose `active/completed/blocked`. Cached snapshot refresh therefore made the cards disappear without a frontend code regression.

Owner fix:
- remove the ambiguous `overviewQ` dependency from the KPI row;
- source all 4 KPI cards from the already-requested deterministic `po.status_report` payload;
- refresh now tracks attention + brief + status only;
- no Agent Core change.

#### B. Sprint + task type composition
Owner fix:
- live sprint canonical rows preserve `unit.suit -> task_type_code/task_type_name`;
- TQL sprint enrichment requests `suit`;
- task-type enrichment is opt-in via `include_task_type=true`;
- `task.type_analysis` uses the live `/api/v1/swtr-read/sprints/{id}/tasks?complete=true&include_task_type=true` corpus, not the historical local task store;
- incomplete sprint membership fails closed;
- skill procedure/capability set now supports sprint resolution before the same terminal `task.type_analysis` call:
  - explicit sprint -> `sprint.resolve`
  - month/period -> `space.resolve + sprint.search`
  - current/latest wording -> `space.resolve + sprint.current`
- person/space/status/type constraints must survive into the terminal call.
- Agent Core remains untouched.

---

## P0 — integrity / regression

1. Record START_HEAD and clean worktree.
2. Prove these Agent Core files are byte-identical to `checkpoint/v4-task-details-richtext-green-a229u2r`:
   - agent_core_v4.py
   - agent_core_v4_robust.py
   - agent_core_v4_reliable.py
   - agent_core_v4_completion.py
   - v4_plugin_registry.py
   - llm/real.py
3. Canonical 54/54 unchanged; exactly 2 extra skills remain `task.type_analysis` and `task.hierarchy`.
4. Run focused tests:
   - task-api sprint collection tests;
   - SWTR task relations tests;
   - task semantics/hierarchy tests;
   - task catalog/plugin registry tests;
   - retained assignee/status/sprint tests.
5. Full V4 blast-radius + frontend build.

Any Core diff or retained regression => RED STOP.

---

## P1 — prove Overview root cause and owner fix

### Forensics
Confirm from git history:
- no recent production change to `OverviewDashboard.tsx` caused the manual regression;
- old dashboard used `getCapabilityData(overviewQ)` from `Дай обзор и риски` for active/completed/blocked;
- `portfolio.overview` does not expose those top-level fields;
- A226R3 previously recorded `119 / 40 / 7` matching the PO status/daily-brief payload.

Do **not** attribute this to AS21 outage.

### Browser re-gate
Fresh browser/sessionStorage and full current stack.

Require:
- Overview loads;
- `Активно`, `Завершено`, `Заблокировано`, `Готовность портфеля` are populated when `po.status_report` is successful;
- values are exact vs one independent direct `po.status_report` agent/API probe;
- no ambiguous `Дай обзор и риски` snapshot POST is needed for the KPI row;
- Attention Queue and Daily Brief remain unchanged/source-backed;
- manual Refresh updates the 3 snapshot queries and preserves stale values while refreshing;
- no 4xx/5xx and no console errors.

Record exact KPI values and screenshot.

---

## P2 — live sprint type source contract

Use a real bounded sprint with known tasks; prioritize the user's reproduced OLP latest/current sprint (previously `OLP-SPRNT-9`) if still current.

A/B source oracle:

A. live sprint facade:
`GET /api/v1/swtr-read/sprints/{sprint}/tasks?space=OLP&complete=true&include_task_type=true`

B. independent direct source type proof for sampled/matching tasks using `read_unit().suit` (or another authoritative source path already proven for unit.suit).

Require:
- `complete=true`;
- `membership_proven=true`;
- no local `/api/v1/tasks` read;
- exact task membership;
- every task used for a type decision has exact source `task_type_code/name`;
- sampled type values match independent `unit.suit`;
- `include_task_type=false` does not force type-only enrichment when it is otherwise unnecessary;
- no fabricated UNKNOWN type.

If source genuinely omits suit for any row, report that exact row and source evidence; do not classify the whole AS21 source as down.

---

## P3 — complex query regression from manual test

Use a **new conversation** for each run.

Primary case, at least 3 runs:
`Покажи открытые задачи Семавина в последнем спринте по OLP с типом дефект`

Also run:
1. same query without `с типом дефект` (retained control);
2. `Покажи задачи Семавина в последнем спринте по OLP с типом дефект`;
3. `Покажи открытые задачи в последнем спринте по OLP с типом дефект`.

Build an independent source oracle:
- resolve Semavin identity through REAL AS21;
- resolve latest/current OLP sprint source-backed;
- get complete live sprint membership;
- apply canonical open/not_completed status;
- compare task type using authoritative `unit.suit`.

Require for the primary case:
- terminal capability = `task.type_analysis`;
- canonical `sprint_id` is source-resolved, not invented;
- terminal arguments preserve `reference + space + sprint_id + status + task_type`;
- exact key/count parity with oracle;
- no model-side intersection;
- no local fallback;
- no tenant-wide scan;
- no `source_unavailable` when the source calls themselves are healthy.

If the planner cannot safely complete the trajectory while source reads are healthy, the response must be the generic trajectory/runtime failure semantics, not an AS21 outage claim. Preserve the trace and first failing boundary.

---

## P4 — error taxonomy audit

Verify without production edits:

- real transport/source outage (`AS21SourceUnavailable`) -> source unavailable semantics;
- planner contract/step-budget/runtime trajectory failure -> `Agent Core v4 не смог безопасно завершить траекторию.` / `v4_runtime_failure`;
- source reachable but a specific fact is unprovable -> typed capability/source insufficiency, never a fake empty result and never a false whole-source outage.

Use existing unit/fake harnesses if an injected failure is needed. Do not modify Core to manufacture a test.

---

## P5 — retained UI + architecture

Re-run:
- task type person+space+status;
- hierarchy DMS-380 or DMS-267;
- ordinary person+sprint search;
- task drawer description/intelligence;
- Overview Attention Queue + Daily Brief;
- Tasks free-text search.

Architecture audit:
- Core byte-identical;
- no phrase router;
- no hardcoded Semavin/OLP/sprint/type result;
- no local task-store fallback in the new sprint/type path;
- no mutation;
- public/community repo untouched.

---

## Verdict

Return exactly one:

- `AGENT_CORE_V4_MANUAL_REGRESSION_GREEN_A229S1R3`
- `AGENT_CORE_V4_MANUAL_REGRESSION_RED_A229S1R3`
- `SOURCE_SAMPLE_BLOCKED_A229S1R3`

GREEN requires P0-P5 GREEN.

If GREEN:
- commit/push the QA report;
- recommend checkpoint `checkpoint/v4-task-semantics-hierarchy-green-a229s1r3`;
- owner can then sync certified delta to public/community;
- next assignment returns to A229R1 latency verification.

If RED:
- record the first failing boundary;
- STOP;
- do not modify production code.

**GigaCode is QA only. Do not modify production code.**
