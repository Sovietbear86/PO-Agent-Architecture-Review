# A205 (re-run) — Agent Core V4: Existing Catalog Adversarial Zero-RED Regate

**Verdict: `AGENT_CORE_V4_EXISTING_CATALOG_ADVERSARIAL_RED`**

- **Branch:** `feat/core8-real-query-hardening-v2`
- **START_HEAD:** `1dba9ad1b1e09b76e9321e7145e7169d31fd7669`
- **First-A205 baseline:** `bd6a973` / report `8fe856c` (RED — D-A205-1 robust planner `next_decision` missing `session_context`)
- **Date:** 2026-09-22
- **QA mode:** adversarial black-box + static audit + service operation. No production/frontend/plugin/test/config changes. No new skills. No Wave S.

---

## 1. Verdict summary

**The A205-1 planner-interface fix is verified working, but a sibling interface-migration defect one layer down — D-A205-2 — breaks 100% of trajectories that execute a governed capability call.** At START_HEAD `1dba9ad`, every V4 query that loads a skill and makes a capability call fails in ~13–45s with:

```
TypeError: PluginizedRobustReliableAgentCoreV4Runtime._validate_call_literals() takes 5 positional arguments but 6 were given
```

returned as typed `FAILED` / `v4_runtime_failure`. The owner's session_context remediation bundle added the `session_context` parameter to the **base** `AgentCoreV4Runtime._validate_call_literals` and the **reliable** override, and to the `process()` call site — but **not** to the **pluginized** override, which is the class the production runtime actually resolves to. Live proof: **37/41** sweep runs FAILED with this identical signature; **0** trajectories reached a completed capability. No LLM call reached source; **0 local-store reads, 0 swtr-read source calls** (the crash precedes any source I/O).

Per the hard-freeze rule, Phases 2–11 live gates are **BLOCKED** (no capability can execute); the mandated 27-skill matrix and 14-case adversarial pack were run and are uniformly RED (Section 5). This supersedes the first A205 report, which is not a valid 27-skill result (it died at the planner boundary).

---

## 2. Robust planner + session_context regression (checked separately first)

The specific A205-1 regression is **FIXED and proven**:

| Check | Result |
|---|---|
| `test_agent_core_v4_robust_protocol.py::test_robust_planner_accepts_and_forwards_generic_session_context` | **PASSED** (asserts `session_context` is in the LLM payload) |
| `pytest tests/test_agent_core_v4*.py` | **97 passed** (first A205: 7 failed / 89 passed — the 7 red `_robust_runtime` tests now green) |
| `pytest tests/test_v4*.py` | 32 passed |
| task-api `test_swtr_read_facade.py` + `test_swtr_read_sprint_collection.py` + `test_swtr_task_query_release.py` | 27 passed |

**Live confirmation the planner interface now works:** the smoke query «Текущий спринт в DMS» now loads `sprint.current` and issues a `space.resolve` capability decision (it got *past* the A205-1 `next_decision` TypeError and proceeded to the next boundary). So D-A205-1 is closed; the failure moved one layer down to `_validate_call_literals`.

## 3. Scope confirmation (no production changes beyond the interface fix)

`git diff --stat bd6a973..1dba9ad -- po-agent-platform-v2/src task-api/app` = **only** `agent_core_v4_robust.py` (3 insertions, 1 deletion). The full `5b42e59..1dba9ad` production delta is the A204 remediation bundle (already audited PASS on all 10 invariants in the first A205) plus the robust-planner interface parity. No new skill ids, no entity hardcoding, no new business branches — confirmed unchanged.

## 4. Root cause — D-A205-2 (production-breaking, deterministic)

`process()` (agent_core_v4.py:1237) **unconditionally** passes `session_context` as the 5th argument (6th positional) to every capability's literal validation:

```python
self._validate_call_literals(
    capability_id,
    raw_args,
    query,
    observations,
    request.session_context,      # ← 5th arg, always passed
)
```

Signature inventory:

| Class (MRO order) | `_validate_call_literals` | `session_context`? |
|---|---|---|
| `AgentCoreV4Runtime` (base, agent_core_v4.py:997) | `(self, capability_id, args, query, observations, session_context=None)` | **yes** |
| `ReliableAgentCoreV4Runtime` (reliable.py:396) | `(self, capability_id, args, query, observations, session_context=None)` | **yes** |
| **`PluginizedRobustReliableAgentCoreV4Runtime` (pluginized.py:38)** | `(self, capability_id, args, query, observations)` | **NO** ← 5 positional only |
| `RobustReliableAgentCoreV4Runtime` (robust.py) | not overridden (inherits) | — |

MRO (verified at runtime): `PluginizedRobustReliableAgentCoreV4Runtime → RobustReliableAgentCoreV4Runtime → ReliableAgentCoreV4Runtime → AgentCoreV4Runtime`. The **pluginized** override wins. Production runtime is exactly this class (`runtime_factory.py:83` → `PluginizedRobustReliableAgentCoreV4Runtime`).

→ `self._validate_call_literals(cap, args, query, obs, session_context)` dispatches to the pluginized 5-positional method → `TypeError: takes 5 positional arguments but 6 were given` → **every capability call crashes**.

### D-A205-2b — secondary (same method, latent)
Even if the parameter is added, the pluginized override **drops** it when delegating (pluginized.py:74):
```python
super()._validate_call_literals(capability_id, forwarded, query, observations)   # ← no session_context
```
So the base's `trusted_context_values` (the same-session referent grounding that D-A204-3 depends on) would be **empty** through the production path — Phase-3 «этом спринте» referent resolution would not work even after the signature is fixed. The fix must add the parameter **and** forward it.

### Why CI was green at ship time
- `test_agent_core_v4_identity_governance.py::_runtime()` builds **`ReliableAgentCoreV4Runtime`** (not the pluginized class) and calls `_validate_call_literals(...)` with **4 args** (5 positional incl. self) — matches the pluginized 5-positional signature, and `ReliableAgentCoreV4Runtime` also accepts 4 args. Passes.
- `test_v4_browser_api_contract.py` monkeypatches `get_runtime_bundle` with a **stub** runtime (records `HarnessRequest`s) — never invokes the real capability path.
- **No test constructs `PluginizedRobustReliableAgentCoreV4Runtime` and drives it through `process()` with a capability call.** The production override signature mismatch is therefore uncovered — the same "untested production override" class as A205-1.

### Owner fix (proposed, not implemented)
In `agent_core_v4_pluginized.py`, `PluginizedRobustReliableAgentCoreV4Runtime._validate_call_literals`:
1. Add `session_context: Mapping[str, str] | None = None` to the signature (mirror reliable.py:396).
2. Forward it: `super()._validate_call_literals(capability_id, forwarded, query, observations, session_context)` (line 74).
3. Add a regression that drives the **pluginized** runtime through `process()` with a real capability call (or at minimum calls the pluginized `_validate_call_literals` with the 5th `session_context` argument), so the production override signature is pinned.

## 5. Phases 2–11 live gates — BLOCKED; uniform 27/27 + 14 adversarial sweep

Because every capability call crashes at `_validate_call_literals` before any LLM synthesis or source read, the mandated matrix was executed as a full live sweep (concurrency 1, fresh sessions, REAL AS21 agent on `1dba9ad`): **37 RED (D-A205-2) + 4 pre-capability clarifications = 41/41, 0 COMPLETED.**

### 27-skill matrix (Phase 10)

| # | skill | NL request | Caps executed | Result |
|---|---|---|---|---|
| 1 | tasks.search | Открытые задачи в DMS | none (crash @ validate) | RED D-A205-2 |
| 2 | sprints.discover | Какой спринт в DMS идёт в сентябре | none | RED D-A205-2 |
| 3 | sprints.list | Активные спринты в DMS | none | RED D-A205-2 |
| 4 | sprint.current | Текущий спринт в DMS | none | RED D-A205-2 |
| 5 | task.lookup | Покажи задачу DMS-380 | none | RED D-A205-2 |
| 6 | task.summary | Опиши задачу DMS-380 | none | RED D-A205-2 |
| 7 | task.quality | Оцени качество задачи DMS-380 | none | RED D-A205-2 |
| 8 | task.acceptance | Оцени критерии приёмки задачи DMS-380 | none | RED D-A205-2 |
| 9 | task.blockers | Покажи блокеры задачи DMS-380 | none | RED D-A205-2 |
| 10 | sprint.health | здоровье сентябрьского спринта по DMS | none | RED D-A205-2 |
| 11 | release.health | здоровье релиза по DMS | none | NEEDS_CLARIFICATION (pre-cap; asks for a concrete release id — the intended D-A204-4 behavior; not a false success) |
| 12 | task.search_text | Найди задачи про аутентификацию в DMS | none | RED D-A205-2 |
| 13 | task.search_attachments | Задачи с вложениями в WMB | none | RED D-A205-2 |
| 14 | task.search_excel | Задачи с Excel вложениями у Уткина в WMB | none | RED D-A205-2 |
| 15 | task.search_pdf | Задачи с PDF вложениями в WMB | none | RED D-A205-2 |
| 16 | task.search_msg | Задачи с MSG вложениями в WMB | none | RED D-A205-2 |
| 17 | task.search_assignee | Задачи Гаранина в DMS | none | RED D-A205-2 |
| 18 | task.search_status | Открытые задачи в DMS | none | RED D-A205-2 |
| 19 | task.search_sprint | Покажи список задач в DMS-SPRNT-3 и их статусы | none | RED D-A205-2 |
| 20 | task.search_release | Задачи в релизе по DMS | none | RED D-A205-2 |
| 21 | task.search_product | Покажи задачи по DMS | none | RED D-A205-2 |
| 22 | task.missing_requirements | Чего не хватает в задаче DMS-380 | none | RED D-A205-2 |
| 23 | task.dependencies | Покажи зависимости задачи DMS-380 | none | RED D-A205-2 |
| 24 | task.history | покажи историю статусов задачи DMS-380 | none | RED D-A205-2 |
| 25 | task.time_in_status | сколько времени задача DMS-399 провела в каждом статусе | none | RED D-A205-2 |
| 26 | task.aging | Старые открытые задачи в DMS старше 30 дней | none | RED D-A205-2 |
| 27 | task.similar | Найди похожие задачи на DMS-380 | none | RED D-A205-2 |

**27-skill totals: 26 RED + 1 pre-cap clarification, 0 GREEN, 0 SOURCE_CONDITIONAL, 0 COMPLETED.**

### Adversarial pack (14 cases)

| Case | Loaded skill | Result |
|---|---|---|
| sprint health | sprints.discover | RED D-A205-2 |
| same-session t1 (health) | sprints.discover | RED D-A205-2 |
| same-session t2 «в этом спринте» | sprint.current | NEEDS_CLARIFICATION (pre-cap; t1 crashed → no session_context stored → turn-2 cannot resolve referent — downstream of the crash, not an independent defect) |
| OLP multi-hop (Garanin) | tasks.search | RED D-A205-2 |
| unassigned OLP | tasks.search | RED D-A205-2 |
| unassigned current-sprint OLP | tasks.search | RED D-A205-2 |
| workload «кто больше всех загружен» | sprints.discover | RED D-A205-2 |
| release health no-id | release.health | NEEDS_CLARIFICATION (pre-cap; correct D-A204-4 behavior) |
| release tasks no-id | task.search_release | RED D-A205-2 |
| history DMS-380 | task.history | RED D-A205-2 |
| time-in-status DMS-399 | task.time_in_status | RED D-A205-2 |
| capability «умеешь определять длительность» | (none) | NEEDS_CLARIFICATION (pre-cap; capability question, no source data) |
| explicit sprint DMS-SPRNT-3 | task.search_sprint | RED D-A205-2 |
| safe negative DMS-999999 | task.lookup | RED D-A205-2 |

**Adversarial totals: 10 RED + 4 pre-cap clarifications, 0 COMPLETED.**

The 4 pre-capability clarifications are **not false successes**: none executed a capability, none returned source data, and 2 of them (release health/tasks no-id) are the *intended* D-A204-4 typed-clarification behavior. No identity-only false completion, no fabrication, no local-truth read occurred (the crash precedes all source I/O). A204 defects D1–D4 are **not independently re-verifiable** — no trajectory reaches skill execution or a completed contract.

## 6. Phases 12–13 (audits)

- **Local store:** 0 `GET /api/v1/tasks` reads (agent log audit).
- **Source:** 0 `swtr-read` factual calls (all 37 RED crash before any source read; only the pre-cap clarifications avoided a capability entirely).
- **LLM:** 73 planner/decide calls total across the sweep (1–2 per run before the crash) — confirms the break is at the post-planner capability-validation boundary, not the LLM.
- **dummy-55 / plugin:** unit-level plugin tests green (within the 32); the live extension gate is BLOCKED by D-A205-2 (no V4 query can run a capability).

## 7. Defect summary

| ID | Severity | Description | Determinism |
|---|---|---|---|
| **D-A205-2** | **RED (blocking, total)** | `PluginizedRobustReliableAgentCoreV4Runtime._validate_call_literals` (agent_core_v4_pluginized.py:38) lacks the `session_context` parameter that `process()` (agent_core_v4.py:1237) passes unconditionally → `TypeError: takes 5 positional arguments but 6 were given` → 100% of capability-executing V4 queries FAILED. Production runtime resolves to this class (MRO verified). | 37/37 live + static MRO proof |
| **D-A205-2b** | RED (latent, same method) | pluginized.py:74 drops `session_context` when calling `super()` → even after the signature is fixed, same-session referent grounding (D-A204-3) would be inert through the production path; Phase-3 «этом спринте» would not resolve. | static |

## 8. Owner remediation + re-gate plan

1. Migrate `PluginizedRobustReliableAgentCoreV4Runtime._validate_call_literals`: add the `session_context` parameter **and** forward it to `super()` (mirror `ReliableAgentCoreV4Runtime._validate_call_literals`, reliable.py:396).
2. Add a regression that drives the **pluginized** runtime through `process()` with a capability call (or calls its `_validate_call_literals` with the 5th arg) so the production override signature is pinned — this exact gap let both A205-1 (planner) and A205-2 (literals) ship.
3. Re-run the full A205 (Phases 2–11) with fresh oracles. Do not add skills / start Wave S until GREEN.

## 9. Services left running

| Service | Port | PID | Health |
|---|---|---|---|
| UI (vite, ::1) | 5175 | 55236 | 200 (`http://localhost:5175/`) |
| agent (1dba9ad) | 8212 | 54878 | `/live` 200; all capability-executing V4 queries FAILED (D-A205-2) |
| task-api (system py3, SSE) | 8241 | 30041 | `swtr-read/health` connected, 48 tools |
| MCP-SWTR | 3000 | 29268 | SSE OPEN |

**QA artifacts (untracked, root):** `qa_205b_restart_agent.sh`, `qa_205_sweep.py`; `/tmp/qa205b_agent.log`, `/tmp/qa205_sweep.jsonl`, `/tmp/qa205b_sweep_adv.log`.

**STOP after this report — no Wave S, no new skills, awaiting owner fix + full re-gate.**
