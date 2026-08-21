# QA Report Review: CORE8_017V2_BATCH_TS01_TS12_STRICT_RERUN_040

## Executive verdict

**040_VERDICT = BLOCKED**

Assignment 040 is accepted only as evidence that GigaCode followed the Git allowlist and did not modify production or runner files. It is not accepted as 017 V2 TS-01..TS-12 acceptance evidence.

The report commit sequence added only the allowed report file, so branch hygiene is acceptable. However, the report itself does not satisfy Assignment 040 acceptance requirements because independent exact-set oracle evidence was not produced.

## Reviewed commits

| Item | Value |
|------|-------|
| Base correction commit | `ef60246860a42280ff8f4fed31f93f36f13119bb` |
| 040 report/fix-metrics HEAD | `a2705315e924cb58fb9ee8c2a15ba71562f97603` |
| Allowed report path | `qa_reports/CORE8_017V2_BATCH_TS01_TS12_STRICT_RERUN_040.md` |
| Production fix under test | `2c0e8aa7f105452e7d7e9efc53ce49344533acfa` |

## Git hygiene result

| Check | Result |
|-------|--------|
| Only allowed report file added after Assignment 040 | PASS |
| Production files modified | NO |
| Runner files modified | NO |
| Unauthorized JSON committed | NO |

## Acceptance blockers

| Requirement | Observed | Verdict |
|-------------|----------|---------|
| Independent source-backed oracle | Direct SWTR returned HTTP 403; oracle marked BLOCKED | BLOCKED |
| Exact key-set comparison | Report uses task counts/statuses, not exact oracle-vs-agent key sets | FAIL |
| Required per-ID table fields | Missing `oracle_keys`, `agent_keys`, `missing_keys`, `extra_keys`, `foreign_keys`, capability args and trace pointers for each row | FAIL |
| Internal metric consistency | Summary table still says `TS_PASS = 4/12` and `TS_CLARIFICATION_PASS = 8/12` while text/footer say 6/12 and 6/12 | FAIL |
| Production verdict | Report says agent works correctly, but oracle was blocked | UNSUPPORTED |

## Useful retained evidence

- Task API health check reportedly returned OK on port `8003`.
- PO Agent health check reportedly returned OK on port `8004`.
- Agent queries returned structured statuses for all TS-01..TS-12.
- Direct SWTR REST/Jira access from GigaCode environment returned HTTP 403.
- MCP-SWTR/Task API SWTR-read path was reportedly available, but was not used to build the required independent exact-set oracle.

## Required next action

Run a narrow oracle-recovery assignment before any Gate E work:

1. Prove a read-only source-backed oracle path that is independent of PO Agent responses.
2. Prefer MCP-SWTR or Task API `/api/v1/swtr-read/*` endpoints only if they hydrate authoritative SWTR units and are not derived from PO Agent output.
3. If no independent source-backed oracle path can be proven, report BLOCKED with exact commands and responses.
4. If oracle path is proven, rerun TS-01..TS-12 exact-set comparison with full per-ID evidence.

## Footer

```text
ASSIGNMENT_ID = CORE8_017V2_BATCH_TS01_TS12_STRICT_RERUN_040
REPORT_HEAD = a2705315e924cb58fb9ee8c2a15ba71562f97603
ACCEPTANCE_VALID = NO
GIT_ALLOWLIST_VALID = YES
RUNNER_MODIFIED = NO
PRODUCTION_MODIFIED = NO
UNAUTHORIZED_FILES_COMMITTED = NO
REQUIRED_PER_ID_TABLE_PRESENT = NO
ORACLE_PREFLIGHT_PASS = BLOCKED
ORACLE_INDEPENDENCE_PASS = BLOCKED
EXACT_SET_COMPARISON_PRESENT = NO
INTERNAL_METRICS_CONSISTENT = NO
FALSE_GREEN_COUNT = 0
040_VERDICT = BLOCKED
READY_TO_RESUME_GATE_E = NO
```
