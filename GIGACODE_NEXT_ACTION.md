# GigaCode — Current Action

## A229R2UR2 — regex hotfix safety re-gate (QA only)

Previous RED: A229R2UR, P0. Root cause was double-escaped whitespace in a raw regex in `v4_synthesis_elision.py`, making `и` / `and` coordination checks unreachable; punctuation still matched. Owner corrected ONLY the regex escaping. Agent Core and planner are frozen. Feature flag `PO_AGENT_V4_SYNTHESIS_ELISION` remains OFF by default.

**STOP RULE:** No production/test/config modifications by GigaCode. Do not update Core, planner, skills, API, or factory. If any QA check fails, report exact first boundary and STOP.

### P0 — strict boundary and focused test
- Pull HEAD, record TESTED_HEAD and verify clean worktree.
- Verify 6/6 Agent Core files byte-identical to checkpoint `checkpoint/v4-complex-task-clarification-green-a229f3r`.
- Verify owner hotfix changed only raw regex escaping in the synthesis module versus previous RED state.
- Run `tests/test_v4_synthesis_elision.py`: **all tests must pass**, including previously failing coordinated-query cases.
- Confirm regex detects Russian `и`, English `and`, comma/semicolon and does not treat plain single-intent query as compound.
- Run full V4 suite, relevant Task API suites and frontend build, require zero failures.

### P1 — reproduce precise previous live failure
Use REAL AS21 and fresh sessions; test flag ON and OFF.

Run each >=3 valid times:
1. `Покажи задачи Калачанова в WMB и задачи Семавина в DMS`
2. `Покажи задачи Калачанова в WMB и иерархию DMS-267`
3. `Покажи задачу DMS-267, её иерархию и задачи Калачанова в WMB`

For any run with just one executed terminal, flag ON must delegate final synthesis to the original LLM, not silently publish the single terminal's answer as full coverage. The original synthesizer may acknowledge missing goals; **this is not proof that all goals executed**. Validate against independent source oracle for each requested goal.

### P2 — feature ON retains optimization safely
- Compare flag OFF/ON for at least 3 simple single-intent exact searches, a lookup, and hierarchy.
- Prove -1 synthesis LLM call only on eligible simple one-terminal trajectories.
- Check correct task key lists, UI cards, zero-results, clarification continuation, provider errors, no mutations/local fallback/unscoped source scans.
- Report elision hit rate and false positives caused by conservative coordination detection. Default stays OFF.

### P3 — report
Verdict:
- `AGENT_CORE_V4_SYNTHESIS_MULTI_INTENT_SAFETY_GREEN_A229R2UR2` only when P0-P2 all green;
- otherwise `AGENT_CORE_V4_SYNTHESIS_MULTI_INTENT_SAFETY_RED_A229R2UR2` with first failing boundary and STOP.

Keep the separate multi-intent *execution* gap OPEN until all independently requested goals can be completed or explicitly clarified.

Commit QA report:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_SYNTHESIS_MULTI_INTENT_SAFETY_A229R2UR2.md`

No checkpoint and no default flag flip before GREEN.
