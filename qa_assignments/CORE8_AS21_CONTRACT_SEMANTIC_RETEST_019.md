# QA Assignment 019 — Core-8 AS21 Contract + Semantic/Correction Retest

GigaCode is TESTER ONLY. Do not change production code, tests, config values, AS21 data, or secrets. Publish only the QA report.

## Purpose
Verify the four defects discovered during live diagnosis before rerunning exhaustive 017_V2:
- DEF-019-001 raw AS21 status Open/Closed caused task-api 422;
- DEF-019-002 task-api omitted top-level project_space/sprint_id although source_data carried them;
- DEF-019-003 LLM_API_KEY was not loaded when PO Agent was launched outside `po-agent-platform-v2`;
- DEF-019-004 complex/correction wording fell into semantic_interpretation_failure instead of source recheck/clarification.

## A. Restart from current HEAD
Restart task-api (8003) and PO Agent (8004) from current branch HEAD. Do not manually export LLM_API_KEY if the project `.env` already contains it. Record only boolean presence, never the secret value.

Required evidence:
- `get_settings().llm_api_key is not None` = YES/NO;
- semantic interpreter configured = YES/NO;
- runtime adapter class = HardenedProductionTaskApiAS21Adapter;
- correction wrapper active = YES/NO.

## B. Task API contract
On real cached SWTR tasks verify TaskResponse exposes:
- `project_space` from `source_data.swtr_space`;
- `sprint_id` and backward-compatible `sprint` from `source_data.sprint_id` or `swtr_attributes[code=scrum_board_plugin_sprint]`.

Sample at least 20 tasks across DMS/OLP/WMB and report counts populated.

## C. Raw AS21 status filtering
Call `/api/v1/tasks?status=Open`, `/api/v1/tasks?status=Closed`, plus local `todo`, `in_progress`, `done`.
Requirements:
- no 422 for Open/Closed;
- results for raw statuses must match `workflow_status` / `workflow_status_name` in source_data;
- local statuses preserve existing behaviour.

## D. Sprint/space source truth
For DMS-SPRNT-1 and DMS-SPRNT-2 call the complete live sprint endpoint and verify all task keys. For each returned task hydrate raw `read_unit` as needed and record:
- raw space;
- raw sprint attribute;
- assignee externalId/login/display.
Do not infer that missing cached fields mean negative membership.

## E. Golden query + correction
Use one fixed session:
1. `Покажи открытые задачи Гаранина в последнем спринте по DMS`
2. `Ты не прав, проверь ещё раз`

Turn 2 MUST NOT be interpreted as an unrelated new business query. It must:
- reopen/recheck source evidence;
- return `NEEDS_CLARIFICATION` when semantics such as open/last remain unresolved, or a corrected grounded result when sufficient evidence exists;
- expose correction metadata with previous and recheck trace ids;
- perform zero persistent skill mutation.

Then answer clarification explicitly and verify the original query context is retained.

## F. Explicit sprint wording
Run:
- `Покажи задачи Гаранина в DMS-SPRNT-1`
- `Покажи задачи Гаранина в DMS-SPRNT-2`
- `Покажи задачи Гаранина по DMS в спринте DMS-SPRNT-1`
These must resolve the full sprint id exactly and must not degrade it to `SPRNT-1`/`SPRNT-2`.

## G. Protected Core-8 smoke
Re-run the accepted 8 Core skills on real AS21. Required 8/8 and zero new HIGH regressions.

## Decision
Only if A-G pass may GigaCode set `READY_TO_RERUN_017_V2 = YES`. Do not run 017_V2 in this assignment.

Publish `qa_reports/CORE8_AS21_CONTRACT_SEMANTIC_RETEST_019.md` with footer:

```text
ASSIGNMENT_ID = CORE8_AS21_CONTRACT_SEMANTIC_RETEST_019
CURRENT_HEAD = <sha>
DEF_019_001_RAW_STATUS_FIXED = YES|NO
DEF_019_002_PROJECT_SPRINT_EXPOSED = YES|NO
DEF_019_003_PROJECT_ENV_LOADED = YES|NO
DEF_019_004_CORRECTION_SEMANTICS_FIXED = YES|NO
TASK_RESPONSE_SAMPLE = N
PROJECT_SPACE_POPULATED = N
SPRINT_ID_POPULATED = N
RAW_STATUS_OPEN_HTTP = <status>
RAW_STATUS_CLOSED_HTTP = <status>
EXPLICIT_SPRINT_ID_PRESERVED = YES|NO
CHALLENGE_TRIGGERS_FRESH_RECHECK = YES|NO
TARGETED_CLARIFICATION_PASS = YES|NO
SESSION_CONTEXT_RETENTION_PASS = YES|NO
PERSISTENT_SKILL_MUTATION_FROM_CORRECTION = 0
CORE8_SMOKE_PASS = x/8
NEW_HIGH_PRODUCTION_REGRESSIONS = N
AS21_MUTATIONS_DURING_TEST = 0
READY_TO_RERUN_017_V2 = YES|NO
```

After publishing, STOP.