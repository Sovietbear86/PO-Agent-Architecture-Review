# Hermes-inspired Agent Core v3

## Purpose

This document defines the additive replacement architecture for the upper PO Agent orchestration layer. It preserves the proven REAL AS21 source/data plane and introduces a new session-safe, contract-driven agent core inspired by Hermes patterns: explicit sessions, progressive skills, capability registry, deterministic executors, isolated learning review and auditable promotion.

The migration is strangler-style. Legacy Harness remains available until a capability family is certified A/B/C through v3.

## 1. Preserved lower plane

The following components remain authoritative building blocks unless a separate source defect is proven:

```text
REAL AS21
  -> MCP-SWTR
  -> Task API live read facades
  -> canonical source models
  -> evidence primitives
```

No v3 component may substitute local DB/sync/fake/frozen task data as production truth.

## 2. Agent Core v3 processing model

```text
Input
 -> Session Envelope
 -> LLM Semantic Draft
 -> Deterministic Grounding
 -> Accepted Turn Contract (immutable)
 -> Capability Registry lookup
 -> Deterministic Executor
 -> Source Evidence
 -> Result Postcondition Validation
 -> Response Synthesis
 -> Output
```

The accepted contract is the central handoff object. Every downstream layer receives the same immutable constraint set.

## 3. Session Envelope

```python
SessionEnvelope(
    conversation_id: str,
    runtime_session_id: str,
    memory_scope_id: str | None,
    turn_id: str,
)
```

Rules:
- new visible chat -> new conversation_id and runtime_session_id;
- runtime_session_id owns only transient dialogue state;
- memory_scope_id owns durable learning scope and must not imply correction state;
- QA uses unique runtime_session_id per case;
- browser and QA state cannot collide;
- future forks/subagents receive explicit parent lineage, never implicit shared state.

## 4. Accepted Turn Contract

Minimum schema:

```python
AcceptedTurnContract(
    turn_id: str,
    intent: str,
    constraints: Mapping[str, str],
    requested_constraints: frozenset[str],
    source_authority: str,
    required_postconditions: tuple[Postcondition, ...],
    semantic_confidence: float,
)
```

Properties:
- immutable after acceptance;
- every explicitly requested constraint must be represented in `requested_constraints`;
- canonicalization may change a value but cannot silently remove a requested field;
- a capability must declare support for every requested constraint before execution;
- any unsupported/unresolved constraint fails closed before source retrieval.

Example:

```yaml
intent: task_search
constraints:
  assignee: Kalachanov.V.V
  space: WMB
requested_constraints: [assignee, space]
source_authority: REAL_AS21
postconditions:
  - task.assignee == Kalachanov.V.V
  - task.space == WMB
```

## 5. Constraint Preservation Guard

Before capability execution:

```text
semantic requested fields
 == grounded accepted requested fields
 <= capability supported constraints
 == executor received required fields
```

If any requested field disappears, execution stops with typed `CONSTRAINT_LOSS` rather than returning data.

This makes a `WMB` request returning DMS evidence structurally invalid.

## 6. Capability Registry

Each v3 capability registers a contract rather than relying on implicit skill-label conventions.

```yaml
id: task-search
version: 1
required_slots: []
optional_slots: [assignee, space, status, sprint_id, release_id]
supported_constraints: [assignee, space, status, sprint_id, release_id]
source_authority: REAL_AS21
executor: task_search_executor
oracle: direct_mcp_task_search
postconditions:
  - returned rows satisfy all supplied filters
availability:
  - search_users
  - find_units_by_filter
```

Registry responsibilities:
- capability availability;
- constraint support;
- deterministic executor binding;
- source and Oracle declaration;
- postconditions;
- certification metadata.

The LLM does not choose MCP endpoints.

## 7. Result Postcondition Validator

Every factual result passes validation before response synthesis.

Task collection validation includes, where requested:
- exact task key shape;
- task belongs to requested space;
- task assignee matches canonical requested identity;
- requested status semantic is satisfied;
- sprint/release membership matches source-grounded constraint;
- evidence exists for every returned source fact.

A violation returns typed `RESULT_CONTRACT_VIOLATION`. Contradictory rows are never rendered to the user as a partial success.

## 8. Progressive Skills

Skills are procedural memory/contracts, not source facts.

Progressive disclosure:
1. LLM sees compact skill metadata: id/domain/description;
2. selected candidate loads full skill contract;
3. detailed references/procedures load only when execution requires them.

This avoids injecting all 54 full skill descriptions into every semantic turn.

## 9. Deterministic Executors

Simple factual request:

```text
one LLM semantic decision
 -> one grounded contract
 -> one deterministic executor
 -> source result
 -> validator
 -> one synthesis step
```

Do not use subagents for a simple task lookup/search.

Heavy analytics may use bounded deterministic pipelines or isolated subagents only when multiple independent domains must be combined.

## 10. Learning Reviewer

Learning is outside the main response path.

```text
completed turn + user feedback
 -> reviewer snapshot
 -> independent source recheck
 -> compare accepted contract/result/source truth
 -> mismatch proven?
      no -> no learning; targeted clarification if useful
      yes -> first failing boundary
             -> generalized candidate
             -> sandbox/replay
             -> independent A/B
             -> promote/reject
```

Reviewer outputs procedural candidates only.

Forbidden:
- user/task-specific counts as learned truth;
- hardcoded task IDs;
- source fact overrides;
- Python rewrite by runtime learning.

## 11. Strangler routing

A feature/routing seam chooses legacy vs v3 per capability family.

Initial v3 pilots:
- exact task lookup;
- task search by assignee;
- task search by assignee + space;
- task search by assignee + space + open/not-completed status.

Legacy remains default for non-migrated families.

A family flips to v3 default only after focused A/B/C certification.

## 12. Observability

Every v3 turn trace must expose:

```text
conversation_id
runtime_session_id
turn_id
interpreter_class
llm_used
raw_semantic_frame
grounded_values
accepted_turn_contract
capability_id/version
executor_args
source_route
source_evidence_ids
postcondition_results
final_status
```

No hidden constraint mutation is allowed.

## 13. Acceptance

Pilot acceptance uses three independent paths:

```text
A = Agent Core v3
B = direct REAL AS21 Oracle
C = real browser/UI
```

For task sets:

```text
A.keys == B.keys == C.keys
```

and every requested constraint must be demonstrably preserved.

## 14. Migration order

1. Session Envelope + Accepted Turn Contract + validator
2. v3 routing seam, disabled by default
3. task-search pilot family
4. Capability Registry
5. progressive skills
6. deterministic heavy executors
7. Learning Reviewer
8. family-by-family migration
9. full 54-skill A/B/C
10. complete UI acceptance and release hardening
