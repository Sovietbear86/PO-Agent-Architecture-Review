# QA Assignment: CORE8 E2E REMEDIATION 011C

## Mission

Close the remaining gaps found by `CORE8_REAL_AS21_BASELINE_011.md` before any Learning Loop work starts.

This is a **production-path remediation gate**, not a new architecture redesign.

Do not proceed to Learning Loop 012 until this assignment is GREEN.

## ROLE BOUNDARY — IMPORTANT

**GigaCode is TESTER/REVIEWER ONLY in this assignment.**

- Do NOT edit production code.
- Do NOT edit tests unless explicitly instructed in a later QA assignment authored by the developer.
- Do NOT apply automatic fixes suggested by the IDE.
- Do NOT change routers, adapters, Harness runtime, semantic layer, configuration, schemas, models, or knowledge files.
- If a defect is found, document the exact file/function/route, evidence, expected behavior and proposed fix in the QA report, then continue all tests that remain safe.
- Code changes are performed by the developer outside GigaCode.

The current developer fix for the Task API collection-route contract is commit `09fc32a8c193fd9a7665bdbb05c9b475bce04dd5`:
- `GET /api/v1/tasks` is defined by `@router.get("")`;
- `POST /api/v1/tasks` is defined by `@router.post("")`;
- item routes such as `PUT /api/v1/tasks/{task_id}`, `PATCH /api/v1/tasks/{task_id}/status`, `DELETE /api/v1/tasks/{task_id}` remain unchanged.

GigaCode must TEST this contract, not modify it.

## Authoritative Core-8

Validate all eight capabilities:

1. `task_search`
2. `task_summary`
3. `task_quality`
4. `sprint_health`
5. `velocity`
6. `team_workload`
7. `competency_match`
8. `release_health`

Reference `CORE8_AS21_SOURCE_CONTRACT.md` and the project master evolution plan/specification. Do not silently redefine the skills.

## Non-negotiable E2E definition

A skill is GREEN only when its required user-facing scenario works through the real production agent path:

`natural-language user query -> semantic interpretation -> Harness/runtime -> skill/capability -> Task API -> MCP/SWTR/knowledge source -> canonical model -> answer + evidence`

Adapter-only, endpoint-only, unit-test-only, config-file-only, or mocked execution is useful diagnostic evidence but **MUST NOT** be counted as E2E GREEN.

For each Core-8 skill report separately:

- adapter/contract status;
- production-agent E2E status;
- real AS21/knowledge evidence;
- exact query used;
- expected result;
- actual result;
- evidence IDs/task IDs/sprint IDs/release IDs;
- blocker if not GREEN.

## Step 1 — Pre-check

Before testing:

- fetch/pull current branch;
- record branch and HEAD;
- ensure working tree is clean before test execution;
- read `CORE8_REAL_AS21_BASELINE_011.md`;
- read `CORE8_AS21_SOURCE_CONTRACT.md`;
- read the master evolution plan/specification;
- inspect the current production routing for `/api/v1/tasks`, `/api/v1/query`, Task API adapter and semantic interpreter **without modifying them**.

Do not overwrite unrelated user changes.

## Step 2 — Verify Task API canonical route

Previous baseline found:

`GET /api/v1/tasks -> 307 -> /api/v1/tasks/`

Developer fix is already committed in `09fc32a8c193fd9a7665bdbb05c9b475bce04dd5`.

Verify:

- `GET /api/v1/tasks` works directly without a 307 redirect;
- `POST /api/v1/tasks` is registered on the slashless collection route;
- item routes retain their path parameters;
- `search_tasks()` works through the production Task API path;
- `get_task()` works through the production Task API path;
- existing `swtr-read` functionality remains intact;
- no AS21 mutations occur during read-only QA scenarios.

Do not change route definitions if any check fails; record the defect.

## Step 3 — Semantic layer investigation

Baseline says `/api/v1/query` returns `semantic_interpretation_failure` and `llm_api_key` is not set.

Do **not** ask the user to paste a secret/API key and do not commit secrets.

Investigate repository history, configuration, `.env.example`/settings, prior working commits, documentation and launch scripts to determine how the semantic LLM was intended to be configured in this application.

Determine:

- expected provider/endpoint;
- expected model;
- expected environment variable names;
- whether the previous working application used another configuration path;
- whether local/dev mode has a supported mechanism;
- whether GigaCode environment already exposes a usable credential without printing it.

Secrets must never be written to Git, QA reports or console output.

If configuration is missing, report the exact non-secret requirement. Do not modify configuration or semantic production code.

For this gate:

`SEMANTIC_LAYER_OPERATIONAL = YES` is required for final GREEN because the production user path starts with a natural-language query.

## Step 4 — Real release-health anchor

Do not mark `release_health` GREEN merely because `fix_version_s` exists in schema.

Use MCP/SWTR `search_versions` and/or legitimate read-only source endpoints to find at least one real release/version associated with WMB, DMS or OLP. Then identify real tasks connected to that release/version and prove canonical extraction/filtering.

Record:

- release/version ID and name;
- source space;
- real task IDs;
- source attribute(s), including `fix_version_s` where applicable;
- production-agent query and result.

If no valid real release exists, mark the skill YELLOW with evidence. Do not fabricate fixtures and call them real-data validation.

## Step 5 — Core-8 production E2E matrix

Execute real user-style queries for every skill. At minimum cover the following intent classes.

### task_search

Real queries covering combinations of space/project, assignee, status and sprint. Prove AND semantics and fail-closed behavior.

Use known real anchors where still valid, including WMB, DMS and OLP.

### task_summary

Use exact real task lookup, including `WMB-30000`. Prove summary/title and description are preserved and evidence refers to the exact task, not the first search hit.

### task_quality

Run the capability through the agent, not just `get_task()`. Quality assessment must be based on real task attributes such as description/status/attachments and return evidence.

Use `WMB-30000` as a rich attachment anchor when appropriate. Office attachments, including XLSX, must remain visible.

### sprint_health

Use real DMS and/or OLP current sprint data. Prove sprint identity, status, dates and task context through the production agent path.

### velocity

Use real sprint tasks, traverse all pages, deduplicate, and calculate the intended velocity metric according to the authoritative skill contract. A raw `100 tasks` count alone is not sufficient if the skill definition requires more.

### team_workload

Use the authoritative team roster from the repository and real DMS/OLP tasks. Validate workload for actual team members, with assignee extraction/filtering proven from SWTR attributes.

Do not equate `search_tasks()` working with `team_workload` being E2E GREEN.

### competency_match

The presence of `knowledge/team/competencies.md` is **not** a passing test.

Run a real competency-matching request through the production agent. The result must combine the authoritative team/competency knowledge with evidence from real task/work context as required by the skill definition. Show why a member matches a competency/request.

### release_health

Use the real release anchor discovered in Step 4 and run the actual capability through the production agent.

## Step 6 — Pagination and completeness

Prove pagination on real data for DMS/OLP where multiple pages exist.

Requirements:

- traverse until `hasNext=false` or equivalent source termination;
- no duplicate task IDs;
- no silent first-page truncation;
- filtering remains correct across page boundaries;
- record total source items read and total canonical items after filtering.

## Step 7 — False-green / adversarial attacks

Repeat and extend false-green attacks:

- nonexistent task;
- nonexistent assignee;
- nonexistent project/space;
- nonexistent sprint;
- nonexistent release/version;
- unknown filter;
- contradictory filters;
- exact-key lookup must not return another task;
- attachment metadata must not leak across tasks;
- pagination must not create duplicates;
- semantic query must not silently fall back to unfiltered/all-task output;
- config/knowledge presence alone must not count as skill execution;
- adapter success while production agent fails must produce E2E RED/YELLOW, never GREEN.

## Step 8 — Regression

Run targeted tests and the complete existing regression suite.

Required:

- no new code regressions versus the previous green baseline;
- no AS21 mutations;
- attachment functionality from 010B remains GREEN;
- AS21 attribute extraction/filtering remains GREEN.

If any regression is found, report it; do not patch it in GigaCode.

## Step 9 — Architecture review

Verify the intended boundary remains:

`AS21/SWTR -> source adapter -> canonical domain model -> Harness capabilities -> semantic/user-facing layer`

Source-specific SWTR details must remain encapsulated at the adapter/source-contract boundary wherever practical. Harness skills should consume canonical data rather than relearn SWTR JSON shapes independently.

Explicitly report any architectural bypass found.

## Gate criteria

`READY_FOR_LEARNING_LOOP_012 = YES` only if all are true:

- `CORE8_RECOVERED = 8/8`
- `CORE8_ADAPTER_CONTRACT_PASS = 8/8`
- `CORE8_REAL_DATA_PASS = 8/8`
- `CORE8_AGENT_E2E_PASS = 8/8`
- `SEMANTIC_LAYER_OPERATIONAL = YES`
- `TASK_API_CANONICAL_ROUTE_PASS = YES`
- `PAGINATION_COMPLETENESS_PASS = YES`
- `RELEASE_REAL_ANCHOR_PASS = YES`
- `ATTACHMENT_REGRESSION_PASS = YES`
- `FALSE_GREEN_ATTACKS_PASS = YES`
- `NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN = 0`
- `AS21_MUTATIONS_DURING_TEST = 0`
- no HIGH blockers remain.

If any condition fails, set `READY_FOR_LEARNING_LOOP_012 = NO`.

## Required QA report

Publish:

`qa_reports/CORE8_E2E_REMEDIATION_011C.md`

The report must contain:

1. Executive verdict.
2. Branch / HEAD / environment (no secrets).
3. Tested developer commit SHAs.
4. Redirect/root-cause verification.
5. Semantic-layer configuration investigation.
6. Real release/version discovery evidence.
7. 8-row Core-8 adapter matrix.
8. 8-row Core-8 **production E2E** matrix.
9. Exact natural-language query and actual answer/evidence for each skill.
10. Pagination/completeness proof.
11. False-green attacks.
12. Targeted + full regression results.
13. Architecture review.
14. Blockers and proposed fixes (no code edits).
15. Machine-readable summary.

## Machine-readable summary format

```text
ASSIGNMENT_ID = CORE8_E2E_REMEDIATION_011C
CORE8_RECOVERED = x/8
CORE8_ADAPTER_CONTRACT_PASS = x/8
CORE8_REAL_DATA_PASS = x/8
CORE8_AGENT_E2E_PASS = x/8
SEMANTIC_LAYER_OPERATIONAL = YES|NO
TASK_API_CANONICAL_ROUTE_PASS = YES|NO
PAGINATION_COMPLETENESS_PASS = YES|NO
RELEASE_REAL_ANCHOR_PASS = YES|NO
ATTACHMENT_REGRESSION_PASS = YES|NO
FALSE_GREEN_ATTACKS_PASS = YES|NO
NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN = N
AS21_MUTATIONS_DURING_TEST = N
HIGH_BLOCKER_COUNT = N
READY_FOR_LEARNING_LOOP_012 = YES|NO
```

## Stop rule

When the report is published, STOP. Do not edit code, do not begin Learning Loop 012, do not expand Core-8 to 48 skills, and do not start frontend finalization in this assignment.

The next phase is authorized only after developer review of this report.
