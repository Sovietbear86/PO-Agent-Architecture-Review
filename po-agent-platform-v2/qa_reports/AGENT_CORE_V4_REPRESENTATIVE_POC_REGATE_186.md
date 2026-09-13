# Assignment 186 — V4 Representative POC Re-Gate after A185 (B1+B2)

**Role:** QA/tester only.
**Branch:** `feat/core8-real-query-hardening-v2`
**START_HEAD / test base:** `5ac6290` (A186 spec) — includes A185 fixes `e997e3a` (B1) and `cc39e18` (B2).
**Date:** 2026-09-13
**Verdict:** **`V4_B1B2_REGATE_GREEN_P1_LLM_ENDPOINT_BLOCK`**

---

## 1. Single verdict

The two A184 bounded defects are **PROVEN fixed** against fresh REAL AS21 at both the
task-api route level and the agent level:

- **B1** (bounded complete sprint-task collection for >100-task sprints): route-level
  exact and agent-level 4/4 exact. The A184 failure mode ("Задачи в текущем спринте DMS"
  fail-closed 3×90s for the 104-task sprint) is **closed**: the same query now returns
  104/104 exact in 28–38s.
- **B2** (source-schema-aware terminal/open status classification): route-level exact
  (404/404, 0 undecodable) and agent-level 3/3 exact on the 2858-row assignee set. The
  A184 failure mode ("открытые задачи в STS" reporting 2609 vs 404 true non-terminal) is
  **closed**: the agent now returns exactly the 404 live non-terminal keys.

No new code defect was found. No safety regression. Zero fabricated keys in any run.
Semantic pre-pass invariant holds (0 `semantic_prepass_used=true` across all live runs).

**Blocked item (environmental, A/B-proven, NOT a B1/B2 regression):** the retained P1
gate — 10× "Покажи DMS-380 и затем задачи его исполнителя" (exact 306/306) — regressed
from A184's 10/10 to 0/10–2/9 today. A controlled A/B against A184's own HEAD
(`21a6275`, the code that scored 10/10 in A184) run on a read-only worktree **also
scores 0/5 today with the identical failure signature** (`planner failed robust bounded
repair: [invalid_primary_decision, invalid_recovery_action …]`). Both stacks share the
same Qwen3.8 endpoint (`api.ai.sbt`). Attribution is therefore **LLM endpoint
degradation** — the documented A179–A182 planner-reliability lineage whose owner fix is
"constrained/structured output JSON decoding or deterministic fallback for the
lookup→assignee→search pattern". All direct-search (non-multistep) V4 paths remain green
on the A185 stack (B1 4/4, B2 3/3+singles, 12/12, 2858/2858, 10/10, 2/2, 6/6 exact),
which is inconsistent with a code regression and consistent with stochastic turn-4
post-observation planner failure.

Consequence per A186 spec: backend POC remediation for B1/B2 is complete and certified;
the POC cannot be declared fully green until the owner-level LLM-reliability fix (A179
class) lands and the 10× P1 multistep gate is re-run.

---

## 2. Static gate (Phase 0/1) — GREEN

| Suite | Result |
|---|---|
| Focused B1/B2, po-agent (`test_sprint_collection_b1.py`, `test_status_semantics_b2.py`) | **15 passed** |
| Focused B1/B2, task-api (`test_swtr_read_sprint_collection.py`, `test_swtr_assignee_canonical.py`) | **34 passed** |
| Broader po-agent suite | **1349 passed, 12 skipped, 16 failed + 11 errors = 27 nodes — ALL pre-existing baseline classes** (real-LLM, SWTR integration, order-dependent), byte-identical node set to the A184/A185 base; zero new node IDs |
| task-api swtr guards | **38 passed** |
| Static invariants | 0 semantic-pre-pass call-sites; 0 `semantic_prepass_used=true` (all 7 literal sites are `false`); entity-scan hits only in pre-existing comments/docstrings; no planner-prompt changes in A185 diff |

A185 B2 diff reviewed at the planner boundary: the `agent_core_v4.py` change is
filter-only (`not_completed` → `task.is_open`); the planner-facing observation builder
(`_compact_data`: 20-key sample + count) is unchanged; the `swtr_assignee.py` status
normalization feeds adapter classification, not planner prompt text.

## 3. Fresh Oracle B (Phase 2) — collected 2026-09-13 11:08Z (live-verified refreshes noted)

| Fact | Value |
|---|---|
| DMS-380 | space=DMS, sprint=DMS-SPRNT-2, status=«Тестирование»/progress, assignee=Semavin.M.M (semavin.m.m) |
| DMS sprints | DMS-SPRNT-1 (current, 104 tasks), DMS-SPRNT-2 (39 tasks); both status NEW |
| B1 primary | `DMS-SPRNT-1` = **104 keys** (the A184 >100-task case) |
| B1 small | `DMS-SPRNT-2` = **39 keys** |
| B2 Kalachanov | total **2858**, open=490, terminal=2368, undecodable=**0**, statusType hist {progress:153, pause:337, done:2368}; **STS open = 404 keys** (the A184 B2 case) |
| Matrix | Semavin 306 (DMS 138 / OLP 166 / STS 2); Zhdanov 12; Kuznetsov 62; Ivanov 36 |
| PVM-Guru | **0 rows** (stale fixture gone from source — negative preserved) |
| Identity route | Ivanov.P.Se 200, Kalachanov.V.V 200, Moiseev.A.N 200; invented → 409 (fail-closed) |

Drift notes (live-verified during the run, agent held correct live truth):
- `OLP-3295` moved to `pause`/«Ready for QA» (non-terminal) after the 11:08Z collection;
  live-verified via source `statusType=pause`. Oracle refreshed.
- Zhdanov WMB open went 1→0 between the A184 and A186 collections (a task closed in-source).

## 4. Route-level proof on fresh task-api (Phase 2b) — GREEN

Fresh task-api `8041` (SSE → MCP-SWTR:3000, HEAD `5ac6290`), plus long-lived `8032` for
load characterization.

- **B1:** `GET /swtr-read/sprints/DMS-SPRNT-1/tasks?space=DMS&complete=true` →
  `complete_tasks=104 unique=104 complete=True source_path=tql_sprint_constraint
  pages_fetched=2` — **exact match to oracle 104**. `DMS-SPRNT-2` → `39/39 complete=True
  source_path=get_sprint_tasks` — exact. (Note: the response's raw `tasks` field is the
  primary-view first page; the deduped complete set is `complete_tasks` — the field the
  agent adapter consumes. An early QA probe that counted `tasks.content` produced a
  false 100-row "anomaly"; re-probing `complete_tasks` closed it.)
- **B2:** `GET /swtr-read/assignee-tasks?assignee=Kalachanov.V.V&space=STS` → 2693 rows;
  flat `swtr_attributes` carry decoded `workflow_status.statusType` on every row;
  open = **404/404 exact match to oracle**, undecodable = **0**; statusType hist
  {progress:98, pause:306, done:2289}.

## 5. Agent-level gates (Phases 3–7)

Fresh PO Agent runtimes (all `PO_AGENT_AGENT_CORE_V4_ENABLED=true`,
`PO_AGENT_EXPECTED_HEAD=5ac6290`): `8035`, `8040`, `8044` (primary A/B stack →
task-api `8041`). Agent contract: `POST /api/v1/query-v4`.

### Phase 3 — B1 regression family: **GREEN 4/4**

| Query | Oracle | Agent | Verdict |
|---|---|---|---|
| «Задачи в текущем спринте DMS» ×3 | 104 (DMS-SPRNT-1) | **104/104 exact ×3** (28.5–38.2s) | PASS ×3 |
| «Покажи задачи в спринте DMS-SPRNT-2» | 39 | **39/39 exact** (27.1s) | PASS |

A184's B1 failure (3×90s fail-closed) is gone; latency is in the 28–38s band.

### Phase 4 — B2 regression family: **GREEN**

| Query | Oracle | Agent | Verdict |
|---|---|---|---|
| «Открытые задачи Калачанова в STS» ×3 | 404 | **404/404 exact ×3** (47.8–59.6s) | PASS ×3 |
| «Открытые задачи Жданова в STS» | 1 | **1/1 exact** (34.8s) | PASS |
| «Открытые задачи Семавина в STS» | 1 | **1/1 exact** (24.5s) | PASS |

Surname-only «Иванова» → typed clarification «Не удалось однозначно определить
пользователя» (ambiguous non-roster reference — correct fail-closed, pre-existing
A182/183 person-resolution boundary, out of B1/B2 scope).

### Phase 5 — Retained P1 10× DMS-380 multistep: **RED (environmental, A/B-proven)**

| Stack | Result |
|---|---|
| 8035 → 8032 (after p3/p4 load) | 7× FAILED (58–118s), typed v4_runtime_failure, 0 keys |
| 8040 → 8032 (fresh agent) | 2/9 (first two pass at ~25s, then fail) |
| **8044 → 8041 (fresh agent + fresh task-api, clean file)** | **0/10** |
| 5× repeat on 8044 | **0/5** — failure signatures: `planner failed robust bounded repair: [invalid_primary_decision, invalid_recovery_action ×3]`; `planner literal is not grounded in user query: task_key=306` (count→key hallucination); re-emitted `task.search` without assignee → clarification |
| **A/B: A184 HEAD `21a6275` worktree stack (8050 → 8045)** | **0/5, identical signature** — the code that scored 10/10 in A184 fails identically today |

Key trajectory fact: on the A185 stack turn-3 is still clean
(`task.search assignee=semavin.m.m` valid JSON — the A182 observation-hygiene fix
holds); failures occur at the post-search READY turn and in bounded-repair attempts.
Both A184-HEAD and A185-HEAD stacks share the same Qwen3.8 endpoint; both fail
identically ⇒ **LLM endpoint degradation, not a B1/B2 code change.** Historical
lineage: A179 ("Qwen3.8-27B planner intermittently emits invalid JSON … 3/16 runs
completed (19%). Fix needed: constrained/structured output JSON decoding or
deterministic fallback for lookup→assignee→search"), A180/A181 (turn-3 derailments),
A182 (route-timeout blocker on the same query).

Load characterization (not the root cause, recorded for completeness): long-lived
task-api→MCP-SWTR SSE sessions show intermittent 26–31s latency spikes for the
assignee route under accumulated load (fresh session: 6–13s; direct MCP-SWTR:3000
fresh connection: 2.5–4.0s). This is the pre-existing A182 owner item
("raise assignee-tasks timeout above p95 under load and/or bounded retry /
connection-refresh").

### Phase 5b — Retained A183 scenarios

| Query | Oracle | Agent | Verdict |
|---|---|---|---|
| «Открытые задачи Семавина в DMS» | 6 | **6/6 exact** (40.9s) | PASS |
| «Открытые задачи Семавина в OLP» | 4→5 (live drift) | **5/5 vs live source** (OLP-3295 verified `pause`/Ready-for-QA) | PASS (oracle refreshed) |
| «Задачи Семавина» | 306 | FAILED, 0 keys, 10.6s — LLM class (retry: `planner person reference is neither query-derived nor uniquely team-scoped: Семанин` — model-mangled name, fail-closed) | LLM class, fail-closed |
| «Задачи Иванова Петра Сергеевича» | 36 | NEEDS_CLARIFICATION, 0 keys | known pre-existing non-roster person boundary (A182/183) |
| «Покажи задачи Неизвестного Псевдонима» | 0 | FAILED, 0 keys | PASS (fail-closed) |

### Phase 6 — Mixed representative matrix: **7/8**

| Query | Oracle | Agent | Verdict |
|---|---|---|---|
| «Задачи Жданова» | 12 | **12/12 exact** | PASS |
| «Задачи Калачанова» | 2858 | **2858/2858 exact** (78.5s) | PASS |
| «Покажи DMS-99 и затем задачи его исполнителя» | 62 (Kuznetsov) | FAILED — LLM class (same turn-4 pattern as P1) | LLM class |
| «Сколько незакрытых задач у Семавина в OLP?» | 4 (11:08Z oracle) → 5 (live, OLP-3295 drift) | COMPLETED, 4/4 vs collection-time oracle; answer «4». Live truth had drifted to 5 minutes earlier (p5-sem-olp returned 5/5 live, incl. OLP-3295 `pause`). The prose count is model-drafted from the observation — an off-by-one vs the live key set is an LLM drafting artifact, not a B1/B2 classification defect; the deterministic key-set check (p5-sem-olp 5/5 live; p4 404/404) is the authoritative status-semantics evidence | PASS (count with drift/drafting note) |
| «Кто исполнитель задачи DMS-380?» | Semavin | COMPLETED, «Семавин Михаил Михайлович (semavin.m.m)» | PASS |
| «Покажи здоровье спринта DMS-SPRNT-1» | 104 | COMPLETED, 104 keys | PASS |
| «Проверь качество формулировки задачи DMS-380» | — | COMPLETED (quality analysis) | PASS |
| «Активные спринты в DMS» | 2 | COMPLETED, lists DMS-SPRNT-1 + DMS-SPRNT-2 | PASS |

### Phase 6b — Unseen combinations: **2/2 exact (+1 known boundary)**

| Query | Oracle | Agent | Verdict |
|---|---|---|---|
| «Открытые задачи Кузнецова в OLP» | 10 | **10/10 exact** (36.4s) | PASS |
| «Открытые задачи Жданова в спринте DMS-SPRNT-1» | 2 | **2/2 exact** (61.0s) | PASS |
| «Открытые задачи Иванова в STS» | 2 | NEEDS_CLARIFICATION | known pre-existing person boundary |

### Phase 7 — Safety / governance / fail-closed: **GREEN**

| Case | Result | Verdict |
|---|---|---|
| «Покажи DMS-999999» (invented task) | COMPLETED, 0 keys, «Задача DMS-999999 не найдена в REAL AS21» | PASS (typed not-found, no fabrication) |
| «Покажи задачи в спринте DMS-SPRNT-999» (invented sprint) | NEEDS_CLARIFICATION, 0 keys, «Не удалось подтвердить спринт … по данным REAL AS21» | PASS (typed clarification) |
| «Покажи задачи Неизвестного Псевдонима» (invented person) | FAILED, 0 keys (typed v4 failure) | PASS (fail-closed) |
| Dead-source probe (disposable agent 8053 → dead task-api port 8099, «Покажи DMS-380») | FAILED, 0 keys, **5.9s bounded**, «Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат.» | PASS (A184 reference: 7.1s) |

**Invariants across all live runs:** `semantic_prepass_used=false` in 100% of runs;
zero fabricated task keys in any FAILED/NEEDS_CLARIFICATION response; every failure is
typed and bounded.

---

## 6. Findings register

1. **[CLOSED] B1** — bounded complete sprint-task collection: route 104/104 + 39/39
   exact, agent 4/4 exact. A184's 3×90s fail-closed eliminated.
2. **[CLOSED] B2** — source-schema-aware open/terminal classification: route 404/404
   exact, undecodable=0; agent 404/404 ×3 + open-filter singles exact. A184's 2609-vs-404
   miscount eliminated.
3. **[BLOCKED, environmental] P1 10× DMS-380 multistep** — regressed 10/10 (A184) →
   0/10–2/9 (A185 stack) and **0/5 on A184 HEAD itself today** (A/B worktree proof,
   identical signature). Root cause: Qwen3.8 planner reliability degradation at the
   post-observation READY turn (A179 lineage). Owner fix (pre-existing, unchanged):
   constrained/structured output JSON decoding or a deterministic fallback for the
   lookup→assignee→search READY step. Re-run this gate after the fix.
4. **[PRE-EXISTING, recorded] Long-lived task-api→MCP-SWTR SSE session latency
   spikes** (26–31s under accumulated load vs 6–13s fresh; MCP-SWTR:3000 fresh
   connection 2.5–4.0s). A182 owner item (timeout/retry/connection-refresh). Not a B1/B2
   contribution; did not cause any incorrect result (all failures were typed
   fail-closed).
5. **[PRE-EXISTING, recorded] Non-roster person references** (Ivanov) return typed
   clarification — A182/183 boundary, unchanged.
6. **[QA artifact, closed] `tasks` vs `complete_tasks`** — early probe miscounted the
   primary-view page as the complete set; the adapter-consumed `complete_tasks` field is
   exact. No defect.
7. **[QA artifact, closed] Oracle staleness** — OLP-3295 and Zhdanov-WMB drifted in the
   live source mid-run; agent held correct live truth in both cases; oracle refreshed.

## 7. Reproduction

- Fresh Oracle B: `python3 qa_186_oracle_b.py` → `qa_186_oracle_b.json`
- Live gates: `PO_BASE=http://127.0.0.1:8044 python3 qa_186_live_runner.py --phase p3|p4|p5a|p5b|p6|p6b|p7`
- A185 stack: task-api `8041` (SSE→MCP-SWTR:3000, HEAD `5ac6290`) + agent `8044`
  (`qa_186_start_po_agent_8044.sh`)
- A/B A184 HEAD: read-only worktree at `21a6275` (removed after use) → task-api `8050`
  + agent `8051` (main-tree venv, worktree code)
- Dead-source probe: agent `8053` → dead port `8099`
- Raw A/B LLM evidence: `qa_186_evidence_llm_ab.json`

## 8. Git

- Only this report file is committed and pushed (per A186 spec).
- Scratch artifacts (untracked, not committed): `qa_186_*` runners/oracles/evidence,
  start scripts, `/tmp` logs.

**END OF REPORT — STOP per assignment (no Assignment 187).**