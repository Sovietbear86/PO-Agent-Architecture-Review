# PO Agent Platform — Canonical Skill Catalog v1

This document is the functional source of truth for the recovery branch.

A Skill is counted as **implemented** only when it has:

1. a versioned Skill definition;
2. an allow-listed capability handler;
3. source-grounded evidence;
4. a typed response contract;
5. acceptance/regression coverage;
6. no direct business execution branch inside the orchestrator.

Merely creating a YAML/JSON/MD file does **not** count as implementation.

## Target

**52 Skills** in six domains. Current executable recovery baseline: **9 implemented / 43 planned**.

## Tasks — discovery & retrieval (10)

1. `task-lookup` — exact key lookup — **IMPLEMENTED**
2. `task-search` — phrase/text search — **IMPLEMENTED**
3. `task-search-attachments` — tasks with any attachments — **IMPLEMENTED**
4. `task-search-excel` — XLS/XLSX attachments — **IMPLEMENTED**
5. `task-search-pdf` — PDF attachments — **IMPLEMENTED**
6. `task-search-msg` — MSG attachments — **IMPLEMENTED**
7. `task-search-assignee` — filter by assignee
8. `task-search-status` — filter by normalized status
9. `task-search-sprint` — tasks in sprint
10. `task-search-release` — tasks in release

## Tasks — intelligence (10)

11. `task-summary` — grounded summary of what must be done
12. `task-quality` — deterministic task-definition quality
13. `task-missing-requirements` — missing task-definition elements
14. `task-acceptance-analysis` — acceptance criteria/testability
15. `task-dependency-analysis` — links/dependencies
16. `task-history` — lifecycle/status history
17. `task-time-in-status` — time in states
18. `task-aging` — aging active tasks
19. `task-blocker-analysis` — blocker explanation
20. `task-similar` — similar/duplicate task discovery

## Sprint intelligence & flow metrics (12)

21. `sprint-health` — deterministic health — **IMPLEMENTED**
22. `sprint-current` — current sprint resolution
23. `sprint-scope` — current sprint scope
24. `sprint-velocity` — velocity with explicit effort unit
25. `sprint-throughput` — completed-task throughput
26. `sprint-wip` — work in progress
27. `sprint-cycle-time` — cycle time
28. `sprint-lead-time` — lead time
29. `sprint-carryover` — carryover
30. `sprint-scope-change` — scope change after sprint start
31. `sprint-predictability` — predictability
32. `sprint-risk-queue` — items requiring PO attention

## Team intelligence (8)

33. `team-workload` — workload distribution
34. `team-wip` — WIP by member
35. `team-blocked` — blocked work by member
36. `team-capacity` — load vs configured capacity
37. `team-competency-match` — task vs declared competencies
38. `team-assignee-recommendation` — assignee recommendation using competencies + load
39. `team-bottlenecks` — concentration/bottleneck detection
40. `team-distribution` — work distribution by competence

## Release & portfolio intelligence (7)

41. `release-health` — readiness/risk summary — **IMPLEMENTED**
42. `release-scope` — release scope
43. `release-progress` — completion
44. `release-blockers` — blockers
45. `release-dependencies` — dependencies
46. `release-risk-queue` — prioritized release risks
47. `portfolio-overview` — portfolio overview + attention queue — **IMPLEMENTED**

## Product-owner assistance & controlled actions (5)

48. `po-attention-queue` — ranked PO attention list
49. `po-daily-brief` — grounded daily brief
50. `po-status-report` — product/sprint/release status report
51. `po-reminder-draft` — contextual reminder/message draft
52. `po-local-task-draft` — prepare local task draft; any write requires explicit approval

---

# Implementation waves

## Wave A — Task Agent parity

Implement 7–20 next. This recovers all capabilities that originally made S21 Task Agent useful: filtered/file search, task reading, summarization, completeness/quality, history, dependencies and related-task discovery.

## Wave B — Sprint deterministic analytics

Implement 22–32. Every numeric metric must come from deterministic code. LLM may explain a result but cannot calculate or alter the metric.

## Wave C — Team intelligence

Implement 33–40 using team configuration and declared competencies. Do not infer employee quality from task counts.

## Wave D — Release / portfolio

Implement 42–46 and then enrich 47/48 using the same evidence model.

## Wave E — PO assistance

Implement 49–52 only after history/session/feedback are stable. Drafting may use LLM. Write actions remain behind explicit approval gates.

---

# Architectural invariant

No user-facing business function is allowed to bypass the Skill layer.

```text
Request
 -> Context Resolver
 -> Router
 -> Skill Resolver
 -> Versioned Skill
 -> Skill Executor
 -> Capability Registry
 -> Domain / Metrics
 -> AS21 Adapter
 -> Evidence
 -> optional LLM synthesis
 -> Trace / History / Feedback
```

The orchestrator coordinates this chain and contains no domain-specific `if/elif` business execution switch.

# Progress definition

The UI/dashboard may show catalog progress using the machine-readable `harness/skill_catalog.py` source, but **planned Skills must never be presented as available to users**.
