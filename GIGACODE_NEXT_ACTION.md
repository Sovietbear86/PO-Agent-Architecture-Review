# GigaCode — Current Action

## ACTIVE: Assignment A229S1R4 — cleanup + all-green freeze gate

Role: QA/source-forensics/browser tester only. Do not modify production code.

A229S1R3 is functionally GREEN. Owner has now cleaned the stale red tests and aligned the local Task API example with the certified 8241 port.

Owner cleanup after A229S1R3:
- refreshed the stale task.type_analysis capability-tuple assertion;
- updated sprint pagination fixtures so they do not accidentally trigger unrelated timestamp enrichment;
- changed .env.example from stale Task API :8003 to http://127.0.0.1:8241;
- no Agent Core or production-logic changes.

### P0 — setup
1. Pull current feat/core8-real-query-hardening-v2 and record START_HEAD.
2. Require clean tracked worktree.
3. Inspect local po-agent-platform-v2/.env if present. For this REAL AS21 gate ensure:
   - AS21_MODE=task-api
   - TASK_API_BASE_URL=http://127.0.0.1:8241
   If it still uses localhost:8003, correct that local value only.
4. Restart the real processes holding 8004/8241/3000/5175 so the tested stack is on START_HEAD.

### P1 — focused stale-test cleanup
Run:
- po-agent-platform-v2/tests/test_agent_core_v4_task_catalog.py
- po-agent-platform-v2/tests/test_agent_core_v4_task_semantics_hierarchy.py
- task-api/tests/test_swtr_read_sprint_collection.py
- task-api/tests/test_swtr_task_relations.py
- task-api/tests/test_swtr_read_canonical.py

Require 0 failed.

Verify:
- task.type_analysis remains an extra plugin skill outside canonical 54;
- its capabilities now include space/sprint resolvers plus terminal task.type_analysis;
- the three formerly stale A185 tql_calls expectations pass;
- new task-type enrichment tests remain green.

Any failure => RED STOP.

### P2 — full all-green gate
Run:
- all test_agent_core_v4*.py
- all test_v4*.py
- relevant full Task API SWTR read/query/assignee suites
- frontend npm run build

Requirement: all executed tests GREEN, 0 failed. Do not waive current failures as non-blocking in this assignment.

### P3 — architecture integrity
Prove byte identity vs A229S1R3 START_HEAD 161f2a0123767eafb84e9c49040b167466da8b81 for:
- agent_core_v4.py
- agent_core_v4_robust.py
- agent_core_v4_reliable.py
- agent_core_v4_completion.py
- v4_plugin_registry.py
- llm/real.py

Require:
- Core 6/6 byte-identical;
- canonical 54 unchanged;
- skill inventory unchanged from A229S1R3;
- no phrase router or hardcoded person/space/sprint result;
- no local task-store fallback;
- cleanup delta contains no production-code changes.

### P4 — minimal REAL AS21 + Web UI retained smoke
On current START_HEAD run fresh conversations:

1. Покажи открытые задачи Семавина в последнем спринте по OLP с типом дефект
   - terminal task.type_analysis;
   - exact vs fresh source oracle;
   - no source_unavailable.
2. Overview
   - top KPI cards populated;
   - exact vs po.status_report;
   - no Дай обзор и риски POST.
3. Покажи иерархию DMS-267
   - exact retained hierarchy.
4. Open one task drawer
   - normal description/intelligence rendering.

Audit:
- no unexpected 4xx/5xx;
- no console errors;
- frontend uses the proxy path;
- no mutations.

### P5 — verdict
GREEN only if P0-P4 are all GREEN:

AGENT_CORE_V4_CLEAN_FREEZE_GREEN_A229S1R4

Commit a short report:
po-agent-platform-v2/qa_reports/AGENT_CORE_V4_CLEAN_FREEZE_A229S1R4.md

Return:
- TESTED_HEAD
- REPORT_COMMIT
- exact passed counts
- effective AS21_MODE and TASK_API_BASE_URL
- whether local 8003 -> 8241 correction was needed

Recommend checkpoint on TESTED_HEAD:
checkpoint/v4-task-semantics-hierarchy-green-a229s1r4

If any gate fails:
AGENT_CORE_V4_CLEAN_FREEZE_RED_A229S1R4
Record first failing boundary and STOP.

After GREEN:
1. freeze checkpoint;
2. sync certified delta to public/community;
3. return to A229R1 latency verification.
