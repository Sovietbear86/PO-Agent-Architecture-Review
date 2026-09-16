# Agent Core V4 — 54-Skill Migration Plan

**Status:** AUTHORITATIVE V4-CATALOG EXECUTION PLAN  
**Date:** 2026-09-16  
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

### Live-source-only invariant — locked after A192

A192 proved that a formally valid skill can silently return false zeroes when a legacy handler scans the empty local task store. Therefore every factual V4 skill must obey all of the following:

- production facts come only from a certified live read path to REAL AS21/SWTR;
- `/api/v1/tasks`, SQLite/local task store, sync snapshot, cache, fixture, fake/frozen data are forbidden as production source-of-truth reads;
- local storage is never a fallback when a live route fails;
- if no certified live read surface exists, the skill is `SOURCE_CONDITIONAL` / `SOURCE_UNAVAILABLE`, not a legitimate empty result;
- `REAL_EMPTY` requires proof from the live source itself;
- QA must verify route provenance, not only answer/count parity;
- a reused legacy capability is acceptable only after proving that its production adapter path is live-source-backed for that specific operation.

Every wave must preserve:
- A188 representative POC GREEN;
- A190 plugin/dummy-55 GREEN;
- A191 Browser C GREEN;
- `semantic_prepass_used=false`;
- REAL AS21 authority and exact key-set parity for factual collections;
- live-source-only factual reads with zero local-store fallback;
- fail-closed source/ambiguity behavior;
- `runtime_contract` completion for contracted successful trajectories;
- session isolation and UIContract presentation-only semantics.

Owner writes production changes. GigaCode remains independent QA/adversarial tester only.

## 3. Canonical 54 matrix and waves

### Wave T — Task catalog (#1–20)

| # | Canonical skill | Legacy/source capability | V4 target | Current state after A192 |
|---:|---|---|---|---|
| 1 | Exact task lookup | `task.lookup` | `task.lookup` | GREEN_SOURCE_SUPPORTED |
| 2 | Task phrase/text search | live source-backed task search | `task.search_text` | **RED_A192_WRONG_LOCAL_SOURCE** |
| 3 | Tasks with attachments | live attachment source | `task.search_attachments` | SOURCE_CONDITIONAL |
| 4 | Tasks with Excel attachments | live attachment source + `attachment_type=excel` | `task.search_excel` | SOURCE_CONDITIONAL |
| 5 | Tasks with PDF attachments | live attachment source + `attachment_type=pdf` | `task.search_pdf` | SOURCE_CONDITIONAL |
| 6 | Tasks with MSG attachments | live attachment source + `attachment_type=msg` | `task.search_msg` | SOURCE_CONDITIONAL |
| 7 | Search/filter by assignee | source-backed `member.resolve` + live task search | `task.search_assignee` | **RED_A192_NL_IDENTITY_DEAD_END** |
| 8 | Search/filter by status | live task collection + deterministic status filter | `task.search_status` | **RED_A192_STATUS_ONLY_REJECTED** |
| 9 | Search/filter by sprint | `sprint.resolve` + live sprint task collection | `task.search_sprint` | GREEN_SOURCE_SUPPORTED |
| 10 | Search/filter by release | `release.resolve` + live release task collection | `task.search_release` | SOURCE_CONDITIONAL |
| 11 | Grounded task summary | `task.summary` | `task.summary` | GREEN_SOURCE_SUPPORTED |
| 12 | Task definition quality | `task.quality` | `task.quality` | GREEN_SOURCE_SUPPORTED |
| 13 | Missing requirements detection | `task.missing_requirements` | `task.missing_requirements` | GREEN_SOURCE_SUPPORTED |
| 14 | Acceptance/testability analysis | `task.acceptance_analysis` | `task.acceptance` | GREEN_SOURCE_SUPPORTED |
| 15 | Task dependency/link analysis | `task.dependencies` | `task.dependencies` | GREEN_SOURCE_SUPPORTED |
| 16 | Task lifecycle/history | live task history | `task.history` | SOURCE_CONDITIONAL |
| 17 | Time in task statuses | live task history | `task.time_in_status` | SOURCE_CONDITIONAL |
| 18 | Aging active tasks | live task collection + source timestamps | `task.aging` | SOURCE_CONDITIONAL |
| 19 | Task blocker analysis | `task.blockers` | `task.blockers` | GREEN_SOURCE_SUPPORTED |
| 20 | Similar/duplicate discovery | live task corpus + deterministic similarity | `task.similar` | SOURCE_CONDITIONAL |

A192 result: **10 GREEN_SOURCE_SUPPORTED / 7 SOURCE_CONDITIONAL / 3 RED**. No A188/A190/A191 regression. The three REDs are bounded owner fixes and block Wave S until re-gated.

Wave T acceptance: all 20 canonical rows are explicitly represented by V4 `SkillSpec`s, and every source-supported row must be GREEN without local-store reads.

### Wave S — Sprint/flow (#21–32)

| # | Canonical skill | Legacy/source capability | V4 target | Source note |
|---:|---|---|---|---|
| 21 | Sprint health | `sprint.health` | `sprint.health` | A191_PRESENT |
| 22 | Resolve current sprint | source-backed `sprint.current` | `sprint.current` | A191_PRESENT |
| 23 | Sprint scope | `sprint.scope` | `sprint.scope` | complete live collection required |
| 24 | Sprint velocity | `sprint.velocity` | `sprint.velocity` | explicit unit/formula |
| 25 | Sprint throughput | `sprint.throughput` | `sprint.throughput` | current live source |
| 26 | Sprint WIP | `sprint.wip` | `sprint.wip` | current live source |
| 27 | Sprint cycle time | `sprint.cycle_time` | `sprint.cycle_time` | history required |
| 28 | Sprint lead time | `sprint.lead_time` | `sprint.lead_time` | history required |
| 29 | Sprint carryover | `sprint.carryover` | `sprint.carryover` | `SOURCE_CONDITIONAL: sprint_snapshots` |
| 30 | Sprint scope change | `sprint.scope_change` | `sprint.scope_change` | `SOURCE_CONDITIONAL: sprint_snapshots` |
| 31 | Sprint predictability | `sprint.predictability` | `sprint.predictability` | semantics/warnings must state baseline limits |
| 32 | Sprint PO risk queue | `sprint.risk_queue` | `sprint.risk_queue` | evidence-backed ranking |

### Wave M — Team (#33–40)

| # | Canonical skill | Legacy/source capability | V4 target | Source note |
|---:|---|---|---|---|
| 33 | Team workload distribution | `team.workload` | `team.workload` | live source-backed tasks |
| 34 | Team WIP by member | `team.wip` | `team.wip` | no employee-quality inference |
| 35 | Team blocked work | `team.blocked` | `team.blocked` | evidence-backed |
| 36 | Team capacity/load | `team.capacity` | `team.capacity` | capacity provenance/warnings required |
| 37 | Competency match | `team.competency_match` | `team.competency_match` | `SOURCE_CONDITIONAL: team_competencies` |
| 38 | Assignee recommendation | `team.assignee_recommendation` | `team.assignee_recommendation` | `SOURCE_CONDITIONAL: team_competencies`; explain recommendation |
| 39 | Team bottlenecks | `team.bottlenecks` | `team.bottlenecks` | concentration, not performance scoring |
| 40 | Work distribution by competence | `team.distribution` | `team.distribution` | approved competency config where used |

### Wave R/P — Release + portfolio (#41–48)

| # | Canonical skill | Legacy/source capability | V4 target | Source note |
|---:|---|---|---|---|
| 41 | Release health/readiness | `release.health` | `release.health` | A191_PRESENT |
| 42 | Release scope | `release.scope` | `release.scope` | complete live source set |
| 43 | Release progress | `release.progress` | `release.progress` | deterministic ratio/counts |
| 44 | Release blockers | `release.blockers` | `release.blockers` | evidence queue |
| 45 | Release dependencies | `release.dependencies` | `release.dependencies` | dependency source required |
| 46 | Release risk queue | `release.risk_queue` | `release.risk_queue` | grounded ranking |
| 47 | Portfolio overview/attention | `portfolio.overview` | `portfolio.overview` | provenance required |
| 48 | PO attention queue | `po.attention_queue` | `po.attention_queue` | cross-domain evidence |

### Wave X — Reconciled additions (#49–54)

| # | Canonical skill | Legacy/source capability | V4 target | Source/safety note |
|---:|---|---|---|---|
| 49 | Task search by product/space | V4 `space.resolve` + live task search | `task.search_product` | exact space postcondition |
| 50 | Release forecast | `release.forecast` | `release.forecast` | `SOURCE_CONDITIONAL: release_timeline` |
| 51 | PO daily brief | `po.daily_brief` | `po.daily_brief` | live source-backed aggregation |
| 52 | PO status report | `po.status_report` | `po.status_report` | live source-backed aggregation |
| 53 | PO reminder draft | `po.reminder_draft` | `po.reminder_draft` | `GREEN_DRAFT_ONLY`; no external send/write |
| 54 | PO local task draft | `po.local_task_draft` | `po.local_task_draft` | `GREEN_DRAFT_ONLY`; no external AS21 write |

## 4. QA contract for every wave

For each wave GigaCode must independently verify, without production edits:

1. architecture/static gate — plugin-only skill addition; no Agent Core/planner/runtime business-skill hardcode;
2. focused unit/contract tests — discovery, binding, completion, UIContract, fail-closed behavior;
3. fresh REAL AS21 Oracle B immediately before factual cases;
4. exact normalized fact/key parity for collection skills;
5. **live route provenance:** factual production requests must not touch `/api/v1/tasks`/local SQLite/task-store truth; only certified live AS21/SWTR facades are accepted;
6. real Browser C for representative skills and every new UI result shape;
7. negative/not-found/ambiguous/source-unavailable states;
8. retained A188/A190/A191 regression sample;
9. no source-supported skill is marked GREEN from fixture/fake/frozen/local data;
10. source-conditional skills are explicitly classified, never fabricated or silently skipped.

A wave is GREEN only after owner implementation **and** independent GigaCode QA report.

## 5. Current execution position

```text
A188_REPRESENTATIVE_POC = GREEN
A190_PLUGIN_GATE = GREEN
A191_BROWSER_UI = GREEN
A192_TASK_WAVE = RED_3_BOUNDED_DEFECTS
V4_LIVE_SOURCE_ONLY_INVARIANT = LOCKED
V4_CATALOG_DENOMINATOR = 54_LOCKED
CURRENT_WAVE = T_TASK_1_20_REMEDIATION
NEXT_GATE = A193_TASK_WAVE_REGATE
NEXT_AFTER_T_GREEN = S_SPRINT_21_32
THEN = M_TEAM_33_40 -> R/P_RELEASE_PORTFOLIO_41_48 -> X_ADDITIONS_49_54
FULL_54_ABC = NOT_DONE
RELEASE_READY = NO
```

Do not start Wave S while the three A192 REDs remain unresolved. Bounded source-conditional classifications may proceed if they are proven fail-closed and explicitly tracked.