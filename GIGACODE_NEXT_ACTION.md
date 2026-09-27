# GigaCode — Current Action

## ACTIVE: Assignment 222R2 — competency signal plumbing re-gate

Role: QA/adversarial tester only. Do not modify production/frontend/plugin/test/config code.

### Prior state
A222R verdict: AGENT_CORE_V4_TEAM_COMPETENCY_RED_A222R.

Closed already:
- zero-overlap completion;
- case-insensitive load join.

Sole blocker:
REAL AS21 exposes task labels/components, but the production adapter dropped them before canonical Task, so competency matching saw empty labels/components.

### Owner fix
Commits:
- 16c0d77ed90c510690215f7469c5cb2433d8c5bf
- bd3c81cc50addb42bcef78d5bbf1235de4536d33
- f9fb1594b4bfd2986c754a3118a8bdbae88f1718
- 66cfa5a3d353fd34372b5178dd3d2fe0e2d2f5e6

Changes:
- source label -> Task.labels
- source sber_component -> Task.components
- raw attributes and normalized swtr_attributes both decoded
- hardened point-read mapper preserves same fields
- focused regression added
- no Agent Core/planner/runtime/session-context change

### P0 — diff/tests
1. Diff from A222R report state.
2. Prove production delta is adapter plumbing only.
3. Run:
   - test_agent_core_v4_task_signal_plumbing.py
   - test_agent_core_v4_team_competency_source.py
   - test_agent_core_v4_batch3.py
   - relevant adapter/source suites
   - planner signature parity
   - relevant full V4 regression
4. Zero unexplained failures.

### P1 — source parity
Independently point-read:
- DMS-408
- OLP-3339
- OLP-3079
- DMS-380

Require canonical Task parity for labels/components.

If source unchanged:
- DMS-408 labels include AQA and DataMarts server
- OLP-3339 components include OLAP
- OLP-3079 components include OLAP
- DMS-380 labels include Lineager and AQA

### P2 — competency signal re-gate
Fresh sessions >=3 each:
- DMS-408 label-driven DataMarts
- OLP-3339 component-driven OLAP
- OLP-3079 component-driven OLAP
- DMS-344 title-driven control
- DMS-380 description-driven control

Require:
- task_signals labels/components reflect source
- matched_by_field identifies the real source field
- weights remain label/component=4, title=3, description=1
- exact candidate set vs independent Oracle B
- no competence inferred from assignee/history

If source unchanged, expected A222R deltas should close:
- DMS-408 DataMarts relevance score 7, not 6
- OLP-3339/OLP-3079 OLAP relevance score 4, not 3

### P3 — retained regressions
Re-run compactly:
- DMS-335 zero-overlap >=3
- DMS-432 zero-overlap >=3
- DMS-380 recommendation >=5 with exact load/WIP/blocked parity
- team workload/WIP/blocked/bottlenecks/distribution
- representative member.time_spent

### P4 — Browser C
Run:
- label-driven competency match
- component-driven match
- zero-overlap
- recommendation with current load

Log rendering defects only; do not repair UI.

### P5 — audit
Require:
- 0 local factual reads
- 0 tenant-wide scans
- 0 mutations
- label/component facts only from bounded REAL AS21
- competency facts only from repository team source

### Verdict
Use exactly one:
- AGENT_CORE_V4_TEAM_COMPETENCY_GREEN_A222R2
- AGENT_CORE_V4_TEAM_COMPETENCY_RED_A222R2

If GREEN: recommend small competency-source checkpoint; next owner phase = UI widget/state/lineage remediation.
If RED: report first failing boundary and STOP.
