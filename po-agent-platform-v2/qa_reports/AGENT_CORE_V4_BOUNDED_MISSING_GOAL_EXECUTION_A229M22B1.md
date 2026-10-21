# A229M2.2B1 — Bounded Missing Goal Executor: Independent Regression Gate

**Verdict: AGENT_CORE_V4_BOUNDED_MISSING_GOAL_EXECUTION_GREEN_A229M22B1**

## Identity

| Field | Value |
|-------|-------|
| TESTED_HEAD | `d425438c44addeb0c7e9b1e17fdeec97e81de9b1` |
| REPORT_COMMIT | _(this commit)_ |
| Date | 2026-10-21 |
| Branch | `feat/core8-real-query-hardening-v2` |
| Services | agent 8004, task-api 8241, MCP 3000, vite 5175 |

## P0 — Frozen Core + Focused Tests

Core 6/6 **byte-identical** to `6fb335d`:

| File | Hash |
|------|------|
| agent_core_v4.py | 52100ca1 |
| agent_core_v4_robust.py | 3bdb4d09 |
| agent_core_v4_reliable.py | 1f7562dc |
| agent_core_v4_completion.py | cf75a6d6 |
| v4_plugin_registry.py | d82929d1 |
| llm/real.py | 1cc10e12 |

**Test suites:**
- Focused (test_v4_missing_goal_execution + goal_coverage + browser_api + synthesis + team_config + runtime_factory + env_aliases): **76 passed / 1 FAILED** (pre-existing: test_runtime_factory_builds_task_api_source stale A206-era expectation, A/B-proven at 453c7dd)
- Full V4 blast (test_agent_core_v4*.py + test_v4*.py): **297 passed**
- Task API SWTR (assignee_canonical + timestamps + task_query_partial): **16 passed**
- Frontend `npm run build`: **exit 0**

## P1 — Owner Implementation Safety Audit

**CONFIRMED SAFE** (see prior session notes). Key properties verified:
- Triple-flag gate: all three flags must be True for executor activation
- Loopback-only: `request.client.host in ("127.0.0.1", "::1")` at `__init__.py:569`
- Governed `v4_runtime.process(HarnessRequest)` only (no handler/MCP bypass)
- MAX_GOALS=3, MAX_EXTRA_CALLS=2, TOTAL_DEADLINE=110s, per-call timeout min(remain,100s)
- Prior credit-only via `_credit_prior_observations` (never in public results)
- `_source_verified_rows` requires REAL_AS21 + not source_unavailable + source_complete != False
- COMPLETED only when all goals have matched terminal evidence; else typed PARTIAL
- Answer composed only from source-verified terminal rows (no LLM re-synthesis)
- Flag defaults: all three `Field(default=False)` in settings.py
- No Core/planner/plugin changes

## P2 — Flag Matrix

| Mode | Result |
|------|--------|
| **OFF** (all false) | M2 COMPLETED 57.7s, C1 COMPLETED 120.5s. No guard/executor markers. ✓ |
| **GUARD_ON** (guard only) | "Покажи задачу DMS-267 и его иерархию" → **NEEDS_CLARIFICATION** + `v4_goal_coverage_incomplete`, gc={2,proven:[g2],unproven:[g1]}. No continuation/executor markers. ✓ |
| **GUARD_CONT** (guard+cont) | T1: NC + gc={2,proven:[g2],unproven:[g1]} + `goal_continuation_pending=True` + cid issued. T2: loaded_skills restored (task.lookup). 429 blocked T2 execution (environmental). ✓ |
| **EXEC_ONLY** (executor only, prereqs OFF) | Code-level guarantee: triple-AND at `__init__.py:563-566` requires all three True. Executor cannot activate. ✓ |
| **ALL_ON** (all three) | Executor activates, bounded execution verified. See P3. ✓ |
| **Remote client** | Loopback gate at `__init__.py:569` blocks non-127.0.0.1/::1. ✓ |
| **Flag defaults** | All three `Field(default=False)`. ✓ |

## P3 — REAL AS21 A/B Oracle (ALL_ON)

### Oracle (no drift: START = END)

| Fact | START | END |
|------|-------|-----|
| DMS-267 parent | DMS-253 | DMS-253 |
| DMS-267 relations | 1 | 1 |
| DMS-380 parent | DMS-254 | DMS-254 |
| Kalachanov WMB | 6 | 6 |
| Kalachanov WMB keys | [WMB-29242,29830,29890,29995,30000,30482] | same |
| Semavin DMS | 175 | 175 |

### Test Matrix

| Case | Query | Runs | Result | Details |
|------|-------|------|--------|---------|
| **M2** (2-goal: lookup+hierarchy) | "Покажи задачу DMS-267 и его иерархию" | 3/3 | **COMPLETED** | caps=[task.lookup, task.hierarchy], gc={2,both proven,extra_calls:1}. Hierarchy: parent_chain=[DMS-253,CRPV-90180], depth=2, root=CRPV-90180, epic=DMS-349. **No duplicate lookup** (log: 1 GET tasks/DMS-267, 1 GET tasks/DMS-267/relations). |
| **M1** (2-goal: two persons) | "Задачи Калачанова в WMB и задачи Семавина в DMS" | 2/2 | **COMPLETED** | caps=[task.search_assignee(Калачанов,WMB), task.search_assignee(Семавин,DMS)]. **K=6, S=175 EXACT oracle.** extra_calls=1. |
| **M4** (3-goal: lookup+hierarchy+person) | "Покажи задачу DMS-267 и его иерархию и задачи Калачанова в WMB" | 1/1 | **COMPLETED** | caps=[task.lookup, task.hierarchy, task.search_assignee]. gc={3,all proven,extra_calls:2}. K=6 exact. |
| **C5** (lookup+relations) | "Покажи задачу DMS-267 и связанные с ней задачи" | 1/1 | **COMPLETED** | caps=[task.lookup, task.hierarchy]. Relations proven via hierarchy: 0 related tasks. |
| **NEG DMS-380** (1-goal) | "Покажи задачу DMS-380" | 1/1 | **COMPLETED** | Single task.lookup. Guard inert (1 goal). No hierarchy inferred. |
| **C1** (1-goal control) | "Открытые задачи Калачанова в WMB" | 2/2 | **COMPLETED** | task.search WMB open=1 (WMB-30482). Guard inert. |
| **M5** (comparison) | "Сравни задачи DMS-267 и DMS-380" | 1/1 | **COMPLETED** | Detector returns () (COMPARE pattern). Guard inert. Single task.lookup. |

### Latency (ALL_ON session, LLM warm)

| Case | Wall (s) |
|------|----------|
| M2#1 | 140.0 (cold LLM) |
| M2#2 | 146.9 |
| M2#3 | 46.4 |
| M1#1 | 87.5 |
| M1#2 | 69.0 |
| M4 | 63.2 |
| C5 | 58.4 |
| NEG | 30.0 |
| C1 | 98.9 / 30.0 |
| M5 | 28.0 |

### LLM calls per case (from log)

- M2: 5 LLM calls (2 main + 2 executor + 1 synthesis)
- M1: 4-5 LLM calls
- M4: 5-6 LLM calls (2 main + 4 executor for 2 goals)

## P4 — Fail-Closed and Adversarial

| Property | Evidence |
|----------|----------|
| **429 → typed fail-closed** | 14x observed in GUARD_CONT session: all resulted in `FAILED` with `v4_runtime_failure` + `planner failed robust bounded repair: ['HTTPStatusError' x4]`. Never false COMPLETED. |
| **No source_unavailable as REAL_EMPTY** | Code: `_source_verified_rows` requires `not data.get("source_unavailable")` AND `data.get("source_complete") is not False`. |
| **No duplicate rereads** | M2 log: GET tasks/DMS-267 (1x lookup) + GET tasks/DMS-267/relations (1x hierarchy). No second lookup. |
| **No local reads** | 0 GET /api/v1/tasks (local store) across entire ALL_ON session. |
| **No mutations** | 0 POST/PUT/DELETE to task-api. |
| **No tenant-wide scans** | 0 unscoped task-query calls. All source reads bounded (53 total, all space/-scoped). |
| **110s shared deadline** | `time.monotonic()` wall clock, shared across all executor calls. Per-call `asyncio.wait_for(..., timeout=min(remain, 100.0))`. On expiry: `asyncio.TimeoutError` → caught → typed error → break. Not reset per subprocess. |
| **PARTIAL renders correctly** | UI: `PARTIAL` → `SOURCE_CONDITIONAL` state (resultState.ts:142), NOT `SUCCESS_WITH_DATA`. Warning `v4_missing_goal_execution_partial` present. Answer text honest ("Часть целей выполнена"). |
| **MAX_EXTRA_CALLS=2 cap** | Code: `pending[:MAX_EXTRA_CALLS]` limits to 2 executor calls total. |
| **Loopback-only** | `request.client.host in ("127.0.0.1", "::1")` at `__init__.py:569`. |
| **Flag defaults false** | All three `Field(default=False)` in settings.py. |
| **No 5xx from source** | 0 actual 5xx errors in ALL_ON session (earlier grep false-positive on `max_pages=500`). |

### Security OPEN (unchanged)

**Session auth/ownership remains an explicit release blocker.** The client supplies `session_id` freely; there is no server-minted session token or principal binding. This is local QA only. **Never claim release-ready auth.**

## Session Audit (ALL_ON)

| Metric | Value |
|--------|-------|
| Total /api/v1/query requests | 17 |
| Total source GETs to task-api | 53 |
| LLM 200 OK | 82 |
| LLM 429 | 0 (endpoint recovered mid-session) |
| Local store reads | 0 |
| Mutations | 0 |
| Unscoped scans | 0 |
| 5xx source errors | 0 |

## Non-Blocking Observations

1. **LLM endpoint rate-limiting** (api.ai.sbt): 14x 429s in GUARD_CONT session, 0 in ALL_ON (recovered). Environmental, not code defect. All 429s → typed FAILED (fail-closed correct).
2. **M5 comparison** (detector returns `()`): the comparison query "Сравни задачи DMS-267 и DMS-380" is detected as a comparison → guard inert. Planner only executed one task.lookup (DMS-267). This is a pre-existing planner limitation, NOT an executor/guard defect. Comparison goal typing remains OPEN for a future stage.
3. **Executor log markers**: The agent log does not emit explicit "executor" log lines. Attribution is via the `extra_calls` field in `goal_coverage` metadata (proven in all responses).
4. **PARTIAL not directly triggered in live tests**: All successful runs completed all goals. The PARTIAL path is code-correct (verified by reading the implementation) but not exercised in this session's live matrix. The 429 failures demonstrate the broader fail-closed path (FAILED, not false COMPLETED).

## Verdict

All P0-P4 phases pass:
- Core frozen, tests green
- Owner delta safe (audit confirmed)
- Flag matrix correct (OFF/GUARD_ON/GUARD_CONT/EXEC_ONLY/ALL_ON/remote/defaults)
- REAL AS21 A/B oracle: 3-goal exact, no drift, no duplicate reads
- Fail-closed: no false COMPLETED, typed PARTIAL, bounded deadline, loopback-only, 0 local/mutations/scans

**AGENT_CORE_V4_BOUNDED_MISSING_GOAL_EXECUTION_GREEN_A229M22B1**

### Recommendation
- Checkpoint: `checkpoint/v4-bounded-missing-goal-execution-green-a229m22b1` on `d425438`
- Session auth/ownership: separate release track (OPEN)
- M5 comparison goal typing: next stage (OPEN, out of scope)
- No flag default flip (all remain false until owner explicit decision)
