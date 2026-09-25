# A215G — Member Time Accounting Gate (member.time_spent / member.worklogs / member.utilization_actual)

**Verdict: `MEMBER_TIME_ACCOUNTING_GREEN_A215G`**

- **START_HEAD:** `b64b3a7a2baec9cb47709b0545012172ddbd60c1`
- **Owner implementation:** `b5fa16f` (feat: member sprint time accounting and utilization, plugin `builtin.time_accounting.member`) + `fad2580` (tests); docs `e4a7693` (freeze A215F2 GREEN + gate), `b64b3a7` (spec)
- **Baseline:** A215F2 GREEN (checkpoint `checkpoint/v4-actual-time-green-a215f2`)
- **Date:** 2026-09-25
- **Services:** agent 8212 (PID 55530 @ b64b3a7), task-api 8241 (PID 81954), MCP-SWTR 3000 (PID 29268), vite UI 5175 (PID 47416, proxy → 8212), LLM endpoint healthy

---

## A215G intent: CLOSED — the original manual-test phrase completes end-to-end in one trajectory

"трудозатраты Семавина по задачам в сентябрьском спринте DMS" → COMPLETED `runtime_contract` in a single trajectory:
`space.resolve(DMS) → sprint.search(period=сентябрь → DMS-SPRNT-3) → member.resolve(Семавин → Semavin.M.M) → member.time_spent(Semavin.M.M, DMS, DMS-SPRNT-3) → deterministic READY`.
Final answer is the aggregation itself (64 ч, 8 списаний, task/type/date breakdown) — **no intermediate task-list final answer, no "готов продолжить", no confirmation before bounded fan-out** (verified on all 3 P3 phrasings).

## Phase 0 — architecture invariant: PASS

- `git diff d177fae..b64b3a7 --name-only`: `GIGACODE_NEXT_ACTION.md`, `V4_DOD_LOCK.md`, `v4_plugins/time_accounting_member.py` (new, +291), `tests/test_agent_core_v4_time_accounting_member.py` (new, +164). **0 lines** in Agent Core/planner/runtime/session-context/task-api.
- Plugin reuses proven seams from `time_accounting_aggregate` (`_bounded_worklogs` semaphore-8, `_sprint_context`, `_aggregate`, `_within`) — no new source surface.
- Attribution is by **worklog author `user.externalId`** only (`attribution: worklog_author_external_id` in every payload); never by current task assignee.
- Registry: 9 plugins, 56 skills; all 3 member skills discovered with CompletionContract (scalar REAL_EMPTY-safe keys, `covers_resolved_constraints=True`) + UIContract.
- dummy-55 extensibility: green (plugin registry suite within Phase 1).

## Phase 1 — tests: PASS

- Focused (member + aggregate + task + batch2): **25/25 passed** (incl. 6 new member tests with zero-worklog completion safety).
- `tests/test_agent_core_v4*.py tests/test_v4*.py`: **185/185 passed** (179 A215F2 + 6 new).

## Phase 2 — DMS Semavin oracle (independent): 

Authoritative: complete DMS-SPRNT-3 membership (72 tasks, complete=true) + period 2026-09-13 → 2026-09-27 (15 cal days) + bounded per-task worklogs (concurrency 8) + in-period filter + author filter `user.externalId == Semavin.M.M`:

| Field | Oracle |
|---|---|
| total_hours | **64.0** |
| worklog_count | **8** |
| by_task | DMS-411 24.0, DMS-408 16.0, DMS-267 8.0, DMS-390 8.0, DMS-403 8.0 |
| by_type | 4Р_Тестирование компонента 64.0 |
| by_date | 8 dates × 8.0 (09-14…09-19, 09-21, 09-22) |

Cross-check: matches A215F2 team oracle `by_member["Semavin.M.M"] = 64.0`.

## Phase 3 — member.time_spent NL gate: 3/3 EXACT

| Case | Trajectory | Result |
|---|---|---|
| "трудозатраты Семавина по задачам в сентябрьском спринте DMS" | space.resolve → sprint.search → member.resolve → member.time_spent (6 turns) | EXACT: 64.0h/8, by_task/by_type/by_date identical, `attribution=worklog_author_external_id`, `runtime_contract` |
| "сколько Семавин списал в DMS-SPRNT-3" | sprint.resolve → member.resolve → member.time_spent (5 turns) | EXACT (space legitimately derived from canonical sprint id; output `space=DMS` exact) |
| "фактические трудозатраты Семавина в текущем спринте DMS" | space.resolve → sprint.current → member.resolve → member.time_spent (6 turns) | EXACT |

No intermediate task-list final answers, no continuation prompts, no confirmation asks in any answer. (Note: the first raw batch right after agent restart hit a warm-up window and failed closed 3/3 in 0–1 turns; every re-probe, including the official batch, passed — see F3.)

## Phase 4 — member.worklogs: 3/3 EXACT + cross-assignee attribution proven live

- "покажи список списаний Семавина в DMS-SPRNT-3" → `member.worklogs` **EXACT**: 8 entries, 64.0h, per-entry `id/task_key/date/duration_hours/work_type_code/work_type_name/comment`, by_task/by_date identical to oracle.
- "кто и когда списывал время — списания Семавина в DMS-SPRNT-3" → `member.worklogs` **EXACT** (same 8 entries).
- **Cross-assignee proof (live):** "список списаний Гальцова в DMS-SPRNT-3" → `member.worklogs` **EXACT**: 5 entries, 40.0h, all on **DMS-389, which is currently UNASSIGNED** in the live source — the hours are attributed to Galtsov.A.A purely via worklog author. (For Semavin, all 5 of his tasks happen to be currently assigned to him, so the natural cross-assignee live case is Galtsov/DMS-389; the same author-filter mechanism is unit-covered by the owner's "Other.User" filter test.)
- Routing note (F1): the spec phrasing "покажи списания Семавина в сентябрьском спринте DMS" routed to `member.time_spent` (aggregate, exact data) rather than `member.worklogs`; explicit list phrasings ("список списаний", "кто и когда") route to `member.worklogs`. Pre-existing planner-routing class, data-accurate in both.

## Phase 5 — member.utilization_actual: 2/2 EXACT

- "фактическая утилизация Семавина в спринте DMS-SPRNT-3" / "…в сентябрьском спринте DMS": both COMPLETED `runtime_contract`.
- Exact formula: **actual 64.0h / capacity 70.65h = 90.6%**; `calendar_days=15`; denominator independently verified (15 × 247 × 8 × 0.87 / 365 = 70.65).
- Provenance: `numerator_source=REAL_AS21_WORKLOGS`, `denominator_source=OWNER_POLICY`, `source=REAL_AS21_PLUS_OWNER_POLICY`, `attribution=worklog_author_external_id`, policy metadata (OWNER_POLICY, 247 days, policy_id), warning `capacity_denominator_owner_policy_average_2026`. No estimate/task-count substitution.

## Phase 6 — insufficient scope ("трудозатраты Семавина за 2 недели"): PASS

- Typed `NEEDS_CLARIFICATION`, non-null `clarification_id`, **0 capability calls** (no tenant scan, no assignment inference, no missing-capability claim).
- Question explicitly reasons: "«2 недели» — это скользящий период, который не привязан к конкретному спринту, а работа с worklogs требует авторитетного ограниченного контекста (space + sprint_id)".
- UI-style continuation (`session_id` + `clarification_id`, answer "DMS, сентябрьский спринт") → COMPLETED `runtime_contract`, EXACT 64.0h/8.

## Phase 7 — continuation safety: PASS

1. "трудозатраты Семавина по задачам в сентябрьском спринте DMS" → COMPLETED EXACT (first request already fulfills the goal — manual-test gap closed).
2. "Продолжи" (same session) → typed `NEEDS_CLARIFICATION` ("что именно продолжить… задачи спринта, загрузка, время, health, WIP"), **0 capability calls**, no stale intermediate observations resurrected, no fabricated aggregation, no generic failure.

## Phase 8 — Browser C: 2/2 PASS

- C1 "трудозатраты Семавина по задачам в сентябрьском спринте DMS" → COMPLETED `runtime_contract`, `member.time_spent`, UI shows 64h total + task breakdown (DMS-411/408) + type, 56.5s.
- C2 "покажи список списаний Семавина в DMS-SPRNT-3" → COMPLETED `runtime_contract`, `member.worklogs`, UI shows dated 8h entries + total, 43.1s.
- Both: no generic ERROR, no fake continuation prompt, no confirmation ask, no session/trace leaks. Screenshots: `qa_215g_browser_c/`.

## Phase 9 — retained regression: PASS

| Item | Result |
|---|---|
| sprint.time_spent DMS (A215F2) | EXACT 428.5h / 65 / 72 tasks |
| team.time_spent DMS (A215F2) | EXACT 428.5h / 65 |
| DMS-380 task.time_spent | EXACT 48.0h / 6 entries (`time_spent_hours=48.0`, complete=true; route parity) |
| team.capacity source-estimate guard | retained typed fail-closed |
| release.search WMB | EXACT 24Q1/24Q2/25Q1 |
| release.health | honest identity-only + "metrics not in source" (A213/A214 state retained, no fabrication) |
| dummy-55 | green (registry suite) |

## Audit: PASS

Agent log over the session:
- local factual `GET /api/v1/tasks` reads: **0**
- mutations (POST to swtr-read): **0**
- unscoped tenant-wide scans: **0** (0 unscoped task-query; only scoped versions calls for release paths)
- worklog route calls: **1731**, 1730×200 + **1 transient 502** (self-recovered in seconds; adapter maps 5xx → typed `AS21SourceUnavailable` → fail-closed, no partial aggregate)
- bounded per-task fan-out: code-enforced `asyncio.Semaphore(8)`; max 10 completions in any 500 ms window (completion-timestamp clustering artifact, not in-flight)
- identity resolution via source-backed `assignees/resolve` (Semavin 17, Galtsov 4) — no local roster truth

## Non-blocking findings

- **F1 (routing):** bare "покажи списания …" routes to `member.time_spent` (exact aggregate) rather than `member.worklogs` (itemized); explicit list phrasings route correctly. Pre-existing planner-routing class; both outcomes data-accurate.
- **F2 (source blip):** one transient 502 on the work-logs route mid-session; self-recovered; agent path is fail-closed by adapter design.
- **F3 (warm-up):** the first 3 live queries right after agent restart failed closed in 0–1 turns (warm-up window); all subsequent runs clean — same transient class as A212; not a code defect (fail-closed, zero source calls, zero fabrication).
- **F4 (cid-only continuation):** clarification continuation without `session_id` re-clarifies — the established contract requires session-scoped state (UI always sends both); matches A213 behavior.

## Services left running

UI 5175 (PID 47416), agent 8212 (PID 55530 @ b64b3a7), task-api 8241 (PID 81954), MCP-SWTR 3000 (PID 29268).

## Recommendation

**GREEN.** Recommend: immutable member-time-accounting checkpoint (A215D+E+F2+G bundle), then resume **A216 / Batch 3 QA** per the spec.
