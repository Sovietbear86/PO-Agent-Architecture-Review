# AGENT_CORE_V4_PO_ACCEPTANCE_A227R3

**Assignment:** A227R3 — P3-B re-gate (owner's declarative fix for person+phrase search), then retained P3 controls, then P4–P7, strict first-RED stop.
**Verdict:** `AGENT_CORE_V4_PO_ACCEPTANCE_GREEN_A227R3`
**START_HEAD:** `f65bd94d6a7ad98635f2c27429354b158713b3e4`
**A227 baseline:** `db5e35f1b378b6ffde0c10085af8b68e4bf1e6b5`
**A227R2 HEAD (prev, RED on P3-B):** `0ddfd71`
**A227R2 code base:** `b5c0f96`
**Date:** 2026-10-01

---

## Summary

The owner's **declarative / plugin-only** A227R3 remediation is **CERTIFIED**. The A227R2 sole blocking defect (P3-B: "Задачи Семавина по рискам" non-deterministic, person→composite planner bounded-repair failures) is **CLOSED** — 5/5 runs now complete deterministically via the single-capability `task.search_text` path with **zero** `member.resolve` hops, phrase + person reference preserved, source-backed identity, exact REAL_EMPTY parity, and **zero** tenant-wide scans. All retained P3 controls (A/C/D), P4 (single Predictability widget + `н/д` + task cards/persistence), P5 (quality refresh isolation), P6 (aging live parity DMS >7/>15), and P7 (retained regression + source audit) are **GREEN**. **No RED encountered** across the full matrix.

**Owner A227R3 remediation** (`b5c0f96`→`f65bd94`), code-level = declarative only:
- `core.py` — `tasks.search` skill description now explicitly defers text/phrase searches to `task.search_text`.
- `task_catalog.py` — `task.search_text` capability description updated ("resolves the person source-backed internally, so a separate member.resolve step is not required"); skill procedure now instructs "call task.search_text directly with the literal phrase … pass that natural person text in reference … Do not add a separate member.resolve hop".
- `tests/test_agent_core_v4_text_person_plugin.py` — new (81 lines).
- `frontend/src/recovery/Pages.tsx` — 5 lines (owner's `e7cb30a` duplicate sprint-predictability-card removal, relevant to P4).
- `_task_live_handlers.py` **unchanged** — the handler `build_task_search_text` (line 204) already resolves the person internally via `_source_assignee_from_args` → `_resolve_assignee_identity` → `_member_resolve`, then calls `_live_query(phrase, space, assignee)` → `task-query?phrase=&assignee=`.
- Commits: `fabb2e2` (single-capability), `6aeb6ee` (disambiguate structured vs text), `8ac1ca1` (test), `abb01e9`/`7b0d302` (docs), `f65bd94` (assign).

---

## P0 — Static audit, tests, services (GREEN)

- **P0.1** START_HEAD `f65bd94`, clean tracked worktree.
- **P0.2** Stable Core/LLM **zero-diff** vs A227 baseline `db5e35f` (blob-hash proven): `agent_core_v4.py`, `agent_core_v4_reliable.py`, `agent_core_v4_robust.py`, `agent_core_v4_pluginized.py`, `llm/real.py`, core tests — all zero diff. Net owner diff is **plugin + frontend only**.
- **P0.3** Focused tests (text_person + status_norm + attachment + retained) = **39/39 passed**; full V4 blast radius = **233/233 passed**.
- **P0.4** Agent (PID 97697) + Vite (PID 97734) restarted on `f65bd94`; task-api (PID 15039) + MCP-SWTR (PID 25954) reused. Liveness verified: agent 200 `/live`, task-api connected (48 tools).
  - Agent env: `PO_AGENT_AGENT_CORE_V4_ENABLED=true`, `PO_AGENT_AS21_MODE=task-api`, `PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8241`, `PO_AGENT_EXPECTED_HEAD=f65bd94`.

## P3-B — "Задачи Семавина по рискам" (5/5 GREEN — A227R2 defect CLOSED)

Fresh REAL AS21 oracle (captured 2026-09-30T21:02Z, `/private/tmp/qa227r3_p3b/oracle.json`):
- Canonical identity for "Семавин": `Semavin.M.M` (via `/assignees/resolve?reference=Семавин`, source=REAL_AS21).
- Source route `task-query?phrase=риски&assignee=Semavin.M.M` → count=0, source_complete=True, all 5 spaces completed.
- Independent substring: Semavin full collection = 346 tasks, **0** with "риск"/"risk" → confirms **REAL_EMPTY**. Expected: count=0, keys=[].

5-run matrix (`/private/tmp/qa227r3_p3b/results.json`), **ALL 5 PASS**:
| # | status | terminal | member.resolve hops | ts_args | count | parity | source | exception | completion | elapsed |
|---|--------|----------|--------------------|---------|-------|--------|--------|-----------|------------|---------|
| 1–5 | COMPLETED | `task.search_text` | **0** | `{"phrase":"риски","reference":"Семавин"}` | 0 | exact | REAL_AS21 | None | runtime_contract | 11.8–28.7s |

**The declarative fix works as intended:** the planner now calls `task.search_text` directly (no `member.resolve` hop), preserves both the literal phrase and the natural person reference, and the handler resolves the identity source-backed internally. Error fields clean across all 5 runs (`exception_type=None`).

**Tenant-scan window audit** (`qa_227r3_p3b_window2.py`, control run): COMPLETED, `count=0`, `keys=[]`, source=REAL_AS21; new source lines in window = only `assignees/resolve?reference=Semavin.M.M` + `task-query?phrase=риски&assignee=Semavin.M.M`; **unscoped task-query in window: 0**.

## Retained P3 controls (one each, all GREEN)

Fresh oracles (`/private/tmp/qa227r3_controls/oracle.json`) + one control each:
- **P3-A** "Найди открытые задачи Калачанова с вложениями в пространстве WMB" — oracle: 5 WMB Kalachanov tasks, **0 open** (all terminal) → REAL_EMPTY. Control: COMPLETED, `count=0`, `keys=[]`, parity=**True**.
- **P3-C** "Задачи в работе в сентябрьском спринте по DMS" — oracle: DMS-SPRNT-3 79 tasks, **11** canonical IN_PROGRESS. Control: COMPLETED, caps=[space.resolve, sprint.search, task.search], `count=11`, **exact** 11 keys (DMS-104/253/269/272/343/349/357/399/401/405/452), parity=**True**.
- **P3-D** "Спринты в DMS" — oracle: 3 sprints. Control: COMPLETED, caps=[space.resolve, sprint.list], `keys=[DMS-SPRNT-1, DMS-SPRNT-2, DMS-SPRNT-3]`, parity=**True**.

## P4 — Task cards/persistence + single Predictability widget (GREEN)

Browser C (Playwright, `/private/tmp/qa227r3_p4/`):
- **Exactly ONE** Predictability widget on the Sprint page: `predMetricCount=1`, no separate Predictability panel (`predPanels=[]`; the "Predictability / Forecast" insight-card is on the Releases page = `release.forecast`, distinct).
- Baseline-absent rendering: value=`**н/д**`, hint=`**AS21 не отдаёт committed baseline на старт спринта**` (explicit source-baseline reason), `anyPercentOnPred=false` (no fabricated %). DMS-SPRNT-3 `sprint.predictability` executes and returns typed source-unavailable (no committed baseline) → `stateAllowsBusinessData=false` → `н/д`+reason.
- **Task cards / local-task persistence:** local task `LOCAL-0001 "QA локальная задача A227R3"` created via drawer → rendered (`.local-task-list-row`) → persisted in `localStorage` (`po-local-tasks`) → **retained after page reload** (retained=true). Source task cards: "Задачи в работе в сентябрьском спринте по DMS" → **11** `.task-card` (exact P3-C IN_PROGRESS set), no empty-data.

## P5 — Quality refresh isolation (GREEN)

Browser C (`/private/tmp/qa227r3_p5/`):
- Initial mount: 4 snapshots [quality, missing, acceptance, aging].
- **Top refresh** (`.page-heading .snapshot-refresh`) → **newCount=3**, classes=[quality, missing, acceptance], **agingFired=false** → top refresh fires only the task-quality group.
- **Aging refresh** (`.aging-toolbar`) → **newCount=1**, classes=[aging], **qualityGroupFired=false** → aging is isolated.
- **Stale kept while refreshing:** during the top refresh (button="Обновляем…"), metric values `["85/100","0/100","1","REWORK"]` retained (`staleKept=true`) — `useSnapshotHarness` keeps the prior `result` until a new one resolves (and on error).
- Code basis: task group uses `taskRefreshNonce` (quality+missing+acceptance, top `SnapshotRefresh` shows only those 3 `updatedAt`); aging uses a separate `agingRefreshNonce` + own "Обновить".

## P6 — Aging live parity DMS >7 and >15 (GREEN)

Exact oracle reproducing `build_task_aging` (team_scope=true, space=DMS, union of `task-query?space=DMS&assignee={login}` over all 16 team logins, `is_open AND age_days >= threshold`): union=**319** rows (all with source created_at, 0 errors) → **≥7d: 47**, **≥15d: 39** (`/private/tmp/qa227r3_p6/oracle.json`).

Agent runs (`/private/tmp/qa227r3_p6/results.json`):
- "…старше 7 дней" → COMPLETED, `task.aging`, `count=47`, **exact key parity**, runtime_contract, no exception.
- "…старше 15 дней" → COMPLETED, `task.aging`, `count=39`, **exact key parity**, runtime_contract, no exception.

**Bounded-reads / no-tenant-scan window audit** (`/private/tmp/qa227r3_p6/audit.json`): 16 task-query lines in window, **16 space+assignee scoped, 16 space=DMS scoped, 0 unscoped, 0 local `/api/v1/tasks` reads**.

## P7 — Retained regression + source audit (GREEN)

Browser C + source audit (`/private/tmp/qa227r3_p7/`):
- **Local CRUD:** create → edit (status IN_PROGRESS + title via drawer) → delete; `createEditDeleteOk=true`, **mutationsDuringCrud=0** (0 AS21 writes), rowsAfterDelete=0.
- **Platform V + chips:** sidebar `.works-logo`="**Platform V**", brandTitle="PO Space", subtitle="DB Tribe". Chip mechanisms (`.risk-chip` team blocked, `.local-tag`) present; team blocked chips=0 (no blocked tasks currently — conditional, correct).
- **Sprint DMS-SPRNT-3** (data-driven wait): Scope=**79**, Completed=**28**, Velocity=**28 tasks/sprint**, Predictability=**н/д** (real data + correct baseline-absent state).
- **Release limitation:** WMB 24Q1 forecast → typed `SOURCE_UNAVAILABLE`, `bodyHasUnavailable=true`, **no fake zero date** (fail-closed, consistent with A227R2/Batch 6 release-linkage unpopulated).
- **Team utilization:** 9 `.capacity-row` / 9 `.utilization-cell` / 13 `.team-member-row` (real utilization rows).
- **Backgrounds / overflow:** at 1440×900 and 1366×850, `overflowX=false` (no horizontal scroll), `bodyBg=rgb(2,10,19)` (dark glass).
- **Source audit (whole P7 window):** **localReads=0, mutations=0, unscopedTenantScans=0**.

---

## Source audit (session-wide)

- **0 local `/api/v1/tasks` reads** (no legacy local-store truth).
- **0 mutations** (no POST/PUT/DELETE/PATCH writes to task-api; local tasks are browser-only `localStorage`).
- **0 tenant-wide scans** (all `task-query` calls space- and/or assignee-scoped; P3-B + P6 window audits confirm 0 unscoped).
- All reads bounded to REAL AS21 via task-api → MCP-SWTR.

## Non-blocking observations

- **F1 (timing, not a defect):** the first P7 pass read the Sprint/Release/Team UIs before the slow snapshots rendered (sprint showed transient `—`, release forecast `LOADING`, team 0 rows). A data-driven re-run (`qa_227r3_p7b.mjs`) confirms all render correctly (Sprint 79/28/28/н/д, Release SOURCE_UNAVAILABLE, Team 9 rows). This is a harness settle-wait artifact, not a production issue.
- **F2 (aging boundary):** aging parity is time-sensitive (a task can cross a day boundary between oracle capture and the agent run). Observed runs matched exactly; any ±1 near-boundary drift on a future re-run would be environmental, not a defect.
- **F3 (pre-existing, out of scope):** plain "Утилизация команды DMS"-style phrasing routes to `team.utilization_actual` (A215F behavior); not part of this assignment's scope.

## Services left running

- Agent `8004` (PID 97697 @ `f65bd94`), task-api `8241` (PID 15039, system py3), MCP-SWTR `3000` (PID 25954), Vite `[::1]:5175` (PID 97734).

## Recommendation

**A227R3 is GREEN.** The owner's declarative single-capability text-person fix closes the A227R2 P3-B defect with no Core/LLM change and no regression across retained P3–P7. Recommend proceeding to the next assigned phase on explicit instruction.
