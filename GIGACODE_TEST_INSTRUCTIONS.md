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
`ASSIGNMENT_ID = CORE8_ASSIGNEE_AND_SPRINT_FAILCLOSED_RETEST_024`
`TARGET_BRANCH = feat/core8-real-query-hardening-v2`
`ASSIGNMENT_PATH = qa_assignments/CORE8_ASSIGNEE_AND_SPRINT_FAILCLOSED_RETEST_024.md`
`REPORT_PATH = qa_reports/CORE8_ASSIGNEE_AND_SPRINT_FAILCLOSED_RETEST_024.md`

Read first:
- `CORE8_HARDENING_FREEZE.md`
- `qa_reports/CORE8_LIVE_SPRINT_GROUNDING_RETEST_023.md`
- `qa_assignments/CORE8_ASSIGNEE_AND_SPRINT_FAILCLOSED_RETEST_024.md`
- `po-agent-platform-v2/src/po_agent/harness/core8_semantic_precision.py`
- `po-agent-platform-v2/src/po_agent/harness/live_entity_grounding.py`
- `po-agent-platform-v2/src/po_agent/adapters/hardened_production_task_api.py`
- `po-agent-platform-v2/tests/test_explicit_sprint_id_precision.py`

Critical rules:
- Restart Task API and PO Agent from CURRENT HEAD before testing.
- GigaCode is QA only; do not repair code during the run.
- Prove the live SWTR oracle independently before judging agent output.
- `задачи Гаранина` must not silently lose the assignee filter.
- QA 023 proved 4 Garanin tasks in DMS-SPRNT-1 and 0 in DMS-SPRNT-2; re-prove current source truth and compare exact keys.
- `DMS-SPRNT-999999` must fail closed; `COMPLETED + 0` is explicitly a failure.
- Do not accept an echoed sprint_id as existence proof by itself.
- `Ты не прав, проверь ещё раз` is a correction to the prior turn, not a fresh query.
- Do not start 017_V2 yourself. Only report whether `READY_TO_RERUN_017_V2` is YES or NO.

Execute Assignment 024 completely, publish the report, push it, and STOP.
