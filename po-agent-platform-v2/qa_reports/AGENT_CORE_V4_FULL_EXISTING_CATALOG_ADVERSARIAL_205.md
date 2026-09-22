# A205 (full re-run) — Agent Core V4 Full Existing-Catalog + Adversarial Zero-RED Gate

**Verdict:** `AGENT_CORE_V4_EXISTING_CATALOG_ADVERSARIAL_GREEN`
**Recommendation:** `FREEZE_NEW_CHECKPOINT_AND_AWAIT_EXPLICIT_WAVE_S_APPROVAL`

| Field | Value |
|---|---|
| Branch | `feat/core8-real-query-hardening-v2` |
| START_HEAD | `1fd519105ba6612f535ad98a55cb1302f387ca43` |
| Preflight (basis) | `AGENT_CORE_V4_A205_PREFLIGHT_GREEN` @ `a4b8a25`, report `61abf6f` |
| Production diff preflight→START_HEAD | empty (`git diff a4b8a25..1fd5191 -- po-agent-platform-v2/src task-api/app mcp-swtr` = ∅; only `GIGACODE_NEXT_ACTION.md` changed) |
| Agent runtime | 8212 (PID 84446, code at `a4b8a25` ≡ `1fd5191` production-wise) |
| Task API | 8241 (PID 30041, system python3, log `/tmp/qa205_taskapi.log`) |
| MCP-SWTR | 3000 (PID 29268) |
| UI | 5175 (PID 55236, bound `[::1]:5175`) |
| Oracle | fresh REAL AS21, `qa_205r_oracle.json`, built 2026-09-22 17:30 UTC immediately before batches |

---

## Phase 0 — start

- `git pull --ff-only`: `61abf6f..1fd5191` (spec only).
- Preflight report present and GREEN; no production changes after preflight START_HEAD.
- Tracked worktree: only known QA-run artifacts modified (`GIGACODE.md`, `po-agent-platform-v2/.po_agent/learned_policies.json`, `po-agent-platform-v2/frontend/vite.config.ts` — QA proxy edit). No production files touched by QA.

## Phase 1 — automated gates (all GREEN)

| Suite | Result |
|---|---|
| `tests/test_agent_core_v4*.py` | 99 passed |
| `tests/test_v4*.py` | 32 passed |
| `task-api: test_swtr_read_sprint_collection.py + test_swtr_task_query_release.py` | 18 passed |

Zero unexplained failures.

## Phase 2 — fresh oracle (REAL AS21, built before batches)

| Fact | Value |
|---|---|
| DMS-380 | 200, «…аутентификация в режиме mTLS, TLS, SSL», assignee `semavin.m.m` |
| DMS-380 history | **502** (typed, sustained) |
| DMS-399 | 200 exists; history **502** |
| WMB-30000 files | 5 (all xlsx) |
| Zhdanov DMS / Garanin DMS / Garanin OLP | 7 / 11 / 7 tasks |
| Semavin (all) / Utkin (all) / Kalachanov WMB | 321 / 57 / 5 |
| Уткин resolve | 409 (ambiguous) |
| DMS current sprint | DMS-SPRNT-3 — 65 tasks, 50 open, 15 terminal, 4 unassigned (DMS-104/166/389/421) |
| OLP current sprint | OLP-SPRNT-8 («Спринт 2026.09 - 3», IN_PROGRESS) — 64 tasks, 63 open, 3 unassigned (OLP-3129/3143/3155) |
| DMS sprints | SPRNT-3 (IN_PROGRESS, 13–27.09.2026), SPRNT-1/2 (FINISH) — September sprint unique |
| OLP sprints | 8 total; September candidates: SPRNT-6 (FINISH), SPRNT-7 (FINISH), SPRNT-8 (IN_PROGRESS) |
| DMS rows (task-query) | 423 total, 88 open, 77 open ≥7d aging (oldest DMS-1, 210d) |
| WMB total | 2364 |
| versions | `/versions` → 400 «space is required»; `/versions?space=DMS` → **502** `search_versions` ToolError (sustained, 2 probes 15s apart) → **no real release id obtainable** |
| phrase «аутентификация» DMS | 2: DMS-267, DMS-380 |
| Multihop oracle | Garanin OLP ∩ OLP-SPRNT-8 = 5 tasks, all 5 active: OLP-3233/3244/3250/3281/3291 |

No stale A204/A205 counts reused.

## Phase 3 — 27/27 V4 skills (0 RED)

| # | Label | Expected skill | Status | Result / parity | Class |
|---|---|---|---|---|---|
| 1 | LKUP | task.lookup | COMPLETED | DMS-380 Закрыт/Не сделано, Semavin — source-accurate | GREEN |
| 2 | SUMM | task.summary | COMPLETED | routed via task.lookup (known A197-F2), source-accurate | GREEN |
| 3 | QUAL | task.quality | COMPLETED | 85/100 completeness | GREEN |
| 4 | ACCE | task.acceptance | COMPLETED | 0/100, no explicit acceptance — source-accurate | GREEN |
| 5 | BLOC | task.blockers | COMPLETED | no blockers, not blocked | GREEN |
| 6 | DEPS | task.dependencies | COMPLETED | 0 dependencies | GREEN |
| 7 | MISS | task.missing_requirements | COMPLETED | missing acceptance expectations | GREEN |
| 8 | HIST | task.history | FAILED | typed «Источник AS21 временно недоступен…»; route 502 (oracle-proven) | SOURCE_CONDITIONAL |
| 9 | TIS | task.time_in_status | FAILED | typed source-unavailable; history route 502 | SOURCE_CONDITIONAL |
| 10 | AGING | task.aging | COMPLETED | **77/77 exact** (open ≥7d) | GREEN |
| 11 | SIMIL | task.similar | COMPLETED | deterministic top-5 (DMS-375, DMS-113, …) | GREEN |
| 12 | TEXT | task.search_text | COMPLETED | **2/2 exact** (DMS-267, DMS-380) | GREEN |
| 13 | ATT | task.search_attachments | COMPLETED | WMB-30000: 5 Excel files = oracle (8.5s) | GREEN |
| 14 | EXCEL | task.search_excel | FAILED | typed bounded fail-closed before broad WMB fan-out (22–26s) | SOURCE_CONDITIONAL |
| 15 | PDF | task.search_pdf | FAILED | typed bounded fail-closed (same class) | SOURCE_CONDITIONAL |
| 16 | MSG | task.search_msg | FAILED | typed bounded fail-closed (same class) | SOURCE_CONDITIONAL |
| 17 | ASGN | task.search_assignee | COMPLETED | Garanin DMS **11/11 exact** | GREEN |
| 18 | STAT | task.search_status | COMPLETED | DMS open **88/88 exact** | GREEN |
| 19 | SPRINT | task.search_sprint | COMPLETED | DMS-SPRNT-3 **65/65 exact** | GREEN |
| 20 | REL | task.search_release | NEEDS_CLARIFICATION | «Не удалось подтвердить релиз «Q3-2026» по данным REAL AS21» (release unconfirmed; versions 502) | SOURCE_CONDITIONAL (grounding correct) |
| 21 | MULTI | tasks.search | COMPLETED | Zhdanov DMS ∩ DMS-SPRNT-3 open = **1/1 exact** (DMS-371) | GREEN |
| 22 | L2A | tasks.lookup_then_assignee | COMPLETED | Semavin **321/321 exact** (17.9s) | GREEN |
| 23 | CURR | sprint.current | COMPLETED | DMS-SPRNT-3 = oracle | GREEN |
| 24 | DISC | sprints.discover | COMPLETED | DMS-SPRNT-3, 13–27.09.2026, IN_PROGRESS | GREEN |
| 25 | LIST | sprints.list | COMPLETED | exactly 1 active DMS sprint = oracle (SPRNT-3 IN_PROGRESS only) | GREEN |
| 26 | SHEALTH | sprint.health | COMPLETED | real metrics: 65 total / 15 done (23,1%) / 11 in work / 3 blocked — matches oracle terminal/in-progress counts | GREEN |
| 27 | RHEALTH | release.health | NEEDS_CLARIFICATION | release identity required; DMS ≠ release id | SOURCE_CONDITIONAL (grounding correct) |

**27/27 tested: 20 GREEN, 7 SOURCE_CONDITIONAL (all typed, source-outage or bounded-fan-out proven), 0 RED.**

## Phase 4 — adversarial pack (closed)

| Case | Runs | Result |
|---|---|---|
| A1 `здоровье сентябрьского спринта по DMS` | **10/10** COMPLETED runtime_contract | `sprints.discover` → **`sprint.health(sprint_id=DMS-SPRNT-3)` actually executed** every run; real metrics 65/15/11/3 in every answer. **D-A204-1 (identity-only completion) CLOSED.** |
| A2 `Покажи список задач сентябрьского спринта DMS и их статусы` | **10/10** COMPLETED | **65/65 exact every run**; 14.8–35.8s |
| A3 same-session pair (t1 «Какой спринт в DMS идёт в сентябре?» → t2 «…в этом спринте…») | **10/10 pairs** | t2 `task.search(sprint_id=DMS-SPRNT-3, space=DMS)` **65/65 exact every run** — source-validated referent reused. **D-A204-3 CLOSED.** |
| A4 multihop `…у Гаранина в сентябрьском спринте по OLAP` | **3/3** COMPLETED | 3-turn chain: typed space clarification [CRPV,DMS,OLP,STS,WMB] → OLP → typed sprint clarification [OLP-SPRNT-8/6/7] → OLP-SPRNT-8 → terminal `task.search(assignee=Garanin.R.V, sprint_id=OLP-SPRNT-8, [space=OLP], status=not_completed)` = **5/5 exact every run**. Person + OLP + sprint + active all preserved, no dropped constraint. |
| A5a unassigned OLP | **3/3** COMPLETED | **3/3 exact** (OLP-3129/3143/3155), `unassigned` constraint honored |
| A5b unassigned DMS | **3/3** COMPLETED | **4/4 exact** (DMS-104/166/389/421) |
| A6 workload `кто больше всех загружен…` | **3/3** COMPLETED | **Honest**: «…нет информации о распределении задач по исполнителям… определить не представляется возможным». No fabricated ranking, no identity-only false success. (No team-workload capability — stated honestly, spec-compliant.) |
| A7a `история статусов DMS-380` | 2/2 FAILED | typed «Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат» (502 proven) |
| A7b `сколько времени DMS-399 провела в статусах` | 2/2 FAILED | typed source-unavailable (502 proven) |
| A7c `Ты умеешь определять длительность задач?` | 2/2 | honest capability statement (`task.time_in_status` exists, history-based) + typed clarification for a concrete task |
| A8a `здоровье релиза по DMS` | 2/2 NEEDS_CLARIFICATION | «DMS — название продуктового пространства, а не идентификатор релиза» — release grounding correct |
| A8b `задачи в релизе по DMS` | 2/2 NEEDS_CLARIFICATION | release id required — DMS never treated as release id |

Explicit real-release-id health/tasks path: **not testable** — `search_versions` 502 sustained (source outage, A204 lineage); classified SOURCE_CONDITIONAL.

### LLM-endpoint outage window (classified, not a code defect)

During the sweep (~17:55–18:05 UTC) the Qwen3.8 endpoint dropped: **11 runs** (A3 pairs #6–10 both turns, A4 ×3, A5a ×3) failed as `planner failed robust bounded repair: [ConnectError ×4]` / one `ReadTimeout` at ~0.0s — typed FAILED, fail-closed, zero fabrication. After the endpoint recovered (probe COMPLETED 18.1s), all 11 were re-run clean (batch B2): A3 5/5 pairs 65/65 exact, A4 3/3 5/5 exact, A5a 3/3 3/3 exact. Same degradation class as A200/A204; retained and classified per spec.

## Phase 5 — performance / provenance (N+1 audit)

- **A2 sprint task list: per-run raw `GET /swtr-read/tasks/{code}` count = 0 in all 10 runs** (task-api access-log windows). Source-proven complete rows (`sprint_membership_proven=true`) avoid per-task raw membership validation — A204 N+1 finding (65 GETs, 92–101s) **closed**: latency now 14.8–35.8s.
- Attachment row (single task, WMB-30000): 8.5s, 5 files.
- Sweep latencies: 3.2–57s per run; L2A (321 tasks) 17.9s; no 300s timeouts in final batches.

## Phase 6 — Browser C (7/7)

| Case | Result |
|---|---|
| C1 sprint health | COMPLETED runtime_contract, 66 evidence, real metrics in UI |
| C2 same-session «этом спринте» | t1 COMPLETED (DMS-SPRNT-3) → t2 same session COMPLETED **65 exact task keys** in UI; `clarification_id` absent (pure same-session reuse) |
| C3 multihop OLP | t1 typed space options → UI click **OLP** (request carries `session_id`+`clarification_id`+`clarification_option`) → t2 typed sprint clarification → t3 (reproduced with exact UI payload shape) COMPLETED, answer lists exactly the 5 oracle tasks |
| C4 unassigned OLP | COMPLETED, 3 exact keys (OLP-3143/3155/3129) |
| C5 workload | COMPLETED, honest «распределение по исполнителям отсутствует», no invented ranking |
| C6 history DMS-380 | FAILED typed source-unavailable (502) |
| C7 release health | NEEDS_CLARIFICATION — «DMS — пространство, а не release id» |

- No stale «AS21 вернул некорректные данные» text in any case; no generic V4 error text except the typed source-unavailable message.
- **Leak audit:** the C2 `leak=true` flag is a **false positive** — the substring `session_context` occurs only inside the planner's `rationale` text (LLM self-referencing its prompt wording: «refers to session_context sprint DMS-SPRNT-3»). No `session_context` data key, no continuation keys in any API response body (exact key-path + substring probes on fresh runs: 0). Internal-only invariant retained.

## Phase 7 — source / local audit (whole run)

- Local `GET /api/v1/tasks` factual reads: **0** (task-api access log, entire run).
- Live `swtr-read` calls: **258+** (sprints 94, spaces 58, tasks 52 — single-task/oracle lookups only, task-query 22, assignees 13, health 10, assignee-tasks 6, versions 3).
- No fake/frozen/local oracle; no broad client-side release scan; no false success on outage (all outages → typed fail-closed or typed clarification).
- `semantic_prepass_used=false` in all captured runs; 0 internal-key leaks in answers/options/executed/ui fields across 89+16 runs.
- Flakes retained and classified: LLM ConnectError/ReadTimeout window (11 runs, re-run clean), versions 502 (source outage), turn-1 clarification shape variance absent this run.

## Phase 8 — plugin invariant

`tests/test_agent_core_v4_plugin_registry.py`: **13/13 passed** (dummy-55 extensibility, duplicate/missing/unknown fail-closed, untrusted-package rejection, both session_context interface-parity tests). Zero Agent Core/planner/runtime business edits in owner diff scope (verified: `agent_core_v4_pluginized.py` +9/−1 + parity tests + docs only).

---

## Findings (non-blocking)

1. **F1 — LLM endpoint outage window** (Qwen3.8): 11 runs typed-FAILED fail-closed during a ~10-min ConnectError/ReadTimeout window; all re-run clean. Owner item: endpoint reliability (constrained/structured output or retry/backoff), A179/A200 lineage.
2. **F2 — planner `rationale` text mentions «session_context»** (substring in LLM-generated rationale). Cosmetic; no state/data leak.
3. **F3 — `search_versions` sustained 502** (MCP tool failure; `/versions` without space → 400 «space is required», with space → 502). Release-id paths SOURCE_CONDITIONAL; explicit release controls untestable until source recovers.
4. **F4 — A4#2 terminal `task.search` omitted optional `space` arg** (sprint_id pins the space; result 5/5 exact). Planner non-determinism class, legal per schema.
5. **F5 — workload question answered via sprint collection + honest refusal** (no team-workload capability exists). Spec-compliant honesty; capability gap to decide in Wave S.

## Services left running

| Service | Port | PID | State |
|---|---|---|---|
| UI (vite) | 5175 (`[::1]`) | 55236 | 200 |
| Agent (a4b8a25 ≡ 1fd5191 prod code) | 8212 | 84446 | /live 200 |
| Task API (system python3) | 8241 | 30041 | swtr-read connected, 48 tools |
| MCP-SWTR (own .venv) | 3000 | 29268 | serving |

QA artifacts (untracked, repo root): `qa_205r_oracle.py/.json`, `qa_205r_sweep.py`, `qa_205r_rerun.py`, `qa_205r_p6_browser.json`; logs in `/tmp/qa205r_*`; browser spec: `po-agent-platform-v2/frontend/e2e/qa205r-browser-c.spec.ts`.

**Verdict:** `AGENT_CORE_V4_EXISTING_CATALOG_ADVERSARIAL_GREEN` — 27/27 tested, 0 RED; adversarial pack closed (sprint health real-metrics 10/10, period list 10/10 exact, same-session 10/10 exact, multihop 3/3 exact with all constraints preserved, unassigned 6/6 exact, workload honest, history/tis typed-source-unavailable, release grounding correct); N+1=0; local factual reads=0; dummy-55 GREEN.
**Next:** `FREEZE_NEW_CHECKPOINT_AND_AWAIT_EXPLICIT_WAVE_S_APPROVAL`.
