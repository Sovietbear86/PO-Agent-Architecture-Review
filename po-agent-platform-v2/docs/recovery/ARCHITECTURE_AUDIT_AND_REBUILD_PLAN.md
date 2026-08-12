# PO Agent Platform v2 — Architecture Audit & Rebuild Plan

## Status

This document is the new recovery source of truth for `po-agent-platform-v2` in branch `chatgpt-harness-recovery`.

The current application contains many architectural building blocks, but the production runtime does not yet behave as a true harness agent. The recovery will therefore be **vertical-slice-first**, not folder-first.

## Core findings

### 1. Production orchestration is disconnected from the real data path

`POOrchestratorV1` accepts optional pre-fetched tasks and, when they are absent, falls back to an empty list instead of obtaining data through `AS21Adapter`. This means the normal `/api/v1/query` path can execute without ever touching the real adapter.

### 2. Several business capabilities are placeholders

The current orchestrator contains direct business dispatch and placeholder implementations. Task search can return an empty result set without calling the existing search service, while sprint/velocity/release behavior is reduced largely to task counts.

### 3. Skill architecture exists structurally but not operationally

There are currently **9 initial Skills**:

1. `task_search`
2. `task_summary`
3. `task_quality`
4. `sprint_health`
5. `velocity`
6. `team_workload`
7. `competency_match`
8. `release_health`
9. `help`

The long-term product needs a substantially richer skill catalog, but the immediate problem is more important: selecting a Skill still leads back into orchestrator-side `if/elif` dispatch. Skills therefore do not yet form the executable harness boundary.

### 4. Evidence is not sufficiently grounded

Current generic evidence can prove that an entity was extracted or a capability name ran, but does not necessarily prove the business statement. Business capabilities must produce source evidence such as task keys, statuses, sprint/release identifiers, metric inputs, calculated values, and freshness timestamps.

### 5. Runtime history is not durable by default

Normal API composition currently uses in-memory history/feedback stores. That prevents real long-lived execution history and weakens the intended AI-PDLC architecture.

### 6. Runtime configuration is environment-specific

The current API contains a local absolute-path fallback for an API key. This must be removed. Credentials/providers must come only from explicit environment/configuration.

### 7. UI breadth was built before backend depth

The frontend already contains Assistant, Tasks, Sprint, Releases, Team, Quality and AI-PDLC views, while several corresponding backend flows are not actually wired end-to-end. Recovery will initially reduce the product surface to one reliable PO Workspace conversation/evidence flow.

## Target architecture

```text
PO Workspace UI
      |
POST /api/v1/query
      |
PO Orchestrator              # coordination only
      |
+-----+-------------------------------+
| Context Resolver                   |
| Deterministic Router               |
| Skill Resolver                     |
+-----+-------------------------------+
      |
Skill Executor
      |
Capability Handler Registry
      |
Domain / Workflow / Metrics
      |
ONE AS21 Adapter interface
      |
FakeAS21Adapter (dev/tests) OR real SWTR bridge later
      |
Structured Result + Evidence
      |
Optional LLM synthesis
      |
Trace / History / Feedback
```

### Dependency rules

Allowed:

```text
API -> Orchestrator
Orchestrator -> Context/Router/Skills
SkillExecutor -> Capability handlers
Capabilities -> Domain/Workflow/Metrics/AS21Adapter
Capabilities -> optional LLM
Orchestrator -> optional response synthesis
```

Forbidden:

```text
AS21Adapter -> Agent/Orchestrator
Metrics -> LLM
Domain -> API
Skill -> raw HTTP
UI -> AS21
LLM -> arbitrary unregistered capability execution
```

## Harness rule

No user-facing business function may be implemented directly inside the orchestrator.

The orchestrator may:

- resolve/request context;
- classify intent;
- resolve a Skill;
- invoke SkillExecutor;
- aggregate the returned structured result;
- record trace/history;
- optionally synthesize presentation text.

The orchestrator must not calculate sprint metrics, search tasks, analyze releases, or contain a growing domain `if/elif` switch.

## Skill contract

A production Skill is a versioned executable contract, not just a prompt.

Each Skill must define at least:

- `skill_id`;
- version/status;
- supported intents;
- required/optional context;
- clarification policy;
- allowed capabilities;
- ordered workflow;
- output contract;
- evidence requirements;
- eval/golden-test identifiers.

SkillExecutor must invoke capabilities only through an allowlisted handler registry.

## Initial recovery strategy

We will not create 48+ Skills immediately. That would reproduce the existing problem at a larger scale.

First we prove the harness mechanism with a small set of fully working Skills, then expand the catalog.

### Phase A — Harness Core

1. `task_lookup/search`
2. `task_summary`
3. `task_quality`
4. `sprint_health`
5. `velocity`

Every one must work end-to-end through the same production API with a deterministic `FakeAS21Adapter` before SWTR is connected.

### Phase B — Product Intelligence

Add real executable Skills for:

- attachment search;
- sprint risk;
- aging/blocked tasks;
- throughput/WIP/cycle time/lead time/carryover/scope change/predictability;
- workload/capacity;
- competency matching;
- release readiness/risk/dependencies;
- cross-capability PO scenarios.

### Phase C — AI-PDLC

Only after core runtime is stable:

```text
execution -> trace -> feedback -> eval -> failure mining
-> improvement candidate -> shadow -> regression gate
-> human approval -> promotion/rollback
```

No automatic self-promotion.

## Rebuild phases

### R0 — Runtime inventory and test baseline

- inventory live/unused/placeholder modules;
- inventory backend/frontend tests;
- establish one canonical FastAPI entrypoint;
- establish one canonical frontend entrypoint;
- record baseline behavior.

### R1 — Application composition

- remove hard-coded local credential paths;
- create explicit dependency composition;
- persistent SQLite paths in normal runtime;
- UUID trace IDs and real timing;
- typed API error envelope.

### R2 — Adapter boundary with deterministic fake

Until SWTR is intentionally connected, implement a high-quality `FakeAS21Adapter` using realistic deterministic fixtures.

The application must be able to switch adapters through configuration/dependency injection without business-code changes.

### R3 — Executable Skill Harness

- capability handler protocol/registry;
- SkillRegistry validates Skills;
- SkillResolver maps intent to Skill;
- SkillExecutor enforces required context + allowed capabilities + workflow;
- remove domain dispatch from orchestrator.

### R4 — Task vertical slice

`/api/v1/query -> router -> Skill -> capability -> FakeAS21Adapter -> evidence -> response -> trace`

Implement lookup, phrase search and attachment search.

### R5 — Summary and task quality

- deterministic task facts;
- optional LLM summary;
- deterministic quality score;
- LLM explanation cannot alter score;
- graceful no-LLM fallback.

### R6 — Sprint/metrics vertical slice

- workflow normalization;
- deterministic metrics;
- sprint health/risk evidence;
- explicit metric units.

### R7 — Team and release intelligence

- workload/capacity/competency evidence;
- release scope/readiness/risk;
- no unsupported employee judgments;
- no fabricated delivery dates.

### R8 — Context, clarification and session memory

Support `NEEDS_CLARIFICATION`, pending request resume and explicit-current-input precedence.

### R9 — UI rebuild

First deliver one coherent PO Workspace:

- conversation;
- clarification options;
- evidence drawer;
- warnings/errors;
- trace/freshness;
- session continuity;
- connection status.

Analytical pages return only after their backend capability is proven.

### R10 — Durable history and AI-PDLC observation

- persistent traces/history;
- feedback linked to trace + skill version;
- eval datasets;
- failure taxonomy/mining;
- improvement candidates only.

### R11 — Shadow / gate / approval / rollback

- candidate versions run in shadow;
- structured comparison;
- fail-closed regression gate;
- human approval required;
- rollback audited.

### R12 — Expand Skill catalog

After the harness mechanism is proven, create the full domain Skill catalog. The exact count is driven by distinct executable workflows, not a cosmetic target number. The expected catalog will likely exceed the original nine significantly and may reach the previously envisioned ~48+ skills/subskills once decomposed into stable business workflows.

## Testing policy

A functional phase is not PASS because a class or directory exists.

Until real SWTR is connected, each vertical slice must pass:

- unit tests;
- contract tests;
- golden tests;
- FastAPI integration tests;
- end-to-end query tests against deterministic FakeAS21Adapter;
- LLM-unavailable fallback tests where relevant;
- unknown/ambiguous context tests;
- skill allowlist enforcement tests;
- trace/evidence tests.

After SWTR connection, the same suite is repeated with read-only real-data acceptance scenarios.

## Stable query envelope

All user queries should converge on one typed response envelope.

```json
{
  "status": "COMPLETED",
  "answer": "...",
  "intent": "task_search",
  "skill": {"id": "task_search", "version": "1.0.0"},
  "data": {},
  "evidence": [],
  "warnings": [],
  "trace_id": "...",
  "session_id": "..."
}
```

Clarification uses the same API contract family:

```json
{
  "status": "NEEDS_CLARIFICATION",
  "question": "По какому продукту?",
  "options": [],
  "clarification_id": "...",
  "trace_id": "...",
  "session_id": "..."
}
```

## Definition of Done

The rebuild is successful when:

1. production API does not depend on manually pre-fetched task lists;
2. all data comes through one adapter interface;
3. fake and real adapters are swappable;
4. orchestrator contains no domain business dispatch;
5. Skills truly own executable workflows and capability allowlists;
6. core Skills pass full vertical tests;
7. deterministic metrics are reproducible;
8. evidence grounds business facts;
9. clarification/session continuity works;
10. history is durable;
11. UI consumes one typed API contract;
12. AI-PDLC observes real runtime and cannot self-promote;
13. shadow/regression/approval/rollback work;
14. a rich versioned Skill catalog replaces the current minimal nine-Skill set;
15. SWTR can be connected without redesigning the harness.

## Engineering principle

```text
working vertical slice > architectural vocabulary
executable Skill       > metadata Skill
real evidence           > generic "capability executed"
thin orchestrator       > domain switch statement
deterministic metric    > LLM calculation
stable contract         > many disconnected UI pages
controlled AI-PDLC      > simulated self-learning
```
