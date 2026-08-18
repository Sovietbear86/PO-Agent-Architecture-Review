# PO Agent — Canonical Evolution Master Plan

> **Purpose:** this document is the single execution roadmap for evolving the original PO Agent application into the current Harness-based PO Agent with controlled self-learning, without losing proven behavior from the legacy application.
>
> **Rule:** if implementation, tests, prompts, or later discussions contradict this file, the contradiction must be resolved explicitly and this file must be updated in the same change. Do not rely on conversational memory as the source of truth.

---

## 1. Why this document exists

The project has already demonstrated a dangerous failure mode: architecture can improve globally while a small but critical legacy behavior silently regresses. The concrete example is AS21 filtering. The early PO Agent used explicit source filters such as `assignee`, while the later Harness adapter translated JQL-like text into a `q` parameter that the real `/api/v1/tasks` endpoint did not support. The result could look superficially correct while returning an overly broad corpus.

This roadmap therefore treats **behavioral continuity** as a first-class architectural requirement.

We are not merely building a more sophisticated agent. We are evolving a working product while preserving the source contracts, task semantics, UI behaviors, analytics formulas, and user workflows that were already proven.

---

## 2. Canonical reference points

The following artifacts are mandatory historical references during implementation and review.

### 2.1 Legacy working baseline

**Commit:**

`6b3bee08c920f5ea32083313481385eb06935b48`

**Meaning:** early integrated PO Agent application with:

- React frontend;
- FastAPI task API;
- SWTR/AS21 integration;
- S21 task agent;
- team-performance agent;
- natural-language task search;
- explicit assignee/source/status filters;
- task list/filter UI;
- task details drawer;
- local task creation drawer;
- agent UI;
- sprint/team analytics.

Important files from this baseline include:

- `ARCHITECTURE_ANALYSIS.md`
- `GIGACODE.md`
- `task-api/src/s21_agent/connectors/s21_swtr_adapter.py`
- `task-api/src/s21_team_performance/agent.py`
- `task-api/app/routers/tasks.py`
- `task-api/app/schemas/task.py`
- `task-api/src/components/App.tsx`
- `task-api/src/components/AgentButton.tsx`
- `task-api/src/components/AgentChat.tsx`
- `task-api/src/components/FilterBar.tsx`
- `task-api/src/components/TaskList.tsx`
- `task-api/src/components/TaskItem.tsx`
- `task-api/src/components/TaskDetailsDrawer.tsx`
- `task-api/src/components/CreateTaskDrawer.tsx`

The legacy application is not automatically architecturally correct, but it is the **behavioral reference** for capabilities that were known to work.

### 2.2 Target architecture specification

Primary target specification:

`PO_AGENT_PLATFORM_V2_GIGACODE_MASTER_SPEC_V2_1.md`

Core target:

**deterministic core + bounded LLM + observable Harness + controlled learning loop**

The migration model is **side-by-side / strangler**, not uncontrolled in-place replacement.

### 2.3 UI target

Primary UI specification:

`UI_REDESIGN_PO_WORKSPACE.md`

Target product identity:

- `PO Workspace`
- WORKS visual language
- DB Tribe identity
- AS21-like task interaction model

### 2.4 Current recovery branch

Current corrective development branch:

`feat/restore-as21-source-contract-v1`

Immediate goal: restore and prove AS21 source-contract correctness **before** returning to learning-loop work.

---

## 3. Product destination

The target product is a **Product Owner Workspace** with a Harness-based assistant that can safely combine deterministic execution and bounded LLM reasoning.

The finished system must support, at minimum:

- AS21/SWTR task retrieval;
- text search;
- filters by assignee, status, space/product, sprint, release and task key;
- task attribute extraction;
- attachment discovery and metadata;
- task summarization;
- task quality/completeness analysis;
- sprint health;
- velocity;
- throughput;
- WIP;
- cycle time;
- lead time;
- carryover;
- aging/blocked-task analysis;
- workload distribution;
- capacity and competency matching;
- release scope/risk/forecast;
- team/product/workflow knowledge;
- multi-turn dialogue and clarification;
- session memory;
- execution history;
- user feedback;
- eval datasets;
- failure mining;
- curated reusable memory;
- prompt/routing/config/capability versioning;
- candidate generation;
- shadow comparison;
- regression gates;
- human-controlled promotion and rollback;
- complete PO Workspace frontend;
- end-to-end tests over the real application stack.

---

## 4. Non-negotiable architectural invariants

These rules must survive every future refactor.

### 4.1 AS21 is a source of truth, not an LLM knowledge source

The LLM may interpret language but must never invent:

- task fields;
- employees;
- statuses;
- sprints;
- releases;
- priorities;
- attachments;
- source results.

All such facts must come from AS21/SWTR or another declared source.

### 4.2 Source filtering must use the real source contract

If task-api supports explicit parameters such as:

- `assignee`
- `status`
- `source`
- `limit`
- `offset`

then the adapter must use those parameters explicitly.

Never send an unsupported `q`, pseudo-JQL or invented parameter and assume the source will interpret it.

Filters unsupported by the transport may be applied only in a bounded, deterministic second stage over an explicitly retrieved corpus.

### 4.3 Fail closed

Source failure must never look like a legitimate empty result.

Distinguish at least:

- no matching tasks;
- source unavailable;
- timeout;
- malformed source response;
- unsupported capability;
- mapping failure.

### 4.4 Canonical Task must preserve source facts

The canonical task model must not silently drop raw source facts needed by downstream features.

Required mapping coverage includes, where present:

- key / source id;
- title;
- description;
- workflow status;
- status category;
- assignee display name;
- assignee login/id;
- priority;
- sprint id;
- release id;
- created/updated/due/resolved dates;
- estimate / effort;
- labels;
- components;
- attachments;
- source URL;
- source identity;
- status history when the source exposes it.

### 4.5 LLM interprets; code retrieves and calculates

LLM may:

- classify ambiguous intent;
- normalize wording;
- summarize;
- explain;
- propose candidate improvements.

LLM must not:

- calculate product metrics;
- perform hidden task filtering;
- override deterministic source facts;
- silently repair source bugs;
- promote its own learned behavior.

### 4.6 Learning must never compensate for a broken source layer

The learning loop may improve semantics, routing, clarifications, prompts, knowledge and candidate tests.

It must never learn rules whose purpose is to hide:

- incorrect AS21 mapping;
- incorrect filtering;
- missing source fields;
- transport defects;
- broken deterministic metrics.

If source truth is wrong, fix the source contract first.

### 4.7 Every production behavior must be observable

For each request, traces must make it possible to answer:

- what the user asked;
- what intent/entities were resolved;
- which version processed it;
- which source was called;
- which filters were applied;
- what evidence was returned;
- whether LLM was used;
- what deterministic calculations ran;
- what warnings/errors occurred;
- what final answer was produced.

### 4.8 No uncontrolled self-modification

“Self-learning” means controlled AI-PDLC:

`run -> trace -> feedback -> evaluate -> mine failures -> candidate -> shadow -> regression -> human approval -> promotion -> observe -> rollback`

It does not mean production code rewriting itself after one user correction.

---

## 5. Evolution map: legacy -> target

### Legacy path

```text
React UI
  -> agent request routing
  -> s21_agent / team-performance agent
  -> TaskService / SWTR adapter
  -> FastAPI task-api
  -> local/synced AS21 task repository
  -> response
```

Strengths to preserve:

- working UI workflows;
- explicit filters;
- proven AS21 parsing;
- deterministic simple task search;
- existing team/sprint analytics;
- source URL behavior;
- local vs AS21 task distinction.

Weaknesses to remove:

- overlapping MCP paths;
- duplicate agent implementations;
- duplicated repository logic;
- hard-coded networking;
- LLM calls for deterministic queries;
- raw source dictionaries leaking through layers;
- mixed concerns in agent classes;
- insufficient versioning/evaluation.

### Target path

```text
PO Workspace Frontend
        |
        v
PO API / Session Boundary
        |
        v
Observed Harness Runtime
        |
        +--> semantic interpretation
        +--> deterministic entity grounding
        +--> clarification
        +--> capability planning/routing
        |
        v
Deterministic Capabilities
        |
        +--> Task Intelligence
        +--> Sprint Intelligence
        +--> Team Intelligence
        +--> Release Intelligence
        |
        v
Canonical Source / Metrics Layer
        |
        +--> AS21 Adapter
        +--> Metrics Engine
        +--> Knowledge Sources
        |
        v
AS21 / SWTR and declared data sources

Observed Runtime
        |
        +--> Trace / Operational History
        +--> Feedback
        +--> Eval Store
        +--> Failure Mining
        +--> Curated Memory
        +--> Candidate Evaluation
        +--> Shadow Runtime
        +--> Regression Gate
        +--> Human Promotion/Rollback
```

---

# 6. Master implementation roadmap

The stages below are sequential gates. A later stage may be prototyped only if it does not hide failures in an earlier stage.

---

## PHASE 0 — Historical archaeology and behavioral inventory

**Status:** partially complete; must remain maintainable.

### Goal

Create a permanent understanding of what the original application actually did before replacing it.

### Required work

- inspect early integrated commit `6b3bee08...`;
- inventory source/API contracts;
- inventory task fields and parsing rules;
- inventory analytics formulas;
- inventory frontend screens/components;
- inventory local-task behavior;
- inventory AS21 sync behavior;
- inventory agent query examples;
- inventory known edge cases;
- record proven behavior as regression tests/golden cases.

### Exit gate

We have a documented feature/contract inventory and tests for every legacy behavior that is still required.

---

## PHASE 1 — Restore and lock AS21 source contract

**Status:** IN PROGRESS.

### Goal

Prove that the current Harness reads and filters real AS21 data correctly.

### Work

- restore explicit task-api filter usage;
- eliminate unsupported `q` behavior;
- preserve fail-closed semantics;
- restore canonical mapping of AS21 attributes;
- test assignee filtering;
- test status filtering;
- test project/space filtering;
- test sprint filtering;
- test release filtering;
- test key lookup;
- test unsupported query clauses;
- test malformed/source-unavailable behavior;
- run against real AS21 task-api data;
- compare with legacy behavior.

### Mandatory regression cases

- `assignee = Kalachanov.V.V` must not return another assignee;
- nonexistent assignee must not return the full corpus;
- nonexistent project/sprint/key must not return the full corpus;
- mixed supported + unknown expression must not silently widen results;
- source outage must not return `[]` as if zero tasks were found.

### Exit gate

`AS21_SOURCE_CONTRACT = GREEN`

and

`READY_TO_RETURN_TO_LEARNING_LOOP = YES`

from an independent adversarial test run over real AS21 data.

---

## PHASE 2 — Canonical domain parity

### Goal

Make the canonical v2 domain model at least as expressive as the working legacy data path.

### Work

Verify mapping for:

- identifiers;
- description;
- status and category;
- assignee + login/id;
- priority;
- sprint;
- release;
- estimates;
- timestamps;
- labels;
- components;
- attachment metadata;
- history/status transitions;
- source URLs.

Add a **raw-present / canonical-missing** detector to tests.

### Exit gate

No required source field is silently discarded.

---

## PHASE 3 — Task Intelligence parity

### Goal

Recover all useful task-agent behavior inside the new deterministic capability layer.

### Capabilities

- find task by key;
- task search by text;
- assignee/status/space/sprint/release filters;
- attachment-type search;
- task summary;
- task quality/completeness;
- missing requirements;
- task history;
- time in status;
- aging;
- blocked task analysis;
- source evidence in every result.

### Rule

Retrieval and quality rules are deterministic. LLM may only synthesize or explain.

### Exit gate

Golden set from the legacy agent passes on the Harness implementation.

---

## PHASE 4 — Sprint, team and release analytics parity

### Goal

Move all validated legacy analytics into deterministic v2 capabilities.

### Sprint

- sprint health;
- committed/completed scope;
- predictability;
- scope change;
- carryover;
- aging;
- WIP;
- throughput;
- cycle time;
- lead time.

### Team

- workload distribution;
- member load;
- capacity;
- competency matching;
- bottlenecks;
- task risk.

### Release

- release scope;
- completion;
- dependency risk;
- forecast;
- sprint linkage.

### Exit gate

For a frozen AS21 corpus, v2 metrics are deterministic, reproducible and equal to the approved baseline formulas.

---

## PHASE 5 — Harness orchestration and dialogue

### Goal

Make the Harness the only production reasoning path.

### Work

- semantic frame contract;
- bounded LLM interpretation;
- deterministic router;
- deterministic entity grounding;
- clarification flow;
- intent-preserving multi-turn dialogue;
- evidence aggregation;
- response synthesis;
- no second hidden agent implementation;
- session state isolation;
- source-awareness.

### Required dialogue scenarios

- person only;
- sprint only;
- person + sprint;
- status semantics;
- ambiguous employee;
- unknown sprint;
- correction by user;
- retry after clarification;
- task reference follow-up;
- product/release follow-up.

### Exit gate

Dialogue improves usability without changing deterministic source truth.

---

## PHASE 6 — Controlled learning loop

### Goal

Enable learning only after source and deterministic capability correctness are proven.

### Layers

1. Session memory.
2. Operational execution history.
3. Curated approved memory.
4. Feedback capture.
5. Eval case generation/storage.
6. Failure mining.
7. Candidate semantics/routing/prompt/knowledge generation.
8. Candidate versioning.
9. Offline evaluation.
10. Shadow evaluation.
11. Regression gate.
12. Human promotion.
13. Rollback.

### Learning-loop invariants

- one correction does not directly alter production behavior;
- candidate behavior is versioned;
- baseline and candidate use the same frozen corpus;
- no candidate may access different source data;
- candidate cannot auto-promote;
- all improvement evidence is retained;
- positive result cannot exceed approval policy;
- regression on known behavior rejects candidate.

### Exit gate

A user correction can produce a candidate improvement that wins a controlled eval and can be deliberately promoted, while the production baseline remains reproducible.

---

## PHASE 7 — Backend API and production boundary

### Goal

Expose one stable API for the frontend, independent of internal Harness classes.

### Required API areas

- query/chat;
- session lifecycle;
- tasks;
- task details;
- sprints;
- releases;
- team;
- analytics;
- execution history;
- feedback;
- version/readiness;
- health;
- sync state;
- local-task CRUD.

### Requirements

- correlation ids;
- typed request/response models;
- no stack traces/secrets;
- explicit source-unavailable response states;
- cancellation/timeouts;
- version metadata;
- stable error taxonomy.

### Exit gate

Frontend can operate without importing or knowing Harness implementation details.

---

## PHASE 8 — Frontend migration: screen-by-screen

The frontend must be reintroduced **before** claiming E2E readiness.

### 8.1 App shell

Target:

- WORKS branding;
- DB Tribe badge;
- PO Workspace identity;
- sidebar;
- top bar;
- desktop-first AS21-like visual system;
- reusable theme tokens.

### 8.2 Overview

Show concise PO-level status:

- current sprint summary;
- tasks requiring attention;
- blocked/aging tasks;
- release risks;
- team load highlights;
- recent agent activity.

No decorative metric may be fabricated when the underlying source is unavailable.

### 8.3 Tasks

Must preserve legacy functionality and UI target:

- AS21 vs Local source badge;
- search;
- status multi-filter;
- assignee filter;
- product/space filter;
- sprint filter;
- priority filter;
- source filter;
- active filter chips;
- reset;
- task list/cards;
- source URL;
- sync action;
- loading/error/empty states.

### 8.4 Task details

Drawer/page with:

- key/title;
- source;
- description;
- status;
- assignee;
- sprint;
- product;
- priority;
- dates;
- attachments;
- history where available;
- source URL;
- quality analysis;
- agent actions.

### 8.5 Local task creation

Drawer/modal with:

- title;
- description;
- assignee;
- status;
- sprint;
- product;
- priority;
- tags;
- due date;
- local source marker.

AS21 tasks remain source-controlled; local CRUD must not silently overwrite AS21 fields.

### 8.6 Sprints

- sprint selector;
- health;
- progress;
- carryover;
- scope change;
- WIP/throughput;
- member breakdown;
- risk list.

### 8.7 Releases

- release selector;
- scope;
- completion;
- linked sprints;
- blocked tasks;
- risk/forecast;
- relevant dependencies.

### 8.8 Team

- members;
- roles;
- products;
- workload;
- capacity;
- competency profile;
- relevant task list.

### 8.9 Analytics

- velocity;
- predictability;
- throughput;
- cycle/lead time;
- WIP;
- aging;
- bottlenecks;
- trends;
- explicit source/timeframe.

### 8.10 Agent / conversation

The agent experience must support:

- natural-language request;
- follow-up questions;
- clarification;
- evidence/task links;
- visible source-readiness warnings;
- feedback control;
- session continuity;
- no false “0 tasks” on source failure.

### 8.11 History / evaluation / settings

At minimum for engineering/admin mode:

- execution trace history;
- active versions;
- candidate/shadow status;
- feedback history;
- source readiness;
- configured products/team/workflow;
- diagnostics without credentials.

### Exit gate

Every screen has component tests, API integration tests and an executable E2E scenario.

---

## PHASE 9 — Full integration and E2E

### Goal

Test the actual user journey, not isolated modules.

### Required stack

```text
Browser
 -> React PO Workspace
 -> PO backend API
 -> Harness runtime
 -> deterministic capability
 -> AS21 adapter
 -> task-api / real or frozen AS21 source
 -> response/evidence
 -> UI rendering
```

### E2E scenario families

1. Search tasks by person.
2. Search person + status.
3. Search person + sprint.
4. Open task details.
5. Open task in AS21.
6. Filter list and clear filters.
7. AS21 sync.
8. Source outage handling.
9. Create/edit local task.
10. Ask agent for task summary.
11. Ask agent for missing requirements.
12. Ask sprint-health question.
13. Ask release-risk question.
14. Ambiguous query -> clarification -> answer.
15. User correction -> feedback captured.
16. Retry in same session.
17. Candidate/shadow evaluation does not alter served baseline.
18. Page refresh preserves allowed session/UI state.

### Exit gate

E2E suite passes against both:

- deterministic frozen corpus in CI;
- controlled real-AS21 environment for release validation.

---

## PHASE 10 — Security, reliability and operational hardening

### Work

- credentials never stored in repo;
- PII handling review;
- source timeout budgets;
- circuit/failure behavior;
- rate limiting where needed;
- logging redaction;
- bounded context;
- storage retention rules;
- frontend error boundaries;
- health/readiness endpoints;
- version observability;
- rollback runbook;
- backup of operational/eval data;
- dependency vulnerability checks;
- source contract monitoring.

### Exit gate

No known blocker/high issue in production-critical paths.

---

## PHASE 11 — Release readiness and production baseline

### Required release evidence

- AS21 contract GREEN;
- canonical mapping GREEN;
- deterministic task capability GREEN;
- analytics parity GREEN;
- Harness dialogue GREEN;
- learning loop GREEN;
- frontend E2E GREEN;
- real-source smoke GREEN;
- source outage behavior GREEN;
- regression suite GREEN;
- security review acceptable;
- documented rollback.

Create a tagged, immutable baseline that all future candidate versions compare against.

---

# 7. Permanent regression matrix

Every significant change must re-run the relevant part of this matrix.

| Layer | Must prove |
|---|---|
| AS21 transport | correct endpoint, parameters, auth boundary, timeout/error semantics |
| AS21 mapping | no required source fields dropped |
| Filtering | assignee/status/space/sprint/release/key exactness |
| Domain | canonical invariants and validation |
| Metrics | deterministic formula parity |
| Capabilities | evidence-backed results |
| Entity grounding | LLM cannot invent identifiers |
| Dialogue | clarification does not change source truth |
| Learning | candidate isolated from baseline and source corpus |
| API | stable typed responses and explicit error states |
| Frontend | correct rendering of success/loading/empty/error |
| E2E | real user workflow works through all layers |

---

# 8. Test hierarchy

Tests must not be treated as interchangeable.

### Level 1 — Unit

Pure functions, parsers, formulas, mappings, routing rules.

### Level 2 — Contract

Adapters vs exact source/API contract.

### Level 3 — Golden behavior

Approved legacy and product scenarios with expected results.

### Level 4 — Integration

Harness + capabilities + adapter + API boundary.

### Level 5 — Frozen-source regression

Same immutable corpus for baseline and candidate.

### Level 6 — Real-source validation

Read-only tests against actual AS21/task-api.

### Level 7 — Browser E2E

Frontend through backend/Harness/source.

### Level 8 — Adversarial / false-green

Prove failures cannot masquerade as success.

A phase is not GREEN merely because unit tests pass.

---

# 9. Known false-green patterns to guard forever

Keep these examples as permanent tests and review prompts.

1. Source endpoint ignores an unsupported query parameter and returns all tasks.
2. Adapter catches all exceptions and returns an empty list.
3. User asks for one assignee; system returns all tasks but answer text still sounds plausible.
4. Canonical mapping drops `assignee_id` or `sprint_id`, so entity grounding cannot work.
5. LLM “fixes” missing source facts using guesses.
6. Fake-adapter tests are green while real adapter is broken.
7. Candidate and baseline are evaluated on different task corpora.
8. Learning rule compensates for a deterministic parser bug.
9. UI interprets source outage as an empty-state message.
10. Full regression contains pre-existing failures, but a new failure is mislabeled as pre-existing without base comparison.

---

# 10. Source-contract checklist for AS21 changes

Any future change touching AS21 transport, mapping, filters, sync, or canonical task fields must answer all of these before merge:

- What exact AS21/task-api endpoint is used?
- What parameters does that endpoint really support?
- Which filters are source-side and which are bounded local filters?
- What happens if the source ignores a parameter?
- What happens on timeout?
- What happens on malformed JSON?
- What happens on non-list payload?
- How is “no tasks” distinguished from “source unavailable”?
- Which raw fields are present?
- Which canonical fields are populated?
- Are any raw-present fields dropped?
- Is the behavior tested with real AS21 data?
- Is there an adversarial test against widening the result set?
- Did the change preserve legacy-required behavior?

If any answer is unknown, the change is not ready.

---

# 11. Definition of Done for a development step

A step is DONE only when all applicable items are satisfied:

- implementation complete;
- targeted tests executed;
- regression against base executed;
- no unexplained regression;
- source contract tested if relevant;
- real source tested if relevant;
- E2E tested if UI/runtime boundary changed;
- docs updated;
- this master plan status updated;
- known limitations recorded;
- next step explicitly identified.

---

# 12. Working protocol for ChatGPT and GigaCode

## ChatGPT

Primary role:

- architect;
- implementation owner;
- code author;
- architecture reviewer;
- roadmap maintainer;
- source-contract guardian.

Before writing code:

1. read this master plan;
2. identify current phase;
3. inspect affected historical reference if behavior existed before;
4. inspect current implementation;
5. preserve invariants;
6. implement narrowly;
7. update tests and this plan when required.

## GigaCode

Primary role for the current workflow:

- independent tester;
- adversarial reviewer;
- regression runner;
- real-environment verifier.

Unless explicitly reassigned, GigaCode must not automatically repair code while performing an independent validation run.

---

# 13. Current execution state

Update this section after every accepted phase/change.

### Completed / substantially implemented

- [x] legacy application exists as behavioral reference;
- [x] v2 side-by-side Harness architecture created;
- [x] canonical domain model created;
- [x] deterministic task-intelligence capability layer created;
- [x] observed Harness runtime created;
- [x] entity grounding created;
- [x] dialogue Harness created;
- [x] source-aware runtime created;
- [x] frozen AS21 evaluation path created;
- [x] evaluation/shadow/candidate infrastructure substantially created;
- [x] controlled learning-loop infrastructure substantially created;
- [x] initial adversarial baseline-vs-candidate evaluation created.

### Current blocking work

- [ ] complete AS21 source-contract recovery and adversarial validation;
- [ ] verify real assignee/status/space/sprint/release filters;
- [ ] verify complete canonical AS21 attribute extraction;
- [ ] classify any missing source capabilities such as history/attachments;
- [ ] merge/finalize recovery only after GREEN report.

### Immediately after AS21 GREEN

- [ ] return to learning-loop user-correction scenario;
- [ ] confirm correction changes candidate semantics without corrupting baseline;
- [ ] add approved regression case for the exact Kalachanov/Ivanov correction scenario;
- [ ] verify repeated request in one session improves only through approved semantics mechanism;
- [ ] verify no source-layer heuristic is stored as learning.

### Next major block

- [ ] inventory complete legacy frontend behavior;
- [ ] wire current Harness backend to frontend-facing API;
- [ ] launch PO Workspace frontend;
- [ ] migrate screens one-by-one;
- [ ] start browser E2E as soon as Tasks + Agent screens are wired;
- [ ] expand E2E to Sprint/Release/Team/Analytics screens;
- [ ] complete production readiness gates.

---

# 14. Decision log

Append durable architectural decisions here or link an ADR.

### ADR-MP-001 — Legacy is behavioral reference, not architecture template

Accepted. Proven behavior must be preserved; obsolete architecture need not be copied.

### ADR-MP-002 — Deterministic source truth precedes learning

Accepted. Learning work pauses when AS21/source correctness is uncertain.

### ADR-MP-003 — Real AS21 contract tests are mandatory

Accepted. Fake/frozen tests cannot alone declare the production adapter GREEN.

### ADR-MP-004 — Harness is the target production agent architecture

Accepted. Do not reintroduce a second autonomous legacy agent path beside the Harness.

### ADR-MP-005 — GigaCode acts as independent tester during recovery phases

Accepted for the current workflow. Code changes are authored separately, then independently attacked/tested.

---

# 15. How this file must evolve

This is a living roadmap, but not an informal note.

When a phase is completed:

1. update `Current execution state`;
2. mark the relevant checklist items;
3. add newly discovered regression cases;
4. add/adjust an ADR when architecture changes;
5. record any intentionally deferred capability;
6. name the next active phase.

Do not delete historical lessons merely because the immediate bug was fixed.

The purpose of this file is specifically to prevent future “architectural amnesia”.
