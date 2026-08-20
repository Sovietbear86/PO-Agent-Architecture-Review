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
`ASSIGNMENT_ID = CORE8_RUNTIME_500_DIAGNOSTIC_RETEST_020`
`TARGET_BRANCH = feat/core8-real-query-hardening-v2`
`ASSIGNMENT_PATH = qa_assignments/CORE8_RUNTIME_500_DIAGNOSTIC_RETEST_020.md`
`REPORT_PATH = qa_reports/CORE8_RUNTIME_500_DIAGNOSTIC_RETEST_020.md`

Read first:
- `CORE8_HARDENING_FREEZE.md`
- the two Assignment 019 reports if present locally;
- `po-agent-platform-v2/src/po_agent/api/v1/__init__.py`;
- `po-agent-platform-v2/src/po_agent/config/settings.py`;
- `po-agent-platform-v2/src/po_agent/harness/runtime_factory.py`;
- `po-agent-platform-v2/src/po_agent/harness/correction_runtime.py`;
- `task-api/app/schemas/task.py`;
- `qa_assignments/CORE8_RUNTIME_500_DIAGNOSTIC_RETEST_020.md`.

Critical rules:
- Restart both services from CURRENT HEAD.
- Run PO Agent in a visible terminal so the real traceback is captured.
- HTTP 500 from `/api/v1/query` is never acceptable Harness behavior.
- Do not expose the LLM key; report presence only.
- Compare LLM-enabled and process-only LLM-disabled paths to isolate provider/transport vs Harness/runtime faults.
- Do not repair code. Do not resume Gate E or 017_V2.

After publishing the 020 report, stop.