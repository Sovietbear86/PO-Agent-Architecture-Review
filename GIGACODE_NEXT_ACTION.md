# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_222_TEAM_COMPETENCY_SOURCE_GATE

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT start UI remediation.
Commit/push only the QA report.

## Frozen baseline
Full functional V4 baseline:
- checkpoint: `checkpoint/v4-full-functional-green-a221r3`
- SHA: `84b0ae28aa4c37b0e502f92f08738fab66dbd4f6`
- canonical matrix 54/54 GREEN
- composition 24/24 GREEN
- Browser C 54/54 PASS

## Owner implementation
Commits:
- `e7d9af437e54d6508efd1e1b752122f053e8019d`
- `d8bd40b52c6930676b5f76f35ad0d0751883bf54`

Affected skills only:
1. `team.competency_match`
2. `team.assignee_recommendation`

No planner/runtime/session-context changes.

## Source truth
Repository competency source is now authoritative for declared competency evidence:

- `task-api/knowledge/team/competencies.md`
- `task-api/knowledge/team/team.md`
- `task-api/config/team_members.yaml`
- loader: `po-agent-platform-v2/src/po_agent/config/real_team.py`

Important semantics:
- competencies are explicit declarations only;
- numeric competency levels/seniority are NOT source-backed and must not be invented;
- product membership must be respected;
- task facts come from bounded REAL AS21 point reads;
- current operational load comes only from bounded current-sprint membership;
- legacy `search_tasks("")` tenant-wide path is forbidden.

## Phase 0 — architecture invariant
1. Pull branch, record START_HEAD and clean worktree.
2. Diff from `checkpoint/v4-full-functional-green-a221r3`.
3. Prove owner production changes are limited to:
   - `wave_batch3.py`
   - focused tests/docs
4. Zero Agent Core/planner/runtime/session-context changes.
5. Zero tenant-wide scan added.
6. Full registry/plugin discovery unchanged except skill behavior/source classification.

Architecture drift => RED.

## Phase 1 — focused tests
Run:
- `tests/test_agent_core_v4_team_competency_source.py`
- `tests/test_agent_core_v4_batch3.py`
- relevant team/current-sprint suites
- planner signature parity
- plugin registry suites

Then relevant full V4 regression.

Zero unexplained failures.

## Phase 2 — source integrity
Independently read:
- `task-api/config/team_members.yaml`
- `task-api/knowledge/team/competencies.md`
- `task-api/knowledge/team/team.md`

Require:
- identities/logins are consistent;
- competency lists used by runtime are explicitly present;
- no numeric competency level is inferred;
- no person outside the requested product is considered.

Record exact source version/SHA.

## Phase 3 — team.competency_match
Use real tasks from DMS and OLP, including:
- `DMS-380`
- at least one Go/DataMarts-oriented task
- at least one OLAP/frontend or Java-oriented task if source-backed
- one task with weak/no declared competency overlap

Run >=3 NL variants per representative case:
- "кто подходит по компетенциям для DMS-380"
- "какие специалисты подходят для задачи DMS-380"
- "competency match for DMS-380 in DMS"

Require:
- bounded task point read;
- repository team source only for competency evidence;
- exact declared competency/profile evidence in result;
- no tenant-wide task scan;
- no fabricated levels;
- no employee-performance language;
- if no overlap: valid empty/insufficient-evidence result, not fabricated match.

## Phase 4 — team.assignee_recommendation
Use same representative tasks.

Require trajectory:
- resolve space/task;
- one bounded task point read;
- bounded current-sprint lookup + sprint membership;
- repository declared competency source;
- recommendation candidates sorted deterministically by:
  1. declared competency overlap descending;
  2. current active-task load ascending;
  3. WIP ascending;
  4. blocked ascending;
  5. login deterministic tie-break.

Require:
- no `search_tasks("")`;
- no tenant-wide source route;
- no capacity/competency value invented;
- result is operational assignment recommendation, not employee quality score.

## Phase 5 — identity/product filters
Test:
- DMS task => only profiles with DMS in `products`;
- OLP task => only profiles with OLP in `products`;
- person with missing/invalid login must not silently become authoritative AS21 identity;
- explicit task not found => typed source limitation/not-found behavior.

## Phase 6 — Browser C
Real UI:
- competency match for DMS task;
- assignee recommendation for DMS task;
- one OLP case.

Require:
- structured Team result visible;
- declared competencies shown as evidence;
- current load shown separately from competency evidence;
- no "SOURCE_CONDITIONAL because no competency source" message;
- no generic V4 ERROR.

## Phase 7 — retained Team regression
Re-run:
- team.workload
- team.wip
- team.blocked
- team.capacity
- team.bottlenecks
- team.distribution
- member/time-accounting representative case

Require A221R3 parity.

## Phase 8 — audit
Require:
- local factual task reads = 0;
- tenant-wide task scans = 0;
- mutations = 0;
- competency config reads are repository/config source reads, not factual AS21 fallback;
- task facts always come from bounded REAL AS21 reads.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_TEAM_COMPETENCY_GREEN_A222`
- `AGENT_CORE_V4_TEAM_COMPETENCY_RED_A222`

If GREEN:
- classify `team.competency_match` = SOURCE_READY;
- classify `team.assignee_recommendation` = SOURCE_READY;
- recommend immutable small competency-source checkpoint;
- next owner phase = UI widget/state/lineage remediation.

If RED:
- identify first failing boundary and STOP.

Do not modify code.
