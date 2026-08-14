# PO Agent Platform — Canonical Skill Catalog v2

The product acceptance baseline for this recovery is the original repository file:

`PO_AGENT_PLATFORM_V2_GIGACODE_MASTER_SPEC_V2_1.md`

This catalog translates its user-facing capability requirements into explicit executable Skills. Infrastructure requirements from the Master Spec — memory, history, feedback, eval, failure mining, curated memory, prompt/version registries, shadow mode, regression gates, human approval, MCP, knowledge layer and UI — are tracked separately and are **not** inflated into fake Skill count.

A Skill is counted as **implemented** only when it has:

1. a versioned Skill definition;
2. an allow-listed capability handler;
3. source-grounded evidence;
4. a typed response contract;
5. acceptance/regression coverage;
6. no direct business execution branch inside the orchestrator.

Merely creating YAML/JSON/MD is not implementation.

## Target

**54 explicit user-facing Skills** in six domains. Current executable recovery baseline: **14 implemented / 40 planned**.

The target is above the original “48+” threshold because reconciliation with the Master Spec restored two requirements that the first recovery catalog had omitted: task search by product/space and release forecasting.

## Tasks — discovery & retrieval (11)

1. `task-lookup` — exact key lookup — **IMPLEMENTED**
2. `task-search` — phrase/text search — **IMPLEMENTED**
3. `task-search-attachments` — tasks with any attachments — **IMPLEMENTED**
4. `task-search-excel` — XLS/XLSX attachments — **IMPLEMENTED**
5. `task-search-pdf` — PDF attachments — **IMPLEMENTED**
6. `task-search-msg` — MSG attachments — **IMPLEMENTED**
7. `task-search-assignee` — filter by assignee — **IMPLEMENTED**
8. `task-search-status` — filter by normalized status — **IMPLEMENTED**
9. `task-search-sprint` — tasks in sprint — **IMPLEMENTED**
10. `task-search-release` — tasks in release — **IMPLEMENTED**
11. `task-search-product` — tasks in product/space — **IMPLEMENTED**

These directly cover Master Spec STEP 09: phrase, key, assignee, sprint, release, product and attachment type.

## Tasks — intelligence (10)

12. `task-summary` — grounded summary of what must be done
13. `task-quality` — deterministic task-definition quality
14. `task-missing-requirements` — missing task-definition elements
15. `task-acceptance-analysis` — acceptance criteria/testability
16. `task-dependency-analysis` — links/dependencies
17. `task-history` — lifecycle/status history
18. `task-time-in-status` — time in states
19. `task-aging` — aging active tasks
20. `task-blocker-analysis` — blocker explanation
21. `task-similar` — similar/duplicate task discovery

Master Spec STEPS 11–12 explicitly require structured summary and deterministic quality; the remaining Skills preserve the broader S21 Task Agent capability surface.

## Sprint intelligence & flow metrics (12)

22. `sprint-health` — deterministic health — **IMPLEMENTED**
23. `sprint-current` — current sprint resolution
24. `sprint-scope` — current sprint scope
25. `sprint-velocity` — velocity with explicit effort unit
26. `sprint-throughput` — completed-task throughput
27. `sprint-wip` — work in progress
28. `sprint-cycle-time` — cycle time
29. `sprint-lead-time` — lead time
30. `sprint-carryover` — carryover
31. `sprint-scope-change` — scope change after sprint start
32. `sprint-predictability` — predictability
33. `sprint-risk-queue` — items requiring PO attention

These correspond to Master Spec STEPS 08 and 13. Numeric values must be deterministic code, never LLM calculations.

## Team intelligence (8)

34. `team-workload` — workload distribution
35. `team-wip` — WIP by member
36. `team-blocked` — blocked work by member
37. `team-capacity` — load vs configured capacity
38. `team-competency-match` — task vs declared competencies
39. `team-assignee-recommendation` — assignee recommendation using competencies + load
40. `team-bottlenecks` — concentration/bottleneck detection
41. `team-distribution` — work distribution by competence

These cover Master Spec STEPS 14–15. The agent must not infer employee quality from raw task counts.

## Release & portfolio intelligence (8)

42. `release-health` — readiness/risk summary — **IMPLEMENTED**
43. `release-scope` — release scope
44. `release-progress` — completion
45. `release-blockers` — blockers
46. `release-dependencies` — dependencies
47. `release-risk-queue` — prioritized release risks
48. `release-forecast` — forecast inputs / bounded forecast
49. `portfolio-overview` — portfolio overview + attention queue — **IMPLEMENTED**

These cover Master Spec STEP 16, including the originally missed forecast requirement.

## Product-owner assistance & controlled actions (5)

50. `po-attention-queue` — ranked PO attention list
51. `po-daily-brief` — grounded daily brief
52. `po-status-report` — product/sprint/release status report
53. `po-reminder-draft` — contextual reminder/message draft
54. `po-local-task-draft` — prepare local task draft

Drafting is not external write permission. Master Spec STEP 43 requires explicit action contracts before any real write is enabled; later mutation must pass confirmation/audit gates.

---

# Master Spec infrastructure checklist

The following are mandatory architecture requirements but **not Skills**:

- deterministic workflow engine;
- Metrics Engine;
- provider-neutral LLM client + fake client + structured validation;
- deterministic intent router + bounded LLM fallback;
- thin PO Orchestrator;
- controlled multi-capability planner with hard call limit;
- evidence-based response synthesis + deterministic fallback;
- execution trace;
- Session Memory;
- persistent Operational History;
- feedback store;
- eval case model + eval runner;
- failure taxonomy + failure miner;
- Curated Memory;
- improvement candidates;
- Prompt Registry;
- Version Registry;
- Shadow Mode;
- comparison engine;
- regression gate;
- human approval;
- promotion + rollback;
- AI-PDLC metrics API;
- stable FastAPI API;
- small high-level MCP surface;
- Knowledge Layer;
- action contracts;
- WORKS/DB/AS21-inspired PO Workspace UI;
- AI-PDLC admin UI;
- full regression suite;
- legacy-vs-v2 comparison.

This prevents the Qwen-era failure mode where infrastructure names existed but the production vertical path did not.

# Implementation waves

## Wave A — Task Agent parity

The discovery/search portion is now executable. Next implement Skills 12–21: summary, deterministic quality, missing requirements, acceptance analysis, dependencies, history, time in status, aging, blocker analysis and similar-task discovery.

## Wave B — Sprint deterministic analytics

Implement 23–33. Every metric is calculated from canonical source data and documented formulas. LLM may explain, never calculate or alter.

## Wave C — Team intelligence

Implement 34–41 using private/external team configuration and declared competencies.

## Wave D — Release / portfolio

Implement 43–48 and enrich 49/50 using the same evidence model.

## Wave E — PO assistance

Implement 51–54 only after Session Memory, Operational History and feedback are stable.

---

# Architectural invariant

No user-facing business function bypasses the Skill layer.

```text
Request
 -> Context Resolver
 -> deterministic Router / bounded LLM fallback
 -> Skill Resolver
 -> Versioned Skill
 -> Skill Executor
 -> Capability Registry
 -> Domain / Workflow / Metrics
 -> AS21 Adapter
 -> Evidence
 -> optional LLM synthesis
 -> Trace / History / Feedback
```

The Orchestrator coordinates this chain and contains no domain-specific business `if/elif` executor.

# Progress definition

The UI may show catalog progress from `harness/skill_catalog.py`, but planned Skills must never be presented as available. A green unit test around a fake class is also insufficient: before SWTR connection, acceptance is through the real application API using `FakeAS21Adapter`; after SWTR connection, the same contract is retested against real data.
