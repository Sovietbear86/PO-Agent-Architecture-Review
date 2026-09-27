# A223 — UI State/Lineage Remediation Batch 1

**Date:** 2026-09-27
**START_HEAD:** `374ffa79163e13db2f4dced1b80dfd5ad0ada36e`
**Backend frozen at:** `17fdacb` (A222R2 GREEN)
**Branch:** `feat/core8-real-query-hardening-v2`
**Verdict:** `AGENT_CORE_V4_UI_STATE_LINEAGE_RED_A223`

---

## A223 Scope

Frontend-only diff vs A222R2 (`17fdacb..374ffa7`): 9 files, 0 backend Python changes.

Files changed:
- `resultState.ts` (new) — state adapter
- `ResultStatePanel.tsx` (new) — state panel component
- `agent/RichAnswer.tsx` (new) — markdown renderer for chat
- `V4ResultPanel.tsx` — updated
- `recovery/OverviewDashboard.tsx` — rewritten
- `recovery/Pages.tsx` — TasksPage/SprintPage/ReleasesPage updated
- `recovery/QualityDashboard.tsx` — rewritten
- `recovery/TeamDashboard.tsx` — rewritten
- `recovery/WorkspaceApp.tsx` — chat drawer updated

---

## P0 — Static/Build Gate

| Check | Result |
|-------|--------|
| `tsc --noEmit` | GREEN (exit 0) |
| `vite build` | GREEN (100 modules, exit 0) |
| `eslint` | NO config file (ESLint 8.57.1 "couldn't find a configuration file") — effective gate = tsc + vite build |

**P0 = GREEN**

---

## P1 — State Adapter Review

Reviewed `resultState.ts` classification chain:

```
loading→LOADING; null→NOT_RUN; NEEDS_CLARIFICATION→NEEDS_CLARIFICATION;
FAILED→{NOT_FOUND,SOURCE_UNAVAILABLE,SOURCE_CONDITIONAL,ERROR} (string-inference);
PARTIAL→SOURCE_CONDITIONAL (or SOURCE_UNAVAILABLE);
else isProvenEmptyCollection→REAL_EMPTY else SUCCESS_WITH_DATA
```

`stateAllowsBusinessData(state)` = SUCCESS_WITH_DATA or REAL_EMPTY only.

**F-A223-1 (non-blocking):** `v4_capability_unavailable` (source-CONDITIONAL: empty release membership, missing capacity estimates) and true source-unavailability both classify to `SOURCE_UNAVAILABLE` via string inference. The label is coarser than `SOURCE_CONDITIONAL` but both render a source-limitation panel (never 0/40h), so UI behavior stays correct.

**P1 = GREEN** (F-A223-1 noted, non-blocking)

---

## P2 — Chat Drawer / RichAnswer

Two chat queries captured via Browser C (Playwright, 2.6m total run):

| Query | Status | Raw MD (##/**/|---|) | Tables | Headings | Evidence | Feedback |
|-------|--------|----------------------|--------|----------|----------|----------|
| "Рекомендуй исполнителя для DMS-380" | COMPLETED | 0/0/0 | 1 | 0 | 1 | 1 |
| "Сделай daily brief" | COMPLETED | 0/0/0 | 2 | 4 | 1 | 1 |

**DMS-380 recommendation:** Kalachanov.V.V (DataMarts competency match, 0 active tasks, 0 WIP) — source-accurate, no fabrication.

**Daily brief:** 126 active, 8 blocked, 8 unassigned, 22 completed; DMS-SPRNT-3=73, OLP-SPRNT-8=74, WMB-SPRNT-2=1; top-5 with real tasks (DMS-352, DMS-379, etc.) — all source-backed.

**RichAnswer rendering:** headings (`####`→`<h4>`), **bold**→`<strong>`, markdown tables (with `|---|` divider)→`<table>`, bullet lists→`<ul>` all working. No raw markdown visible.

**Clarification option buttons:** Not triggered in either query (both COMPLETED). Page-level NEEDS_CLARIFICATION state panels (see P4/P5/P6/P7) prove `ResultStatePanel` renders correctly.

**P2 = GREEN**

---

## P3 — Overview Dashboard

**Metric cards:** All 4 show "—" (Всего задач, В работе, Заблокировано, Готовность портфеля).

**Root cause (F-A223-2, non-blocking):** `overview.data` = `{_agent_core_v4, results}`. The frontend reads `od.tasks_total`, `od.active`, `od.blocked` from `overview.data` directly, but the actual capability data is at `overview.data.results[0].data` with keys `active=126, blocked=8, unassigned=8, completed=22`. The `tasks_total` key does not exist in the source at all.

**Not a false zero:** The em-dash "—" is the correct "no data at expected path" indicator. The A223 spec requirement "no false zeros" is met.

**Daily Brief panel:** Shows real data via `RichAnswer` (126/8/8/22, sprint table, top-5 attention queue) — source-backed, GROUNDED badge visible.

**Attention queue / Product status panels:** `stateAllowsBusinessData` gates working (no state panels rendered = COMPLETED/SUCCESS).

**Raw markdown:** 0 (hash=0, bold=0, tableSep=0).

**P3 = GREEN** (F-A223-2 noted: data-shape mismatch means real values not displayed, but no false zeros)

---

## P4 — Tasks Page + Sprint Page

### Tasks Page

- Default query "Найди login" → NEEDS_CLARIFICATION
- State panel renders: "Нужно уточнение / Для выполнения запроса нужно уточнение." ✓
- No false zeros, no raw markdown
- Task grid not rendered (stateAllowsBusinessData = false for NEEDS_CLARIFICATION) ✓

### Sprint Page

- Default sprint: WMB-SPRNT-1
- All 4 metric cards show "—" (data-shape mismatch, F-A223-2 class)
- Risk queue: "Источник подтвердил: риски не выявлен." — WMB-SPRNT-1 is an older sprint; the sprint.risk_queue capability returned COMPLETED. The risk data is at `risks.data.results[1].data` (nested), frontend reads `risks.data.risks` (wrong level) → `[]`. If WMB-SPRNT-1 genuinely has 0 risk tasks, this is REAL_EMPTY (correct). Cannot confirm without full nested data dump.
- Throughput/WIP/Готовность insight cards: "—" values (data-shape mismatch)
- No false zeros, no raw markdown

**P4 = GREEN** (no false zeros, state panels correct; data-shape mismatch is pre-existing class)

---

## P5 — Releases Page

Default release: WMB-2024-Q3 (not a real release in source).

**Observed state panels:** 3× NEEDS_CLARIFICATION (scope, progress, blockers likely).

**Metric cards:** All 4 show "—" (Scope, Completed, Blocked, Готовность) — no false zeros ✓

**Risk queue:** `muted=[]` in artifact — "Риски не выявлены" NOT shown (stateAllowsBusinessData = false → ResultStatePanel instead) ✓

**Dependencies:** Not shown as 0/0 (stateAllowsBusinessData = false) ✓

**Blockers:** Not shown as "none" (stateAllowsBusinessData = false) ✓

**Pseudo-forecast:** "Forecast не активирован: master-spec требует честный исторический baseline." note visible ✓

**Backend grounding probes (direct API):**

| Query | Status | Warnings | UI would show |
|-------|--------|----------|---------------|
| "Покажи scope WMB 24Q1" | NEEDS_CLARIFICATION | v4_capability_clarification | State panel (NEEDS_CLARIFICATION) |
| "Покажи прогресс OLP 1.6.0" | FAILED | v4_capability_unavailable | State panel (SOURCE_UNAVAILABLE via F1) |
| "Покажи блокеры OLP 1.6.0" | FAILED | v4_capability_unavailable | State panel (SOURCE_UNAVAILABLE via F1) |

All three render source-limitation state panels, NOT 0/empty. No false zeros.

**P5 = GREEN**

---

## P6 — Team Dashboard

- Capacity input: placeholder "Пусто = owner policy", no hardcoded 40h ✓
- Competency note: "Competency match и рекомендация исполнителя SOURCE_READY: используются заявленные компетенции из team_members.yaml..." ✓
- 2× NEEDS_CLARIFICATION state panels (capacity queries)
- All 4 metric cards show "—" (Активных задач, WIP, Blocked, Capacity baseline) — data-shape mismatch (F-A223-2 class), no false zeros
- No raw markdown

**P6 = GREEN** (no hardcoded 40h, capacity shows state panel, competency note present)

---

## P7 — Quality Dashboard — BLOCKING DEFECT

### D-A223-1: Quality page shows `NaN/100` + incorrect READY decision

**Observed (Browser C capture):**

| Metric Card | Displayed Value | Expected |
|-------------|----------------|----------|
| Quality score | `NaN/100` | `85/100` or `—` |
| Acceptance | `NaN/100` | `0/100` or `—` |
| Пробелы | `0` | `1` (acceptance_expectations) |
| Решение PO | `READY` / "Можно брать в работу" | `REWORK` / "Вернуть на доработку" |

**Backend truth (direct API probe, WMB-102):**

| Capability | Actual data at `data.results[0].data` |
|------------|---------------------------------------|
| task.quality | `score=85, quality_level="good", missing_elements=["acceptance_expectations"]` |
| task.missing_requirements | `quality_score=85, missing_elements=["acceptance_expectations"]` |
| task.acceptance | `score=0, criteria=[], testable_criteria=[], gaps=["Нет явно выделенных критериев приемки"]` |

**Correct REWORK computation** (per dashboard logic):
```
score=85, acceptanceScore=0, missingCount=1
returnForRework = (85<70) || (0<70) || (1>0) = false || true || true = true
→ Decision should be REWORK
```

**Actual (buggy) computation:**
```
qd = quality.data = {_agent_core_v4, results}  ← wrong level
qd.score = undefined
md.quality_score = undefined  (md = missing.data = {_agent_core_v4, results})
score = Number(undefined) = NaN
acceptanceScore = Number(ad.score) = NaN  (ad = acceptance.data = {_agent_core_v4, results})
missingCount = md.missing_elements?.length ?? 0 = 0  (wrong level → undefined → 0)
returnForRework = (NaN<70) || (NaN<70) || (0>0) = false || false || false = false
→ Decision = READY  ← INCORRECT
```

**Root cause:** QualityDashboard reads `quality?.data` as the flat capability data, but the V4 API response nests the actual result at `quality.data.results[0].data`. This is the same data-shape mismatch documented since A218 ("capability payload at data.results[0].data"). The A223 state gate (`classifyResult`) correctly identifies COMPLETED → `qualityReady=true`, but the data extraction from the wrong level produces NaN.

**Impact:**
1. User-visible garbage: `NaN/100` in two metric cards
2. Incorrect PO decision: shows READY when WMB-102 should show REWORK (acceptance score 0 + 1 missing element)
3. New to A223: the QualityDashboard was written fresh for A223; the pre-A223 QualityPage (dead code in Pages.tsx) just dumped `JSON.stringify(result.data, null, 2)` which at least showed the nested structure

**Fix boundary (owner):** In `QualityDashboard.tsx`, extract capability data from `result?.data?.results?.[0]?.data` (or add a helper `getCapabilityData(result)` in `resultState.ts`). Apply the same fix to all dashboards (Overview, Sprint, Team, Releases) that read `result?.data` as flat capability data.

**P7 = RED** (D-A223-1)

---

## P8 — Source Audit (task-api log delta)

**Baseline:** 13524 lines (recorded before new vite + browser run)
**Total after run:** 13882 lines
**Delta:** 358 lines

| Check | Count |
|-------|-------|
| Mutations (POST/PUT/DELETE) | 0 |
| Local `/api/v1/tasks` reads (non-swtr) | 0 |
| Unscoped task-query (no `space=`) | 0 |
| swtr-read calls | 358 |
| 500 errors | 0 |

All 358 calls are read-only `GET /api/v1/swtr-read/*` (health, current-sprint, sprint tasks, point reads).

**P8 = CLEAN**

---

## P9 — Compact Regression Smoke

Not run (STOP at P7 RED per spec: "identify first failing UI boundary + STOP").

Retained from A222R2 (backend unchanged at 17fdacb):
- Competency match + assignee recommendation SOURCE_READY
- Time accounting (member.time_spent, sprint.time_spent, task.time_spent)
- Release search (WMB 3, OLP 1, DMS 0)
- Sprint health/scope/wip/velocity/throughput
- Person+status search
- 54/54 canonical A/B/C GREEN

---

## Systemic Finding: V4 Data Shape Mismatch

**All A223 dashboards** read `result?.data` as if it's the flat capability data. The V4 API response structure is:

```
result.data = {
  _agent_core_v4: { runtime, loaded_skills, trajectory, ... },
  results: [
    { step, capability_id, arguments, answer, data: { <actual capability data> } },
    ...
  ]
}
```

The actual capability data is at `result.data.results[N].data`, not `result.data`. This was documented as a QA gotcha since A218 but was not addressed in the A223 frontend rewrite.

**Affected dashboards and keys:**

| Dashboard | Reads | Actual path | Result |
|-----------|-------|-------------|--------|
| QualityDashboard | `quality.data.score` | `quality.data.results[0].data.score` | NaN → `NaN/100` |
| QualityDashboard | `acceptance.data.score` | `acceptance.data.results[0].data.score` | NaN → `NaN/100` |
| QualityDashboard | `missing.data.missing_elements` | `missing.data.results[0].data.missing_elements` | undefined → 0 (masks real 1) |
| OverviewDashboard | `overview.data.tasks_total` | key doesn't exist | undefined → `—` |
| OverviewDashboard | `overview.data.active` | `overview.data.results[0].data.active` | undefined → `—` |
| SprintPage | `health.data.total/completed` | `health.data.results[1].data.*` | undefined → `—` |
| SprintPage | `risks.data.risks` | `risks.data.results[1].data.*` | undefined → `[]` (false "no risks" if >0) |
| TeamDashboard | `workload.data.workload` | `workload.data.results[0].data.*` | undefined → `[]` |
| TeamDashboard | `capacity.data.members` | `capacity.data.results[0].data.*` | undefined → `[]` |
| ReleasesPage | `scope.data.count` | `scope.data.results[0].data.*` | undefined → `—` |

**Classification:** Pre-existing data-shape assumption (was in the old dead-code pages too). A223 made it worse by adding `stateAllowsBusinessData` gates that return `true` for COMPLETED responses, then reading from the wrong level → NaN (Quality) instead of just `—` (other pages).

---

## Findings Summary

| ID | Severity | Page | Description |
|----|----------|------|-------------|
| **D-A223-1** | **BLOCKING** | Quality | `NaN/100` display + incorrect READY decision (should be REWORK). Data-shape mismatch in new QualityDashboard. |
| F-A223-1 | Non-blocking | All | `v4_capability_unavailable` → SOURCE_UNAVAILABLE (coarse label, correct panel) |
| F-A223-2 | Non-blocking | Overview/Sprint/Team/Releases | Real data not displayed (all "—") due to data-shape mismatch. No false zeros. |
| F-A223-3 | Non-blocking | Sprint | Risk queue "no risks" may be false if WMB-SPRNT-1 has risk tasks at nested level |

---

## Verdict

**`AGENT_CORE_V4_UI_STATE_LINEAGE_RED_A223`**

**First failing UI boundary:** P7 Quality Dashboard — `NaN/100` in metric cards + incorrect READY decision for WMB-102 (should be REWORK). Root cause: QualityDashboard reads `quality.data.score` instead of `quality.data.results[0].data.score`.

**STOP.** No checkpoint. No Learning Reviewer.

**Owner fix required:**
1. Add a `getCapabilityData(result: HarnessQueryResponse | null): Record<string, unknown>` helper in `resultState.ts` that extracts `result?.data?.results?.[0]?.data ?? {}`
2. Use this helper in all dashboards (QualityDashboard, OverviewDashboard, SprintPage, TeamDashboard, ReleasesPage) instead of reading `result?.data` directly
3. Add `Number.isFinite` guard before displaying numeric scores (defensive: show `—` if the value is not a finite number)
4. Add a non-mocked regression test: assert QualityDashboard shows the actual score (not NaN) and correct REWORK/READY decision for a task with acceptance score < 70

**Preserved artifacts:**
- Screenshots: `qa_223_browser_c/*.png` (overview, tasks, sprint, releases, team, quality, 2 chat)
- Browser C data: `po-agent-platform-v2/qa_artifacts/a223_browser_c.json`
- Backend grounding probes documented above

**Services left running:** agent 8212 (PID 29982 @ 17fdacb), task-api 8241 (PID 81954), MCP-SWTR 3000 (PID 29268), vite 5175 (PID 77775, [::1]).
