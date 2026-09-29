# GigaCode — Current Action

## ACTIVE: Assignment 227R — planner reliability re-gate + deferred PO acceptance

Role: QA/adversarial tester only. Do NOT modify code.

Prior verdict:
`AGENT_CORE_V4_PO_ACCEPTANCE_RED_A227`

Retain P0/P1/P2 GREEN from A227 unless contradicted by the current diff.

## Owner fixes under test

1. RealLLMClient normalizes null/list/non-string message content before LLMResponse validation.
2. Robust planner no longer retries an identical prompt after provider/client decode failure; it appends the generic action-only recovery instruction for the next bounded attempt.
3. Production V4 runtime normalizes `В работе / In Progress / in_progress` to source workflow category `progress`.
4. Focused regressions added for provider-exception recovery and progress normalization.

No phrase/person/entity-specific production router is allowed.

## P0 — focused build/protocol gate

- clean worktree, record START_HEAD;
- tsc + vite build;
- run robust protocol tests, task-search/composition tests, sprint discovery tests;
- prove no semantic-prepass/person router/phrase router introduced;
- prove recovery remains action-only and cannot mint READY after a malformed turn.

Unexpected regression => RED STOP.

## P1 — blocking NL composition re-gate

Run each case at least 5 fresh sessions; exact source Oracle B refreshed immediately before the batch.

A. `Открытые задачи Калачанова с вложениями в пространстве WMB`
- expected source truth may be empty after intersecting open + assignee + attachments;
- all constraints must be preserved;
- no confident non-empty/empty unless Oracle B proves it;
- no ValidationError/V4ContractError planner failure.

B. `Задачи Семавина по рискам`
- source-resolve Semavin;
- no invented risk/task rows;
- no planner transport failure;
- if the implemented skill interprets "по рискам" as phrase/risk analysis, prove exact source behavior and document trajectory.

C. `Задачи в работе в сентябрьском спринте по DMS`
- resolve source sprint for September;
- task.search must use the canonical progress semantic, not literal-localized equality;
- exact key parity against source status_type=progress set;
- confident false zero is blocking RED.

D. `Спринты в DMS`
- grounded non-task answer remains GREEN.

Acceptance:
- A/B: 5/5 terminally correct/fail-closed with no planner runtime failure;
- C: 5/5 exact keys;
- D: 3/3 grounded.
First failure => STOP.

## P2 — task rendering/persistence

Complete the deferred A227 P4:
- task collections render cards;
- cards open Task Details;
- non-task result renders grounded answer;
- away/back = 0 new POST;
- editing input without Find does not change submitted result;
- Refresh re-runs the exact submitted NL query.

## P3 — Quality refresh isolation

Use DMS-380:
- top page refresh triggers only quality/missing/acceptance;
- Aging does not re-fire;
- same-task Проверить re-runs only task-quality group;
- normal response before 120s must not false-timeout.

## P4 — Aging exactness

Use DMS >7 and >15 days.
Refresh Oracle B first.
Require:
- Aging button only fires Aging;
- team-scoped bounded reads;
- exact key/count parity;
- rows show key/title/assignee/status/age_days;
- same criteria refresh performs a live re-read;
- no false zero / no fake source state.

## P5 — retained regression/audit

Recheck:
- LOCAL-NNNN CRUD/deadline/tags/priority/edit/delete;
- Overview cached revisit and refresh;
- Sprint DMS-SPRNT-3 exact;
- Releases typed source limitation;
- Team utilization;
- Platform V + OLAP/DataMarts;
- six backgrounds / responsive;
- 0 local factual reads;
- 0 tenant-wide scans;
- 0 mutations.

## Verdict

Exactly one:
- `AGENT_CORE_V4_PO_ACCEPTANCE_GREEN_A227R`
- `AGENT_CORE_V4_PO_ACCEPTANCE_RED_A227R`

GREEN -> recommend checkpoint `checkpoint/v4-po-acceptance-green-a227r`, then release hardening.
RED -> preserve first failing evidence and STOP.

Do not modify code.
