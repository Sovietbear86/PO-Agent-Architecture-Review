# A230R3.1 — Independent QA on owner's additive person/date worklog implementation

**Verdict: AGENT_CORE_V4_WORKLOG_PERIOD_GREEN**

**TESTED_HEAD:** `5d27aca060e293949fb4d3695c7d67921c07da1d`
**Branch:** `feat/core8-real-query-hardening-v2`
**Role:** Strict independent QA — no production/test/Core/MCP/config/frontend edits, no auto-fixes, no source writes.
**Date:** 2026-10-24

---

## Summary

Owner's additive person/date worklog capability is **GREEN**. All P0–P2 gates pass. The new
`member.worklogs_period` skill returns REAL AS21 worklogs attributed to the worklog **author**
(not task assignee) over an inclusive logged-on date range, with fail-closed source semantics.
The 4-layer chain (MCP → Task API → adapter → plugin) returns **exact parity** against an
independent bounded REAL AS21 oracle. Core V4 is unchanged (6/6). No regressions.

---

## P0 — Provenance & security

- **Core V4 6/6 IDENTICAL** to checkpoint `6fb335d` (agent_core_v4.py, agent_core_v4_robust.py,
  agent_core_v4_reliable.py, agent_core_v4_completion.py, v4_plugin_registry.py, llm/real.py).
- **Delta scope (adbf5b9..5d27aca)** — purely additive, no Core/frontend/config:
  - `mcp-swtr/mcp_server.py` — new tool `get_work_report_filter` (POST `/rest/api/timesheet/v1/report`).
  - `task-api/app/routers/swtr_read.py` — new `GET /api/v1/swtr-read/work-logs/report`.
  - `po-agent-platform-v2/src/po_agent/adapters/task_api.py` — new `get_member_worklogs_period` (capped 20×50).
  - `po-agent-platform-v2/src/po_agent/harness/v4_plugins/time_accounting_period.py` — new plugin `builtin.time_accounting.period`, skill+capability `member.worklogs_period`, relative-weeks parser.
  - 2 test files + 2 docs.
- **Security (P0.2):** MCP tool requires single canonical author externalId (`[A-Za-z0-9_.@-]{1,120}`),
  inclusive ordered dates ≤366d and not in future, bounded page(0–99)/size(1–100); optional
  space/unit validated; **no empty tenant-wide filter, no per-task fanout**. Task API re-validates and
  fails closed (400/502). No new personal data in source (tests use synthetic `Ivanov.I.I`; the only real
  name in the delta is in the QA spec text itself).
- **Registry discovery:** `discover_v4_plugins()` clean — 14 plugins, 75 capabilities, 73 skills;
  `member.worklogs_period` registered with args `{member_login, period, date_from, date_to, space, unit}`;
  all invariants (capability/binding match, skill→capability subset, UI→skill) pass.
- **P0.3 duration shape VERIFIED = MILLIS** at the raw source: MCP `get_work_report_filter` returns
  `temporalUnit: MILLIS` on all rows; `_duration_hours` converts `time` (ms)→hours only when
  `temporalUnit == MILLIS`, else returns `None` → Task API fails closed (502). No invented conversion.
- **P0.4 invokable as documented:** MCP tool registry increased **48 → 49** after restart; Task API
  route returns 422 (validation) for missing params (not 404).

## P1 — Targeted tests, oracle, planner, negatives

### P1a — tests
- New `test_swtr_person_worklogs_report.py`: **12 passed** (happy path, 400 pre-MCP, 502 source-mismatch,
  has_next≠complete-zero).
- New `test_member_worklogs_period.py`: **12 passed** (relative/explicit dates, typed clarifications,
  complete-zero, incomplete-rejection).
- Existing SWTR facade (task-api): **51 passed**. Existing time-accounting (po-agent): **18 passed**.

### P1b — negative paths (live, before source)
| input | result |
|-------|--------|
| missing `user` / missing `to` | 422 (required field) |
| blank user / `bad user` (space) | 400 "Canonical worklog author externalId is required" |
| future `to` / unordered / >366 days | 400 "ordered, <=366 days, not in future" |
| bad date format (`01.10.2026`) | 400 "Valid YYYY-MM-DD" |
| page>99 / size>100 | 422 (bounds) |
| valid control | 200, count=14 |

502 source-mismatch paths (author mismatch, date out of interval, missing duration, missing/ mismatched
pagination metadata) are **unit-proven** (cannot be forced against the consistent live source).

### P1c — bounded REAL AS21 oracle A/B (author Garanin.R.V, 2026-10-01→24, DMS)
Independent bounded read, not hardcoded. **Exact parity across all 4 layers:**

| Layer | count | hours | complete | source |
|-------|-------|-------|----------|--------|
| MCP `get_work_report_filter` (raw) | 14 | 112.0 (raw ms 403200000, `temporalUnit=MILLIS`) | hasNext=False | REAL |
| Task API `/work-logs/report` | 14 | 112.0 | true | REAL_AS21 |
| Adapter `get_member_worklogs_period` | 14 | 112.0 (pages_read=1) | true | REAL_AS21 |
| Plugin `member.worklogs_period` (via agent) | 14 | 112.0 | true | REAL_AS21 |

All rows author = `Garanin.R.V`; dates 2026-10-01..16 in-range; per-day 8.0h on 14 working days.

### P1d — planner trajectory (relative + explicit)
- Explicit `...в DMS с 01.10.2026 по 24.10.2026` → **COMPLETED**, `runtime_contract`,
  `member.resolve` → `member.worklogs_period(date_from=2026-10-01, date_to=2026-10-24, space=DMS)`
  → count=14, total=112.0, 15 evidence.
- Relative `покажи списания Гаранина за последние 2 недели` (standalone, no space) → **COMPLETED**,
  `runtime_contract`, `member.worklogs_period(period="за последние 2 недели")` → count=5, total=40.0,
  period 11.10..24.10 (5 working days × 8h). Matches source.
- Planner selects `member.worklogs_period` — **not** `task.search_created`, **not** sprint-only
  `member.worklogs`; resolves person identity; no generic task-filter clarification.

### P1e — true zero + outage
- True source-backed zero (Garanin 10.10–11.10, weekend with no worklogs): Task API count=0
  complete=True; agent **COMPLETED**, count=0, total=0, complete=True, "Результат подтверждён полным
  отчётом AS21" — zero only when pagination complete.
- Source outage → `V4CapabilityUnavailable` (typed failure), **not** a fabricated zero.

## P2 — Full regression

- **Full V4 suite (po-agent):** **297 passed**.
- **Task API suite:** 25 failed / 115 passed. Baseline at parent `adbf5b9` (read-only worktree):
  **25 failed / 103 passed** → **0 new failures, +12 new passing** (the new test file). The 25 failures
  are pre-existing local-store tests (test_api/test_repository/test_service/test_task_api_freshness),
  unrelated to the SWTR delta.
- **Frontend build (tsc + vite):** GREEN (exit 0). The delta added only a `preferred_widget`
  UIContract; frontend handles it generically.
- **7 A230R3 human-query routing comparison (all on 5d27aca):**
  | A230R3 query | now routes to | vs A230R3 |
  |---|---|---|
  | worklog "за 2 недели" (standalone) | `member.worklogs_period` → COMPLETED 5/40.0 | was clarification → **fixed** |
  | worklog "в DMS за последние 2 недели" | `member.worklogs_period` → COMPLETED | was clarification → **fixed** |
  | worklog "в активном спринте DMS" | `member.time_spent` (sprint-bounded) count=0 | **unchanged** (source-accurate zero) |
  | "задачи Гаранина в активном спринте DMS" | `task.search` count=8 | **unchanged** |
  | "задачи Агатаевой в активном спринте DMS" | `task.search` count=2 | **unchanged** |
  | follow-up "с 21.09 по сегодня" / "Что уточнить?" | typed clarification continuation | **separate design gap (see below)** |
- **A230R2.1 task-creation week grammar:** `_task_live_handlers.py`, `task_catalog.py`,
  `sprint_period.py` are **byte-identical** (absent from delta). `...созданные за 7 дней` →
  `task.search_created` COMPLETED (34). Task-creation never hijacked by worklog.
- **Session audit (new agent log):** 0 local-store reads, 0 unscoped tenant scans, 0 5xx, 0 mutations;
  all 4 `work-logs/report` calls `user=`-scoped.

## Non-blocking / separate (NOT this feature, NOT green-lit)

- **F1 (pre-existing task-creation-grammar gap, out of scope):** `...созданные за последнюю неделю`
  (natural-language 1-week) and `за последние 2 недели` (14-day) for **task creation** return a typed
  clarification. The A230R2.1 creation grammar is 7-day/1-week bounded and was not touched by this delta
  (files byte-identical). `за 7 дней` works. Separate owner follow-up if 1-week/2-week task-creation
  phrasings are wanted.
- **Carried over from A230R3 (separate, explicitly not scored here per spec):** (a) free-text
  clarification continuation / "что уточнить" design gap; (b) `V4ResultPanel` rendering the internal
  `results` planner envelope as raw JSON. Both remain open and independent of this worklog feature;
  this GREEN is scoped to person/date worklogs only.

## Services left running (controlled isolated QA)

- MCP-SWTR `:3000` (PID 95040, **49 tools**, restarted on 5d27aca).
- Task API `:8241` (PID 95129, new `/work-logs/report` route, restarted on 5d27aca).
- Agent Core V4 `:8004` (PID 95611, healthy, v4_ready=True, `PO_AGENT_EXPECTED_HEAD=5d27aca…`, restarted on 5d27aca).

## Recommendation

Freeze `member.worklogs_period` as a certified additive checkpoint on `5d27aca`. Safe to proceed to the
next owner phase. No production changes, no merge, no Public synchronization performed by QA.
