# PO Agent Harness — Authoritative Evolution Plan

**Status:** ACTIVE / source of truth for further work  
**Branch:** `feat/real-baseline-candidate-eval-v1`  
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
11. Never compensate for an AS21 source-contract defect in a prompt, skill, learning rule or UI.
12. A task-api 200 response is not proof of correct filtering; supported query parameters and returned source facts must be contract-tested.

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
- sprint source/list/current-sprint contract and task-to-sprint relation;
- release/fix-version source contract if required by `release_health`;
- attachment metadata/read path required by task intelligence skills;
- status history/changelog/read path required by flow metrics;
- pagination / bounded queries;
- no fabricated fallback records;
- read-only boundary.

Canonical model must expose fields required by active skills. Raw `source_data` may remain available for future mapping, but active business logic must not depend on ad-hoc raw parsing throughout the codebase.

**Important source architecture:** current task-api is not the only possible read facade. The repository already contains `SWTRSyncService`, which calls the real MCP-SWTR source read-only for `find_units`, `find_units_by_filter`, `read_unit`, `get_current_sprint`, and sprint-task retrieval. Gate A must inspect and reuse proven source read paths rather than assuming all required facts must already be present in `/api/v1/tasks`.

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
Expand in waves:
- Wave 1: task intelligence/search/attachments;
- Wave 2: sprint/flow metrics;
- Wave 3: team/capacity/competency;
- Wave 4: release/product analytics;
- Wave 5: cross-capability PO scenarios, notifications/actions and support capabilities.

Each new skill gets source contract requirements, unit tests, real-AS21 test where applicable, registry definition, trace/evidence, protected regression cases and learning-loop eligibility policy.

### GATE F — Frontend / PO Workspace integration
Only after Gates A-E. Recover the original UI specification and compare it with current frontend implementation screen by screen: conversational PO workspace, clarification UX, task search/results/detail, sprint health, velocity/flow metrics, team workload/performance, competency view, release health/risk, execution/evidence/trace, feedback controls, AI-PDLC lifecycle surfaces and all loading/empty/error/partial states.

### GATE G — Full E2E
Browser E2E must exercise the actual chain:

```text
Frontend -> API -> Orchestrator -> Context/Clarification -> Skill Resolver/Executor
 -> deterministic capability -> AS21 adapter/read source -> evidence/trace -> response -> UI
```

Critical E2E suites cover Core-8, clarification/resume, session isolation, AS21 unavailable, LLM unavailable deterministic fast path, empty results, real sprint/release selection, attachments where supported, feedback capture, learning candidate isolation and zero mutation authority.

## 3. Core-8 Real-AS21 Test Matrix

| Skill | Mandatory real-AS21 checks | Minimum source fields/contracts |
|---|---|---|
| task_search | exact key; phrase; assignee; status; sprint; project/space; empty result | key, title, description, assignee_id/login, raw+normalized status, sprint relation, project/space |
| task_summary | meaningful real task; grounded summary; attachment-aware when referenced | key, title, description, requirements-related fields, attachment metadata/read path |
| task_quality | complete/incomplete task; reproducible reasons; attachment-aware evidence | description, acceptance criteria/required sections, attachments/links as defined by metric |
| sprint_health | real current/recent sprint; WIP/blocked/aging/scope | current sprint/list endpoint, sprint tasks, status, dates/history, assignee, scope/effort |
| velocity | real sprint; reproducible formula; explicit unit | sprint tasks, completed state, estimate/task-count policy, sprint dates/history as formula requires |
| team_workload | actual team; active/WIP/blocked by assignee | assignee_id/login, status, sprint/project, effort where used |
| competency_match | task + approved competency config; no invented skills | task type/components/labels/description + approved team config |
| release_health | real release; scope/done/remaining/blocked/risk | release/fix version, status, sprint/project, dependencies, dates/timeline where required |

## 4. AS21 field/source policy

1. Preserve sanitized raw `source_data` for diagnostics/future mapping.
2. Canonicalize every field required by active skills.
3. Centralize AS21 extraction in adapters/mappers, not skills/prompts/UI.
4. Prefer a proven dedicated source capability over scanning an unrelated cached corpus.
5. `/api/v1/tasks` is a local task read facade; it does not support arbitrary `q`/JQL.
6. `SWTRSyncService`/MCP-SWTR may provide richer read-only facts (`read_unit`, current sprint, sprint tasks, filtered unit search). These must be contract-tested and wrapped cleanly before Harness consumption.
7. Unknown attributes remain raw but cannot silently influence deterministic logic.
8. Every newly activated skill declares required facts first.
9. Real examples define schema truth; never guess codes/nesting.
10. Do not truncate a real source description merely to satisfy an artificial canonical limit.

## 5. Learning-loop protection rules

- Never learn a source-data bug.
- Feedback may create eval/failure records; it may not directly rewrite the active skill.
- Candidate changes go through AI-PDLC only.
- Baseline/candidate comparisons use identical frozen evidence/corpus.
- Candidate must improve target metrics and preserve protected metrics.

## 6. Frontend rule

Frontend work is deliberately sequenced after source/skill/learning correctness. Before release, compare every original screen requirement from the earliest technical assignment with current implementation and build a screen-level acceptance matrix.

## 7. Work ownership and Git QA handoff

### ChatGPT/OpenAI side
- architecture analysis;
- production code changes;
- test design;
- migration/refactoring decisions;
- roadmap/contract updates;
- write current QA assignment to `GIGACODE_TEST_INSTRUCTIONS.md`;
- read QA reports directly from `qa_reports/`.

### GigaCode side
- pull target branch;
- read `GIGACODE_TEST_INSTRUCTIONS.md`;
- execute tests/adversarial review/read-only real-AS21 inspection;
- create/update only the assigned Markdown report in `qa_reports/`;
- do not modify production code unless explicitly authorized.

## 8. Current execution status

- [x] Harness architecture / governance foundations.
- [x] Human approval boundary / restart-safe governance tested.
- [x] Read-only SWTR shadow / frozen real-AS21 evaluation foundations.
- [x] Real baseline-vs-candidate evaluation boundary.
- [x] Real AS21 connectivity through local task-api bridge.
- [x] **A1: Core-8 source-contract inventory started and real assignee/project facts identified.**
- [x] **A2: deterministic base task mapping/filtering restored and verified on real AS21:** exact key, assignee externalId/login, project/space, status, free text, long descriptions, no ignored `q`, no false-positive assignee.
- [ ] **CURRENT A3: extended real SWTR source discovery + formal filter matrix.** Discover current sprint/sprint-task, attachments, history and release contracts using real MCP/SWTR read paths; then wire only proven facts.
- [ ] A4: freeze Core-8 corpus/query pack.
- [ ] Gate B: Core-8 8/8 real AS21.
- [ ] Gate C: learning-loop measurable improvement.
- [ ] Gate D: exact original 48-skill catalog.
- [ ] Gate E: expand 8 -> 48.
- [ ] Gate F: frontend screen finalization.
- [ ] Gate G: browser E2E/release readiness.

## 9. Immediate ordered actions

### STEP A1 — Source contract inventory — DONE
Historical/current architecture inspected; real assignee identity and project source proven.

### STEP A2 — Base deterministic mapping/filtering — DONE
Real QA proves:
- `WMB-30000` exact lookup;
- `assignee = Kalachanov.V.V` / login case-insensitive matching;
- nonexistent assignee -> 0;
- `project = WMB` and project+assignee intersection;
- status and free-text filtering;
- unknown fields fail closed;
- long descriptions no longer break corpus mapping;
- no new regressions.

### STEP A3 — Extended SWTR source discovery + real filter matrix — CURRENT
Do not merely scan `/api/v1/tasks` for absent data. Inspect proven real read-only SWTR/MCP routes and early implementation.

Required work:
1. Validate `/api/v1/swtr/sprints?space=WMB` / underlying `get_current_sprint`.
2. Validate `/api/v1/swtr/sprint-tasks` / underlying sprint-task source on a real sprint.
3. Inspect `SWTRSyncService` and local MCP tool catalog for attachment metadata/content read capabilities and history/changelog capabilities.
4. Owner provided a concrete clue: at least one task assigned to `Kalachanov.V.V` in WMB has attachments. QA must discover the task deterministically from real WMB tasks and inspect the raw `read_unit`/MCP payload instead of asking the owner to relay screenshots.
5. Determine whether attachments are a top-level `read_unit` field, an attribute, or require a dedicated MCP tool. Record metadata shape and safe read path.
6. Determine release/fix-version contract via real `read_unit`/filtered search or a dedicated release source; do not assume the local cached sample is representative.
7. Determine status history/changelog read path needed by sprint-health/velocity formulas. If none exists, explicitly redesign those formulas or mark the relevant capability unavailable; never fabricate history.
8. Formalize already-proven filter matrix: key, assignee, project, status, free-text and safe intersections. Add sprint/release only after source evidence exists.

**Exit:** `READY_FOR_A4=YES` when required Core-8 source facts are either proven and mapped, or explicitly classified unavailable with an approved skill behavior/metric policy.

### STEP A4 — Freeze Core-8 test corpus/query pack
Select bounded real tasks/sprints/releases/attachment examples and record IDs + hashes/expected source facts only. No secrets.

### STEP B1-B8 — Execute Core-8
Run one skill at a time on real AS21, fixing root-layer failures and protecting previous GREEN tests.

### STEP C1/C2 — Learning loop
After 8/8 GREEN, prove controlled improvement on `task_search`, then one analytical skill.

### STEP D1 — Recover original 48
Search earliest commits/specification, generate `PO_AGENT_48_SKILL_MATRIX.md`, reconcile with current registry.

### STEP E/F/G
Expand skills, finalize frontend, then browser E2E.

## 10. Definition of Done

- Core 8 real-AS21 = 8/8 GREEN;
- learning loop demonstrates measurable improvement without regressions;
- exact original 48 requirements accounted for and accepted;
- deterministic/evidence-grounded source contracts;
- human approval/rollback enforced;
- original frontend product scope restored/finalized;
- full critical browser E2E = 100%;
- P0 = 0;
- unauthorized AS21 writes = 0;
- secret leakage = 0.

---

**Next action:** STEP A3 — use real MCP/SWTR read capabilities (not only cached `/api/v1/tasks`) to discover and prove sprint, attachment, history and release contracts, then complete the formal Core-8 source/filter matrix.
