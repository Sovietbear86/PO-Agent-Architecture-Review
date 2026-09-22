# A205 — Agent Core V4: Existing Catalog Adversarial Zero-RED Regate

**Verdict: `AGENT_CORE_V4_EXISTING_CATALOG_ADVERSARIAL_RED`**

- **Branch:** `feat/core8-real-query-hardening-v2`
- **START_HEAD:** `bd6a97305775864696f8b96e6945e3bcceb107cb`
- **Previous checkpoint:** A204 START `5b42e59` / report `c741081` (RED, D-A204-1…4)
- **Date:** 2026-09-22
- **QA mode:** adversarial black-box + static audit + service operation. No production/frontend/plugin/test/config changes. No new skills. No Wave S.

---

## 1. Verdict summary

**A single production-breaking defect blocks the entire V4 surface.** At START_HEAD `bd6a973`, **100% of V4 queries fail** in ~0.03–0.1s with:

```
TypeError: RobustSkillNativePlannerV4.next_decision() got an unexpected keyword argument 'session_context'
```

returned as typed `FAILED` / `v4_runtime_failure` («Agent Core v4 не смог безопасно завершить траекторию.»). The owner's session_context remediation bundle (D-A204-3 fix) updated the base planner signature and the `process()` call site but **did not update the robust planner override used by the production runtime**. The owner's own suite ships with **7 failing tests** (all the same TypeError). Live proof: **41/41** sweep runs (all 27 skills + 14 adversarial cases) FAILED with the identical signature; 0 LLM calls, 0 source calls, 0 local-store reads.

Per the assignment rule («Any RED: STOP… Return root cause for owner remediation and another full re-gate»), Phases 2–11 live gates are **BLOCKED** (no query can execute); the mandated 27-skill matrix and adversarial pack were run and are uniformly RED (Section 6).

---

## 2. Phase 0 — architecture audit (diff `5b42e59..bd6a973`)

Static audit (no code edits). All 10 invariants **PASS at the source level**:

| Invariant | Verdict | Evidence |
|---|---|---|
| no-new-skill | PASS | identical skill-id sets in `v4_plugins/core.py` + `task_catalog.py` (27 total); zero new `SkillSpecV4` entries |
| no-hardcoding | PASS | no person/sprint/release literals or query-specific branches in production diff (only test fixtures) |
| session-context-generic-hidden-bounded | PASS | `SessionEntityContext` (api/v1/__init__.py:44), ≤4 keys (fixed role set `space/sprint_id/release_id/assignee` via `validated_session_context`), TTL 15 min, session-keyed; `v4_state.pop("session_context", None)` at response build (api/v1/__init__.py:262) |
| context-does-not-satisfy-contract | PASS | `completion_frontier_satisfied` receives observations only (agent_core_v4.py:608–613); context never passed |
| multi-hop-pinned | PASS | `PendingClarification` carries `original_query` + `resume_loaded_skills` + `resume_observations` + `required_completion_skills` through each hop; re-stored on every NEEDS_CLARIFICATION |
| discovery-identity-only-helper | PASS | `sprints.discover` now `completion=()` with explicit "identity-only helper" procedure text |
| release-live-filter-no-local | PASS | `swtr_query.py` pushes `fix_version_s = "<release>"` TQL clause; `release.resolve` rejects `APPROVED_PRODUCT_SPACES` as release ids; no local-store path in release flow |
| unassigned-typed | PASS | schema-level `unassigned` param on `task.search`, safe-enum, requires bounded `space`, null-assignee filter in handler |
| plugin-intact | PASS | no registry/BINDINGS changes |
| semantic_prepass-false | PASS | all V4 response paths emit `semantic_prepass_used: False` |

**The remediation design is sound. The implementation has one signature-migration defect (Section 3).**

## 3. Root cause — D-A205-1 (production-breaking, deterministic)

`process()` (agent_core_v4.py:1156–1160) now **unconditionally** passes the new context:

```python
decision = await self.planner.next_decision(
    user_query=query,
    catalog=self.catalog,
    loaded_skills=tuple(loaded),
    observations=observations,
    session_context=request.session_context,   # ← unconditional
)
```

- Base planner **has** the parameter: `agent_core_v4.py:324–330` — `async def next_decision(self, *, user_query, catalog, loaded_skills, observations, session_context: Mapping[str, str] | None = None)` ✓ (and includes it in the LLM payload, line 335).
- **The override does not:** `agent_core_v4_robust.py:149–154` —
  ```python
  async def next_decision(
      self, *, user_query, catalog, loaded_skills, observations,
  ) -> V4Decision:
  ```
  No `session_context`, no `**kwargs` → `TypeError` at every call.

**Production wiring uses exactly this override** (verified chain):
`runtime_factory.py:83` → `PluginizedRobustReliableAgentCoreV4Runtime` (agent_core_v4_pluginized.py:17) → `RobustReliableAgentCoreV4Runtime` (agent_core_v4_robust.py:218) → `self.planner = RobustSkillNativePlannerV4(...)` (robust.py:226–230).

### D-A205-1b — secondary (latent) defect in the same override
Even after the TypeError is fixed, `RobustSkillNativePlannerV4.next_decision` builds its LLM payload **without** `session_context` (robust.py:155–161: only `user_query / compact_skill_catalog / loaded_skills / observations / step_budget_remaining`). The model would therefore never see prior resolved entities — same-session «этом спринте» (Phase 3) could not work through the production planner. The literal-guard whitelist (agent_core_v4_reliable.py:406–410) would only help if the model already knew the id. **Both must be migrated together** (signature + payload), mirroring the base planner.

### Why CI was green at ship time
The owner's **new** session-context tests pass (they exercise `validated_session_context` and runtimes where the base planner is used). The **7 pre-existing** tests in `tests/test_agent_core_v4_completion_contract.py` that build `RobustReliableAgentCoreV4Runtime` via `_robust_runtime()` fail — the owner shipped with them red:

```
FAILED test_agent_core_v4_completion_contract.py::test_runtime_completes_lookup_then_assignee_without_model_ready
FAILED test_agent_core_v4_completion_contract.py::test_runtime_completion_cannot_fabricate_without_observations
FAILED test_agent_core_v4_completion_contract.py::test_premature_model_ready_is_rejected_until_contract_is_satisfied
FAILED test_agent_core_v4_completion_contract.py::test_zero_row_search_is_a_legitimate_source_completion
FAILED test_agent_core_v4_completion_contract.py::test_person_collection_completes_at_search_with_exact_keys
FAILED test_agent_core_v4_completion_contract.py::test_missing_resolved_constraint_is_injected_before_terminal_call
FAILED test_agent_core_v4_completion_contract.py::test_runtime_contract_completion_marker_and_prepass_flag
```
(each: `FAILED` + `data._agent_core_v4.error = "...next_decision() got an unexpected keyword argument 'session_context'"`)

### Owner fix (proposed, not implemented)
In `agent_core_v4_robust.py`, change `RobustSkillNativePlannerV4.next_decision` to accept `session_context: Mapping[str, str] | None = None` **and** include `"session_context": dict(session_context or {})` in the payload (mirroring `agent_core_v4.py:324–336`). Then `pytest tests/test_agent_core_v4*.py` must be 100% green before any re-gate.

## 4. Phase 1 — automated suites at START_HEAD

| Suite | Result |
|---|---|
| `pytest tests/test_agent_core_v4*.py` (po-agent) | **7 failed, 89 passed** — all 7 = D-A205-1 TypeError |
| `pytest tests/test_v4*.py` (po-agent; incl. new `test_v4_browser_api_contract.py`, owner-fix contracts, plugin registry) | **32/32 passed** |
| `pytest tests/test_swtr_read_facade.py tests/test_swtr_read_sprint_collection.py tests/test_swtr_task_query_release.py` (task-api) | **27/27 passed** |

Named proofs (all present and passing at unit level): guard→`sprints.list` + «список задач в этом спринте»=False (`test_agent_core_v4_sprint_discovery.py`); session-context internal/same-session + ambiguous-drop (`test_v4_browser_api_contract.py`, `test_agent_core_v4_completion_contract.py`); multi-hop original-goal preservation (`test_v4_browser_api_contract.py::test_multi_hop_clarification_preserves_original_goal`); unassigned bounded filter + space≠release + explicit-release live adapter (`test_v4_owner_fix_contracts.py`); history flat/nested schema (`task-api test_swtr_read_facade.py`); sprint rows `membership_proven` (`task-api test_swtr_read_sprint_collection.py`); release TQL push (`task-api test_swtr_task_query_release.py`); plugin/dummy-55 (pre-existing plugin tests, green in the 32).

**Unit-level design proofs are green; the production runtime they target is broken** — the robust planner override is the one component the named proofs don't exercise.

## 5. Services at START_HEAD

Restarted for A205: task-api 8241 (PID 30041, `swtr-read/health` connected, sse, 48 tools), agent 8212 (PID 24154, `PO_AGENT_EXPECTED_HEAD=bd6a973…`, `/live` 200), MCP-SWTR 3000 (PID 29268, fresh SSE session — prior instance was dead-state: MCP message endpoints 404 after ~20h), UI 5175 (PID 55236, unchanged, `http://localhost:5175/`).

Probe query «Текущий спринт в DMS» → `FAILED` 0.1s, `error = "RobustSkillNativePlannerV4.next_decision() got an unexpected keyword argument 'session_context'"`.

## 6. Phases 2–11 live gates — BLOCKED; uniform 27/27 + adversarial sweep

Because every query fails at the planner boundary before any LLM/source call, the mandated full matrix was executed as a **uniform sweep** (concurrency 1, fresh sessions): **27/27 skills + 14/14 adversarial = 41/41 FAILED**, identical signature, 0.0–0.04s each.

### 27-skill matrix (all rows: FAILED, `loaded=[]`, 0 evidence, same TypeError)

| # | skill | NL request | Result |
|---|---|---|---|
| 1 | tasks.search | Открытые задачи в DMS | RED (D-A205-1) |
| 2 | sprints.discover | Какой спринт в DMS идёт в сентябре | RED (D-A205-1) |
| 3 | sprints.list | Активные спринты в DMS | RED (D-A205-1) |
| 4 | sprint.current | Текущий спринт в DMS | RED (D-A205-1) |
| 5 | task.lookup | Покажи задачу DMS-380 | RED (D-A205-1) |
| 6 | task.summary | Опиши задачу DMS-380 | RED (D-A205-1) |
| 7 | task.quality | Оцени качество задачи DMS-380 | RED (D-A205-1) |
| 8 | task.acceptance | Оцени критерии приёмки задачи DMS-380 | RED (D-A205-1) |
| 9 | task.blockers | Покажи блокеры задачи DMS-380 | RED (D-A205-1) |
| 10 | sprint.health | здоровье сентябрьского спринта по DMS | RED (D-A205-1) |
| 11 | release.health | здоровье релиза по DMS | RED (D-A205-1) |
| 12 | task.search_text | Найди задачи про аутентификацию в DMS | RED (D-A205-1) |
| 13 | task.search_attachments | Задачи с вложениями в WMB | RED (D-A205-1) |
| 14 | task.search_excel | Задачи с Excel вложениями у Уткина в WMB | RED (D-A205-1) |
| 15 | task.search_pdf | Задачи с PDF вложениями в WMB | RED (D-A205-1) |
| 16 | task.search_msg | Задачи с MSG вложениями в WMB | RED (D-A205-1) |
| 17 | task.search_assignee | Задачи Гаранина в DMS | RED (D-A205-1) |
| 18 | task.search_status | Открытые задачи в DMS | RED (D-A205-1) |
| 19 | task.search_sprint | Покажи список задач в DMS-SPRNT-3 и их статусы | RED (D-A205-1) |
| 20 | task.search_release | Задачи в релизе по DMS | RED (D-A205-1) |
| 21 | task.search_product | Покажи задачи по DMS | RED (D-A205-1) |
| 22 | task.missing_requirements | Чего не хватает в задаче DMS-380 | RED (D-A205-1) |
| 23 | task.dependencies | Покажи зависимости задачи DMS-380 | RED (D-A205-1) |
| 24 | task.history | покажи историю статусов задачи DMS-380 | RED (D-A205-1) |
| 25 | task.time_in_status | сколько времени задача DMS-399 провела в каждом статусе | RED (D-A205-1) |
| 26 | task.aging | Старые открытые задачи в DMS старше 30 дней | RED (D-A205-1) |
| 27 | task.similar | Найди похожие задачи на DMS-380 | RED (D-A205-1) |

### Adversarial pack (14 cases, all FAILED, same signature)

| Case | Query | Result |
|---|---|---|
| sprint health | здоровье сентябрьского спринта по DMS | RED (D-A205-1) |
| same-session pair t1/t2 | здоровье… / Покажи список задач в этом спринте и их статусы | RED (D-A205-1) ×2 |
| OLP multi-hop | покажи активные задачи у Гаранина в сентябрьском спринте по OLAP | RED (D-A205-1) |
| unassigned ×2 | найди задачи без исполнителя в OLP / в текущем спринте OLP | RED (D-A205-1) ×2 |
| workload | кто больше всех загружен в сентябрьском спринте по DMS? | RED (D-A205-1) |
| release ×2 | здоровье релиза по DMS / задачи в релизе по DMS | RED (D-A205-1) ×2 |
| history / time-in-status / capability | DMS-380 / DMS-399 / «Ты умеешь определять длительность задач?» | RED (D-A205-1) ×3 |
| explicit sprint | Покажи список задач в DMS-SPRNT-3 и их статусы | RED (D-A205-1) |
| safe negative | Покажи задачи DMS-999999 | RED (D-A205-1) |

A204 defects D-A204-1…4 are **not re-verifiable** — every trajectory dies before skill loading. No false success, no fabrication, no local-truth read occurred (fail-closed everywhere, but at the wrong boundary).

## 7. Phases 12–13 (audits)

- **Local store:** 0 `GET /api/v1/tasks` reads (agent log audit). **Source:** 1 `swtr-read/health` only. **LLM:** 0 calls. Zero fabrication possible at this boundary.
- **dummy-55/plugin:** unit-level green (within 32); live extension gate BLOCKED by D-A205-1 (no V4 query can run).

## 8. Defect summary

| ID | Severity | Description | Determinism |
|---|---|---|---|
| **D-A205-1** | **RED (blocking, total)** | `RobustSkillNativePlannerV4.next_decision` (agent_core_v4_robust.py:149–154) lacks the new `session_context` parameter that `process()` (agent_core_v4.py:1159) passes unconditionally → `TypeError` → 100% of V4 queries FAILED. Production runtime chain verified (runtime_factory.py:83). 7 owner tests ship red. | 48/48 (41 live + 7 unit) |
| **D-A205-1b** | RED (latent, same file) | Robust planner payload (robust.py:155–161) omits `session_context` even after signature fix → same-session referent resolution (Phase 3) unreachable through the production planner; model never sees validated prior entities. | static |

## 9. Owner remediation + re-gate plan

1. Migrate `RobustSkillNativePlannerV4.next_decision`: add `session_context: Mapping[str, str] | None = None` and include `"session_context": dict(session_context or {})` in the payload (mirror base `agent_core_v4.py:324–336`).
2. `pytest tests/test_agent_core_v4*.py` → 100% green (the 7 red tests are the exact regression net for this class).
3. Full A205 re-gate: Phases 2–11 as specified (fresh oracle per batch), including the 10× sprint health, 10 same-session pairs, 5 OLP multi-hop chains, unassigned, workload, release, history, N+1 audit, 27-skill matrix, Browser C, local-store audit, dummy-55.
4. Do not add skills / start Wave S until GREEN.

## 10. Services left running

| Service | Port | PID | Health |
|---|---|---|---|
| UI (vite, ::1) | 5175 | 55236 | 200 (`http://localhost:5175/`) |
| agent (bd6a973) | 8212 | 24154 | `/live` 200; all V4 queries FAILED (D-A205-1) |
| task-api (system py3, SSE) | 8241 | 30041 | `swtr-read/health` connected, 48 tools |
| MCP-SWTR (fresh) | 3000 | 29268 | SSE OPEN |

**QA artifacts (untracked, root):** `qa_205_restart_services.sh`, `qa_205_restart_taskapi.sh`, `qa_205_restart_mcp.sh`, `qa_205_mcp_probe.py`, `qa_205_sweep.py`; `/tmp/qa205_*.jsonl|log` (sweep results, service logs).

**STOP after this report — no Wave S, no new skills, awaiting owner fix + full re-gate.**
