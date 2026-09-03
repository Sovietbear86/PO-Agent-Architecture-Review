# PO Agent — Authoritative Evolution Plan

**Status:** ACTIVE / architecture cutover approved  
**Current branch:** `feat/core8-real-query-hardening-v2`  
**Last reviewed:** 2026-09-03  
**Current baseline:** Assignment 142 GREEN for recovered live assignee/source transformation path, but real UI still contradicts backend behavior  
**Architecture decision:** stop broad point-fixing of the legacy orchestration layer; preserve proven REAL AS21/source components and replace the upper Harness orchestration incrementally with a Hermes-inspired Agent Core  
**Frontend status:** UI is part of acceptance truth; Harness-only GREEN is insufficient  
**Purpose:** evolve PO Agent into a source-grounded, session-safe, contract-driven, self-improving agent without throwing away the proven AS21 integration work.

> Historical QA GREEN is evidence, not product acceptance. A live browser counterexample reopens the affected gate. GigaCode remains QA-only. Production architecture and code changes are owner work.

---

## 0. Non-negotiable principles

1. REAL AS21/SWTR is authoritative for business facts.
2. Fixtures, local task DB, sync snapshots, fake/mock/frozen data and historical counts are never acceptance truth for live answers.
3. Natural-language understanding remains LLM-first; deterministic code grounds entities, retrieves source data, applies filters and calculates metrics.
4. Requested constraints are **immutable after semantic acceptance**. A constraint such as `space=WMB` may be canonicalized, but must never silently disappear before execution.
5. Every factual result must satisfy postconditions before it is released to the user. Example: a WMB query may not return DMS tasks.
6. Exact task-key-set equality against independent REAL AS21 Oracle B outranks counts/prose.
7. Browser/UI is an independent acceptance path C. Harness/API cannot impersonate UI.
8. New UI conversations, QA sessions and long-term memory scopes must be isolated.
9. Learning generalizes procedure/policy; it never memorizes task IDs, people-specific counts or source answers as truth.
10. Runtime learning cannot rewrite Python, source data or silently mutate capability contracts.
11. Ambiguity fails closed; source unavailability is never represented as a legitimate empty result.
12. GigaCode is QA/adversarial reviewer only and does not change production code.
13. Preserve proven lower-layer components instead of full rewrite.
14. Migrate by strangler pattern: new Agent Core runs alongside legacy Harness until capability families are certified and switched over.
15. A/B/C certification is required for every migrated capability family before legacy routing is retired.

---

## 1. Architecture decision — 2026-09-03

Assignment 142 proved that the lower live assignee/source path can return fresh Oracle-parity data. Immediately afterward real browser tests still produced semantically wrong behavior: one simple assignee query requested clarification, while a WMB-filtered query displayed DMS tasks. Therefore the dominant remaining risk is no longer just MCP/source integration; it is orchestration-state and constraint propagation across the current Harness stack.

Decision:

```text
DO NOT rewrite everything from zero.
DO preserve the proven source/data plane.
DO replace the upper orchestration plane incrementally.
DO start Hermes-inspired Architecture Evolution now.
```

### Preserve

```text
REAL AS21
MCP-SWTR transport
Task API live read facades
canonical source normalization
point-read + NOT_FOUND semantics
server-side assignee TQL route
source evidence primitives
deterministic business calculations that pass certification
```

### Replace / evolve

```text
session/runtime ownership
semantic-state propagation
constraint handling
skill/capability resolution
result/postcondition validation
Learning Loop orchestration
progressive skill loading
heavy multi-step orchestration
```

Target is an incremental ~40/60 preserve/evolve split, not a greenfield rewrite.

---

## 2. Target Hermes-inspired architecture

```text
Browser / API / other channels
          |
          v
+--------------------------+
| Session Manager          |
| conversation_id          |
| runtime_session_id       |
| memory_scope_id          |
+------------+-------------+
             |
             v
+--------------------------+
| LLM Semantic Interpreter |
| intent + raw constraints |
+------------+-------------+
             |
             v
+--------------------------+
| Grounding Layer          |
| canonical source IDs     |
+------------+-------------+
             |
             v
+--------------------------+
| Immutable Turn Contract  |
| intent                   |
| constraints              |
| required postconditions  |
+------------+-------------+
             |
             v
+--------------------------+
| Capability Registry      |
| requirements/source/     |
| oracle/availability      |
+------------+-------------+
             |
             v
+--------------------------+
| Deterministic Executor   |
+------------+-------------+
             |
             v
+--------------------------+
| REAL Source Plane        |
| Task API -> MCP -> AS21  |
+------------+-------------+
             |
             v
+--------------------------+
| Result Validator         |
| postconditions/evidence  |
+------------+-------------+
             |
             v
+--------------------------+
| Response Synthesizer     |
+--------------------------+
```

Separate learning plane:

```text
User feedback
    |
    v
Learning Reviewer
    |
    +--> immutable previous-turn snapshot
    +--> independent REAL AS21 recheck
    +--> mismatch proof / first failing boundary
    +--> generalized policy/skill candidate
    +--> sandbox/replay + independent A/B
    +--> approve/promote or reject
```

---

## 3. Core invariant: Immutable Turn Contract

After interpretation + grounding the runtime creates exactly one accepted contract:

```yaml
turn_id: <uuid>
intent: task_search
constraints:
  assignee: Kalachanov.V.V
  space: WMB
requested_constraints:
  - assignee
  - space
postconditions:
  - every_task.assignee == Kalachanov.V.V
  - every_task.space == WMB
source_authority: REAL_AS21
```

Rules:
- downstream components may enrich metadata but cannot delete requested constraints;
- capability selection must declare that it supports all required constraints;
- unsupported constraint -> typed clarification/unsupported result before source execution;
- source result violating a postcondition -> fail closed and never show contradictory data in UI;
- trace contains the same contract from semantic acceptance through response validation.

This invariant is specifically intended to make the observed `WMB query -> DMS evidence` impossible.

---

## 4. Architecture Evolution stages

### STAGE H1 — New Agent Core + Session/Constraint Contract — P0

Create additive `agent_core_v3` foundations alongside legacy Harness.

Deliverables:
- explicit `conversation_id`, `runtime_session_id`, `memory_scope_id`;
- immutable accepted turn contract;
- requested-constraint preservation audit;
- postcondition validation before response;
- full trace from raw frame -> grounded values -> contract -> capability -> result validation;
- no correction state inherited by a fresh conversation;
- feature flag / routing seam so legacy and v3 can coexist.

Pilot scenarios:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи задачу DMS-380`
5. `Открытые задачи <человек> в <space>`

Exit: all pilot scenarios A/B/C GREEN and requested constraints survive end-to-end.

### STAGE H2 — Capability Registry v1 — P0

Replace implicit skill/capability assumptions with explicit contracts.

Each capability declares:

```yaml
id: task-search
version: ...
required_slots: []
optional_slots: [assignee, space, status, sprint, release]
supported_constraints: [...]
source_authority: REAL_AS21
production_route: ...
oracle_contract: ...
availability_requirements: ...
postconditions: ...
latency_budget: ...
last_certification_sha: ...
```

Exit: pilot families are routed only through Registry; no silent fallback to another internal label.

### STAGE H3 — Progressive Skills + Deterministic Executors — P1

Hermes-inspired procedural skills become thin contracts/procedures over a small number of deterministic executors.

Goals:
- model initially sees compact skill metadata only;
- full skill instructions are loaded only for selected candidates;
- reduce context size and skill collisions;
- task/sprint/team/release families reuse deterministic executors;
- simple factual queries remain one semantic decision + one capability execution, no agent-of-agents chain;
- isolated subagents only for genuinely multi-domain analysis.

Exit: migrated skill families show zero semantic regression and improved latency/context footprint.

### STAGE H4 — Learning Reviewer 2.0 — P0

Move learning out of the main dialogue path.

Required flow:

```text
answer -> feedback
 -> independent reviewer
 -> source recheck
 -> prove mismatch/no mismatch
 -> locate boundary
 -> generalized candidate
 -> sandbox/replay
 -> independent A/B
 -> promote/reject
```

Learning must not require the user to diagnose the bug. If the source proves a mismatch, reviewer should identify it. If no mismatch is provable, ask a targeted clarification and learn nothing.

Exit: feedback scenarios demonstrate generalized learning, persistence where supported, rollback and zero entity-fact memorization.

### STAGE H5 — Family-by-family strangler migration — P0/P1

Migration order:
1. exact-task + task search/assignee/product/status;
2. sprint/current-sprint factual skills supported by live source;
3. team/competency;
4. release factual skills supported by live source;
5. portfolio/PO aggregations;
6. history-dependent skills only where authoritative historical source contracts exist.

A family switches from legacy to v3 only after focused A/B/C GREEN.

### STAGE H6 — Full backend + browser recertification — P0

After migration, discover the full production catalog and certify every real user-facing skill.

For every applicable factual scenario:
- A = new Agent Core;
- B = independent REAL AS21 Oracle;
- C = real browser/UI;
- compare normalized facts and exact key sets;
- no surrogate C through Harness API.

Long runs are checkpointed; timeout never permits skipping a case.

### STAGE H7 — Full UI Data Wiring & Acceptance — P0 release gate

Large independent UI stage after architecture migration. Inventory every route/widget/action and map:

```text
UI element -> frontend -> API -> Agent Core capability -> source -> Oracle
```

Required UI states:
`LOADING`, `REAL_EMPTY`, `PARTIAL_DATA`, `SOURCE_UNAVAILABLE`, `ERROR`, `SUCCESS_WITH_DATA`, and where relevant `NOT_FOUND`.

Exit:
- 100% screen/widget/action inventory;
- 100% data lineage;
- zero unexplained empty/zero widgets;
- real-data A/B/C parity;
- all filters/pagination/drill-down/refresh/feedback/session behaviors GREEN.

### STAGE H8 — Release hardening

Security/read-only guarantee, secrets, packaging, restart/recovery, latency and release-readiness certification.

---

## 5. Source and Oracle contract

Production factual path after migration:

```text
UI -> Agent Core v3 -> Capability Registry -> deterministic executor
 -> Task API -> MCP-SWTR -> REAL AS21
```

Oracle B is independently built from direct authoritative source operations and cannot reuse Agent output or the same capability calculation.

Production task spaces remain `WMB`, `STS`, `OLP`, `DMS`, `CRPV`.

For task collections:

```text
set(A.task_keys) == set(B.task_keys)
set(C.task_keys) == set(B.task_keys)
set(A.task_keys) == set(C.task_keys)
```

Counts alone are insufficient.

---

## 6. What we still point-fix in legacy code

While migration is underway, legacy point-fixes are allowed only for P0 lower-layer defects that would also affect v3:

- MCP schema/transport compatibility;
- canonical source parsing/mapping;
- pagination;
- point-read/NOT_FOUND/source-error semantics;
- authoritative source routes;
- proven deterministic calculation defect shared with v3.

Do **not** spend cycles broadly patching legacy:

- phrase/intent heuristics;
- multiple overlapping semantic recovery layers;
- correction-state orchestration;
- skill-label routing inconsistencies;
- learning behavior that will be replaced by Learning Reviewer;
- UI-specific workarounds hiding broken constraint propagation.

---

## 7. Session contract

Three identities are explicit and independent:

```text
conversation_id     # one visible chat/conversation
runtime_session_id  # transient dialogue state
memory_scope_id     # durable reusable learning scope
```

Rules:
- New Chat => new conversation_id + runtime_session_id;
- QA case => unique runtime_session_id per case;
- browser and QA never share transient state;
- memory_scope does not imply previous-turn correction state;
- concurrent sessions are isolated;
- parent/fork lineage is explicit if introduced later.

---

## 8. Learning contract

Learning artifacts are procedural policy/skill versions, never source facts.

Allowed candidate example:

```text
For assignee collection queries, preserve every explicit source-space constraint
through capability arguments and validate every returned row against it.
```

Forbidden learned artifact:

```text
Kalachanov has 2823 tasks.
Garanin has 16 tasks.
DMS-380 belongs to Garanin.
```

Promotion requires authoritative recheck, reproducible mismatch, independent validation and rollback metadata.

---

## 9. Performance track

Measure separately:
- semantic interpretation;
- grounding;
- capability resolution;
- Task API;
- MCP-SWTR/AS21;
- deterministic calculation;
- response synthesis.

Optimize by progressive disclosure, one-shot deterministic executors, avoiding duplicate source reads and safe metadata caching. Never trade authoritative truth for speed.

---

## 10. Updated ordered roadmap

| Assignment/Stage | Work | Exit condition |
|---|---|---|
| **142** | Last focused legacy source/assignee certification | Source/data plane recovery evidence captured; legacy orchestration not declared product-GREEN |
| **143 / H1A** | Agent Core v3 architecture + immutable turn/session contracts | Additive architecture foundation committed; legacy path untouched by default |
| **144 / H1B** | Wire 5 pilot scenarios behind v3 feature flag | Same browser/API path can execute pilots through v3 |
| **145 / H1C** | Pilot A/B/C certification | All 5 pilots exact/semantic parity GREEN; WMB can never return DMS |
| **146 / H2** | Capability Registry v1 | Pilot capabilities use explicit source/oracle/constraint/postcondition contracts |
| **147 / H3A** | Progressive skill disclosure | Compact routing context; selected skill contracts loaded lazily |
| **148 / H3B** | Deterministic executor consolidation | Task family first; then sprint/team/release |
| **149 / H4A** | Learning Reviewer implementation | Isolated reviewer + source recheck + mismatch proof |
| **150 / H4B** | Learning governance | candidate validation, persistence/versioning, rollback |
| **151 / H5** | Family-by-family strangler migration | Legacy routing retired only per certified family |
| **152 / H6** | Full no-skip A/B/C catalog certification | Every production user-facing skill terminally classified; no surrogate C |
| **153 / H7A** | Full UI inventory/data-lineage matrix | 100% screens/widgets/actions mapped |
| **154 / H7B** | UI REAL-data/state/interaction certification + remediation | Zero unexplained empty/wrong widgets; complete matrix GREEN |
| **155** | Full browser E2E incl. session/feedback/restart/failure | Critical E2E 100% GREEN |
| **156 / H8** | Release hardening | Release candidate |
| **157** | Final release readiness | `RELEASE_READY=YES` |

Assignment numbers may split when a proven defect requires focused certification, but stages cannot be skipped.

---

## 11. Immediate next action

**Start Stage H1 now.**

Owner work:
1. create the v3 architecture module/contracts alongside legacy runtime;
2. create explicit immutable Turn Contract and session identities;
3. create result postcondition validator;
4. introduce a disabled-by-default v3 routing seam/feature flag;
5. document pilot migration behavior.

GigaCode remains idle/QA-only until the owner Stage H1A commit is ready. It then certifies architecture invariants before H1B wiring.

---

## 12. Current gate values

```text
SOURCE_DATA_PLANE = RECOVERED_FOCUSED_GREEN
LEGACY_HARNESS_PRODUCT_ACCEPTANCE = REOPENED_BY_REAL_UI_COUNTEREXAMPLES
ARCHITECTURE_CUTOVER_DECISION = APPROVED
NEW_AGENT_CORE_V3 = STARTING_H1
SESSION_ISOLATION = H1_REQUIRED
IMMUTABLE_CONSTRAINT_CONTRACT = H1_REQUIRED
POSTCONDITION_VALIDATION = H1_REQUIRED
CAPABILITY_REGISTRY = H2_PLANNED
PROGRESSIVE_SKILLS = H3_PLANNED
LEARNING_REVIEWER = H4_PLANNED
STRANGLER_MIGRATION = H5_PLANNED
FULL_ABC_RECERTIFICATION = H6_PLANNED
UI_DATA_WIRING_ACCEPTANCE = H7_MANDATORY_RELEASE_GATE
RELEASE_READY = NO
CURRENT_NEXT_ACTION = OWNER_STAGE_H1A_AGENT_CORE_V3_FOUNDATION
```

---

## 13. Definition of Done

Release-ready requires:

- REAL AS21/source contracts fail closed and remain read-only;
- all requested semantic constraints survive to execution or trigger typed clarification;
- postcondition validator blocks contradictory result rows;
- UI/API share the intended Agent Core semantics;
- browser/QA/session/memory scopes are isolated;
- LLM-first interpretation is observable without heuristic replacement;
- capability contracts declare supported constraints, source, Oracle, availability and postconditions;
- Learning Reviewer autonomously rechecks feedback and learns only generalized evidence-backed procedure;
- all production user-facing skills pass no-skip A/B/C certification;
- every UI data element has authoritative lineage and explicit state semantics;
- zero unexplained empty/zero/wrong-space widgets;
- full browser E2E GREEN;
- P0 defects = 0;
- unauthorized AS21 writes = 0;
- secret leakage = 0;
- final release-readiness gate GREEN.
