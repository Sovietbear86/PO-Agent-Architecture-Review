# Assignment 173 — H1B Canonical Grounded Literal Certification

**Verdict: `H1B_AGENT_ORACLE_PARITY_RED`** (Phase 3: 5/10 — collection parity broken by a pre-existing H1B executor 50-item cap; all other gates GREEN)

**Date:** 2026-09-10
**Test base HEAD:** `aaf4dbcd673b4bc62a9748b06e4154321c1d0894`
**Owner commits under test (ancestors verified via `git merge-base --is-ancestor`):**
- `b95cd24ecc777342bd514a9dae5d47ca8e2be7bf` — fix(h1b): accept literals equal to grounded source values
- `5c4473f90ca6aa21ddcf168309ef81cfc097ae6b` — test(h1b): cover canonical grounded literal acceptance

**Role:** QA/tester only. No production/backend/frontend/test code, prompts, config, or AS21/SWTR data modified by QA. Report-only commit.

---

## Executive summary

The owner fix is **certified at the identity/literal boundary**: the 172 defect (planner-verbatim canonical login rejected by the H1B guard) is closed. The primary gate **Phase 2 = 10/10** with exact REAL AS21 parity, and the full negative matrix (fuzzy/invented/wrong-field) proves the acceptance is exact-equality-only with no inference.

The assignment is **RED on Phase 3** (5/10) for a **different, pre-existing reason**: the H1B `task-search-v3` executor calls `adapter.search_tasks(jql)` without `max_results`, inheriting the adapter's default **50** (`production_task_api.py:121`, truncation at `:180`). For high-cardinality assignee collections (Kalachanov = **2867** tasks) exact key-set parity is structurally impossible, and the executor **misreports** `count=50` / "Найдено 50 задач" as the total. Identity grounding on those runs was correct (keys ⊆ oracle, canonical assignee). A second contributing finding: the same query shape ("Задачи <person>") routes **non-deterministically** between the H1B loop (capped) and the legacy `task-search-assignee` skill (full collection — Semavin 308/308 exact parity), so collection fidelity depends on the LLM's intent choice.

All other phases are GREEN: Phase 4 literal-safety negatives 6/6, Phase 5 protected multi-step regression (2-step typed loops, `$obs.*` observation-derived identity, constraint preservation), Phase 6 Browser C H0 5/5, Phase 7 Browser C real multi-step (2-step loop, observation-derived assignee, collected ⊆ Oracle B).

---

## Phase 0 — Preflight: PASS

| Check | Result |
|---|---|
| `git pull --ff-only origin feat/core8-real-query-hardening-v2` | `361d35a..aaf4dbc` fast-forward, clean |
| HEAD | `aaf4dbcd673b4bc62a9748b06e4154321c1d0894` |
| Owner commits ancestors | `b95cd24` YES, `5c4473f` YES |
| PO Agent restarted on new code | old uvicorn killed, 17 `__pycache__` dirs removed, restarted via `qa_168_start_po_agent.sh` (fresh `PO_AGENT_EXPECTED_HEAD`) |
| Task API `:8003/health` | `{"status":"healthy"}` |
| MCP-SWTR `:8003/api/v1/swtr-read/health` | `{"status":"connected","transport":"sse","tool_count":48}` |
| PO Agent `:8004/health` | `status=healthy, adapter=task-api, semantic_mode=qwen-llm, agent_core_v3_enabled=true, source_status=healthy` |
| Frontend `:5175` | 200, SPA root present |
| LLM | Qwen 3.8-27B, `https://api.ai.sbt/openai/v1`, unchanged |

**Static proof of the fix (loaded `agent_core_v3_h1b.py`):**
1. `_literal_matches_grounded()` exists; source check: only `raw.casefold() == candidate.casefold()` equality; no `startswith`/substring/`resolve_person`/`search_tasks`/intent/capability/team/adapter access.
2. Behavior matrix (10/10): `assignee` accepts literal equal to grounded `assignee` or `member_login` (case-insensitive, returns canonical form); partials `Garanin`, `Garanin.R`, `Garanin.R.Viktor`, foreign `Semavin.M.M`, empty → `None`; non-assignee fields accept only same-name grounded field; `space="Garanin.R.V"` → `None`; `release`/`task_key` with no grounded value → `None`.
3. No hardcoded name literals in `agent_core_v3_h1b.py`, `agent_core_v3_pilot.py`, `production_entity_grounding_v2.py` (grep: none).

---

## Phase 1 — Unit/build gate: PASS

| Suite | Result |
|---|---|
| 9 H1/H1B files incl. `test_agent_core_v3_h1b_grounding.py` (now 4 tests, incl. 3 new grounded-literal tests) + `test_production_entity_grounding_recovery.py` | **61/61 PASS** |
| Frontend `tsc --noEmit` | exit 0 |
| Static: no new literal name mappings / capability routing in production guard code | clean |

---

## Phase 2 — Primary gate: 10/10 GREEN

Fresh **Oracle B** (direct REAL AS21, `/api/v1/swtr-read/assignee-tasks?assignee=garanin.r.v`, never `/api/v1/tasks`): **23 tasks**.

| # | ms | llm_used | grounded member_login | loop assignee | keys | parity |
|---|-----|----------|----------------------|---------------|------|--------|
| 1 | 13535 | True | Garanin.R.V | Garanin.R.V | 23/23 | exact |
| 2 | 18330 | True | Garanin.R.V | Garanin.R.V | 23/23 | exact |
| 3 | 18124 | True | Garanin.R.V | Garanin.R.V | 23/23 | exact |
| 4 | 27743 | True | Garanin.R.V | Garanin.R.V | 23/23 | exact |
| 5 | 14030 | True | Garanin.R.V | Garanin.R.V | 23/23 | exact |
| 6 | 27046 | True | Garanin.R.V | Garanin.R.V | 23/23 | exact |
| 7 | 15104 | True | Garanin.R.V | Garanin.R.V | 23/23 | exact |
| 8 | 16053 | True | Garanin.R.V | Garanin.R.V | 23/23 | exact |
| 9 | 18396 | True | Garanin.R.V | Garanin.R.V | 23/23 | exact |
| 10 | 12073 | True | Garanin.R.V | Garanin.R.V | 23/23 | exact |

- **10/10 COMPLETED, exact 23/23 key-set parity, canonical assignee `Garanin.R.V`, no Cyrillic sent as identifier, zero `UNRESOLVED_CONSTRAINT`** — the 172 failure class (`llm_used=False` + planner-verbatim `Garanin.R.V` rejected) is gone: in 172 the identical behavior was 3/10; the fix accepts the verbatim grounded login.
- In this window the LLM prepass returned the person on all 10 runs (`llm_used=True`); the `llm_used=False`/empty-frame recovery path is covered by (a) offline live-source proof on the identical code+source (172: empty frame → `person_raw`/`member_login`/`assignee` bound, 0 clarifications), (b) the non-mocked unit suite, and (c) the 172 live evidence that the planner-verbatim path (the only path reachable when the prepass is empty) now passes.
- Planner constraint form: resolved step constraints show the canonical login in all runs; both syntaxes (reference / verbatim) are accepted by the guard — verified statically (Phase 0 matrix) and by unit tests; no run was rejected on literal-vs-reference asymmetry (`literal_vs_ref_asym_failure=false` for all 10).

**Primary stopping gate (10/10) PASSED.**

---

## Phase 3 — Cross-member: 5/10 RED

Fresh Oracle B: Semavin = **308**, Kalachanov = **2867** (REAL AS21 assignee route).

| run | route | skill | assignee | keys | parity |
|---|---|---|---|---|---|
| sem-1..5 (5× `Задачи Семавина`) | legacy | task-search-assignee | Semavin.M.M | **308/308** | **exact** |
| kal-1..5 (5× `Задачи Калачанова`) | H1B | agent-core-v3-h1b-loop | Kalachanov.V.V | **50/2867** | FAIL (⊆ oracle) |

Findings:
1. **Identity grounding correct in all 10**: canonical source-backed login in every run, keys always a subset of the oracle, no raw names sent.
2. **Semavin exact parity (308/308)** — routed to the legacy `task-search-assignee` skill, which returns the full collection.
3. **Kalachanov capped at 50** — routed to the H1B loop; `task-search-v3` executor returns at most 50 and reports `count=50`.
4. **Routing non-determinism (finding):** identical query shape routes per-query-string by LLM intent choice — 8/8 Semavin runs → legacy, 8/8 Kalachanov runs → H1B, 17/17 Garanin runs → H1B. Collection fidelity is therefore path-dependent, not capability-guaranteed.

---

## Root cause of the parity RED (pre-existing, not the owner fix)

```
agent_core_v3_pilot.py _execute_search:
    tasks = await self.adapter.search_tasks(jql)      # no max_results → default 50
    ...
    {"count": len(rows), ...}                          # 50 reported as the total
production_task_api.py search_tasks(..., max_results=50):
    # live assignee route pages fully (limit=100, max_pages=100), then
    return tasks[:max_results]                          # silent truncation at :180
```

- The truncation + misreported count predate `b95cd24` (executor/adapter unchanged by the fix) and were masked while all H1B-routed collections were ≤ 50 tasks.
- The legacy `task-search-assignee` path returns the full set (308 observed), so the capability exists — the H1B executor simply doesn't use it for large collections.
- Impact: any assignee with > 50 tasks routed to H1B cannot satisfy exact parity and receives a factually wrong count in the answer.

**Owner recommendation (QA did not modify code):**
1. In `task_search_executor_v3`, do not inherit the 50 default: either pass an explicit large `max_results` (the live assignee route already pages `limit=100/max_pages=100`) or make the capability contract explicit "top-N sample with authoritative total" (`count` = true total, `sample_size` = len(rows)).
2. Make "задачи <person>" vertical routing deterministic (single certified path with full-collection fidelity), or extend H1B to page the full collection.
3. Companion regression: non-mocked H1B test asserting full-collection parity for an assignee with > 50 REAL tasks (or a ≥ 60-row fake), plus a routing-stability test.

---

## Phase 4 — Literal safety negatives: 6/6 PASS

| # | Check | Result |
|---|---|---|
| 1 | Partial/fuzzy `Garanin`, `Garanin.R`, `Garanin.R.Viktor` vs grounded `Garanin.R.V` | NOT accepted (`None`) — static matrix + unit `test_grounded_literal_match_is_not_fuzzy` |
| 2 | Invented login-like literal not in query, not grounded (`Invented.X.Y`) | rejected by BOTH layers: `_literal_matches_grounded → None` and `_literal_is_source_safe → False` |
| 3 | Wrong-field grounded value (`space=Garanin.R.V`, `release=DMS`) | NOT authorized (`None`) — unit `test_non_assignee_literal_must_match_same_grounded_field` |
| 4 | `$ground.assignee` / `$ground.member_login` / `$ground.space` | resolve to canonical values; missing `$ground.release` → `UNRESOLVED_CONSTRAINT` fail-closed |
| 5 | `$obs.*` references | accepted by source-safety guard; exercised live in Phase 5A (observation-derived assignee) |
| 6 | Nonexistent identity (3× `Задачи Петрова`, not in TeamDirectory/source) | 3/3 `NEEDS_CLARIFICATION`, 0 tasks, no auto-bind ("Петров не найден в списке участников команды…") |

No fabricated execution anywhere; fuzzy matches remain unsafe.

---

## Phase 5 — Protected H1B multi-step regression: loop GREEN, collection capped

Fresh Oracle B: DMS-380 `assigned_to = semavin.m.m` (308 tasks); Garanin@DMS = 7; Kalachanov@WMB = 5.

| query | route | steps | result |
|---|---|---|---|
| 3× `Проверь DMS-380 и затем покажи задачи его исполнителя` | H1B | 2 each (task-lookup → task-search) | **3/3 OK** — real typed multi-step loop; step-2 assignee resolved from the DMS-380 observation (`semavin.m.m`); collection 50/308 (50-cap, keys ⊆ oracle) |
| `Задачи Гаранина в DMS` | H1B | 1 | **PASS** 7/7 exact; cons `{assignee: Garanin.R.V, space: DMS}` |
| `Задачи Калачанова в WMB` | H1B | 1 | **PASS** 5/5 exact; cons `{assignee: Kalachanov.V.V, space: WMB}` |
| `Покажи DMS-380` | H1B | 1 | **PASS** keys = {DMS-380} |
| `Найди задачи Гаранина в DMS и затем покажи подробности DMS-380` | H1B | 2 | **PASS** — 8 keys = 7 Garanin@DMS (full set) + DMS-380; both sub-results present |

Observation-derived (`$obs.*`) and source-grounded constraints preserved; no heuristic single-shot regression. The only defect is again the collection cap (A: 50/308).

*(First Phase 5 attempt hit a transient LLM-provider 429 window — `HTTP 429 Too Many Requests` from `api.ai.sbt`; re-run after backoff produced the results above. No source outage.)*

---

## Phase 6 — Browser C H0: 5/5 PASS

`npm run e2e:h0` (Playwright Chromium, dev server :5175, concurrency 1):

```
✓ session isolation and new conversation are real browser behavior (1.7m)
✓ v3 browser pilot: Задачи Гаранина (29.0s)
✓ v3 browser pilot: Задачи Гаранина в DMS (19.5s)
✓ v3 browser pilot: Задачи Калачанова в WMB (41.4s)
✓ v3 browser pilot: Покажи DMS-380 (10.5s)
5 passed (3.4m)
```

## Phase 7 — Browser C real multi-step: PASS (collection capped, documented)

Fresh Playwright Chromium conversation, query `Проверь DMS-380 и затем покажи задачи его исполнителя`:

| Field | Value |
|---|---|
| Browser session id | `ui-bfd51ed5-bc14-46a0-93e7-11dccfa8c086` (first attempt, 429) → re-run session persisted in artifacts |
| trace_id | persisted in `qa_173_browser_c/browser_c_result.json` |
| status | COMPLETED |
| loop steps | 2 (task-lookup DMS-380 → task-search assignee) |
| Oracle B (fresh) | DMS-380 `assigned_to=semavin.m.m`, 308 tasks |
| Browser C collection | 50 keys, **⊆ Oracle B**, exact parity false (50-cap, same as Agent A) |
| Rendered answer | visible in browser, matched to payload |
| Screenshot | `qa_173_browser_c/browser_c_multistep.png` |

**Browser C == Agent A** (identical 2-step behavior and identical 50-key collection for the same query, same window); both equal Oracle B only up to the shared 50-cap.

---

## Verdict

`H1B_AGENT_ORACLE_PARITY_RED`

- The owner fix under test is **fully certified**: 172 boundary closed, primary gate 10/10, negative matrix 6/6, no routing/inference introduced, `$ground.*`/`$obs.*` intact, browser intact.
- H1B is **NOT closed**: exact collection parity is broken for H1B-routed collections > 50 tasks (Phase 3 Kalachanov 50/2867; Phase 5A 50/308) due to the pre-existing `max_results=50` executor default + misreported total, compounded by non-deterministic legacy/H1B routing for the same query shape.
- Next actions for the owner: (1) fix the task-search-v3 collection cap/count (root cause above), (2) deterministic routing or full-collection H1B capability, (3) regression tests. Then a 174 retest of Phases 3+5 collection parity is expected to close H1B and proceed to **H1C Progressive Skill Loading**.

## QA artifacts (untracked, not committed)

- `qa_173_phase23_results.json` — Phase 2/3 per-run evidence (latency, llm_used, recovery flag, grounded slots, resolved constraints, keys, parity, failure codes) + Oracle key sets
- `qa_173_phase3_results.json` — Phase 3 re-run (dual-shape extraction, per-route)
- `qa_173_phase5_results.json` — Phase 5 loop steps + oracles
- `qa_173_browser_c/browser_c_result.json` + `browser_c_multistep.png` — Phase 7 persisted evidence
- No production/test/config/`.env`/AS21-SWTR data modified; no runner modified.