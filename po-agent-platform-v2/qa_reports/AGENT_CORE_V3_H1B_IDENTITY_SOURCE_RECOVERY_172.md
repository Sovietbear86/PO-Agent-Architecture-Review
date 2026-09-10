# Assignment 172 — H1B Identity Source Recovery Retest

**Verdict: `H1B_IDENTITY_SOURCE_RECOVERY_RED`** (Phase 2 stopping gate: 3/10)

**Date:** 2026-09-10
**HEAD:** `e59efe3f7bdf784da6adf1b08c3dece499bcbd2c`
**Owner commits under test (ancestors verified via `git merge-base --is-ancestor`):**
- `3e26bace1f578e62683749708628aa40ccf35b53` — fix(h1b): seed recovery identities from team directory
- `c4f2d57381672284da90bdd50b9abf27af3d8e90` — test(h1b): cover empty bulk identity source recovery

**Role:** QA/tester only. No production/backend/frontend/test code, prompts, config, or AS21/SWTR data modified by QA. Report-only commit.

---

## Executive summary

The 171 blocker (empty `assignee_identities` pool from the bulk `/api/v1/tasks` scan) is **fixed at the grounding layer**: identity candidates are now seeded from the configured TeamDirectory, and full `ground()` on an empty (`llm_used=False`) semantic frame binds `person_raw` + `member_login=Garanin.R.V` + `assignee=Garanin.R.V` with zero clarifications (proven offline against the live source and in the live H1B flow).

The Phase 2 gate is nevertheless **RED 3/10** because a **new, previously masked boundary** is now exposed: the H1B assignee-literal guard (`agent_core_v3_h1b.py:119–135`) rejects the typed planner's verbatim proposal of the **canonical login** `Garanin.R.V` when the user query is Russian (`Задачи Гаранина`). The guard accepts (a) a value equal to `person_raw` (Russian display name) and (b) login-like literals typed verbatim in the query — but not (c) a value equal to the grounded `member_login`/`assignee`, even though that value is the system's own source-safe canonical identity.

All 7 failures: `FAILED / UNRESOLVED_CONSTRAINT / details={"value": "Garanin.R.V"}` — i.e., the person was **fully resolved**; the rejection is the H1B guard, not semantic entity omission and not the identity source.

---

## Phase 0 — Preflight: PASS

| Check | Result |
|---|---|
| `git pull --ff-only origin feat/core8-real-query-hardening-v2` | `bc55e4f..e59efe3` fast-forward, clean |
| HEAD | `e59efe3f7bdf784da6adf1b08c3dece499bcbd2c` |
| Owner commit `3e26bac` ancestor | YES |
| Owner commit `c4f2d57` ancestor | YES |
| PO Agent restarted on new code | killed old uvicorn, removed 16 `__pycache__` dirs under `src/`, restarted via `qa_168_start_po_agent.sh` (fresh `PO_AGENT_EXPECTED_HEAD`) |
| Task API `:8003/health` | `{"status":"healthy"}` |
| MCP-SWTR `:8003/api/v1/swtr-read/health` | `{"status":"connected","transport":"sse","tool_count":48}` |
| PO Agent `:8004/health` | `status=healthy, adapter=task-api, semantic_mode=qwen-llm, agent_core_v3_enabled=true, source_status=healthy`, `source_facts` includes `team_competencies` (TeamDirectory wired) |
| Frontend `:5175` | 200, `id="root"` present |
| LLM endpoint | unchanged (Qwen 3.8, `https://api.ai.sbt/openai/v1`) |
| Concurrency / timeouts | 1 / 300s source, 600s e2e |

**Static proof of the fix (`production_entity_grounding_v2.py`):**
1. `semantic_context()` seeds `assignee_identities` from `context["team_members"]` (TeamDirectory `public_context()`, keys `login`/`full_name`) **before** enriching with live task rows; task-derived identities only enrich (`seen` set, no overwrite).
2. Live check against the real production resolver + adapter + TeamDirectory: `assignee_identities count: 16` (was **0** in Assignment 171 — the 171 blocker).
3. No hardcoded name literals in the file (`grep` for known surnames/logins: none). No capability/intent routing: recovery is entity annotation only; `intent_hint` is pass-through; docstring states "never intent/capability routing".
4. Unique-only binding preserved: recovery binds only when the query mentions exactly one identity (zero or >1 remain fail-closed); ambiguity unit test passes.

**Offline live-source proof of the recovery chain (real adapter + real TeamDirectory, empty frame = the 171 failure class):**

```
frame = SemanticFrame(slots={}, llm_used=False, canonical_query='{member_login}')
query = 'Задачи Гаранина'
grounded.slots = {'person_raw': 'Гаранин Родион Владимирович',
                  'member_login': 'Garanin.R.V',
                  'assignee': 'Garanin.R.V'}
clarifications = []
```

The exact 171 boundary (empty bulk scan + populated TeamDirectory → recovery binds one unique source/configured identity) now works end-to-end.

---

## Phase 1 — Unit/build gate: PASS

| Suite | Result |
|---|---|
| `test_production_entity_grounding_recovery.py` (4 tests, **incl. new non-mocked** `test_semantic_context_seeds_identity_from_team_directory_when_bulk_scan_is_empty`) | 4/4 PASS |
| `test_agent_core_v3_foundation.py` `test_agent_core_v3_h1b_grounding.py` `test_agent_core_v3_loop.py` `test_agent_core_v3_registry.py` `test_agent_core_v3_typed_planner.py` `test_harness_entity_grounding.py` `test_harness_recovery_runtime.py` `test_semantic_slot_recovery.py` | 58/58 PASS total |
| Frontend `tsc --noEmit` | exit 0 |

**New non-mocked test proof (requirement):** the new owner test constructs a real `ProductionEntityResolverV2` with `_EmptyBulkTaskAdapter` (bulk `search_tasks("")` → `[]`) and a populated `TeamDirectory` (Garanin + Semavin), calls the real `semantic_context()`, and asserts `assignee_identities == {Garanin.R.V, Semavin.M.M}` plus recovery binding of `person_raw`. It does not mock `semantic_context` — the exact 171 unit gap is closed.

---

## Phase 2 — Primary recovery gate: RED 3/10

Fresh **Oracle B** (direct REAL AS21 via MCP-SWTR assignee route — `/api/v1/swtr-read/assignee-tasks?assignee=garanin.r.v`, never `/api/v1/tasks`): **23 tasks**

```
DMS-243, DMS-248, DMS-262, DMS-326, DMS-328, DMS-36, DMS-93,
OLP-3037, OLP-3040, OLP-3145, OLP-3233, OLP-3244, OLP-3248, OLP-3250,
OLP-3252, OLP-3275, OLP-3281, OLP-3282,
STS-184686, STS-311024, STS-311026, STS-311033, STS-311034
```

Ten fresh sessions, query `Задачи Гаранина`, concurrency=1:

| # | status | ms | llm_used | member_login | assignee (loop constraint) | keys | parity | failure_code |
|---|--------|-----|----------|--------------|------------------------------|------|--------|--------------|
| 1 | COMPLETED | 17900 | True | Garanin.R.V | Garanin.R.V | 23/23 | exact | — |
| 2 | FAILED | 9039 | **False** | — (guard rejected pre-loop) | — (value=Garanin.R.V) | 0 | — | UNRESOLVED_CONSTRAINT |
| 3 | FAILED | 10646 | **False** | — | — (value=Garanin.R.V) | 0 | — | UNRESOLVED_CONSTRAINT |
| 4 | COMPLETED | 13972 | True | Garanin.R.V | Garanin.R.V | 23/23 | exact | — |
| 5 | FAILED | 16850 | **False** | — | — (value=Garanin.R.V) | 0 | — | UNRESOLVED_CONSTRAINT |
| 6 | FAILED | 6303 | **False** | — | — (value=Garanin.R.V) | 0 | — | UNRESOLVED_CONSTRAINT |
| 7 | COMPLETED | 11930 | True | Garanin.R.V | Garanin.R.V | 23/23 | exact | — |
| 8 | FAILED | 6853 | **False** | — | — (value=Garanin.R.V) | 0 | — | UNRESOLVED_CONSTRAINT |
| 9 | FAILED | 6760 | **False** | — | — (value=Garanin.R.V) | 0 | — | UNRESOLVED_CONSTRAINT |
| 10 | FAILED | 7370 | **False** | — | — (value=Garanin.R.V) | 0 | — | UNRESOLVED_CONSTRAINT |

- 3/10 PASS — all PASS runs `llm_used=True`, exact 23/23 key-set parity, canonical assignee `Garanin.R.V`, raw Cyrillic name never sent as an identifier.
- 7/10 FAIL — all `llm_used=False`, all `UNRESOLVED_CONSTRAINT` with `details={"value": "Garanin.R.V"}`.
- 22 additional ad-hoc probes (pre/post gate) show the same bimodal signature: COMPLETED runs all carry resolved assignee `Garanin.R.V`; FAILED runs all carry `details={"value": "Garanin.R.V"}`.

**Stopping rule applied: acceptance was 10/10. Result 3/10 ⇒ STOP `H1B_IDENTITY_SOURCE_RECOVERY_RED`. Phases 3–7 SKIPPED.**

---

## Root-cause forensics

### 1. The identity-source fix is working (171 boundary closed)

Evidence chain:
- Static: 16/16 TeamDirectory identities seeded into `assignee_identities` (171: 0).
- Offline live source: empty frame → `member_login=Garanin.R.V`, `assignee=Garanin.R.V`, no clarifications.
- Live: on every `llm_used=False` run the planner proposed `assignee="Garanin.R.V"`. At step 1 there are no observations and the Russian query does not contain that string — the **only** source of `Garanin.R.V` for the planner is `grounded_values`, which is populated because TeamDirectory seeding now binds `member_login`/`assignee` even when the semantic prepass is empty.

### 2. New exposed boundary: H1B assignee-literal guard asymmetry

`po-agent-platform-v2/src/po_agent/harness/agent_core_v3_h1b.py` (`_run_grounded_agent_loop`, lines 119–135):

```python
if field == "assignee":
    person_raw = str(grounded_values.get("person_raw") or "").strip()
    member_login = str(grounded_values.get("member_login") or "").strip()
    if member_login and person_raw and raw_text.casefold() == person_raw.casefold():
        resolved[field] = member_login          # (a) Russian display name → login
        continue
    if "." not in raw_text or raw_text.casefold() not in request.query.casefold():
        raise AgentCoreV3ContractError(UNRESOLVED_CONSTRAINT, ..., details={"value": raw_text})
        # (b) login-like literal must appear VERBATIM in the user query
```

Accepted today: `$ground.*` references (resolved before this branch), a value equal to `person_raw` (display name), and login-like literals typed verbatim in the query.
**Rejected:** a value equal to `grounded_values["member_login"]`/`assignee` — i.e., the planner copying the system's own canonical login — when the query is in Russian.

Concretely, for `raw_text="Garanin.R.V"`, `person_raw="Гаранин Родион Владимирович"`, query `Задачи Гаранина`:
- branch (a): `"garanin.r.v" != "гаранин родион владимирович"` → not taken;
- branch (b): `"." in raw_text` (True) but `"garanin.r.v" not in "задачи гаранина"` → **raise**.

The same asymmetry holds in the generic literal guard `_literal_is_source_safe` (`agent_core_v3_pilot.py:230–245`: non-task/space fields require `raw.casefold() in query.casefold()`), so even a fixed assignee branch would need the grounded-value exception to carry through.

### 3. Why the fix surfaced it

The typed planner receives `grounded_values` in its prompt (`agent_core_v3_typed_planner.py:39` — "Constraint values may only be literals present in user_query, $ground.<field> from grounded_values, or $obs.<step>.<path>" — and line 226 passes `grounded_values` through). Before the fix, on `llm_used=False` runs `grounded_values` had no `member_login`/`assignee`, so the planner could only echo the prepass `person_raw` or fail earlier (171). After the fix, the planner sees `member_login`/`assignee = "Garanin.R.V"` and non-deterministically (Qwen 3.8) either:
- uses the `$ground.assignee` reference → resolved before the literal guard → COMPLETED, or
- copies the login verbatim as a literal → rejected by the assignee guard → `UNRESOLVED_CONSTRAINT`.

The `llm_used=True` path still passes because the prepass `person_raw` ("Гаранина") matches branch (a) and resolves to the login — exactly the 171 behavior.

### 4. What this is (and is not)

- **Not** semantic entity omission: on every failed run the identity is fully grounded (the very value the planner proposed, `Garanin.R.V`, proves `grounded_values` was populated).
- **Not** an AS21/source outage: assignee route healthy, Oracle B fetched fresh, 23/23 parity on all COMPLETED runs.
- **Not** H1B loop loss: no loop-budget exhaustion; failure is pre-execution contract rejection at the constraint-resolution guard.
- **Is** the H1B guard rejecting a canonical, source-safe, system-grounded identity because its literal-acceptance rule only covers (a) display-name echo and (b) verbatim-in-query login.

---

## Owner recommendation (QA did not modify code)

In the `assignee` branch of `_run_grounded_agent_loop` (`agent_core_v3_h1b.py:119–135`), accept a planner-proposed value that equals the grounded login, symmetric to the existing `person_raw` branch, before the verbatim-in-query check:

```python
if member_login and raw_text.casefold() == member_login.casefold():
    resolved[field] = member_login
    continue
```

(and mirror the same grounded-value exception in `_literal_is_source_safe` for the assignee field, `agent_core_v3_pilot.py:230–245`, so the exception is coherent end-to-end). This remains fail-closed for any login that is not grounded (unknown logins still require verbatim-in-query), introduces no hardcoded names and no capability routing.

Companion regression test (non-mocked): drive `_run_grounded_agent_loop` with a planner stub returning `assignee=<grounded member_login verbatim>` while `user_query` is Russian and contains no login → expect COMPLETED with `resolved["assignee"] == member_login`.

Optional (insufficient alone, per Assignments 163/164 planner-reliability evidence): strengthen the typed-planner prompt to prefer `$ground.assignee`; prompt reliability does not replace the guard's grounded-value acceptance.

---

## Skipped phases (STOP rule — Phase 2 not 10/10)

- Phase 3 (Семавин/Калачанов cross-member), Phase 4 (identity safety), Phase 5 (protected H1B regression), Phase 6 (Browser C H0 5/5), Phase 7 (Browser C real multi-step): **SKIPPED** per the assignment stopping rule.

## QA artifacts

- `qa_172_phase23_results.json` — per-run Phase 2 evidence (latency, llm_used, recovery flag, member_login, assignee, keys, parity, failure codes) + Oracle B key sets.
- No production/test/config/`.env`/AS21-SWTR data modified; no runner modified.

**Verdict: `H1B_IDENTITY_SOURCE_RECOVERY_RED` — STOP.** The 171 identity-source boundary is fixed and proven; the gate is blocked by the H1B assignee-literal guard rejecting planner-verbatim canonical logins (root cause + minimal fix above).