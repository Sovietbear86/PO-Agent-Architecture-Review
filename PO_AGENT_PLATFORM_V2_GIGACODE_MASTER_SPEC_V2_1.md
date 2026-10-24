# PO Agent Platform v2.1
## GIGACODE CLI + QWEN CODER 3.7 MASTER SPECIFICATION
### Harness Architecture + AI PDLC + Memory + Evaluation + Controlled Self-Improvement

**Purpose:** build a new PO Agent Platform v2.1 as a separate application next to the existing legacy project, preserving the old application as a working reference and source of proven implementations.

**Primary implementation environment:** GigaCode CLI  
**Primary coding model:** Qwen Coder 3.7  
**Development strategy:** greenfield shell + selective reuse from legacy project  
**Migration strategy:** side-by-side / strangler, NOT in-place refactoring  
**Target architecture:** harness-based PO assistant with deterministic domain capabilities, structured memory, evaluation, versioning, shadow mode and controlled AI-PDLC improvement loop  
**Important:** the old application must remain untouched unless the owner explicitly asks otherwise.

---

# 0. CORE OPERATING MODE FOR GIGACODE

This specification is written specifically for a coding model that may be less reliable than frontier models.

Therefore GigaCode/Qwen MUST follow these rules:

1. Never implement the whole project in one pass.
2. Work one numbered stage at a time.
3. Before modifying files, inspect only files needed for the current stage.
4. First produce a short implementation plan.
5. Then implement only the current stage.
6. Run tests after each meaningful sub-step.
7. If tests fail, fix them before continuing.
8. Never silently widen scope.
9. Never rewrite working legacy components merely for style.
10. Never invent AS21 fields, API methods, statuses, routes or schemas.
11. If an external contract is unknown, create an interface and fixture, not a guessed implementation.
12. Prefer deterministic Python code over LLM reasoning wherever possible.
13. LLM must interpret and explain; code must retrieve and calculate.
14. Every stage must end with an explicit report.
15. Do not start the next stage until the owner says:
   `Продолжай`
   or
   `Следующий этап`.
16. If a stage uncovers unrelated technical debt, record it and continue unless blocked.
17. Do not claim a test passed unless it was actually executed.
18. Do not claim AS21 integration works unless it was actually tested.
19. Do not copy credentials, sessions, tokens or personal data from the legacy project into the new project.
20. Do not introduce autonomous self-modification of production code.

---

# 1. DIRECTORY STRATEGY

The existing application is the legacy/reference project.

Create a NEW sibling application.

Recommended structure:

```text
<workspace>/
├── legacy-po-agent/              # existing project, DO NOT MODIFY
│   └── ...
│
└── po-agent-platform-v2/         # NEW project
    ├── README.md
    ├── pyproject.toml
    ├── .env.example
    ├── .gitignore
    ├── docs/
    ├── config/
    ├── src/
    ├── tests/
    ├── scripts/
    ├── data/
    └── frontend/
```

If the existing project already has another folder name, keep it.

The new project MUST NOT require moving or renaming the legacy application.

---

# 2. PRODUCT GOAL

PO Agent Platform v2.1 is a harness-based assistant for a product owner.

It must eventually support:

- intelligent task search in AS21/SWTR;
- task search by text;
- task search by attachment type;
- Excel/PDF/MSG attachment detection;
- task summarization;
- task completeness/quality analysis;
- sprint health;
- velocity;
- throughput;
- WIP;
- cycle time;
- lead time;
- carryover;
- blocked/aging tasks;
- workload distribution;
- team capacity;
- competency matching;
- release scope;
- release risk;
- release forecast;
- product/team/workflow knowledge;
- controlled notifications/actions;
- PO Workspace UI;
- execution history;
- conversation/session memory;
- feedback capture;
- evaluation datasets;
- eval runner;
- failure mining;
- curated experience memory;
- prompt/version registry;
- shadow-mode comparison;
- controlled improvement proposals;
- regression gates;
- human approval before promotion.

The system must be designed so that new capabilities can be added without turning one agent into a giant monolith.

---

# 3. HARNESS PRINCIPLE

The final system is NOT a single all-powerful prompt.

The system is a harness composed of:

```text
user request
    |
    v
PO Orchestrator
    |
    +--> detдпerministic router
    +--> optional LLM intent fallback
    +--> capability plan
    +--> capability calls
    +--> evidence aggregation
    +--> optional response synthesis
    |
    v
Trace Recorder
    |
    +--> Execution History
    +--> Feedback
    +--> Eval Dataset
    +--> Failure Analysis
    +--> Candidate Improvements
    +--> Shadow Evaluation
    +--> Regression Gate
    +--> Human Approval
    +--> Version Promotion/Rollback
```

The key architectural goal is:

**deterministic core + bounded LLM + observable execution + controlled learning loop**

---

# 4. LEGACY APPLICATION: WHAT TO REUSE

The existing project is a reference source, not something to copy wholesale.

Reuse selectively.

## 4.1 AS21/SWTR integration
Inspect the legacy project for components such as:

- `swtr_client.py`
- `s21_mcp_proxy.py`
- `swtr_sync_service.py`
- `s21_swtr_adapter.py`
- MCP-related SWTR tools
- sync CLI utilities
- AS21 task parsing logic

Determine:
- actual transport code;
- mapping/parsing code;
- proxy/agent glue;
- obsolete workaround code.

Reuse only proven transport/parsing logic behind the NEW v2 adapter.

## 4.2 Team-performance formulas
Inspect existing `s21_team_performance`.

Preserve validated deterministic formulas and logic, including where relevant:

- velocity;
- predictability;
- scope change;
- sprint health;
- flow metrics;
- workload calculations;
- bottleneck logic;
- forecasting;
- release linkage.

Extract formulas into the new deterministic metrics layer.

## 4.3 Task intelligence
Reuse proven behavior for:
- task search;
- attachment detection;
- summarization;
- completeness analysis.

Separate retrieval from LLM explanation.

## 4.4 Team/workflow configuration
Existing files describing:
- team members;
- roles;
- logins;
- competencies;
- task status scheme

may be reused as references.

Convert them into clean machine-readable configuration for v2.

---

# 5. WHAT MUST NOT BE COPIED AS ARCHITECTURE

Do NOT reproduce these legacy problems:

- multiple overlapping AS21 access paths;
- adapter calling back into agent endpoint;
- multiple MCP servers doing overlapping jobs;
- hardcoded ports scattered across classes;
- business logic hidden inside prompts;
- metrics calculated by LLM;
- one agent class handling routing + retrieval + calculation + response generation;
- employee names hardcoded in routing;
- raw AS21 dictionaries passed through all layers;
- UI coupled to internal agent implementation;
- LLM failure causing simple deterministic queries to fail;
- unbounded context accumulation;
- direct promotion of unvalidated learned behavior into production.

---

# 6. TARGET ARCHITECTURE

```text
                           PO Workspace
                                |
                                v
                         PO Orchestrator
                                |
             +------------------+------------------+
             |                  |                  |
             v                  v                  v
      Task Intelligence  Sprint Intelligence  Team Intelligence
             |                  |                  |
             +------------------+------------------+
                                |
                          Release Intelligence
                                |
                                v
                         Shared Services
             +------------------+------------------+
             |                  |                  |
             v                  v                  v
        AS21 Adapter       Metrics Engine     Knowledge Layer
             |
             v
          AS21/SWTR
```

AI PDLC / learning loop:

```text
Runtime Execution
      |
      v
Trace Recorder
      |
      +--> Session Memory
      +--> Execution History
      +--> User Feedback
      |
      v
Eval Store
      |
      v
Failure Miner
      |
      v
Improvement Candidate Generator
      |
      +--> prompt candidate
      +--> routing-rule candidate
      +--> knowledge candidate
      +--> test candidate
      +--> capability candidate
      |
      v
Shadow / Offline Evaluation
      |
      v
Regression Gate
      |
      v
Human Approval
      |
      v
Version Registry
      |
      +--> Promote
      +--> Rollback
```

Do not create microservices for every box.

Start as a modular monolith.

---

# 7. THREE LEVELS OF MEMORY

The system MUST distinguish three types of memory.

## 7.1 Session Memory
Short-lived state for current conversation/session.

Examples:
- selected sprint;
- current product;
- previous clarification;
- active task reference;
- unresolved question.

Session Memory must not become permanent automatically.

## 7.2 Operational History
Append-only execution history.

Store:
- request;
- timestamp;
- user/session id or anonymized reference;
- intent;
- entities;
- plan;
- capability calls;
- evidence;
- metrics;
- adapter calls;
- LLM used or not;
- prompt version;
- model version;
- capability version;
- latency;
- warnings;
- errors;
- final response metadata;
- feedback.

Operational History is NOT directly injected wholesale into prompts.

## 7.3 Curated Memory
Approved reusable knowledge derived from repeated experience.

Examples:
- confirmed terminology;
- user/product conventions;
- routing exceptions;
- validated operational patterns;
- known aliases;
- accepted clarification rules.

Curated Memory must require:
1. evidence;
2. evaluation;
3. approval or policy gate;
4. versioning.

Never promote arbitrary chat text directly into Curated Memory.

---

# 8. AI PDLC PRINCIPLE

"Self-learning" means controlled improvement, NOT automatic model retraining or uncontrolled self-modification.

The loop is:

```text
RUN
 -> TRACE
 -> HISTORY
 -> FEEDBACK
 -> EVALUATE
 -> FAILURE ANALYSIS
 -> GENERATE CANDIDATE IMPROVEMENT
 -> SHADOW/OFFLINE TEST
 -> REGRESSION TEST
 -> HUMAN APPROVAL
 -> PROMOTE
 -> OBSERVE
 -> ROLLBACK IF NEEDED
```

The system must never rewrite production prompts/config/code based on one failed example without evaluation.

---

# 9. VERSIONING REQUIREMENT

Version these independently where practical:

- `agent_version`
- `router_version`
- `prompt_version`
- `knowledge_version`
- `capability_version`
- `metrics_version`
- `workflow_version`
- `model_version`
- `config_version`

Trace records should capture active versions.

This enables reproducibility:

"What changed between yesterday's correct answer and today's wrong answer?"

---

# 10. SHADOW MODE

The architecture MUST support a future shadow mode.

A candidate version may process the same request without serving its result to the user.

Store:

```text
production result
candidate result
versions
expected result if known
user feedback if available
evaluation scores
```

Candidate must not be promoted until regression gate passes.

---

# 11. TECH STACK FOR V2

Unless a compelling repository constraint is discovered:

## Backend
- Python 3.11+
- FastAPI
- Pydantic v2
- httpx
- pytest
- pytest-asyncio

## Storage
Start simple.

Preferred initial local/dev options:
- SQLite for operational history/evals/version metadata;
- YAML/JSON for static config;
- filesystem Markdown for human-readable knowledge.

Do NOT add PostgreSQL/vector DB/event broker before required.

Storage interfaces must allow future replacement.

## Frontend
Later:
- React
- TypeScript
- Vite

## LLM
Use a provider-neutral OpenAI-compatible abstraction.

Model identity must be config, not domain code.

---

# 12. PROPOSED NEW PROJECT STRUCTURE

Target shape:

```text
po-agent-platform-v2/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── config/
│   ├── products.yaml
│   ├── team.example.yaml
│   ├── workflow.yaml
│   └── quality_rules.yaml
│
├── data/
│   └── .gitkeep
│
├── docs/
│   ├── architecture/
│   ├── adr/
│   ├── metrics/
│   ├── ai_pdlc/
│   └── runbooks/
│
├── src/
│   └── po_agent/
│       ├── api/
│       ├── config/
│       ├── domain/
│       ├── contracts/
│       ├── adapters/
│       ├── workflow/
│       ├── metrics/
│       ├── capabilities/
│       ├── orchestration/
│       ├── llm/
│       ├── knowledge/
│       ├── memory/
│       ├── history/
│       ├── feedback/
│       ├── evaluation/
│       ├── improvement/
│       ├── versions/
│       └── observability/
│
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── golden/
│   ├── integration/
│   ├── regression/
│   └── fixtures/
│
├── scripts/
│   ├── inspect_legacy.py
│   ├── validate_config.py
│   ├── run_eval.py
│   ├── compare_versions.py
│   └── run_dev.py
│
└── frontend/
```

Do not create all files immediately.

Each stage below specifies what to add.

---

# 13. COMMON CONTRACTS

Every capability should converge toward:

```python
class CapabilityRequest(BaseModel):
    query: str
    session_id: str | None = None
    context: dict = {}

class Evidence(BaseModel):
    source_type: str
    source_id: str | None = None
    fact: str
    value: object | None = None

class CapabilityResult(BaseModel):
    capability: str
    status: str
    data: dict
    evidence: list[Evidence]
    warnings: list[str] = []
```

Qwen may refine exact fields.

Do not overgeneralize too early.

---

# 14. ERROR MODEL

Recommended categories:

```text
ConfigurationError
AuthenticationError
AdapterUnavailableError
AdapterTimeoutError
NotFoundError
InvalidExternalDataError
ContractViolationError
CapabilityExecutionError
LLMUnavailableError
EvaluationError
VersionPromotionError
MemoryPolicyError
```

User-facing API errors must not expose stack traces or secrets.

---

# 15. SOURCE-OF-TRUTH POLICY

### YAML/JSON
For:
- team;
- competencies;
- product aliases;
- workflow statuses;
- thresholds;
- capability config.

### Python
For:
- calculations;
- routing;
- validation;
- adapters;
- business logic;
- eval algorithms.

### Markdown
For:
- system instructions;
- metric explanations;
- product knowledge;
- runbooks;
- developer instructions.

### SQLite / storage interface
For:
- operational history;
- feedback;
- eval cases;
- version metadata;
- shadow comparisons.

---

# 16. MODEL USAGE RULES

## LLM MAY
- classify ambiguous intent;
- summarize task descriptions;
- explain metrics;
- synthesize recommendations;
- identify missing natural-language clarity;
- propose improvement candidates;
- cluster failure examples;
- generate candidate golden tests for review.

## LLM MUST NOT
- calculate metrics;
- invent AS21 facts;
- invent employees/statuses/releases;
- directly mutate external systems;
- promote its own improvement candidate;
- overwrite Curated Memory without gate;
- rewrite production code automatically.

For simple queries, avoid LLM.

---

# 17. DEVELOPMENT STAGES

==================================================
# STEP 01 — CREATE NEW APPLICATION SKELETON
==================================================

Goal:
Create `po-agent-platform-v2` next to legacy.

Implement:
- package;
- FastAPI;
- `/health`;
- `/version`;
- settings;
- logging;
- correlation ID;
- base errors;
- README;
- `.env.example`;
- `.gitignore`;
- tests.

Do NOT:
- connect AS21;
- add agents;
- metrics;
- memory;
- orchestrator.

Exit:
tests green.

STOP.

==================================================
# STEP 02 — LEGACY DISCOVERY TOOL
==================================================

Create:
- `scripts/inspect_legacy.py`
- `docs/architecture/LEGACY_REUSE_MAP.md`

Classify:
- AS21 transport;
- mapping;
- MCP;
- task intelligence;
- metrics;
- workflow config;
- team config;
- LLM client;
- API routes;
- frontend API client.

For each:
```text
path
responsibility
reuse YES/PARTIAL/NO
target module
risks
```

No legacy modification.

STOP.

==================================================
# STEP 03 — CANONICAL DOMAIN MODELS
==================================================

Implement:
- Task
- Attachment
- StatusTransition
- Sprint
- Release
- TeamMember
- Competency
- Dependency
- common identifiers/timestamps

Transport-independent.

Tests.

STOP.

==================================================
# STEP 04 — WORKFLOW CONFIGURATION
==================================================

Create:
`config/workflow.yaml`

Use actual known statuses from legacy.

Implement:
- normalize_status
- is_terminal
- is_active
- is_waiting
- is_blocked

Tests.

STOP.

==================================================
# STEP 05 — READ-ONLY AS21 ADAPTER CONTRACT
==================================================

Create interface + fake adapter + fixtures.

Operations:
- get_task
- search_tasks
- get_task_history
- get_sprint_tasks
- get_release_tasks
- get_attachment_metadata

No live AS21 required yet.

Contract tests.

STOP.

==================================================
# STEP 06 — LEGACY AS21 BRIDGE
==================================================

Reuse proven transport only.

Do not call old agent or old LLM just to fetch data.

Map external -> canonical.

Mocks/fixtures required.

STOP.

==================================================
# STEP 07 — WORKFLOW ENGINE
==================================================

Implement deterministic:
- build_status_timeline
- time_in_status
- total_blocked_time
- current_age
- reopen_count
- stale detection

Tests with fixed timestamps.

STOP.

==================================================
# STEP 08 — METRICS ENGINE CORE
==================================================

Implement:
- throughput
- WIP
- cycle time
- lead time
- completion ratio
- carryover
- velocity
- predictability
- scope change

Each metric documented in `docs/metrics`.

Exact unit tests.

STOP.

==================================================
# STEP 09 — TASK INTELLIGENCE SEARCH
==================================================

Support:
- phrase;
- task key;
- assignee;
- sprint;
- release;
- product;
- attachment type xls/xlsx/pdf/msg.

Deterministic filtering only.

Golden tests.

STOP.

==================================================
# STEP 10 — LLM CLIENT ABSTRACTION
==================================================

Create provider-neutral client.

Must support:
- fake/test client;
- structured response validation;
- timeout;
- unavailable fallback;
- model id/version capture.

No live provider required for tests.

STOP.

==================================================
# STEP 11 — TASK SUMMARY
==================================================

Structured summary:
- goal
- what_to_do
- acceptance_expectations
- dependencies
- open_questions

If LLM unavailable:
return deterministic facts + warning.

Golden tests with fake LLM.

STOP.

==================================================
# STEP 12 — TASK QUALITY ANALYSIS
==================================================

Deterministic completeness rules + optional LLM explanation.

Configurable rules.

Output:
- score
- missing elements
- evidence
- recommendations

STOP.

==================================================
# STEP 13 — SPRINT INTELLIGENCE
==================================================

Output:
- health_status
- completion_ratio
- velocity
- throughput
- WIP
- carryover_risk
- aging_tasks
- blocked_tasks
- scope_change
- predictability
- risks
- evidence

LLM explains only.

STOP.

==================================================
# STEP 14 — TEAM CONFIG
==================================================

Create:
- `config/team.example.yaml`
- loader
- validator
- support external/private real config path

No real PII required in public repo.

STOP.

==================================================
# STEP 15 — TEAM INTELLIGENCE
==================================================

Implement:
- workload
- capacity
- overload/underload
- competency matching
- task-competency mismatch
- evidence

No unsupported performance judgments.

STOP.

==================================================
# STEP 16 — RELEASE INTELLIGENCE
==================================================

Implement:
- release scope
- completed/remaining
- blocked
- dependencies
- sprint linkage
- scope change
- readiness
- risk indicators
- forecast inputs

No fabricated dates.

STOP.

==================================================
# STEP 17 — DETERMINISTIC INTENT ROUTER
==================================================

Intents:
- task_search
- task_summary
- task_quality
- sprint_health
- velocity
- team_workload
- competency_match
- release_health
- help

Return:
- intent
- confidence
- entities
- router_version

Russian phrase tests.

STOP.

==================================================
# STEP 18 — LLM INTENT FALLBACK
==================================================

Only for low-confidence deterministic routing.

Strict JSON schema.

Allowlisted intent only.

Invalid output -> unknown/help.

STOP.

==================================================
# STEP 19 — PO ORCHESTRATOR V1
==================================================

Pipeline:
```text
request
-> route
-> validate entities
-> select one capability
-> execute
-> collect evidence
-> deterministic answer or LLM synthesis
```

Trace required.

No recursive planning.

STOP.

==================================================
# STEP 20 — MULTI-CAPABILITY PLANNER
==================================================

Support controlled multi-capability plans.

Allowlist only.

Hard maximum number of capability calls.

No autonomous recursion.

STOP.

==================================================
# STEP 21 — RESPONSE SYNTHESIS
==================================================

LLM receives:
- request
- intent
- facts
- metrics
- evidence
- warnings

Rules:
- Russian
- concise
- evidence-based
- distinguish fact / inference / recommendation
- no invented facts

Fallback formatter mandatory.

STOP.

==================================================
# STEP 22 — EXECUTION TRACE MODEL
==================================================

Create trace schema.

Minimum fields:
- trace_id
- request_id
- session_id
- timestamp
- request
- intent
- intent_confidence
- entities
- plan
- capability_calls
- adapter_calls
- llm_calls
- evidence_refs
- warnings
- errors
- latency
- versions

Tests.

STOP.

==================================================
# STEP 23 — SESSION MEMORY
==================================================

Create session-memory abstraction.

Store short-lived state:
- current sprint
- current product
- selected member
- referenced task
- clarification state

Requirements:
- TTL or lifecycle;
- explicit keys;
- no automatic permanent promotion.

Use in-memory first if enough.

Tests.

STOP.

==================================================
# STEP 24 — OPERATIONAL HISTORY STORE
==================================================

Create storage interface + SQLite implementation.

Persist traces and execution metadata.

Requirements:
- append-oriented;
- query by session/time/intent/status;
- no secrets;
- version fields;
- retention configurable.

Tests.

STOP.

==================================================
# STEP 25 — USER FEEDBACK STORE
==================================================

Support:
- thumbs up/down
- correction text
- expected intent
- expected entity
- expected answer fact
- optional comment

Feedback must link to trace_id.

No automatic learning yet.

Tests.

STOP.

==================================================
# STEP 26 — EVAL CASE MODEL
==================================================

Create eval-case schema.

Fields may include:
- case_id
- source
- query
- fixture/reference
- expected_intent
- expected_entities
- expected_structured_result
- tags
- severity
- status
- created_from_trace
- approved

Allow converting feedback into candidate eval cases.

STOP.

==================================================
# STEP 27 — EVAL RUNNER
==================================================

Create offline eval runner.

Evaluate:
- routing accuracy
- entity extraction
- structured capability outputs
- warning behavior
- no-LLM fallback
- LLM schema validity

Do not score exact prose as primary metric.

Generate machine-readable report.

STOP.

==================================================
# STEP 28 — FAILURE TAXONOMY
==================================================

Create failure categories:

```text
ROUTING_ERROR
ENTITY_EXTRACTION_ERROR
ADAPTER_ERROR
DATA_MAPPING_ERROR
METRIC_ERROR
MISSING_EVIDENCE
LLM_SCHEMA_ERROR
LLM_HALLUCINATION
KNOWLEDGE_ERROR
PROMPT_FAILURE
CAPABILITY_ERROR
UNKNOWN
```

Create classifier based on deterministic signals first.

Optional LLM-assisted categorization later.

STOP.

==================================================
# STEP 29 — FAILURE MINER
==================================================

Analyze historical failed/negative-feedback traces.

Output clusters such as:
- repeated routing confusion
- alias issue
- missing knowledge
- fragile prompt
- adapter mapping gap
- metric edge case

Do not modify production behavior.

Generate report only.

STOP.

==================================================
# STEP 30 — CURATED MEMORY
==================================================

Create Curated Memory store.

Candidate entry fields:
- key
- category
- content
- evidence_trace_ids
- source
- confidence
- status
- created_at
- approved_by
- version

Statuses:
- candidate
- approved
- rejected
- deprecated

Runtime may only use approved entries.

STOP.

==================================================
# STEP 31 — IMPROVEMENT CANDIDATE MODEL
==================================================

Support candidate types:
- prompt change
- router rule
- alias mapping
- knowledge entry
- golden test
- capability change
- config change

Candidate fields:
- reason
- linked failures
- expected benefit
- affected version
- risk
- proposed diff or content
- status

No auto-promotion.

STOP.

==================================================
# STEP 32 — PROMPT REGISTRY
==================================================

Version prompts.

Prompt metadata:
- prompt_name
- version
- content/path
- schema
- model compatibility
- created_at
- status
- eval score

Statuses:
- candidate
- active
- deprecated

Runtime logs active prompt version.

STOP.

==================================================
# STEP 33 — VERSION REGISTRY
==================================================

Track:
- agent
- router
- prompts
- capabilities
- metrics
- knowledge
- workflow
- model
- config

Provide active version snapshot.

Trace captures snapshot.

STOP.

==================================================
# STEP 34 — SHADOW MODE
==================================================

Create ability to execute candidate router/prompt/config in parallel.

Rules:
- candidate output not shown to user;
- no external writes;
- same input/fixture;
- result stored for comparison.

Tests.

STOP.

==================================================
# STEP 35 — COMPARISON ENGINE
==================================================

Compare production vs candidate.

Metrics:
- routing correctness
- entity correctness
- structured output match
- evidence coverage
- error rate
- latency
- fallback rate

Store comparison result.

STOP.

==================================================
# STEP 36 — REGRESSION GATE
==================================================

Create promotion criteria.

Example:
- no critical regression;
- routing score >= baseline;
- no new hallucination class;
- capability golden tests pass;
- no deterministic metric regression;
- latency within threshold.

Promotion must fail closed.

STOP.

==================================================
# STEP 37 — HUMAN APPROVAL GATE
==================================================

Implement explicit approval state.

No candidate becomes active without approval.

For local/dev:
CLI approval may be enough.

Example:
```bash
python scripts/promote_candidate.py <id>
```

Require:
- candidate passed eval;
- regression gate passed;
- approval recorded.

STOP.

==================================================
# STEP 38 — PROMOTION & ROLLBACK
==================================================

Support:
- promote candidate version
- rollback to previous active version
- audit record

Do not overwrite history.

Tests.

STOP.

==================================================
# STEP 39 — AI PDLC DASHBOARD DATA API
==================================================

Expose read-only endpoints for:
- success rate
- routing accuracy
- negative feedback rate
- LLM usage rate
- deterministic fast-path rate
- tool success rate
- regression escapes
- version comparisons
- top failure categories

Do not build UI yet.

STOP.

==================================================
# STEP 40 — FASTAPI ORCHESTRATOR API
==================================================

Routes:
- POST /api/v1/query
- GET /api/v1/health
- GET /api/v1/capabilities
- POST /api/v1/feedback
- GET /api/v1/trace/{id}
- GET /api/v1/versions

Stable schemas.

STOP.

==================================================
# STEP 41 — MCP SERVER
==================================================

Expose few high-level tools:
- po_query
- find_tasks
- analyze_sprint
- analyze_team
- analyze_release

Avoid dozens of duplicates.

STOP.

==================================================
# STEP 42 — KNOWLEDGE LAYER V1
==================================================

Load:
- product descriptions
- team roles
- workflow
- metric definitions
- release rules
- approved curated memory

No vector DB unless justified.

STOP.

==================================================
# STEP 43 — ACTION CONTRACTS
==================================================

Define:
- ActionProposal
- ActionConfirmation
- ActionResult
- AuditRecord

No real writes yet.

STOP.

==================================================
# STEP 44 — FRONTEND SKELETON
==================================================

React + TypeScript + Vite.

Views:
- Assistant
- Tasks
- Sprint
- Team
- Releases
- Quality/Evals

STOP.

==================================================
# STEP 45 — PO WORKSPACE UI
==================================================

Add:
- query workspace
- evidence panel
- trace view
- session context
- feedback buttons
- version info
- local task creation via modal/drawer/button

Use WORKS/DB/AS21-inspired visual language.

STOP.

==================================================
# STEP 46 — AI PDLC UI
==================================================

Add admin/dev view:
- eval results
- failure categories
- candidate improvements
- shadow comparison
- promotion status
- active versions
- rollback history

No hidden auto-promotion.

STOP.

==================================================
# STEP 47 — REGRESSION SUITE
==================================================

Minimum cases:

1. task phrase search
2. Excel attachment
3. PDF attachment
4. MSG attachment
5. task summary
6. task quality
7. sprint health
8. velocity
9. workload
10. competency match
11. release health
12. LLM unavailable
13. AS21 unavailable
14. unknown intent
15. malformed LLM JSON
16. empty sprint
17. missing member
18. unknown status
19. session memory continuity
20. history persisted
21. negative feedback -> eval candidate
22. candidate not auto-promoted
23. shadow result not served
24. regression gate rejects worse candidate
25. rollback restores prior active version

STOP.

==================================================
# STEP 48 — LEGACY COMPARISON
==================================================

Create:
`docs/architecture/LEGACY_VS_V2.md`

For each old capability:
- legacy capability
- v2 capability
- parity
- behavior differences
- tests
- migration readiness

Legacy stays intact until owner decides otherwise.

STOP.

---

# 18. KEY AI PDLC METRICS

Track eventually:

- Task Success Rate
- First-pass Correctness
- Routing Accuracy
- Entity Extraction Accuracy
- Grounded Answer Rate
- Tool Success Rate
- Deterministic Fast-path Rate
- LLM Fallback Rate
- Human Correction Rate
- Negative Feedback Rate
- Regression Escape Rate
- Candidate Win Rate
- Mean Latency
- Cost/LLM call count if available

Do not optimize a metric without understanding tradeoffs.

---

# 19. EVIDENCE MODEL

Every analytical capability should return evidence.

Example:

```json
{
  "type": "task",
  "id": "ABC-123",
  "fact": "task is blocked",
  "value": true
}
```

or:

```json
{
  "type": "metric",
  "fact": "carryover_ratio",
  "value": 0.31
}
```

Natural-language answer is secondary.

Evidence is primary.

---

# 20. CONFIGURATION RULES

No hardcoded:
- API keys
- tokens
- JSESSIONID
- personal email
- absolute local paths
- unexplained ports

Use env/config.

Example:

```env
PO_AGENT_ENV=dev
PO_AGENT_HOST=127.0.0.1
PO_AGENT_PORT=8010
PO_AGENT_DATA_DIR=./data
AS21_BASE_URL=
AS21_AUTH_MODE=
LLM_BASE_URL=
LLM_MODEL=
LLM_API_KEY=
HISTORY_BACKEND=sqlite
HISTORY_DB_PATH=./data/history.db
```

Unit tests must not require real secrets.

---

# 21. TEST RULES FOR QWEN CODER 3.7

Before code, print:

```text
FILES TO CREATE
FILES TO MODIFY
FILES TO READ
FILES NOT TO TOUCH
```

After code:
1. focused tests
2. stage suite
3. regression subset if applicable

Never "fix" tests by:
- deleting them;
- weakening assertions without reason;
- catching all exceptions;
- returning fake success;
- skipping important tests.

If blocked:
STOP.

---

# 22. GOLDEN TEST RULE

Do not assert exact free-form LLM prose.

Assert:
- intent
- entities
- structured facts
- evidence
- warnings
- version metadata
- required semantic constraints only where necessary

---

# 23. PROMPT DESIGN RULES

Use small versioned prompts:

- intent_classifier
- task_summarizer
- task_quality_explainer
- sprint_explainer
- team_explainer
- release_explainer
- final_synthesizer
- failure_clusterer
- improvement_candidate_generator

No universal mega-prompt.

---

# 24. ANTI-HALLUCINATION RULES FOR GIGACODE

Every stage implicitly includes:

```text
Do not invent file paths.
Do not invent classes.
Do not invent API schemas.
Search legacy before referencing it.
If not found, say NOT FOUND.
If legacy behavior is unclear, inspect callers/tests.
If still unclear, isolate behind interface.
Do not claim tests passed unless executed.
Do not claim AS21 works unless tested.
Do not change unrelated code.
Do not silently redesign the architecture.
```

---

# 25. REQUIRED REPORT AFTER EVERY STEP

Output exactly:

```text
STEP:
STATUS: COMPLETED | BLOCKED | PARTIAL

CREATED:
- ...

MODIFIED:
- ...

READ FROM LEGACY:
- ...

TESTS:
- command
- result

BEHAVIOR IMPLEMENTED:
- ...

NOT IMPLEMENTED:
- ...

RISKS:
- ...

TECH DEBT:
- ...

OWNER ACTION NEEDED:
- ...

NEXT STEP:
- ...

STOPPED: YES
```

Then STOP.

---

# 26. OWNER COMMANDS

Start:

```text
Прочитай PO_AGENT_PLATFORM_V2_GIGACODE_MASTER_SPEC_V2_1.md полностью.
Выполни только STEP 01.
```

Continue:

```text
Выполни следующий шаг по MASTER_SPEC.
```

Check current step:

```text
Проверь текущий шаг по MASTER_SPEC. Ничего не меняй.
```

Retry tests:

```text
Повтори тесты текущего шага. Не расширяй scope.
```

Stop:

```text
Остановись. Ничего больше не меняй.
```

---

# 27. GIT WORKFLOW

Develop the new app as a separate git repository.

At validated checkpoint:

```bash
git status
git add .
git commit -m "feat: complete step XX"
git push
```

Push the NEW v2 repository to GitHub.

ChatGPT can then inspect:
- architecture
- code
- tests
- diffs
- regressions
- AI PDLC artifacts
- next-step correctness

Keep real internal config local/private.

---

# 28. FIRST GIGACODE COMMAND

After saving this file where GigaCode can read it:

```text
Прочитай PO_AGENT_PLATFORM_V2_GIGACODE_MASTER_SPEC_V2_1.md полностью.

Мы создаём НОВОЕ приложение рядом с существующим legacy-проектом.
Старый проект не изменяй.

Выполни ТОЛЬКО STEP 01 — CREATE NEW APPLICATION SKELETON.

Перед изменениями выведи:
1. текущий каталог;
2. путь к legacy-проекту;
3. путь к новому po-agent-platform-v2;
4. FILES TO CREATE;
5. FILES TO MODIFY;
6. FILES TO READ;
7. FILES NOT TO TOUCH.

После этого реализуй STEP 01, запусти тесты, выдай отчёт строго по разделу 25 и остановись.

Не начинай STEP 02 без моей команды.
```

---

# 29. FINAL PRINCIPLE

The target is a real harness agent with AI PDLC, not an omnipotent chatbot.

Prefer:

```text
explicit contract
> implicit behavior

deterministic function
> prompt logic

small capability
> giant agent

evidence
> confident prose

history
> forgotten failures

evaluation
> intuition

shadow testing
> direct production replacement

human approval
> autonomous promotion

versioned improvement
> uncontrolled self-modification
```

The system should improve over time through controlled engineering loops:
**history -> feedback -> eval -> candidate -> shadow -> regression -> approval -> promotion -> rollback**.
