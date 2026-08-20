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
`ASSIGNMENT_ID = CORE8_EXPLICIT_SPRINT_ENTITY_FIX_RETEST_022`
`TARGET_BRANCH = feat/core8-real-query-hardening-v2`
`ASSIGNMENT_PATH = qa_assignments/CORE8_EXPLICIT_SPRINT_ENTITY_FIX_RETEST_022.md`
`REPORT_PATH = qa_reports/CORE8_EXPLICIT_SPRINT_ENTITY_FIX_RETEST_022.md`

Read first:
- `CORE8_HARDENING_FREEZE.md`
- `qa_reports/CORE8_AS21_CONTRACT_SEMANTIC_RETEST_019_RERUN.md`
- `po-agent-platform-v2/src/po_agent/harness/core8_semantic_precision.py`
- `po-agent-platform-v2/src/po_agent/harness/fail_closed_dialogue_runtime.py`
- `po-agent-platform-v2/tests/test_explicit_sprint_id_precision.py`
- `qa_assignments/CORE8_EXPLICIT_SPRINT_ENTITY_FIX_RETEST_022.md`

Critical rules:
- Restart both services from CURRENT HEAD before testing.
- Explicit source IDs such as `DMS-SPRNT-1` are atomic and must remain exact end to end.
- A sprint-id suffix such as `SPRNT-1` must never become a `task_key` when the user supplied `DMS-SPRNT-1`.
- Compare task results with independent live SWTR evidence; the agent may not be its own oracle.
- `Ты не прав, проверь ещё раз` must reopen the prior evidence chain and preserve session context.
- Classify the unknown-status test unambiguously as either stale expectation or production regression; do not count it both ways.
- HTTP 500 is never acceptable.
- Do not repair code. Do not resume Gate E or full 017_V2 in this assignment.

Execute Assignment 022 completely. Only if every required gate is green may you set `READY_TO_RERUN_017_V2 = YES`. After publishing the report, STOP.