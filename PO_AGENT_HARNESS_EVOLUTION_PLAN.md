# PO Agent Harness — Authoritative Evolution Plan

**Status:** ACTIVE / consolidated source of truth  
**Current branch:** `feat/core8-real-query-hardening-v2`  
**Last reviewed:** 2026-09-02  
**Current active gate:** Assignment 132 — full 54-skill TRUE A/B certification against REAL AS21 + Learning Loop regression  
**Next architecture phase:** post-132 Architecture Evolution — Learning Reviewer, Session Isolation, Capability Registry, Progressive Skills  
**Frontend status:** DEFERRED until backend + learning certification is genuinely GREEN  
**Purpose:** preserve the original PO Agent behavior while evolving it into a source-grounded, self-improving, auditable agent with controlled persistent learning.

> This document is the execution roadmap. Historical QA reports remain evidence, but current runtime behavior and current source-backed regression outrank historical GREEN. GigaCode is QA-only. Production code changes are owned by the ChatGPT/OpenAI side after a defect boundary is proven.

---

## 0. Non-negotiable principles

1. Preserve the useful product behavior of the original PO Agent.
2. The complete production skill catalog must be discovered from the running registry; current reconciled target is 54 skills, but runtime discovery is authoritative.
3. AS21/SWTR business facts must be validated against real read-only source data. Fixtures, local DB snapshots, fake/mock/frozen data and historical counts are never acceptance truth.
4. GigaCode is tester/adversarial reviewer only. It must not modify production code, prompts, skills, adapters, learning implementation, AS21 data or test rules.
5. Deterministic retrieval, filtering and calculation stay in code. LLM interprets, clarifies and synthesizes; it must not invent AS21 facts or deterministic metrics.
6. A successful HTTP response is not proof of semantic correctness. Requested constraints must survive semantic interpretation, grounding, capability argument building, source routing and final validation.
7. Exact task-key-set equality against an independent authoritative Oracle B outranks prose and count-only checks.
8. Exact task lookup must use authoritative point-read semantics and must never leak an unrelated assignee/task collection.
9. Historical GREEN is a baseline, not permanent acceptance. Any later REAL-source counterexample reopens the affected gate.
10. Every production skill must pass functional regression and the applicable learning-loop contract before backend acceptance is complete.
11. Learning must generalize behavior, not memorize entities, task IDs, sprint IDs, answers, counts or user-provided source facts.
12. Learned behavior must be versioned, auditable, restart-safe and rollbackable.
13. A user correction never overrides contradictory authoritative SWTR evidence.
14. Runtime learning must not rewrite Python, prompts, Skill Catalog definitions or AS21 source data.
15. Any regression in an already-green critical skill blocks backend certification.
16. Any semantic/correction fix must preserve the complete learning loop.
17. Frontend finalization and full browser E2E happen only after backend functional + learning certification is genuinely GREEN.
18. No AS21 write authority is permitted during acceptance.
19. **No surrogate tests:** Agent A and Oracle B must be independent production paths. Harness output cannot serve as Oracle B.
20. QA runners must never silently substitute local task caches, sync jobs or bounded lists for REAL AS21 truth.
21. Source timeout and latency are part of the contract: slow REAL AS21 is acceptable; false fast GREEN is not.
22. New UI conversations must be session-isolated from prior browser turns and from QA marathon sessions.

---

## 1. Current target evolution

```text
Original PO Agent / legacy behavior
        |
        v
AS21/SWTR source contract + Core hardening
        |
        v
Exact-key / sprint / multi-filter / history hardening
        |
        v
Controlled persistent Learning Loop foundation
        |
        v
Semantic correction + session-state hardening
        |
        v
TRUE A/B source recovery for assignee queries
        |
        v
CURRENT: Assignment 132
FULL 54-SKILL TRUE A/B CERTIFICATION
+ exact-task semantics
+ dialogue regression
+ Learning Loop regression
        |
        v
POST-132 ARCHITECTURE EVOLUTION
Learning Reviewer + Session Isolation
+ Capability Registry + Progressive Skills
        |
        v
Backend catalog certification / Gate E closure
        |
        v
Frontend / PO Workspace acceptance
        |
        v
Full browser E2E
        |
        v
Release hardening and release readiness
```

---

## 2. What has been proven during the current recovery line

The previous total-regression campaign exposed that some earlier GREEN reports were not sufficiently authoritative. The acceptance model has therefore been tightened to TRUE A/B.

### Proven owner-side recovery

The current branch now contains fixes that have already passed focused source-backed checks:

- live assignee routing preserves the authoritative REAL AS21 path instead of falling back to empty legacy `/api/v1/tasks` behavior;
- composite task-search results expose normalized `task_keys` for exact A/B comparison;
- approved product spaces `WMB`, `STS`, `OLP`, `DMS`, `CRPV` are grounded independently of whether a generic task scan happens to contain tasks from that space;
- long AS21 titles are accepted by the domain model and no longer crash semantic context construction;
- session clarification handling was repaired so a clarification choice does not automatically become a semantic correction;
- REAL MCP-SWTR response envelopes and inner JSON payloads are now treated as distinct layers during QA/oracle work.

### Focused TRUE A/B evidence already obtained

Assignment 131 established a meaningful end-to-end recovery gate for assignee queries with fresh REAL AS21 Oracle B:

```text
natural-language query
 -> LLM semantic interpretation
 -> entity grounding
 -> capability selection
 -> live Task API route
 -> MCP-SWTR
 -> REAL AS21
 -> task key set
 -> response
```

Focused Garanin generic/DMS/OLP cases and a second-member control matched fresh independent source truth. This is strong evidence that the current assignee-route fix is not entity-hardcoded.

However Assignment 131 did **not** execute the complete 54-skill regression, so its wording `FULL_REGRESSION_GREEN` is not accepted as final backend certification. Assignment 132 exists specifically to close that gap.

---

## 3. Current active gate — Assignment 132

Assignment 132 is the first accepted candidate for a complete backend certification run under the strengthened anti-surrogate rules.

### Required contents

1. clean runtime provenance and fresh process IDs;
2. REAL AS21/MCP-SWTR health;
3. focused sanity A/B for already-recovered assignee routes;
4. exact-task semantics forensic:
   - at least two current existing IDs;
   - one guaranteed nonexistent ID;
   - distinguish `NOT_FOUND` from `SOURCE_UNAVAILABLE`;
5. all 54 discovered production skills actually executed/classified;
6. independent Oracle B wherever source-backed factual comparison is possible;
7. exact key-set equality for task collections;
8. semantic/dialogue regression pack;
9. Russian-language contract;
10. no invented sprint/member/status/space;
11. Learning Loop regression through the actually supported runtime path;
12. source integrity and latency evidence;
13. anti-surrogate audit;
14. exact arithmetic across the 54-skill matrix.

### Accepted final GREEN

`FULL_54_SKILL_AB_CERTIFICATION_GREEN` is allowed only when:

```text
54 unique production skills really executed/classified
+ no proven product defect
+ required factual A/B comparisons GREEN
+ no surrogate Oracle
+ Learning Loop contract GREEN or safely typed non-applicable
```

If the marathon is skipped or partial, FULL GREEN is forbidden.

---

## 4. Source and Oracle architecture contract

### Agent A

```text
User/UI
 -> Harness API
 -> semantic interpreter
 -> grounded frame
 -> skill/capability
 -> Task API
 -> MCP-SWTR
 -> REAL AS21
```

### Oracle B

Oracle B must be independently constructed from authoritative REAL AS21 operations. It must not reuse the Harness answer, the same capability calculation, local task DB, previous report counts or fixtures.

For task collections the primary equality rule is:

```text
set(Agent_A.task_keys) == set(Oracle_B.task_keys)
```

### Allowed scope

Production task spaces are:

```text
WMB
STS
OLP
DMS
CRPV
```

QA must not introduce random external members/spaces as control data. Controls come from the configured team and approved spaces unless a test explicitly concerns rejection of an out-of-scope entity.

### No synchronization as truth

Local synchronization may exist for non-authoritative product features, but acceptance of live agent answers must not depend on preloading AS21 tasks into a local DB. During source certification, Agent A and Oracle B read REAL AS21 directly through approved read-only routes.

---

## 5. Semantic interpretation contract

Production natural-language understanding remains **LLM-first**.

The intended division is:

```text
LLM:
  infer intent
  extract human semantic slots
  detect ambiguity

Deterministic grounding:
  resolve members
  validate spaces
  validate sprints/statuses/releases
  map to authoritative identifiers

Capability code:
  retrieve/filter/calculate deterministically
```

Legacy phrase heuristics must not silently become the production NLP path for ordinary Russian user queries. Post-132 browser forensic must explicitly expose for key UI cases:

- interpreter class;
- `llm_used` flag;
- raw LLM semantic frame;
- grounded semantic frame;
- resolved skill;
- capability args;
- final source route.

This observability is required so we never again infer from a correct answer that LLM-first interpretation must have been used.

---

## 6. Learning Loop — current contract and required evolution

### Existing protected contract

The current controlled learning foundation requires:

```text
negative feedback / correction
 -> fresh authoritative source recheck
 -> source-grounded correction
 -> generalized allow-listed policy candidate
 -> validation
 -> persistence/versioning
 -> reuse where applicable
 -> cold restart survival
 -> rollback
```

Safety requirements:

- no entity memorization;
- no answer/count memorization;
- no fabricated source facts;
- no direct production code/prompt/catalog mutation;
- no promotion from unsupported user assertion;
- malformed policy state fails safely;
- duplicate correction does not create unbounded duplicate active policies;
- rollback actually removes active effect.

### Current UX concern

The current user-visible flow can still behave too passively: after negative feedback the agent may recheck the source and ask the user what exactly should be improved, without independently localizing the mismatch or creating a useful generalized repair candidate.

That is not the target product behavior.

### Post-132 target — Learning Reviewer architecture

Inspired by the strongest pattern found in NousResearch/Hermes, learning should move to a **separate asynchronous review plane** so the ordinary conversation path does not have to both answer and self-modify.

Target:

```text
User feedback
    |
    v
Learning Reviewer (isolated context)
    |
    +-- previous semantic frame/result
    +-- user feedback
    +-- independent REAL AS21 Oracle recheck
    |
    v
Mismatch classification
    |
    v
FIRST_FAILING_BOUNDARY
    |
    v
Generalized repair/skill-policy candidate
    |
    v
Sandbox/replay + independent A/B
    |
    v
Promotion Gate
    |
    v
Versioned Skill/Policy Store
```

The reviewer may propose a candidate but must not directly rewrite production Python or source truth.

### Product expectation

A user saying "нет", "неверно" or "улучши" should not merely receive a clarification prompt. When source evidence permits, the system should autonomously:

1. recheck REAL AS21;
2. identify whether the original answer is actually wrong;
3. localize the failure;
4. generate a generalized repair candidate;
5. validate it on independent cases;
6. promote only through governance rules.

If both Agent and Oracle prove the same result, no false learning is created.

---

## 7. Post-132 Architecture Evolution — patterns adopted from Hermes

The following architecture work is now part of the official roadmap and must not be lost after the current marathon.

### EVOLUTION A — Learning Reviewer / Background Review Plane — P0

**Goal:** replace the passive feedback UX with an isolated source-grounded reviewer.

Deliverables:

- immutable snapshot of the original turn;
- independent source recheck;
- mismatch/no-mismatch decision;
- first-failing-boundary evidence;
- generalized candidate only;
- sandbox/replay gate;
- A/B gate before promotion;
- auditable candidate/promotion/rejection records.

### EVOLUTION B — Session Isolation Architecture — P0

Current UI evidence suggests a new visible conversation may sometimes be interpreted as continuation/correction state. Introduce explicit separation:

```text
browser_conversation_id
        |
        v
harness_session_id
        |
        v
user_memory_scope_id
```

Rules:

- New Chat => new `harness_session_id`.
- QA marathon => unique `qa:<assignment>:<case>:<uuid>` session IDs.
- Browser sessions must never share dialogue state with QA sessions.
- Long-term user memory scope is separate from transcript state.
- Concurrent writers to one dialogue session are serialized or rejected safely.

### EVOLUTION C — Capability Registry — P0/P1

Move from implicit skill/capability/adapter coupling to one explicit runtime contract per capability.

Target metadata:

```yaml
id: task-search-assignee
version: 2.x
semantic_contract:
  requires: [assignee]
  optional: [space, status, sprint]
source_contract:
  authority: AS21
  route: live-assignee
  pagination: required
oracle_contract:
  independent_route: true
availability:
  required_tools: [...]
certification:
  last_ab_sha: ...
  exact_key_parity: true
latency_budget:
  p50_ms: ...
  p95_ms: ...
```

The semantic layer should not know MCP endpoint details; the UI should not know AS21 routing; capability availability must be explicit.

### EVOLUTION D — Progressive Skill Disclosure — P1

Do not inject all 54 full skill definitions into every semantic turn.

Target flow:

```text
catalog summary (name + description)
 -> skill candidate selection
 -> load full contract only for top candidate(s)
 -> execute
```

Expected benefits:

- lower context cost;
- lower latency;
- fewer skill-resolution collisions;
- clearer observability of why a skill was selected.

### EVOLUTION E — Deterministic Capability Pipelines — P1

For heavy analytics such as Team Workload, Sprint Intelligence, velocity and release forecast, prefer one deterministic executor over repeated LLM/tool ping-pong.

Target:

```text
LLM semantic frame
 -> one deterministic capability pipeline
 -> bounded REAL AS21 reads
 -> calculation/invariants
 -> compact evidence/result
 -> LLM response formulation
```

This should be evaluated as a primary latency-reduction strategy.

### EVOLUTION F — Isolated Subagents for genuinely complex analysis — P2

Subagents are allowed only where decomposition materially helps, e.g. multi-domain analysis across sprint/team/release/quality. They are not the default path for simple factual queries such as "Задачи Гаранина".

### EVOLUTION G — Session/Skill observability and curation — P2

Add per-skill operational metadata:

- usage count;
- failure rate;
- last REAL A/B certification;
- last source-contract validation;
- latency p50/p95;
- learning candidate count;
- active policy version;
- stale/archived/duplicate skill detection.

---

## 8. UI / browser forensic immediately after Assignment 132

Before broad frontend redesign, run one narrow backend-to-browser forensic because current UI behavior has contradicted direct CLI/Harness behavior multiple times.

Mandatory cases:

1. fresh browser New Chat;
2. prove new browser conversation ID and new Harness session ID;
3. one clean Russian query with no prior dialogue state;
4. capture LLM semantic frame and `llm_used`;
5. capture grounded frame;
6. capture capability/route;
7. prove same REAL AS21 facts as direct Harness and Oracle B;
8. negative feedback/correction in the same browser session;
9. trace the actual Learning Loop/reviewer path;
10. prove a second fresh browser session is uncontaminated.

This forensic happens **before** frontend polish, widget redesign or screen-gap remediation.

---

## 9. Performance / latency track

Current representative responses can take roughly several seconds to several tens of seconds. The objective is not to fake speed by using stale/local truth; it is to reduce avoidable overhead while preserving REAL AS21 authority.

Post-certification profiling must separate:

```text
LLM semantic latency
entity-grounding latency
Task API overhead
MCP-SWTR latency
REAL AS21 latency
post-source filtering/calculation
response synthesis
```

Priority optimizations:

1. progressive skill disclosure;
2. deterministic single-call capability pipelines;
3. avoid duplicate source rechecks within one turn;
4. bounded and contract-aware pagination;
5. cache only non-authoritative metadata where safe;
6. never cache acceptance truth in place of REAL AS21.

---

## 10. Updated ordered next steps

| Step | Work | Exit condition |
|---|---|---|
| **132** | Full 54-skill TRUE A/B marathon + exact-task forensic + dialogue + Learning Loop | 54 skills actually classified; no surrogate GREEN |
| **133** | UI/session/LLM-path forensic on fresh browser sessions | Browser/direct Harness/Oracle path parity proven; session contamination localized if present |
| **134** | Owner fixes for any 132/133 proven defects | Minimal evidence-backed fixes only |
| **135** | Focused post-fix TRUE A/B regression | All affected boundaries GREEN |
| **136** | Learning Reviewer architecture implementation | Negative feedback automatically produces evidence-backed review/candidate flow |
| **137** | Session Isolation implementation | Browser/QA/transcript/memory scopes separated and concurrency-safe |
| **138** | Capability Registry v1 | Explicit skill/source/oracle/availability/certification contracts |
| **139** | Progressive Skill Disclosure + latency benchmark | Reduced context/latency with zero semantic regression |
| **140** | Deterministic heavy-capability pipelines | Team/Sprint/Release analytics use bounded source-backed executors |
| **141** | Final backend clean certification after architecture evolution | Full catalog TRUE A/B + Learning Loop GREEN |
| **142** | Freeze backend evidence, versions and release baseline | Gate E formally closed |
| **143** | Frontend screen-level gap/acceptance audit | Exact UI gap matrix |
| **144** | Frontend remediation | Screen matrix GREEN |
| **145** | Full browser E2E including feedback/learning/session/restart/failure states | Critical E2E 100% GREEN |
| **146** | Release hardening: security/read-only/secrets/packaging/restart | Release candidate |
| **147** | Final release-readiness certification | `RELEASE_READY=YES` |

Assignment numbers after 132 are roadmap identifiers; they may be subdivided when evidence shows multiple defect clusters. Do not skip the architectural work merely because 132 is GREEN.

---

## 11. Decision rules

### During Assignment 132

1. GigaCode changes no production code.
2. All 54 skills must really be executed/classified for FULL GREEN.
3. Factual source-backed PASS requires independent REAL AS21 evidence where the contract permits it.
4. Exact-task lookup is checked independently from assignee collection search.
5. `NOT_FOUND` must not be mislabeled as source outage when source health is proven.
6. Learning Loop is validated via its supported runtime path, not via intentionally absent dashboard endpoints.
7. If a defect is found, identify `FIRST_FAILING_BOUNDARY` before repair.

### After Assignment 132

If `FULL_54_SKILL_AB_CERTIFICATION_GREEN`: do **not** jump directly to frontend redesign. First execute the narrow browser/session/LLM/Learning forensic (133), then Architecture Evolution A-D.

If product defects are proven: group by first failing boundary; owner fixes one boundary at a time; focused QA follows each fix; then resume the roadmap.

If `BLOCKED_BY_ENVIRONMENT`: prove the dependency problem independently; never substitute fake source truth.

---

## 12. Work ownership

### ChatGPT/OpenAI side

- architecture and production changes;
- source-contract and learning-policy decisions;
- QA assignment design;
- roadmap updates;
- diagnosis/fixes after QA reports;
- acceptance and release decisions.

### GigaCode side

- QA/tester only;
- pull current branch and restart real services when instructed;
- use real read-only source data;
- run active assignment autonomously;
- collect traces/adversarial evidence;
- never weaken tests or acceptance rules;
- never modify production code/prompts/skills/adapters/learning implementation;
- commit/push only explicitly allowed QA artifacts;
- stop after report and return SHA + verdict.

---

## 13. Current gate values

```text
GATE_A_SOURCE_CONTRACT = REAL_SOURCE_REQUIRED / TRUE_AB_REQUIRED
GATE_B_CORE_TASK_ROUTING = FOCUSED_GREEN / FULL_132_PENDING
GATE_C_LEARNING_FOUNDATION = IMPLEMENTED
GATE_C_LEARNING_UX = REOPENED_FOR_POST_132_EVOLUTION
GATE_C_PER_SKILL_CERTIFICATION = ASSIGNMENT_132_IN_PROGRESS
GATE_D_REQUIREMENT_RECOVERY = GREEN
CATALOG_IMPLEMENTATION = 54_RECONCILED / RUNTIME_DISCOVERY_AUTHORITATIVE
GATE_E_BACKEND_ACCEPTANCE = PENDING_ASSIGNMENT_132 + POST_132_BROWSER_FORENSIC
SESSION_ISOLATION = REQUIRES_ARCHITECTURE_EVOLUTION
CAPABILITY_REGISTRY = PLANNED_POST_132
PROGRESSIVE_SKILLS = PLANNED_POST_132
DETERMINISTIC_HEAVY_PIPELINES = PLANNED_POST_132
FRONTEND_FINALIZATION = DEFERRED
FULL_BROWSER_E2E = NOT_STARTED
RELEASE_READY = NO
CURRENT_NEXT_ACTION = ASSIGNMENT_132_FULL_54_SKILL_TRUE_AB_CERTIFICATION
NEXT_ARCHITECTURE_GATE = POST_132_LEARNING_REVIEWER_AND_SESSION_ISOLATION
```

---

## 14. Definition of Done

The product is release-ready only when:

- every production skill is functionally certified against its real contract;
- every applicable skill passes the controlled learning-loop contract;
- REAL AS21/SWTR source contracts are grounded and fail closed;
- exact-key, sprint, multi-filter, attachment/history and team competency paths are proven where applicable;
- semantic correction preserves unaffected valid constraints and replaces corrected constraints without state corruption;
- UI and direct Harness use the same intended production semantics/source path;
- fresh UI sessions cannot inherit correction state from unrelated sessions;
- LLM-first semantic interpretation is observable and no hidden heuristic fallback silently replaces it;
- Learning Reviewer can autonomously source-recheck negative feedback and create only generalized, evidence-backed candidates;
- no entity/answer/count memorization occurs;
- learned policies survive restart and support rollback;
- human/governance boundaries remain intact where promotion requires them;
- Capability Registry explicitly declares source/oracle/availability contracts;
- latency is measured and avoidable orchestration overhead is reduced without replacing REAL source truth;
- frontend original product scope is restored/accepted;
- critical browser E2E is 100% GREEN;
- P0 defects = 0;
- unauthorized AS21 writes = 0;
- secret leakage = 0;
- final release-readiness gate = GREEN.

---

**Current next action:** let Assignment 132 finish without production changes. Inspect its full Git QA report. Then execute the dedicated browser/session/LLM/Learning forensic before any frontend remediation. Regardless of whether 132 is GREEN, preserve the post-132 architecture program: Learning Reviewer, Session Isolation, Capability Registry and Progressive Skill Disclosure.