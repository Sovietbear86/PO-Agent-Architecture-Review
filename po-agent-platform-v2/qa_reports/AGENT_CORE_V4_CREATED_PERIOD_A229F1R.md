# A229F1R — Created-period functional pre-gate

**Verdict:** `AGENT_CORE_V4_CREATED_PERIOD_RED_A229F1R`
**Classification:** RED_PRODUCTION_PLUGIN_REGISTRY_INIT_FAILURE (missing `CapabilitySpecV4` for `task.search_created`)
**Date:** 2026-10-01
**QA role:** QA/adversarial tester only, zero code changes
**Branch:** `feat/core8-real-query-hardening-v2`
**START_HEAD:** `efea3ca9b4c0f65aa20ce9c8833fe600caae8d71`
**STOP boundary:** P0, item 4→5 (first failing evidence at agent init / first live query). P1–P4 NOT executed.

---

## P0 — integrity (executed until first RED)

| # | Item | Result |
|---|---|---|
| 1 | Pull + START_HEAD + worktree | `efea3ca` (fast-forward from `f1141aa`); tracked worktree clean (untracked QA artifacts only) |
| 2 | Byte-identical Core vs `c41b00c` | **PASS 5/5** (git blob hashes): `contracts.py` 20d93d5d, `agent_core_v4.py` 52100ca1, `agent_core_v4_robust.py` 3bdb4d09, `api/v1/__init__.py` 8f4b1663, `test_agent_core_v4_robust_protocol.py` 6e8e8cd9 — the dialogue-context revert is real at the byte level |
| 3 | Focused created-period + sprint single-read tests | 5/5 (`test_agent_core_v4_task_created_period.py`) + 1/1 (`test_agent_core_v4_plugin_sprint_single_read.py`) — handler logic and period parsing (explicit + relative, Moscow TZ) unit-green |
| 4 | Full V4 blast-radius | **RED — 51 failed / 187 passed**, all 51 with the SAME production error (below) |
| 5 | Frontend tsc/build | GREEN (tsc clean, vite build 624ms) |
| — | Task API focused tests | 12/12 (`test_swtr_assignee_canonical.py`) |

Owner net diff since A229 (`f1141aa..efea3ca`, 12 files): created-period capability (task_catalog.py +15, _task_live_handlers.py +123, test +159), sprint single-read (core.py +98, test +96), registry capability-duration instrumentation (v4_plugin_registry.py +31), UI snapshot concurrency cap = 2 (pageSnapshot.tsx +20), assignee-tasks TQL space push (task-api swtr_assignee.py +17, test ±12), docs. All five reverted dialogue-context files byte-identical to `c41b00c` (item 2).

## First failing evidence (preserved)

1. **Agent init / first query** — agent restarted on `efea3ca` (PID 38141, env V4-enabled, task-api mode). First live query `Спринты в DMS`:
   - HTTP 200, `status=FAILED`, wall 0.0–0.1s, 0 planner turns, 0 LLM calls, 0 source calls
   - `data._harness.runtime_init_error = "V4PluginError: capability binding mismatch: missing=[], extra=['task.search_created']"`, `exception_type=V4PluginError`, `warnings=["harness_internal_error"]`, `runtime=legacy_harness`
   - trace `aecac4bf-f4ce-4dc6-90e5-4d5c0ec774a6` (probe payload preserved at `/private/tmp/qa229f1r/red_live_probe.json`)
   - agent log `/private/tmp/qa229f1r_agent.log`: traceback `discover_v4_plugins() → V4PluginRegistry.__init__ (v4_plugin_registry.py:149)` on every query; first logged failure 15:19:52 MSK
2. **Test suite** — the same `V4PluginError: capability binding mismatch: missing=[], extra=['task.search_created']` at `v4_plugin_registry.py:149` in **51 tests across 17 files** (incl. `test_agent_core_v4_task_catalog.py` 8/8, `test_agent_core_v4_plugin_registry.py` 3/3, morphology/grounding 6, batch 2/3/4/5/6, wave s1/s2, agent_help, time_accounting ×3, status_normalization 2, release_regression 1, team_competency 1). These are NOT stale fixtures: the tests construct the registry from the production plugin modules and the error is the production invariant firing.

## Root cause (proven, single line)

`task_catalog.py` registers `task.search_created` in **SKILLS** (line 177), **BINDINGS** (line 223, `build_task_search_created`) and **UI** (line 241), but the **CAPABILITIES** tuple (lines 94–140, ends at `task.similar`) has **no `CapabilitySpecV4("task.search_created", ...)` entry**.

Registry invariant `v4_plugin_registry.py:147-149`:
```python
missing = sorted(set(self._capabilities) - set(self._bindings))
extra   = sorted(set(self._bindings) - set(self._capabilities))
raise V4PluginError(f"capability binding mismatch: missing={missing}, extra={extra}")
```
→ `extra=['task.search_created']` → `discover_v4_plugins()` raises at agent init → `PluginizedRobustReliableAgentCoreV4Runtime.__init__` fails → **100% of V4 queries** (including all previously certified capabilities: task search, sprints, attachments, time accounting, release, portfolio, po.local_task_draft, …) return typed FAILED `runtime_init_error`. Fail-closed and safe (no data leakage, no local fallback — verified in the probe payload), but the V4 surface is entirely down.

This is the same recurring owner-shipped-RED class as A205-1/A205B/A217C (production path exercised in tests is broken while narrow new tests pass): the 6 new created-period tests pass because they call `build_task_search_created` directly and never construct the full registry.

## Minimal owner fix (proposed, not implemented by QA)

Add the missing spec to `CAPABILITIES` in `task_catalog.py` (matching the skill's grounded arguments), e.g.:
```python
CapabilitySpecV4(
    "task.search_created",
    "Find REAL AS21 tasks created during a relative or explicit calendar period; period wording is passed raw and parsed inside the capability. Missing source created_at provenance fails closed.",
    {"reference": "optional natural person reference", "space": "optional grounded product space", "created_period": "required raw user period wording (relative 'последние N дней' or two explicit dates)"},
),
```
Then re-run: full V4 blast (expect 51→0, plus the 2 pre-existing fixture gaps below), and the A229F1R re-gate from P0.

Secondary (will surface after the fix, fixture-side): `test_agent_core_v4_plugin_status_normalization.py` 2 tests use a fake Runtime without `_safe_status`, now required by the new sprint single-read path in `core.py:44` (production Runtime has it — `agent_core_v4.py:690`, byte-identical Core; fixture gap only).

## Phases not executed (STOP per spec)

P1 (explicit period 5/5), P2 (relative 2 days 5/5), P3 (fail-closed provenance), P4 (architecture audit) — the agent cannot execute any V4 capability while `discover_v4_plugins()` raises.

## Non-blocking observations (for the re-gate, not the verdict)

1. **STS Kalachanov corpus is large and active**: 2,800 tasks, task-query person+space scan ≈ 70s (28 pages); newest created_at observed 2026-10-01T11:35:38Z (minutes before probe) — P2 «последние 2 дня» runs will need oracle built immediately before the batch with a documented drift re-probe protocol.
2. All 2,800 corpus rows currently carry `created_at` (0 missing) via task-query — the P3 fail-closed path is fixture-provable only live unless the source changes.
3. Registry instrumentation (capability duration logging) is behavior-neutral (wrap-only, re-raises).
4. UI snapshot semaphore (max 2 in flight) matches A229 R3; tsc/build green.
5. QA note: independent MCP-direct oracle script (`qa_229f1r_oracle.py`) was not needed for the verdict; its SSE response reader still needs a rework for large frames before P1 use.

## Services state at STOP

agent 8004 (PID 38141 @ efea3ca, /live 200 but V4 init broken), task-api 8241 (PID 96598), MCP-SWTR 3000 (PID 97012), vite 5175 [::1] (PID 39280). Log: `/private/tmp/qa229f1r_agent.log`; evidence: `/private/tmp/qa229f1r/red_live_probe.json`.

**Recommendation:** owner adds the missing `CapabilitySpecV4` (one entry) + refreshes the stale status_normalization fixture, then A229F1R re-gate from P0 item 4.
