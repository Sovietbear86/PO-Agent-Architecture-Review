# A221R — Full V4 Canonical-54 A/B/C Certification: Row-10 Re-gate + Matrix Continuation

**Verdict: `AGENT_CORE_V4_FULL_54_ABC_RED_A221R`**
**First failing canonical row (this re-gate): 49 (`tasks.search` — task search by product/space)**
**First failing boundary: A/contract — `task.search` guard rejects the only remaining space-only collection path**

---

## 1. Summary

- Owner's row-10 fix **CERTIFIED**: row 10 re-gated **GREEN_SOURCE_CONDITIONAL** (typed `v4_capability_unavailable`, exact directory-backed trajectory, Oracle B membership=0).
- Matrix continued from row 11: **48/54 certified GREEN** (35 `GREEN_SOURCE_READY` + 13 `GREEN_SOURCE_CONDITIONAL`), rows 1-9 not re-run (per instruction), row 10 recertified.
- **Confirmed RED at row 49** (deterministic, root-caused, safety-intact). Stopped per the first-confirmed-RED rule.
- **Rows 50-54 and Phases 8-13 NOT_RUN** (resumable).
- **0 production code changes by QA.** P11 audit **PASS** over the A221R window.

---

## 2. Baseline / owner fix verification

- **START_HEAD:** `f132bc15a6dad246fb9836c3c187200b66f52b47` (docs-only over the fix).
- Owner fix commits: `3347e33` fix (plugin-only: `v4_plugins/task_catalog.py` +76/-6), `c18a03d` test (new `test_agent_core_v4_task_search_release_regression.py`, 3/3).
- Fix content: new `build_task_search_release` handler (bounded `get_release_tasks(release_id, space)`; empty membership → typed `V4CapabilityUnavailable`); skill procedure rewritten to `space.resolve → release.search(require_single) → task.search_release` with **explicit "do NOT use task-based release.resolve"**; capability now requires `space`.
- Unit level: new regression **3/3**; V4 suites **213 passed** + 1 **stale** test (see F1).
- Agent restarted on START_HEAD (PID 8547); smoke DMS-380 COMPLETED 19s.

### Row 10 re-gate — GREEN (fix certified)
- 3 fresh-session probes + formal runner run: trajectory `space.resolve → release.search → task.search_release(release_id=7a84006f-7823-4052-ae46-b94f5165518e, space=WMB)` → **typed `v4_capability_unavailable`** ("release is source-verified, but current REAL AS21 task data does not expose populated release/fix-version linkage"), no fabrication, 14.8-17s.
- Oracle B: WMB 24Q1 membership = 0 rows (proven independently) → `GREEN_SOURCE_CONDITIONAL`.
- A221 zero-option `release.resolve` dead-end is GONE.

---

## 3. Matrix results (rows 1-49)

| Group | Rows | Result |
|-------|------|--------|
| 1 task discovery/search | 1-10 | 8 GREEN_SOURCE_READY + 2 GREEN_SOURCE_CONDITIONAL (row 6 MSG REAL_EMPTY, row 10 release SC) |
| 2 task intelligence | 11-20 | 10 GREEN_SOURCE_READY (aging 81/81 exact, similar top-5 exact vs production token_jaccard_v1, history/tis labels exact, DMS-352 blockers grounded) |
| 3 sprint/flow | 21-32 | 8 GREEN_SOURCE_READY (health/scope/velocity/wip exact; cycle 206.06 class; carryover; risk queue) + 2 GREEN_SOURCE_CONDITIONAL (scope_change, predictability — typed SC, baseline absent in source) |
| 4 team | 33-40 | 4 GREEN_SOURCE_READY (workload/wip/blocked/bottlenecks member-exact) + 4 GREEN_SOURCE_CONDITIONAL (capacity/competency_match/assignee_recommendation typed SC; no estimates/competency config in source) |
| 5 release+portfolio | 41-48 | 6 GREEN_SOURCE_CONDITIONAL (release.health/scope/progress/blockers/dependencies/risk_queue — all typed `v4_capability_unavailable` via directory-backed release.search, membership=0) + 2 GREEN_SOURCE_READY (portfolio.overview, po.attention_queue exact) |
| 6 additions | 49 | **RED** (row 49); 50-54 NOT_RUN |

**Totals: 48/54 GREEN (35 READY + 13 SC), 1 RED (49), 5 NOT_RUN.**

---

## 4. Row 49 RED — `tasks.search` (task search by product/space)

- **Queries probed:** "покажи задачи по продукту DMS" (first rep), "найди все задачи по продукту DMS", "все задачи в DMS" ×2, "список всех задач в DMS".
- **Observed behaviors (deterministic):**
  1. `tasks.search` (loaded correctly) → `space.resolve → task.search(space=DMS)` → **zero-option `v4_capability_clarification`**: "Для task.search нужен исполнитель, спринт или явно ограниченный запрос без исполнителя; уточните фильтр." (reproduced 4/4).
  2. Alternate phrasing "покажи задачи по продукту DMS" → planner silently re-scoped to **current sprint** (`sprint.current → task.search`, 73 tasks) — COMPLETED on a **different scope** than requested (product-wide), no disclosure.
- **Control (adjacent path works):** "открытые задачи в DMS" (space+status) → COMPLETED 92 tasks via `task.search_status` — the capability layer itself handles bounded space+status collections.

### Root cause (pinned)
- Guard `agent_core_v4.py:925-926`: `if not any((assignee, sprint_id, space and unassigned)): raise V4NeedsClarification(...)`.
- Allowed `task.search` combinations: **assignee** (±space), **sprint_id** (±space), **space ∧ unassigned=true**. **Space-only is rejected** — and no dedicated task-catalog skill covers space-only collection (assignee/status/sprint/release/text/attachments each have one; product-wide does not).
- The capability's else-branch (`search_tasks('project = "<space>"', max_results=10000)` + space re-filter) exists in `_task_search` but is **unreachable** for space-only because the guard precedes it.
- Safety intact: fail-closed, 0 fabrication, 0 tenant-wide scans. The clarification is zero-option with misattributed phrasing (asks to "clarify the filter" although the user gave a bounded product filter).
- **Class:** same structural defect as A221 row 10 — a skill guard/procedure dead-end for a legitimate, bounded user intent.

### Owner fix (proposed, plugin/guard-level, not implemented)
1. Allow **space-only** in the `task.search` guard (it is bounded: one approved space, `max_results=10000`, space re-filter already present) — i.e., `if not any((assignee, sprint_id, space, unassigned))` with the unassigned branch unchanged; **or**
2. Give the `tasks.search` composition a dedicated space-only handler (bounded `project = "<space>"` read) that bypasses the person/sprint guard, keeping the guard for the other compositions.
+ non-mocked regression: "все задачи в DMS" must COMPLETED with the true space total (currently 432), not a zero-option clarification; and the sprint-narrowing alternate route must not silently substitute current-sprint scope for a product-wide request.

---

## 5. Findings (all non-blocking)

- **F1 (stale test, owner's):** `test_agent_core_v4_task_catalog.py::test_task_wave_progressive_catalog_exposes_procedure_and_typed_capabilities` asserts the **pre-fix** capability tuple `["release.resolve", "task.search_release"]`; the fix changed it to `["space.resolve", "release.search", "task.search_release"]`. The owner's new regression test (3/3) is the current contract. (Same test-logic class as A196-F1/A217C-F1.)
- **F-A221R-1 (QA oracle fix, row 12):** b12 required the word "estimate" in `task.quality` output; estimate is a planning attribute, **not** part of the formulation-quality contract (spec `required_fields=("task_key","score")`). Agent output was source-accurate (85/100, correctly flagged missing acceptance — DMS-380 description 6137 chars, no acceptance section, verified).
- **F-A221R-2 (QA oracle fix, row 18):** `row_is_open` counted 194 no-`workflow_status` rows as open (273 vs 81). Production `Task.is_open` (domain/models.py:110-113) is explicit: **undecodable statuses are NOT open**. Agent's 81-key set = exact known-status non-terminal aged≥7d set.
- **F-A221R-3 (QA oracle fix, row 20):** b20 used a naive key-inclusive jaccard; replaced with a faithful mirror of production `token_jaccard_v1` (tokens(title+description), stopword filter, {3,} token length, jaccard r3, top-5, reference excluded from matches). Agent output then matched exactly.
- **F-A221R-4 (QA oracle fix, row 33/34/39/40):** member-presence checks were case-sensitive; agent renders lowercase logins (`moiseev.a.n`) vs source `externalId` case (`Moiseev.A.N`). Made case-insensitive.
- **F-A221R-5 (manifest reps, rows 23/40/49):** reps changed to target the certified skill intents — row 23 "состав задач в спринте" → "анализ охвата спринта DMS-SPRNT-3" (scope-analysis intent; the old phrasing is row-9 task-list semantics and correctly routes to task.search_sprint); row 40 "распределение работ по компетенциям" → "распределение задач по статусам у исполнителей в DMS" (per spec "task/status distribution by assignee"); row 49 rep kept as product-wide (the defect is real).
- **F-A221R-6 (row 49 scope-narrowing, part of the RED):** for the soft phrasing "покажи задачи по продукту DMS" the planner completed with the **current sprint's** 73 tasks instead of the product-wide collection — a silent scope substitution worth fixing alongside the guard (see §4 owner fix, item 2).

---

## 6. Phase 11 — source/write audit (A221R window, task-api log lines 10463-10686)

| Check | Result |
|-------|--------|
| local DB/API factual reads (`GET /api/v1/tasks`) | **0** ✓ |
| local fallback reads | 0 ✓ |
| mutations (POST/PUT/PATCH/DELETE) | **0** ✓ |
| task-query total / unscoped | 32 / **0** ✓ |
| release membership total / unscoped | 14 / **0** ✓ |
| versions total / unscoped | 14 / **0** ✓ |
| sprint collections unscoped | 0 ✓ |
| assignee route | 0 ✓ |

**AUDIT PASS.** (Sprint collections this window went through the space-scoped task-query `sprint=` constraint route, A185-B1 pattern.)

## 7. Phase 12 — latency (PARTIAL, rows 1-49)

- all_rows: n=49, p50=10.2s, p95=33.7s, max=37.5s
- task_collection p95=37.4s (attachment rows); sprint_analytics p50=10.7s; team_analytics p50=7.6s; release_SC p50=11.7s; simple point p50=6.6s
- **pathological >60s: 0**
- Rows 50-54 + Phases 8-13 not run (null).

## 8. Phases NOT run (first-confirmed-RED stop)

Phases 8 (composition), 9 (clarification/session), 10 (Browser C full-surface), 11 (full window — partial done above), 12 (full — partial done above), 13 (retained extras). Runners prepared (`qa_221_p8/p9/p13_runner.py`, `qa221-browser-c.spec.ts`); resume after the row-49 owner fix.

## 9. Artifacts (resumable)

- `qa_artifacts/a221_matrix_progress.json` — RED_STOPPED, red_row=49, 48 GREEN + full row-49 RED record (5 determinism probes, root_cause, a221r_regate metadata).
- `qa_artifacts/a221_canonical54_manifest.json` — 54 rows, rep changes noted for rows 23/40/49.
- `qa_artifacts/a221_latency.json` — PARTIAL_A221R.
- `qa_artifacts/a221r_source_audit.json` — A221R window PASS.
- `qa_artifacts/a221_source_audit.json` — original A221 (rows 1-10) window, retained.

## 10. Next re-gate (A221R2, after owner row-49 fix)

1. Re-run row 49 (expect COMPLETED, true total 432 exact, no silent sprint narrowing);
2. Run rows 50-54 (release.forecast SC, po.daily_brief, po.status_report, po.reminder_draft, po.local_task_draft);
3. Run Phases 8-13 (runners ready);
4. Full-window P11 audit + full P12;
5. Final GREEN/RED per spec. Do not re-run certified rows 1-48 unless the fix could affect them (the proposed guard change does affect `task.search` consumers — rows 7/8/9/49-adjacent may need a quick re-probe at the owner's discretion).

**Services left running:** agent 8212 (PID 8547 @ f132bc1), task-api 8241 (81954, system py3), MCP 3000 (29268), UI 5175 [::1] (47416).

**STOP.** Awaiting owner fix for row 49 (`task.search` guard space-only / `tasks.search` dedicated space handler). No code changed by QA.
