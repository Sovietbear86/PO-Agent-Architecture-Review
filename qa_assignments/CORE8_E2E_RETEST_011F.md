# QA Assignment: CORE8 E2E RETEST 011F

## Role boundary

GigaCode is QA only for this assignment.

- DO NOT modify production code.
- DO NOT modify tests to make them pass.
- DO NOT change configuration semantics or source contracts.
- You MAY restart local services, run commands, inspect logs and publish this report.
- Any failure must be reported with reproducible evidence; do not patch it.

## Required branch / pre-check

Branch: `feat/real-baseline-candidate-eval-v1`

1. `git pull --ff-only origin feat/real-baseline-candidate-eval-v1`
2. Record exact HEAD.
3. Confirm developer commits are present:
   - `7a74bbf` fail-closed Core-8 deterministic semantic recovery
   - `667cf64` schema-aware nested `request` handling for MCP `search_versions`
4. Restart Task API and PO Agent from the current HEAD so no stale process is tested.
5. Confirm MCP-SWTR SSE is reachable and record tool count.

## Test A — canonical task/attachment regression

Verify again:

- `GET /api/v1/tasks?limit=1` -> 200 with no redirect.
- `GET /api/v1/tasks/?limit=1` is not silently accepted through redirect.
- `WMB-30000` is readable.
- its 5 XLSX attachments are visible through the canonical adapter.
- zero AS21 mutations.

## Test B — real team and current sprint grounding

Verify source-backed facts:

- `Гончаров` -> `Goncharov.A.O`.
- `Калачанов` -> `Kalachanov.V.V`.
- OLP current sprint comes from live AS21.
- DMS current sprint comes from live AS21.

Do not substitute hard-coded sprint IDs for the live lookup.

## Test C — semantic production path

All requests MUST be sent through the real production endpoint `/api/v1/query`, not by invoking capabilities directly.

Run at least these requests and capture status, intent, skill_id, warnings and evidence summary:

1. `Покажи задачу WMB-30000`
2. `Суммаризируй задачу WMB-30000`
3. `Оцени качество постановки WMB-30000`
4. `Какой текущий спринт OLP?`
5. `Покажи здоровье текущего спринта OLP`
6. `Покажи velocity текущего спринта OLP`
7. `Какая нагрузка у Калачанова?`
8. `Подбери исполнителя для WMB-30000`
9. `Найди задачи Гончарова в актуальном спринте по OLAP`
10. `Найди открытые задачи Гончарова в актуальном спринте по OLAP`

Expected contract:

- Provider formatting/availability must not produce `semantic_interpretation_failure` for the high-precision Core-8 shapes above.
- Deterministic recovery is allowed only for the catalog-closed recognized shapes. Record `_harness.llm_used` when present.
- Query #10 MAY legitimately return `NEEDS_CLARIFICATION` for the exact meaning of `открытые`, if no active learned semantic rule exists. That is a correct fail-closed result and is NOT `semantic_interpretation_failure`.
- Unsupported natural-language requests must still fail closed; do not treat deterministic recovery as a generic NLP router.

Also test at least three unsupported controls, e.g. weather, arithmetic and an unrelated code-generation request. None may execute a Core-8 skill.

## Test D — release/version source contract

This test is specifically for the live MCP schema mismatch found in 011E.

1. Inspect and record the live `search_versions` input schema.
2. Confirm whether it exposes a top-level `request` property and record the nested request property names/type.
3. Call:
   - `/api/v1/swtr-read/versions?space=WMB`
   - `/api/v1/swtr-read/versions?space=OLP`
   - `/api/v1/swtr-read/versions?space=DMS`
4. Record `mcp_argument_shape`, `mcp_arguments`, HTTP status and a sanitized shape/count of returned version rows.
5. At least one real source-backed release/version anchor must be captured if the live MCP tool supports the data.
6. If MCP still returns ToolError, report the exact sanitized schema and exception class. Do NOT label it a Task API bug unless the generated arguments violate the reported schema.

## Test E — sprint completeness

Re-verify current behavior:

- first page can contain 100 rows with `hasNext=true`;
- `complete=true` returns the complete source-backed/canonical set;
- report complete count and first-page count;
- retain explicit `completeness_source` and do not false-green an incomplete page.

## Test F — Core-8 production E2E gate

Evaluate the canonical Core-8 set through `/api/v1/query` only:

1. task_search
2. task_summary
3. task_quality
4. sprint_health
5. velocity (`sprint_velocity` implementation is acceptable canonical mapping)
6. team_workload
7. competency_match / assignee recommendation (state exactly which catalog skill was executed)
8. release_health

For every skill record:

- query;
- response status;
- semantic intent;
- skill_id/version;
- source evidence present?;
- source-backed identifiers used;
- final PASS/FAIL reason.

A PASS requires real execution, not merely successful intent classification.

## Test G — false-green / adversarial controls

Repeat at minimum:

- nonexistent task;
- nonexistent assignee;
- nonexistent sprint;
- nonexistent release;
- contradictory filters;
- unsupported semantic request;
- invalid/prose JSON provider response if test harness supports injection;
- no attachment cross-task leakage;
- no AS21 mutation path.

All must fail closed.

## Test H — targeted regressions from 011E

Run the seven failures reported by 011E individually and include the full pytest node/result summary:

- `test_normalize_unknown_status`
- `test_local_and_generated_artifacts_are_not_committed`
- `test_source_dependent_request_cannot_be_reinterpreted`
- `test_portfolio_overview_never_labels_task_api_data_as_fake`
- `test_task_api_marks_missing_source_skills_unavailable`
- `test_task_api_end_to_end_query_maps_source_to_harness_contract`
- `test_injected_sources_make_source_gated_skills_ready`

Classify each as:

- production regression;
- stale/incorrect test expectation;
- repository hygiene issue;
- environment/integration issue.

Do not edit the tests.

## Test I — full regression

Run the full regression suite and compare with 011E:

- passed;
- failed;
- errors;
- skipped;
- `NEW_CODE_REGRESSIONS_VS_011E`.

The learning-loop gate requires zero NEW production-code regressions. Existing integration errors requiring unavailable external credentials must be listed separately and may not be counted as functional PASSes.

## Required report

Publish exactly:

`qa_reports/CORE8_E2E_RETEST_011F.md`

The report must contain all sections A-I, exact branch/HEAD, commands or reproducible call descriptions, and a machine-readable footer.

Required footer keys:

```text
ASSIGNMENT_ID = CORE8_E2E_RETEST_011F
CURRENT_HEAD = <sha>
SEMANTIC_HIGH_PRECISION_RECOVERY_PASS = YES|NO
UNSUPPORTED_REQUESTS_FAIL_CLOSED = YES|NO
RELEASE_VERSION_ENDPOINT_PASS = YES|NO
REAL_RELEASE_ANCHOR_PASS = YES|NO
CURRENT_SPRINT_GROUNDING_PASS = YES|NO
SPRINT_COMPLETENESS_PASS = YES|NO
CORE8_TASK_SEARCH = PASS|FAIL
CORE8_TASK_SUMMARY = PASS|FAIL
CORE8_TASK_QUALITY = PASS|FAIL
CORE8_SPRINT_HEALTH = PASS|FAIL
CORE8_VELOCITY = PASS|FAIL
CORE8_TEAM_WORKLOAD = PASS|FAIL
CORE8_COMPETENCY_MATCH = PASS|FAIL
CORE8_RELEASE_HEALTH = PASS|FAIL
CORE8_AGENT_E2E_PASS = <n>/8
FALSE_GREEN_ATTACKS_PASS = YES|NO
TARGETED_011E_REGRESSIONS_REMAINING = <n>
NEW_CODE_REGRESSIONS_VS_011E = <n>
AS21_MUTATIONS_DURING_TEST = 0|<n>
READY_FOR_LEARNING_LOOP_012 = YES|NO
```

`READY_FOR_LEARNING_LOOP_012 = YES` only if Core-8 is 8/8, release/source grounding is real, false-green controls pass, AS21 mutations are zero, and no new production regression remains.
