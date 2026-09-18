# A197 — Agent Core v4 Full Existing-Catalog Regression Regate (27 skills)

**Date:** 2026-09-18
**Branch:** `feat/core8-real-query-hardening-v2`
**START_HEAD:** `303f5a9a0982b3817a5953bd601c2cba161f3d81`
**Owner window since A196 (395a614..303f5a9):** `60933ca` (bounded aging/similar/attachment fan-out), `01cc11d` (plugin bindings for aging/similar), `ff02bd6` (task-api live timestamps), `088d6f7` (task.quality UIContract), `eb13bfe`/`f01f27f`/`6c24634` (tests), docs.
**Role:** QA/adversarial tester + service operator only. No production changes.
**Permanent rollback:** `0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`

## Verdict

**`AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_RED`**

D2 (attachments) and D1-similar are **CLOSED** and proven. **D1-aging is NOT closed**: the owner's `ff02bd6` timestamp-preservation fix uses snake_case field names (`created_at`) while the SWTR raw TQL rows expose camelCase (`unit.createdAt`). All 409 live DMS rows therefore arrive at the agent without timestamps, the adapter falls back to `datetime.now()` (`task_api.py:381`), `age_days = 0` for every task, and `task.aging` returns **"0 tasks" as COMPLETED** against a live ground truth of **81** open DMS tasks ≥7 days old (oldest DMS-1, 205 days). A factually wrong count is presented as a complete, source-backed result — exactly the fabrication class the spec forbids ("no fabricated age when source timestamp is absent"; here the timestamp **is present in the source** and is dropped in transit).

27/27 skills executed: **19 GREEN, 5 SOURCE_CONDITIONAL, 1 RED (task.aging)**.

---

## Phase 0 — start / architecture audit (PASS)

- `git pull --ff-only` → `395a614..303f5a9`; tracked worktree clean except the 3 pre-existing files (`GIGACODE.md` owner doc, `.po_agent/learned_policies.json` runtime artifact, `frontend/vite.config.ts` QA proxy edit) — none part of the owner diff.
- Owner diff touches **only** `v4_plugins/` (plugin boundary), `task-api/app/routers/swtr_query.py` (source boundary), tests, docs. **Zero** planner / Agent Core / completion edits.
- `build_task_aging`: requires `space` or `assignee` (else `AS21SourceUnavailable`), collects via `_live_rows` → `GET /api/v1/swtr-read/task-query` (`limit=100`, `max_pages=100`), no tenant-wide `search_tasks("")`.
- `build_task_similar`: source task resolved via live `task-query?phrase=<key>&space=<space>`; candidate corpus = the task's own space only; `token_jaccard_v1`, top-5.
- `build_task_search_attachments`: `max_fanout=250` guard raises `AS21SourceUnavailable` **before** fan-out for broad space-only queries; `asyncio.Semaphore(12)` bounds concurrent file calls. Bounded/fail-closed, not timeout masking.
- No local `/api/v1/tasks` truth in any new handler.
- Services restarted at START_HEAD: task-api 8241 (PID 44407), agent 8212 (PID 44579, `PO_AGENT_EXPECTED_HEAD=303f5a9…`), UI 5175 (PID 22389), MCP-SWTR 3000 (PID 45891). All 200.

## Phase 1 — automated suites

| Suite | Result |
|---|---|
| `tests/test_agent_core_v4*.py` | **88 passed, 1 failed** (F1 below) |
| `tests/test_v4*.py` (incl. `test_v4_owner_fix_contracts.py` — new bounded aging/similar/attachment contract tests) | **20 passed** |
| `task-api/tests -k swtr` | **37 passed, 1 failed** (pre-existing stale `test_s21_agent_integration.py` from first commit `6b3bee0`; asserts removed `SWTRAdapter.mcp_host` attribute; unrelated to this window) |
| `tests/test_agent_core_v4_plugin_registry.py` (P7) | **11/11 passed** (0.43s) |
| frontend `tsc --noEmit` + `vite build` | **GREEN** (build 825ms) |

**F1 (test-logic bug, non-blocking):** owner-refreshed `test_task_wave_capabilities_bind_only_through_registry_contract` builds `V4PluginRegistry((PLUGIN,))` with the task plugin alone, but `task.search_sprint`/`task.search_release` skills legitimately reference **core** capabilities (`sprint.resolve`, `task.search`, `release.resolve`) → registry constructor fail-closes with "references unknown capabilities". Production `discover_v4_plugins()` (all plugins) validates fine (discovery test passes). Same test-logic class as A190's two test bugs. Owner should bind the test against the full discovered registry (or a stubbed core plugin).

**task.quality UI contract registered and live:** response top-level `ui = {"result_kind":"analysis","preferred_widget":"task_analysis","required_fields":["task_key","score"]}` (088d6f7 confirmed end-to-end; UI panel renders `widget: task_analysis · kind: analysis` — see P6 C4).

## Phase 2 — fresh REAL AS21 Oracle (all refreshed, not reused from A196)

| Entity | Live value | A196 (drift) |
|---|---|---|
| DMS task-query rows | 409 (open 85 / terminal 134 / no-status 190) | 190 statusless retained (B2 fail-closed intact) |
| DMS open set | 85 | 84 |
| DMS-380 | Closed, assignee Semavin.M.M, created 2026-09-02 | — |
| WMB-30000 files | 5 × xlsx | 5 |
| WMB-29996 / WMB-30001 files | 7 each (6 xlsx + 1 eml), assignee **Utkin.S.A** | 6/5 |
| Zhdanov.A.Ni (DMS) | 8 (oracle 7 → live 8: +DMS-412 mid-run) | 7 |
| Garanin.R.V (DMS) | 8 | 8 |
| Semavin.M.M (all) | 313 (312 at matrix time → +1 mid-window) | 312 |
| Utkin.S.A (all) | 57 (CRPV/STS/WMB) | 57 |
| Kalachanov.V.V (STS) | 2695 | 2858 (source drift) |
| DMS current sprint | DMS-SPRNT-3, **54** tasks (complete=true) | 53 |
| Уткин resolve | 409 → 7 source matches | 7 |
| DMS-380 history / time-in-status | **502** `get_unit_change_history` (proven source outage) | 502 |
| versions | live, "Q3-2026" absent | absent |
| text "аутентификация" (DMS) | 2 (DMS-267, DMS-380) | 2 |
| **Aging ground truth (raw TQL `unit.createdAt`)** | **81** open DMS tasks ≥7d (oldest DMS-1, 205d) | n/a (A196: 246s timeout) |

## Phase 3 — D1/D2 focused re-gate

### D1 task.aging — **RED (3/3)**

`Застоящиеся открытые задачи в DMS` ×3 → all **COMPLETED, count=0** (13.9s / 19.8s / 38.2s), skill `task.aging` loaded, bounded live `task-query?space=DMS` provenance. Ground truth = **81**. Root-cause chain (proven):
1. Raw TQL rows carry `unit.createdAt`/`unit.updatedAt` (camelCase) — verified via direct MCP-SWTR probe.
2. `swtr_query.py` (ff02bd6) does `_row_text(raw, "created_at")` — snake_case lookup in `unit`/`row`/`attrs` → always `""` → route rows carry **no** `created_at` (verified: 0/409).
3. Agent adapter `_map` (`task_api.py:381`): `_parse_datetime(data.get("created_at")) or datetime.now()` → `created_at = now` → `age_days = 0` for every row.
4. `build_task_aging` filters `is_open and age_days >= 7` → 0 rows → "их количество: 0" presented as complete.

Boundedness of the fix itself is proven (no tenant-wide scan, 14–38s), but the timestamp bridge is broken → false REAL_EMPTY. **Owner fix (minimal, source boundary):** in `swtr_query.py`, map SWTR camelCase unit fields — `created_at ← unit.createdAt`, `updated_at ← unit.updatedAt` (e.g. extend `_row_text` names or the projection loop); no agent-side change needed. Then re-gate: DMS aging ≥7d must equal the live-computed 81 (± live drift), and a source-timestamp-absent row must stay excluded, not become age 0.

### D1 task.similar — **CLOSED (3/3)**

`Найди похожие задачи на DMS-380` / `Похожие на DMS-380` ×3 → COMPLETED (25.7/38.6/46.7s), skill `task.similar`, **identical deterministic top-5** (DMS-375, DMS-113, DMS-400, DMS-329, DMS-339) + source task evidence; method `token_jaccard_v1` visible in data; corpus restricted to DMS via live `task-query?space=DMS`; source task resolved through live bounded route; practical latency. A196's 234s tenant-wide timeout is gone.

### D2 attachments — **CLOSED**

- Exact task (WMB-30000) ×3 (matrix + S5): COMPLETED, **5/5** files (all xlsx) — exact.
- Bounded person-scoped (Utkin.S.A, WMB) ×3: COMPLETED (61.9/78.5/65.5s), **WMB-29996 + WMB-30001** with 6 Excel attachments each — exact vs source; route audit: `task-query?space=WMB&assignee=Utkin.S.A` + **5** `/files` calls only (candidates bounded to the person's WMB set).
- Broad space-only Excel/PDF/MSG ×3 each: **FAILED typed** `source_unavailable` in 56–80s (A196: 300s timeout) — `AS21SourceUnavailable` raised **before** fan-out (>250 candidates, no batch attachment surface). Route audit: exactly **1** `task-query?space=WMB` call, **zero** `/files` calls, **zero** local-store reads. Meets the spec's SOURCE_CONDITIONAL bar (fast bounded fail-closed, no N+1, no partial-scan-as-complete).
- Classification: exact + person-scoped = **GREEN_SOURCE_SUPPORTED**; broad space-only = **SOURCE_CONDITIONAL** (until AS21 exposes a certified batch attachment-search surface).

## Phase 3 (full matrix) — 27-skill API results

| # | Skill | Query | Status | Skill match | Parity (fresh oracle) | Class |
|---|---|---|---|---|---|---|
| 1 | task.lookup | Открой задачу DMS-380 | COMPLETED | ✓ | source-accurate detail | GREEN |
| 2 | task.summary | Расскажи о задаче DMS-380 | COMPLETED | ✗ → task.lookup | facts exact | GREEN (F2) |
| 3 | task.quality | Насколько полностью описана… | COMPLETED | ✓ | 85/100; **UIContract task_analysis live** | GREEN |
| 4 | task.acceptance | Критерии приёмки… | COMPLETED | ✓ | 0/100 (no AC in source) | GREEN |
| 5 | task.blockers | Какие блокеры… | COMPLETED | ✓ | 0 (Closed task) | GREEN |
| 6 | task.dependencies | Зависимости… | COMPLETED | ✓ | 0 | GREEN |
| 7 | task.missing_requirements | Каких требований не хватает… | COMPLETED | ✓ | acceptance missing | GREEN |
| 8 | task.history | История изменений… | FAILED | ✓ | `source_unavailable` (502 proven) | SOURCE_CONDITIONAL |
| 9 | task.time_in_status | Сколько времени в статусах… | FAILED | ✓ | `source_unavailable` (502 proven) | SOURCE_CONDITIONAL |
| 10 | **task.aging** | Застоявшиеся открытые в DMS | COMPLETED | ✓ | **0 vs GT 81** | **RED** |
| 11 | task.similar | Найди похожие на DMS-380 | COMPLETED | ✓ | deterministic top-5, method visible | GREEN |
| 12 | task.search_text | …про аутентификацию в DMS | COMPLETED | ✓ | **2/2 EXACT** | GREEN |
| 13 | task.search_attachments | Вложения WMB-30000 | COMPLETED | ✓ | **5/5 EXACT** | GREEN |
| 14 | task.search_excel | Excel-вложения в WMB | FAILED | ✓ | typed fail-closed 63.7s, N+1=0 | SOURCE_CONDITIONAL |
| 15 | task.search_pdf | PDF-вложения в WMB | FAILED | ✓ | typed fail-closed 56.2s | SOURCE_CONDITIONAL |
| 16 | task.search_msg | MSG-вложения в WMB | FAILED | ✓ | typed fail-closed 58.2s | SOURCE_CONDITIONAL |
| 17 | task.search_assignee | Задачи Родиона Гаранина в DMS | COMPLETED | ✓ | **8/8 EXACT** (re-scored) | GREEN |
| 18 | task.search_status | Открытые задачи в DMS | COMPLETED | ✓ | **85/85 EXACT** (190 statusless NOT open — B2 retained) | GREEN |
| 19 | task.search_sprint | Задачи в спринте DMS-SPRNT-3 | COMPLETED | ✓ | **54/54 EXACT** (sprint-id in evidence = cosmetic) | GREEN |
| 20 | task.search_release | Задачи релиза Q3-2026 в DMS | NEEDS_CLARIFICATION | ✓ | typed: release not confirmed by source | SOURCE_CONDITIONAL |
| 21 | tasks.search (multi) | Открытые задачи Жданова в текущем спринте DMS | COMPLETED | ✓ | **1/1 EXACT** (DMS-371; open-filter semantics correct) | GREEN |
| 22 | tasks.lookup_then_assignee | Покажи DMS-380 и затем задачи его исполнителя | COMPLETED | ✓ | **312/312 point-in-time EXACT** (oracle +1 later = drift) | GREEN |
| 23 | sprint.current | Текущий спринт DMS | COMPLETED | ✓ | DMS-SPRNT-3 | GREEN |
| 24 | sprints.discover | Сентябрьский спринт DMS | COMPLETED | ✓ | DMS-SPRNT-3 | GREEN |
| 25 | sprints.list | Активные спринты в DMS | COMPLETED | ✓ | both DMS sprints | GREEN |
| 26 | sprint.health | Здоровье спринта DMS-SPRNT-3 | COMPLETED | ✓ | 56 evidence, live sprint tasks | GREEN |
| 27 | release.health | Здоровье релиза Q3-2026 в DMS | NEEDS_CLARIFICATION | ✓ | typed: release absent | SOURCE_CONDITIONAL |

**Tally: 19 GREEN / 5 SOURCE_CONDITIONAL / 1 RED.**

### Route provenance & boundedness audit (task-api access log)

- All factual collections via live routes: `task-query` (17), `assignee-tasks` (19), `sprints/<id>/tasks?complete=true`, `current-sprint`, `assignees/resolve`, per-task `files` (22 total for exact/person-scoped attachment cases only).
- **Zero unbounded N+1**: broad WMB attachment runs show exactly 1 task-query + 0 `/files`.
- **Local store:** 2 `GET /api/v1/tasks?limit=10000` hits during the matrix window (09:49:35, 09:53:53) — **non-reproducible** across 9 targeted re-probes (SPRINT, MULTI, MSG, L2A, CURR, DISC, LIST, SHEALTH — all LOCAL=0); the local store is **empty (0 items)** so zero facts could have leaked. Hygiene note (F4) for the owner to add request logging to the local route.
- `semantic_prepass_used=false` on every row; `prepass=0`.

## Phase 4 — retained identity/clarification adversarial

| Case | Result |
|---|---|
| A inflected full name «Задачи Александра Жданова в DMS» | COMPLETED **8/8 live-exact** (oracle 7 → live 8, +DMS-412 drift proven) |
| B non-team canonical «Задачи Utkin.S.A» | COMPLETED **57/57 EXACT** |
| C ambiguous «Задачи Уткина» | NEEDS_CLARIFICATION, options **== 7 source matches** (409 detail) |
| D continuation (Utkin.S.A option) | turn1 NEEDS_CLARIFICATION (non-null cid) → turn2 **COMPLETED 57/57** |
| E invented «Задачи Пупкина» | NEEDS_CLARIFICATION (safe typed, no source error text) |
| F «задачи Гаранина в сентябрьском спринте» | **Flaky — F3** (below) |

**F3 (planner/completion reliability, pre-existing class, non-blocking for A196-defect scope but must be tracked):** 8 runs of the F query: 3× typed space-NEEDS_CLARIFICATION (one with a `«?»` placeholder artifact in the question), 1× FAILED, **2× COMPLETED via `completion=planner_ready` after only `member.resolve` — the loaded primary capability (`task.search`) was never invoked**, with an LLM-drafted "no data in current observations" answer. In A196 this query was consistently a typed clarification → clean turn-2. The owner's A197 diff does not touch planner/completion, so this is not a new A197 defect, but a READY accepted without satisfying the loaded skill's completion contract is a completion-gate hole worth a dedicated owner follow-up (A188 gate had 0 planner_ready on its 40 representative runs).

## Phase 5 — stability (all live-exact & cross-run consistent)

| Tag | Query | Result |
|---|---|---|
| S1 ×5 | Покажи DMS-380 и затем задачи его исполнителя | 5/5 COMPLETED, n=314 each (313 Semavin live + 1 known cosmetic DMS-380 evidence dup) |
| S2 ×5 | Задачи Александра Жданова в DMS | 5/5 COMPLETED, **8/8** each (live-exact) |
| S3 ×5 | Открытые задачи Жданова в текущем спринте DMS | 5/5 COMPLETED, consistent (1 task DMS-371 + 3 observation ids) |
| S4 ×3 | Текущий спринт DMS | 3/3 COMPLETED (DMS-SPRNT-3) |
| S5 ×3 | Какие вложения есть у задачи WMB-30000 | 3/3 COMPLETED, 5 files each |

`stale_source_error_text` (`AS21 вернул некорректные данные` / `invalid data`) = **false on every response** in all phases.

## Phase 6 — Browser C (12/12, 4.6 min, Playwright)

- C1 task_detail, C2 task_table, C3 attachment_table (widget `attachment_table`), C5 dependencies, C7 similar (`similar_task_list` / `similar_task_collection`), C8 sprint_health, C9 sprint_list — all COMPLETED with correct UIContract widgets.
- **C4 task.quality: panel renders `widget: task_analysis · kind: analysis`** — A196's raw-JSON gap is closed (088d6f7 verified in UI).
- C6 history: FAILED → panel state `SOURCE_UNAVAILABLE` (typed, no stale text).
- C10 release.health: NEEDS_CLARIFICATION (release absent).
- C11 continuation: NEEDS_CLARIFICATION → option click (session_id + clarification_id preserved) → **COMPLETED 57/57**.
- C12 safe not-found: NEEDS_CLARIFICATION.
- `has_stale_source_error_text=false` on all 12; pre-query label stays "Legacy Harness" until first V4 result (pre-existing A195B F2: unscoped `/health` scan hang).

## Phase 7 — plugin/extensibility gate

`tests/test_agent_core_v4_plugin_registry.py`: **11/11 passed** (0.43s) — dummy-55 add-without-core-change, fail-closed duplicate/missing/binding/untrusted-package contracts all intact.

---

## Findings summary

| ID | Severity | Class | Description |
|---|---|---|---|
| **D1-aging** | **RED (blocking)** | Correctness, source boundary | ff02bd6 timestamp bridge uses snake_case `created_at`/`updated_at`; SWTR raw rows expose camelCase `unit.createdAt`/`updatedAt` → 0/409 rows carry timestamps → adapter `datetime.now()` fallback → `age_days=0` → aging reports **0** (COMPLETED) vs live GT **81**. Fix: map camelCase unit fields in `swtr_query.py`; re-gate 3× against live-computed GT. |
| F1 | non-blocking | Test logic | Owner-refreshed `test_task_wave_capabilities_bind_only_through_registry_contract` constructs a single-plugin registry that references cross-plugin core capabilities → fail-closed in constructor. Production discovery unaffected. |
| F2 | non-blocking | Planner routing (Qwen3.8, A179 lineage) | «Расскажи о задаче DMS-380» → `task.lookup` **6/6** (A196: `task.summary` with 1 one-off). Answers remain source-accurate and complete. |
| F3 | non-blocking (track) | Planner/completion reliability | P4F: 2/8 runs end `COMPLETED` via `planner_ready` after only `member.resolve` (primary capability never invoked); 1/8 FAILED; 1 typed question contains `«?»` artifact. A196 behaved consistently as typed clarification. |
| F4 | hygiene | Observability | 2 non-reproducible local `GET /api/v1/tasks` reads (store empty, zero facts); "Legacy Harness" pre-query label + agent `/health` unscoped-scan hang (A195B F2) unchanged. |
| F5 | cosmetic | Presentation | L2A evidence duplicates DMS-380 (known since A188); SPRINT evidence includes sprint-id key. |

**Source drift observed live during the window:** Zhdanov 7→8 (+DMS-412), Semavin 312→313, DMS rows →409, sprint DMS-SPRNT-3 →54 tasks. Agent held live truth in every drift case (oracle refreshed accordingly).

## Recommendation

**STOP.** Fix D1-aging at the source boundary (camelCase timestamp bridge in `task-api/app/routers/swtr_query.py`) + fix F1 test, then one consolidated A198 re-gate: aging 3× vs live GT (expect 81±drift), full 27-skill matrix, P4F 5× stability, Browser C spot-check (C4/C6/C11). F2/F3 to be scheduled as a planner-reliability follow-up (constrained output / deterministic READY fallback lineage) — neither blocks Wave S entry by themselves, but F3's premature `planner_ready` completion should be closed before Wave S scales the catalog.

## Services left running (current-HEAD)

| Service | URL | PID | Health |
|---|---|---|---|
| UI (vite) | http://127.0.0.1:5175 | 22389 | 200 |
| PO Agent | http://127.0.0.1:8212 | 44579 | `/live` 200 (pinned `PO_AGENT_EXPECTED_HEAD=303f5a9a0982b3817a5953bd601c2cba161f3d81`) |
| Task API | http://127.0.0.1:8241 | 44407 | `/health` 200 |
| MCP-SWTR (SSE) | http://127.0.0.1:3000/sse | 45891 | SSE active (task-api session live; all live data served) |

**START_HEAD:** `303f5a9a0982b3817a5953bd601c2cba161f3d81`
