# GigaCode — Current Action

## ACTIVE: Assignment A229R2 — planner-turn reduction design gate

Role: QA/performance/source-forensics only. **Do not modify production code.**

Functional baseline is now frozen at:

`checkpoint/v4-complex-task-clarification-green-a229f3r@6fb335d6f67344245a5c65e5c1b5b145759e96da`

A229R1 proved:
- source/data plane is no longer the dominant bottleneck;
- assignee+space direct route improved from ~34.5s to ~1.0s;
- duplicate sprint read removed;
- UI snapshot fan-out capped at 2;
- LLM/planner accounts for ~96% of wall on representative runs;
- planner/model calls are typically 3–8, p50 ~5;
- removing one model round-trip is expected to save roughly one provider call (~7.5s in normal conditions, much more during slow sessions).

A229F3R additionally proved complex composition + typed clarification GREEN, so any latency change must preserve:
- immutable constraints;
- safe clarification;
- source truth;
- no silent period drop.

This assignment is **forensics/design only**. Do not implement a Core/planner change yet.

---

## P0 — integrity / baseline

1. Pull current branch and record START_HEAD.
2. Prove Core 6/6 byte-identical to checkpoint `6fb335d`.
3. Full focused sanity:
   - complex task + period/type/status;
   - latest sprint + type;
   - hierarchy;
   - Overview;
   - task drawer.
4. Do not benchmark during provider 429/outage windows.

---

## P1 — decompose every LLM/model call

For each scenario below run at least 5 valid warm samples and reconstruct **every** model call in order:

A. `Задачи Калачанова в WMB`
B. `Задачи в работе в сентябрьском спринте по DMS`
C. exact task lookup `DMS-267`
D. `Открытые задачи Калачанова в WMB за последние 2 дня`
E. `Открытые задачи Семавина с типом дефект в DMS с 30.09.2026`
F. `Покажи иерархию DMS-267`
G. incomplete complex request that produces typed clarification
H. clarification continuation from G

Classify each model call as exactly one:
1. skill selection / load_skill;
2. entity-resolution planning;
3. terminal capability planning;
4. bounded repair;
5. READY/completion planning;
6. final response synthesis;
7. other — explain.

For each call capture:
- call ordinal;
- input purpose;
- output decision;
- wall/duration;
- whether removing it could change factual execution;
- whether a deterministic existing contract already proves the same decision.

Produce a per-scenario call graph.

---

## P2 — identify the single safest removable turn

Evaluate these candidate classes independently. Do **not** implement them.

### Candidate S — final synthesis turn
Question:
Can a subset of task-collection / exact-lookup responses safely use the already validated terminal capability answer without an extra LLM synthesis call?

Prove:
- capability answer already contains the exact count/key/result needed;
- no multi-observation reasoning is required;
- no clarification/source/error semantics would be lost;
- current deterministic fallback output is acceptable and source-grounded.

Estimate:
- scenarios eligible;
- LLM calls saved/request;
- wall saved;
- UX/prose trade-off;
- blast radius.

### Candidate L — load_skill round-trip
Question:
Can skill discovery and first governed action be combined without phrase routing or preloading all detailed skills?

Analyze only:
- what additional planner schema/runtime change would be required;
- whether progressive disclosure remains intact;
- whether a model could request `load_skill + first call` safely in one decision;
- effect on anti-invention and allowed-capability checks.

No implementation.

### Candidate R — resolver-planning round-trip
Question:
Where a terminal skill procedure deterministically requires a resolver (person/space/sprint), can one planning turn be removed while keeping the resolver source-backed and generic?

Reject any design that:
- parses surnames/spaces with hardcoded heuristics;
- adds phrase routers;
- skips source validation;
- invents canonical ids.

### Candidate C — completion/READY turn
Verify whether runtime completion contracts already eliminate this turn for certified skills. If already eliminated, mark NON-CANDIDATE rather than optimizing it again.

---

## P3 — safety matrix for each candidate

For Candidate S/L/R/C score:

- expected LLM calls removed;
- median wall saving;
- Core files touched if implemented;
- plugin/API-only alternative available?;
- constraint-propagation risk;
- clarification risk;
- source-grounding risk;
- progressive-disclosure risk;
- regression blast radius;
- rollback simplicity.

Use:
LOW / MEDIUM / HIGH risk with evidence.

The preferred candidate must remove **exactly one model round-trip first**. Do not propose multiple simultaneous optimizations.

---

## P4 — counterfactual replay

For the preferred candidate, use recorded trajectories from P1 and perform a no-code counterfactual replay.

Show for each A-H:
- current model-call count;
- hypothetical count after one-turn reduction;
- which exact call disappears;
- why the resulting executed capabilities/arguments would remain identical;
- scenarios not eligible and therefore unchanged.

The preferred design must keep exact factual trajectory identical for all eligible factual runs.

If this cannot be proven, verdict RED and recommend no Core change.

---

## P5 — target selection / implementation boundary

Recommend exactly one implementation target:

- `SYNTHESIS_TURN_ELISION`
- `LOAD_AND_CALL_FUSION`
- `RESOLVER_PLANNING_ELISION`
- `NO_SAFE_ONE_TURN_REDUCTION`

For the selected target specify:
1. minimal files that would change;
2. whether Agent Core must change;
3. exact feature flag / rollback seam;
4. exact tests to add before implementation;
5. exact A/B/C re-gate set;
6. expected median call-count and wall improvement;
7. explicit non-goals.

Prefer an external/plugin/synthesizer seam over Core if equivalent safety can be achieved.

---

## P6 — GVS5H / multi-agent interaction note

Do not implement multi-agent behavior.

Provide one short architecture note:
- whether the selected latency optimization is compatible with the future V5 manager/worker/verifier sidecar;
- ensure A229R2 does not make V4 more monolithic or phrase-routed;
- preserve the governed capability/evidence plane so V5 can reuse it later.

---

## Verdict

Return exactly one:

- `AGENT_CORE_V4_PLANNER_TURN_DESIGN_GREEN_A229R2`
- `AGENT_CORE_V4_PLANNER_TURN_DESIGN_RED_A229R2`

GREEN means:
- model-call anatomy is measured;
- one preferred removable turn is proven by counterfactual replay;
- expected benefit and blast radius are quantified;
- no code changed.

RED means:
- no single model turn can be removed safely with current contracts.

Commit report:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_PLANNER_TURN_DESIGN_A229R2.md`

**GigaCode is QA only. Do not modify production code.**
