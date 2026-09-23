# AGENT CORE V4 — Pre-S2 Manual Query Consistency (A208) — QA Report

**Assignment:** 208 — Pre-S2 manual query consistency re-gate
**Role:** QA / adversarial + service-operator only (no production edits, no Wave S2, no new skills)
**START_HEAD:** `6519b87885314076942dfb2eb09f35c67a5fecd8` (branch `feat/core8-real-query-hardening-v2`)
**Stable rollback checkpoint:** `checkpoint/v4-wave-s1-green@ce64264` (A207 GREEN)
**Date:** 2026-09-23 (supersedes the earlier same-day BLOCKED_BY_PROVEN_SOURCE_OUTAGE report; the LLM endpoint recovered and live phases 3–8 were re-run)

---

## VERDICT

### **AGENT_CORE_V4_PRE_S2_MANUAL_CONSISTENCY_RED**

**Blocking defect D-A208-1** (deterministic, 8/8 live): the short-form / explicit-id forms of **`sprint.wip`** (and, proven latent and reproduced live for **`sprint.scope`**) cannot complete. Root cause: the `sprint.wip`/`sprint.scope` completion contracts require the observation data key **`task_keys`**, but the V4 observation pipeline (`AgentCoreV4Runtime._compact_data`, `agent_core_v4.py:1085-1089`) **always renames `task_keys` → `task_keys_sample` and pops `task_keys`** — so the contract is **structurally unsatisfiable** whenever the READY-path contract gate is active (i.e. when the planner loads only contracted skills, which the new 3aa47ce procedure induces for product-only/current and explicit-id forms). The planner's READY is then rejected `unsatisfied_completion_contract` 4–5 times → `v4 planner step budget exhausted without READY` → FAILED.

**Not a regression in the owner's task.search/blocked/source-status fixes** — those are certified GREEN live (P3/P4 below). The defect is in the Wave S1 completion-contract / observation-compaction interaction, newly exposed by 3aa47ce's direct-skill-loading procedure.

**STOP.** No code fixed, no Wave S2 started. Owner fix proposed (report §Root cause), then re-gate A208 live phases 5–8.

---

## LLM preflight (resumed run) — **GREEN**

After the earlier outage window, a preflight of 3 planner-sized requests: **3/3 within the 60 s budget** (29.7 s / 11.1 s / 20.3 s, `finish_reason=stop`, non-empty content). Phases 0–2 were already GREEN at this HEAD and were not repeated; live phases 3–8 proceeded.

## Phase 0 / 1 / 2 (retained from first run, same HEAD) — **GREEN**

- P0 diff `ce64264..6519b87`: generic predicates only (`blocked`→`task.is_blocked`; `status_raw`/`status_type` matching; declarative sprint-resolution exposure); no hardcodes, no phrase-routing, no local fallback.
- P1: 22 + **140** tests passed (incl. new `test_agent_core_v4_task_search_source_status.py`).
- P2 fresh oracle (rebuilt at re-run, source drifted 65→66→**68**): DMS-SPRNT-3, **68 tasks**; status names: In progress 12, Open 20, Resolved 10, Closed 4, Закрыт 3, **На исправлении 1**, Тестирование 2, In review 6, Ready for QA 2, QA 4, Ready for review 1, **Need info 2**, Зарегистрирован 1; **canonical `is_blocked` = 2 → DMS-352, DMS-379**; terminal = 17 (Closed 4 + Resolved 10 + Закрыт 3); non-terminal = 51.

## Phase 3 — Blocked drill-down parity — **10/10 EXACT ✅**

| Form | Runs | Result |
|------|------|--------|
| "Заблокированные задачи спринта DMS-SPRNT-3" | 6/6 COMPLETED `runtime_contract` | `task.search(sprint_id=DMS-SPRNT-3, status=blocked)` → **exactly [DMS-352, DMS-379]** |
| "покажи заблокированные задачи сентябрьского спринта по DMS" | 3/3 COMPLETED | sprint.search-period → `task.search(sprint_id=DMS-SPRNT-3, space=DMS, status=blocked)` → [DMS-352, DMS-379] |
| "какие задачи заблокированы в текущем спринте DMS?" | 1/1 COMPLETED | sprint.current → same exact keys |

- **blocked ↔ sprint.health parity: EXACT** — `sprint.health` at the same 68-task moment: `total=68, completed=17, active=13, blocked=2` (both parity runs); `task.search status=blocked` count = 2, keys = oracle `is_blocked` set. No zero-while-health->0, no premature planner-ready before the blocked collection.
- Same-predicate provenance: `team_intelligence.py:75` (health) and `agent_core_v4.py:965` (task.search blocked) both use `task.is_blocked`.

## Phase 4 — Raw source status filtering — **EXACT ✅**

| Query (sprint DMS-SPRNT-3) | Runs | Result vs oracle |
|------------------------------|------|------------------|
| "задачи в статусе На исправлении" | 3/3 | exactly **[DMS-399]** (1) — A207-F2 gap closed live |
| "задачи в статусе In review" | 2/2 | 6 keys, matches oracle In review set |
| "задачи в статусе Закрыт" (enum-UNKNOWN label) | 2/2 | exactly [DMS-273, DMS-390, DMS-380] (3) |
| "задачи в статусе Need info" | 1/1 | exactly [DMS-352, DMS-379] |
| "незакрытые задачи" (not_completed retained) | 1/1 | 51 = 68 − 17 ✅ |
| "закрытые задачи" (completed retained) | 1/1 | 17 ✅ |

No custom source label became empty merely because the TaskStatus enum is UNKNOWN.

## Phase 5 — Short-form metric resolution — **RED (D-A208-1)**

| Form | Runs | Result |
|------|------|--------|
| **`wip спринта по DMS`** | 5/5 (batch) + 1 (probe) | **FAILED** `v4 planner step budget exhausted without READY`; all READY turns `ready_rejected=unsatisfied_completion_contract` |
| **"WIP спринта DMS-SPRNT-3"** (explicit id, probe) | 1/1 | **FAILED**, identical signature |
| **"scope спринта по DMS"** (probe) | 1/1 | **FAILED**, identical signature (latent defect confirmed live) |
| "velocity спринта по DMS" | 1/1 | COMPLETED `runtime_contract` (17 tasks/sprint — correct at 68-task moment) |
| "WIP сентябрьского спринта по DMS" (period, probe) | 1/1 | COMPLETED `planner_ready` (wip=30) — via contract-gate bypass (see below) |

Trajectory of every failing run (identical): `sprint.wip {sprint_id, space}` call executes (capability bound and invoked), then the model's READY is rejected 4–5× `unsatisfied_completion_contract` → step budget → FAILED. The metric call is never the problem; the completion gate is.

**Phases 6–8 (health/WIP sanity, retained regression, Browser C) NOT run** — STOP at first new defect per assignment rule ("Любой RED — локализовать и остановиться").

## Root cause — D-A208-1 (proven at unit level)

1. **Structural:** `sprint.wip` contract = `CompletionRequirement("sprint.wip", data_keys=("sprint_id", "wip", "task_keys"))` (wave_s1.py:407); `sprint.scope` = `data_keys=("sprint_id", "total", "task_keys")` (wave_s1.py:380). But `AgentCoreV4Runtime._compact_data` (agent_core_v4.py:1085-1089) always does `result.pop("task_keys")` after renaming to `task_keys_sample`/`task_key_count`. Unit proof: real handler output → real `_compact_data` → `_observation_matches_base` = **False**, `is_skill_satisfied(sprint.wip)` = **False** (and the same False for sprint.scope). The contracts are **unsatisfiable by construction** on the stored observation.
2. **Trigger (why only now):** the READY-path gate (agent_core_v4.py:1226-1229) applies contract checking only when **every** loaded skill has a contract (`all(skill_id in self._skill_contracts ...)`). Owner 3aa47ce's new procedure ("resolve the sprint generically… then call sprint.wip…") leads the planner to load **only** the metric skill for product-only/current and explicit-id forms → gate active → unsatisfiable contract → forced rejection loop → FAILED.
3. **Why the period form (and all of A207) passed:** there the planner additionally loads `sprints.discover`, which has **no** completion contract (`completion=()`) → `all(...)` is False → planner READY accepted as-is (`planner_ready`) → the broken contract is never evaluated. Verified: wip-period probe completed `planner_ready` wip=30; A207's scope/velocity/wip runs all loaded sprints.discover and completed `planner_ready`.
4. **Unaffected:** sprint.velocity (`data_keys=("sprint_id","velocity","unit")`) and sprint.throughput (`("sprint_id","throughput","unit")`) — no `task_keys` in their contracts; velocity short-form COMPLETED live.
5. **Safety preserved:** every failing run fails closed (typed `v4_runtime_failure`, 0 fabricated facts); no premature completion.

**Proposed owner fix (generic, not a QA change):** align the Wave S1 completion contracts with the stored (compacted) observation shape — e.g. `data_keys=("sprint_id","wip","task_key_count")` for sprint.wip and `("sprint_id","total","task_key_count")` for sprint.scope (or preserve `task_keys` for these capabilities in `_compact_data`), plus a non-mocked regression test that the short-form "wip спринта по DMS" completes via `runtime_contract`. Then re-gate A208 phases 5–8.

## Service health (left running)

| Service | Port | State |
|---------|------|-------|
| PO Agent (HEAD `6519b87`) | 8212 | `/live` 200 (PID 64407) |
| Task API (system python3) | 8241 | `/health` 200 |
| UI (IPv6 `[::1]`) | 5175 | 200 |
| MCP-SWTR | 3000 | connected (fresh oracle + 30+ live queries served) |
| `/versions` (release dir) | — | HTTP 502 (independent, pre-existing; release.search stays SOURCE_CONDITIONAL) |
| LLM endpoint (Qwen3.8-27B) | — | recovered; preflight 3/3 within 60 s budget |

**STOP.** Only this QA report committed; no production code modified; Wave S2 not started.
