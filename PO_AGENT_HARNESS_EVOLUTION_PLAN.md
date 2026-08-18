# PO Agent Harness — Authoritative Evolution Plan

**Status:** ACTIVE / source of truth for further work  
**Branch at creation:** `feat/real-baseline-candidate-eval-v1`  
**Purpose:** prevent architectural drift and loss of earlier product requirements while evolving the original PO Agent into a self-improving Harness agent.

> This document is the execution roadmap. `PO_AGENT_PLATFORM_V2_GIGACODE_MASTER_SPEC_V2_1.md`, `PO_AGENT_PLATFORM_V2_ADDENDUM_SKILLS_CLARIFICATION.md`, `REAL_DATA_COMPREHENSIVE_TEST_CHECKLIST.md`, the legacy implementation and early commits are normative sources. If they disagree, do not guess: record the conflict and resolve it explicitly before implementation.

## 0. Non-negotiable principles

1. Preserve the product behavior of the original PO Agent while evolving the architecture.
2. The final target is the complete original skill model (48 skills/capabilities from the original specification), implemented in the Harness architecture.
3. Do not jump directly to all 48. First prove the architecture on the eight core domain skills.
4. AS21/SWTR behavior must be validated on real read-only data. Fixtures are allowed only for fault injection and impossible-to-reproduce edge cases.
5. GigaCode is tester/reviewer for this work unless the owner explicitly changes this rule. Production code changes are implemented by ChatGPT/OpenAI side of the workflow.
6. Deterministic retrieval/filtering/calculation stays in code. LLM interprets, clarifies and synthesizes; it must not invent AS21 facts or deterministic metrics.
7. Learning never mutates active production behavior directly. Required path: evidence -> failure cluster/feedback -> candidate -> eval -> shadow -> regression gate -> human approval -> promotion; rollback must exist.
8. No AS21 write authority during real-data acceptance. Search/evaluation/shadow are read-only.
9. Any regression in an already-green skill blocks promotion of a candidate.
10. Frontend finalization and full browser E2E happen only after the real-data skill contract and learning loop are proven.

## 1. Target evolution

```text
Original PO Agent / legacy proven behavior
        |
        v
Restore AS21 source contract and canonical mapping
        |
        v
8 core skills on REAL AS21 data (8/8 GREEN)
        |
        v
Learning loop on those same 8 skills
(candidate -> shadow -> gate -> human approval -> rollback)
        |
        v
Prove measurable improvement without regressions
        |
        v
Recover canonical original catalog of 48 skills
        |
        v
Expand 8 -> 48 in controlled waves, each with real-data tests
        |
        v
48/48 functional + safety + grounding acceptance
        |
        v
Frontend integration / PO Workspace / all original screens
        |
        v
Full backend + Harness + AS21 + frontend E2E
        |
        v
Release readiness
```

## 2. Phase gates

### GATE A — AS21 Source Contract GREEN
Required before any learning-loop work.

Must prove on real AS21 data:
- exact task lookup;
- title/description and identity mapping;
- assignee id/login extraction and filtering;
- project/space filtering;
- status raw -> normalized mapping;
- sprint extraction and filtering;
- release extraction and filtering;
- attachments required by core skills;
- pagination / bounded queries;
- no fabricated fallback records;
- read-only boundary.

Canonical model must expose fields required by active skills. Raw `source_data` may remain available for future mapping, but active business logic must not depend on ad-hoc raw parsing throughout the codebase.

**Current known blocker/history:** real `assigned_to` user metadata may store login/externalId inside `source_data.swtr_attributes[].value.externalId`; canonical `assignee_id` must be populated from the real structure before assignee filtering can be considered GREEN.

### GATE B — Eight Core Skills GREEN on real AS21
The canonical eight domain skills are:

1. `task_search`
2. `task_summary`
3. `task_quality`
4. `sprint_health`
5. `velocity`
6. `team_workload`
7. `competency_match`
8. `release_health`

`help` is a platform/support skill and is tested separately; it does not count toward the 8/8 core-domain gate.

For every skill require:
- at least one real-data happy path;
- negative/empty-result path;
- context/clarification case where applicable;
- deterministic source/evidence verification;
- trace with `skill_id` + version;
- no unauthorized capability/tool call;
- no AS21 mutation;
- no regression in the other core skills.

**Exit criterion:** `CORE_SKILLS_REAL_AS21 = 8/8 GREEN`.

### GATE C — Learning Loop GREEN
Run only after Gate B.

For at least two representative core skills (first `task_search`, then one analytical skill such as `sprint_health`):
1. Capture a reproducible failure or controlled weaker baseline.
2. Link feedback/evidence to trace + skill version.
3. Create improvement candidate; active version remains unchanged.
4. Evaluate baseline and candidate on identical frozen corpus.
5. Run shadow comparison.
6. Reject false-green candidates and any candidate that regresses protected tests.
7. Require human approval before promotion.
8. Verify promoted version measurably improves the intended metric.
9. Verify all eight skills still pass regression.
10. Exercise rollback and confirm restoration of previous active version.

**Exit criterion:** measurable improvement demonstrated, `NEW_CODE_REGRESSIONS_VS_BASE=0`, no auto-promotion, rollback verified.

### GATE D — Recover and Freeze the 48-Skill Catalog
Do not invent the catalog from memory.

Actions:
- inspect earliest specification/technical assignment commits;
- locate the original 48-skill/capability list;
- map legacy names to current Harness skill/capability names;
- identify duplicates, renamed items and composite capabilities;
- freeze a versioned matrix: `original_requirement -> current_skill -> capability -> required_context -> AS21 fields -> tests -> UI consumer`.

Deliverable: `PO_AGENT_48_SKILL_MATRIX.md`.

**Exit criterion:** exactly 48 original requirements are accounted for as `implemented / mapped / intentionally merged / not-yet-implemented`, with no silent omissions.

### GATE E — Expand 8 -> 48
Expand in waves. Recommended order:

- Wave 1: task intelligence/search/attachments;
- Wave 2: sprint/flow metrics;
- Wave 3: team/capacity/competency;
- Wave 4: release/product analytics;
- Wave 5: cross-capability PO scenarios, notifications/actions and support capabilities.

Each new skill gets:
- source contract requirements;
- unit tests;
- real-AS21 test where safe/applicable;
- skill registry definition;
- trace/evidence;
- protected regression cases;
- learning-loop eligibility policy.

No wave starts if previous wave is not GREEN.

**Exit criterion:** `ORIGINAL_SKILL_REQUIREMENTS = 48/48 accounted`, functional acceptance GREEN, P0=0.

### GATE F — Frontend / PO Workspace integration
Only after Gates A-E.

Recover the original UI specification and compare it with the current frontend implementation screen by screen. Validate at minimum:
- conversational PO workspace;
- clarification UX;
- task search/results/detail;
- sprint health;
- velocity/flow metrics;
- team workload/performance;
- competency view where specified;
- release health/risk;
- execution history/evidence/trace surfaces;
- feedback controls;
- AI-PDLC/skill lifecycle admin surfaces defined by the v2 addendum;
- loading/empty/error/partial states.

Do not redesign away original business functions merely to fit the Harness architecture.

### GATE G — Full E2E
Browser E2E must exercise the actual chain:

```text
Frontend
 -> API
 -> Orchestrator
 -> Context Resolver / Clarification
 -> Skill Resolver / Executor
 -> deterministic capability
 -> AS21 adapter (real read-only data for approved cases)
 -> evidence / trace
 -> response
 -> UI
```

E2E suites:
- core eight skills;
- clarification/resume;
- session override/isolation;
- AS21 unavailable;
- LLM unavailable deterministic fast path;
- empty results;
- real sprint/release selection;
- feedback capture;
- learning candidate visible only in admin/shadow flow;
- no write/mutation path from user-facing evaluation flow.

**Exit criterion:** critical E2E = 100%, P0=0, no secret leakage, no unauthorized writes.

## 3. Core-8 Real-AS21 Test Matrix — first working set

| Skill | Mandatory real-AS21 checks | Minimum source fields/contracts |
|---|---|---|
| task_search | exact key; phrase; assignee; status; sprint; project/space; empty query result | key, title, description, assignee_id/login, raw+normalized status, sprint_id, project/space, source_data |
| task_summary | real meaningful task; grounded summary; no fabricated requirement | key, title, description, acceptance/requirements-related fields, links/attachments when referenced |
| task_quality | complete/incomplete task; reproducible score and reasons | description, acceptance criteria/required sections, attachments/links as defined by metric |
| sprint_health | current/recent sprint; WIP/blocked/aging/scope; evidence | sprint_id, status, dates/history, assignee, scope/effort fields required by formula |
| velocity | real sprint; formula reproducible; units explicit | sprint_id, completed state, effort/estimate or task-count policy, sprint dates |
| team_workload | actual team; active/WIP/blocked by assignee | assignee_id/login, status, sprint/project, effort where used |
| competency_match | task + approved team competency config; no invented skills | task type/components/labels/description + approved team competency config |
| release_health | real release; scope/done/remaining/blocked/risk | release_id/fix version, status, sprint/project, dependencies/blocked indicators, dates |

## 4. AS21 field policy

We do **not** need to flatten every possible AS21 attribute immediately. We do need a safe extensible mapping strategy:

1. Preserve sanitized raw `source_data` for diagnostics/future mapping.
2. Canonicalize every field required by active skills.
3. Centralize AS21 attribute extraction in the adapter/mapper, not in skills/prompts/UI.
4. Support typed extraction helpers for user, sprint, release, status, project/space, attachment, component/label and other required attribute families.
5. Unknown attributes remain available in raw form but cannot silently influence deterministic logic.
6. Every newly activated skill must declare additional required source fields before implementation.
7. Real examples define schema truth; do not guess AS21 codes or nesting.

## 5. Learning-loop protection rules

- Never learn a source-data bug. If wrong result originates in AS21 mapping/transport, fix deterministic code first.
- Feedback such as “ты вывел задачи Иванова, а не Калачанова” may create an eval/failure record; it may not directly rewrite the active skill.
- A candidate may change intent aliases, required context, workflow, prompt refs, capability allowlist or output constraints only through AI-PDLC.
- It may not bypass AS21 source contract, governance or human approval.
- Baseline/candidate comparisons must use identical frozen evidence/corpus.
- Candidate must improve target metrics and preserve protected metrics.

## 6. Frontend rule

Frontend work is not abandoned; it is deliberately sequenced after source/skill/learning correctness. Before release, compare every original screen requirement from the earliest technical assignment with current implementation and build a screen-level acceptance matrix.

## 7. Work ownership

### ChatGPT/OpenAI side
- architecture analysis;
- code changes;
- test design;
- migration and refactoring decisions;
- updating this roadmap and skill matrices.

### GigaCode side
- execute requested tests;
- adversarial testing;
- inspect real AS21 responses where authorized;
- report evidence/root causes;
- **do not modify production code** unless explicitly instructed by the owner.

## 8. Current execution status

- [x] Harness architecture / production runtime / governance foundations implemented and repeatedly regression-tested.
- [x] Restart-safe governance / human approval boundary tested.
- [x] Read-only SWTR shadow and real-shadow evaluation foundations tested.
- [x] Frozen AS21 runtime implemented so real Harness can execute on frozen tasks with zero reads after freeze.
- [x] Real baseline-vs-candidate evaluation boundary implemented/tested.
- [x] Real AS21 connectivity demonstrated through local task-api bridge.
- [ ] **CURRENT: Gate A — restore/verify complete source contract needed by Core-8.**
- [ ] Gate B — Core-8 on real AS21.
- [ ] Gate C — learning-loop measurable improvement.
- [ ] Gate D — recover/freeze exact 48-skill catalog.
- [ ] Gate E — expand 8 -> 48.
- [ ] Gate F — frontend screen-by-screen finalization.
- [ ] Gate G — full browser E2E/release readiness.

## 9. Immediate ordered actions

### STEP A1 — Source contract inventory
Inspect current canonical `Task`, AS21 adapter/mapper and legacy proven mapper. Produce field mapping for Core-8 only. Verify real structures for assignee, status, sprint, release, project/space, attachments and fields needed by metrics.

### STEP A2 — Fix deterministic mapping defects
Fix assignee extraction first, then sprint/release/status/project as evidence requires. Add regression tests from sanitized real payload shapes.

### STEP A3 — Real filter matrix
On real AS21 data test: key, assignee, status, sprint, project/space, release and safe combinations. Expected values must be derived independently from returned real records, not from the agent answer.

### STEP A4 — Freeze Core-8 test corpus/query pack
Select bounded real tasks/sprints/releases and record only IDs + hashes/expected facts needed for reproducible acceptance. Do not store secrets.

### STEP B1-B8 — Execute each core skill
Run one skill at a time on real AS21, fix deterministic/root layer failures, protect previous green tests.

### STEP C1 — Learning loop on task_search
Use a controlled failure/eval; prove candidate creation, shadow, gate, approval and rollback.

### STEP C2 — Learning loop on analytical skill
Repeat on `sprint_health` or another evidence-rich analytical skill.

### STEP D1 — Recover original 48
Search earliest commits/specification, generate `PO_AGENT_48_SKILL_MATRIX.md`, reconcile with current registry.

### STEP E/F/G
Expand skills, finalize frontend and run browser E2E only after preceding gates.

## 10. Definition of Done

The project is not considered complete merely because the Harness infrastructure is GREEN.

Final DoD:
- Core 8 real-AS21 = 8/8 GREEN;
- learning loop demonstrates real measurable improvement without regressions;
- exact original 48 requirements accounted for and accepted;
- source contracts deterministic and evidence-grounded;
- human approval/rollback enforced;
- frontend original product scope restored/finalized;
- full browser E2E critical suite = 100%;
- P0 = 0;
- unauthorized AS21 writes = 0;
- secret leakage = 0.

---

**Next action:** STEP A1 — inventory the Core-8 source contract and compare current AS21 mapping with the proven early implementation. Do not return to learning-loop changes before Gate A and Gate B are GREEN.
