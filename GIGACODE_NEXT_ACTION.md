# GigaCode — Current Action

## ACTIVE: Assignment A229F3R — complex task clarification re-gate

Role: QA/source-forensics/browser tester only. **Do not modify production code.**

Previous verdict:
`AGENT_CORE_V4_COMPLEX_TASK_CLARIFICATION_RED_A229F3`

Previous first failing boundary:
P4-A planner silently omitted the user-requested `created_period` and still COMPLETED an over-broad task result in 3/6 runs.

Owner fix on current branch is deliberately outside Agent Core:

1. **Catalog hardening**
   - `task.search_created` and `task.type_analysis` explicitly forbid silently dropping a requested period.
   - If the period is incomplete/ambiguous, planner must preserve raw `created_period` for typed fail-closed parsing or ask clarification.

2. **API/dialogue postcondition guard**
   - after a V4 COMPLETED response, only for executed `task.*` factual trajectories:
   - if the original user query explicitly contains task-period intent;
   - and no executed task capability actually applied a non-empty `created_period`;
   - convert the unsafe COMPLETED answer into resumable `NEEDS_CLARIFICATION`.
   - the guard does **not route**, infer the missing period, query AS21, or alter capability arguments.
   - invalid over-broad results/evidence are removed from the public clarification payload.
   - provider/source/internal failure taxonomy remains unchanged.

3. **Tests**
   - silent period drop -> clarification;
   - applied created_period -> COMPLETED unchanged;
   - non-period task query -> COMPLETED unchanged.

Agent Core/planner/runtime orchestration files must remain byte-identical.

---

## P0 — pull / integrity / focused tests

1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD and clean tracked worktree.
2. Prove Core 6/6 byte-identical vs certified checkpoint:
   `checkpoint/v4-task-semantics-hierarchy-green-a229s1r4@afb6fa1d9b6e5d13a5d743f0d45afef94d1821a1`
3. Run focused:
   - `tests/test_agent_core_v4_task_created_period.py`
   - `tests/test_agent_core_v4_task_semantics_hierarchy.py`
   - `tests/test_agent_core_v4_task_catalog.py`
   - `tests/test_v4_browser_api_contract.py`
4. Run full V4 blast, relevant Task API SWTR suites, frontend build.
5. Require 0 failed.

If P0 RED -> STOP.

---

## P1 FIRST — exact previous failing boundary

Fresh browser/API sessions. Query:

`Открытые задачи Семавина с типом дефект в DMS за период`

Run at least 6 valid attempts with cooldown spacing sufficient to avoid provider burst artifacts.

Expected invariant on **every** valid run:
- final public status = `NEEDS_CLARIFICATION`;
- never public `COMPLETED`;
- never return DMS-431 or any over-broad task result;
- question explicitly says the period needs clarification;
- concrete reformulation examples are visible;
- `clarification_id` present;
- evidence/result payload from the unsafe over-broad execution is not exposed as a valid answer.

Accept either safe path:
A. planner-native clarification before task execution;
B. API constraint-coverage guard after planner omitted the period.

For path B prove:
- original query contains period intent;
- executed task call lacked `created_period`;
- guard changed only presentation/dialogue state to clarification;
- it did not invent a period or reroute/re-execute.

Then answer the clarification with:
`Период создания задач: с 30.09.2026 по сегодняшний день`

Require continuation:
- original goal preserved;
- terminal `task.type_analysis`;
- reference Semavin + DMS + open/not_completed + defect + created_period all present;
- exact REAL AS21 oracle parity;
- no need to repeat the full original request.

Any valid run that silently COMPLETES without the requested period => RED STOP.

---

## P2 — false-positive guard controls

Fresh sessions, prove the coverage guard does not break valid queries.

Run at least twice each:

1. `Открытые задачи Семавина с типом дефект в DMS`
   - no period requested;
   - normal COMPLETED exact result;
   - no clarification from the new guard.

2. `Открытые задачи Семавина с типом дефект в DMS с 30.09.2026`
   - created_period applied;
   - normal COMPLETED exact result.

3. `Открытые задачи Семавина с типом дефект в DMS за последние 2 дня`
   - created_period applied;
   - normal COMPLETED exact result.

4. `Открытые задачи Калачанова в WMB за последние 2 дня`
   - terminal `task.search_created`;
   - exact REAL_EMPTY if source still says zero.

5. `Задачи Калачанова в STS за 1 день`
   - terminal `task.search_created`;
   - exact current oracle.

Require no false `NEEDS_CLARIFICATION` when period is valid and applied.

---

## P3 — full complex-query regression

Re-run the four A229F3 primary cases, 3 valid runs each:

1. `Задачи Калачанова в STS за 1 день`
2. `Открытые задачи Калачанова в WMB за последние 2 дня`
3. `Открытые задачи Семавина с типом дефект в DMS с 30.09.2026`
4. `Открытые задачи Семавина с типом дефект в DMS за период с 30.09.2026 по сегодняшний день`

Build fresh independent REAL AS21 oracle for each.

Require exact key/count parity and all requested constraints preserved.

---

## P4 — clarification/error taxonomy

Re-prove:

- planner misunderstanding/incomplete period -> `NEEDS_CLARIFICATION`;
- provider 429 / HTTPStatusError / timeout/connectivity -> remains FAILED/provider;
- REAL AS21 unavailable -> remains source failure;
- internal non-planner exception -> remains FAILED/internal;
- deterministic option-button clarification + continuation retained;
- free-text clarification continuation retained.

No infrastructure or source defect may be disguised as user ambiguity.

---

## P5 — architecture / no-router audit

Require:
- Core 6/6 byte-identical;
- canonical 54 unchanged;
- no query-specific route;
- no person/space/date-result hardcodes;
- period coverage guard is post-execution fail-closed validation only;
- guard never creates factual values;
- task facts remain REAL AS21 authoritative;
- 0 local fallback;
- 0 mutations;
- 0 tenant-wide scans.

Also re-run retained:
- task type + latest sprint;
- hierarchy;
- Overview KPI;
- task drawer.

---

## P6 — latency observation only

Record for P1/P3:
- LLM calls;
- total wall;
- source duration;
- whether the guard avoided exposing a wrong answer.

Do not optimize planner/Core in this assignment.

A229R2 stays paused until this functional gate is GREEN.

---

## Verdict

Return exactly one:

- `AGENT_CORE_V4_COMPLEX_TASK_CLARIFICATION_GREEN_A229F3R`
- `AGENT_CORE_V4_COMPLEX_TASK_CLARIFICATION_RED_A229F3R`

GREEN requires:
- P1: 100% of valid incomplete-period runs clarify, zero silent drops;
- clarification continuation exact;
- P2/P3 exact;
- taxonomy and retained gates GREEN;
- Core untouched;
- all tests GREEN.

Commit report:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_COMPLEX_TASK_CLARIFICATION_REGATE_A229F3R.md`

If RED:
- preserve first failing boundary;
- STOP;
- do not modify production code.

If GREEN:
- recommend small checkpoint on TESTED_HEAD;
- then resume A229R2 planner-turn reduction.

**GigaCode is QA only. Do not modify production code.**
