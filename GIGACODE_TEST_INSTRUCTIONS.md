# GigaCode Test Instructions

> Canonical QA handoff from ChatGPT/developer to GigaCode. GigaCode is tester/adversarial reviewer only.

## Handoff protocol
1. Pull the target branch and read this file before every run.
2. Do not modify production code, existing tests, fixtures, roadmap docs, skill definitions, configuration, AS21 data, or `PO_AGENT_48_SKILL_MATRIX.md`.
3. The only repository file you may create/update for this run is the assigned QA report.
4. Commit and push the report to the same target branch.
5. Never commit credentials, cookies, Authorization headers, tokens, attachment contents, or secrets.
6. Prefer truthful RED/YELLOW/BLOCKED over false GREEN.

## Current assignment
`ASSIGNMENT_ID = CORE8_SOURCE_GROUNDING_CORRECTION_RETEST_018`
`TARGET_BRANCH = feat/core8-real-query-hardening-v2`
`ASSIGNMENT_PATH = qa_assignments/CORE8_SOURCE_GROUNDING_CORRECTION_RETEST_018.md`
`REPORT_PATH = qa_reports/CORE8_SOURCE_GROUNDING_CORRECTION_RETEST_018.md`

Read first:
- `CORE8_HARDENING_FREEZE.md`
- `qa_reports/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
- `po-agent-platform-v2/src/po_agent/adapters/hardened_production_task_api.py`
- `po-agent-platform-v2/src/po_agent/harness/core8_hardening.py`
- `po-agent-platform-v2/src/po_agent/harness/correction_runtime.py`
- `po-agent-platform-v2/tests/test_core8_real_query_hardening.py`
- `qa_assignments/CORE8_SOURCE_GROUNDING_CORRECTION_RETEST_018.md`

Critical rules:
- For DMS-SPRNT-1/2 use the COMPLETE sprint corpus (`complete=true`), never page 1 as ground truth.
- Resolve Garanin by canonical externalId/login/display evidence and report the exact aliases used.
- Missing cached project/sprint relation means UNKNOWN until raw/live SWTR is checked; it never means NO.
- Negative feedback must cause a fresh source read and correction trace; do not accept cached repetition.
- Do not repair code. Do not resume Gate E.

If and only if 018 is green, stop and report `READY_TO_RERUN_017_V2 = YES`; the full 017_V2 rerun will be the next assignment.