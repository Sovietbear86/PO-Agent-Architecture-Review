# QA Assignment 016 — Gate E Wave 1 Task Intelligence

GigaCode is TESTER ONLY. Do not modify production code, tests, fixtures, skill definitions, AS21, or roadmap files. Publish only the QA report.

## Scope
Gate-E Wave E1 expands task intelligence requirements #13–20 while preserving accepted #1–12 and Core-8.

New deterministic analyzer: `po_agent.analysis.task_intelligence.TaskIntelligenceAnalysis`.

## A. Developer regression
Run `tests/test_task_intelligence.py`, task-quality tests, Core-8 semantic/runtime tests and full pytest. New HIGH production regressions must be 0.

## B. Real AS21 task evidence
Using read-only real AS21 tasks, exercise all eight capabilities against at least two distinct tasks where the source facts exist:
1. missing requirements;
2. acceptance/testability analysis;
3. dependency analysis;
4. status history;
5. time in current status;
6. aging;
7. blocker analysis;
8. similar-task discovery over a bounded real task corpus.

For every result record task keys and which canonical fields supplied the evidence. Do not manufacture missing history/dependencies. If current Task API/adapter does not expose a required fact, mark that capability `SOURCE_CONTRACT_BLOCKED`, not PASS and not a learning failure.

## C. Fail-closed attacks
Prove:
- empty `depends_on` never invents a dependency;
- empty `status_transitions` never invents history or time-in-status;
- completed old task is not called active aging;
- similar-task result excludes the source task and respects threshold/limit;
- blocker result does not convert arbitrary labels/text into a blocker unless the canonical contract supports it.

## D. Production wiring audit
Critically verify whether each #13–20 capability is merely implemented as an analyzer or is actually reachable through the production Harness/API semantic path. Report separately:
- `ANALYZER_READY`
- `PRODUCTION_E2E_READY`

Do NOT give Gate-E Wave 1 green if analyzers exist but the Harness cannot invoke them from user queries. This audit is intentionally strict.

## E. Protected baseline
Re-run Core-8 real-AS21 smoke. Required 8/8. AS21 mutations = 0. Learning-loop safety boundary must remain unchanged.

## Report
Publish `qa_reports/GATE_E_WAVE1_TASK_INTELLIGENCE_016.md` with concrete evidence and footer:

```text
ASSIGNMENT_ID = GATE_E_WAVE1_TASK_INTELLIGENCE_016
CURRENT_HEAD = <sha>
TASK_INTELLIGENCE_UNIT_PASS = x/7
REAL_AS21_CAPABILITIES_PROVEN = x/8
SOURCE_CONTRACT_BLOCKED = N
ANALYZER_READY = x/8
PRODUCTION_E2E_READY = x/8
FAIL_CLOSED_ATTACKS_PASS = YES|NO
CORE8_AGENT_E2E_PASS = x/8
NEW_HIGH_PRODUCTION_REGRESSIONS = N
AS21_MUTATIONS_DURING_TEST = 0
GATE_E_WAVE1_GREEN = YES|NO
READY_FOR_GATE_E_WAVE2 = YES|NO
```

Wave 1 GREEN requires all eight capabilities to be production-E2E reachable, source-grounded or explicitly supported by a proven canonical source contract, fail-closed, and Core-8 8/8. If production wiring is missing, return RED/YELLOW and identify exact missing integration points. After publishing, STOP.