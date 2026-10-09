# GigaCode — Current Action

## ACTIVE: Assignment A229F3 — complex task composition + clarification regression

Role: QA/source-forensics/browser tester only. **Do not modify production code.**

Manual browser testing reopened the task-composition gate. Four representative failures were observed:

1. `Задачи Калачанова в STS за 1 день`
2. `Открытые задачи Калачанова в WMB за последние 2 дня`
3. `Открытые задачи Семавина с типом дефект в DMS за с 30.09.2026`
4. `Открытые задачи Семавина с типом дефект в DMS за период с 30.09.2026 по сегодняшний день`

The product requirement is broader than these phrases:
- complex task filters must compose generically;
- if the agent cannot safely understand/plan the request, it must return a typed clarification with a useful reformulation recommendation, not a generic FAILED card;
- provider/source/internal failures must NOT be disguised as user ambiguity;
- Agent Core must remain untouched unless the defect is proven impossible to solve outside Core.

Owner delta on current branch:
- plugin parser accepts bare relative periods and open-ended dates (`с DATE`, `с DATE по сегодня`, including harmless `за с DATE`);
- task catalog explicitly routes type + person + space + status + created_period through one terminal `task.type_analysis` capability;
- API/dialogue layer outside Agent Core promotes only recognized planner-understanding/runtime-period failures into resumable `NEEDS_CLARIFICATION`;
- provider/network markers (429/HTTPStatusError/timeouts/connectivity) remain FAILED;
- tests added for open-ended periods, full type/status/person/period composition, clarification continuation, and provider guard.

Certified baseline:
`checkpoint/v4-task-semantics-hierarchy-green-a229s1r4@afb6fa1d9b6e5d13a5d743f0d45afef94d1821a1`

A229R2 latency work remains paused until this gate is GREEN.

---

## P0 — integrity / tests

1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD and clean tracked worktree.
2. Prove Agent Core 6/6 byte-identical to certified baseline.
3. Run focused:
   - `tests/test_agent_core_v4_task_created_period.py`
   - `tests/test_agent_core_v4_task_semantics_hierarchy.py`
   - `tests/test_agent_core_v4_task_catalog.py`
   - `tests/test_v4_browser_api_contract.py`
4. Run full V4 blast + relevant Task API SWTR suites + frontend build.
5. Require 0 failed.

Report production diff by file. Expected product changes are only:
- plugin task handlers/catalog;
- API clarification policy seam.
No Agent Core/planner/runtime orchestration files may change.

---

## P1 — parser/source truth

Prove generic calendar semantics directly:

A. `за 1 день` -> today 00:00 Moscow through now.
B. `за последние 2 дня` -> previous calendar day 00:00 through now.
C. `с 30.09.2026` -> 30.09.2026 00:00 through now.
D. `с 30.09.2026 по сегодняшний день` -> same open-ended window.
E. `за с 30.09.2026` -> tolerate as the same start-to-now window.
F. two explicit dates remain inclusive and unchanged.

Build independent REAL AS21 oracles using authoritative created_at and bounded person/space scope. No local store, no tenant-wide scan.

---

## P2 — generic terminal capability composition

Directly call the governed terminal capability, independent of planner, for:

### Case 1
Kalachanov + STS + created_period=`за 1 день`
Terminal: `task.search_created`

### Case 2
Kalachanov + WMB + status=not_completed + created_period=`за последние 2 дня`
Terminal: `task.search_created`

### Case 3
Semavin + DMS + status=not_completed + task_type=defect + created_period=`с 30.09.2026 по сегодняшний день`
Terminal: `task.type_analysis`

Require exact key/count parity with independent REAL AS21 oracle.

For Case 3 prove all constraints survive in the SAME terminal call:
- reference
- space
- status
- task_type
- created_period

No model-side intersection and no split into separate date/type result sets.

---

## P3 — live Agent/browser complex-query matrix

Fresh conversation for every run. Run each primary case at least 3 valid times:

1. `Задачи Калачанова в STS за 1 день`
2. `Открытые задачи Калачанова в WMB за последние 2 дня`
3. `Открытые задачи Семавина с типом дефект в DMS с 30.09.2026`
4. `Открытые задачи Семавина с типом дефект в DMS за период с 30.09.2026 по сегодняшний день`

For 1/2 require terminal `task.search_created`.
For 3/4 require terminal `task.type_analysis`.

Require:
- exact fresh source oracle parity;
- raw period preserved;
- explicit status preserved;
- task type preserved where requested;
- person and space preserved;
- no local fallback;
- no tenant-wide scan;
- no false source_unavailable.

Also run wording controls:
- same type query with two explicit dates;
- same type query with `за последние 2 дня`;
- same type query without status;
- same type query without type (must route to created-period search, not type_analysis).

---

## P4 — clarification UX outside Agent Core

### A. User ambiguity / incomplete period
Fresh browser conversation:
`Открытые задачи Семавина с типом дефект в DMS за период`

The request does not contain a resolvable period.

Require:
- result is `NEEDS_CLARIFICATION`, NOT generic `FAILED`;
- visible question tells the user what is ambiguous;
- visible text includes concrete reformulation examples;
- clarification_id is present;
- free-text answer is accepted, e.g.:
  `Период создания задач: с 30.09.2026 по сегодня`
- continuation preserves the original query/goal and completes with exact oracle parity;
- user does not have to repeat the full original request.

### B. Existing deterministic clarification
Retain one identity/space/sprint ambiguity case with option buttons. Existing clarification continuation must remain GREEN.

### C. Provider/source taxonomy
Using tests/injected harness only (do not wait for a real outage), prove:
- planner-understanding failure / unsupported period syntax -> `NEEDS_CLARIFICATION`;
- 429 / HTTPStatusError / timeout / connectivity -> remains FAILED/provider failure;
- REAL AS21 unavailable -> remains SOURCE_UNAVAILABLE;
- internal non-planner defect -> remains ERROR/FAILED.

No user clarification may hide a real infrastructure or code defect.

---

## P5 — first-failing-boundary diagnostics

For every primary browser run capture:
- loaded skill(s);
- planner decisions;
- terminal capability;
- terminal arguments;
- bounded repairs;
- LLM/planner call count;
- source calls;
- total wall;
- final status.

If a complex query still fails, classify first boundary exactly:
1. skill discovery/routing;
2. planner argument schema;
3. bounded repair;
4. terminal capability execution;
5. completion/postcondition;
6. response synthesis;
7. provider outage/rate limit;
8. source failure.

Do not change code. STOP on the first reproducible product RED after preserving evidence.

---

## P6 — retained architecture

Require:
- Core 6/6 byte-identical;
- canonical 54 unchanged;
- task.type_analysis remains plugin-owned;
- no phrase-specific deterministic router;
- no surname/space/date hardcode;
- API clarification promotion is generic by typed failure class, not query text;
- REAL AS21 authoritative;
- zero unauthorized mutations;
- zero tenant-wide scans;
- previous hierarchy/type/latest-sprint/Overview/task-drawer gates retained.

---

## Verdict

Return exactly one:

- `AGENT_CORE_V4_COMPLEX_TASK_CLARIFICATION_GREEN_A229F3`
- `AGENT_CORE_V4_COMPLEX_TASK_CLARIFICATION_RED_A229F3`

GREEN requires:
- all 4 primary complex browser queries exact;
- clarification browser continuation GREEN;
- provider/source error taxonomy GREEN;
- P0 all-green;
- Core untouched.

Commit report:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_COMPLEX_TASK_CLARIFICATION_A229F3.md`

If GREEN:
- recommend a small checkpoint on TESTED_HEAD;
- then resume A229R2 planner-turn reduction.

If RED:
- preserve first failing boundary and STOP;
- owner applies the smallest plugin/catalog/API-seam fix possible;
- Core changes require explicit proof that no external seam can solve the defect.

**GigaCode is QA only. Do not modify production code.**
