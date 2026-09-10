# Assignment 171 — H1B Identity Recovery Certification

**Date:** 2026-09-10
**HEAD:** `634ee0bff2ff57ae7574f0ccc2f864d66c99693b`
**Owner commits verified as ancestors:**
- `429cf51316c03b7ebd913249b56fcb4bcd203e7b` — source-backed identity recovery no longer depends on a non-empty semantic intent
- `9f3a7a30b61607249c8b68e57d7b863a7251c282` — regression tests for unique recovery / ambiguity fail-closed / no-overwrite
**Query under test:** `Задачи Гаранина` (Phase 2 primary gate)
**Model:** Qwen3.8-27B via `https://api.ai.sbt/openai/v1`
**Source:** REAL AS21 via MCP-SWTR (Task API `:8003`)
**Oracle B:** `garanin.r.v` → 24 tasks (7 DMS + 12 OLP + 5 STS)
**QA role:** tester only — no production/backend/frontend/test code modified

---

## Verdict

**`H1B_IDENTITY_RECOVERY_RED`**

The owner's identity-recovery fix is **correct in isolation but non-functional in the
production task-api path**. The Phase 2 primary gate (10× `Задачи Гаранина` → 10/10) is
**RED: 4/10**. Every one of the 6 failures is an `llm_used=False` run — precisely the case
the fix was designed to rescue. STOP issued per the assignment rule: *"Any identity omission
failure => STOP `H1B_IDENTITY_RECOVERY_RED`."*

Phases 3–7 were **not** run because the primary gate failed deterministically.

---

## Why this is a deterministic defect, not an environment flake

The source is healthy. The assignee-routed read returns full data:

```
GET /api/v1/swtr-read/assignee-tasks?assignee=garanin.r.v&limit=100&max_pages=100
  -> HTTP 200, count=23 tasks
```

But the bulk all-tasks scan that the fix's identity source depends on is empty:

```
GET /api/v1/tasks?limit=100&offset=0
  -> HTTP 200, [] (len 0)
```

This is a stable property of the current Task API surface (only the swtr-read assignee/sprint/
release/single-task routes are populated; the legacy `/api/v1/tasks` bulk scan returns nothing).
It is **not** a transient source outage: the same Task API serves 23 live tasks on the
assignee route in the identical request window.

---

## Phase 0 — preflight (PASS)

- `git pull --ff-only` → up to date at `634ee0b`; both owner commits are ancestors (`git merge-base --is-ancestor` YES/YES).
- PO Agent `:8004` `/health`: `status=healthy v3=True source=healthy semantic=qwen-llm`.
- Static proof from loaded production code (`production_entity_grounding_v2.py:140`
  `_infer_missing_person_from_query`):
  - does NOT read `frame.intent_hint` — recovery may run on an empty semantic frame; ✅
  - mutates only `slots["person_raw"]` — never intent/capability routing; ✅
  - matches against `context["assignee_identities"]` built from `semantic_context()`; ✅ (no hardcoded names)
  - assigns only when exactly one unique `(display_name, login, external_id)` matches; ✅
  - returns immediately if `member_login`/`person_raw`/any alias is already set (no overwrite); ✅
- **Static no-hardcoded-names check** across `production_entity_grounding_v2.py`,
  `agent_core_v3_h1b.py`, `agent_core_v3_pilot.py`: `NO HARDCODED NAMES FOUND`. ✅

## Phase 1 — unit/build safety gate (PASS, but see defect)

- H1/H1B unit suites incl. `test_production_entity_grounding_recovery.py`: **33 passed**.
- Frontend `tsc --noEmit`: **clean**.

**Critical caveat:** `test_production_entity_grounding_recovery.py::_resolver_with_identities`
builds the resolver with `object.__new__(ProductionEntityResolverV2)` and **mocks
`semantic_context`** to return a canned `assignee_identities` list. The 3 recovery tests
therefore never exercise the real production `semantic_context()` → `search_tasks("")` →
`GET /api/v1/tasks` path. Green unit tests are **not** evidence the production identity source
is populated (it is not — see below).

---

## Phase 2 — primary identity recovery gate: **4/10 (RED)**

Fresh Oracle B first: `garanin.r.v` = 24 tasks. Ten fresh-session requests, concurrency=1,
fresh restart of PO Agent after clearing `src/**/__pycache__` (to guarantee the new code is
loaded). Timeout 600s.

| Run | ms | llm_used | intent | person_raw | member_login | assignee sent | status | keys | parity | result |
|-----|---------|----------|--------|------------|--------------|---------------|---------|------|--------|--------|
| 1 | 59,522 | **True** | task_search_assignee | Гаранина | Garanin.R.V | Garanin.R.V | COMPLETED | 24/24 | ✅ | PASS |
| 2 | 61,440 | **True** | task_search_assignee | Гаранина | Garanin.R.V | Garanin.R.V | COMPLETED | 24/24 | ✅ | PASS |
| 3 | 30,613 | **False** | *(empty)* | *(empty)* | *(empty)* | — | FAILED | 0/24 | ✗ | **UNRESOLVED_CONSTRAINT** |
| 4 | 37,683 | **False** | *(empty)* | *(empty)* | *(empty)* | — | FAILED | 0/24 | ✗ | **UNRESOLVED_CONSTRAINT** |
| 5 | 36,557 | **False** | *(empty)* | *(empty)* | *(empty)* | — | FAILED | 0/24 | ✗ | **UNRESOLVED_CONSTRAINT** |
| 6 | 39,423 | **False** | *(empty)* | *(empty)* | *(empty)* | — | FAILED | 0/24 | ✗ | **UNRESOLVED_CONSTRAINT** |
| 7 | 77,828 | **True** | task_search_assignee | Гаранина | Garanin.R.V | Garanin.R.V | COMPLETED | 24/24 | ✅ | PASS |
| 8 | 75,035 | **True** | task_search_assignee | Гаранина | Garanin.R.V | Garanin.R.V | COMPLETED | 24/24 | ✅ | PASS |
| 9 | 30,562 | **False** | *(empty)* | *(empty)* | *(empty)* | — | FAILED | 0/24 | ✗ | **UNRESOLVED_CONSTRAINT** |
| 10 | 28,212 | **False** | *(empty)* | *(empty)* | *(empty)* | — | FAILED | 0/24 | ✗ | **UNRESOLVED_CONSTRAINT** |

**Score: 4/10 PASS.** 100% of the 4 passing runs have `llm_used=True`; 100% of the 6 failing
runs have `llm_used=False` and `failure_code=UNRESOLVED_CONSTRAINT` with
`details={"value": "Garanin.R.V"}`.

The two mechanisms behave exactly as diagnosed:
- **`llm_used=True`:** the LLM prepass emits `person_raw=Гаранина`; `_ground_person_login`
  resolves it via the **team directory** (`self.team.resolve_person`) → `member_login=Garanin.R.V`
  → exact 24/24 Oracle parity. ✅
- **`llm_used=False`:** prepass emits an empty frame; the new recovery
  `_infer_missing_person_from_query` is invoked but finds **zero** candidate identities, so no
  `person_raw` is bound; the H1B planner then proposes a source-unsafe literal and the loop
  fail-closes with `UNRESOLVED_CONSTRAINT`. ❌ (recovery did not fire)

This is the **same 80% failure signature** observed in Assignment 170 (8/10), now reproduced
again after the owner fix was merged — proving the fix did not close the blocker.

---

## Root cause (deterministic, reproduced three ways)

The recovery matches only against `context["assignee_identities"]`. That field is populated by
`ProductionEntityResolverV2.semantic_context()` (`production_entity_grounding_v2.py:46`):

```python
tasks = await self.adapter.search_tasks("", max_results=getattr(self.adapter, "_scan_limit", 10000))
...
context["assignee_identities"] = identities   # built from `tasks`
```

For a **non-assignee** JQL, `ProductionTaskApiAS21Adapter.search_tasks`
(`production_task_api.py`) falls through to the parent `TaskApiAS21Adapter.search_tasks`,
which calls `_fetch_tasks` → `GET /api/v1/tasks`. In this production Task API that endpoint
returns an **empty array**, so the scan yields 0 tasks → `assignee_identities = []` → recovery
finds 0 matches → no `person_raw` → fail-closed.

Reproduced three independent ways against the live source (same request window as the Phase 2
gate):

1. **Direct grounder** (real `EvidenceValidatedProductionTaskApiAS21Adapter` +
   `ProductionEntityResolverV2`, empty frame, query `Задачи Гаранина`):
   `assignee_identities count: 0` → `_infer_missing_person_from_query` no-op →
   `_ground_person_login` no-op → `slots={}`.
2. **Adapter scan:** `search_tasks("", 50)→0`, `search_tasks("", 10000)→0`,
   `search_tasks("space = DMS", 50)→0`; assignee route → 23 (healthy).
3. **Raw HTTP:** `GET /api/v1/tasks?limit=100 → []` (len 0) vs
   `GET /api/v1/swtr-read/assignee-tasks?assignee=garanin.r.v → 23`.

**Conclusion:** the owner fix chose a **non-functional production identity source**. The
recovery logic itself is sound (and its unit test passes), but its input
`assignee_identities` is always empty in the task-api deployment, so the recovery never
binds a person.

---

## Recommendation to owner (QA does not implement)

`_infer_missing_person_from_query` / `semantic_context` must source candidate identities from
a **populated** store rather than the empty bulk `search_tasks("")` scan. Viable options:

1. Seed `assignee_identities` from the **team directory / config**
   (`TeamDirectory` / `self.team`), which is already populated and is exactly what the working
   LLM path uses via `self.team.resolve_person`. This keeps the "source/config-backed, unique
   only, no hardcoding" contract.
2. Or build the identity pool by fanning out the **live per-assignee route**
   (`/api/v1/swtr-read/assignee-tasks`) over known assignee logins, which is proven to return data.
3. Add a **non-mocked** integration regression that asserts `semantic_context()` yields a
   non-empty `assignee_identities` in task-api mode, so the unit suite catches this class of
   defect before merge.

No change to production code, prompts, model config, `.env`, or tests was made by QA.

---

## Gates not reached (STOP)

- Phase 3 (5× Семавин + 5× Калачанов → 10/10): **skipped** — same empty `assignee_identities`
  source guarantees identical `llm_used=False` fail-closed behavior for any entity-omitted run.
- Phase 4 (ambiguity / negative safety), Phase 5 (protected H1B regression), Phase 6 (Browser C
  H0 5/5), Phase 7 (Browser C real multi-step): **skipped** per STOP rule.

## Artifacts

- `qa_171_phase2.json` — per-run Phase 2 evidence (llm_used, intent, person_raw, member_login,
  assignee sent, keys, parity, status) for the 10 fresh-session runs.
- Oracle B window: `garanin.r.v` = 24 task keys (see `qa_171_phase2.json`).

**Final verdict: `H1B_IDENTITY_RECOVERY_RED`.** STOP.