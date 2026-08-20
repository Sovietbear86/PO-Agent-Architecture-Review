# GigaCode Test Instructions

> Canonical QA handoff from ChatGPT/developer to GigaCode. GigaCode is tester/adversarial reviewer only.

## Handoff protocol
1. Pull the target branch and read this file before every run.
2. Do not modify production code, prompts, existing tests, fixtures, roadmap docs, skill definitions, AS21 data, learning state, or `PO_AGENT_48_SKILL_MATRIX.md`.
3. Keep the restored local LLM transport configuration from 027/028, but never commit `.env`, API keys, tokens or secrets.
4. Only QA report/result files permitted by the assignment may be created/updated.
5. Commit and push the report to the same target branch.
6. Prefer truthful RED/YELLOW/BLOCKED over false GREEN.

## Current assignment
`ASSIGNMENT_ID = CORE8_SEMANTIC_FRAME_BOUNDARY_RETEST_029`
`TARGET_BRANCH = feat/core8-real-query-hardening-v2`
`ASSIGNMENT_PATH = qa_assignments/CORE8_SEMANTIC_FRAME_BOUNDARY_RETEST_029.md`
`REPORT_PATH = qa_reports/CORE8_SEMANTIC_FRAME_BOUNDARY_RETEST_029.md`

Read first:
- `CORE8_HARDENING_FREEZE.md`
- `architecture_reviews/SEMANTIC_ROBUSTNESS_ARCH_REVIEW_025.md`
- `qa_reports/CORE8_REAL_DATA_SEMANTIC_ARCHITECTURE_ACCEPTANCE_026_RERUN.md`
- `qa_assignments/CORE8_SEMANTIC_FRAME_BOUNDARY_RETEST_029.md`
- `po-agent-platform-v2/src/po_agent/harness/semantic_core_v2.py`
- `po-agent-platform-v2/src/po_agent/harness/production_entity_grounding_v2.py`
- `po-agent-platform-v2/src/po_agent/harness/semantic_correction_runtime_v2.py`
- `po-agent-platform-v2/src/po_agent/adapters/evidence_validated_task_api.py`
- `po-agent-platform-v2/tests/test_semantic_frame_boundary_v3.py`

Critical rules:
- Restart Task API and PO Agent from CURRENT HEAD before testing.
- Use real `PO_AGENT_AS21_MODE=task-api` and the restored semantic LLM endpoint.
- Production NLU must remain LLM-first. Do not credit legacy phrase routers.
- Do not repair anything during the run.
- Reuse the unchanged 026 V2 benchmark/oracle methodology; do not tune tests to the new implementation.
- For assignee/status truth, hydrate sprint task keys through individual task reads.
- Compare exact task-key sets, not answer text and not count-only equality.
- A requested filter that disappears and broadens execution is a production failure.
- Capture pre-ground semantic frame, grounded frame and capability args for focused failures.
- Do not start 017_V2. Only report `READY_TO_RERUN_017_V2`.

Execute Assignment 029 completely, publish the report, push it, and STOP.
