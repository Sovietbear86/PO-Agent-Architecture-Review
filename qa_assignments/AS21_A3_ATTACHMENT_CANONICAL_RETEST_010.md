# QA Assignment: AS21-A3-ATTACHMENT-CANONICAL-RETEST-010

## Context
Read first:
- `qa_reports/AS21_A3_ATTACHMENT_AND_SPRINT_RETEST_009.md`
- `CORE8_AS21_SOURCE_CONTRACT.md`
- `CORE8_TEAM_SPRINT_DISCOVERY_CONTRACT.md`

Developer fixed the canonical attachment mapper to support the real MCP-SWTR metadata shape proven in RETEST-009:
- `fileId`
- `filePathParsedDto.fileName`
- `fileMetadataDto.contentLength`
- `fileMetadataDto.contentType`
- `createdAt`

The mapper still supports the legacy normalized aliases for backward compatibility, but real AS21 shape is authoritative.

## Rules
- Tester/reviewer only.
- Do NOT modify production code or existing tests.
- Publish only the QA report.
- Use real AS21/SWTR via the existing SSE transport.
- No attachment content download.
- Do not proceed to learning loop.

## Required checks

### 1. Live transport
Verify:
- MCP-SWTR SSE reachable;
- Task API reachable;
- `/api/v1/swtr-read/health` == 200;
- `read_unit(WMB-30000)` == 200.

### 2. Real attachment facade
Call:
`GET /api/v1/swtr-read/tasks/WMB-30000/files`

Assert:
- HTTP 200;
- exactly the real attachment count returned by AS21 at test time;
- report current count and IDs/names in sanitized form;
- no content/body bytes downloaded.

### 3. Canonical attachment mapping — critical gate
Using production `TaskApiAS21Adapter.get_attachment_metadata('WMB-30000')` against live Task API, assert each real attachment maps successfully to canonical `Attachment`:
- `id` from `fileId`;
- `name` from `filePathParsedDto.fileName` (or top-level `fileName` if source supplies it);
- `size_bytes` from `fileMetadataDto.contentLength`;
- `created_at` from `createdAt`;
- `type` derived from file name/MIME;
- `url is None` for metadata-only path.

For the known XLSX sample, `type` must be `excel`.

### 4. attachment_id filtering
Choose one real attachment ID returned in step 2.
Call `get_attachment_metadata('WMB-30000', attachment_id=<id>)`.
Assert:
- exactly one attachment returned;
- returned ID equals requested ID;
- nonexistent attachment ID returns empty list;
- no cross-task attachment can leak into result.

### 5. Base task retrieval anti-regression
Re-run real task retrieval and filters already GREEN in A2:
- exact `WMB-30000`;
- `assignee = Kalachanov.V.V`;
- `project = WMB`;
- `project = WMB AND assignee = Kalachanov.V.V`;
- nonexistent assignee -> 0;
- unknown field fails closed.

Report `BASE_TASK_RETRIEVAL_REGRESSION = NO/YES` unambiguously.

### 6. Sprint source confirmation
Re-confirm the real sprint source contract discovered in RETEST-009 without placeholder text.

DMS:
- current sprint ID/name;
- sprint task count returned by source;
- team task count after intersection with `task-api/knowledge/team/team.md`;
- sample team task keys/logins.

OLP:
- current sprint ID/name;
- sprint task count;
- team task count;
- sample team task keys/logins.

If the sprint changes between runs, report the new real value; do not hard-code RETEST-009 values as expected truth.

### 7. Regression
Run targeted adapter tests and full `po-agent-platform-v2` regression.
Compare against RETEST-009 baseline:
- 1166 passed
- 5 pre-existing failed
- 11 errors
- 12 skipped

New regressions must be 0.

## Gate logic
Set:
`ATTACHMENT_WIRING_READY_FOR_PROMOTION = YES`
only if the live canonical adapter successfully maps the real attachments and filtering works.

Set:
`SPRINT_SOURCE_CONTRACT = GREEN`
only if DMS and OLP live sprint/task reads remain proven.

`READY_FOR_CORE8_REAL_E2E = YES` is allowed only if no A3 blocker remains for the Core-8 source facts required at this stage. Do not equate this with learning-loop readiness.

`READY_FOR_LEARNING_LOOP = NO` for this assignment.

## Output
Publish:
`qa_reports/AS21_A3_ATTACHMENT_CANONICAL_RETEST_010.md`

End with:
```text
ASSIGNMENT_ID = AS21-A3-ATTACHMENT-CANONICAL-RETEST-010
MCP_SWTR_CONNECTED =
TASK_API_CONNECTED =
REAL_WMB_30000_READ =
REAL_ATTACHMENT_FACADE =
REAL_ATTACHMENT_COUNT =
CANONICAL_ATTACHMENT_MAPPING =
ATTACHMENT_ID_FILTER =
ATTACHMENT_FALSE_POSITIVE =
ATTACHMENT_CONTENT_DOWNLOADED = NO/YES
BASE_TASK_RETRIEVAL_REGRESSION =
DMS_CURRENT_SPRINT_READ =
DMS_REAL_SPRINT_ID =
DMS_REAL_SPRINT_NAME =
DMS_SPRINT_TASK_COUNT =
DMS_TEAM_TASK_COUNT =
OLP_CURRENT_SPRINT_READ =
OLP_REAL_SPRINT_ID =
OLP_REAL_SPRINT_NAME =
OLP_SPRINT_TASK_COUNT =
OLP_TEAM_TASK_COUNT =
NEW_CODE_REGRESSIONS_VS_RETEST_009 =
BLOCKER_COUNT =
HIGH_COUNT =
ATTACHMENT_WIRING_READY_FOR_PROMOTION =
SPRINT_SOURCE_CONTRACT =
GATE_A = GREEN/YELLOW/RED
READY_FOR_CORE8_REAL_E2E = YES/NO
READY_FOR_LEARNING_LOOP = NO
```
