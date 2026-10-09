# GigaCode — Current Action

## ACTIVE: Assignment A229F3 — Natural task-period wording regression gate

Role: QA/source-forensics/browser tester only. **Do not modify production code.**

Context:
A live browser counterexample reopened the created-period gate after A229R1:

1. `Задачи Калачанова в STS за 1 день` -> generic trajectory failure.
2. `Открытые задачи Калачанова в WMB за последние 2 дня` -> generic trajectory failure.

Existing certified capability family already supports:
- `task.search_created`
- `task.search_created_in_progress`
- person + space + created_period
- open/completed status + created_period
- source-backed created_at fail-closed semantics.

Root causes addressed by owner:
- parser now accepts `за N дней`, `за день`, `сегодня` in addition to `последние N дней` / explicit date ranges;
- plugin catalog now states that a **bare task-search period** defaults to creation time unless the user explicitly names another timestamp dimension;
- open/completed status must stay in the same `task.search_created` call;
- explicit in-progress + period keeps using fixed-status `task.search_created_in_progress`;
- Agent Core is untouched.

Current owner delta is plugin/test only.

---

## P0 — integrity / focused tests

1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD and clean tracked worktree.
2. Prove Agent Core 6/6 byte-identical to checkpoint:
   `checkpoint/v4-task-semantics-hierarchy-green-a229s1r4@afb6fa1d9b6e5d13a5d743f0d45afef94d1821a1`
3. Run:
   - `tests/test_agent_core_v4_task_created_period.py`
   - `tests/test_agent_core_v4_task_catalog.py`
   - retained task semantics/hierarchy tests
   - full V4 blast-radius
   - relevant Task API SWTR suites
   - frontend build
4. Require 0 failed.
5. Canonical 54 unchanged; extra plugin skills unchanged except procedure text.

Any RED => STOP.

---

## P1 — parser contract

Directly verify `_parse_human_created_period`:

- `за 1 день` -> start today 00:00 Europe/Moscow, end=now, kind=`last_1_calendar_days`
- `за день` -> same
- `сегодня` -> same
- `за 3 дня` -> start at 00:00 two calendar days before today, end=now
- retained `последние 2 дня`
- retained explicit inclusive date range

Require no rolling-24h reinterpretation for `за 1 день`; semantics are calendar-day based.

---

## P2 — exact live browser counterexamples

Use a **new conversation for every run** and REAL AS21.

### Case A — exact first counterexample
Run at least 3 times:

`Задачи Калачанова в STS за 1 день`

Require:
- terminal capability = `task.search_created`;
- raw `created_period="за 1 день"`;
- source-backed canonical person + `space=STS`;
- no workflow status invented;
- exact key/count parity vs independent REAL AS21 oracle using source `createdAt` from today 00:00 Europe/Moscow to run time;
- no local fallback;
- no tenant-wide scan;
- no generic trajectory failure.

### Case B — exact second counterexample
Run at least 3 times:

`Открытые задачи Калачанова в WMB за последние 2 дня`

Require:
- terminal capability = `task.search_created`;
- raw `created_period="за последние 2 дня"`;
- explicit open/not_completed status preserved in the SAME terminal call;
- canonical person + WMB preserved;
- exact key/count parity vs independent REAL AS21 oracle;
- no broadening to all WMB tasks;
- no generic trajectory failure.

---

## P3 — retained composition matrix

Fresh conversation each, at least 2 runs each:

1. `Покажи задачи Калачанова в STS созданные за последние 2 дня`
   - retained explicit creation wording -> `task.search_created`.

2. `Открытые задачи Калачанова в STS за 1 день`
   - `task.search_created` + open/not_completed.

3. `Задачи Калачанова в работе в STS за 1 день`
   - terminal `task.search_created_in_progress`;
   - planner must not supply/override the fixed in-progress status.

4. `Задачи Калачанова в STS сегодня`
   - `task.search_created`, no invented status.

5. Existing explicit range control:
   `Задачи Калачанова в STS за период с 29.09.2026 по 01.10.2026`
   - retained exact behavior.

Build fresh independent REAL AS21 oracle for every factual case.

---

## P4 — semantic boundary / no overreach

Prove from catalog/procedure and one planner probe that bare-period default applies **only when no other timestamp dimension is explicitly named**.

The owner fix must not create a phrase router or deterministic query-text branch in Agent Core.

Audit:
- no surname/space/day-count hardcode;
- no Core/planner/runtime edit;
- no local factual cache;
- no tenant-wide scan;
- no fabricated timestamps;
- missing source created_at still fails closed.

If the user explicitly names another time dimension (deadline, updated time, time-in-status), do not silently reinterpret it as created_period. If no matching capability exists, safe failure/clarification is preferable.

---

## P5 — browser/error audit

For the P2/P3 runs:
- 0 unexpected 4xx/5xx;
- 0 console errors;
- 0 mutations;
- frontend proxy only;
- no false `AS21 unavailable` when source is healthy.

A planner/trajectory failure, if any remains, must stay classified as trajectory/runtime failure — never as source outage.

---

## Verdict

Return exactly one:

- `AGENT_CORE_V4_NATURAL_PERIOD_GREEN_A229F3`
- `AGENT_CORE_V4_NATURAL_PERIOD_RED_A229F3`

GREEN requires P0-P5 GREEN.

If GREEN:
- commit report `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_NATURAL_PERIOD_A229F3.md`;
- recommend checkpoint `checkpoint/v4-natural-period-green-a229f3`;
- then return to A229R2 planner-turn reduction planning.

If RED:
- preserve first failing boundary;
- STOP;
- do not modify production code.

**GigaCode is QA only.**
