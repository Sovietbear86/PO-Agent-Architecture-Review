# Agent Core V4 — 54-Skill Migration Plan

**Status:** AUTHORITATIVE V4-CATALOG EXECUTION PLAN  
**Date:** 2026-09-17  
**Branch:** `feat/core8-real-query-hardening-v2`  
**Permanent rollback:** `0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`

## 1. Scope lock

The V4 production catalog denominator is exactly **54 user-facing skills**:

- the original frozen 48 requirements from `PO_AGENT_48_SKILL_MATRIX.md`;
- plus the six reconciled additions preserved by that matrix.

No row may be silently skipped, merged out of the denominator, or replaced by an infrastructure/helper skill. Helper/composition skills such as `tasks.search`, `tasks.lookup_then_assignee`, `sprints.discover`, and `sprints.list` may remain in the progressive catalog, but they do **not** change the canonical 54 denominator.

Every canonical skill must end in one terminal classification:
- `GREEN_SOURCE_SUPPORTED` — A/B/C certified against fresh REAL AS21;
- `GREEN_DRAFT_ONLY` — safe non-writing draft behavior certified where applicable;
- `SOURCE_CONDITIONAL` — implementation exists but the authoritative source contract is unavailable in the tested environment; must fail closed and be re-certified when the source is present;
- `RED` — bounded implementation defect requiring owner remediation.

`NOT_TESTED`, silent skip, remembered source facts, fake/frozen truth, or local-DB truth are forbidden final classifications.

## 2. Migration invariant

Each wave is implemented only through the trusted V4 plugin surface. Adding a canonical skill may add or edit plugin artifacts, reusable deterministic/source handlers, tests, and UI contracts, but MUST NOT require a per-skill edit to:

- `agent_core_v4.py`;
- planner strategy/prompt routing logic for a particular business skill;
- runtime trajectory orchestration;
- deterministic completion engine internals.

Existing lower-layer deterministic capabilities should be reused where they are already source-correct. Do not reimplement proven business logic merely to rename it V4.

### Live-source-only invariant

Every factual V4 skill must obey all of the following:

- production facts come only from a certified live read path to REAL AS21/SWTR;
- `/api/v1/tasks`, SQLite/local task store, sync snapshot, cache, fixture, fake/frozen data are forbidden as production source-of-truth reads;
- local storage is never a fallback when a live route fails;
- if no certified live read surface exists, the skill is `SOURCE_CONDITIONAL` / `SOURCE_UNAVAILABLE`, not a legitimate empty result;
- `REAL_EMPTY` requires proof from the live source itself;
- QA must verify route provenance, not only answer/count parity;
- a reused legacy capability is acceptable only after proving that its production adapter path is live-source-backed for that specific operation.

### Identity invariant — locked after A195D

Person resolution is generic and source-authoritative:

- configured team membership is only an optional hint and never defines the searchable population;
- any REAL AS21 person may be queried when source identity resolution can establish a canonical identity;
- ambiguous identities must return typed clarification with source-backed options when available;
- unknown identities fail closed with meaningful clarification/not-found semantics;
- morphology normalization is generic and must not rely on person/surname hardcoding;
- task collection starts only after canonical identity is confirmed by REAL AS21.

Every wave must preserve:
- A188 representative POC GREEN;
- A190 plugin/dummy-55 GREEN;
- A191 Browser C GREEN;
- A195D universal identity resolver GREEN;
- `semantic_prepass_used=false`;
- REAL AS21 authority and exact key-set parity for factual collections;
- live-source-only factual reads with zero local-store fallback;
- fail-closed source/ambiguity behavior;
- `runtime_contract` completion for contracted successful trajectories;
- session isolation and UIContract presentation-only semantics.

Owner writes production changes. GigaCode remains independent QA/adversarial tester only.

## 3. Canonical 54 matrix and waves

### Wave T — Task catalog (#1–20)

| # | Canonical skill | V4 target | Current state after A195D |
|---:|---|---|---|
| 1 | Exact task lookup | `task.lookup` | GREEN_SOURCE_SUPPORTED |
| 2 | Task phrase/text search | `task.search_text` | GREEN_SOURCE_SUPPORTED |
| 3 | Tasks with attachments | `task.search_attachments` | GREEN_SOURCE_SUPPORTED |
| 4 | Tasks with Excel attachments | `task.search_excel` | SOURCE_CONDITIONAL |
| 5 | Tasks with PDF attachments | `task.search_pdf` | SOURCE_CONDITIONAL |
| 6 | Tasks with MSG attachments | `task.search_msg` | SOURCE_CONDITIONAL |
| 7 | Search/filter by assignee | `task.search_assignee` | GREEN_SOURCE_SUPPORTED |
| 8 | Search/filter by status | `task.search_status` | GREEN_SOURCE_SUPPORTED |
| 9 | Search/filter by sprint | `task.search_sprint` | GREEN_SOURCE_SUPPORTED |
| 10 | Search/filter by release | `task.search_release` | SOURCE_CONDITIONAL |
| 11 | Grounded task summary | `task.summary` | GREEN_SOURCE_SUPPORTED |
| 12 | Task definition quality | `task.quality` | GREEN_SOURCE_SUPPORTED |
| 13 | Missing requirements detection | `task.missing_requirements` | GREEN_SOURCE_SUPPORTED |
| 14 | Acceptance/testability analysis | `task.acceptance` | GREEN_SOURCE_SUPPORTED |
| 15 | Task dependency/link analysis | `task.dependencies` | GREEN_SOURCE_SUPPORTED |
| 16 | Task lifecycle/history | `task.history` | SOURCE_CONDITIONAL |
| 17 | Time in task statuses | `task.time_in_status` | SOURCE_CONDITIONAL |
| 18 | Aging active tasks | `task.aging` | SOURCE_CONDITIONAL |
| 19 | Task blocker analysis | `task.blockers` | GREEN_SOURCE_SUPPORTED |
| 20 | Similar/duplicate discovery | `task.similar` | SOURCE_CONDITIONAL |

A195D result: **Wave T re-closed GREEN** with universal source-backed identity resolution restored. Before Wave S starts, execute one full regression of every currently exposed V4 skill and helper/composition skill on current HEAD.

### Wave S — Sprint/flow (#21–32)

| # | Canonical skill | V4 target | Source note |
|---:|---|---|---|
| 21 | Sprint health | `sprint.health` | already present; must remain GREEN |
| 22 | Resolve current sprint | `sprint.current` | already present; must remain GREEN |
| 23 | Sprint scope | `sprint.scope` | complete live collection required |
| 24 | Sprint velocity | `sprint.velocity` | explicit unit/formula |
| 25 | Sprint throughput | `sprint.throughput` | current live source |
| 26 | Sprint WIP | `sprint.wip` | current live source |
| 27 | Sprint cycle time | `sprint.cycle_time` | history required |
| 28 | Sprint lead time | `sprint.lead_time` | history required |
| 29 | Sprint carryover | `sprint.carryover` | `SOURCE_CONDITIONAL: sprint_snapshots` |
| 30 | Sprint scope change | `sprint.scope_change` | `SOURCE_CONDITIONAL: sprint_snapshots` |
| 31 | Sprint predictability | `sprint.predictability` | semantics/warnings must state baseline limits |
| 32 | Sprint PO risk queue | `sprint.risk_queue` | evidence-backed ranking |

### Wave M — Team (#33–40)

| # | Canonical skill | V4 target | Source note |
|---:|---|---|---|
| 33 | Team workload distribution | `team.workload` | live source-backed tasks |
| 34 | Team WIP by member | `team.wip` | no employee-quality inference |
| 35 | Team blocked work | `team.blocked` | evidence-backed |
| 36 | Team capacity/load | `team.capacity` | capacity provenance/warnings required |
| 37 | Competency match | `team.competency_match` | `SOURCE_CONDITIONAL: team_competencies` |
| 38 | Assignee recommendation | `team.assignee_recommendation` | `SOURCE_CONDITIONAL: team_competencies`; explain recommendation |
| 39 | Team bottlenecks | `team.bottlenecks` | concentration, not performance scoring |
| 40 | Work distribution by competence | `team.distribution` | approved competency config where used |

### Wave R/P — Release + portfolio (#41–48)

| # | Canonical skill | V4 target | Source note |
|---:|---|---|---|
| 41 | Release health/readiness | `release.health` | already present; must remain GREEN |
| 42 | Release scope | `release.scope` | complete live source set |
| 43 | Release progress | `release.progress` | deterministic ratio/counts |
| 44 | Release blockers | `release.blockers` | evidence queue |
| 45 | Release dependencies | `release.dependencies` | dependency source required |
| 46 | Release risk queue | `release.risk_queue` | grounded ranking |
| 47 | Portfolio overview/attention | `portfolio.overview` | provenance required |
| 48 | PO attention queue | `po.attention_queue` | cross-domain evidence |

### Wave X — Reconciled additions (#49–54)

| # | Canonical skill | V4 target | Source/safety note |
|---:|---|---|---|
| 49 | Task search by product/space | `task.search_product` | exact space postcondition |
| 50 | Release forecast | `release.forecast` | `SOURCE_CONDITIONAL: release_timeline` |
| 51 | PO daily brief | `po.daily_brief` | live source-backed aggregation |
| 52 | PO status report | `po.status_report` | live source-backed aggregation |
| 53 | PO reminder draft | `po.reminder_draft` | `GREEN_DRAFT_ONLY`; no external send/write |
| 54 | PO local task draft | `po.local_task_draft` | `GREEN_DRAFT_ONLY`; no external AS21 write |

## 4. QA contract for every wave

For each wave GigaCode must independently verify, without production edits:

1. architecture/static gate — plugin-only skill addition; no Agent Core/planner/runtime business-skill hardcode;
2. focused unit/contract tests — discovery, binding, completion, UIContract, fail-closed behavior;
3. fresh REAL AS21 Oracle B immediately before factual cases;
4. exact normalized fact/key parity for collection skills;
5. live route provenance: factual production requests must not touch `/api/v1/tasks`/local SQLite/task-store truth;
6. real Browser C for representative skills and every new UI result shape;
7. negative/not-found/ambiguous/source-unavailable states;
8. retained A188/A190/A191/A195D regression sample;
9. no source-supported skill is marked GREEN from fixture/fake/frozen/local data;
10. source-conditional skills are explicitly classified, never fabricated or silently skipped.

A wave is GREEN only after owner implementation **and** independent GigaCode QA report.

## 5. Full-regression checkpoint before Wave S

Before implementing #23–32, run a clean **full existing-catalog regression checkpoint** against current HEAD. A196 found bounded D1/D2 implementation defects. A197 closed D2 and similar, but exposed a timestamp-bridge correctness defect in aging plus a generic premature planner-READY completion hole. After owner remediation, A198 is the mandatory final pre-Wave-S re-gate.

Scope is broader than the canonical 20 Task skills: it includes every currently exposed V4 skill in `builtin.core.a188` and `builtin.catalog.tasks`, including helper/composition skills (`tasks.search`, `tasks.lookup_then_assignee`, `sprints.discover`, `sprints.list`) and already-present `sprint.health`, `sprint.current`, `release.health`.

A198 must prove:
- every exposed skill can be loaded/selected and terminates according to its contract;
- every factual skill uses REAL AS21 only;
- source-supported factual collections match fresh Oracle B exactly;
- SOURCE_CONDITIONAL rows fail closed and never fabricate support;
- identity/morphology/clarification continuation remain healthy;
- Browser C/UIContract works for every currently used result shape;
- plugin registry/dummy-55 remains GREEN;
- no regression to A188/A190/A191/A195D.

Only after the current zero-RED pre-Wave-S gate is GREEN may owner implementation of Wave S #23–32 begin. A201 is the current mandatory gate after A200 exposed clarification-continuation false completion.

## 6. Current execution position

```text
A188_REPRESENTATIVE_POC = GREEN
A190_PLUGIN_GATE = GREEN
A191_BROWSER_UI = GREEN
A195D_UNIVERSAL_IDENTITY = GREEN
WAVE_T_TASK_1_20 = GREEN / RE-CLOSED
A196_FULL_EXISTING_CATALOG = RED_D1_D2_BOUNDED_IMPLEMENTATION_DEFECTS
A197_FULL_EXISTING_CATALOG = RED_AGING_TIMESTAMP_BRIDGE
A197_D2_ATTACHMENTS = CLOSED
A197_SIMILAR = CLOSED
OWNER_AGING_AND_COMPLETION_FIX = IMPLEMENTED
V4_LIVE_SOURCE_ONLY_INVARIANT = LOCKED
V4_IDENTITY_SOURCE_AUTHORITY = LOCKED
V4_CATALOG_DENOMINATOR = 54_LOCKED
A198_FULL_EXISTING_CATALOG = RED_MULTI_FILTER_CONSTRAINT_COVERAGE
A198_AGING = CLOSED
A198_ATTACHMENTS = CLOSED
A198_SIMILAR = CLOSED
OWNER_MULTI_FILTER_AND_RELEASE_LOCAL_PATH_FIX = IMPLEMENTED
A199_FULL_EXISTING_CATALOG = RED_CROSS_SKILL_COMPLETION_FRONTIER
A199_CANONICAL_27_MATRIX = 20_GREEN_7_SOURCE_CONDITIONAL_0_RED
OWNER_COMPLETION_FRONTIER_FIX = IMPLEMENTED
A200_FULL_EXISTING_CATALOG = RED_CLARIFICATION_CONTINUATION_FALSE_COMPLETION
A200_CANONICAL_27_MATRIX = 20_GREEN_7_SOURCE_CONDITIONAL_0_RED
A200_BROWSER_C = 10_10_GREEN
A200_LOCAL_STORE_FACTUAL_READS = 0
OWNER_GENERIC_CONTINUATION_STATE_FIX = IMPLEMENTED
A201_FULL_EXISTING_CATALOG = GREEN_ZERO_RED_PRE_WAVE_S
A201_CANONICAL_27_MATRIX = 20_GREEN_7_SOURCE_CONDITIONAL_0_RED
A201_BROWSER_C = 10_10_GREEN
A201_LOCAL_STORE_FACTUAL_READS = 0
POST_A201_HYGIENE = GREEN_A202
A202_ROLLBACK_CHECKPOINT = checkpoint/v4-pre-wave-s-a202@e580489950e5a149a6a740cb8779dfdb0351d471
POST_A202_TEST_COMPAT_CLEANUP = CLOSED
A203_TEST_COMPAT = RED_TEST_ONLY_STALE_TUPLE
A204_SPRINT_RELEASE_HEALTH_DIALOG = RED_4_BOUNDED_DEFECT_CLASSES
A204_MANUAL_ADVERSARIAL = CONFIRMED_ADDITIONAL_UNASSIGNED_MULTI_HOP_HISTORY_CASES
OWNER_A204_REMEDIATION_BUNDLE = IMPLEMENTED_PENDING_A205
A205_ATTEMPT_1 = RED_PLANNER_INTERFACE_SESSION_CONTEXT
A205_ATTEMPT_2 = RED_PLUGINIZED_LITERAL_GUARD_SESSION_CONTEXT
OWNER_RUNTIME_INTERFACE_PARITY_FIX = GREEN_PREFLIGHT
A205_PREFLIGHT_RUNTIME_INTERFACE = GREEN
A205_FULL_EXISTING_CATALOG_ADVERSARIAL = GREEN_27_27_ZERO_RED
A205_CANONICAL_27_MATRIX = 20_GREEN_7_SOURCE_CONDITIONAL_0_RED
A205_BROWSER_C = GREEN_7_7
A205_LOCAL_STORE_FACTUAL_READS = 0
A205_N_PLUS_ONE_SPRINT_MEMBERSHIP = CLOSED
A205_PLUGIN_DUMMY_55 = GREEN
A205_ROLLBACK_CHECKPOINT = checkpoint/v4-a205-green@1fd519105ba6612f535ad98a55cb1302f387ca43
CURRENT_GATE = EXPLICIT_OWNER_APPROVAL_FOR_WAVE_S_23_32
NEXT = OWNER_IMPLEMENT_WAVE_S_23_32_IN_BOUNDED_BATCHES_THEN_INDEPENDENT_QA
ALREADY_PRESENT_WAVE_S = #21 sprint.health, #22 sprint.current
THEN = M_TEAM_33_40 -> R/P_RELEASE_PORTFOLIO_41_48 -> X_ADDITIONS_49_54
FULL_54_ABC = NOT_DONE
RELEASE_READY = NO
```
