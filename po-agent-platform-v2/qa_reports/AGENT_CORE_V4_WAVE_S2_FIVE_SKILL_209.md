# AGENT_CORE_V4_WAVE_S2_FIVE_SKILL_209

**Assignment:** 209 — Wave S2 five-skill QA (cycle_time, lead_time, carryover, predictability, risk_queue)
**Date:** 2026-09-24
**Role:** QA/adversarial + service-operator only (no production/test/config edits)
**Branch:** `feat/core8-real-query-hardening-v2`

| Field | Value |
|---|---|
| START_HEAD | `a417097dee9045217465b4374bd9f5281e945131` (docs handoff) |
| Stable rollback checkpoint (A208B) | `2e284fd` |
| Owner S2 commits | `186c1c6` (wave_s2.py, 424 lines), `54bfe29` (tests, 166 lines) |
| Agent under test | port 8212, PID 6813, HEAD `a417097` |
| task-api | 8241 (system python3, SSE, 48 tools) |
| MCP-SWTR | 3000 |
| UI | 5176 (vite; 5175 held by stale listener) |

## VERDICT

**AGENT_CORE_V4_WAVE_S2_FIVE_SKILL_RED** — classification `RED_SOURCE_TIMESTAMP_PLUMBING` (fixable in our code, not source-conditional)

Two blocking defects share one root cause: the task-api sprint route does not expose per-task `created_at`/`deadline`, the agent adapter substitutes `datetime.now()` (naive), and the new wave_s2 plugin both trips over it (cycle/lead → deterministic 100% FAILED) and silently consumes it (risk_queue → aging signal zeroed). Per the first-new-defect rule: **STOP. No Wave S3, no new skills until re-gated.**

---

## P0 — Diff audit (A208B `2e284fd` → `a417097`): CLEAN

`git diff --stat 2e284fd..a417097` = 7 files; code is only:
- `po-agent-platform-v2/src/po_agent/harness/v4_plugins/wave_s2.py` (new, 424 lines)
- `po-agent-platform-v2/tests/test_agent_core_v4_wave_s2.py` (new, 166 lines)
- docs (handoff, next-action, evolution plan, DoD lock)

No Agent Core / planner / runtime / adapter / task-api changes. All 5 skills are registry-discovered via the plugin surface (no core routing branches). No hardcoded person/task/sprint IDs in the plugin. No local `/api/v1/tasks` or fake source references. Completion contract + UIContract present for all 5.

## P1 — Unit suites: 146 passed / 1 failed (test-logic bug, not production)

`test_agent_core_v4_wave_s2.py` + wave_s1 + plugin registry + full V4 suites: **146 passed, 1 failed**.

Sole failure `test_risk_queue_ranks_tasks_not_people`: asserts `"employee" not in formula.lower()`, but the production formula string is `"blocked first, then overdue_days desc, then age_days desc; no employee scoring"` — it legitimately contains the word "employee". All substantive ranking assertions in that test pass (count=2, blocked-first order, second rank). **Not a production defect** — owner should change the assertion (e.g. match on the sort keys, not a substring of the formula sentence).

## P2 — Fresh oracle (live REAL AS21, DMS space)

| Fact | Value |
|---|---|
| DMS-SPRNT-3 (IN_PROGRESS, 2026-09-13 → 2026-09-27) | 68 tasks, complete, `has_next=false` |
| DMS-SPRNT-2 (FINISH) | 17 tasks, complete (A184 said 39 — live source drift) |
| Intersection (carryover) | **0** |
| Completed SPRNT-3 tasks with workflow history | 17 (e.g. DMS-335: 3 transitions 2026-08-03T06:37Z → 2026-09-23T13:03Z) |
| Sprint metadata fields | code, name, status, start_at, finish_at, deleted — **no committed/baseline/planned fields** |
| Open SPRNT-3 tasks with source `created_at` (task-query route) | 51/51 |
| Open SPRNT-3 tasks age ≥ 14d | **37** (max 161d: DMS-64; incl. DMS-86 148d, DMS-93 138d, …) |
| Blocked (canonical) | 2: DMS-352, DMS-379 |

**Root-cause proof (in-process, production adapter stack, live source):**
- `GET /sprints/DMS-SPRNT-3/tasks?complete=true` rows: **0/68** carry `created_at` (top-level or in `source_data`); adapter provenance flag `_canonical_created_at_from_source = False` on all 68.
- Adapter `task_api.py:395-397` then substitutes `created_at = datetime.now()` (**naive**).
- History timestamps are tz-aware UTC.
- Direct handler calls: `build_sprint_cycle_time` → **`TypeError: can't compare offset-naive and offset-aware datetimes`** at `wave_s2.py:61` (`terminal_transition < task.created_at`); `build_sprint_lead_time` → same. Even if tz were normalized, `terminal < now()` would fire the "inconsistent timeline" branch — the skill can never produce an aggregate.

## P3 — sprint.cycle_time: RED (4/4 FAILED, deterministic)

| Form | Runs | Result |
|---|---|---|
| explicit `cycle time спринта DMS-SPRNT-3` | 2 | FAILED (22.2s, 23.6s) |
| period `cycle time сентябрьского спринта DMS` | 1 | FAILED (13.2s) |
| current `cycle time текущего спринта DMS` | 1 | FAILED (20.5s) |

Agent log proves the capability executed: sprint route 200 + full history fan-out (17/17 `/history` 200 OK) → then FAILED. No fabrication, no premature completion (fail-closed). But the spec P3 requirement (exact per-task cycle aggregation from source history) is **structurally unmet** — the source data exists (history is complete and authoritative); the defect is the created_at plumb described in P2. **RED, fixable in our code.**

## P4 — sprint.lead_time: RED (4/4 FAILED, same signature)

Identical matrix (explicit ×2, period, current): 4/4 FAILED (22.3s, 25.4s, 13.5s, 31.0s), identical root cause (`wave_s2.py:69` computes `lead_hours` from the now()-fallback `created_at`; the `:61` guard trips first). **RED, same defect as D-A209-1.**

## D-A209-1 (BLOCKING)

**Sprint tasks carry no source `created_at`/`deadline` through the task-api sprint route; the adapter's `datetime.now()` (naive) fallback makes both `sprint.cycle_time` and `sprint.lead_time` fail 100% deterministically (aware-vs-naive `TypeError` at the `wave_s2.py:61` guard).**

Chain:
1. `task-api/app/routers/swtr_read.py` sprint route (`get_sprint_tasks` MCP tool) canonical rows expose only `source_id, title, status, source, source_data, sprint_id, project_space` — no timestamps. Contrast: the task-query route (`swtr_query.py:189-199`) already applies the `created_at/createdAt`, `updated_at/updatedAt`, `deadline/dueDate` alias bridge.
2. `po-agent-platform-v2/src/po_agent/adapters/task_api.py:395-397` falls back to `datetime.now()` (naive) and sets `_canonical_created_at_from_source=False`.
3. `wave_s2.py:61` compares tz-aware history timestamps with the naive fallback → `TypeError`; even tz-normalized, `terminal < now` → "inconsistent timeline".

**Minimal generic fix (owner):** expose `created_at`/`updated_at`/`deadline` in the sprint-task route (same alias-bridge pattern as task-query, or enrich via the bounded sprint-constraint TQL path per A185 B1); and in wave_s2 fail closed on `_canonical_created_at_from_source is False` with an explicit "sprint task rows lack source timestamps" message instead of the misleading timeline error. Data availability proven: 51/51 open SPRNT-3 tasks have source `created_at` via task-query.

## P5 — sprint.carryover: GREEN (3/3 exact vs oracle)

| Form | Result |
|---|---|
| explicit ×2 | COMPLETED, prev=DMS-SPRNT-2 (auto from sprint dates), carryover=0, current_total=68, previous_total=17 |
| current `carryover текущего спринта DMS` | COMPLETED, identical |

Intersection oracle = 0 → **exact match 3/3**. No title/fuzzy matching used (key intersection per spec). Auto-previous resolution correct (SPRNT-2 finish 2026-08-30 < SPRNT-3 start 2026-09-13).

## P6 — sprint.predictability: SOURCE_CONDITIONAL (per spec, acceptable)

3/3 typed fail-closed: `V4CapabilityUnavailable: sprint.predictability requires committed/baseline scope from REAL AS21; current scope is not a substitute` → UI answer "Необходимая возможность не подтверждена источником данных и не выполняется." Sprint metadata has no committed/baseline/planned field (verified live). Spec P6 explicitly allows SOURCE_CONDITIONAL here. **Not RED.** Re-gate when a baseline source exists.

## P7 — sprint.risk_queue: D-A209-2 (BLOCKING) — silent aging truncation

Agent runs: 2/2 COMPLETED with queue = [DMS-352, DMS-379] (both blocked), `age_days=0` and `overdue_days=0` on every row, no warning in the answer.

Oracle: **37 open SPRNT-3 tasks are ≥14d old** (161d down to 14d). The queue is missing all **35 aging-only tasks**. `age_days` is reported as 0 because the adapter fallback `created_at=now()` makes `(now - created_at).days = 0` for every row — the exact antipattern A197 eliminated for `task.aging` ("adapter fallback timestamp interpreted as a source fact"); here the `_canonical_created_at_from_source=False` flag is ignored by `wave_s2.py:305-306`. `overdue_days` is dead for the same reason (no `deadline` in sprint rows).

**Severity: silent inaccuracy (COMPLETED with wrong/incomplete data and no warning) — worse category than D-A209-1's fail-closed.** The blocked subset itself is correct: exactly matches `sprint.health` blocked=2 and `task.search` blocked (cross-check 2/2, same keys DMS-352/DMS-379).

**Minimal generic fix (owner):** in wave_s2 risk_queue, gate the aging/overdue signals on source provenance (`_canonical_created_at_from_source`, and deadline presence); when absent, exclude those reasons and state the limitation explicitly in the answer/warnings (A207 F1 pattern) — or, better, fix the route per D-A209-1 so the signals are real.

## P8 — Resolution forms (covered inside P3–P7 batches)

Period ("сентябрьского спринта DMS") and current ("текущего спринта DMS") forms resolved to DMS-SPRNT-3 correctly for cycle/lead/carryover/predictability/risk. All failures occur at the capability layer, never at routing/resolution — no planner defect.

## P9 — Browser C (UI 5176, Playwright chromium, 6/6)

| Case | Status | Notes |
|---|---|---|
| C1 cycle explicit | FAILED | generic safe message "не смог безопасно завершить траекторию", no stack/contract leak |
| C2 lead explicit | FAILED | same |
| C3 carryover current | COMPLETED | 0/68/17, prev DMS-SPRNT-2, exact |
| C4 predictability | FAILED | typed "возможность не подтверждена источником" |
| C5 risk current | COMPLETED | 2 rows (DMS-352, DMS-379); **no aging caveat shown** (D-A209-2 visible in UI) |
| C6 wip retained | COMPLETED | 30/68 (A208B retained) |

`leak=false` in all 6 (no session_context/clarification_id/contract/traceback in visible payload); UI session preserved (`ui-d55abd6f…`). Screenshots: `qa_209_browser_c/C1…C6.png` + `results.json`. Note: 5175 was held by a stale IPv6-only listener; fresh vite instance served on **5176** (proxy → 8212).

## P10 — Retained regression (A207/A208B checkpoint): ALL GREEN

| Check | Result |
|---|---|
| sprint.health DMS-SPRNT-3 | 68 total / 17 completed (25%) / 51 active / blocked 2 — matches live drift |
| blocked in sprint | 2: DMS-352, DMS-379 (exact) |
| wip | 30/68 (A208B exact) |
| velocity | 17 tasks/sprint (A208B exact) |
| throughput | 1.689 completed/calendar-day (A208B 1.702 — time drift) |
| scope | 68 |
| task.lookup DMS-380 | COMPLETED (mTLS/SSL auth title) |
| task.history DMS-380 | 4 transitions, labels render ("Закрыт") — A206B retained |
| time-in-status DMS-380 | Открыт 0,0h → Closed zero-span at closure — A206B retained |
| person+status "Открытые задачи Жданова в DMS" | 2: [DMS-371, DMS-1] (A208B exact) |
| attachments WMB-30000 | 5 Excel (A193/A207 exact) |

No regression from the S2 plugin wave.

## P11 — Source/local/perf audit

- **Local `/api/v1/tasks` reads from agent: 0** (agent log, whole session).
- Live swtr-read calls: 294 (sprints 56, tasks 212, spaces 17, assignees 1, task-query 1, health 7); history fan-out 206; LLM 167 calls, no 429 storm this session.
- `GET /api/v1/swtr-read/versions` → HTTP 400 (MCP `search_versions` still broken; A204–A208 lineage) → `release.search` remains **SOURCE_CONDITIONAL**.
- Perf: all agent queries 6.4–49.6s; no 300s client timeouts; cycle/lead fail after bounded history fan-out (17 calls, semaphore 8).

## Findings (non-blocking)

- **F1 (test-logic bug):** `test_risk_queue_ranks_tasks_not_people` substring assertion on the formula sentence (see P1). Owner one-liner.
- **F2 (misleading error text):** when provenance flags are false, cycle/lead raise `TypeError`/timeline errors instead of "sprint task rows lack source timestamps" — fix alongside D-A209-1.
- **F3 (drift, not defect):** DMS-SPRNT-2 membership 39 (A184) → 17 now; DMS-380 history 6 → 4 events. Live source drift, routes complete (`has_next=false`).
- **F4:** 5175 stale listener (IPv6-only, refuses 127.0.0.1); harmless, cleaned up by owner at convenience.

## Owner fix bundle (proposed, not implemented — QA did not touch production)

1. task-api sprint-task route: expose `created_at`/`updated_at`/`deadline` (alias bridge like `swtr_query.py:189-199`, or bounded TQL enrichment per A185 B1).
2. wave_s2 `_completed_history_metrics`: fail closed with an explicit source-timestamp message when `_canonical_created_at_from_source is False` (and normalize tz-awareness before comparing).
3. wave_s2 risk_queue: gate aging/overdue reasons on source provenance; state the limitation when absent.
4. Fix `test_risk_queue_ranks_tasks_not_people` assertion; add regression tests: cycle/lead exact on a fixture with source-backed created_at, risk_queue excludes aging when provenance absent.

**Then: full A209 re-gate (P3 10x + P4 10x + P7 aging-parity vs oracle + retained).**

## Services left running

UI 5176 (vite, PID 12803), agent 8212 (PID 6813 @ a417097), task-api 8241 (system python3, SSE 48 tools), MCP-SWTR 3000.

## QA artifacts

`/tmp/qa209_p34.jsonl`, `/tmp/qa209_p567.jsonl`, `/tmp/qa209_p10.jsonl`, `/tmp/qa209_carryover_oracle.json`, `/tmp/qa209_aging_oracle.json`, `/tmp/qa209_agent.log`, `qa_209_browser_c/`.

**Recommendation: STOP. Fix D-A209-1 + D-A209-2 (single root cause), then re-gate. Do not start Wave S3.**
