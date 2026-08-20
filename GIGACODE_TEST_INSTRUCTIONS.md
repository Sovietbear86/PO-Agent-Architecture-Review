# GigaCode Test Instructions

> Canonical QA handoff from ChatGPT/developer to GigaCode. GigaCode is tester/adversarial reviewer only.

## Handoff protocol
1. Pull the target branch and read this file before every run.
2. Do not modify production code, existing tests, fixtures, roadmap docs, skill definitions, configuration values, AS21 data, or `PO_AGENT_48_SKILL_MATRIX.md`.
3. The only repository file you may create/update for this run is the assigned QA report.
4. Commit and push the report to the same target branch.
5. Never commit credentials, cookies, Authorization headers, tokens, attachment contents, or secrets.
6. Prefer truthful RED/YELLOW/BLOCKED over false GREEN.

## Current assignment
`ASSIGNMENT_ID = CORE8_SOURCEFACT_SPACES_FIX_RETEST_021`
`TARGET_BRANCH = feat/core8-real-query-hardening-v2`
`ASSIGNMENT_PATH = qa_assignments/CORE8_SOURCEFACT_SPACES_FIX_RETEST_021.md`
`REPORT_PATH = qa_reports/CORE8_SOURCEFACT_SPACES_FIX_RETEST_021.md`

Read first:
- `CORE8_HARDENING_FREEZE.md`
- Assignment 020 report;
- `po-agent-platform-v2/src/po_agent/harness/source_readiness.py`;
- `po-agent-platform-v2/src/po_agent/adapters/hardened_production_task_api.py`;
- `po-agent-platform-v2/tests/test_source_readiness_spaces.py`;
- `qa_assignments/CORE8_SOURCEFACT_SPACES_FIX_RETEST_021.md`.

Critical rules:
- Restart both services from CURRENT HEAD.
- Verify the exact 020 root cause is gone before any semantic conclusions.
- HTTP 500 from `/api/v1/query` is never acceptable Harness behavior.
- A non-500 response is not automatically semantically correct.
- Do not expose secrets.
- Do not repair code. Do not resume Gate E or the full 017_V2 yet.

If and only if 021 is GREEN, stop and report `READY_TO_RERUN_019 = YES`.