# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_222R_TEAM_COMPETENCY_REGATE

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Commit/push only QA reports/artifacts.

## Retained baseline
Full functional checkpoint remains:
`checkpoint/v4-full-functional-green-a221r3@84b0ae28aa4c37b0e502f92f08738fab66dbd4f6`

A222 verdict:
`AGENT_CORE_V4_TEAM_COMPETENCY_RED_A222`

Confirmed A222 defects:
1. legitimate zero-overlap result could not satisfy completion contract;
2. YAML camelCase logins did not join production lowercase AS21 assignee logins, silently zeroing load.

## Owner remediation
Commits:
- `b1d0341ba4389a57712e9aeae33b42e47b3fe332`
- `3c436b32bf0b5fd6c2f7f0356ff5dfcc29bdd5c6`
- `2e770bf2183087728606450bca24733d542e4c6a`

### Functional change
Competency relevance is now derived only from source-backed task signals:
- task title;
- task description;
- task labels/tags;
- task components.

Declared competencies still come only from:
`task-api/config/team_members.yaml`

No competency level/seniority is inferred.

The matcher now returns:
- matched_competencies;
- matched_by_field;
- match_count;
- relevance_score;
- task_signals.

`relevance_score` is a deterministic TASK-TO-COMPETENCY relevance score, not an employee performance/quality score.

Field weights:
- labels/tags = 4
- components = 4
- title = 3
- description = 1

For each declared competency, only the strongest matching field contributes to score.

Assignee recommendation then orders by:
1. relevance_score desc;
2. match_count desc;
3. active_tasks asc;
4. WIP asc;
5. blocked asc;
6. login deterministic tie-break.

Load join is case-insensitive.

### Completion fix
- competency_match completion now uses scalar `match_count`;
- assignee_recommendation completion now uses scalar `candidate_count`;
- zero is a valid terminal value, mirroring the established A215F2 REAL_EMPTY-safe pattern.

## P0 — diff + architecture audit
1. Pull branch, record START_HEAD, clean worktree.
2. Diff from A222 report state.
3. Prove production delta limited to `wave_batch3.py`.
4. Prove no Core/planner/runtime/session-context change.
5. Prove no tenant-wide scan or new adapter route.
6. Confirm task model source fields `title/description/labels/components` are canonical source-backed fields.

Architecture drift => RED STOP.

## P1 — tests
Run:
- `tests/test_agent_core_v4_team_competency_source.py`
- `tests/test_agent_core_v4_batch3.py`
- relevant team/current-sprint suites
- planner signature parity
- registry/plugin suites
- focused full V4 regression

Require zero unexplained failures.

## P2 — zero-overlap completion re-gate
Re-probe A222 zero-overlap tasks:
- DMS-335 >=3 fresh sessions
- DMS-432 >=3 fresh sessions

Require:
- COMPLETED, not step-budget failure;
- `matches=[]` + `match_count=0` for competency_match where independent Oracle B proves no declared competency overlap;
- typed warning `no_declared_competency_match`;
- assignee recommendation: `candidates=[]`, `candidate_count=0`, recommendation=null and insufficient-evidence warning where applicable;
- zero fabrication.

## P3 — task-signal matching
Use independently selected source tasks that prove each field.

At minimum prove:
A. competency signal in TITLE;
B. competency signal in DESCRIPTION;
C. competency signal in LABEL/TAG;
D. competency signal in COMPONENT.

For every case:
- point-read the source task independently;
- record exact source title/description/labels/components;
- calculate expected declared-competency intersection from team_members.yaml;
- compare Agent candidate/member set exactly;
- verify `matched_by_field` identifies the correct source field;
- verify `relevance_score` follows documented deterministic weights.

Do not accept a candidate based on previous ownership/assignee history.

## P4 — mixed-signal ranking
Find or controlled-source-shape a task with multiple competency signals across title/description/labels/components.

Require:
- multiple declared competencies can contribute;
- tag/component signal outranks description-only signal under equal declared competency count;
- score is described as task relevance, never human quality/performance;
- no numeric competency level appears.

## P5 — load join re-gate
Re-probe DMS-380 recommendation >=5 fresh sessions.

Independent Oracle B:
- read current DMS sprint;
- derive exact active/WIP/blocked counts by case-insensitive canonical login.

Require:
- candidate load fields are non-zero where source proves load;
- exact per-candidate parity;
- lowercase AS21 login joins camelCase YAML login;
- recommendation order respects relevance then load/WIP/blocked;
- no tenant-wide scan.

## P6 — product and identity safety
- DMS task => DMS profiles only.
- OLP task => OLP profiles only.
- missing task => typed source limitation/not-found.
- invalid/missing team login must not silently become authoritative identity.
- no competency inferred from task assignee.

## P7 — Browser C
Test real UI for:
- competency match with non-empty match;
- zero-overlap competency match;
- assignee recommendation with real load;
- one label/component-driven example.

Require structured result without generic error.
Record current Team widget rendering defects separately; do not repair UI in this assignment.

## P8 — retained Team regression
Re-run:
- team.workload
- team.wip
- team.blocked
- team.capacity
- team.bottlenecks
- team.distribution
- member.time_spent representative case

Require A221R3/A222 parity allowing verified source drift.

## P9 — audit
Require:
- local factual task reads = 0;
- tenant-wide task scans = 0;
- mutations = 0;
- all task facts from bounded REAL AS21;
- competency facts from repository team source only.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_TEAM_COMPETENCY_GREEN_A222R`
- `AGENT_CORE_V4_TEAM_COMPETENCY_RED_A222R`

If GREEN:
- classify team.competency_match SOURCE_READY;
- classify team.assignee_recommendation SOURCE_READY;
- recommend competency-source checkpoint;
- next owner phase = UI widget/state/lineage remediation.

If RED:
- identify first failing boundary and STOP.

Do not modify code.
