# GigaCode Test Instructions

> Canonical QA handoff from ChatGPT/developer to GigaCode.  
> GigaCode is a tester/adversarial reviewer only unless this file explicitly says otherwise.

## Handoff protocol

1. Before every QA run, GigaCode MUST `git fetch` / pull the target branch and read this file from Git.
2. GigaCode MUST NOT modify production code, tests, fixtures, or this instruction file while executing a QA assignment.
3. GigaCode MAY create/update only the report file named in `REPORT_PATH`, then commit and push that report to the same target branch.
4. Reports must contain commands executed, relevant outputs, sanitized real-data evidence, findings by severity and final gate verdict.
5. ChatGPT/developer reads the report directly from GitHub, implements fixes, updates this instruction file and repeats the cycle.
6. User does not relay screenshots/terminal output between ChatGPT and GigaCode.
7. Never commit credentials, cookies, Authorization headers, tokens or other secrets.

## Current assignment

`ASSIGNMENT_ID = AS21-A2-FILTER-RETEST-002`

`TARGET_BRANCH = feat/real-baseline-candidate-eval-v1`

`REPORT_PATH = qa_reports/AS21_A2_FILTER_RETEST_002.md`

## Context

Read first:
- `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`
- `CORE8_AS21_SOURCE_CONTRACT.md`
- prior report `qa_reports/AS21_A2_REAL_CONTRACT_DISCOVERY_001.md`

The prior report correctly found a BLOCKER: `TaskApiAS21Adapter` sent unsupported `q=<query>` to `/api/v1/tasks`, which FastAPI ignored and therefore broad filters returned the full corpus.

Developer has now changed the deterministic source contract:
- NO `q` parameter is sent;
- equality/AND search grammar is parsed inside `TaskApiAS21Adapter`;
- unknown fields fail closed;
- assignee matching is done against canonical `assignee_id`, `assignee_login`, display name after a bounded read;
- `project_space` maps from proven `source_data.swtr_space`;
- task-api statuses `todo/in_progress/done` map to Open/In progress/Closed;
- truly unknown statuses still map to UNKNOWN;
- sprint/release extraction is conservative and must not be called proven without populated real examples;
- history/attachments remain unsupported at the current task-api boundary.

## QA rules

- DO NOT change production code.
- DO NOT fix failures.
- DO NOT modify tests/fixtures.
- READ ONLY against task-api/AS21.
- The ONLY file you may create/update is the report named above.
- Truthful RED/YELLOW is preferred to false GREEN.

## Procedure

### 1. Pre-check

```bash
git fetch --all --prune
git checkout feat/real-baseline-candidate-eval-v1
git pull --ff-only
git status --short
git log --oneline -12
```

Record HEAD and verify working tree is clean before testing.

### 2. Targeted tests

From `po-agent-platform-v2`:

```bash
pytest -q tests/test_task_api_as21_adapter.py -vv
```

Then run related adapter/source/harness tests already present in repository. Record counts separately.

### 3. Full regression

```bash
pytest -q
```

Report:
- passed/failed/errors/skipped;
- `NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN`.

### 4. Verify source request contract

Using instrumentation/MockTransport/static inspection AND the real endpoint where useful, prove that current adapter never sends `q` to `/api/v1/tasks`.

Expected task-api source parameters are only supported ones (`source`, `limit`, `offset`, and only other native parameters if explicitly used by code).

Report:
- `Q_PARAMETER_USED = YES/NO`
- request examples without secrets.

### 5. Real exact lookup

Using production `TaskApiAS21Adapter`:

`get_task("WMB-30000")`

Expected one exact task, not first arbitrary source record.

Verify canonical:
- key
- status/status_raw/category
- assignee_id/login
- project_space

Expected real project source: `source_data.swtr_space`.

### 6. Real assignee filter matrix

Run using production adapter:

- `assignee = Kalachanov.V.V`
- `assignee = kalachanov.v.v`
- `assignee = nonexistent-user`
- one known different real assignee externalId/login discovered from source data
- `project = WMB AND assignee = Kalachanov.V.V`

For each report COUNT and KEYS (bounded list is fine).

Critical invariants:
- nonexistent user returns 0;
- other assignee tasks do not leak into Kalachanov result;
- lower-case login may match `assignee_login` case-insensitively;
- project+assignee is an intersection, never a broader corpus.

Report:
- `ASSIGNEE_FILTER_CORRECT = YES/NO`
- `FALSE_POSITIVE_ASSIGNEE = YES/NO`

### 7. Real project/space filter

Run:
- `project = WMB`
- one additional real space if available
- `project = NONEXISTENT`

Cross-check every returned task's canonical `project_space` against raw `source_data.swtr_space`.

Report:
- `PROJECT_SPACE_MAPPING = PASS/FAIL`
- `PROJECT_FILTER_CORRECT = YES/NO`

### 8. Real status filter

First inspect a bounded real sample and identify actual task-api status values and, where present, `source_data.workflow_status`.

Then run filters using canonical/user-facing values where possible, including at least:
- `status = Closed` against records with task-api `done` if available;
- `status = In progress` against `in_progress` if available;
- a nonexistent/unknown status value.

Verify task-api `done` does not remain canonical UNKNOWN.

Report:
- `TASK_API_DONE_NORMALIZATION = PASS/FAIL`
- `STATUS_FILTER_CORRECT = YES/NO`
- truly unknown status still remains UNKNOWN.

### 9. Sprint discovery + filter

Search beyond the first 50 records if safe, up to the task-api documented bounded limit, for a real task with populated `sprint` or `scrum_board_plugin_sprint`.

If found:
- record sanitized raw shape;
- record canonical `sprint_id`;
- run `sprint = <real id>`;
- optionally `project = <space> AND sprint = <real id>`;
- prove no task with another sprint appears.

If not found, report `REAL_SPRINT_SAMPLE = NOT_FOUND` and do not fabricate PASS.

### 10. Release discovery + filter

Search bounded real records for non-empty `fix_version_s`.

If found:
- sanitized value shape;
- canonical `release_id`;
- `release = <real id>` filter;
- optional project+release intersection.

If not found, report `REAL_RELEASE_SAMPLE = NOT_FOUND`.

### 11. Free-text search

Choose a distinctive real phrase/key fragment already present in the bounded task set and call `search_tasks(<plain text>)`.

Verify every returned record actually contains the phrase in key/title/description under current deterministic semantics; no `q` is sent to source.

### 12. Fail-closed/adversarial search

Verify:
- `magic = anything` => explicit unsupported-field failure, not broad results;
- malformed clause => explicit failure;
- contradictory duplicate field filters => empty result;
- `max_results=0` => empty result without source broadening;
- `max_results=-1` => validation error;
- source unavailable => `AS21SourceUnavailable`;
- malformed response => `AS21SourceError`.

### 13. Architecture/security review

Confirm no:
- AS21 write authority added;
- LLM filtering;
- hardcoded special cases for Kalachanov/WMB-30000;
- fake fallback corpus;
- autonomous promotion/learning workaround;
- secret leakage.

### 14. Remaining Core-8 source gaps

Re-check, description only:
- attachment metadata read path;
- task history/changelog read path.

Also inspect legacy SWTR/MCP code for a **proven READ-ONLY** source for these facts. Do not wire or change code. If one exists, record exact file/tool/endpoint names for developer.

## Gate interpretation

This assignment primarily decides whether the previous filtering BLOCKER is closed.

`READY_FOR_STEP_A3 = YES` may be returned if exact/assignee/project/status deterministic filtering is correct on real data and no new source blocker exists, even if Gate A overall remains YELLOW because history/attachments or populated sprint/release samples are still pending.

`READY_FOR_LEARNING_LOOP` must remain NO.

## Report format

Create `qa_reports/AS21_A2_FILTER_RETEST_002.md` with:

1. Executive verdict
2. Environment/HEAD
3. Commands executed
4. Targeted tests
5. Full regression
6. Source request contract
7. Exact lookup
8. Assignee matrix
9. Project/space matrix
10. Status matrix
11. Sprint discovery/filter
12. Release discovery/filter
13. Free-text search
14. Fail-closed attacks
15. History/attachments source discovery
16. Security/architecture review
17. Findings by severity
18. Gate decision

End exactly with:

```text
ASSIGNMENT_ID = AS21-A2-FILTER-RETEST-002
Q_PARAMETER_USED =
REAL_TASK_API_CONNECTED =
EXACT_TASK_LOOKUP =
ASSIGNEE_FILTER_CORRECT =
FALSE_POSITIVE_ASSIGNEE =
PROJECT_SPACE_MAPPING =
PROJECT_FILTER_CORRECT =
TASK_API_DONE_NORMALIZATION =
STATUS_FILTER_CORRECT =
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

Only report file may be modified:

```bash
git add qa_reports/AS21_A2_FILTER_RETEST_002.md
git commit -m 'qa: report AS21 A2 filter retest 002'
git push origin feat/real-baseline-candidate-eval-v1
git status --short
```

Then tell user only:

`QA report published: qa_reports/AS21_A2_FILTER_RETEST_002.md`
