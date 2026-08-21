# PO Agent Harness — Authoritative Evolution Plan

**Status:** ACTIVE / consolidated source of truth  
**Current branch:** `feat/core8-real-query-hardening-v2`  
**Last reviewed:** 2026-08-21
**Current blocking gate:** Assignment 032 — full unchanged 029/026 V2 semantic/Core-8 benchmark
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
13. Historical GREEN is a baseline, not permanent acceptance: a later source-backed counterexample reopens the affected gate.
14. The sprint-list facade is only a candidate-key source. Sprint membership, assignee, status and other task facts used by an oracle must come from individually hydrated authoritative SWTR task units.
15. Every explicit user constraint must survive semantic interpretation, grounding and capability arguments, or execution must clarify/fail closed. Silent broadening is forbidden.
16. Production NLU is LLM-first. Deterministic code normalizes structural identifiers and validates/grounds facts; it must not replace semantic interpretation with Russian phrase dictionaries or keyword routing.
17. Exact task-key-set equality against an independent hydrated oracle outranks answer prose, HTTP status and count-only checks.

## 1. Target evolution

```text
Original PO Agent / legacy proven behavior
        |
        v
Restore AS21 source contract + Core-8 real-data baseline
        |
        v
Controlled Learning Loop with human approval and rollback
        |
        v
Recover/freeze original 48 requirements + preserve 6 reconciled additions
        |
        v
Implement 54 catalog entries (implementation state only)
        |
        v
Revalidate Core-8 semantic/source boundary with hydrated oracle
(Assignment 031 GREEN -> Assignment 032 full unchanged 029/026 V2 benchmark)
        |
        v
Accept 48 + 6 skills in controlled Gate-E waves on real evidence
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

### GATE E — Accept the implemented catalog in controlled waves

The production catalog currently contains 54 entries marked `implemented`: the frozen historical 48 plus six reconciled additions. `implemented` proves that an executable path exists; it does **not** by itself prove real-data, grounding, safety or cross-skill acceptance. Gate E remains open until every wave passes its source/evidence contract and protected regression suite.

Expand/accept in waves:
- Wave 1: task intelligence/search/attachments;
- Wave 2: sprint/flow metrics;
- Wave 3: team/capacity/competency;
- Wave 4: release/product analytics;
- Wave 5: the six reconciled additions, cross-capability PO scenarios, drafts/actions and support capabilities.

Each new skill gets source contract requirements, unit tests, real-AS21 test where applicable, registry definition, trace/evidence, protected regression cases and learning-loop eligibility policy.

### GATE F — Frontend / PO Workspace integration
Only after Gates A-E. Recover the original UI specification and compare it with current frontend implementation screen by screen: conversational PO workspace, clarification UX, task search/results/detail, sprint health, velocity/flow metrics, team workload/performance, competency view, release health/risk, execution/evidence/trace, feedback controls, AI-PDLC lifecycle surfaces and all loading/empty/error/partial states.

### GATE G — Full E2E
Browser E2E must exercise the actual chain:

```text
Frontend -> API -> Orchestrator -> Context/Clarification -> Skill Resolver/Executor
 -> deterministic capability -> AS21 adapter/read source -> evidence/trace -> response -> UI
```

Critical E2E suites cover Core-8, clarification/resume, session isolation, AS21 unavailable, LLM unavailable **fail-closed behavior**, empty results, real sprint/release selection, attachments where supported, feedback capture, learning candidate isolation and zero mutation authority. Production must not fall back to deterministic natural-language phrase routing when the semantic model is unavailable.

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
- architecture analysis and production changes;
- source-contract, semantic-boundary and deterministic execution decisions;
- test/acceptance design without weakening existing oracles;
- roadmap and contract updates;
- create versioned assignments under `qa_assignments/`;
- point `GIGACODE_NEXT_ACTION.md` to exactly one active assignment;
- inspect QA reports directly from `qa_reports/`;
- diagnose and fix production defects reported by QA.

### GigaCode side
- pull the target branch and restart the real local services;
- read `GIGACODE_NEXT_ACTION.md`, then the referenced assignment;
- act only as tester/adversarial reviewer;
- execute the complete authorized QA workflow autonomously without asking for confirmation after every step or integration; source/LLM reads, local restarts, tests and publishing the allowed report are pre-authorized;
- ask only for genuinely missing authority/credentials, unavoidable platform approval, destructive/out-of-scope action or material scope expansion, and batch unavoidable approval prompts;
- use real read-only AS21/SWTR evidence when required;
- never modify production code, prompts, tests, fixtures, acceptance runners, learning state or local source data unless the owner explicitly changes the role;
- create, commit and push only the report named by the active assignment (plus an already-supported machine-readable result only when allowed);
- stop after publishing the report and return its commit SHA and full contents.

### Stable command to GigaCode

```text
Открой репозиторий Sovietbear86/PO-Agent-Architecture-Review, перейди в ветку feat/core8-real-query-hardening-v2 и выполни GIGACODE_NEXT_ACTION.md. Работай только как тестировщик и выполни весь разрешённый QA-сценарий автономно, без подтверждения после каждого шага или интеграции. Закоммить и отправь только разрешённый заданием QA-отчёт, затем верни SHA и полный текст отчёта.
```

## 8. Consolidated execution status

### Verified historical gates

- [x] Harness/governance foundations, restart-safe approval boundary and read-only SWTR evaluation.
- [x] Gate A historical source-contract campaign: task mapping/filtering, sprint/release paths, attachments, pagination and read-only boundary were exercised.
- [x] Gate B historical Core-8 baseline: 8/8 was recorded during the 011/014 campaigns.
- [x] Gate C closed: Learning Loop 012/013/014 proved isolated candidate evaluation, measurable improvement, human approval and rollback. `GATE_C_LEARNING_LOOP_GREEN=YES`.
- [x] Gate D closed: `PO_AGENT_48_SKILL_MATRIX.md` accounts for exactly 48 historical requirements and preserves six later reconciled additions. QA 015 recorded `GATE_D_48_SKILL_CATALOG_GREEN=YES`.
- [x] Skill-catalog implementation surface: 54/54 entries are currently marked `implemented`.

### Acceptance distinction

The 54/54 catalog state is an implementation inventory, not a release verdict. Gate E real-data acceptance is not complete. Earlier Core-8 GREEN was legitimately reopened when exhaustive natural-language queries exposed:

- incomplete paraphrase invariance;
- correction/session-context weaknesses;
- silent slot/filter loss;
- false-green task sets;
- sprint-list candidates whose authoritative individual task relation belonged to another sprint.

Therefore Gate B is currently **REVALIDATION BLOCKED**, Gate E is **FROZEN**, and frontend/release work remains deferred.

### Fixes already completed after the freeze

- LLM transport restored locally with the required `/openai/v1` base path; secrets remain uncommitted.
- LLM-first semantic boundary hardened with an independent semantic audit pass.
- Structural task/sprint identifiers are canonicalized separately from natural-language interpretation.
- Requested filters must be grounded or fail closed.
- Correction turns reuse structured prior semantic state.
- Production commit `fe1b5990e9234fdf959eaccec9187755c4161629` stopped fabricating sprint membership from the sprint-list facade and now requires individual SWTR task hydration.
- Production commit `319ae1e85311f3123c44c2dd0118b843172aef4d` preserves independent sprint constraints across specialized task-search intents and revalidates sprint proof at the final execution boundary.

### Current active gate

- [x] **Assignment 030 — Source-backed Sprint Membership Retest:** valid report `3077c4b`, BLOCKED with 17 foreign-sprint tasks and two silent slot drops.
- [x] **Assignment 031 — Multi-filter Execution and Sprint Fail-closed Retest:** valid report commit `b5ac573`, narrow gate GREEN.
- [x] Garanin/DMS-SPRNT-1 exact set PASS: `DMS-248`, `DMS-243`, `DMS-93`, `DMS-36`.
- [x] Moiseev/DMS-SPRNT-2 exact set PASS: `DMS-261`.
- [x] `FOREIGN_SPRINT_TASK_COUNT=0`, unknown sprint fail-closed, focused tests 5/5.
- [x] `FALSE_GREEN_COUNT=0`, `SILENT_SLOT_DROP_COUNT=0`, `QUERY_HTTP_500_COUNT=0` in the narrow gate.
- [ ] **Assignment 032 — Full Core-8 Semantic Benchmark:** execute the complete unchanged 029/026 V2 real-data benchmark. Assignment 031 did not perform it and therefore did not close Gate B.
- [ ] Resolve/classify `test_conversation_context_is_supplied_to_next_semantic_turn` after the sprint-membership gate without confusing a stale fixture with production correction behavior.

### Current release/gate values

```text
GATE_A_HISTORICAL_BASELINE = GREEN
GATE_B_HISTORICAL_BASELINE = 8/8 GREEN
GATE_B_CURRENT_REVALIDATION = PENDING_032_FULL_BENCHMARK
GATE_C_LEARNING_LOOP = GREEN
GATE_D_48_REQUIREMENT_RECOVERY = GREEN
CATALOG_IMPLEMENTATION = 54/54
GATE_E_ACCEPTANCE = FROZEN
FRONTEND_FINALIZATION = DEFERRED
RELEASE_READY = NO
READY_TO_RERUN_017_V2 = NO
```

## 9. Immediate ordered actions

### STEP 030 — source-backed sprint-membership gate — BLOCKED

Assignment 030 executed from branch HEAD `483c35b` and reported `030_NARROW_GATE=BLOCKED`: specialized `task_search_assignee` execution silently dropped `sprint_id`, returned 17 foreign `OLP-SPRNT-5` tasks for DMS queries, and accepted an unproven sprint as `COMPLETED + empty`.

The earlier commit `9f7e604` remains an invalid stale Assignment 006 run and has no gate verdict. The valid 030 report is commit `3077c4b`.

`sprint candidate keys -> individual SWTR task hydration -> authoritative relation/assignee/status -> requested filters -> exact task-key set`

Do not use facade echo, answer prose, counts or the agent result itself as oracle evidence.

### STEP 031 — multi-filter execution remediation and retest — GREEN

Production commit `319ae1e85311f3123c44c2dd0118b843172aef4d` routes every task-search skill with two or more filters through the hardened composite capability and re-proves `sprint_id` at the final execution boundary. Focused local gate: 5/5 PASS. No phrase-routing or LLM architecture change was introduced.

Assignment 031 report commit `b5ac573` proved fresh service PIDs/process paths, exact-set equality for both required multi-filter cases, zero foreign-sprint tasks, and correct fail-closed handling of an unproven sprint. Narrow gate GREEN does not replace the complete 026/029 benchmark.

### STEP 032 — full unchanged semantic/Core-8 acceptance — CURRENT

Execute `qa_assignments/CORE8_FULL_SEMANTIC_BENCHMARK_032.md`. Run the complete unchanged 029/026 V2 benchmark:

- architecture preflight;
- Core-8 8/8 on real AS21;
- paraphrase invariance 8/8;
- person/product/status robustness;
- multi-filter preservation;
- explicit identifier safety;
- correction/recheck loop 6/6;
- ambiguity and fail-closed cases;
- exact source-backed equality;
- zero false greens and zero silent slot drops.

### STEP 033 — resume or continue freeze

Resume roadmap work only when all Assignment 026 hard gates are GREEN and `READY_TO_RERUN_017_V2=YES`. Then rerun/close 017_V2 as required by the freeze. Otherwise continue the developer-fix -> versioned-QA loop.

### STEP E — Gate-E wave acceptance

After Core-8 hardening closes, reconcile the 54 implemented catalog entries against `PO_AGENT_48_SKILL_MATRIX.md` and accept them wave-by-wave. Update matrix statuses from historical `MAPPED` to accepted states only with source, execution, evidence and regression proof.

### STEP F — Frontend / PO Workspace

Recover the original screen scope and complete a screen-level acceptance matrix only after Gate E.

### STEP G — Full browser E2E and release

Run the actual production chain end-to-end, verify failure/clarification/loading states, approval boundaries and zero AS21 mutation authority.

## 10. Definition of Done

- Core 8 real-AS21 = 8/8 GREEN;
- learning loop demonstrates measurable improvement without regressions;
- exact original 48 requirements plus six reconciled additions accounted for and accepted;
- deterministic/evidence-grounded source contracts;
- human approval/rollback enforced;
- original frontend product scope restored/finalized;
- full critical browser E2E = 100%;
- P0 = 0;
- unauthorized AS21 writes = 0;
- secret leakage = 0.

---

**Next action:** execute Assignment 032 from `GIGACODE_NEXT_ACTION.md`. Do not resume 017_V2, Gate E, frontend or release work until the unchanged full 029/026 V2 benchmark is GREEN with zero false greens and zero silent slot drops.
