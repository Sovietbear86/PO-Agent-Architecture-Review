# QA Assignment: AS21-A3-ATTACHMENT-WIRING-RETEST-007

## Context
Read `qa_reports/AS21_A3_ATTACHMENT_WIRING_RETEST_006.md` first.

The previous report correctly identified that the attachment facade and Task API route are implemented, but real verification was blocked because MCP-SWTR was not running on port 8000.

Do NOT ask the user to manually invent or guess commands. Determine the actual MCP-SWTR entrypoint from the repository and execute the correct startup/retest sequence yourself where tool permissions allow it.

## Goal
Bring the real AS21 attachment path to a definitive GREEN/RED result:

`Harness -> TaskApiAS21Adapter -> task-api :8003 -> swtr-read facade -> MCP-SWTR :8000 -> real AS21`

Use real task `WMB-30000` as the primary positive fixture because it is known to have attachments.

## Step 1 — locate the real MCP-SWTR entrypoint
From repository root run:

```bash
pwd
find . -maxdepth 4 -type f \( -name '*mcp*.py' -o -name '*swtr*.py' -o -name 'main.py' \) | sort
find . -maxdepth 4 -type f \( -name 'pyproject.toml' -o -name 'requirements*.txt' -o -name 'README*.md' \) | sort
```

Inspect the candidate MCP server file before starting it. In particular, do NOT assume `task-api/s21_agent_mcp_server.py` exists merely because the previous report suggested it.

Search for the port and server startup definitions:

```bash
grep -R "8000\|uvicorn\|FastAPI\|MCP\|mcp" -n task-api . --include='*.py' --include='*.md' --include='*.toml' 2>/dev/null | head -200
```

Record the exact discovered entrypoint and startup command in the report.

## Step 2 — start MCP-SWTR with the discovered command
Use the repository's actual entrypoint. If it is a Python module, prefer module execution from the directory expected by its imports, e.g.:

```bash
python3 -m <actual.module>
```

If the code exposes a FastAPI `app` rather than starting itself, use:

```bash
python3 -m uvicorn <actual.module>:app --host 127.0.0.1 --port 8000
```

Do not hard-code either example until inspection proves which one is correct.

If process enumeration is blocked, that is NOT sufficient evidence that the service is down. Verify by HTTP instead.

## Step 3 — prove port 8000 is serving the expected service
Try the service's documented health endpoint first. If none exists, inspect OpenAPI/root endpoints:

```bash
python3 - <<'PY'
import httpx
for path in ('/health', '/openapi.json', '/'):
    url = 'http://127.0.0.1:8000' + path
    try:
        r = httpx.get(url, timeout=5)
        print(path, r.status_code, r.text[:500])
    except Exception as e:
        print(path, 'ERROR', repr(e))
PY
```

Do not require `/health == 200` if this MCP implementation has no `/health`; prove readiness using an endpoint that actually exists in its contract.

## Step 4 — ensure Task API :8003 is running current HEAD
From `task-api` use the actual application entrypoint already proven by RETEST-006. If `main:app` is still correct:

```bash
python3 -m uvicorn main:app --host 127.0.0.1 --port 8003
```

Verify:

```bash
python3 - <<'PY'
import httpx
for path in ('/health', '/openapi.json'):
    r = httpx.get('http://127.0.0.1:8003' + path, timeout=5)
    print(path, r.status_code)
PY
```

## Step 5 — real WMB-30000 attachment test
With BOTH services alive:

```bash
python3 - <<'PY'
import json, httpx
url='http://127.0.0.1:8003/api/v1/swtr-read/tasks/WMB-30000/files'
r=httpx.get(url, timeout=30)
print('HTTP', r.status_code)
try:
    print(json.dumps(r.json(), ensure_ascii=False, indent=2))
except Exception:
    print(r.text)
PY
```

Required proof:
- HTTP success for a real existing task with attachments;
- at least one real attachment metadata item if WMB-30000 still contains attachments;
- task/file identity is preserved;
- no file content is downloaded;
- no credentials/tokens are printed.

If WMB-30000 unexpectedly has zero attachments, prove the task response and source contract first, then find another real WMB task belonging to Kalachanov with attachment metadata. Do not manufacture fixtures.

## Step 6 — canonical adapter verification
Run the real `TaskApiAS21Adapter.get_attachment_metadata('WMB-30000')` path against :8003 and record the canonical fields for each returned Attachment. Verify optional `attachment_id` filtering returns exactly the requested item and never another task's file.

## Step 7 — negative tests
Verify at minimum:
- nonexistent syntactically valid WMB task -> empty/not-found semantics according to contract;
- invalid task key -> fail closed;
- nonexistent attachment_id -> empty result;
- MCP unavailable -> `AS21SourceUnavailable`, not fake empty success;
- malformed payload -> `AS21SourceError`;
- no cross-task leakage.

## Step 8 — regression
Run targeted adapter/attachment tests and full regression. Compare to RETEST-006 baseline:

`1166 passed, 5 failed, 11 errors, 12 skipped`

No new failures/errors caused by this assignment are allowed.

## Promotion rule
Only set:

```text
ATTACHMENT_WIRING_READY_FOR_PROMOTION = YES
ATTACHMENTS_SOURCE_FACT_PROVEN = YES
```

when real AS21 attachment metadata has traversed the complete live chain successfully.

After that, update `source_facts` to advertise `attachments` only if this assignment explicitly includes the promotion change and all relevant readiness tests remain GREEN. Otherwise report that promotion is now safe but do not silently change capability advertisement.

Do not proceed to learning loop yet.

## Output
Publish the result as:

`qa_reports/AS21_A3_ATTACHMENT_WIRING_RETEST_007.md`

Include machine-readable summary:

```text
ASSIGNMENT_ID = AS21-A3-ATTACHMENT-WIRING-RETEST-007
MCP_ENTRYPOINT_DISCOVERED = YES/NO
MCP_SWTR_CONNECTED = YES/NO
TASK_API_CONNECTED = YES/NO
REAL_WMB_30000_READ = YES/NO
REAL_ATTACHMENT_FACADE = YES/NO
REAL_ATTACHMENT_COUNT = <n>
CANONICAL_ATTACHMENT_MAPPING = YES/NO
ATTACHMENT_ID_FILTER = YES/NO
ATTACHMENT_FALSE_POSITIVE = YES/NO
ATTACHMENT_CONTENT_DOWNLOADED = NO/YES
READ_ONLY_ATTACHMENT_BOUNDARY = PASS/FAIL
NEW_CODE_REGRESSIONS_VS_RETEST_006 = <n>
BLOCKER_COUNT = <n>
HIGH_COUNT = <n>
ATTACHMENT_WIRING_READY_FOR_PROMOTION = YES/NO
GATE_A = GREEN/YELLOW/RED
READY_FOR_LEARNING_LOOP = NO
```
