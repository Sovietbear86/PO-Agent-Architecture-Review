# GigaCode Test Instructions

> Canonical QA handoff from ChatGPT/developer to GigaCode. GigaCode is tester/adversarial reviewer only.

## Handoff protocol
1. Pull the target branch and read this file before every run.
2. Do not modify production code, existing tests, fixtures, roadmap docs, or this file.
3. The ONLY repository file you may create/update is `REPORT_PATH`.
4. Commit and push the report to the same target branch.
5. Never commit credentials, cookies, Authorization headers, tokens, attachment contents, or secrets.
6. Prefer truthful RED/YELLOW/BLOCKED over false GREEN.

## Current assignment

`ASSIGNMENT_ID = AS21-A3-ATTACHMENT-WIRING-RETEST-005`

`TARGET_BRANCH = feat/real-baseline-candidate-eval-v1`

`REPORT_PATH = qa_reports/AS21_A3_ATTACHMENT_WIRING_RETEST_005.md`

Read first:
- `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`
- `CORE8_AS21_SOURCE_CONTRACT.md`
- `qa_reports/AS21_A3_EXTENDED_SOURCE_DISCOVERY_004.md`

## Context

A3 discovery proved a real attachment source:
- real task `WMB-30000` has attachment(s);
- MCP tool `get_unit_files(unit_code, safe)` returns metadata;
- `download_unit_file` exists but must NOT be used in this assignment;
- current Harness should not spawn MCP directly.

Developer has now added a read-only facade in task-api:

`GET /api/v1/swtr-read/tasks/{task_code}/files`

Implementation:
- `task-api/app/routers/swtr_read.py`
- registered in `task-api/main.py`
- facade calls only MCP `get_unit_files` with `safe=True`;
- `TaskApiAS21Adapter.get_attachment_metadata()` calls this endpoint and maps metadata to canonical `Attachment`;
- `TaskApiAS21Adapter.source_facts` intentionally still advertises only `tasks` until this real QA is GREEN.

Do NOT change code.

## QA rules
- READ ONLY against AS21/SWTR/MCP/task-api.
- Do not call download/create/update/delete/comment/transition/sync/save tools.
- Do not expose file contents.
- Sanitized metadata only.
- Do not modify tests to make them pass.

## Procedure

### 1. Pre-check
```bash
git fetch --all --prune
git checkout feat/real-baseline-candidate-eval-v1
git pull --ff-only
git status --short
git log --oneline -15
```
Record HEAD and confirm clean working tree.

### 2. Targeted regression
From `po-agent-platform-v2`:
```bash
pytest -q tests/test_task_api_as21_adapter.py -vv
pytest -q tests/test_as21_adapter.py tests/test_harness_source_readiness.py -vv
```
Run full `pytest -q` afterwards and compute `NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN`.

### 3. Task-api router import/startup
Start the real task-api on the repository's normal port/config. Verify startup succeeds with new `swtr_read` router.

Check OpenAPI or route list contains:
`GET /api/v1/swtr-read/tasks/{task_code}/files`

Report `SWTR_READ_ROUTE_REGISTERED = YES/NO`.

### 4. Real attachment metadata facade
Call only:
`GET http://localhost:8003/api/v1/swtr-read/tasks/WMB-30000/files`

Do not call content download.

Expected:
- HTTP 200;
- `task_code == WMB-30000`;
- `files` is an array;
- at least one real file;
- every returned item is metadata only.

Record sanitized per-file facts only:
- id present? YES/NO (do not publish full UUID; hash/redact it);
- filename extension or generic type (filename may be redacted if sensitive);
- size number;
- contentType;
- created timestamp presence;
- version/hash/storageType presence.

Report:
`REAL_ATTACHMENT_FACADE = PASS/FAIL`
`REAL_ATTACHMENT_COUNT = N`
`ATTACHMENT_CONTENT_DOWNLOADED = NO`

### 5. Production Harness adapter mapping
Using production `TaskApiAS21Adapter(base_url="http://localhost:8003")`, call:
`get_attachment_metadata("WMB-30000")`.

Verify each canonical Attachment:
- id present;
- name present;
- `size_bytes` equals raw metadata size;
- `created_at` parsed;
- `type` correctly classified from MIME/extension;
- `url is None` (metadata path must not expose automatic content download);
- count equals raw facade count.

Report `CANONICAL_ATTACHMENT_MAPPING = PASS/FAIL`.

### 6. Specific attachment filtering
Take one real attachment id only in process memory (do not print full id) and call:
`get_attachment_metadata("WMB-30000", attachment_id=<id>)`.

Expected exactly one matching canonical item.

Report `ATTACHMENT_ID_FILTER = PASS/FAIL`.

### 7. Empty/nonexistent task behavior
Find or use a real task known to have no files, if available, and verify empty `files` -> canonical empty list.

For invalid task code syntax, verify fail-safe local behavior / HTTP 400 as appropriate.

For a syntactically valid nonexistent task, record actual source behavior without inventing expected semantics. It must never return WMB-30000's files or another task's files.

Report `ATTACHMENT_FALSE_POSITIVE = YES/NO`.

### 8. Failure semantics
Using MockTransport/unit tests/static inspection, verify:
- malformed endpoint payload -> `AS21SourceError`;
- malformed file item -> `AS21SourceError`;
- transport failure -> `AS21SourceUnavailable`;
- non-200 source failure does not become a false empty success except explicit 404 handling;
- no broad fallback to unrelated files.

### 9. Read-only security audit
Inspect new router and adapter. Confirm:
- router invokes only `get_unit_files`;
- `safe=True` is passed;
- no `download_unit_file` call;
- no create/update/delete/comment/transition/sync/save;
- no token returned/logged;
- Harness still has no AS21 write authority.

Report `READ_ONLY_ATTACHMENT_BOUNDARY = PASS/FAIL`.

### 10. Source-readiness decision
Because `source_facts` still contains only `tasks`, verify attachment-dependent skills remain unavailable until developer explicitly promotes the proven source fact.

This is expected for this assignment.

Report:
`ATTACHMENTS_ADVERTISED_BEFORE_QA = NO`.

### 11. Sprint/release/history status reminder
Do not spend time trying to fix these. Briefly carry forward discovery 004 status:
- sprint current-source = PARTIAL / invalid-parameters issue;
- release source = PARTIAL via `search_versions` + `fix_version_s`;
- comments = PROVEN REAL but NOT status-transition history.

## Gate logic

This assignment can be GREEN even while overall Gate A remains YELLOW.

`ATTACHMENT_WIRING_READY_FOR_PROMOTION = YES` only if:
- real facade works on WMB-30000;
- canonical mapping works;
- no content download;
- no false-positive cross-task files;
- no new regressions;
- read-only boundary passes.

## Report format
Create `qa_reports/AS21_A3_ATTACHMENT_WIRING_RETEST_005.md` with:
1. Executive verdict
2. Environment/HEAD
3. Targeted/full regression
4. Route/startup proof
5. Real WMB-30000 attachment facade
6. Canonical adapter mapping
7. Specific-id filtering
8. Empty/nonexistent behavior
9. Failure semantics
10. Read-only/security audit
11. Source-readiness state
12. Findings by severity
13. Gate decision

End with exactly:
```text
ASSIGNMENT_ID = AS21-A3-ATTACHMENT-WIRING-RETEST-005
REAL_TASK_API_CONNECTED =
SWTR_READ_ROUTE_REGISTERED =
REAL_ATTACHMENT_FACADE =
REAL_ATTACHMENT_COUNT =
CANONICAL_ATTACHMENT_MAPPING =
ATTACHMENT_ID_FILTER =
ATTACHMENT_FALSE_POSITIVE =
ATTACHMENT_CONTENT_DOWNLOADED = NO
READ_ONLY_ATTACHMENT_BOUNDARY =
ATTACHMENTS_ADVERTISED_BEFORE_QA = NO
NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN =
BLOCKER_COUNT =
HIGH_COUNT =
ATTACHMENT_WIRING_READY_FOR_PROMOTION =
GATE_A = YELLOW
READY_FOR_LEARNING_LOOP = NO
```

## Publish
```bash
git add qa_reports/AS21_A3_ATTACHMENT_WIRING_RETEST_005.md
git commit -m 'qa: report AS21 A3 attachment wiring retest 005'
git push origin feat/real-baseline-candidate-eval-v1
git status --short
```

Then tell user only:
`QA report published: qa_reports/AS21_A3_ATTACHMENT_WIRING_RETEST_005.md`
