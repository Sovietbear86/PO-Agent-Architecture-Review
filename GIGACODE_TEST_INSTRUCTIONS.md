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

`ASSIGNMENT_ID = GATE_D_48_SKILL_RECOVERY_AUDIT_015`

`TARGET_BRANCH = feat/gate-d-48-skill-recovery-v1`

`ASSIGNMENT_PATH = qa_assignments/GATE_D_48_SKILL_RECOVERY_AUDIT_015.md`

`REPORT_PATH = qa_reports/GATE_D_48_SKILL_RECOVERY_AUDIT_015.md`

Read first:
- `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`
- `PO_AGENT_48_SKILL_MATRIX.md`
- `po-agent-platform-v2/docs/recovery/CANONICAL_SKILL_CATALOG.md`
- `PO_AGENT_PLATFORM_V2_ADDENDUM_SKILLS_CLARIFICATION.md`
- `qa_reports/LEARNING_LOOP_014_SPRINT_HEALTH_ROLLBACK.md`
- `qa_assignments/GATE_D_48_SKILL_RECOVERY_AUDIT_015.md`

Execute the assignment exactly. Audit repository history/specifications where required. Do not start Gate E and do not modify the matrix. After publishing the report, stop and tell the user only that the report has been published.