# GigaCode — Current Action

## ACTIVE: Assignment A229R2I — synthesis-turn elision implementation re-gate

Role: QA/performance/source-forensics/browser tester only. **Do not modify production code.**

Previous design verdict:
`AGENT_CORE_V4_PLANNER_TURN_DESIGN_GREEN_A229R2`

Selected target:
`SYNTHESIS_TURN_ELISION`

Owner implementation is now on current branch.

### Owner delta to verify

1. New `harness/v4_synthesis_elision.py`
   - `TerminalSynthesisElider` wraps the existing LLM synthesizer.
   - It elides the final model synthesis only when there is exactly one proven eligible task terminal observation and every other observation is resolver/intermediate-only.
   - It uses only validated terminal observation data/answer.
   - It delegates to the original LLM synthesizer for multi-terminal, unknown/non-resolver, or empty-answer trajectories.

2. Runtime factory seam only
   - no Agent Core/planner/runtime-loop code changed;
   - factory wraps `v4_runtime.synthesizer` when feature flag is enabled.

3. Feature flag
   - `PO_AGENT_V4_SYNTHESIS_ELISION`
   - default = false.
   - false must preserve previous behavior exactly.
   - true enables elision for eligible simple task trajectories.

4. Current deliberately narrow eligible terminal set:
   - task.search
   - task.search_assignee
   - task.search_created
   - task.search_created_in_progress
   - task.search_status
   - task.search_sprint
   - task.search_text
   - task.search_attachments
   - task.search_excel
   - task.search_pdf
   - task.search_msg
   - task.type_analysis
   - task.lookup
   - task.hierarchy

5. Initial deterministic rendering policy
   - task-search answers may append exact task keys when <=20;
   - lookup/type/hierarchy preserve the validated terminal capability answer;
   - structured response data/evidence remain unchanged.

Functional baseline:
`checkpoint/v4-complex-task-clarification-green-a229f3r@6fb335d6f67344245a5c65e5c1b5b145759e96da`

---

## P0 — integrity / static regression

1. Pull current branch, record START_HEAD, require clean tracked worktree.
2. Prove Core 6/6 byte-identical to checkpoint 6fb335d:
   - agent_core_v4.py
   - agent_core_v4_robust.py
   - agent_core_v4_reliable.py
   - agent_core_v4_completion.py
   - v4_plugin_registry.py
   - llm/real.py
3. Run focused:
   - tests/test_v4_synthesis_elision.py
   - tests/test_runtime_env_aliases.py
   - tests/test_harness_runtime_factory.py
   - tests/test_v4_browser_api_contract.py
   - tests/test_agent_core_v4_task_created_period.py
   - tests/test_agent_core_v4_task_semantics_hierarchy.py
4. Run full V4 blast + relevant Task API SWTR suites + frontend build.
5. Require 0 failed.

Any Core diff or test failure => RED STOP.

---

## P1 — flag OFF baseline control

Start full stack with:
`PO_AGENT_V4_SYNTHESIS_ELISION=false`

Use fresh sessions.

Run at least 3 valid samples each:

A. `Задачи Калачанова в WMB`
C. `Покажи задачу DMS-267`
F. `Покажи иерархию DMS-267`

Require:
- current factual results exact vs fresh REAL AS21 oracle;
- current final LLM synthesis still occurs;
- model-call count remains baseline class:
  - A ~3
  - C ~3
  - F ~3
  unless bounded-repair/provider artifacts are explicitly shown.

This proves rollback behavior.

---

## P2 — flag ON exact call-elision proof

Restart agent with:
`PO_AGENT_V4_SYNTHESIS_ELISION=true`

Repeat A/C/F at least 5 valid samples each.

Require on every clean no-repair run:
- A: 3 -> **2** model calls;
- C: 3 -> **2**;
- F: 3 -> **2**;
- the missing call is exactly final synthesis;
- planner decisions, capability ids, capability arguments, source calls, completion mode, structured data and evidence are identical to flag-OFF control;
- final user-visible answer remains correct and grounded.

Measure:
- p50/p90 wall flag OFF vs ON;
- exact LLM calls saved;
- source calls unchanged.

---

## P3 — full A229R2 eligible matrix

With flag ON run at least 5 valid samples each:

A. person+space task collection
B. sprint+status
C. exact lookup
D. open+created-period
E. type+person+space+status+created-period
F. hierarchy
H. clarification continuation from an incomplete-period request

For every COMPLETED eligible run require:
- exactly one synthesis round-trip absent compared with equivalent baseline trajectory;
- factual structured result exact vs independent REAL AS21 oracle;
- no changed capability arguments;
- no changed source reads;
- no changed completion contract;
- no silent constraint drop.

For H specifically:
- first turn still NEEDS_CLARIFICATION;
- continuation still resumes original goal;
- only the COMPLETED continuation may elide synthesis.

---

## P4 — non-eligible delegation safety

Prove `TerminalSynthesisElider` delegates to the wrapped LLM synthesizer for:

1. two terminal task observations in one trajectory;
2. one task terminal plus another analytical/non-resolver observation;
3. unknown terminal capability;
4. eligible terminal with empty answer;
5. any multi-part query that requires cross-observation synthesis.

Use unit/integration harness evidence. At least one live multi-part query is preferred if a stable source-backed example is available; do not invent a brittle phrase-router-style test just to force it.

Require:
- wrapped synthesizer called;
- answer behavior unchanged from flag OFF;
- no deterministic flattening of multi-part reasoning.

---

## P5 — clarification / error taxonomy retained

With flag ON prove:

- incomplete period -> typed NEEDS_CLARIFICATION;
- silent-period-drop backstop still blocks unsafe result;
- option-button clarification retained;
- provider 429/timeout remains provider failure;
- REAL AS21 unavailable remains source failure;
- internal error remains FAILED;
- no synthesis elision code runs for non-COMPLETED responses.

No infrastructure/code defect may be rendered as successful deterministic prose.

---

## P6 — browser/UI acceptance

With flag ON verify in the real Web UI:

1. A task collection shows correct concise answer + cards/table.
2. Exact lookup drawer opens normally.
3. Hierarchy result remains readable.
4. Type-analysis complex query remains readable and exact.
5. Overview / task drawer / retained widgets unchanged.

Audit:
- no unexpected 4xx/5xx;
- no console errors;
- no direct frontend source calls;
- no mutations.

Check that deterministic answer text is not misleading or materially worse than current UX. Cosmetic terseness is acceptable; missing required factual content is not.

---

## P7 — performance decision

Report per scenario:
- OFF p50/p90;
- ON p50/p90;
- model calls OFF -> ON;
- wall saved;
- source calls;
- exact parity.

Expected:
- exactly -1 LLM call on eligible COMPLETED requests;
- normal-provider wall saving roughly one model call (~7.5s from A229R1), possibly less/more depending on session;
- no factual/source regression.

Also report whether the previously observed redundant second LOAD in B/D is still present. Do **not** fix it in this assignment.

---

## Verdict

Return exactly one:

- `AGENT_CORE_V4_SYNTHESIS_ELISION_GREEN_A229R2I`
- `AGENT_CORE_V4_SYNTHESIS_ELISION_RED_A229R2I`

GREEN requires:
- Core unchanged;
- all tests green;
- flag OFF rollback proven;
- flag ON removes exactly one final model call on eligible trajectories;
- factual/source parity exact;
- non-eligible delegation safe;
- clarification/error taxonomy retained;
- browser/UI accepted.

Commit report:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_SYNTHESIS_ELISION_A229R2I.md`

If RED:
- preserve first failing boundary and STOP;
- do not modify production code.

If GREEN:
- owner may flip the feature default only after reviewing measured UX/performance;
- then proceed to A230/A231 or separately scope redundant-second-LOAD optimization.

**GigaCode is QA only. Do not modify production code.**
