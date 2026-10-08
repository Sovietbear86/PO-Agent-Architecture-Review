# GigaCode — Current Action

## ACTIVE: A229S1R4R — clean freeze re-gate

QA only. Do not modify production code.

Previous RED was a test-only bug: the catalog test selected capabilities[0] after resolver capabilities were added. Owner fixed the test to select id == task.type_analysis.

Run the exact previous P1 suites first:
- test_agent_core_v4_task_catalog.py
- test_agent_core_v4_task_semantics_hierarchy.py
- test_swtr_read_sprint_collection.py
- test_swtr_task_relations.py
- test_swtr_assignee_canonical.py

Require 0 failed. If RED, STOP.

Then run:
- full test_agent_core_v4*.py
- full test_v4*.py
- relevant Task API SWTR read/query/assignee suites
- frontend npm run build

Require 0 failed.

Prove Core 6/6 byte-identical vs A229S1R3 production head 161f2a0123767eafb84e9c49040b167466da8b81, canonical 54 unchanged, skill inventory unchanged, and no production-code change in this cleanup.

Run minimal REAL AS21/UI smoke:
1. open tasks of Semavin in latest OLP sprint with type defect
2. Overview KPIs exact vs po.status_report
3. hierarchy DMS-267
4. one task drawer

Require exact source-backed results, no false source_unavailable, no unexpected HTTP errors, no console errors, no mutations.

GREEN verdict:
AGENT_CORE_V4_CLEAN_FREEZE_GREEN_A229S1R4R

Report:
po-agent-platform-v2/qa_reports/AGENT_CORE_V4_CLEAN_FREEZE_REGATE_A229S1R4R.md

Return TESTED_HEAD, REPORT_COMMIT, exact passed counts, and recommend:
checkpoint/v4-task-semantics-hierarchy-green-a229s1r4

If RED, return AGENT_CORE_V4_CLEAN_FREEZE_RED_A229S1R4R with first failing boundary and STOP.
