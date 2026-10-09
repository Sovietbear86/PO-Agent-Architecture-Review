# GigaCode — Current Action

## ACTIVE: Assignment A229F3 — created-period composition regression

Role: QA/source-forensics/browser tester only. **Do not modify production code.**

Context:
Two manual browser failures reopened the created-period gate:

1. `Задачи Калачанова в STS за 1 день`
   - FAILED after ~35.7s with generic trajectory failure.
2. `Открытые задачи Калачанова в WMB за последние 2 дня`
   - FAILED after ~46.9s with generic trajectory failure.

Created-period functionality already exists and was previously certified:
- `task.search_created`
- `task.search_created_in_progress`

Current branch also contains an owner plugin-only language fix for bare relative wording such as `за 1 день`:
- parser accepts bare `за N дней` / `за день`;
- task catalog guidance routes bare task periods to created-period search;
- focused tests were added.
This assignment must verify that fix and diagnose the second failure, which uses an already-supported phrase.

Certified functional checkpoint:
`checkpoint/v4-task-semantics-hierarchy-green-a229s1r4@afb6fa1d9b6e5d13a5d743f0d45afef94d1821a1`

Do not start A229R2 planner optimization until A229F3 is closed.

---

## P0 — integrity / focused regressions

1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD and clean tracked worktree.
2. Prove Agent Core 6/6 byte-identical to certified checkpoint.
3. Run:
   - `tests/test_agent_core_v4_task_created_period.py`
   - `tests/test_agent_core_v4_task_catalog.py`
   - `tests/test_agent_core_v4_task_semantics_hierarchy.py`
4. Run full V4 blast + relevant Task API SWTR suites.
5. Require 0 failed before live testing.

Any production/Core diff beyond plugin/catalog + tests for the bare-period fix must be reported.

---

## P1 — direct plugin/source truth

Build independent REAL AS21 oracle for both scopes:

### Case A
Person: Kalachanov
Space: STS
Period: `за 1 день`

Expected semantics:
- same calendar semantics as `последний 1 день`;
- Moscow calendar day: today 00:00 through execution time;
- no workflow status unless explicitly requested.

### Case B
Person: Kalachanov
Space: WMB
Period: `последние 2 дня`
Status: open / not_completed

Oracle requirements:
- source-bounded person + space read;
- authoritative created_at only;
- canonical open/not_completed status;
- exact key set/count;
- no local store, no tenant-wide scan.

Directly invoke the governed terminal capability for each case:
- A -> `task.search_created`
- B -> `task.search_created` with `status=not_completed`

Require exact parity with oracle and source=REAL_AS21.

If direct capability is RED, stop and report the exact plugin/source boundary.

---

## P2 — live Agent trajectory for the two user failures

Use a **fresh conversation for every run**. Run each primary query at least 3 times.

### A — bare period
`Задачи Калачанова в STS за 1 день`

Require:
- planner selects/loads created-period skill;
- terminal capability = `task.search_created`;
- raw period is preserved (`за 1 день`);
- person + STS preserved;
- no invented workflow status;
- exact oracle parity.

### B — status + supported period
`Открытые задачи Калачанова в WMB за последние 2 дня`

Require:
- terminal capability = `task.search_created`;
- arguments preserve:
  - reference=Калачанов
  - space=WMB
  - created_period=`за последние 2 дня` or semantically identical raw wording from the user request
  - status=open/not_completed
- exact oracle parity;
- no separate model-side intersection;
- no local fallback;
- no source_unavailable unless a real source call fails.

For every run capture:
- selected skill;
- every planned capability id;
- capability arguments;
- bounded-repair attempts;
- number of LLM/planner calls;
- last valid planner output before FAILED/COMPLETED;
- total wall time;
- source call count.

If FAILED, classify the **first failing boundary** precisely:
1. skill discovery/routing;
2. planner argument schema;
3. bounded repair;
4. terminal capability execution;
5. completion/postcondition;
6. response synthesis;
7. provider 429/outage;
8. REAL AS21/source failure.

Do not label a healthy-source planner failure as AS21 unavailable.

---

## P3 — discriminating controls

Run once each in fresh conversations:

1. `Задачи Калачанова в STS созданные за последний 1 день`
2. `Задачи Калачанова в STS за последние 2 дня`
3. `Открытые задачи Калачанова в WMB созданные за последние 2 дня`
4. `Задачи Калачанова в WMB за последние 2 дня`
5. `Открытые задачи Калачанова в WMB`

Purpose:
- distinguish bare-period language routing from period+status composition;
- distinguish planner failure from terminal capability/source behavior;
- prove whether adding the word `созданные` changes only routing or correctness.

Every completed factual run must match a fresh independent oracle.

---

## P4 — latency evidence

This is not an optimization assignment, but record latency because the failures occurred after 35–47s.

For each primary run report:
- total wall;
- LLM/planner call count;
- whether repeated repair/planning consumed the time;
- source duration where observable.

If a failed trajectory spends multiple LLM turns before failing, quantify the avoidable turn count for later A229R2 work.

No planner/Core optimization in A229F3.

---

## P5 — retained controls / architecture

Require retained GREEN:
- explicit date-range created search;
- `последние 2 дня` created search;
- created + in-progress fixed capability;
- task type + latest sprint;
- hierarchy;
- Overview KPI;
- task drawer.

Architecture:
- Core byte-identical;
- no phrase-specific deterministic router;
- no hardcoded person/space/day result;
- REAL AS21 authoritative;
- zero unauthorized mutations;
- zero tenant-wide scans.

---

## Verdict

Return exactly one:

- `AGENT_CORE_V4_CREATED_PERIOD_COMPOSITION_GREEN_A229F3`
- `AGENT_CORE_V4_CREATED_PERIOD_COMPOSITION_RED_A229F3`

GREEN requires both primary browser queries to complete with exact source parity in all valid runs.

If RED:
- preserve the first failing boundary;
- include the full trajectory classification above;
- STOP;
- do not modify production code.

Commit report:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_CREATED_PERIOD_COMPOSITION_A229F3.md`

After GREEN:
- freeze a small functional checkpoint;
- resume A229R2 planner-turn reduction.

After RED:
- owner applies the smallest plugin/catalog fix possible; Core changes require explicit proof that the defect cannot be solved outside Core.

**GigaCode is QA only. Do not modify production code.**
