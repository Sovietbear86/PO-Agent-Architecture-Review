# PO Agent — Gate D: Original 48 Requirement Matrix

## Purpose
This file freezes the **original 48-requirement acceptance surface** before expanding the Harness beyond Core-8.

Authoritative recovery rule from `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`: do not invent requirements from memory; account for exactly 48 original requirements and map them to current Harness skills/capabilities with no silent omissions.

The current recovery catalog later reconciled the Master Spec to **54 explicit user-facing skills**. That 54-skill catalog is useful for future expansion, but Gate D intentionally freezes the earlier **48-requirement threshold** first. The six later/restored requirements are tracked separately below and do not alter the Gate-D denominator.

Statuses used here:
- `IMPLEMENTED` — executable production path exists and is protected by tests;
- `MAPPED` — requirement has a clear current target skill/capability but is not yet accepted end-to-end;
- `MERGED` — original requirement is intentionally represented by another current skill/capability;
- `NOT_YET_IMPLEMENTED` — target contract is known but implementation remains for Gate E.

## Frozen original 48

| # | Original requirement | Current Harness skill / mapping | Required context / source facts | Gate-D status | Gate-E acceptance focus |
|---:|---|---|---|---|---|
| 1 | Exact task lookup by key | `task-lookup` | task key, canonical AS21 task | IMPLEMENTED | preserve exact-key fail-closed |
| 2 | Task phrase/text search | `task-search` | query, canonical task text | IMPLEMENTED | Core-8 protected |
| 3 | Tasks with attachments | `task-search-attachments` | attachment metadata | IMPLEMENTED | Office/PDF/MSG coverage |
| 4 | Tasks with Excel attachments | `task-search-excel` | XLS/XLSX metadata | IMPLEMENTED | WMB-30000 regression |
| 5 | Tasks with PDF attachments | `task-search-pdf` | PDF metadata/read path | IMPLEMENTED | preserve proven PDF support |
| 6 | Tasks with MSG attachments | `task-search-msg` | MSG metadata/read path | IMPLEMENTED | real attachment example |
| 7 | Search/filter by assignee | `task-search-assignee` | assignee id/login | IMPLEMENTED | team member real-AS21 cases |
| 8 | Search/filter by status | `task-search-status` | raw + normalized status | IMPLEMENTED | unknown status fail-closed |
| 9 | Search/filter by sprint | `task-search-sprint` | sprint relation/id | IMPLEMENTED | current/recent sprint |
| 10 | Search/filter by release | `task-search-release` | fix version/release id | IMPLEMENTED | real release |
| 11 | Grounded task summary | `task-summary` | title, description, requirements, attachments | IMPLEMENTED | Core-8 |
| 12 | Task definition quality | `task-quality` | description, acceptance evidence | IMPLEMENTED | deterministic reasons |
| 13 | Missing requirements detection | `task-missing-requirements` | task definition sections | MAPPED | deterministic checklist |
| 14 | Acceptance criteria/testability analysis | `task-acceptance-analysis` | AC/description | MAPPED | evidence + reproducibility |
| 15 | Task dependency/link analysis | `task-dependency-analysis` | links/dependencies | MAPPED | prove source contract first |
| 16 | Task lifecycle/history | `task-history` | changelog/history | MAPPED | dedicated history source |
| 17 | Time in task statuses | `task-time-in-status` | status history/timestamps | MAPPED | deterministic duration |
| 18 | Aging active tasks | `task-aging` | created/updated/status dates | MAPPED | deterministic aging policy |
| 19 | Task blocker analysis | `task-blocker-analysis` | status, links, blocker evidence | MAPPED | grounded explanation |
| 20 | Similar/duplicate task discovery | `task-similar` | canonical task corpus/text | MAPPED | bounded similarity + evidence |
| 21 | Sprint health | `sprint-health` | sprint tasks/status/dates/effort | IMPLEMENTED | Core-8 + Learning Loop 014 |
| 22 | Resolve current sprint | `sprint-current` | current sprint source | MAPPED | deterministic current selection |
| 23 | Sprint scope | `sprint-scope` | complete sprint task set | MAPPED | pagination/completeness |
| 24 | Sprint velocity | `sprint-velocity` / Core-8 `velocity` | completed tasks + effort policy | IMPLEMENTED | explicit unit/formula |
| 25 | Sprint throughput | `sprint-throughput` | completed task set + dates | MAPPED | deterministic count/rate |
| 26 | Sprint WIP | `sprint-wip` | active statuses | MAPPED | deterministic status policy |
| 27 | Sprint cycle time | `sprint-cycle-time` | history/timestamps | MAPPED | deterministic formula |
| 28 | Sprint lead time | `sprint-lead-time` | creation/completion history | MAPPED | deterministic formula |
| 29 | Sprint carryover | `sprint-carryover` | previous/current sprint relations | MAPPED | source-backed comparison |
| 30 | Sprint scope change | `sprint-scope-change` | sprint membership history | MAPPED | additions/removals after start |
| 31 | Sprint predictability | `sprint-predictability` | commitment/completion policy | MAPPED | documented formula |
| 32 | Sprint PO risk queue | `sprint-risk-queue` | health metrics + task evidence | MAPPED | ranked grounded risks |
| 33 | Team workload distribution | `team-workload` | assignee/status/sprint/effort | IMPLEMENTED | Core-8 |
| 34 | Team WIP by member | `team-wip` | assignee + active status | MAPPED | no employee-quality inference |
| 35 | Team blocked work | `team-blocked` | assignee + blocker/status | MAPPED | evidence-backed |
| 36 | Team capacity/load | `team-capacity` | approved capacity config + work | MAPPED | config provenance required |
| 37 | Competency match | `team-competency-match` / Core-8 `competency_match` | task facts + approved competency config | IMPLEMENTED | no invented competencies |
| 38 | Assignee recommendation | `team-assignee-recommendation` | competencies + workload | IMPLEMENTED | explain recommendation |
| 39 | Team bottlenecks | `team-bottlenecks` | workload/WIP/blocked evidence | MAPPED | concentration, not performance scoring |
| 40 | Work distribution by competence | `team-distribution` | task + competency config | MAPPED | grounded distribution |
| 41 | Release health/readiness | `release-health` | release scope/status/blockers | IMPLEMENTED | Core-8 real release |
| 42 | Release scope | `release-scope` | fix version/release task set | MAPPED | complete source set |
| 43 | Release progress | `release-progress` | done/remaining scope | MAPPED | deterministic ratio/counts |
| 44 | Release blockers | `release-blockers` | blocked tasks/dependencies | MAPPED | evidence queue |
| 45 | Release dependencies | `release-dependencies` | task/release dependency source | MAPPED | source contract required |
| 46 | Release risk queue | `release-risk-queue` | release metrics + evidence | MAPPED | ranked grounded risks |
| 47 | Portfolio overview / attention | `portfolio-overview` | multi-product/sprint/release facts | IMPLEMENTED | source provenance + attention queue |
| 48 | PO attention queue | `po-attention-queue` | task/sprint/release risk evidence | MAPPED | ranked cross-domain queue |

## Reconciled additions beyond the original 48
The later canonical recovery catalog contains 54 explicit user-facing skills. These six requirements are **outside the frozen Gate-D denominator** and are queued for Gate E/roadmap reconciliation:

1. `task-search-product` — task search by product/space;
2. `release-forecast` — bounded release forecasting inputs;
3. `po-daily-brief`;
4. `po-status-report`;
5. `po-reminder-draft`;
6. `po-local-task-draft`.

They must not be lost, but they also must not silently rewrite the historical “48” acceptance gate into a different denominator.

## Core-8 crosswalk

| Core-8 accepted skill | Matrix requirement(s) |
|---|---|
| `task_search` | #2 plus implemented filter/search variants #1–10 |
| `task_summary` | #11 |
| `task_quality` | #12 |
| `sprint_health` | #21 |
| `velocity` | #24 |
| `team_workload` | #33 |
| `competency_match` | #37/#38 depending query contract |
| `release_health` | #41 |

## Gate D acceptance
Gate D is green only when an independent repository audit confirms:
1. denominator is exactly 48;
2. every row is traceable to historical/master-spec evidence or an explicitly documented merge/rename;
3. no original requirement is silently omitted;
4. no infrastructure component is counted as a fake business skill;
5. the six reconciled additions are preserved separately;
6. current Core-8 mappings remain correct;
7. Gate E can consume this matrix wave-by-wave without changing the denominator.

## Gate E waves after approval
- **E1 Task intelligence:** #11–20, preserving #1–10.
- **E2 Sprint/flow:** #21–32.
- **E3 Team:** #33–40.
- **E4 Release/portfolio:** #41–48.
- **E5 Reconciled additions:** the six post-48 requirements above, after the historical 48 gate is satisfied.

No frontend finalization starts before Gate E acceptance.