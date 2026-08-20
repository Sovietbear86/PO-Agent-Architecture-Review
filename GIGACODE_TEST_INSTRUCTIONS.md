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
`ASSIGNMENT_ID = CORE8_AS21_CONTRACT_SEMANTIC_RETEST_019_RERUN`
`TARGET_BRANCH = feat/core8-real-query-hardening-v2`
`ASSIGNMENT_PATH = qa_assignments/CORE8_AS21_CONTRACT_SEMANTIC_RETEST_019.md`
`REPORT_PATH = qa_reports/CORE8_AS21_CONTRACT_SEMANTIC_RETEST_019_RERUN.md`

Read first:
- `CORE8_HARDENING_FREEZE.md`
- Assignment 020 report;
- Assignment 021 report;
- `qa_assignments/CORE8_AS21_CONTRACT_SEMANTIC_RETEST_019.md`;
- `task-api/app/schemas/task.py`;
- `task-api/app/routers/tasks.py`;
- `po-agent-platform-v2/src/po_agent/config/settings.py`;
- `po-agent-platform-v2/src/po_agent/adapters/hardened_production_task_api.py`;
- `po-agent-platform-v2/src/po_agent/harness/core8_hardening.py`;
- `po-agent-platform-v2/src/po_agent/harness/correction_runtime.py`;
- `po-agent-platform-v2/src/po_agent/harness/runtime_factory.py`.

Critical rules:
- Restart both services from CURRENT HEAD before testing.
- 021 proved the SourceFact.SPACES/runtime-500 defect is fixed; do not reclassify non-500 as semantic PASS automatically.
- Do not manually inject secrets merely to force GREEN; verify project `.env` loading and report only boolean key presence.
- Missing cached project/sprint relation means UNKNOWN until source_data/raw/live SWTR is checked; it never means NO.
- Explicit `DMS-SPRNT-1` and `DMS-SPRNT-2` must remain exact identifiers end to end.
- `Ты не прав, проверь ещё раз` is a correction to the prior turn, not a fresh query.
- Golden query must be compared with independent real-AS21/SWTR evidence, not with the same adapter interpretation.
- Do not repair code. Do not resume Gate E or full 017_V2 in this assignment.

Execute all sections A-G from Assignment 019 exactly and publish the rerun report. Only if all A-G pass may you set `READY_TO_RERUN_017_V2 = YES`. After publishing, STOP.