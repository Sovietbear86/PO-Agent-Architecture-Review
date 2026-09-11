# Assignment 179 — Agent Core v4 Capability-Binding Continuation

**Verdict: `V4_CAPABILITY_BINDING_RED`**

**Date:** 2026-09-11
**QA role:** tester/adversarial reviewer only (no production/backend/frontend/test code, prompts, model config, skill registry, or learning data modified)
**Branch:** `feat/core8-real-query-hardening-v2`
**Test base HEAD:** `4776614aeb038fa948b6e726ab71b3b0043acd7b`
**Owner commits under test (verified ancestors of HEAD):**
- `ba7f453cdc8f9e01696833c5a71156881d773b9a` — `fix(v4): bind canonical task assignee observations safely`
- `d7ebcd283ac3152941cad85f2c702460206bb903` — focused regression tests for canonical lookup binding + false-positive identity matching

**Runtime under test:**
- Model/provider: `Qwen/Qwen3.8-27B` (unchanged, per rules)
- Env: `PO_AGENT_AGENT_CORE_V4_ENABLED=true`, `PO_AGENT_AS21_MODE=task-api`
- PO Agent: **fresh instance on `127.0.0.1:8006`** started from current HEAD `4776614`
  (health: `v4_enabled:true, v4_ready:true, adapter:task-api, source_status:healthy`)
- Task API: `127.0.0.1:8003` (shared) — `swtr-read` connected to MCP-SWTR (SSE, 48 tools)
- MCP-SWTR (Oracle B): `127.0.0.1:3000/sse` → REAL AS21
- Concurrency: 1. Source timeout ≥ 300 s. Fresh session per run.

---

## 0. Checkpoint reuse & environment integrity

Retained (not re-run) Assignment 178 evidence per checkpoint-reuse instruction:
sprint.current source wiring GREEN; Phase 2 Garanin/Moiseev/PVM-Guru benchmark GREEN;
current sprint GREEN; generalization 5/6 exact; cross-skill task lookup/summary/quality/
acceptance/blockers/sprint-health/current-sprint GREEN; release health is source-limited
(fail-closed, no fabrication — retained as source-capability-unavailable).

**Stale runtime rule honored:** the Assignment 178 instance (port 8005, previous commit)
was **not** reused. A fresh PO Agent process was started from current HEAD `4776614` on
port 8006 and all Agent A phases ran against it.

---

## 1. Phase 0 — Focused build/unit gate → GREEN

- `pytest tests/test_agent_core_v4_reliable.py tests/test_agent_core_v4_skill_native.py`
  → **11 passed** (includes the new canonical-lookup-binding and false-positive-identity
  regression tests from `d7ebcd2`).
- Production V4 factory still instantiates `ReliableAgentCoreV4Runtime` (unchanged).
- Static/runtime proof (`qa_179_p0_static.py`, **17/17 PASS**):
  1. `_token_equivalent("гарановых","гаранин") == False` (178 false-positive closed);
     `"моисеев"/"моисеева" == True` (inflection preserved); exact-token matches preserved.
  2. `ref("Гарановых")` does **not** match the Garanin roster entry; `ref("Гаранин")` does.
  3. `task.lookup` is wired to the **new** source-backed handler
     `_task_lookup_source_backed` (not the legacy observation shape).
  4. The lookup observation surfaces canonical **`assignee_login`** and **`assignee_id`**.
  5. `_trusted_identity_values` accepts `assignee_login`/`assignee_id`/`member_login` and
     **rejects the human display string** (no id derived from display text).
  6. No person/task/sprint entity facts hardcoded in the handler.

Phase 0 gate = **GREEN** (no `V4_BUILD_RUNTIME_RED`).

---

## 2. Phase 1 — Canonical lookup → assignee → tasks binding gate → **RED (first failing boundary)**

### 2.1 Oracle B (REAL AS21, refreshed)
- `DMS-380` canonical assignee (via REAL AS21 `swtr-read` path → `get_task`):
  **`assignee_id = Semavin.M.M`**, `assignee_login = semavin.m.m`,
  display `Семавин Михаил Михайлович`, status **QA**, sprint `DMS-SPRNT-2`.
  (MCP `read_unit`/`get_task`/TQL-by-code are flaky for DMS-380 specifically; the
  `swtr-read` task path that the agent actually uses consistently returns `Semavin.M.M`,
  independently corroborated in Assignment 178.)
- `Semavin.M.M` full task set (REAL MCP-SWTR TQL `assigned_to = "Semavin.M.M"`):
  **306 tasks**, all in approved PO Agent spaces `DMS/OLP/STS`.

### 2.2 Result — 5x fresh sessions `Покажи DMS-380 и затем задачи его исполнителя`
The `task.lookup` observation **now exposes** the canonical identity (fix confirmed):
```
LOOKUP OBS: {"assignee_login":"semavin.m.m","assignee_id":"Semavin.M.M",
             "assignee_display":"Семавин Михаил Михайлович","task_key":"DMS-380"}
```
- **Required 5x run:** **2/5** terminated `COMPLETED` with **306/306 exact parity**;
  **3/5** `FAILED`.
- Larger batch (N=8): **0/8** completed. Error-capture (N=3): 1/3 completed.
- **Aggregate: 3/16 (≈19%)** terminally correct with exact parity.

### 2.3 First failing boundary (raw)
Successful runs:
```
trajectory: load_skill:tasks.lookup_then_assignee
            -> call:task.lookup {"task_key":"DMS-380"}
            -> call:task.search {"assignee":"semavin.m.m"}
            -> ready:None      →  COMPLETED, 306/306 exact
```
Failing runs:
```
status=FAILED  warnings=[v4_runtime_failure]
exception_type=V4ContractError
error="planner failed bounded repair: ['invalid_json_decision','invalid_json_decision','invalid_json_decision']"
trajectory: load_skill:tasks.lookup_then_assignee
            -> call:task.lookup {"task_key":"DMS-380"}
            (no task.search step emitted)
```
(`invalid_json_decision` ×3 in 7/8 batch runs; 1 run `['ValidationError','invalid_json…']`.)

### 2.4 Root-cause analysis (important)
- **The owner's observation-binding contract fix is PROVEN WORKING.** When the LLM planner
  emits a valid step-2 decision, the `task.search` assignee is bound to the trusted
  observation value `semavin.m.m` (never derived from the display string), and the result
  is **306/306 exact**. There is **no** `task.search.assignee must equal a source-backed
  prior observation` rejection anymore (that was the Assignment 178 defect — now fixed).
- **The remaining RED is planner (LLM) reliability.** After the `task.lookup` observation,
  `SkillNativePlannerV4.decide()` asks `Qwen/Qwen3.8-27B` for the next decision. The model
  intermittently returns content that is not valid decision JSON (or JSON that fails the
  `V4Decision` schema); after 3 bounded-repair attempts it raises
  `V4ContractError: planner failed bounded repair: ['invalid_json_decision' …]`. This is
  the Qwen3.8 planner's 2nd-step decision emission, not the binding contract.
- No LLM endpoint outage: 8006 log shows HTTP 200 responses (no 429/timeout) — the model
  is responding, just with malformed decisions at a high rate on this 2-step trajectory.

Per the assignment Phase 1 rule — *"Any `V4ContractError` at this boundary ⇒
`V4_CAPABILITY_BINDING_RED` and STOP"* — the verdict is `V4_CAPABILITY_BINDING_RED`, with
the precise mechanism documented above (planner JSON reliability at the binding boundary,
not a binding-contract rejection).

**Smallest generalized owner fix (QA recommendation, not implemented):** harden the
planner's 2nd-step decision reliability for the multi-step `tasks.lookup_then_assignee`
trajectory — e.g. constrained/structured-output JSON decoding against the `V4Decision`
schema, a smaller/trimmed planner observation view after `task.lookup`, more repair
attempts, or a deterministic fallback step for the known lookup→assignee→search pattern.
This is a planner/orchestration fix, **not** a binding-contract change (the contract already
works) and **not** a surname/phrase/semantic-prepass patch.

---

## 3. Phase 2 — Identity safety precision gate → GREEN (6/6)

`qa_179_p2_results.json`. Oracle B refreshed: `Garanin.R.V` = 33 tasks.

| Case | Query | Runs | Result |
|---|---|---|---|
| 178 false-positive | `Задачи Гарановых` | 3/3 | **NEEDS_CLARIFICATION**, 0 tasks, **not** Garanin |
| real inflection | `Задачи Гаранина` | 3/3 | **COMPLETED**, **33/33 exact** `Garanin.R.V` |
| invented prefix | `Задачи Гарановича` | 3/3 | **NEEDS_CLARIFICATION**, 0 tasks, **not** a real colleague |

- Unrelated/nonexistent surnames sharing only a partial prefix (`гарановых`, `гаранович`)
  no longer resolve to a real colleague by common prefix. **The 178 false-positive is closed.**
- Real inflected names still resolve with exact Oracle parity.
- No fabricated identities/tasks. `semantic_prepass_used=false` on all runs.

Phase 2 gate = **GREEN** (no `V4_SAFETY_RED`).

---

## 4. Phase 3 — Context identity generalization gate → mechanism GREEN; 1 source-transliteration gap

`qa_179_p3_oracle.json` (Oracle B, `OLP-SPRNT-5` = 67 tasks) + `qa_179_p3_results.json`.
Sprint assignees include sprint-only non-roster `Shaldunov.A.V` and `Sidneva.Y.S`.

| Case | Query | Runs | Oracle | Result |
|---|---|---|---|---|
| Shidneva (Ш) | `Открытые задачи Шидневой в спринте OLP-SPRNT-5` | 5/5 | `OLP-3179` (1) | **NEEDS_CLARIFICATION** |
| Shaldunov (regression) | `Задачи Шалдунова в спринте OLP-SPRNT-5` | 2/2 | 10 keys | **COMPLETED, 10/10 exact** |

**Root cause of the `Шиднева` (Ш) non-resolution (source transliteration coverage, not a binding defect):**
the owner's new `_resolve_identity_in_task_context` intersects source-resolver candidates
with the sprint's canonical assignees, and the source resolver is the transliteration
authority. Probed via `GET /api/v1/swtr-read/assignees/resolve`:

| reference | resolver result |
|---|---|
| `Шалдунова` (Cyrillic) | **200 → `Shaldunov.A.V`** (resolves) |
| `Sidneva` (Latin) | **200 → `Sidneva.Y.S`** (resolves) |
| `Сиднева` (correct Cyrillic transliteration) | **200 → `Sidneva.Y.S`** |
| `Шиднева` / `Шидневой` (Ш) | **409, `matches: []`** (no AS21 user matches this spelling) |

`Sidneva` is canonically transliterated **`Сиднева` (with С)**, not `Шиднева` (with Ш).
The AS21 user index does not contain a `Шиднева` spelling, so the source resolver correctly
returns empty → the agent fails closed (no fabrication). **When the reference uses the
source's own transliteration, the contextual fix works end-to-end:** agent query
`Открытые задачи Сидневой в спринте OLP-SPRNT-5` → **2/2 COMPLETED, exact `OLP-3179`**.

So:
- **The owner's contextual-identity fix is PROVEN working** for correctly-transliterated
  sprint-only people (Shaldunov 10/10; correct-`Сиднева` 1/1).
- The specific `Шиднева` (Ш) query is a **source-name transliteration-coverage gap**: that
  non-standard spelling is absent from the AS21 user index, so no source identity "matching
  the natural reference" exists to resolve. This is a source-availability limitation,
  terminally fail-closed (not a binding/context defect and not fabrication).

Phase 3: mechanism **GREEN**; the single failing query is classified as a source
transliteration-coverage edge case (fail-closed), carried to the source-capability matrix.

---

## 5. Phase 4 — Focused cross-skill closure → GREEN

`qa_179_p4_results.json`.

| Scenario | Result |
|---|---|
| `Покажи DMS-380` — trusted observation | **canonical identity present:** `assignee_login=semavin.m.m`, `assignee_id=Semavin.M.M` |
| `Покажи DMS-380 и затем задачи его исполнителя` | see Phase 1 (binding chain — RED) |
| `Какой текущий спринт в DMS?` ×5 | **5/5 user-visible `DMS-SPRNT-1`**, exact canonical id, **no duplicated `SPRNT`** (178 cosmetic glitch did not reproduce) |
| `Покажи здоровье спринта OLP-SPRNT-5` | **COMPLETED**, 67 total / 66 done |
| `Проверь качество постановки DMS-380` | **COMPLETED**, 85/100 (good) |

- `semantic_prepass_used=false` on all runs; progressive skill loading visible.
- Release health: retained Assignment 178 source-limited classification (live release-task
  linkage unavailable; fail-closed, not fabrication) — carried to the 54-skill source-
  capability matrix.

---

## 6. Phase 5 — Mini generalized POC decision gate → NOT GREEN

| GREEN requirement | Result |
|---|---|
| task lookup → canonical assignee → full task search works **5/5 exact** | **FAIL** — 2/5 (19% aggregate); planner `invalid_json_decision` V4ContractError |
| Garanin/Moiseev critical search GREEN | PASS (retained 178 + Phase 2 `Гаранина` 33/33 recheck) |
| PVM-Guru benchmark GREEN | PASS (retained 178) |
| current sprint exact source-backed (user-visible) | **PASS** — 5/5 `DMS-SPRNT-1`, no doubled `SPRNT` |
| contextual sprint-only identity works when source context unique | **PARTIAL** — Shaldunov 10/10 & correct-`Сиднева` 1/1 work; `Шиднева`(Ш) is a source transliteration gap (fail-closed) |
| false-positive unrelated surname safety defect closed | **PASS** — `Гарановых` no longer maps to Garanin |
| progressive skill loading visible | PASS |
| semantic pre-pass absent | PASS (`semantic_prepass_used=false` throughout) |
| no entity-specific hardcodes | PASS |
| no local task DB/sync accepted as truth | PASS (REAL AS21 / swtr-read / MCP-SWTR only) |

The **first failing generalized production boundary** is the multi-step
`task.lookup → assignee → task.search` chain (Phase 1), where a `V4ContractError`
(`planner failed bounded repair: invalid_json_decision`) prevents 5/5 exact completion.

### Decision
The owner's three fixes are **individually proven correct** — canonical lookup binding
(306/306 when the planner cooperates), morphology tightening (`Гарановых` false-positive
closed, inflections preserved), and contextual sprint identity (Shaldunov 10/10).
The **overall Agent Core v4 API POC architecture gate is NOT GREEN** because the
headline multi-step binding chain does not reach 5/5 — the blocking defect is
**Qwen3.8 planner JSON-reliability** at the 2nd step, surfacing as a `V4ContractError`
at the binding boundary.

**Verdict: `V4_CAPABILITY_BINDING_RED`** (per the Phase 1 rule for a `V4ContractError`
at this boundary). Precise root cause and smallest owner fix are in §2.4.

---

## 7. Recommended owner next steps (QA recommendations, not implemented)
1. **Planner decision reliability (blocking for the binding chain):** harden
   `SkillNativePlannerV4.decide()` 2nd-step output for the multi-step
   `tasks.lookup_then_assignee` trajectory — constrained/structured JSON decoding against
   the `V4Decision` schema, a trimmed planner observation view after `task.lookup`, more
   repair attempts, or a deterministic fallback for the known lookup→assignee→search
   pattern. (This is the true blocker; the binding contract itself is proven working.)
2. **Source-name transliteration coverage (non-blocking, source matrix):** `Шиднева`(Ш) is
   not in the AS21 user index (`Сиднева`/`Sidneva` are). Carry to the 54-skill
   source-capability matrix; no code fix is a QWERTY/phonetic transliteration of a
   non-source spelling.
3. **Release health (source matrix):** live release-task linkage still unavailable
   (fail-closed, no fabrication) — retain source-capability-unavailable classification.

---

## Appendix — artifacts (working directory, not committed)
- `qa_179_p0_static.py` (static proof), `qa_179_d380_adapter.py`, `qa_179_p1_semavin_tasks.py`,
  `qa_179_p1_runner.py` (5x), `qa_179_p1_batch.py` (N=8), `qa_179_p1_errcap.py`
- `qa_179_p2_results.json` (safety), `qa_179_p3_oracle.json`, `qa_179_p3_results.json`,
  `qa_179_p3_resolve.py`, `qa_179_p3_sidneva_correct.py`
- `qa_179_p4_results.json` (cross-skill closure)
- Oracle B: DMS-380 → `Semavin.M.M` (306 tasks), OLP-SPRNT-5 (67 tasks, `Sidneva.Y.S` open
  `OLP-3179`, `Shaldunov.A.V` 10), Garanin.R.V (33 tasks)

**STOP** — report only. No production/test/code changes made; only this report committed.