# GigaCode — Next Action

## A229R2UR — multi-intent synthesis safety re-gate

QA only. Do not change production code.

Previous verdict: AGENT_CORE_V4_SYNTHESIS_ELISION_UX_RED_A229R2U.
First boundary: one-terminal multi-intent queries were deterministically synthesized from one observation and silently omitted other requested goals.

Owner fix outside Core:
- v4_synthesis_elision.py delegates queries containing coordination/enumeration signals to the original query-aware LLM synthesizer.
- Single-intent queries still skip exactly one synthesis call when eligible.
- New focused regression tests cover M1/M3/M4 and ordinary single intent.
- Flag remains OFF by default.
- This guard is conservative presentation safety, not a router and NOT a multi-intent execution fix.

P0: pull HEAD, verify Core 6/6 unchanged, run test_v4_synthesis_elision.py, focused V4 tests, full V4 blast, Task API SWTR, frontend build. Require 0 new failures.

P1 FIRST: reproduce M1/M3/M4 on flag ON with at least 3 valid runs each. For one-terminal trajectories verify final synthesis is delegated to the underlying LLM and no longer emits an unqualified one-goal answer. Compare with flag OFF using the same source oracle. Do not count a prose acknowledgment as completion of unexecuted goals. If an intent is not executed, report it OPEN. If LLM still silently drops an unexecuted intent, RED with the exact boundary.

P2: ensure flag ON still removes exactly one LLM call in simple single-intent A/C/F examples, with exact REAL AS21 parity, cards/keys/drawer, no source-call changes. Test representative single intent with conjunctive filters: conservative delegation is acceptable but measure any elision hit-rate loss.

P3: prove true 2-terminal multi-intent still delegates; incomplete-period clarification and continuation, source/provider error taxonomy remain correct. Browser network/console clean, 0 local reads, mutations, tenant scans.

P4: create a separate multi-intent correctness gap report: where planner omitted a goal, document source oracle for each goal, exact first failing boundary, recommended plugin/completion/API goal-coverage design without Core changes, and whether it can safely clarify. Do not add new routing logic or implement multi-agent here.

P5: report A229R2UR GREEN only if presentation safeguard, normal elision, error taxonomy, and correctness tests pass. Mark multi-intent execution limitation OPEN until independently fixed. Otherwise RED, STOP.

Commit QA report at po-agent-platform-v2/qa_reports/AGENT_CORE_V4_SYNTHESIS_MULTI_INTENT_SAFETY_A229R2UR.md.
Return TESTED_HEAD, REPORT_COMMIT, pass counts and flag recommendation. Do not enable flag by default.
