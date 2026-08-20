# QA Assignment 030 — Source-backed Sprint Membership Retest

## Purpose

Verify production commit `fe1b5990e9234fdf959eaccec9187755c4161629`, which makes the SWTR sprint-list facade a candidate-key source only and requires individually hydrated SWTR evidence for sprint membership.

This is a narrow gate before the unchanged Assignment 029/026 V2 benchmark. It is not a new or weakened benchmark.

## Tester role and immutable scope

1. GigaCode acts only as QA/tester.
2. Do not modify production code, prompts, adapters, tests, fixtures, acceptance runners, AS21/SWTR data, learning state, configuration or `.env`.
3. Do not repair defects. Record them with evidence for ChatGPT/developer.
4. Only the assigned QA report, plus an already-supported machine-readable result JSON, may be committed.
5. Never commit secrets or `.env`.

## Environment

- repository: `Sovietbear86/PO-Agent-Architecture-Review`
- branch: `feat/core8-real-query-hardening-v2`
- required production commit: `fe1b5990e9234fdf959eaccec9187755c4161629`
- `PO_AGENT_AS21_MODE=task-api`
- semantic LLM enabled with the locally restored `/openai/v1` base path
- real AS21/SWTR only; FakeAS21Adapter cannot support any acceptance claim

Pull the branch, record the actual HEAD, restart Task API and PO Agent from that HEAD, and record PIDs/ports. If the environment prevents restart, report `MANUAL_ACTION_REQUIRED` with the exact command; do not fabricate runtime evidence.

## Independent hydrated oracle

For every source-backed sprint query:

1. Obtain candidate task keys from the sprint-list facade.
2. Read every candidate through the individual authoritative SWTR task-unit capability.
3. Extract task key, assignee identity, status, space/product and `scrum_board_plugin_sprint`.
4. Include a task in the sprint oracle only when its individually hydrated `scrum_board_plugin_sprint` exactly equals the requested sprint.
5. Apply the requested assignee and other filters after hydration.
6. Exhaust pagination/complete corpus.
7. Compare exact task-key sets. Answer prose, HTTP 200 and counts alone are not acceptance evidence.
8. Never use the agent result as its own oracle.

## Narrow source-membership gate

For every case capture original query, raw semantic frame, semantic audit, grounded frame, capability name/args, facade candidate keys, authoritative per-task sprint relation, response status and exact key diff.

### A. Garanin / DMS-SPRNT-1

Query:

`Покажи задачи Garanin.R.V в DMS-SPRNT-1`

Required:

- assignee and `sprint_id=DMS-SPRNT-1` survive semantic interpretation and grounding;
- capability args contain both constraints;
- every returned task is individually source-proven in `DMS-SPRNT-1`;
- `AGENT_KEYS == ORACLE_KEYS`;
- no task from `OLP-SPRNT-5` or any other sprint is returned.

### B. Moiseev / DMS-SPRNT-2

Query:

`Покажи задачи Moiseev.A.N. в DMS-SPRNT-2`

Apply the same invariants with `sprint_id=DMS-SPRNT-2`.

If `Moiseev.A.N.` does not exist in current source truth, the original case must remain in the report and must fail closed/clarify with source evidence. A real DMS-SPRNT-2 assignee may be added as a supplemental positive case, but may not silently replace the original case.

### C. Foreign-sprint rejection

For both DMS queries prove:

`FOREIGN_SPRINT_TASK_COUNT = 0`

Pay special attention to `scrum_board_plugin_sprint=OLP-SPRNT-5`. HTTP 200/COMPLETED with even one foreign-sprint task is a false green.

### D. Unproven sprint

Query:

`Покажи задачи в DMS-SPRNT-999999`

Required: source-backed clarification/failure. It must not return arbitrary tasks or report successful empty completion as if an echoed sprint ID proved existence.

## Mismatch evidence

For every mismatch report:

- raw and grounded semantic frames;
- capability args;
- facade candidate keys;
- authoritative relation for every relevant task;
- `ORACLE_KEYS`, `AGENT_KEYS`, `MISSING_KEYS`, `EXTRA_KEYS`;
- trace/error code and response status.

## Narrow-gate decision

Narrow gate is GREEN only when:

- Case A exact set passes;
- Case B exact set passes, or the absent identity is handled with correct source-backed fail-closed behavior;
- `FOREIGN_SPRINT_TASK_COUNT=0`;
- the unproven sprint fails closed;
- `FALSE_GREEN_COUNT=0`;
- `SILENT_SLOT_DROP_COUNT=0`;
- `QUERY_HTTP_500_COUNT=0`.

If the narrow gate is not GREEN, do not run the full 026 benchmark. Publish the report and stop.

## Full unchanged acceptance after narrow GREEN

Only after narrow GREEN, rerun without modification:

- Assignment 029;
- Assignment 026 V2 real-data runner and independent hydrated oracle;
- production architecture preflight;
- Core-8 real-data smoke;
- B1–B8 paraphrase invariance;
- person/product/status robustness;
- multi-filter preservation;
- explicit identifier safety;
- correction/recheck loop F1–F6;
- ambiguity/fail-closed cases;
- focused semantic regression tests and the relevant full regression suite.

Do not change query wording, tune the oracle, weaken pass criteria, add phrase regex/keyword routing, or mark HTTP 200/COMPLETED as PASS without exact source-backed equality.

Separately classify the known `test_conversation_context_is_supplied_to_next_semantic_turn` failure, if still present, as a stale/mock fixture or production defect. Do not mix it with the sprint-membership gate; real correction-loop acceptance remains authoritative.

## Report

Create:

`qa_reports/CORE8_SOURCE_BACKED_SPRINT_MEMBERSHIP_RETEST_030.md`

Include branch/HEAD, service restart evidence, production wiring, independent oracle, all narrow cases, per-task authoritative relations, exact-set diffs, mismatch traces, regression classification and full 029/026 results if the narrow gate passed.

Report these final metrics exactly:

```text
030_NARROW_GATE = GREEN|RED|BLOCKED
030_CASE_A_EXACT_SET = PASS|FAIL|BLOCKED
030_CASE_B_EXACT_SET = PASS|FAIL|BLOCKED
FOREIGN_SPRINT_TASK_COUNT = n
UNPROVEN_SPRINT_FAILCLOSED = YES|NO
026_FULLY_EXECUTED = YES|NO
CORE8_REAL_DATA = x/8
PARAPHRASE_INVARIANCE = x/8
CORRECTION_LOOP = x/6
MULTIFILTER_PRESERVATION = x/y
FALSE_GREEN_COUNT = n
SILENT_SLOT_DROP_COUNT = n
SEMANTIC_CRUTCH_COUNT_PRODUCTION = n
QUERY_HTTP_500_COUNT = n
NEW_HIGH_PRODUCTION_REGRESSIONS = n
READY_TO_RERUN_017_V2 = YES|NO
```

`READY_TO_RERUN_017_V2=YES` is allowed only after full GREEN with zero false greens and zero silent slot drops.

Commit and push only the report (and existing runner JSON if automatically produced), then stop and return the report commit SHA and verdict.
