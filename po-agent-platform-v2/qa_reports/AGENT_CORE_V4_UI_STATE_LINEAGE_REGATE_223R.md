# A223R — UI Capability Payload/State Lineage Re-gate

**Date:** 2026-09-27
**START_HEAD:** `fb94da6` (owner A223R fix)
**A223 report base:** `25a84cc` (AGENT_CORE_V4_UI_STATE_LINEAGE_RED_A223)
**Backend frozen at:** `17fdacb` (A222R2 GREEN) — unchanged, agent PID 29982
**Branch:** `feat/core8-real-query-hardening-v2`
**Verdict:** `AGENT_CORE_V4_UI_STATE_LINEAGE_RED_A223R`

---

## Scope

Owner remediation of the A223 blocking defect (Quality `NaN/100` + flat-vs-nested payload). Frontend/docs only.

Owner commits (25a84cc..fb94da6):
- `9da3857` shared `getCapabilityData()`
- `2317d3f` Overview unwrap
- `dd71d63` Team unwrap
- `dbd9053` Quality unwrap + finite-number guards
- `56cbd3d` Tasks/Sprints/Releases unwrap
- `e84910a` Overview metrics aligned to payload keys

**Diff scope (P0):** 7 files — 2 docs + 5 frontend (`OverviewDashboard.tsx`, `Pages.tsx`, `QualityDashboard.tsx`, `TeamDashboard.tsx`, `resultState.ts`). **0 backend/Core/planner/runtime/session files.** ✓

Services: agent 8212 (PID 29982 @ 17fdacb), task-api 8241 (48 tools, connected), MCP 3000, fresh vite 5175 (PID 86408, [::1]).

---

## P0 — static/build — GREEN

| Check | Result |
|-------|--------|
| diff 25a84cc..fb94da6 frontend/docs only | ✓ (7 files, 0 backend python) |
| `tsc --noEmit` | GREEN (exit 0) |
| `vite build` | GREEN (100 modules, exit 0) |

---

## P1 — getCapabilityData contract — GREEN (23/23)

Transpiled the real `resultState.ts` (esbuild) and ran the actual function against the 5 spec cases + classify integration:

- **flat legacy payload** → returns the flat object ✓
- **composed V4 (single envelope)** → final business data, NOT the `_agent_core_v4` envelope ✓
- **resolver + business** → business payload (risk_queue), not resolver payload; `capabilityId` filter selects the right envelope ✓
- **empty/missing results** (null / no-data / `results:[]` / all-null-data) → `{}` ✓
- **no mutation** of the original response (incl. filtered calls) ✓
- `classifyResult` now applies REAL_EMPTY to the **unwrapped** capability data: acceptance `score=0`+empty criteria → SUCCESS_WITH_DATA (not REAL_EMPTY); `tasks:[]`+`count:0` → REAL_EMPTY; `FAILED v4_capability_unavailable` → SOURCE_UNAVAILABLE; `FAILED requires authoritative` → SOURCE_CONDITIONAL ✓

---

## P2 — Quality WMB-102 (BLOCKING) — GREEN, D-A223-1 CLOSED

Backend truth (direct API, unchanged): quality `score=85`/`good`/`missing_elements=[acceptance_expectations]`; missing `quality_score=85`; acceptance `score=0`/`criteria=[]`/`gaps=[2]`.

**Browser C (fresh frontend):**

| Metric | Rendered | Expected | |
|--------|----------|----------|---|
| Quality score | **85/100** | 85/100 | ✓ |
| Acceptance | **0/100** | 0/100 | ✓ |
| Пробелы | **1** | 1 | ✓ |
| Решение PO | **REWORK** / «Вернуть на доработку» | REWORK | ✓ |
| NaN occurrences | **0** | 0 | ✓ |

**Absent-score path** (invented `WMB-999999`, score path not finite): all scores render **"—"**, decision **"NOT RUN"** / «Ожидание данных», **0 NaN/Infinity**. ✓

The A223 blocking defect is closed: `getCapabilityData` unwrap + `Number.isFinite` guards produce correct values and a correct REWORK decision.

---

## P3 — Overview — GREEN

Metric cards from the nested `po.status_report` payload (no `tasks_total`):

| Card | Rendered | Source | |
|------|----------|--------|---|
| Активно | **126** | active=126 | ✓ |
| Завершено | **22** | completed=22 | ✓ |
| Заблокировано | **8** | blocked=8 | ✓ |
| Готовность портфеля | **14.9%** | status.completion_percent | ✓ |

Daily Brief rich rendering retained; attention queue state-safe; 0 raw-markdown, 0 NaN.

---

## P4 — Sprints (DMS-SPRNT-3, source-ready) — **RED** (first failing boundary)

Metric cards now populate correctly from the unwrapped payload: **Scope 73, Completed 19, Velocity 19 tasks/sprint, Predictability "—"** (predictability is a genuine `v4_capability_unavailable` → em-dash, correct). WIP insight=31, Готовность=26%.

**BUT two leaf field-name mismatches, both in `Pages.tsx` SprintPage, are now exposed by the unwrap (they were masked in A223 when the whole read returned the envelope → all "—"):**

### D-A223R-1 — Sprint Risk Queue: false «риски не выявлены» despite 38 risks
- **Rendered (Browser C, preserved):** Risk Queue panel **title = "38"**, body = **0 rows**, muted = **«Источник подтвердил: риски не выявлены.»**
- **Backend payload (preserved, DMS-SPRNT-3):** `sprint.risk_queue` → `{ count: 38, queue: [38 rows], source: "REAL_AS21" }`; each row = `{task_key, title, status, assignee, blocked, overdue_days, age_days, reasons, rank}`.
- **Root cause:** `Pages.tsx:176` `const riskRows = rd.risks ?? []` — the capability field is **`queue`**, not `risks`. So `rd.count` (38) renders in the title but `rd.risks` is `undefined` → `riskRows=[]` → the empty-branch muted text. The UI simultaneously claims **38** and **"no risks found"**.
- This is exactly the P4 spec requirement violated: *"no false 'Риски не выявлены' caused by wrong nesting"* and *"risk queue exact vs backend payload"*.
- Row rendering is also field-mismatched (even after `queue`): UI reads `row.key`/`row.risk_score`; the source rows use `task_key`/`rank`.

### D-A223R-2 — Sprint Throughput: shows "—" instead of the source value
- **Rendered (preserved):** Throughput insight value = **"—"**, muted = "завершённых задач · unit completed_tasks/calendar_day".
- **Backend payload (preserved):** `sprint.throughput` → `{ throughput: 1.385, unit: "completed_tasks/calendar_day", completed: 19, total: 73, ... }`.
- **Root cause:** `Pages.tsx:188` `String(td.throughput_tasks ?? '—')` — the capability field is **`throughput`**, not `throughput_tasks`. `td.unit` (same object) renders fine, proving the payload is unwrapped correctly; only the value key is wrong.

**Classification:** The owner's A223R fix correctly introduced `getCapabilityData()` (envelope unwrap) and aligned the *metric-card* keys (Scope/Completed/Velocity/Predictability all correct), but left two pre-existing SprintPage leaf accessors unaligned to the actual V4 capability schema. The unwrap **exposed** them (A223 showed all "—"; A223R shows correct cards + a self-contradicting risk queue + a dropped throughput).

**Evidence preserved:**
- `po-agent-platform-v2/qa_artifacts/a223r_p4_red.json` — exact rendered Risk Queue title/body + Throughput value + both backend capData objects.
- `qa_223r_browser_c/p4_red_sprint.png` and `qa_223r_browser_c/p4_sprint_dms.png` — full-page screenshots.
- `po-agent-platform-v2/qa_artifacts/a223r_pages2.json` — full per-query capData for the sprint page.

**Owner fix (SprintPage only, no backend):**
1. `Pages.tsx:188` `td.throughput_tasks` → `td.throughput`
2. `Pages.tsx:176` `rd.risks` → `rd.queue`; align row fields `row.key`→`row.task_key`, `row.risk_score`→`row.rank` (`reasons` already present)
3. Non-mocked regression: for a sprint with a non-empty risk queue, the Risk Queue body renders `count` rows (not the empty muted text) and Throughput renders the source `throughput` value.

**Per the STOP rule, I stopped at this first confirmed RED.** Phases P5–P9 were captured as context below (not a full gate).

---

## P5 — Releases — observed GREEN (context, not the failing boundary)

- **OLP 1.6.0** (source-conditional): all 5 queries `FAILED v4_capability_unavailable` → capData `null`. Rendered: 3 SOURCE_UNAVAILABLE state panels, all 4 metric cards **"—"**, `muted=[]` (no «риски не выявлены», no 0/0 deps, no "none" blockers), no pseudo-forecast. ✓
- **WMB 24Q1**: 3 state panels (SOURCE_UNAVAILABLE×2 + NEEDS_CLARIFICATION), all cards **"—"**. ✓

SOURCE_CONDITIONAL semantics preserved: state panels, never fake 0/empty. (Label is the coarse SOURCE_UNAVAILABLE via the known F-A223-1 string-inference; the panel behavior is correct.)

## P6 — Team — observed state-safe (context)

- Bare team queries (`Покажи нагрузку команды`, etc.) **consistently** return `NEEDS_CLARIFICATION` (3/3 stable; `v4_ready_without_source_observation`) — a pre-existing LLM space-ambiguity on the frozen backend (17fdacb), **not** an A223R regression. UI renders clarification panels + all cards **"—"** (no fake 0, **no hardcoded 40h**, capacity input placeholder «Пусто = owner policy»). Competency note present. ✓
- Field mapping verified correct via a scoped probe: `Покажи нагрузку команды DMS` → `workload:[{member, active_tasks, wip, blocked, completed}]` — exactly the fields `TeamDashboard` reads (`row.active_tasks`/`row.wip`/`row.blocked`). Capacity DMS → `v4_capability_unavailable` (source-safe). The `getCapabilityData` unwrap (P1) + these field names mean the team page WILL render correctly when the backend returns data; the bare-query clarification is a separate (non-A223R) planner characteristic.

## P7 — Tasks — observed (context)

- **clarify** (`Найди login`): NEEDS_CLARIFICATION state panel ✓
- **empty** (`Найди zzzqqqxyz123`): typed **ERROR** state panel (fail-closed, no fake empty grid) ✓
- **non-empty** (`Найди DMS-380`): routes to `task.lookup` → capData `{task_key, task, ...}` (single `task`), but `TasksPage` grid reads `data.tasks` (plural) → **0 cards**. A list-mode query (assignee/status/sprint) is the intended non-empty path; a single-key lookup returns a detail, not a list. **Non-blocking observation** (pre-existing routing/field class), not the failing boundary.

## P8 — Chat — observed GREEN (context)

- **daily brief:** 2 tables, 3 headings, 0 raw-markdown (##/**/|---|), evidence + feedback present ✓
- **competency (DMS-380):** 1 table, 0 raw-markdown, evidence + feedback present ✓

## P9 — audit (context)

task-api log delta from baseline 13894 (377 lines): **0 mutations, 0 local fallback reads, 0 unscoped task-query, 377 swtr-read, 0 ×500.** No tenant-wide broadening, no local-truth fallback, no writes. Clean.

---

## Findings summary

| ID | Severity | Boundary | Description |
|----|----------|----------|-------------|
| **D-A223R-1** | **BLOCKING** | P4 Sprint | Risk Queue reads `rd.risks` but source field is `queue` → title "38" + body «риски не выявлены» (38 real risks hidden). `Pages.tsx:176`. |
| **D-A223R-2** | **BLOCKING** | P4 Sprint | Throughput reads `td.throughput_tasks` but source field is `throughput` (1.385) → renders "—". `Pages.tsx:188`. |
| F-A223R-1 | Non-blocking | P5 | `v4_capability_unavailable` → coarse SOURCE_UNAVAILABLE label (panel behavior correct). Inherited from A223 F-A223-1. |
| F-A223R-2 | Non-blocking | P7 | Single-key "Найди \<key\>" → `task.lookup` (`task`) vs grid `data.tasks`; list modes are the intended path. |
| F-A223R-3 | Non-blocking | P6 | Bare team queries → NEEDS_CLARIFICATION (pre-existing LLM space-ambiguity, frozen backend); field mapping verified correct. |

**Note:** The P2 blocking defect (A223 `NaN/100`) is **CLOSED**, P1/P3/P5/P8 are GREEN. The gate is RED solely due to the two SprintPage field-name mismatches (D-A223R-1/2) that the A223R unwrap newly exposed.

---

## Verdict

**`AGENT_CORE_V4_UI_STATE_LINEAGE_RED_A223R`**

**First failing UI boundary:** P4 Sprint page — (1) Risk Queue title "38" contradicts body «риски не выявлены» (`rd.risks` should be `rd.queue`), (2) Throughput shows "—" instead of source `throughput`=1.385 (`td.throughput_tasks` should be `td.throughput`).

**STOP.** No checkpoint. No Learning Reviewer.

**Preserved evidence:** `qa_artifacts/a223r_p4_red.json` (rendered + backend payload), `qa_223r_browser_c/p4_red_sprint.png` + `p4_sprint_dms.png`, `qa_artifacts/a223r_pages2.json`, `qa_artifacts/a223r_p2_quality.json`.

**Services left running:** agent 8212 (PID 29982 @ 17fdacb), task-api 8241, MCP 3000, vite 5175 (PID 86408, [::1]).
