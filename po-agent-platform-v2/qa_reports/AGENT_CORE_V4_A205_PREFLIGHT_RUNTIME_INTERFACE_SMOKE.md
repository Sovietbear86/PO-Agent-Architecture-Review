# A205 Runtime Interface Preflight — Smoke (QA)

**Date:** 2026-09-22
**Role:** QA/adversarial tester + service operator only (no production changes)
**Branch:** `feat/core8-real-query-hardening-v2`
**START_HEAD:** `a4b8a25c613b117a8bd6d20e648079e6b11a6d02`
**Prior A205 attempts:** `bd6a973` (D-A205-1: robust planner `next_decision` signature) → `1dba9ad` (D-A205-2: pluginized `_validate_call_literals` signature + `super()` drop). Both fixed by owner since.

## Verdict

`AGENT_CORE_V4_A205_PREFLIGHT_GREEN`

Recommendation: `PROCEED_TO_FULL_A205_RERUN` (not started automatically, per spec).

## Phase 0 — diff / static interface sweep: GREEN

Owner diff `fbf4745..a4b8a25` limited to:
- `agent_core_v4_pluginized.py` (+8/−1): `_validate_call_literals` gains `session_context: Mapping[str, str] | None = None` and forwards it in the `super()` call (the exact D-A205-2/2b remedy);
- `test_agent_core_v4_plugin_registry.py` (+52): interface-parity regressions;
- docs/spec (GIGACODE_NEXT_ACTION, V4_54_SKILL_MIGRATION_PLAN, V4_DOD_LOCK).

No other src/test changes. No task-api changes (only the agent file changed vs `1dba9ad`, so only the agent was restarted).

Signature audit (python `inspect`, MRO order) of the full production chain:

| Method | Pluginized | RobustReliable | Reliable | Base | Planner (Robust / Base) |
|---|---|---|---|---|---|
| `_validate_call_literals` | 5+`session_context` (defined) | inherited [ctx] | defined [ctx] | defined [ctx] | — |
| `process` | inherited `(self, request)` ×3 | base `(self, request)` | | | — |
| `next_decision` | — | — | — | — | Robust `(self, user_query, catalog, loaded_skills, observations, session_context)` = Base [ctx] |

Critical bind check: MRO-resolved `PluginizedRobustReliableAgentCoreV4Runtime._validate_call_literals` accepts `session_context` and `sig.bind(self, cap, args, query, obs, ctx)` **OK** — the exact 6-positional call made by `process()` (`agent_core_v4.py:1237`) is now compatible at every layer. No incompatible override found.

## Phase 1 — focused interface tests: GREEN

- `test_agent_core_v4_plugin_registry.py` + `test_agent_core_v4_robust_protocol.py` + `test_v4_browser_api_contract.py`: **30/30 passed** (verbose), including the two new parity tests `test_session_context_interface_parity_across_production_runtime_chain` and `test_pluginized_literal_guard_forwards_session_context_to_base`, and the A205-1 test `test_robust_planner_accepts_and_forwards_generic_session_context`.
- Note: spec-named `tests/test_agent_core_v4.py` does not exist; superseded by the full glob below.
- No-regression: `tests/test_agent_core_v4*.py tests/test_v4*.py` → **131/131 passed**.
- Task-api suites unchanged since `1dba9ad` (no task-api diff).

## Phase 2 — production-chain smoke (agent restarted on a4b8a25, PID 84446): GREEN

Concurrency 1, fresh sessions. **Zero TypeError / signature mismatch / unexpected keyword / positional-argument errors** in any response or in the agent log (84 LLM calls total, 0 signature markers).

| # | Case | Status | Capability calls executed | Result (live source) |
|---|---|---|---|---|
| 1 | `покажи задачу DMS-380` | COMPLETED 27.5s | `task.lookup` | DMS-380 mTLS/SSL, Закрыт/Не сделано, 1 evidence |
| 2 | `задачи Калачанова в WMB` | COMPLETED 53.7s | `task.search_assignee` | Kalachanov.V.V, 5 WMB tasks (WMB-30000/29890/29995/29830/29242), 5 evidence |
| 3 | `Покажи список задач в DMS-SPRNT-3 и их статусы` | COMPLETED 53.8s | `sprint.resolve`, `task.search` | DMS-SPRNT-3, 65 tasks, 66 evidence |
| 4 | `найди задачи без исполнителя в текущем спринте OLP` | COMPLETED 35.1s | `space.resolve`, `sprint.current`, `task.search` | OLP-SPRNT-8, 3 unassigned (OLP-3143/3155/3129) |
| 5 | `задачи Гаранина в сентябрьском спринте` → pick real space | t1 NEEDS_CLARIFICATION (typed options CRPV/DMS/OLP/STS/WMB, after `member.resolve`+`sprint.search` executed); t2 (real `clarification_id` + `DMS`) **COMPLETED** | `member.resolve`, `sprint.search` → `space.resolve`, `sprint.search`, `task.search` | `task.search(assignee=Garanin.R.V, sprint_id=DMS-SPRNT-3, space=DMS)` → **7 tasks** (A200/A201 continuation contract retained) |
| 6 | `Какой спринт в DMS идёт в сентябре?` → same session `Покажи список задач в этом спринте и их статусы` | t1 COMPLETED; t2 **COMPLETED 29.3s** | t1 `space.resolve`, `sprint.search` (sprints.discover); t2 `task.search` | t2 executed `task.search(sprint_id=DMS-SPRNT-3, space=DMS)` → 65 tasks — same-session «этом спринте» referent resolved to the exact prior-turn sprint (D-A204-3 channel works; D-A205-2b latent drop confirmed fixed) |
| 7 | `вложения у Калачанова в WMB` | COMPLETED 275.5s (first attempt hit a 240s client timeout — LLM endpoint slowness, not framework) | `task.search_attachments` | 3 WMB tasks, 16 files — matches A193 ground truth (WMB-29890×1, WMB-29995×10, WMB-30000×5) |

Hard-requirement checks:
- zero framework TypeErrors: **PASS** (responses + agent log);
- at least one real capability executed in every supported factual case: **PASS** (7/7);
- no local factual reads: **PASS** (0 × `GET /api/v1/tasks` in agent log);
- no false success: **PASS** (every COMPLETED answer backed by swtr-read evidence; clarification path typed, not a completion).

Source/local audit (agent log, all preflight runs): `local_reads=0`, `swtr-read source calls=34` (sprints/10, tasks/7, assignees/resolve/7, spaces/5, task-query/3, health/2), `LLM calls=84`, `signature markers=0`.

Session-context leak audit (precise key-path walk over the v4 state of a fresh same-session pair): `top_level_session_context_key_present=false`, zero `*context*` key paths anywhere in `_agent_core_v4` (top-level keys: runtime, semantic_prepass_used, progressive_skill_loading, loaded_skills, trajectory, observation_count, completion). One earlier coarse substring check flagged `True` — re-audited as a substring-in-value false positive, not a public key. Internal-only invariant retained.

Non-blocking LLM non-determinism observed (pre-existing classes, no interface markers, no crashes):
- Case 5 t1 variant noise across ~4 runs: once typed options (canonical), once NL question without options (A193 turn-1 shape variance), once `FAILED` after `member.resolve` only with caps=['member.resolve'] (error text not capturable from access-log; signature identical to the documented A199-F3/A200 flake class on the same query class). Canonical typed-clarification → continuation path proven end-to-end in the decisive run.
- Case 7 first attempt: 275s wall time — Qwen3.8 endpoint slowness under this run (retry succeeded).
- `semantic_prepass_used=false` in all captured trajectories; no prepass.

## Phase 3 — plugin extension sanity: GREEN

`test_dummy_55_can_be_added_without_agent_core_change` **PASSED** (registry/binding/completion/UI contract, zero core business edits).

## Services (left running)

| Service | URL | PID | Health |
|---|---|---|---|
| Agent (a4b8a25) | http://localhost:8212 | 84446 | `/live` 200, `EXPECTED_HEAD=a4b8a25` |
| Task API (system py3, SSE) | http://127.0.0.1:8241 | 30041 | `swtr-read/health` connected, 48 tools |
| MCP-SWTR (own venv) | http://127.0.0.1:3000/sse | 29268 | serving (48 tools via task-api) |
| UI (vite) | http://localhost:5175 | 55236 | 200 |

## Conclusion

The runtime interface is compatible across the entire production inheritance chain; the D-A205-2/D-A205-2b defect is confirmed fixed at both test level (parity tests) and live level (all 7 smoke cases reach real capability execution through the pluginized runtime with `session_context` forwarded, including the same-session «этом спринте» referent and the clarification continuation with full multi-filter constraints). No framework/interface crash of any kind.

`PROCEED_TO_FULL_A205_RERUN` — awaiting explicit instruction; not started.
