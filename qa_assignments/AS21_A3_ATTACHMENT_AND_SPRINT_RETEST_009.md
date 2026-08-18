# QA Assignment: AS21-A3-ATTACHMENT-AND-SPRINT-RETEST-009

## Context
Read first:
- `qa_reports/AS21_A3_UNIFIED_SSE_RETEST_008.md`
- `CORE8_TEAM_SPRINT_DISCOVERY_CONTRACT.md`
- `task-api/knowledge/team/team.md`
- `task-api/knowledge/team/competencies.md`

Developer fixed the real attachment envelope discovered in RETEST-008. `get_unit_files` returns a paged payload with `content: [...]`; `swtr_read._extract_files()` now accepts this proven `content` envelope, keeps compatibility with the previously tested `files` envelope, accepts a direct single-file object, and fails closed on unsupported shapes.

Do not modify production code. Tester/reviewer only.

## 1. Pull current branch

```bash
git fetch --all --prune
git checkout feat/real-baseline-candidate-eval-v1
git pull --ff-only
git status --short
git log --oneline -8
```

Record HEAD. Working tree must be clean before testing.

## 2. Live services
Use the already proven MCP-SWTR SSE server on `http://127.0.0.1:3000/sse` and Task API on `:8003`.

If either service is not running, start it using the actual commands proven in RETEST-008. Do not revert to legacy stdio/subprocess transport.

Verify:

```bash
python3 - <<'PY'
import httpx
for url in (
    'http://127.0.0.1:8003/health',
    'http://127.0.0.1:8003/api/v1/swtr-read/health',
):
    r=httpx.get(url, timeout=10)
    print(url, r.status_code, r.text[:500])
PY
```

## 3. Re-prove normal real task retrieval
This is mandatory because rich-read changes must never regress base task reads.

Verify all of:
- `GET /api/v1/swtr-read/tasks/WMB-30000` returns real task data;
- normal `/api/v1/tasks` still returns real SWTR-backed tasks;
- `TaskApiAS21Adapter` exact lookup of `WMB-30000` works;
- assignee filter `Kalachanov.V.V` remains correct and has no foreign-assignee false positives;
- project/space `WMB` remains correct.

Report `BASE_TASK_RETRIEVAL_REGRESSION = NO/YES` with evidence. Note: RETEST-008 printed `BASE_TASK_SEARCH_REGRESSION = YES` while also reporting zero new regressions; resolve this ambiguity explicitly rather than copying it.

## 4. Real attachment facade — WMB-30000
Call:

```bash
python3 - <<'PY'
import json, httpx
u='http://127.0.0.1:8003/api/v1/swtr-read/tasks/WMB-30000/files'
r=httpx.get(u, timeout=30)
print('HTTP', r.status_code)
print(json.dumps(r.json(), ensure_ascii=False, indent=2)[:12000])
PY
```

Required assertions:
- HTTP 200;
- `task_code == WMB-30000`;
- real `files` list is returned;
- expected real count is currently 5 unless source data changed;
- each item is metadata only, not file content;
- no credentials/tokens are exposed.

Record the structural fields actually present, including where available:
`fileId`, `fileName`, `fileMetadataDto.contentType`, `fileMetadataDto.contentLength`, `createdAt`.

## 5. Canonical attachment mapping
Use production `TaskApiAS21Adapter.get_attachment_metadata('WMB-30000')` against the live Task API.

For each returned canonical Attachment record:
- id
- name
- type
- size_bytes
- created_at
- url

Expected:
- count equals real facade count;
- the known xlsx attachment maps to Excel type;
- `url` remains absent/None for metadata-only mode;
- no content download occurs.

Then select one real `attachment_id` and verify the adapter returns only that item. A nonexistent `attachment_id` must return empty, not a different file.

## 6. Attachment false-green attacks
Verify fail-closed behavior for:
- invalid task code;
- syntactically valid nonexistent task;
- malformed attachment envelope fixture/static unit test;
- non-list `content`;
- `content` containing a non-object item;
- MCP outage;
- no cross-task leakage.

## 7. DMS and OLP current sprint — capture actual evidence
RETEST-008 claimed both current-sprint endpoints work, but its machine summary contained placeholders instead of actual sprint IDs. This run must capture the actual sanitized values.

Call:

```bash
python3 - <<'PY'
import json, httpx
for space in ('DMS','OLP'):
    u=f'http://127.0.0.1:8003/api/v1/swtr-read/spaces/{space}/current-sprint'
    r=httpx.get(u, timeout=30)
    print('\nSPACE', space, 'HTTP', r.status_code)
    try: print(json.dumps(r.json(), ensure_ascii=False, indent=2))
    except Exception: print(r.text)
PY
```

Record exact real sprint identifier/name fields returned by AS21. Do not invent a canonical ID if the source shape differs from assumptions.

## 8. Sprint tasks and real team intersection
For each real DMS/OLP current sprint discovered above, call the live sprint-tasks endpoint using the exact source identifier required by MCP.

Use `task-api/knowledge/team/team.md` as the authoritative roster. Do NOT use placeholder identities from `task-api/config/team_members.yaml`.

For each sprint:
- count all sprint tasks;
- extract assignee externalId/login where present;
- intersect with real team AS21 logins from `team.md`;
- report actual matching team members and task keys;
- identify any sprint tasks whose assignee cannot yet be normalized.

Minimum evidence fields:

```text
DMS_REAL_SPRINT_ID =
DMS_REAL_SPRINT_NAME =
DMS_SPRINT_TASK_COUNT =
DMS_TEAM_TASK_COUNT =
DMS_TEAM_LOGINS_FOUND =
DMS_TEAM_TASK_KEYS_SAMPLE =

OLP_REAL_SPRINT_ID =
OLP_REAL_SPRINT_NAME =
OLP_SPRINT_TASK_COUNT =
OLP_TEAM_TASK_COUNT =
OLP_TEAM_LOGINS_FOUND =
OLP_TEAM_TASK_KEYS_SAMPLE =
```

If the sprint-tasks response shape does not carry assignee identity directly, document the exact shape and use read-only `read_unit` for a bounded sample to prove team membership. Do not silently infer by display name if externalId/login is available elsewhere.

## 9. Core-8 readiness implications
Based only on proven real evidence, assess source readiness for:
- `task_search`
- `task_summary`
- `task_quality`
- `sprint_health`
- `velocity`
- `team_workload`
- `competency_match`
- `release_health`

Do not test the learning loop yet. This assignment is source-contract evidence only.

## 10. Regression
Run targeted tests plus full regression and compare with RETEST-008 baseline:
- 1166 passed
- 5 failed (pre-existing)
- 11 errors
- 12 skipped

Any new failure/error caused by the latest change is a regression.

## Output
Publish:

`qa_reports/AS21_A3_ATTACHMENT_AND_SPRINT_RETEST_009.md`

End with:

```text
ASSIGNMENT_ID = AS21-A3-ATTACHMENT-AND-SPRINT-RETEST-009
MCP_SWTR_CONNECTED =
TASK_API_CONNECTED =
REAL_WMB_30000_READ =
BASE_TASK_RETRIEVAL_REGRESSION =
REAL_ATTACHMENT_FACADE =
REAL_ATTACHMENT_COUNT =
CANONICAL_ATTACHMENT_MAPPING =
ATTACHMENT_ID_FILTER =
ATTACHMENT_FALSE_POSITIVE =
ATTACHMENT_CONTENT_DOWNLOADED =
DMS_CURRENT_SPRINT_READ =
DMS_REAL_SPRINT_ID =
DMS_REAL_SPRINT_NAME =
DMS_SPRINT_TASK_COUNT =
DMS_TEAM_TASK_COUNT =
DMS_TEAM_LOGINS_FOUND =
OLP_CURRENT_SPRINT_READ =
OLP_REAL_SPRINT_ID =
OLP_REAL_SPRINT_NAME =
OLP_SPRINT_TASK_COUNT =
OLP_TEAM_TASK_COUNT =
OLP_TEAM_LOGINS_FOUND =
NEW_CODE_REGRESSIONS_VS_RETEST_008 =
ATTACHMENT_WIRING_READY_FOR_PROMOTION =
SPRINT_SOURCE_CONTRACT = GREEN/YELLOW/RED
GATE_A = GREEN/YELLOW/RED
READY_FOR_CORE8_REAL_E2E = YES/NO
READY_FOR_LEARNING_LOOP = NO
```

Do not modify production code. Commit/push only this QA report.