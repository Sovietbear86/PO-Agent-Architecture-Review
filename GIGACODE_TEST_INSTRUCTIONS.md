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
`ASSIGNMENT_ID = CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2`
`TARGET_BRANCH = feat/core8-real-query-hardening-v2`
`ASSIGNMENT_PATH = qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
`REPORT_PATH = qa_reports/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`

Read first:
- `CORE8_HARDENING_FREEZE.md`
- `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`
- `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017.md`
- `qa_assignments/CORE8_CORRECTION_LOOP_ADDENDUM_017A.md`

Important: the V2 file is the single canonical entry point and consolidates the functional matrix plus correction/recheck-loop acceptance. Before declaring PASS, independently prove the oracle/source contract. Known positive anchors: Garanin has task(s) in DMS-SPRNT-1 and DMS-SPRNT-2; verify them directly from AS21/SWTR. If your oracle says zero for both, classify ORACLE_SOURCE_CONTRACT_BROKEN and do not mark dependent tests PASS.

Do not repair code. Do not resume Gate E. After publishing the V2 report, stop.