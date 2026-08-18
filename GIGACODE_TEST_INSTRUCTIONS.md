# GigaCode Test Instructions

> Canonical QA handoff from ChatGPT/developer to GigaCode.  
> GigaCode is a tester/adversarial reviewer only unless this file explicitly says otherwise.

## Handoff protocol

1. Before every QA run, GigaCode MUST `git fetch` / pull the target branch and read this file from Git.
2. GigaCode MUST NOT modify production code, tests, fixtures, or this instruction file while executing a QA assignment.
3. GigaCode MAY create/update only the report file named in `REPORT_PATH` below, then commit and push that report to the same target branch.
4. The report must contain commands executed, relevant outputs/summaries, real-data evidence (sanitized), findings by severity, and the final gate verdict.
5. ChatGPT/developer reads the report directly from GitHub, implements fixes, updates this instruction file for the next run, and repeats the cycle.
6. User does not need to relay screenshots or copy terminal output between ChatGPT and GigaCode.
7. Never commit credentials, cookies, authorization headers, tokens, or unsanitized secrets.

## Current assignment

`ASSIGNMENT_ID = AS21-A2-REAL-CONTRACT-DISCOVERY-001`

`TARGET_BRANCH = feat/real-baseline-candidate-eval-v1`

`REPORT_PATH = qa_reports/AS21_A2_REAL_CONTRACT_DISCOVERY_001.md`

### Context

Current roadmap documents:
- `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`
- `CORE8_AS21_SOURCE_CONTRACT.md`

Current phase: restore deterministic AS21 source contract before Core-8 real-data qualification and before returning to the learning loop.

Already implemented by developer:
- canonical `Task` has `TaskStatus.UNKNOWN` / `StatusCategory.UNKNOWN`;
- `status_raw`, `assignee_login`, `project_space`, diagnostic `source_data`;
- production `TaskApiAS21Adapter` owns deterministic mapping rather than delegating to permissive legacy mapping;
- `assigned_to.value.externalId` is the canonical candidate for `assignee_id` / login;
- unknown source status must not silently become Open;
- sprint/release mapping must remain fail-closed until their real payload shapes are observed.

## QA rules

- DO NOT change production code.
- DO NOT fix failures.
- DO NOT modify existing tests to make them pass.
- DO NOT create fake AS21 data as evidence for a real-data gate.
- READ-ONLY access to AS21/task-api only.
- Do not call create/update/comment/transition/write APIs.
- A truthful YELLOW/RED/BLOCKED result is preferred to a false GREEN.

## Test procedure

### 1. Pre-check

From repository root:

```bash
git fetch --all --prune
git checkout feat/real-baseline-candidate-eval-v1
git pull --ff-only
git status --short
git log --oneline -10
```

Read this file and both roadmap/source-contract documents before testing.

### 2. Targeted adapter tests

From `po-agent-platform-v2`:

```bash
pytest -q tests/test_task_api_as21_adapter.py -vv
```

Also discover and run existing tests directly related to:
- `TaskApiAS21Adapter`
- `AS21Adapter`
- `LegacyAS21Bridge`
- canonical Task mapping
- task intelligence
- frozen AS21 / SWTR shadow

Record pass/fail counts. Do not repair failures.

### 3. Full regression

```bash
pytest -q
```

Record passed/failed/errors/skipped and determine:

`NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN = N`

Do not classify an existing failure as new without comparison evidence.

### 4. Real task-api connectivity

Check the real local read-only task-api at `http://localhost:8003`.

```bash
curl -sS 'http://localhost:8003/api/v1/tasks?limit=5'
```

Sanitize report output. Never include secrets/headers/tokens.

### 5. Real assignee mapping

Use production `TaskApiAS21Adapter` to read real task `WMB-30000`.

Record canonical fields:
- key
- title
- status
- status_raw
- status_category
- assignee
- assignee_id
- assignee_login
- project_space
- sprint_id
- release_id
- source

Critical assertion: canonical `assignee_id` must equal the real `assigned_to.value.externalId` (known example: `Kalachanov.V.V`, if still true in source data).

Record a sanitized structural view of the raw `assigned_to` attribute: code/name/value keys only.

### 6. Unknown-status fail-closed

Verify by test/static review that an unknown raw AS21 status maps to:
- `TaskStatus.UNKNOWN`
- `StatusCategory.UNKNOWN`
- original value preserved in `status_raw`

It must never silently become `Open`.

### 7. Discover real sprint contract

Find at least one real WMB task with sprint populated. Do not change mapper.

Identify the actual attribute code (expected candidate `scrum_board_plugin_sprint`, but source data decides), value type/shape, relevant object keys, and candidate canonical sprint identifier/name.

Sanitize personal/business-sensitive values where not needed.

Report:
- `REAL_SPRINT_ATTRIBUTE_CODE`
- `REAL_SPRINT_VALUE_SHAPE`
- `CANONICAL_SPRINT_ID_CANDIDATE_FIELD`

### 8. Discover real release contract

Find a real task with release/fix-version if available. Inspect likely attributes such as `fix_version_s`/actual source code.

Report:
- `REAL_RELEASE_ATTRIBUTE_CODE`
- `REAL_RELEASE_VALUE_SHAPE`
- `CANONICAL_RELEASE_ID_CANDIDATE_FIELD`

If no sample exists, report `REAL_RELEASE_SAMPLE = NOT_FOUND`; do not invent a contract.

### 9. Discover project/space contract

Determine the strongest actual source for project/space: top-level field, `source_data`, `swtr_attributes`, or only task-key prefix.

Report:
- `REAL_PROJECT_SPACE_SOURCE`
- example sanitized value
- source level

Do not assume key prefix is authoritative unless no stronger source exists.

### 10. Attachment metadata contract

Inspect code/routes and real read-only payloads for attachment metadata support. Do not download attachment contents unless necessary.

Report:
- `ATTACHMENT_METADATA_AVAILABLE = YES/NO`
- `ATTACHMENT_SOURCE_PATH`
- available metadata fields

### 11. Task history contract

Inspect available read-only APIs/payloads for changelog/status-transition/history data.

Report:
- `TASK_HISTORY_AVAILABLE = YES/NO`
- `TASK_HISTORY_SOURCE_PATH`
- available history fields

### 12. Raw-to-canonical matrix

For at least 5 real tasks compare raw task-api facts to canonical Task for:
- key
- title
- description
- raw/normalized status
- assignee display
- assignee externalId/login
- project/space
- sprint
- release
- priority
- created_at
- updated_at
- due/deadline
- source
- source_url

Classify each field: `MAPPED`, `MISSING_CANONICAL`, `SOURCE_NOT_PRESENT`, or `INCORRECT_MAPPING`.

### 13. Real filter smoke

Test only operations genuinely supported by the current contract. At minimum:
- exact lookup `WMB-30000`;
- assignee identity/filter if adapter currently exposes it safely;
- prove a task assigned to another user cannot appear as `Kalachanov.V.V`.

Do not declare sprint/release/project filtering GREEN until their contracts are proven.

### 14. Security/adversarial review

Confirm A2 did not introduce:
- AS21 write authority;
- autonomous promotion/rollback;
- learning mutation as a source-layer workaround;
- LLM-based filtering;
- hard-coded special case for `Kalachanov` or `WMB-30000`;
- secrets/tokens;
- fake fallback tasks.

Identity extraction must be generic from source structure.

## Report requirements

Create `qa_reports/AS21_A2_REAL_CONTRACT_DISCOVERY_001.md` with sections:

1. Executive verdict
2. Environment / branch / HEAD
3. Commands executed
4. Targeted tests
5. Full regression
6. Real task-api connectivity
7. Assignee mapping
8. Status mapping
9. Sprint contract discovery
10. Release contract discovery
11. Project/space contract discovery
12. Attachments contract
13. History contract
14. Raw -> canonical matrix
15. Real filter smoke
16. Security/adversarial review
17. Findings by severity (`BLOCKER/HIGH/MEDIUM/LOW/INFO`)
18. Recommended next implementation (description only; DO NOT implement)
19. Gate decision

End the report with exactly these machine-readable lines:

```text
ASSIGNMENT_ID = AS21-A2-REAL-CONTRACT-DISCOVERY-001
REAL_TASK_API_CONNECTED =
REAL_TASKS_INSPECTED =
ASSIGNEE_ID_MAPPING =
UNKNOWN_STATUS_FAIL_CLOSED =
REAL_SPRINT_ATTRIBUTE_CODE =
REAL_SPRINT_VALUE_SHAPE =
REAL_RELEASE_ATTRIBUTE_CODE =
REAL_RELEASE_VALUE_SHAPE =
REAL_PROJECT_SPACE_SOURCE =
ATTACHMENT_METADATA_AVAILABLE =
TASK_HISTORY_AVAILABLE =
NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN =
BLOCKER_COUNT =
HIGH_COUNT =
GATE_A =
READY_FOR_STEP_A3 =
```

`READY_FOR_STEP_A3 = YES` only when required deterministic mappings are proven. A YELLOW result is expected and acceptable if sprint/release/project still need implementation.

## Publishing the report

The report file is the ONLY repository file GigaCode may modify for this assignment.

After writing it:

```bash
git status --short
git add qa_reports/AS21_A2_REAL_CONTRACT_DISCOVERY_001.md
git commit -m 'qa: report AS21 A2 real contract discovery'
git push origin feat/real-baseline-candidate-eval-v1
git status --short
```

Final working tree must be clean.

After push, GigaCode should tell the user only:

`QA report published: qa_reports/AS21_A2_REAL_CONTRACT_DISCOVERY_001.md`

ChatGPT/developer will read the report directly from GitHub and continue implementation.
