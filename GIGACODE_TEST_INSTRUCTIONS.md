# GigaCode Test Instructions

> Canonical QA handoff from ChatGPT/developer to GigaCode. GigaCode is tester/adversarial reviewer only.

## Handoff protocol

1. Pull the target branch and read this file before every run.
2. Do not modify production code, existing tests, fixtures, roadmap docs, or this file.
3. The ONLY repository file you may create/update is `REPORT_PATH` below.
4. Commit and push the report to the same target branch.
5. Never commit credentials, cookies, Authorization headers, tokens, or secrets.
6. Prefer truthful RED/YELLOW/BLOCKED over false GREEN.

## Current assignment

`ASSIGNMENT_ID = AS21-A2-FILTER-RETEST-003`

`TARGET_BRANCH = feat/real-baseline-candidate-eval-v1`

`REPORT_PATH = qa_reports/AS21_A2_FILTER_RETEST_003.md`

Read first:
- `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`
- `CORE8_AS21_SOURCE_CONTRACT.md`
- prior reports `qa_reports/AS21_A2_REAL_CONTRACT_DISCOVERY_001.md` and `qa_reports/AS21_A2_FILTER_RETEST_002.md`

## What changed since retest 002

The previous real run found that at least one AS21 task has a description longer than 10,000 characters. Canonical `Task.description` rejected it, so the bounded corpus scan failed before filtering.

Developer fix:
- removed the arbitrary 10k limit from canonical `Task.description`;
- preserves the FULL AS21 description (no truncation and no silent skipping);
- added a regression test with a 25,000-character real-shaped description;
- existing `q`-parameter fix remains in place;
- assignee/project/status filtering remains deterministic over canonical facts.

## QA rules

- READ ONLY AS21/task-api.
- Do not call create/update/delete/comment/transition/write routes.
- Do not patch code when something fails.
- Do not use mock results as evidence for real-data gates.

## Procedure

### 1. Pre-check

```bash
git fetch --all --prune
git checkout feat/real-baseline-candidate-eval-v1
git pull --ff-only
git status --short
git log --oneline -12
```

Record HEAD and verify working tree clean.

### 2. Targeted tests

From `po-agent-platform-v2`:

```bash
pytest -q tests/test_task_api_as21_adapter.py -vv
pytest -q tests/test_domain_models.py -vv
pytest -q tests/test_as21_adapter.py tests/test_frozen_as21.py tests/test_harness_source_readiness.py -vv
```

Important: if the old domain test still expects unknown status -> OPEN, classify it explicitly as a stale test expectation against the new fail-closed source contract; do not modify it.

### 3. Full regression

```bash
pytest -q
```

Report pass/fail/error/skip and `NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN`.

### 4. Prove long-description blocker is gone on REAL data

Use production `TaskApiAS21Adapter` against `http://localhost:8003`.

Perform a bounded real scan/search that previously failed. Confirm no canonical validation error occurs for descriptions >10k.

Report:
- `REAL_LONG_DESCRIPTION_TASKS_FOUND`
- maximum observed description length (number only)
- `LONG_DESCRIPTION_MAPPING = PASS/FAIL`
- whether full text length is preserved (do not print full long descriptions)

### 5. Exact task lookup

Read real `WMB-30000` through production adapter.

Verify exact key only, title/description, assignee_id/externalId mapping, project_space, normalized status/status_raw, and no broad false positive.

### 6. Real assignee matrix

Run through production adapter:
- `assignee = Kalachanov.V.V`
- `assignee = kalachanov.v.v`
- `assignee = nonexistent-user`

For the first two, independently inspect returned canonical tasks and prove every task's `assignee_id` or `assignee_login` matches the requested identity. Nonexistent user must return empty.

Critical: `FALSE_POSITIVE_ASSIGNEE = NO`.

### 7. Real project/space matrix

Run:
- `project = WMB`
- `project = NONEXISTENT`
- `project = WMB AND assignee = Kalachanov.V.V`

Every WMB result must have canonical `project_space == WMB` derived from `source_data.swtr_space`.

### 8. Real status matrix

Discover raw/normalized statuses present in current corpus first. Then query canonical statuses that are genuinely represented. Verify every returned task matches canonical status and no leakage occurs. Prove raw task-api `done` -> canonical `Closed` where applicable, while truly unknown statuses remain UNKNOWN.

### 9. Free-text search

Choose one rare phrase from a real task title/description. Query it through production adapter and prove returned records actually contain it; no broad corpus fallback.

### 10. Sprint discovery

Scan enough bounded real WMB tasks to find a non-empty sprint if one exists. Record sanitized attribute code/value shape/derived `sprint` field/canonical `sprint_id`. If none exists, report `REAL_SPRINT_SAMPLE = NOT_FOUND`.

### 11. Release discovery

Same for `fix_version_s`/real release value. If none exists, report `REAL_RELEASE_SAMPLE = NOT_FOUND`.

### 12. History and attachment discovery

Re-check repository/task-api/legacy read paths. Report whether any proven read-only path exists for attachment metadata and status history/transitions. Do not add code.

### 13. Fail-closed / security

Verify no `q` parameter; unknown field and malformed clause fail closed; nonexistent assignee/project cannot broaden results; no AS21 writes; no LLM filtering; no hardcoded Kalachanov/WMB special case; no fake fallback tasks; no secret leakage.

## Gate logic

If exact/assignee/project/status/free-text now work on real data with zero false positives and no source mapping error, the current filtering blocker is closed.

Gate A may remain YELLOW if sprint/release/history/attachments lack real source evidence needed by Core-8.

`READY_FOR_STEP_A3 = YES` only when the basic real filter matrix is proven sufficiently stable to formalize A3. `READY_FOR_LEARNING_LOOP` remains NO.

## Report format

Create `qa_reports/AS21_A2_FILTER_RETEST_003.md` with:
1. Executive verdict
2. Environment / HEAD
3. Commands executed
4. Targeted tests
5. Full regression
6. Long-description real-data proof
7. Exact lookup
8. Assignee matrix
9. Project matrix
10. Status matrix
11. Free-text search
12. Sprint discovery
13. Release discovery
14. Attachments/history discovery
15. Fail-closed/security
16. Findings by severity
17. Gate decision
18. Recommended next implementation (description only)

End with:

```text
ASSIGNMENT_ID = AS21-A2-FILTER-RETEST-003
REAL_TASK_API_CONNECTED =
REAL_LONG_DESCRIPTION_TASKS_FOUND =
MAX_REAL_DESCRIPTION_LENGTH =
LONG_DESCRIPTION_MAPPING =
EXACT_TASK_LOOKUP =
ASSIGNEE_FILTER_CORRECT =
FALSE_POSITIVE_ASSIGNEE =
PROJECT_SPACE_MAPPING =
PROJECT_FILTER_CORRECT =
TASK_API_DONE_NORMALIZATION =
STATUS_FILTER_CORRECT =
FREE_TEXT_FILTER_CORRECT =
REAL_SPRINT_SAMPLE =
SPRINT_FILTER_CORRECT =
REAL_RELEASE_SAMPLE =
RELEASE_FILTER_CORRECT =
ATTACHMENT_METADATA_AVAILABLE =
TASK_HISTORY_AVAILABLE =
NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN =
BLOCKER_COUNT =
HIGH_COUNT =
GATE_A =
READY_FOR_STEP_A3 =
READY_FOR_LEARNING_LOOP = NO
```

## Publish

```bash
git add qa_reports/AS21_A2_FILTER_RETEST_003.md
git commit -m 'qa: report AS21 A2 filter retest 003'
git push origin feat/real-baseline-candidate-eval-v1
git status --short
```

Final working tree clean. Tell the user only:

`QA report published: qa_reports/AS21_A2_FILTER_RETEST_003.md`
