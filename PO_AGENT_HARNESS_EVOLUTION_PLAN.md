# PO Agent Harness — Authoritative Evolution Plan

**Status:** ACTIVE / consolidated source of truth  
**Current branch:** `feat/core8-real-query-hardening-v2`  
**Last reviewed:** 2026-09-02  
**Current active gate:** Assignment 132 — full 54-skill TRUE A/B certification against REAL AS21 + Learning Loop regression  
**Next architecture phase:** post-132 Architecture Evolution — Learning Reviewer, Session Isolation, Capability Registry, Progressive Skills  
**Frontend status:** DEFERRED until backend + learning certification is genuinely GREEN; then mandatory full UI Data Wiring & Acceptance Certification  
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
23. **Every data-bearing UI element is part of the product contract.** A widget/table/card/chart cannot be accepted merely because it renders: its backend/capability/source lineage and displayed facts must be proven.
24. **No unexplained empty UI.** If REAL AS21 contains applicable data, the UI must show it. If data are legitimately absent, partial or unavailable, the UI must render the corresponding explicit state rather than an ambiguous empty block/zero.

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
+ Deterministic Capability Pipelines
        |
        v
Final backend recertification / Gate E closure
        |
        v
FULL UI DATA WIRING & ACCEPTANCE CERTIFICATION
screen/widget inventory + data lineage
+ REAL-data A/B + empty/error/partial states
        |
        v
UI remediation
        |
        v
Full browser E2E
        |
        v
Release hardening and release readiness
```

---

## 2. Current recovery baseline

The previous total-regression campaign exposed that some earlier GREEN reports were not sufficiently authoritative. The acceptance model has therefore been tightened to TRUE A/B. Focused recovery already proved live assignee routing, exact task-key propagation, independent approved-space grounding, long-title compatibility and correction/session fixes. Assignment 131 provided meaningful REAL AS21 A/B evidence for recovered assignee queries, but it did not execute the complete 54-skill catalog. Assignment 132 exists to close that gap.

---

## 3. Current active gate — Assignment 132

Assignment 132 is the first accepted candidate for a complete backend certification run under the strengthened anti-surrogate rules.

Required contents include clean runtime provenance, REAL AS21/MCP-SWTR health, focused sanity A/B, exact-task semantics, all 54 discovered production skills actually executed/classified, independent Oracle B where factual comparison is possible, exact key-set equality for task collections, dialogue/Russian-language regression, Learning Loop regression, source integrity/latency evidence, anti-surrogate audit and exact arithmetic across the matrix.

`FULL_54_SKILL_AB_CERTIFICATION_GREEN` is allowed only when all 54 unique production skills really execute/classify, no product defect is proven, required factual A/B comparisons are GREEN, no surrogate Oracle is used and the Learning Loop contract is GREEN or safely typed non-applicable.

---

## 4. Source and Oracle architecture contract

Agent A follows:

```text
User/UI -> Harness API -> semantic interpreter -> grounded frame
 -> skill/capability -> Task API -> MCP-SWTR -> REAL AS21
```

Oracle B must be independently constructed from authoritative REAL AS21 operations and must not reuse Harness output, the same capability calculation, local task DB, previous report counts or fixtures. For task collections the primary equality rule is `set(Agent_A.task_keys) == set(Oracle_B.task_keys)`.

Production task spaces are `WMB`, `STS`, `OLP`, `DMS`, `CRPV`. Local synchronization may exist for non-authoritative features, but acceptance of live answers must not depend on preloading AS21 tasks into a local DB.

---

## 5. Semantic interpretation contract

Production natural-language understanding remains **LLM-first**:

```text
LLM: infer intent + extract semantic slots + detect ambiguity
Deterministic grounding: resolve/validate entities and authoritative identifiers
Capability code: retrieve/filter/calculate deterministically
```

Legacy phrase heuristics must not silently become the production NLP path. Post-132 browser forensic must expose interpreter class, `llm_used`, raw semantic frame, grounded frame, resolved skill, capability args and final source route.

---

## 6. Learning Loop — current contract and required evolution

Current protected contract:

```text
negative feedback/correction
 -> fresh authoritative source recheck
 -> source-grounded correction
 -> generalized allow-listed policy candidate
 -> validation
 -> persistence/versioning
 -> reuse where applicable
 -> cold restart survival
 -> rollback
```

Learning must never memorize entity facts/answers/counts or mutate production Python/source truth. The current UX is still too passive when negative feedback only triggers recheck + clarification. Target behavior is a separate isolated **Learning Reviewer** that can compare the previous turn against independent REAL AS21, prove mismatch/no-mismatch, localize the first failing boundary, create a generalized candidate, sandbox/replay it, run independent A/B, and promote only through governance rules.

---

## 7. Post-132 Architecture Evolution — six major stages

### STAGE 1 — Session + LLM-path hardening — P0

- browser conversation, Harness session and long-term memory scope are explicitly separated;
- New Chat creates a fresh Harness session;
- QA sessions use unique isolated IDs;
- parallel browser/QA execution cannot cross-contaminate dialogue state;
- production LLM-first path is observable end-to-end.

### STAGE 2 — Learning Loop 2.0 / Learning Reviewer — P0

- isolated background review plane;
- immutable original-turn snapshot;
- independent REAL AS21 recheck;
- mismatch/no-mismatch and first-failing-boundary evidence;
- generalized repair candidate only;
- sandbox/replay + independent A/B before promotion;
- versioned/auditable promotion, persistence and rollback.

### STAGE 3 — Capability Registry — P0/P1

Each capability declares semantic requirements, authoritative source route, independent Oracle contract, required tools/availability, pagination, certification SHA and latency budget. Semantic code must not know MCP endpoint details; UI must not know AS21 routing.

### STAGE 4 — Progressive Skills + Deterministic Executors — P1

- expose only compact skill catalog first, load full contracts for selected candidates;
- reduce context cost and skill collisions;
- Team/Sprint/Velocity/Release and other heavy analytics use deterministic bounded pipelines instead of repeated LLM/tool ping-pong;
- isolated subagents are reserved for genuinely multi-domain analysis, not simple factual queries.

### STAGE 5 — Full backend recertification — P0

After architecture evolution, rerun the complete production catalog under TRUE A/B, including Learning Reviewer, session isolation, restart/rollback and latency regression. Freeze backend evidence only after this clean run is GREEN.

### STAGE 6 — Full UI Data Wiring & Acceptance Certification — P0 release gate

This is a **large independent product stage**, not cosmetic frontend polish. Current UI has multiple places where data are missing or ambiguous; every such element must be traced and certified.

#### 6A. Complete UI inventory

Enumerate every route/screen and every interactive/data-bearing element:

- cards/KPIs;
- tables and rows;
- charts/graphs;
- filters/selectors;
- task/sprint/team/release panels;
- evidence/trace views;
- feedback/Learning controls;
- buttons/actions/navigation;
- loading, empty, partial and error states.

No element is omitted because it "looks secondary".

#### 6B. UI Data-Lineage Matrix

For each data-bearing element record:

```text
UI element
 -> frontend component/hook
 -> API endpoint
 -> Harness capability/skill
 -> adapter/source route
 -> authoritative source
 -> expected data contract
 -> Oracle B method
```

This matrix must reveal dead endpoints, stale local-data dependencies, disconnected widgets, wrong filters, missing source routes and UI elements wired to placeholder/mock data.

#### 6C. REAL-data A/B per element

Where the element displays AS21 business facts, compare displayed normalized facts against an independent REAL AS21 Oracle. For task lists use exact task-key-set equality where applicable; for counts/aggregates compare both the underlying set and derived metric when feasible.

A rendered widget with `0` or an empty array is **not PASS** unless Oracle B proves that the authoritative result is genuinely empty.

#### 6D. State semantics certification

Every data-bearing element must distinguish at least:

```text
LOADING
REAL_EMPTY
PARTIAL_DATA
SOURCE_UNAVAILABLE
ERROR
SUCCESS_WITH_DATA
```

Where relevant also certify `NOT_FOUND`, permission/read-only failures and long-running source requests. `0` must never be used as a generic substitute for unknown/error/unavailable.

#### 6E. Interaction certification

Filters, selectors, pagination, drill-down, refresh, navigation, feedback controls and any user action must preserve intended session/context and produce the expected backend request. UI state must not silently retain stale filters or stale conversation state.

#### 6F. UI remediation and rerun

Defects are grouped by first failing boundary: frontend wiring, API contract, Harness capability, adapter/source route or state rendering. Fix one boundary at a time, run focused A/B, then rerun the complete UI matrix.

#### Stage 6 exit criterion

```text
100% inventory coverage
+ 100% data-lineage coverage
+ every data-bearing element classified
+ REAL-data A/B GREEN where applicable
+ zero unexplained empty/zero widgets
+ all loading/empty/partial/error/source-unavailable states explicit
+ all critical interactions GREEN
+ no mock/local-surrogate production truth
```

Only then proceed to final full browser E2E/release hardening.

---

## 8. UI / browser forensic immediately after Assignment 132

Before the broad Stage 6 UI audit, run a narrow browser forensic because current UI behavior has contradicted direct Harness behavior. It must prove fresh New Chat IDs, one clean Russian query with no inherited state, LLM semantic frame/`llm_used`, grounded frame, capability/route, parity with direct Harness + Oracle B, negative feedback flow and a second uncontaminated browser session.

This is an architecture diagnostic and happens before broad frontend remediation.

---

## 9. Performance / latency track

Profile LLM semantic latency, grounding, Task API, MCP-SWTR, REAL AS21, deterministic calculation and response synthesis separately. Optimize via progressive skill disclosure, deterministic pipelines, avoiding duplicate reads, contract-aware pagination and safe non-authoritative metadata caching. Never trade REAL-source truth for artificial speed.

---

## 10. Updated ordered next steps

| Step | Work | Exit condition |
|---|---|---|
| **132** | Full 54-skill TRUE A/B marathon + exact-task forensic + dialogue + Learning Loop | 54 skills actually classified; no surrogate GREEN |
| **133** | UI/session/LLM-path forensic on fresh browser sessions | Browser/direct Harness/Oracle parity; session contamination localized if present |
| **134** | Owner fixes for any 132/133 proven defects | Minimal evidence-backed fixes only |
| **135** | Focused post-fix TRUE A/B regression | All affected boundaries GREEN |
| **136** | Learning Reviewer architecture implementation | Negative feedback produces evidence-backed review/candidate flow |
| **137** | Session Isolation implementation | Browser/QA/transcript/memory scopes separated and concurrency-safe |
| **138** | Capability Registry v1 | Explicit skill/source/oracle/availability/certification contracts |
| **139** | Progressive Skill Disclosure + latency benchmark | Reduced context/latency with zero semantic regression |
| **140** | Deterministic heavy-capability pipelines | Team/Sprint/Release analytics use bounded source-backed executors |
| **141** | Final backend clean certification after architecture evolution | Full catalog TRUE A/B + Learning Loop GREEN |
| **142** | Freeze backend evidence, versions and release baseline | Gate E formally closed |
| **143** | Full UI inventory + screen/element acceptance map | 100% routes/screens/widgets/actions inventoried |
| **144** | UI Data-Lineage Matrix | Every data-bearing element mapped UI -> API -> capability -> REAL source -> Oracle |
| **145** | REAL-data A/B certification for all UI data elements | Zero unexplained empty/zero widgets; factual parity GREEN |
| **146** | UI state + interaction certification | Loading/empty/partial/error/source-unavailable + filters/actions GREEN |
| **147** | UI remediation by first failing boundary | Complete UI acceptance matrix GREEN |
| **148** | Clean rerun of full UI Data Wiring & Acceptance gate | Stage 6 formally GREEN |
| **149** | Full browser E2E including feedback/learning/session/restart/failure states | Critical E2E 100% GREEN |
| **150** | Release hardening: security/read-only/secrets/packaging/restart | Release candidate |
| **151** | Final release-readiness certification | `RELEASE_READY=YES` |

Assignment numbers after 132 are roadmap identifiers and may be subdivided by proven defect cluster. Do not skip architectural or UI certification work merely because an earlier gate is GREEN.

---

## 11. Decision rules

During Assignment 132 GigaCode changes no production code; all 54 skills must really execute/classify for FULL GREEN; factual PASS requires independent REAL AS21 evidence; Learning Loop must be tested through its supported runtime path; and defects require `FIRST_FAILING_BOUNDARY` before repair.

After Assignment 132, even if GREEN, do not jump directly to UI remediation. First run the narrow browser/session/LLM forensic, complete architecture evolution and backend recertification, then execute the full UI acceptance stage.

During UI acceptance, a missing/zero value is treated as **UNPROVEN**, not PASS, until its lineage and Oracle truth are established. Do not fix presentation code to hide a backend/source defect.

---

## 12. Work ownership

### ChatGPT/OpenAI side

Architecture and production changes, source/learning decisions, QA assignment design, roadmap updates, diagnosis/fixes and acceptance/release decisions.

### GigaCode side

QA/tester only: pull/restart as instructed, use REAL read-only sources, execute assignments, collect traces/evidence, never weaken tests, never modify production implementation, and commit/push only explicitly allowed QA artifacts.

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
GATE_E_BACKEND_ACCEPTANCE = PENDING_132 + ARCHITECTURE_EVOLUTION + FINAL_RECERTIFICATION
SESSION_ISOLATION = REQUIRES_ARCHITECTURE_EVOLUTION
CAPABILITY_REGISTRY = PLANNED_POST_132
PROGRESSIVE_SKILLS = PLANNED_POST_132
DETERMINISTIC_HEAVY_PIPELINES = PLANNED_POST_132
GATE_F_UI_DATA_WIRING_ACCEPTANCE = PLANNED / MANDATORY_RELEASE_GATE
UI_UNEXPLAINED_EMPTY_VALUES = NOT_ACCEPTABLE
FULL_BROWSER_E2E = NOT_STARTED
RELEASE_READY = NO
CURRENT_NEXT_ACTION = ASSIGNMENT_132_FULL_54_SKILL_TRUE_AB_CERTIFICATION
NEXT_ARCHITECTURE_GATE = POST_132_SESSION_LLM_FORENSIC
```

---

## 14. Definition of Done

The product is release-ready only when:

- every production skill is functionally certified against its real contract;
- every applicable skill passes the controlled Learning Loop contract;
- REAL AS21/SWTR source contracts are grounded and fail closed;
- exact-key, sprint, multi-filter, attachment/history and team competency paths are proven where applicable;
- UI and direct Harness use the same intended production semantics/source path;
- fresh UI sessions cannot inherit unrelated correction state;
- LLM-first semantic interpretation is observable with no silent heuristic replacement;
- Learning Reviewer autonomously source-rechecks feedback and creates only generalized evidence-backed candidates;
- no entity/answer/count memorization occurs and learned policies support persistence/restart/rollback;
- Capability Registry declares source/oracle/availability contracts;
- latency is measured and avoidable orchestration overhead reduced without replacing REAL truth;
- **every UI route/screen/widget/action is inventoried and classified;**
- **every data-bearing UI element has a documented data lineage to its authoritative source;**
- **REAL-data UI facts match independent Oracle B where applicable;**
- **there are zero unexplained empty/zero data widgets;**
- **REAL_EMPTY, PARTIAL_DATA, SOURCE_UNAVAILABLE and ERROR are visibly distinguishable;**
- **filters, selectors, pagination, drill-down, refresh, navigation and feedback controls work against the intended backend contract;**
- complete UI acceptance matrix is GREEN;
- critical browser E2E is 100% GREEN;
- P0 defects = 0;
- unauthorized AS21 writes = 0;
- secret leakage = 0;
- final release-readiness gate = GREEN.

---

**Current next action:** let Assignment 132 finish without production changes. Inspect its full Git QA report. Then execute the dedicated browser/session/LLM/Learning forensic. After architecture evolution and final backend recertification, run the mandatory Full UI Data Wiring & Acceptance Certification before browser E2E and release hardening.