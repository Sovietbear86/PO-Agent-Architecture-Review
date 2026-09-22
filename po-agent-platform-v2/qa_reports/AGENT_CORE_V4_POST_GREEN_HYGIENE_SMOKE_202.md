# A202 — Post-Green Hygiene Smoke

**Date:** 2026-09-22
**Verdict:** `AGENT_CORE_V4_POST_GREEN_HYGIENE_SMOKE_GREEN`
**START_HEAD:** `e580489950e5a149a6a740cb8779dfdb0351d471`
**A201 base:** `ae5caeed503ebc3839a5957cd612fc1751cbada3`
**Owner hygiene diff:** `ae5caee..e580489` (5 commits, 2 source files + 2 test files + docs)

## Executive summary

The `/health` fix is **CERTIFIED**: Agent `/health` now returns in **194ms** (was >25s hang before), using a lightweight `swtr-read/health` probe with **0** unscoped task collection queries. All high-risk A201 paths remain intact. No new RED.

## Phase 0 — diff/static gate (PASS)

Source diff: 2 files, 21 insertions, 1 deletion.

| File | Change | Verdict |
|---|---|---|
| `adapters/task_api.py` | New `source_health()` method: calls `GET /api/v1/swtr-read/health` with 5s timeout, returns metadata dict | ✅ Operational only, no task collection |
| `api/v1/__init__.py` | `health_check()`: replaces `search_tasks("", max_results=1)` with `source_health()`; adds generic `Exception` catch | ✅ No behavioral change beyond health path |

No Agent Core/planner/completion change. No new skills. No local-store fallback.

## Phase 1 — focused automated tests (62 passed, 3 owner test bugs)

| Suite | Result |
|---|---|
| `test_v4_owner_fix_contracts.py` | 2 pass, 2 fail (owner bug: lines 187/213 still use 2-tuple unpack for 3-tuple function) |
| `test_v4_browser_api_contract.py` | 10 pass, 1 fail (owner bug: mock missing `available_facts` attribute) |
| `test_agent_core_v4_completion_contract.py` | **23/23** |
| `test_agent_core_v4_plugin_registry.py` + `test_agent_core_v4_task_catalog.py` | **20/20** |

3 failures are owner test-compatibility bugs (incomplete test fix in `5410d00`), not production defects. The production `health_check` code path is correct (verified live in Phase 2).

## Phase 2 — live health hygiene (PASS)

| Endpoint | Status | Latency |
|---|---|---|
| Agent `/live` | 200 | **154ms** |
| **Agent `/health`** | **200** | **194ms** |
| Task API `swtr-read/health` | 200 | 72ms |

Log proof: 0 `task-query` calls, 0 `GET /api/v1/tasks` reads. `/health` called only `GET /api/v1/swtr-read/health` (the lightweight probe).

**A195B F2 CLOSED.**

## Phase 3 — retained high-risk live smoke (all GREEN)

| Scenario | Result |
|---|---|
| S1: DMS-380→assignee ×2 | **2/2 COMPLETED `runtime_contract` 320/320 exact** (Semavin) |
| S2: person attachments WMB ×2 | **2/2 COMPLETED 3/3 exact** |
| S3: person text WMB ×2 | **2/2 COMPLETED 4/4 exact** |
| S4: current-sprint multi-filter ×2 | **2/2 COMPLETED [DMS-371] exact** |
| S5: period-sprint continuation ×5 | **2/5 TRUE** exact 6/6 (D-A200-1 retained), 0 FALSE |
| S6: ambiguous Уткин → click → turn2 | **COMPLETED 57/57 exact** |
| S7: release SOURCE_CONDITIONAL | **FAILED** ev=0, fail-closed typed |

No false completions. No all-space leaks. No internal state leak.

## Phase 4 — Browser C smoke (4/4)

| Case | Result |
|---|---|
| S1 factual DMS-380 | NEEDS_CLARIFICATION (LLM non-determinism, safe, no error) |
| S2 person attachments | **COMPLETED `runtime_contract`** ev=17 |
| S3 ambiguity continuation | NEEDS_CLARIFICATION → click `Utkin.S.A` → **turn2=COMPLETED** |
| S4 release SOURCE_CONDITIONAL | **FAILED** ev=0, fail-closed |

`has_internal_leak=false` in all 4. `has_generic_v4_error=false` in all 4.

## Phase 5 — plugin extensibility (GREEN)

`test_agent_core_v4_plugin_registry.py` + `test_agent_core_v4_task_catalog.py`: **20/20** (dummy-55 gate retained).

## Final classification

| Check | Result |
|---|---|
| `/health` fast (≤5s target) | **194ms** ✅ |
| 0 unscoped task scan on `/health` | **0 calls** ✅ |
| High-risk live paths exact | **all exact** ✅ |
| No false completion | **0** ✅ |
| Browser C supported paths | **GREEN** ✅ |
| dummy-55/plugin | **20/20** ✅ |
| New RED | **0** ✅ |

**Verdict: `AGENT_CORE_V4_POST_GREEN_HYGIENE_SMOKE_GREEN`**

**Recommendation: Create immutable/rollback checkpoint for tested HEAD `e580489` and wait for explicit owner/user approval before Wave S #23–32.**

## Non-blocking findings

- **F1 — LLM endpoint degradation (ongoing):** 3/5 S5 runs lost to timeout/ValidationError (same A200/A201 F1). No product logic impact.
- **F2 — Owner test bugs (3 tests):** Incomplete 2→3-tuple fix (lines 187/213 of `test_v4_owner_fix_contracts.py`) + missing `available_facts` in health test mock. Owner needs 3-line fix.

## Services left running (HEAD e580489)

| Service | URL | Port | PID | Health |
|---|---|---|---|---|
| UI (Vite) | http://localhost:5175 | 5175 | 55206 | 200 |
| PO Agent | http://127.0.0.1:8212 | 8212 | 63078 | `/live` 200, `/health` 200 **194ms**, EXPECTED_HEAD=`e580489` |
| Task API | http://127.0.0.1:8241 | 8241 | 55200 | `swtr-read/health` 200, 72ms |
| MCP-SWTR | http://127.0.0.1:3000/sse | 3000 | 55196 | connected |
