# Assignment 182 — Agent Core v4 Final POC Reliability Decision Gate

**Verdict: `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`**

The owner observation-hygiene fix is **certified correct at the planner boundary** (Phase 0
GREEN 8/8 + 23/23; DMS-380's 6137-char source description is bounded to 385 chars in the
planner-facing observation with all canonical identity fields intact; the 181 turn-3
bug-analysis essay is gone — turn 3 is a clean primary-JSON `task.search assignee=semavin.m.m`
in **30/30** runs). The mandatory 10× DMS-380 gate could **not** be certified 10/10 for a
reason that is **not** a planner/model defect: a **proven source-transport boundary** —
`task.search` → `GET /api/v1/swtr-read/assignee-tasks` (MCP-SWTR live read-through)
intermittently exceeds the adapter's **30 s httpx timeout** in the long-lived agent runtime
under sequential load, raising `AS21SourceUnavailable` and failing the run closed. The same
call succeeds **20/20 in isolation** (fresh connections, 6–18 s). This is outside the
observation-hygiene fix and outside QA scope (no production/adapter/timeout changes allowed).

**Date:** 2026-09-12
**QA role:** tester/adversarial reviewer only (no production/backend/frontend/test code,
prompts, model config, skill registry, adapter, or learning data modified)
**Branch:** `feat/core8-real-query-hardening-v2`
**Test base HEAD:** `c482ff67744dfd9ca1508dbfb3c50127d6f4bcbc` (Assignment 182 spec)
**Owner commits under test (all verified as ancestors of HEAD):**
- `93c6ffc` — `fix(v4): bound unstructured planner observations, keep identity fields exact`
  (`_compact_planner_value` classmethod recursively bounds known unstructured fields —
  `description`, `comment(s)`, `body`, `details`, `stacktrace(_trace)`, `log(s)`, `raw(_text)` —
  to 384 chars + `…`; structured identity/task/sprint/status/count fields untouched; only the
  planner observation (process line 843) is compacted, authoritative `result.data`/`evidence`
  (lines 836–837) remain raw)
- `c442f1b` — `test(v4): planner observation hygiene` (2 regression tests: bounded
  description + preserved identity; generic nested free-text bounding)
- `804ec23` — `docs: V4 DoD lock — final focused POC reliability gate before model/architecture decision`

**Runtime under test:**
- Model/provider: `Qwen/Qwen3.8-27B` (unchanged, per rules)
- Env: `PO_AGENT_AGENT_CORE_V4_ENABLED=true`, `PO_AGENT_AS21_MODE=task-api`,
  `PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8003`
- PO Agent: **fresh instance on `127.0.0.1:8009`** started from HEAD `c482ff6`
  (health: `agent_core_v4_enabled:true, agent_core_v4_ready:true, adapter:task-api,
  source_status:healthy, skill_readiness ready:51/degraded:0/unavailable:3`)
- Task API: `127.0.0.1:8003` (shared, healthy) — `swtr-read` → MCP-SWTR (SSE, 48 tools)
- MCP-SWTR (Oracle B): `127.0.0.1:3000/sse` → REAL AS21
- Runtime adapter (from health + probe): `EvidenceValidatedProductionTaskApiAS21Adapter`
  → `HardenedProductionTaskApiAS21Adapter` → `ProductionTaskApiAS21Adapter`;
  httpx `timeout_seconds = 30.0` (inherited from `task_api.py:214`)
- Concurrency: 1. Long agent call ≤ 600 s. Fresh session per run.

**Stale-runtime rule honored:** 8004/8005/8006/8007/8008 (prior assignments) not reused;
a fresh PO Agent was started from `c482ff6` on port **8009**.

---

## 0. Scope of the fix under test

`_compact_planner_value` (classmethod on `AgentCoreV4Runtime`) is invoked from
`_compact_data`; it recursively walks the observation dict, and for any string whose
field-name (casefolded) is in `_PLANNER_UNSTRUCTURED_FIELDS` (`description`, `comment`,
`comments`, `body`, `details`, `stacktrace`, `stack_trace`, `log`, `logs`, `raw`, `raw_text`)
and whose length exceeds `_PLANNER_FREE_TEXT_LIMIT = 384`, truncates to 384 + `…`. All other
values pass through unchanged. The **authoritative** result/evidence path is untouched
(`full_results.append({"data": result.data})`, `all_evidence.extend(result.evidence)` use raw
`result.data`/`result.evidence`); only the planner observation
(`data=self._compact_data(capability_id, result.data)`, line 843) is compacted.

---

## 1. Phase 0 — Focused build/protocol gate → **GREEN**

**Unit tests:**
`pytest tests/test_agent_core_v4_skill_native.py tests/test_agent_core_v4_robust_protocol.py tests/test_agent_core_v4_reliable.py`
→ **23/23 passed** (includes the 2 new `c442f1b` observation-hygiene tests).

**Static/behavioral gate (script `qa_182_p0_static.py`): 8/8 PASS**
1. Production V4 runtime uses the robust/action-only planner path (`RobustReliableAgentCoreV4Runtime`,
   constructed planner `RobustSkillNativePlannerV4`). PASS
2. Semantic-prepass absent from the V4 planner path: `process()` hardcodes
   `"semantic_prepass_used": False`; no `prepass(` call-site in any v4 module; the only
   `semantic-prepass` mention in the planner SYSTEM is the DO-NOT negation. PASS
3. Planner-facing long `description` is bounded: 2000-char input → len 385, ends with `…`. PASS
4. Nested unstructured fields (`details`, `comments`, `stacktrace`, `logs[]`) bounded by the
   same generic mechanism (all end with `…`, `count` intact). PASS
5. Canonical identity/task/sprint/status/space/count fields remain exact in the compact
   observation (`key=DMS-380`, `login=semavin.m.m`, `id=Semavin.M.M`, `status=Тестирование`,
   `sprint=DMS-SPRNT-2`, `space=DMS`, `count=42`). PASS
6. Authoritative `result.data` not mutated by compaction (original description length + assignee
   unchanged; compact structure is distinct). PASS
7. No DMS-380/entity/phrase/trajectory-specific branch in the fix: the `2f5d38e..HEAD` diff
   adds **no** entity literal in production `src/`; no `if`/`elif` branch in the v4 modules is
   keyed on an entity literal. (Matches in the tree are docstrings, Russian user-facing
   clarification strings, and the owner's *test fixture* — none are routing branches.) PASS
8. Action-only recovery safety retained: `_decode_dsl("READY…", allow_ready=False)` → None;
   primary READY still decodes; 4 bad turns end in `V4ContractError` (fail-closed). PASS

---

## 2. Phase 1 — Mandatory 10× multi-step gate → **BLOCKED (0/10, 3× runs = 30 attempts)**

### 2.1 Oracle B (fresh, REAL AS21/MCP-SWTR only) — script `qa_182_p1_oracle.py`
- `DMS-380` → `space=DMS`, `status=Тестирование (QA)`, `sprint=DMS-SPRNT-2`,
  `assignee = semavin.m.m` (id `Semavin.M.M`, Семавин Михаил Михайлович). Cross-checked:
  direct MCP-SWTR `get_task` and task-api `swtr-read` **agree** on the assignee.
- Canonical source assignee task collection via MCP-SWTR TQL `assigned_to = "Semavin.M.M"`:
  **306 tasks** (all in approved spaces DMS/OLP/STS). **Parity target = 306.**

### 2.2 Planner-observation proof (deterministic, real source) — script `qa_182_p1_observation.py`
Ran the real production `task.lookup` on DMS-380 and applied the production `_compact_data`:
- Authoritative `result.data.task.description` = **6137 chars** (a JSON doc blob — the exact
  181 distraction source).
- Planner-facing observation `description` = **385 chars**, ends with `…` (bounded).
- Identity fields **exact** in the observation: `key`, `status`, `sprint_id`,
  `assignee_login=semavin.m.m`, `assignee_id=Semavin.M.M` (both nested and at root).
- Authoritative dict **not mutated** by compaction. Source = REAL AS21.

This is the exact observation the planner receives at the post-lookup turn: the long
description is bounded, the canonical assignee login is intact.

### 2.3 10× gate — script `qa_182_p1_runner.py` (fresh session, concurrency 1)
Query: `Покажи DMS-380 и затем задачи его исполнителя`. Executed 3× (30 runs total):
two plain runs and one with an 8 s inter-run recovery gap. **All 30 runs: turn 3 is a clean
primary-JSON `task.search assignee=semavin.m.m` (via JSON, `recovery=0` on the critical turn,
`bad_lookup=False`, `any_wrong_lookup_on_assignee=False`)** — the 181 essay/derailment is gone.
**All 30 runs: `status=FAILED` (or `NEEDS_CLARIFICATION` on the 2 recovery-retry runs) with
0/306 keys**, `warnings=['source_unavailable']`, answer
`"Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат."`
(fail-closed, not empty/fabricated).

The first failing boundary is **not the planner**: every run's last trajectory step is the
correct `task.search assignee=semavin.m.m` at turn 3, and the run dies on the **source call**.

### 2.4 Proven source-transport boundary (the blocker)
The turn-3 `task.search` → `ProductionTaskApiAS21Adapter.search_tasks` →
`GET /api/v1/swtr-read/assignee-tasks?assignee=semavin.m.m&limit=100&max_pages=100`
(MCP-SWTR live read-through, up to 10000 rows, server-side TQL `assigned_to`). Evidence:

| Probe | Path | Result |
|---|---|---|
| Direct endpoint ×4 (fresh conn) | `/api/v1/swtr-read/assignee-tasks` | **200, 306 tasks, 6.5–14 s** |
| In-process `adapter._fetch_tasks(10000, source=swtr)` ×6 | task-api `/api/v1/tasks` | ok 6/6 (fast) |
| In-process `rt._task_search({assignee})` ×6 (real V4 handler) | `assignee-tasks` | **ok 6/6, 306, 2.9–12.4 s** |
| In-process `adapter.get_task("DMS-380")` ×6 (turn-2 path, swtr-read) | `/api/v1/swtr-read/tasks/{key}` | **found 6/6, 148–750 ms** |
| **Agent long-lived runtime, 10× gate ×3 (30 runs)** | `assignee-tasks` | **FAILED 30/30 — `source_unavailable`** (23–74 s ≈ 30 s httpx timeout) |

**Contrast:** the identical call succeeds **20/20 with fresh connections** (6–18 s) but fails
**30/30 in the long-lived uvicorn agent runtime** under sequential load, breaching the 30 s
httpx timeout. The turn-2 `get_task` path (fast swtr-read single key) is unaffected; the
turn-3 paged `assignee-tasks` read-through is the failed boundary.

This is a **source/transport reliability** failure at the task-api→MCP-SWTR read-through,
outside the observation-hygiene fix and outside QA's permitted changes (no adapter/timeout/
transport modifications). Per the assignment's Phase 1 STOP rule, this is recorded as
**`BLOCKED_BY_PROVEN_SOURCE_OUTAGE`**; the missing/failed source boundary is
`task.search → /api/v1/swtr-read/assignee-tasks` (30 s httpx ceiling vs. 6–30 s+ read-through
latency under sequential agent load).

### 2.5 Safety invariants during the 30 runs (all satisfied)
- **No wrong `task.lookup` recovery on an assignee:** `bad_lookup=False` in 30/30; the
  turn-4 `task.search` retry (DSL) in the 2 `NEEDS_CLARIFICATION` runs is a bounded
  post-source-failure retry, not a `task.lookup` on an assignee, and not a terminal.
- **No recovery-time READY:** no terminal `ready` was minted via DSL/recovery (terminals were
  `call`, then the run failed closed).
- **No local source truth / no fabricated facts:** 0 keys in every failed run; fail-closed
  `source_unavailable`, not an empty/zero-task answer.

---

## 3. Phase 2 — Mixed generalization gate → **SKIPPED**

Phase 2 runs only if Phase 1 is GREEN. Phase 1 is BLOCKED by a proven source outage, so the
mixed generalization matrix (3× person, 3× person+space, 3× PVM-Guru, 3× current sprint,
2× lookup-long-desc, 2× analytical, 2× unseen, plus the three saved defect cases) is **not
executed** for this assignment. The three 181 defect cases (sprint-by-period, enumerate all
active sprints, non-roster person morphology) are pre-existing **capability/catalog gaps**
documented in memory `GIGACODE-PO-AGENT-182-CASES` and are orthogonal to the observation
fix; they remain open items for a post-source-stability re-run.

---

## 4. Phase 3 — Safety / governance regression → **fail-closed preserved** (subset)

Executed the source-independent negative probes (the `assignee-tasks`-dependent ones are
unavailable under the outage). Script/probe results (`qa_182_p3_safety.json`):

| Case | Query | Status | Keys | Behavior |
|---|---|---|---|---|
| Invented task | `Покажи DMS-999999` | COMPLETED | 0 | fail-closed: "Задача DMS-999999 не найдена в REAL AS21." (no fabrication) |
| Invented person | `Задачи Неизвестного Псевдонима в DMS` | FAILED | 0 | fail-closed: `v4_runtime_failure`, "не смог безопасно завершить траекторию" (no fabrication) |
| Invented sprint | `Покажи задачи в спринте DMS-SPRNT-999` | NEEDS_CLARIFICATION | 0 | typed clarification: "Не удалось подтвердить спринт «DMS-SPRNT-999»…" |
| Source unavailable | (30× Phase 1 runs) | FAILED | 0 | fail-closed `source_unavailable`, "не интерпретируются как пустой результат" |

Governance preserved: **zero fabricated facts** across all probes; invented entities never
yield source-backed data. The fake `CALL`/`LOAD`/`READY` decode-safety property is retained
from Phase 0 item 8 (action-only recovery, 4 bad turns → `V4ContractError`, fail-closed).
Note: the invented-person case ends in `v4_runtime_failure` (fail-closed) rather than a typed
person-clarification — a minor control-plane polish item, not a safety regression (no
fabrication), and possibly influenced by the concurrent source outage.

---

## 5. Phase 4 — POC architecture evidence summary

- **Raw-query / progressive-skill V4 loop** active and end-to-end: load generic skill
  `tasks.lookup_then_assignee` → `task.lookup` (REAL AS21, canonical assignee) →
  `task.search` (trusted observation binding) → `ready`. Confirmed in 30/30 runs and the
  observation probe.
- **No semantic-prepass:** `semantic_prepass_used=false` in every run; prepass absent from
  the V4 planner SYSTEM/loop (Phase 0 item 2).
- **REAL source-backed grounding:** `task.lookup` exposes canonical `assignee_login`/
  `assignee_id`; `task.search` binds the trusted observation value (`semavin.m.m`), not a
  re-derived login. No entity hardcode / trajectory branch (Phase 0 item 7).
- **Observation hygiene (the 182 fix):** long unstructured source text (6137-char DMS-380
  description) is bounded to 385 chars **for the planner only**; authoritative `result.data`/
  `evidence` remain full-length; identity fields stay exact. This removes the 181
  distraction root cause (unbounded `description` derailing the turn-3 primary into a
  bug-analysis essay).
- **Fail-closed governance:** invented task/person/sprint and source-unavailable all fail
  closed with no fabricated facts; action-only recovery rejects terminal READY (Phase 0 item 8).

---

## 6. Phase 5 — Mandatory architecture decision gate

Decision framework (from the assignment): A = GREEN (all phases pass); B =
`V4_PLANNER_STRATEGY_REVIEW_REQUIRED` (fix correct but a fundamental model/control-plane
planner defect persists); C = bounded RED (concrete non-planner defect); and, per the Phase 1
STOP rule, a proven environment/source outage that is the **only** blocker →
`BLOCKED_BY_PROVEN_SOURCE_OUTAGE` (record the failed source boundary, stop remediation).

**Selected: `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`.**

Rationale:
- The observation-hygiene fix is **proven correct at its intended (planner) boundary**
  (Phase 0 8/8 + 23/23; observation bounded 6137→385 with exact identity; turn-3 clean
  primary-JSON `task.search assignee=semavin.m.m` in 30/30; no essay / no wrong lookup / no
  recovery-time READY).
- The 10× gate is **0/10 (30 runs)** solely because the turn-3 `task.search` read-through
  (`/api/v1/swtr-read/assignee-tasks`, MCP-SWTR-backed) intermittently exceeds the 30 s httpx
  timeout in the long-lived agent runtime, while succeeding 20/20 in isolation. This is a
  **source/transport boundary**, not a planner/model/control-plane defect.
- **Not B:** the planner is not the problem — there is no fundamental model or planner
  strategy defect; classifying this as B would misattribute a source-layer failure to the planner.
- **Not C:** this is not a single concrete, bounded, in-scope code defect QA can characterize
  into a fix; it is a source/adapter reliability boundary (timeout/transport/pagination under
  load) outside QA's permitted changes.

**Failed source boundary (recorded):** `task.search` → `GET /api/v1/swtr-read/assignee-tasks`
in the long-lived `EvidenceValidatedProductionTaskApiAS21Adapter`, whose paged MCP-SWTR
read-through (6–18 s baseline) exceeds the 30 s httpx `timeout_seconds` under sequential agent
load → `AS21SourceUnavailable` → run fails closed.

**Recommended owner action (out of QA scope, for the next assignment):** raise the
`assignee-tasks` read-through timeout above its observed p95 under agent load, and/or make the
read-through resilient (bounded retry + backoff on `ReadTimeout`, connection refresh, or
server-side pagination that returns within the timeout). Once the source boundary is stable,
re-run the 10× gate and Phases 2–4; the observation-hygiene fix is already certified at the
planner level and should pass.

**Consequence:** focused remediation **stops** for this assignment. Do **not** proceed to
Browser C / UI or 54-skill migration on the strength of this run (verdict is not A). Re-open the
decision gate after the source-boundary fix + a clean 10× (and Phase 2) re-run.

---

## 7. Reproduction

- Oracle B: `python3 qa_182_p1_oracle.py` (global `python3`, has `fastmcp`)
- Observation probe + source probes: `po-agent-platform-v2/.venv/bin/python qa_182_p1_*.py`
- 10× gate: `po-agent-platform-v2/.venv/bin/python qa_182_p1_runner.py` (and
  `qa_182_p1_runner_gap.py` for the 8 s-gap control)
- Safety probes: `qa_182_p3_safety.json`
- Artifacts: `qa_182_p1_oracle.json`, `qa_182_p1_observation.json`, `qa_182_p1_results.json`,
  `qa_182_p1_results_gap.json`, `qa_182_p1_sourceprobe.json`, `qa_182_p1_lookup_search.json`,
  `qa_182_p3_safety.json`, `qa_182_agent.log` (all untracked QA artifacts, not committed).