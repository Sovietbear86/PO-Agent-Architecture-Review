# QA Assignment 020 — Runtime 500 Diagnostic Retest

GigaCode is tester only. Do not modify production code, tests, configuration, AS21, or `.env`. Publish only the QA report.

## Goal
Identify and prove the exact cause of the PO Agent `/api/v1/query` crash seen in Assignment 019, and verify the Harness now fails closed as structured JSON instead of HTTP 500.

## Preconditions
- Branch: `feat/core8-real-query-hardening-v2`
- Update to current HEAD.
- Start Task API on 8003 and PO Agent on 8004 from a visible terminal (not nohup) so traceback/log output is captured.

## A. Runtime bootstrap
1. GET `/api/v1/health`.
2. Record HTTP status and full JSON fields: `status`, `adapter`, `semantic_mode`, `source_status`, `runtime_init_error`.
3. If `runtime_init_error` is non-null, copy the exact exception class/message and traceback from server logs into the report.

## B. Minimal query isolation
Run separately:
1. `Покажи WMB-30000`
2. `Покажи задачи Калачанова`
3. `Покажи задачи Гаранина по DMS`
4. `Покажи задачи Гаранина в DMS-SPRNT-1`
5. `Покажи открытые задачи Гаранина в последнем спринте по DMS`

For every query record HTTP status and Harness `status/warnings/exception_type`. An internal fault may return Harness `FAILED`, but MUST NOT return HTTP 500.

## C. Semantic-layer isolation
Report whether `.env` loads `LLM_API_KEY` as present WITHOUT printing its value. Verify configured base URL, model name and TLS verify flag. Make one direct semantic-client health/completion probe using a harmless supported prompt, without exposing credentials. If it fails, record exact exception type/status only.

Then repeat one query with semantic LLM deliberately disabled only via process environment for the test process (`SEMANTIC_LLM_ENABLED=false`; do not edit files). Compare behavior. This distinguishes runtime construction/adapter defects from LLM transport/provider defects.

## D. Source contract sanity
Verify Task API still returns 200 for `status=Open` and `status=Closed`. For at least one real DMS task record top-level `project_space`, `sprint_id`, and relevant `source_data` fields. Do not infer NO from missing sprint relation.

## E. Correction path
If normal queries no longer crash, use one `session_id`:
1. original golden query;
2. `Ты не прав, проверь ещё раз`.
Expected: second turn is either `NEEDS_CLARIFICATION` or a source-backed corrected result with correction metadata. It must not be HTTP 500 and must not be parsed as unrelated standalone intent.

## F. Gate
Do NOT rerun exhaustive 017_V2 yet unless all runtime bootstrap/query crashes are understood and HTTP_500_COUNT=0.

Publish `qa_reports/CORE8_RUNTIME_500_DIAGNOSTIC_RETEST_020.md` with footer:

```text
ASSIGNMENT_ID = CORE8_RUNTIME_500_DIAGNOSTIC_RETEST_020
CURRENT_HEAD = <sha>
HEALTH_HTTP_STATUS = N
RUNTIME_INIT_ERROR = <none|exact class>
QUERY_HTTP_500_COUNT = N
HARNESS_TYPED_FAILURE_COUNT = N
LLM_ENV_PRESENT = YES|NO
LLM_DIRECT_PROBE = PASS|FAIL|BLOCKED
LLM_DISABLED_QUERY_PATH = PASS|FAIL
TASK_API_STATUS_OPEN_200 = YES|NO
TASK_API_STATUS_CLOSED_200 = YES|NO
TOP_LEVEL_PROJECT_SPACE_PROVEN = YES|NO
TOP_LEVEL_SPRINT_ID_PROVEN = YES|NO
CORRECTION_RECHECK_PATH = PASS|FAIL|BLOCKED
ROOT_CAUSE_PROVEN = YES|NO
READY_FOR_019_RETEST = YES|NO
READY_TO_RERUN_017_V2 = NO
```

After publishing, stop. Do not repair code.