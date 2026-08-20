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
`ASSIGNMENT_ID = CORE8_AS21_CONTRACT_SEMANTIC_RETEST_019`
`TARGET_BRANCH = feat/core8-real-query-hardening-v2`
`ASSIGNMENT_PATH = qa_assignments/CORE8_AS21_CONTRACT_SEMANTIC_RETEST_019.md`
`REPORT_PATH = qa_reports/CORE8_AS21_CONTRACT_SEMANTIC_RETEST_019.md`

Read first:
- `CORE8_HARDENING_FREEZE.md`
- `qa_reports/CORE8_SOURCE_GROUNDING_CORRECTION_RETEST_018.md`
- `task-api/app/schemas/task.py`
- `task-api/app/routers/tasks.py`
- `po-agent-platform-v2/src/po_agent/config/settings.py`
- `po-agent-platform-v2/src/po_agent/adapters/hardened_production_task_api.py`
- `po-agent-platform-v2/src/po_agent/harness/core8_hardening.py`
- `po-agent-platform-v2/src/po_agent/harness/correction_runtime.py`
- `po-agent-platform-v2/src/po_agent/harness/runtime_factory.py`
- `qa_assignments/CORE8_AS21_CONTRACT_SEMANTIC_RETEST_019.md`

Critical rules:
- Restart both services from CURRENT HEAD before testing.
- Do not manually inject a secret merely to force GREEN; verify whether the project `.env` is loaded by Settings. Report only boolean key presence.
- Missing cached project/sprint relation means UNKNOWN until source_data/raw/live SWTR is checked; it never means NO.
- Explicit `DMS-SPRNT-1/2` must remain exact identifiers end to end.
- `Ты не прав, проверь ещё раз` is a correction to the prior turn, not a fresh query.
- Do not repair code. Do not resume Gate E.

If and only if 019 is green, stop and report `READY_TO_RERUN_017_V2 = YES`.