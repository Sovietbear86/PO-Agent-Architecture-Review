# GigaCode Test Instructions

> Canonical QA handoff from ChatGPT/developer to GigaCode. GigaCode is tester/adversarial reviewer only.

## Handoff protocol
1. Pull the target branch and read this file before every run.
2. Do not modify production code, existing tests, fixtures, roadmap docs, skill definitions, configuration values, AS21 data, learning state, or `PO_AGENT_48_SKILL_MATRIX.md`.
3. The only repository file you may create/update for this run is the assigned QA report.
4. Commit and push the report to the same target branch.
5. Never commit credentials, cookies, Authorization headers, tokens, attachment contents, or secrets.
6. Prefer truthful RED/YELLOW/BLOCKED over false GREEN.

## Current assignment
`ASSIGNMENT_ID = CORE8_REAL_DATA_SEMANTIC_ARCHITECTURE_ACCEPTANCE_026`
`TARGET_BRANCH = feat/core8-real-query-hardening-v2`
`ASSIGNMENT_PATH = qa_assignments/CORE8_REAL_DATA_SEMANTIC_ARCHITECTURE_ACCEPTANCE_026.md`
`REPORT_PATH = qa_reports/CORE8_REAL_DATA_SEMANTIC_ARCHITECTURE_ACCEPTANCE_026.md`

Read first:
- `CORE8_HARDENING_FREEZE.md`
- `architecture_reviews/SEMANTIC_ROBUSTNESS_ARCH_REVIEW_025.md`
- `qa_assignments/CORE8_REAL_DATA_SEMANTIC_ARCHITECTURE_ACCEPTANCE_026.md`
- `po-agent-platform-v2/src/po_agent/harness/semantic_core_v2.py`
- `po-agent-platform-v2/src/po_agent/harness/semantic_correction_runtime_v2.py`
- `po-agent-platform-v2/src/po_agent/harness/production_entity_grounding_v2.py`
- `po-agent-platform-v2/src/po_agent/adapters/evidence_validated_task_api.py`
- `po-agent-platform-v2/src/po_agent/harness/runtime_factory.py`
- `po-agent-platform-v2/tests/test_semantic_core_v2.py`

Critical rules:
- Restart Task API and PO Agent from CURRENT HEAD before testing.
- Use `PO_AGENT_AS21_MODE=task-api` with the real semantic LLM enabled.
- GigaCode is QA only; do not repair code during the run.
- Production natural-language understanding must be LLM-first. Legacy DeterministicRouter/Core8 phrase regexes must not be credited as production success.
- Prove live SWTR/task-api oracle independently before judging every factual task-set answer.
- Use complete corpus/pagination and compare exact task keys.
- Re-prove Garanin/DMS-SPRNT anchors from current source; old counts are hints, not authority.
- `DMS-SPRNT-999999` must fail closed; an echoed sprint id is not existence evidence.
- Test broad paraphrase/word-order/grammatical variation without adding code patterns.
- Test natural corrections including `Ты не прав`, `Опечатался`, `я имел в виду`, status/sprint/person corrections, but judge by semantic behavior rather than literal trigger matching.
- Disabling semantic LLM in task-api mode must fail closed instead of falling back to regex business routing.
- Do not start 017_V2 yourself. Only report whether `READY_TO_RERUN_017_V2` is YES or NO.

Execute Assignment 026 completely, publish the report, push it, and STOP.
