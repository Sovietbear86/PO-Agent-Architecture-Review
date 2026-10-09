# A229F3 — Complex task composition + clarification regression (QA)

**Verdict: `AGENT_CORE_V4_COMPLEX_TASK_CLARIFICATION_RED_A229F3`**
**Classification: `RED_P4A_PLANNER_SILENT_PERIOD_DROP`**

- **START_HEAD / TESTED_HEAD:** `65601f6fc83e69b27d11b7c2adc2d3a20c27cd4a` (branch `feat/core8-real-query-hardening-v2`, clean tracked worktree; local `GIGACODE.md` memory addendum uncommitted, untracked QA scripts only otherwise)
- **Certified baseline:** `checkpoint/v4-task-semantics-hierarchy-green-a229s1r4@afb6fa1`
- **Services:** agent 8004 (fresh on `65601f6`, `TASK_API_BASE_URL=8241` override, `PO_AGENT_AGENT_CORE_V4_ENABLED=true`), task-api 8241 (unchanged, SSE→MCP, 48 tools), MCP-SWTR 3000 (SSE), vite `[::1]:5175`
- **Date of testing:** 2026-10-09 (MSK)

---

## P0 — integrity / tests — GREEN

1. Production diff vs `afb6fa1` = **3 files only** (expected boundary):
   - `src/po_agent/api/v1/__init__.py` (+72) — `_promote_planner_failure_to_clarification` seam, wired after `_decorate_v4_response` in `_run_query`
   - `src/po_agent/harness/v4_plugins/_task_live_handlers.py` (+58) — `_parse_human_created_period` extended: bare `за N дней`/`за день`/`сегодня`, single start date `с/от/начиная с DATE` (incl. harmless `за с DATE`), open tail `по/до сегодня(шний день)/текущий день`
   - `src/po_agent/harness/v4_plugins/task_catalog.py` (+18) — procedure-text edits on existing `task.search_created` / `task.type_analysis` (bare periods default to creation time; type+person+space+status+period compose in one terminal call)
2. **Agent Core 6/6 byte-identical** to `afb6fa1` (empty `git diff` on `agent_core_v4.py`, `agent_core_v4_robust.py`, `agent_core_v4_reliable.py`, `agent_core_v4_completion.py`, `v4_plugin_registry.py`, `llm/real.py`). No planner/runtime/orchestration file touched.
3. Focused: `test_agent_core_v4_task_created_period.py` + `test_agent_core_v4_task_semantics_hierarchy.py` + `test_agent_core_v4_task_catalog.py` + `test_v4_browser_api_contract.py` = **36/36 pass** (incl. owner's 4 new parser tests + 2 new API-seam tests: planner-failure→resumable clarification, provider-429→stays FAILED).
4. Full V4 blast `test_agent_core_v4*.py test_v4*.py` = **255/255 pass**. Task API SWTR (9 suites) = **57/57 pass**. Frontend `npm run build` (tsc+vite) = **exit 0**. **0 failed.**

## P1 — parser/source truth — GREEN

Unit-level `_parse_human_created_period` (fixed `now=2026-10-09T12:30+03:00`), all exact:

| Case | Input | Window (MSK) | kind |
|---|---|---|---|
| A | `за 1 день` | 09.10 00:00 → now | `last_1_calendar_days` |
| B | `за последние 2 дня` | 08.10 00:00 → now | `last_2_calendar_days` |
| C | `с 30.09.2026` | 30.09 00:00 → now | `explicit_start_to_now` |
| D | `с 30.09.2026 по сегодняшний день` | 30.09 00:00 → now | `explicit_start_to_now` |
| E | `за с 30.09.2026` | 30.09 00:00 → now | `explicit_start_to_now` |
| F | `с 29.09.2026 по 01.10.2026` | 29.09 00:00 → 01.10 23:59:59.999999 | `explicit_inclusive_dates` |

Negatives typed-raise: `за период`, `когда-то`, `с 99.99.9999`, `с 01.01.2030` (future).

Independent REAL AS21 oracles (MCP-direct `find_units_by_filter`, `calculatedAttributes:[]`, `createdAt` UTC authoritative, person+space TQL pushdown, **no local store, no tenant scan**; 0 missing `created_at` in all 3 corpora):

| Case | Corpus | In-window | Oracle result |
|---|---|---|---|
| c1 Kalachanov+STS, today | 2831 | 42 | 42 keys |
| c2 Kalachanov+WMB, open, last 2 days | 6 | 0 | **0 REAL_EMPTY** |
| c3 Semavin+DMS, open, defect, ≥30.09 | 174 | 14 (4 open: DMS-486/455/453/458, all type `task`) | **0 REAL_EMPTY** — zero defect-suit rows created ≥30.09 |

**Discriminant proof (c3):** Semavin DMS has exactly 5 defect rows all-time (DMS-431 open QA/progress created 25.09; DMS-390/380/353/338 closed, ≤04.09). Any dropped-constraint bug (period → ≥1; type → 4; status → 14) would change the count — the 0 answers are discriminating, not vacuous.

## P2 — generic terminal capability composition (direct, planner-free) — GREEN

Production bundle built in-process (same wiring as API: `EvidenceValidatedProductionTaskApiAS21Adapter`→8241, `PluginizedRobustReliableAgentCoreV4Runtime`); governed handlers driven directly with terminal args. `member.resolve` source-backed: Калачанов→`Kalachanov.V.V`, Семавин→`Semavin.M.M`.

| Case | Terminal | Args (one call, all constraints) | Result | Oracle parity |
|---|---|---|---|---|
| 1 | `task.search_created` | `{reference:Калачанов, space:STS, created_period:«за 1 день»}` | 42 keys | **42/42 EXACT** |
| 2 | `task.search_created` | `{reference:Калачанов, space:WMB, status:not_completed, created_period:«за последние 2 дня»}` | 0 | **0 = 0 REAL_EMPTY** |
| 3 | `task.type_analysis` | `{reference:Семавин, space:DMS, status:not_completed, task_type:дефект, created_period:«с 30.09.2026 по сегодняшний день»}` | 0, `type_breakdown={task:4}` | **0 = 0 REAL_EMPTY**; breakdown = exact open-in-window set (4 Задача, 0 дефект) |

Drift: after-corpora fetched post-run are **identical** (2831/6/174) — zero source drift in the test window; parity is exact, not drift-bounded. No model-side intersection: Case 3 result is the full 5-constraint intersection of ONE terminal call.

## P3 — live complex-query matrix — GREEN (all 4 primary + 4 controls)

Fresh session per run; 80 s spacing; 0 provider-invalid reruns needed in the matrix itself.

| Case | Query (terminal requirement) | Runs | Terminal (every run) | Result vs oracle |
|---|---|---|---|---|
| P1 | `Задачи Калачанова в STS за 1 день` (search_created) | 3/3 COMPLETED | `task.search_created` | **42/42 EXACT** every run; raw period `«за 1 день»` preserved |
| P2 | `Открытые задачи Калачанова в WMB за последние 2 дня` (search_created) | 3/3 COMPLETED | `task.search_created` + `status:not_completed` | **0 = 0 REAL_EMPTY** |
| P3 | `Открытые задачи Семавина с типом дефект в DMS с 30.09.2026` (type_analysis) | 3/3 COMPLETED | `task.type_analysis`, all 5 constraints in args | **0 = 0 REAL_EMPTY** |
| P4 | `... за период с 30.09.2026 по сегодняшний день` (type_analysis) | 3/3 COMPLETED | `task.type_analysis`, raw period preserved | **0 = 0 REAL_EMPTY** |
| CA | type query, explicit 2 dates `с 30.09.2026 по 05.10.2026` | 2/2 COMPLETED | `task.type_analysis`, `explicit_inclusive_dates` | 0 = 0 |
| CB | type query, `за последние 2 дня` | 2/2 COMPLETED | `task.type_analysis`, `last_2_calendar_days` | 0 = 0 |
| CC | type query **without status** | 2/2 COMPLETED | `task.type_analysis`, **no status arg** (correct) | 0 = 0 |
| CD | **without type** (must route to created-search, not type_analysis) | 2 valid (smoke + rerun) | **`task.search_created`** (not type_analysis) | **4/4 EXACT** [DMS-453, DMS-455, DMS-458, DMS-486] |

- Every COMPLETED run: `prepass=false`, `completion=runtime_contract`, `semantic_prepass_used=false`.
- Status wording variance is safe: planner passes `open` or `not_completed` — `_safe_status` maps both to the same `is_open` path (agent_core_v4.py:692).
- Cosmetic: CA r2 planner passed `«30.09.2026 по 05.10.2026»` (dropped leading `с`) — two explicit dates still parse identically; no semantic effect.
- Transient (documented, not product): CD run-2 client 300 s timeout + one 240 s FAILED re-probe under the day's slow/rate-limited LLM window; both fail-closed, **clean re-runs exact** (spec: not counted as measurements).

## P4 — clarification UX — **RED at A (first boundary)** / B GREEN / C GREEN

### P4-A — incomplete period — **RED**

Spec query (fresh browser conversation + API probes): `Открытые задачи Семавина с типом дефект в DMS за период` — contains **no resolvable period**; required result: typed `NEEDS_CLARIFICATION`.

Observed across 6 runs (1 browser + 5 API, fresh sessions):

| Run | Channel | Result |
|---|---|---|
| 1 | Browser (Playwright) | **COMPLETED** — silent period drop |
| 2 | API | NEEDS_CLARIFICATION (planner-native, `v4_ready_without_source_observation`): «Уточните, пожалуйста, какой именно период вы имеете в виду под «за период» — например, … диапазон дат (с 01.05.2025 по 31.05.2025) или относительный период (за последние 30…)» |
| 3 | API | NEEDS_CLARIFICATION (owner promotion seam, `v4_planner_needs_clarification`, bounded-repair failure) with recommended format |
| 4 | API | **COMPLETED** — `task.type_analysis {reference:Семавин, space:DMS, status:open, task_type:defect}` — **`created_period` absent** → count=1 (DMS-431, created 25.09) |
| 5 | API | **COMPLETED** — same, `created_period` absent → count=1 |

**Defect:** the planner non-deterministically SILENTLY DROPS the unresolvable period constraint and completes with an over-broad result (DMS-431 — a task that violates the user's requested (unspecified) period). 3/6 runs dropped the constraint. This is worse than a generic FAILED card: it is a confident, source-backed-but-constraint-violating answer. The two clarification paths (native planner question and the new owner promotion seam) both work when the planner fails to plan — the gap is the planner's third option: omitting the constraint entirely. The `task.type_analysis` completion contract (`data_keys=("count","type_breakdown")`) cannot detect the dropped constraint, so nothing gates it.

- **First failing boundary (P5 taxonomy):** **2. planner argument schema** — the planner's terminal arguments omit a user-requested constraint (`created_period` is optional in the schema, so the omission is not rejected); contributing gap at **5. completion/postcondition** — the completion contract is satisfied despite the user's period intent being unmet. Boundaries 1, 3, 4, 6, 7, 8 verified clean for this scenario (skill loaded, no repair reached on dropped runs, capability executes correctly for the args given, synthesis correct, no provider/source involvement).
- Pre-existing class (A200/A227 planner-reliability lineage); the owner delta did not touch Core/planner and the completion contract is unchanged. Not an A/B baseline re-run (stop rule).

### P4-B — deterministic option-buttons clarification — GREEN

Browser, fresh conversation, `задачи Гаранина в сентябрьском спринте`:
- Turn 1: `NEEDS_CLARIFICATION`, question «Не удалось подтвердить пространство «?»», **options [CRPV, DMS, OLP, STS, WMB]**, `clarification_id` present (1/1 attempt).
- Click **DMS** → turn-2 POST carries `clarification_id` + option `DMS` (UI auto-attach) → **COMPLETED**, terminal `task.search {assignee:Garanin.R.V, sprint_id:DMS-SPRNT-3, space:DMS}`, count=0 — **source-exact**: DMS-SPRNT-3 complete collection 51 tasks (`complete=true`, `membership_proven=true`), Garanin.R.V = 0.
- Note: the same query is LLM-non-deterministic between the typed option clarification and the promoted free-text clarification (both typed, both resumable); the option path rendered on first attempt.

### P4-C — provider/source error taxonomy — GREEN

Direct drive of `_promote_planner_failure_to_clarification` (injected harness, 11/11) + owner's live stub tests (passing in P0):
- period-syntax `ValueError` (`created_period` in error) → **NEEDS_CLARIFICATION** (question + concrete examples)
- `V4ContractError` planner markers (bounded repair / step budget / ungrounded literal / person reference) → **NEEDS_CLARIFICATION**
- 429/HTTPStatusError, ReadTimeout, ConnectError → **stays FAILED**
- `AS21SourceUnavailable` (membership / created_at provenance) → **stays FAILED** (source, not disguised as user ambiguity)
- internal `RuntimeError` / unknown-skill contract error → **stays FAILED**

No user clarification can hide a provider/source/internal defect. `clarification_id` minted by `_remember_clarification`; free-text answer accepted when `options` empty; turn-2 combines original query + question + answer (proven live in P4-B and by owner's stub test).

## P5 — first-failing-boundary diagnostics

Per-run capture from matrix + agent log:
- LLM/planner calls per query run: **3–8** (p50 ≈ 4–5); 94 total LLM calls over 21 query runs in the agent lifetime window.
- Source reads: 49 `swtr-read` GETs, **every `task-query`/`assignee-tasks`/`assignees/resolve` call scoped** (`space=` and/or `assignee=`/`reference=` present); 0 unscoped; 0 5xx.
- Bounded repair: not reached in any P3 matrix run (all direct); reached + promoted in P4-A run 3 (the working path).
- P4-A failure runs (4/5): no source anomaly, no provider markers, no repair — clean COMPLETED with `created_period` absent from terminal args. Boundary = **2 (planner argument schema/plan quality), contributing 5 (completion contract cannot detect dropped constraint)**.

## P6 — retained architecture — GREEN (static + audits)

- Core 6/6 byte-identical (P0); canonical 54 unchanged (0 new `SkillSpecV4`/`CapabilitySpecV4` in diff; registry 13 plugins / 72 skills = baseline); `task.type_analysis` remains plugin-owned (`task_catalog.py`).
- No phrase-specific deterministic router (diff grep clean); promotion seam keyed on **typed failure classes** (`exception_type` + typed error markers), not query text.
- No surname/space hardcodes in production diff (0 person names, 0 space tokens); date literals only in clarification-question UX copy / comments / spec prose.
- Audits (agent log, full live window): **0 local-store reads, 0 mutations to task-api, 0 tenant-wide/unscoped scans, 0 HTTP 5xx, 0 console/runtime errors.**
- REAL AS21 authoritative end-to-end (oracles MCP-direct; all parity proven).
- Retained live gates (hierarchy/latest-sprint/Overview/task-drawer control runs): **not executed** — stop rule at P4-A.

## Environmental (non-product, documented)

- LLM `api.ai.sbt` (Qwen3.8-27B) slow all day (≈19 s+/call) with transient 429/timeout windows after burst load: 1 browser-batch FAILED window (3 attempts, ~4 s fail-closed, 0 evidence) and 2 CD-probe failures — all clean on cooldown re-runs. Per spec, excluded from measurements.
- Source drift: zero in all P2 windows (before/after corpora identical).

## Owner fix proposal (smallest, plugin/catalog/API-seam — no Core)

1. **Catalog procedure text** (`task.type_analysis` + `task.search_created`): add explicit rule — "if the user's request contains a period expression that does not resolve to concrete dates/numbers (e.g. a dangling «за период»), do NOT complete without it: pass the raw wording as `created_period` (the parser will reject it → typed clarification) or ask a typed clarification; never omit a user-requested period constraint."
2. **Deterministic plugin guard** (robustness, optional): in the `type_analysis`/`search_created` handlers, if the user query expresses a period intent but the planner supplied no `created_period` (or an unparseable one), raise `V4NeedsClarification` with a typed reason instead of completing. Generic by typed failure class ("period requested, constraint missing"), not by entity phrase.
3. **Hardening (Core — only if 1+2 are judged insufficient):** completion-constraint coverage — a user-requested created-period must be covered by the terminal call's args before `runtime_contract` completion (A198 `covers_resolved_constraints` precedent). Requires explicit proof that plugin/seam fixes cannot close the gap.

Then full A229F3 re-gate (P4-A ≥3/3 typed clarification + continuation parity, P3 matrix regression, P6 retained-gate controls).

---

**Verdict: `AGENT_CORE_V4_COMPLEX_TASK_CLARIFICATION_RED_A229F3`** — STOP at first failing boundary (P4-A). All earlier phases (P0/P1/P2/P3) GREEN; P4-B/P4-C GREEN; Core untouched.

**QA evidence:** `/private/tmp/qa229f3/` (p2_direct.json, p3_runs.json, p3_matrix.log, p4_browser.json, p4a_nondet.json, p4b_debug.json, cd_rerun2.json, audit.json, corpus_*.json, oracle_*.json, agent log `/private/tmp/qa229f3_agent.log`); QA scripts at repo root (untracked): `qa_229f3_p1_parser.py`, `qa_229f3_oracle.mjs`, `qa_229f3_oracle_probe.mjs`, `qa_229f3_p2_direct.py`, `qa_229f3_p3_runner.py`, `qa_229f3_p4c_taxonomy.py`, `qa_229f3_audit.py`, `po-agent-platform-v2/frontend/e2e/qa229f3-clarification.spec.ts`.

**Services left running:** agent 8004 (@65601f6), task-api 8241, MCP 3000, vite `[::1]:5175`.
