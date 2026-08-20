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
`ASSIGNMENT_ID = GATE_E_WAVE1_TASK_INTELLIGENCE_016`
`TARGET_BRANCH = feat/gate-e-wave1-task-intelligence-v1`
`ASSIGNMENT_PATH = qa_assignments/GATE_E_WAVE1_TASK_INTELLIGENCE_016.md`
`REPORT_PATH = qa_reports/GATE_E_WAVE1_TASK_INTELLIGENCE_016.md`

Read first:
- `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`
- `PO_AGENT_48_SKILL_MATRIX.md`
- `qa_reports/GATE_D_48_SKILL_RECOVERY_AUDIT_015.md`
- `po-agent-platform-v2/src/po_agent/analysis/task_intelligence.py`
- `po-agent-platform-v2/tests/test_task_intelligence.py`
- `qa_assignments/GATE_E_WAVE1_TASK_INTELLIGENCE_016.md`

Execute the assignment exactly. Be strict about the distinction between an analyzer existing and a user query being production-E2E reachable. Do not repair code. After publishing the report, stop.