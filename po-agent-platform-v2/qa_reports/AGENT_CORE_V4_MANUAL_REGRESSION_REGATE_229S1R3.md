# A229S1R3 — Manual regression re-gate: Overview KPIs + sprint/type composition

**Verdict:** `AGENT_CORE_V4_MANUAL_REGRESSION_GREEN_A229S1R3`
**START_HEAD:** `161f2a0123767eafb84e9c49040b167466da8b81` (`161f2a0`)
**Baseline checkpoint:** `be5131c83b7fd666c79af0e69e1b5cefd0961e62` (`checkpoint/v4-task-details-richtext-green-a229u2r`)
**Previous verdict:** `AGENT_CORE_V4_TASK_SEMANTICS_HIERARCHY_GREEN_A229S1R2` — manual UI testing then found 2 regressions (Overview KPI `—`; person+sprint+status+type `source_unavailable`)
**Owner delta (5db48e6..161f2a0, 7 files):** `frontend/src/recovery/OverviewDashboard.tsx`, `v4_plugins/_task_live_handlers.py`, `v4_plugins/task_catalog.py`, `tests/test_agent_core_v4_task_semantics_hierarchy.py`, `task-api/app/routers/swtr_read.py`, `task-api/tests/test_swtr_read_sprint_collection.py`, `GIGACODE_NEXT_ACTION.md`. **0 Core/planner/runtime changes.**

## P0 — integrity + focused regression — **GREEN**

- **Core byte-identity 6/6** vs be5131c: `agent_core_v4.py`, `agent_core_v4_robust.py`, `agent_core_v4_reliable.py`, `agent_core_v4_completion.py`, `v4_plugin_registry.py`, `llm/real.py` (blob-hash proven).
- **Skill inventory unchanged vs A229S1R2 (5db48e6):** 72 skills both sides, 0 added / 0 removed (A/B worktree probe). The 2 "extra" skills `task.type_analysis` + `task.hierarchy` are the A229S1R2 additions, not new in this delta. Canonical 54 unchanged (`SKILL_CATALOG` 54 entries, untouched file).
- **Focused tests:** `test_agent_core_v4_task_semantics_hierarchy.py` 5/5; catalog/registry/batch4/completion 55/55; full V4 blast `test_agent_core_v4*.py + test_v4*.py` = **247 passed, 1 failed** — the failure is `test_agent_core_v4_task_catalog.py::test_task_semantics_hierarchy_skills_are_extra_plugin_skills_not_canonical54_rows` asserting the stale tuple `capabilities == ("task.type_analysis",)`. The owner delta intentionally expands the capability set to `("space.resolve","sprint.resolve","sprint.search","sprint.current","task.type_analysis")` (exactly what the spec mandates), and this old assertion was not updated. **Test-logic class** (A222/A226R precedent), file untouched by the delta.
- **Frontend build:** `npm run build` (tsc && vite) exit 0.
- **task-api focused:** `test_swtr_read_sprint_collection.py + test_swtr_task_relations.py + test_swtr_read_canonical.py` = 37 passed, **3 failed** — all on `assert client.tql_calls == {0|2}` (got 1|3). Root cause: the timestamp-enrichment block (`1da4dae`, "preserve source timestamps on sprint tasks", A197-era — present at be5131c) fires whenever a canonical row lacks `created_at`/`deadline`; the 3 failing fixtures (`_nested_row`/`_sprint_rows`) never set them. **A/B-proven pre-existing:** read-only worktree at 5db48e6 (A229S1R2, previously certified) fails the same 3 identically. Not introduced by this delta; documented as stale A185-era test expectations. (The delta's own new `include_task_type` tests — which set `created_at`/`deadline` — all pass, 8/8.)

## P1 — Overview KPI regression — **GREEN**

**Forensics (no production code change needed to explain the regression):**
- A226R3 (report line 83) recorded KPIs `119/40/7` — at that time the `Дай обзор и риски` snapshot was planner-routed to a capability exposing top-level `active/completed/blocked` (routing is non-deterministic across catalog growth).
- `portfolio.overview` (wave_batch4.py) top-level data keys are `spaces/space_count/source_backed_space_count/total_current_sprint_tasks/total_blocked/source/scope` — **no top-level `active`/`completed`** (per-space `active`/`completed`/`blocked` are nested under `spaces[].*`). So `od.active ?? '—'` → `—` whenever the snapshot routed to `portfolio.overview`. No frontend code regression — the ambiguous NL dependency was the defect.
- Owner fix (verified in diff): removed `overviewQ`/`od`; all 4 KPI cards read `sd` (`po.status_report` via `statusQ`) gated on `stateAllowsBusinessData(statusState)`; `SnapshotRefresh` tracks only [attention, brief, status] (3 queries). `po.status_report` (wave_batch5_po.py) provides top-level `total/completed/active/blocked/completion_percent`.

**Independent API probe:** `Сделай status report` → COMPLETED, `po.status_report`, runtime_contract: **active=82, completed=29, blocked=5, completion=26.1%** (total 111).

**Browser re-gate (fresh session, 1440×900):**
- 4 KPI cards populated at ~115 s: **Активно=82, Завершено=29, Заблокировано=5, Готовность портфеля=26.1% — exact vs probe.**
- POST audit: exactly 3 snapshot queries — `Покажи очередь внимания`, `Сделай daily brief`, `Сделай status report`; **no `Дай обзор и риски` POST**; 0 direct :8241/:3000 calls; 0 non-2xx; 0 console/page errors.
- Attention Queue + Daily Brief sections intact and rendered.
- Manual refresh: stale KPI values kept during refresh (before == during snapshot), no 4xx/5xx. Screenshots: `p1_kpi_populated.png`, `p1_after_refresh.png` (/private/tmp/qa229s1r3/).

## P2 — live sprint task-type source contract — **GREEN** (space OLP, current sprint `OLP-SPRNT-9`, IN_PROGRESS 2026-10-05→19)

- **Route A** `GET /api/v1/swtr-read/sprints/OLP-SPRNT-9/tasks?space=OLP&complete=true&include_task_type=true`: 78 rows, `complete=true`, `membership_proven=true`, `source_path=get_sprint_tasks`, 1.5 s. Type distribution **100% resolved: bug=41 (Дефект), task=35 (Задача), epic=2 (Эпик); 0 missing, 0 fabricated UNKNOWN**; `source_data.swtr_suit` preserved (`{"code":"bug","name":"Дефект","icon":"skull_crossbones"}`); `created_at` present on all 78.
- **Route B (independent) `read_unit().suit`:** 8 sampled tasks (4 bug / 3 task / 1 epic) — **8/8 exact parity** of `task_type_code`/`task_type_name` vs `unit.suit.code`/`unit.suit.name`.
- **TQL membership cross-check** `find_units_by_filter(scrum_board_plugin_sprint="OLP-SPRNT-9")`: 78 rows, **membership parity 78/78** with route A, 0 rows with wrong sprint attribute, 0 undecodable statusType (distribution: Resolved|done 19, In progress|progress 15, Ready for QA|pause 14, Open|pause 13, QA|progress 5, Ready for review|pause 4, Need info|pause 4, Closed|done 1, Cancelled|done 1, В работе|progress 1, В работу|pause 1).
- **Flag off** (`include_task_type=false`): identity parity 78/78. The live primary `get_sprint_tasks` view returns `unit.suit` + `unit.createdAt` natively on this SWTR version (78/78 raw rows), so both variants resolve types from the primary view with **no extra TQL type read**; the `include_type` enrichment clause is only a fallback for sources whose primary omits `suit` (owner unit tests `test_sprint_type_enrichment_is_opt_in_and_source_backed` / `..._does_not_add_type_read_when_not_requested` lock the opt-in semantics; both pass).
- 0 local `/api/v1/tasks` reads (audit below).

## P3 — complex person+latest-sprint+status+type regression — **GREEN (6/6 exact)**

Independent oracle built immediately before the batch (MCP-direct, 78 rows, 0 drift on post-batch re-probe):
O1 Semavin+open+bug = [OLP-2974, OLP-3241, OLP-3357, OLP-3392]; O2 Semavin+open = same 4; O3 Semavin+bug = 15 keys; O4 open+bug = 27 keys.

| Case | Query (fresh conversation) | Terminal | Exact parity |
|---|---|---|---|
| P1a/b/c (×3) | `Покажи открытые задачи Семавина в последнем спринте по OLP с типом дефект` | `task.type_analysis` | **4/4 EXACT** (O1), all 3 runs |
| P2 no-type | `...в последнем спринте по OLP` (без типа) | `task.search(assignee=Semavin.M.M, sprint_id, status=not_completed, space)` | **4/4 EXACT** (O2) |
| P3 no-status | `Покажи задачи Семавина ... с типом дефект` | `task.type_analysis` (no status arg) | **15/15 EXACT** (O3) |
| P4 no-person | `Покажи открытые задачи ... с типом дефект` | `task.type_analysis` | **27/27 EXACT** (O4) |

- Trajectories: `space.resolve → [member.resolve →] sprint.current(OLP) → task.type_analysis` — **sprint resolved from source** (`OLP-SPRNT-9`), never a phrase guess.
- Terminal args preserve **all** constraints: `{"task_type":"defect","reference":"Семавин","space":"OLP","status":"not_completed","sprint_id":"OLP-SPRNT-9"}` (status omitted only where the query omits it).
- `source_assignee=Semavin.M.M`, `unknown_type_count=0`, `type_breakdown` exact (e.g. P3: bug 15 + task 4 out of scope 19).
- Agent-side reads (task-api log): bounded `GET /swtr-read/sprints/OLP-SPRNT-9/tasks?space=OLP&complete=true&include_task_type=true&limit=100&max_pages=100` ×5 — the new `_live_sprint_rows` shape; **0 `source_unavailable`, 0 local-store reads, 0 tenant-wide scans** (vs the pre-fix symptom).
- No model-side intersection: scope_count = full sprint-open set (57), count = type-filtered subset — server-side filtering.
- Drift re-probe after the batch: O1–O4 all unchanged (78 rows).

## P4 — error taxonomy audit — **GREEN**

- 76/76 focused taxonomy tests pass (`test_v4_owner_fix_contracts`, `test_task_api_as21_adapter`, `test_agent_core_v4_team_aging`, `test_agent_core_v4_batch5_po`, `test_agent_core_v4_completion_contract`).
- Unit probe of the new seam `_live_sprint_rows` (fake adapter, no Core edits):
  - `complete=false` → `AS21SourceUnavailable("REAL AS21 sprint membership is incomplete for OLP-SPRNT-9; exact composition is unproven")`
  - `membership_proven=false` → same typed raise; missing keys → same.
  - healthy path → rows via `adapter._map`, bounded params `{complete:true, include_task_type:true, limit:100, max_pages:100, space:"OLP"}`.
- Transport failures: production `_get_resilient` (task_api.py) retries transient 502/503/504/timeouts and raises typed `AS21SourceUnavailable` on budget exhaustion — raw httpx errors do not leak through the production chain; runtime maps `AS21SourceUnavailable` → typed `source-unavailable` (proven live in P1-era smoke: `Источник AS21 временно недоступен...`, 0 evidence, no fabrication).
- Reachable-but-unprovable is typed insufficiency, never fake-empty (P2: 100% type resolution; no UNKNOWN fabrication anywhere).

## P5 — retained UI + architecture — **GREEN**

**Retained API controls (fresh conversations, independent oracles):**
- Person+space+status: `Покажи открытые задачи Жданова в DMS` → `task.search(assignee=Zhdanov.A.Ni, space=DMS, status=not_completed)` **COMPLETED, 1/1 EXACT** = [DMS-1] vs fresh task-api person+space oracle (7 rows; DMS-371 drifted to `done` since A227 — oracle captured pre-batch, source-verified per-row statusType).
- Hierarchy: `Покажи иерархию задачи DMS-267` → `task.hierarchy` COMPLETED, exact A229S1R2 chain `CRPV-90180 → DMS-253 → DMS-267`, depth 2, epic DMS-349.
- Person+sprint: covered by P3 trajectories (all 6 preserve `sprint_id` in the terminal call).

**Retained browser (1440×900, /tasks):** free-text `Задачи Семавина в спринте OLP-SPRNT-9` → **19 task cards** (exact vs oracle 19), card click → TaskDetailsDrawer opens with task content, **no raw JSON/ProseMirror leak**, close works, 0 non-2xx, 0 console errors. (Single-key lookup `DMS-380` renders as rich answer — expected: cards render only for task collections; drawer path fully exercised via the collection.)

**Architecture audit (delta 5db48e6..161f2a0):**
- Core byte-identical (P0); **no phrase router** and **no hardcoded person/space/sprint/type** in any diff hunk (grep both sides clean).
- **No local task-store fallback** in the new sprint/type path: `_live_sprint_rows` uses the live `/api/v1/swtr-read/sprints/{id}/tasks` via `_get_resilient` and fails closed; production `get_sprint_tasks` (hardened + production adapters) is live-route only.
- **0 mutations** (task-api log: 0 POST/PUT/PATCH/DELETE), **0 local `/api/v1/tasks` reads**, **0 fully-unscoped task-query** (65 calls: all `space=`-scoped or single-`assignee=` team-summary reads from `po.status_report.by_space_tasks` — pre-existing bounded design, unchanged file).
- Public/community repo untouched: sole remote `origin` (Sovietbear86/PO-Agent-Architecture-Review); only the QA report is committed.

## Findings (non-blocking)

- **F1 (pre-existing, A/B-proven):** 3 stale A185-era `tql_calls` assertions in `test_swtr_read_sprint_collection.py` fail at both 161f2a0 and 5db48e6 (timestamp enrichment `1da4dae` predates the delta; fixtures lack `created_at`/`deadline`). Owner may refresh those fixtures/assertions.
- **F2 (test-logic, pre-existing file):** `test_task_semantics_hierarchy_skills_are_extra_plugin_skills_not_canonical54_rows` asserts the pre-delta capability tuple; the delta's expansion is spec-mandated.
- **F3 (pre-existing routing edge, not in scope):** bare sprint-id query `OLP-SPRNT-9` → planner FAILED (ambiguous identifier, typed, no fabrication). Natural-language forms all work.
- **F4:** `.env` pins `TASK_API_BASE_URL=http://localhost:8003` (first `AliasChoices` alias wins over `PO_AGENT_TASK_API_BASE_URL`) — agent must be started with explicit `TASK_API_BASE_URL=http://127.0.0.1:8241` override; also the stale-agent gotcha recurred (wrapper kill left python child 18757 holding 8004 — killed the real child before the certified run).

## Services left running (all on 161f2a0)

- agent 8004 — PID 28341 (log `/private/tmp/qa229s1r3_agent.log`)
- task-api 8241 — PID 18282 (started 09:57 from 161f2a0 tree; auto-reconnected to fresh MCP; log `/private/tmp/qa229s1r3_taskapi.log`)
- MCP-SWTR 3000 — PID 27466 (fresh restart; log `/private/tmp/qa229s1r3_mcp.log`)
- vite [::1]:5175 — PID 25816 (log `/private/tmp/qa229s1r3_vite.log`)

## Recommendation

**FREEZE checkpoint `checkpoint/v4-task-semantics-hierarchy-green-a229s1r3` on `161f2a0`.** Both manual-regression defects (Overview KPI `—`; person+sprint+status+type `source_unavailable`) are closed and retained controls are green. Owner may sync the certified delta to public/community. Next assignment returns to **A229R1 latency verification** on this checkpoint.

QA artifacts: `/private/tmp/qa229s1r3/` (p1_browser.json + screenshots, p2A*.json, p2b_p3_oracle.json, p3_*.json, p3_drift_after.json, p4 probe output, p5_*.json + screenshots). Untracked QA scripts in repo root: `qa_229s1r3_p1_browser.mjs`, `qa_229s1r3_p2b_p3_oracle.mjs`, `qa_229s1r3_p3_runner.mjs`, `qa_229s1r3_p4_probe.py`, `qa_229s1r3_p5_retained.mjs`, `qa_229s1r3_p5_ui.mjs`.
