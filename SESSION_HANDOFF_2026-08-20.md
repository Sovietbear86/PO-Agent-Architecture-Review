# PO Agent Harness — Session Handoff

**Date:** 2026-08-20  
**Branch:** `feat/core8-real-query-hardening-v2`  
**Repository:** `Sovietbear86/PO-Agent-Architecture-Review`  
**Last production fix commit:** `fe1b5990e9234fdf959eaccec9187755c4161629`

## 1. Where we stopped

We are hardening and validating the production PO Agent Harness on **real AS21/SWTR data**. We deliberately stopped forward roadmap work until the existing Core-8 skills and learning/correction behavior are proven on real data without false-green results.

The LLM-first semantic architecture is retained. The intended execution chain is:

`natural language -> LLM semantic frame -> semantic audit -> canonical grounding/validation -> capability execution -> AS21/SWTR evidence`

GigaCode is used as **tester/adversarial QA only**. Production fixes are made by ChatGPT/developer. Existing acceptance tests/oracles must not be weakened to make implementation pass.

## 2. Important history

### LLM transport regression

Assignments 027/028 established that the LLM client code had not regressed. The local `.env` had lost `/openai/v1` from `LLM_API_BASE_URL`.

Restored local configuration:

- working base path includes `/openai/v1`;
- direct LLM calls return HTTP 200;
- natural-language queries pass through the production semantic interpreter;
- `.env` and secrets must never be committed.

### Real-data oracle correction

The SWTR sprint listing is not authoritative for all task facts, especially assignee and relation membership. The acceptance oracle must use:

`sprint candidate keys -> individual task hydration -> authoritative relation/assignee/status facts -> filter -> exact task-key set`

Do not compare answer prose or counts only.

## 3. Assignment 026 result before semantic hardening

The corrected 026 V2 runner exposed real production failures:

- paraphrase invariance was incomplete;
- correction loop was incomplete;
- multiple false-green results existed;
- equivalent natural-language queries could return zero tasks, a correct subset, or an entire sprint.

This led to a semantic-boundary redesign rather than phrase-by-phrase patches.

## 4. Semantic-boundary redesign already implemented

Production semantic architecture was hardened so that:

1. LLM-first semantic extraction remains primary.
2. A second semantic audit pass can restore independent constraints dropped by the first pass.
3. Structural identifiers such as `DMS-SPRNT-1` are canonicalized and cannot be replaced by an entire sentence.
4. Requested filters must be grounded or cause fail-closed/clarification; silent filter dropping is forbidden.
5. Correction turns reuse structured previous semantic state rather than concatenating prose and reparsing from scratch.
6. Focused regression tests were added without changing the real-data 026 acceptance benchmark.

## 5. Assignment 029 — latest QA result

Report:

`qa_reports/CORE8_SEMANTIC_FRAME_BOUNDARY_RETEST_029.md`

HEAD tested by GigaCode: `49dd047`.

Focused semantic tests passed, showing the semantic boundary itself was substantially improved:

- `test_semantic_frame_boundary_v3.py`: **4/4 PASS**
- `test_semantic_core_v2.py`: **3/4 PASS**; conversation-context fixture still needs later review

However real-data execution was correctly marked **BLOCKED**.

Critical reproduction:

`Покажи задачи Garanin.R.V в DMS-SPRNT-1`

Expected: tasks belonging to `DMS-SPRNT-1` and assigned to Garanin.R.V.

Observed: tasks whose authoritative relation was `OLP-SPRNT-5`, while the request was reported as HTTP 200 / COMPLETED.

029 metrics at stop point:

- `029_FOCUSED_TESTS_PASS = 4/4`
- `026_FULLY_EXECUTED = NO`
- `CORE8_REAL_DATA = 0/8`
- `PARAPHRASE_INVARIANCE = 0/8`
- `CORRECTION_LOOP = 0/6`
- `FALSE_GREEN_COUNT = 3`
- `SILENT_SLOT_DROP_COUNT = 2`
- `READY_TO_RERUN_017_V2 = NO`

## 6. Root cause found after 029

The semantic frame could correctly contain `sprint_id = DMS-SPRNT-1`, but the sprint-read/capability path trusted the SWTR sprint-list facade too much.

The previous `HardenedProductionTaskApiAS21Adapter.get_sprint_tasks()` treated task codes returned by `/swtr-read/sprints/{id}/tasks` as members of the requested sprint and then **stamped the requested sprint_id onto returned Task objects**. If the facade returned candidates from another sprint, this could manufacture false evidence and produce a false-green result.

This is an execution/source-contract defect, not a reason to abandon the LLM-first architecture.

## 7. Production fix made at end of session

Commit:

`fe1b5990e9234fdf959eaccec9187755c4161629`

File:

`po-agent-platform-v2/src/po_agent/adapters/hardened_production_task_api.py`

### New invariant

The sprint-list facade is now treated only as a **candidate-key source**.

For every candidate task returned for a requested sprint:

1. read the individual SWTR task unit;
2. extract the real `scrum_board_plugin_sprint` relation;
3. compare it with the requested sprint;
4. reject the task if the relation is absent or different;
5. if product/space is requested, prove that relation as well;
6. only then map the task into the result set.

The adapter no longer fabricates sprint membership by blindly assigning the requested sprint ID to a candidate.

`sprint_exists()` is also now fail-closed and requires at least one source-proven task membership rather than trusting an echoed sprint identifier.

## 8. What must happen next

**Do not continue to Learning Loop 017_V2 yet.**

First perform a narrow verification of commit `fe1b599...`, then rerun the unchanged 029/026 real-data benchmark.

Recommended next QA assignment:

### Assignment 030 — Source-backed Sprint Membership Retest

GigaCode must be tester only and must not change production code.

Required checks:

1. Restart Task API and PO Agent from current HEAD.
2. Confirm `Покажи задачи Garanin.R.V в DMS-SPRNT-1` returns only tasks whose individually hydrated SWTR sprint relation is exactly `DMS-SPRNT-1`.
3. Confirm `Покажи задачи Moiseev.A.N. в DMS-SPRNT-2` obeys the same invariant.
4. Confirm no returned task belongs to `OLP-SPRNT-5` when DMS sprint is requested.
5. Test a definitely non-proven sprint such as `DMS-SPRNT-999999`; it must fail closed / clarify and must not return arbitrary tasks.
6. Compare exact task-key sets with the independent hydrated oracle.
7. Capture semantic frame, grounded frame, capability args and authoritative per-task sprint relation for any mismatch.
8. Count `FALSE_GREEN_COUNT` and `SILENT_SLOT_DROP_COUNT`; both must be zero for GREEN.
9. If the narrow gate passes, rerun the **unchanged** Assignment 029/026 V2 real-data benchmark completely: Core-8, paraphrase invariance, multi-filter preservation and correction loop.
10. Do not tune or modify the acceptance benchmark.

### Gate to resume roadmap

Do not proceed to 017_V2 until all are true:

- full real-data benchmark executed;
- Core-8 acceptance is green;
- paraphrase invariance is green;
- correction/self-recheck tests are green;
- `FALSE_GREEN_COUNT = 0`;
- `SILENT_SLOT_DROP_COUNT = 0`;
- no production semantic phrase-routing crutches are introduced.

## 9. Known secondary issue

029 also showed one focused failure:

`test_conversation_context_is_supplied_to_next_semantic_turn`

with `semantic_model_unavailable_or_invalid_json` in its fixture. Do not confuse this with the sprint-membership blocker. After sprint execution is green, verify whether this is only a stale/mock fixture or a real correction-loop production defect. The real multi-turn correction acceptance tests remain authoritative.

## 10. Non-negotiable architectural principles

- LLM-first NLU; do not enumerate every Russian phrase in deterministic routers.
- Deterministic code validates and grounds entities/constraints; it does not try to understand arbitrary natural language.
- Every explicit user constraint must either survive into the execution plan or cause clarification/fail-closed.
- Never silently broaden a query.
- Never manufacture source facts from request parameters.
- Real source evidence beats cached/echoed facade metadata.
- Exact task-key-set equality beats answer text and count-only assertions.
- Correction such as `ты не прав, проверь ещё раз` must trigger meaningful re-evaluation using preserved conversation/semantic state.
- GigaCode tests; ChatGPT/developer fixes production code.

## 11. Suggested first message in the next ChatGPT chat

> Продолжаем работу над PO Agent Harness. Прочитай `SESSION_HANDOFF_2026-08-20.md` в ветке `feat/core8-real-query-hardening-v2` и проверь текущий HEAD. Мы остановились сразу после production-фикса `fe1b599`, который запрещает доверять sprint-list facade без индивидуального подтверждения sprint relation. Следующий шаг — подготовить Assignment 030 для GigaCode и проверить фикс на реальных AS21/SWTR данных. Не переходить к 017_V2 до полного GREEN без false-green и silent slot drop.
