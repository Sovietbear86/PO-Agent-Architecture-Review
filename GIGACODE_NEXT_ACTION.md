# GigaCode — Current Action

## ACTIVE: A229M1 — Multi-Intent Goal Coverage architecture and feasibility gate

**Role: QA / architecture investigator only. NO production/test/config modifications.** 
Do not change Agent Core, planner, synthesizer, registry, Task API, UI, or prompt logic. No implementation in this assignment.

### Context and immutable baselines

- Most recent synthesis safety result: `AGENT_CORE_V4_SYNTHESIS_MULTI_INTENT_SAFETY_GREEN_A229R2UR2`.
- Previous certified functional checkpoint: `checkpoint/v4-complex-task-clarification-green-a229f3r`.
- V4 Core 6/6 must remain byte-identical to checkpoint.
- `PO_AGENT_V4_SYNTHESIS_ELISION=false` remains the default and MUST NOT be flipped.
- Baseline source: REAL AS21, governed skill/capability/evidence plane, read-only.
- A229R2UR2 verifies presentation safety ONLY. **Multi-intent execution remains OPEN.**
- Known source-truth contradiction: lookup-only observations for DMS-267 once led the LLM to assert no parent; authoritative task.hierarchy shows parent DMS-253. A synthesized inference is not an executed, verified hierarchy goal.

### Objective

Design a generic, typed **goal decomposition → goal coverage verification → safe continuation** approach *outside Agent Core* for multiple independent user goals. Distinguish:
- a single composed search with several filters (ONE goal),
- multiple independent deliverables (MULTIPLE goals),
- ambiguous wording requiring clarification,
- analytics needing cross-collection comparisons.

Completion means *all explicitly requested goals covered by independently sourced terminal observations*, or a typed partial/incomplete/clarification response. Never treat acknowledgment of missing information as completed.

### P0 — safety, evidence and regression baseline

1. Pull current branch; record START_HEAD and clean tracked worktree.
2. Compare Core 6/6 against frozen checkpoint (hashes), inspect all existing response/trajectory/completion schemas, `api/v1` clarification-session seam, catalog procedures and plugin registry.
3. Confirm latest synthesis elision tests, full V4 and relevant Task API suites and frontend build GREEN (or document any exact baseline failures; STOP on new regression).
4. Record the actual public status/output shapes currently supported by API and UI. Avoid inventing protocol enums.

### P1 — goal semantics and source-backed oracles

Use fresh sessions and independent REAL AS21 direct source-oracle for EACH separate goal. 3 clean runs/case where feasible, record actual trajectory and execution facts:

M1: `Покажи задачи Калачанова в WMB и задачи Семавина в DMS`
M2: `Покажи задачу DMS-267 и её иерархию`
M3: `Покажи задачи Калачанова в WMB и иерархию DMS-267`
M4: `Покажи задачу DMS-267, её иерархию и задачи Калачанова в WMB`
M5: `Сравни незавершённые задачи в DMS и OLP`

Controls — ONE goal with composed filters (must NOT split):
C1: `Открытые задачи Семавина типа дефект в DMS за последние 2 дня`
C2: `Задачи Калачанова в WMB с вложениями`
C3: `Покажи открытые дефекты Семавина в последнем спринте OLP`

Ambiguity/coordination controls:
C4: `Задачи в работе и с вложениями у Калачанова в WMB` (ONE intersected collection)
C5: `Покажи DMS-267 и связанные задачи` (may need clarification depending on capability semantics)
C6: `Сравни DMS и OLP` (underspecified comparison metric → clarification)

For every case produce an immutable goal set:
goal_id, goal_kind, source-backed entities, filter constraints, required capability/evidence, dependencies, expected source oracle keys/facts.
Mark `AND` / `и` as a coordination signal only, NEVER use conjunction detection alone as a goal splitter or router.

### P2 — first-failing-boundary analysis

For each goal map:
- loaded/discovered skills and governance checks,
- planner decision/arguments and executed terminal capabilities,
- completion contract satisfaction,
- source evidence lineage,
- whether final answer asserts facts unsupported by executed observations,
- where and why a goal was lost (discovery, planner, execution, completion, synthesis, API presentation).
Make a coverage matrix: requested goals vs proven observations; no invented facts or model-side fabricated oracles.

Explicitly reproduce the DMS-267 parent mismatch: `task.lookup` does NOT prove absent hierarchy; `task.hierarchy` / source oracle establishes DMS-253. Determine how the verifier prevents this false claim before user-visible response.

### P3 — design three solution options (NO implementation)

A. **Plugin/capability-side composition**: dedicated governed multi-goal procedural skill, bounded sequential orchestration or multiple source-backed terminal calls without changing Core. Prove what current Core completion policy can/cannot certify.

B. **Typed API/dialogue goal-coverage guard**: compare immutable goals to terminal observation coverage AFTER Core response, hide misleading overbroad/partial success, use existing clarification_id/session continuation where applicable. Specify how to reliably derive goals using a typed extractor and independent verification; no regex/phrase router by surname, space, or conjunction alone. Never infer unexecuted facts. A guard only detects incomplete coverage; it does not pretend to execute missing goals.

C. **V5 deep orchestration sidecar** (GVS5H-inspired) only for genuinely independent analytical work. Same governed skills, evidence, read-only source; not required to fix basic multi-intent queries.

For each: minimal files/interfaces, cost (additional LLM calls, latency/429), source/permissions safety, 54 canonical skills impact, Core touch? (must be NONE for preferred path), rollback flag, counterexamples, risk and test coverage.

### P4 — typed goal contract / proof-of-feasibility

Provide proposed schema and examples **in the QA report, not production code**:
`RequestGoals` (immutable goal ids, source text span, goal_kind, constraints, dependencies, required evidence);
`GoalEvidence` (goal_id, capability_id, source ids, source status, result reference);
`GoalCoverage` (proven/unproven/ambiguous; reason and evidence refs);
`ContinuationState` (unfinished goal ids, original request, prior proven evidence, bounded retry budget).

Specify how to bind terminal observations to goal ids deterministically, verify no unsupported claim, prevent evidence for one goal from satisfying another, and guard stale/partial source failures. Enumerate statuses: all proven, incomplete but safe to clarify, genuinely unsupported, source outage, provider outage. Match CURRENT API semantics wherever possible; introduce proposed new statuses only in design.

Use traces to test counterfactual verification without executing new production logic. Show what would be flagged for M1–M5 and what remains one goal for C1–C4.

### P5 — recommendation and follow-on assignment

Recommend **one** minimal owner implementation path outside Core, including stages:
1. typed goal extraction and evidence mapping;
2. postcondition coverage fail-closed;
3. resume missing goals safely via bounded plugin/API continuation, if possible;
4. non-regression/UI/REAL AS21 A/B oracle gate.

If completion of remaining goals is impossible without Core under existing interfaces, prove the precise boundary and propose a sidecar instead of modifying frozen Core in this task.

Specify explicit regression acceptance:
- 100% coverage or honest partial/clarification, NEVER silent goal drop;
- no false positive goal splits for composed-filter single-goal queries;
- DMS-267 cannot claim parent absent without hierarchy evidence;
- no local fallback, no scans, no unauthorized writes, no invented data;
- minimal additional calls; feature default OFF; easy rollback.

### Verdict

Return:
`AGENT_CORE_V4_MULTI_INTENT_DESIGN_GREEN_A229M1` if P0–P5 evidence is complete and a safe implementation boundary has been demonstrated;
otherwise `AGENT_CORE_V4_MULTI_INTENT_DESIGN_RED_A229M1` with exact first failing boundary and STOP.

**DESIGN GREEN is NOT multi-intent functionality GREEN.** Do not implement/fix code and do not create a new production checkpoint in A229M1.

Commit/push only report:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_MULTI_INTENT_GOAL_COVERAGE_DESIGN_A229M1.md`.

Return TESTED_HEAD, REPORT_COMMIT, traces, coverage matrix, selected option, minimal next owner task and Core invariant.
