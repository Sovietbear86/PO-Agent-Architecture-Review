# GigaCode — Current Action

## ACTIVE: A229M2.1 — typed goal detection + postcondition guard (OFF-by-default gate)

Role: independent QA / architecture forensics only. **Do not modify production, test, settings, Core, or UI code.**
This is the *first bounded implementation gate*, NOT multi-intent functional certification.

### Baseline & owner change
- A229M1 design GREEN; report: `qa_reports/AGENT_CORE_V4_MULTI_INTENT_GOAL_COVERAGE_DESIGN_A229M1.md`.
- Core frozen against `checkpoint/v4-complex-task-clarification-green-a229f3r` (six files byte-identical).
- Owner added `api/v1/goal_coverage.py`: immutable RequestGoal + GoalCoverage; conservative independently anchored goal detection; per-goal terminal argument/evidence match; incomplete result becomes NEEDS_CLARIFICATION with unverified prose/data/evidence stripped.
- API postcondition integration after existing period guard, **only** if `PO_AGENT_V4_GOAL_COVERAGE_GUARD=true`.
- Settings default `false`; synthesis-elision flag default also unchanged (OFF).
- New offline matrix tests in `test_v4_goal_coverage.py`.
- This implementation intentionally DOES NOT execute missing goals, does not use Core, and does NOT certify all free-text multi-intent patterns. A229M2.2 will own continuation.

### P0 — safety / invariant / static tests FIRST
1. Pull branch, record START_HEAD, verify clean tracked worktree.
2. Compare Core 6/6 byte-for-byte to frozen checkpoint. Confirm no changes to Core/planner/registry/source/task API.
3. Run `tests/test_v4_goal_coverage.py` and `tests/test_v4_browser_api_contract.py`, `tests/test_agent_core_v4_task_created_period.py`, `tests/test_v4_synthesis_elision.py`, configuration tests.
4. Run full `test_agent_core_v4*.py` + `test_v4*.py`, relevant Task API SWTR suites and frontend build.
5. 0 failures required. If RED, record first failing boundary and STOP. **Do not fix code.**

### P1 — offline replay: requested vs executed goal matrix
Build fixtures from A229M1 REAL AS21 traces; use *exact* terminal capability ids and real argument shapes (do NOT adjust oracle to fit parser).

Test:
- M1 Kalachanov WMB + Semavin DMS (2 person collections, one terminal);
- M2 DMS-267 lookup + hierarchy (one lookup terminal);
- M3 Kalachanov WMB + DMS-267 hierarchy;
- M4 DMS-267 lookup + hierarchy + Kalachanov WMB;
- C5 DMS-267 lookup + related tasks.
For each: required goals count, proven/unproven exact, insufficient evidence must NOT be marked proven, no unsupported negative claims leak. DMS-267 parent source oracle = DMS-253, so absence cannot be claimed without hierarchy evidence.
Then full two-terminal replay for M2 / both person collections for M1: should remain COMPLETED if evidence and arguments truly cover all goals.

### P2 — false-positive and scope safety
Ensure composed-filter ONE-goal cases do NOT trigger:
- C1 Semavin+DMS+open+defect+period;
- C2 Kalachanov+WMB+attachments;
- C3 latest OLP sprint+Semavin+open+defect;
- C4 in-progress+attachments one intersected collection;
- `Сравни DMS и OLP` (one comparison goal; unimplemented comparison extractor must not fabricate coverage).

Add tricky alternative syntaxes and identify **false negatives** (valid multiple goals not recognized) separately.
Do not claim comprehensive natural-language goal extraction from this conservative first-stage module.

### P3 — feature flag integration
- With flag default OFF, prove API path byte-equivalent to pre-owner behavior for COMPLETED / NEEDS_CLARIFICATION / FAILED / PARTIAL.
- With flag explicitly ON in a controlled test harness, replay M1/M2/M3/M4/C5. Verify guard runs AFTER existing period guard and BEFORE `_remember_clarification`, sets typed NEEDS_CLARIFICATION, produces clarification_id, and strips unsupported factual answer/evidence/results.
- Existing clarification flow and provider/source error taxonomy must remain unchanged; no loss of original user request.
- **Do not flip flag default or enable flag on real stack** until P0–P3 GREEN.

### P4 — architecture gap audit
- Detector is a bounded conservative pilot, not universal goal parsing.
- No use of conjunction alone as a splitter or phrase-specific result routing.
- Check correct case handling of Russian inflection, pronouns, mixed entities, same-person two spaces, AND/intersections, comparison queries.
- Check evidence freshness/completeness and negative lookup/hierarchy inference.
- Report missing kinds (comparisons, nested multi-goal structures, unknown languages) as OPEN; do not reinterpret unrecognized multi-goal as certified success.
- The verified guard can block unsafe success; **it cannot perform unexecuted goals**.
- Explain risks of deterministic lexical goal extraction and propose typed LLM-free/skill-native or source-governed extractor before enabling broadly.

### P5 — verdict
Only:
- `AGENT_CORE_V4_GOAL_COVERAGE_STAGE1_GREEN_A229M21` if OFF safety, focused and full tests, matrix replay and ON injected guard semantics all correct (with unimplemented intents explicitly OPEN);
- otherwise `AGENT_CORE_V4_GOAL_COVERAGE_STAGE1_RED_A229M21`, exact first failing boundary and STOP.

Commit ONLY a QA report:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_GOAL_COVERAGE_STAGE1_A229M21.md`.
Return TESTED_HEAD, REPORT_COMMIT, exact suite counts, coverage/false-positive/false-negative table, Core hashes, residual OPEN gaps. **No checkpoint yet** and no next code task before reviewing gate.

GigaCode = QA only. Do not change production code.
