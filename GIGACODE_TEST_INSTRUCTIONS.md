# GigaCode Test Instructions

> Canonical QA handoff from ChatGPT/developer to GigaCode. GigaCode is tester/adversarial reviewer only.

## Handoff protocol
1. Pull the target branch and read this file before every run.
2. Do not modify production code, existing tests, fixtures, roadmap docs, skill definitions, configuration, or AS21 data.
3. The only repository file you may create/update for this run is the assigned QA report.
4. Temporary `/tmp` scripts are allowed only for isolated in-memory candidate evaluation and must not be committed.
5. Commit and push the report to the same target branch.
6. Never commit credentials, cookies, Authorization headers, tokens, attachment contents, or secrets.
7. Prefer truthful RED/YELLOW/BLOCKED over false GREEN.

## Current assignment

`ASSIGNMENT_ID = LEARNING_LOOP_013_TASK_SEARCH_SELF_IMPROVEMENT`

`TARGET_BRANCH = feat/learning-loop-013-v1`

`ASSIGNMENT_PATH = qa_assignments/LEARNING_LOOP_013_TASK_SEARCH_SELF_IMPROVEMENT.md`

`REPORT_PATH = qa_reports/LEARNING_LOOP_013_TASK_SEARCH_SELF_IMPROVEMENT.md`

Read first:
- `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`
- `PO_AGENT_HARNESS_EVOLUTION_PLAN_STATUS_013.md`
- `qa_reports/LEARNING_LOOP_012_QA.md`
- `qa_assignments/LEARNING_LOOP_013_TASK_SEARCH_SELF_IMPROVEMENT.md`

Then execute the assignment exactly. Do not start Learning Loop 014. After publishing the report, stop and tell the user only that the report has been published.
