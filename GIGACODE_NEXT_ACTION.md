# GigaCode — Current Action

## ACTIVE: Assignment 223R — UI capability payload/state lineage re-gate

Role: QA/adversarial tester only. Do not modify production/frontend/backend/plugin/test/config code.

### Prior verdict
A223 = AGENT_CORE_V4_UI_STATE_LINEAGE_RED_A223

Blocking defect:
- Quality page read flat result.data instead of V4 capability payload under data.results[N].data
- user saw NaN/100 and incorrect READY instead of REWORK

Systemic finding:
- same payload-shape mismatch affected Overview, Sprints, Releases and Team, mostly as em-dash/empty data.

### Owner remediation
Commits:
- 9da38579e80682ebc326c3d4f22001e5461fe280 — shared getCapabilityData()
- 2317d3f28007c784528c7b91b35dc3fa7e59e59a — Overview unwrap
- dd71d630ee39ff41710d09858c10f9ec5d465913 — Team unwrap
- dbd9053ae68e4a149d5ac93b334f24007810e3fe — Quality unwrap + finite-number guards
- 56cbd3dfea2e0e73718c5bdd1d44e06d926f0d4a — Tasks/Sprints/Releases unwrap
- e84910a3b858d638783a889fbf1436a56ccfc0cb — Overview metrics aligned to actual payload keys

No backend/Core/planner/runtime/session change.

### P0 — static/build
1. Pull branch, clean worktree, record START_HEAD.
2. Diff from A223 report commit.
3. Prove remediation is frontend/docs only.
4. Run tsc --noEmit and vite build.
5. Run existing relevant e2e smoke.
6. Zero unexplained build/runtime errors.

### P1 — getCapabilityData contract
Validate shared helper against real captured V4 responses:
- flat legacy-compatible payload -> same object
- composed V4 response -> final business capability data
- resolver + business result -> business payload, not resolver payload
- empty/missing results -> {}
- no mutation of original response

Check state adapter now applies REAL_EMPTY classification to unwrapped capability data, not the outer results envelope.

### P2 — blocking Quality regression
Browser C, WMB-102.

Independent backend truth from A223:
- quality score = 85
- missing_elements = [acceptance_expectations]
- acceptance score = 0
- acceptance gaps non-empty

Require UI:
- Quality score 85/100
- Acceptance 0/100
- Пробелы = 1
- Decision = REWORK / Вернуть на доработку
- no NaN
- no READY
- no placeholder zero caused by missing path

Also test one task whose finite score path is incomplete/absent:
- no NaN/Infinity
- render em-dash / NOT RUN until all decision inputs are finite and source-backed

### P3 — Overview data-shape regression
Require real values from capability payload:
- active and completed metrics populated from source-backed overview payload
- blocked metric populated
- status/product cards populate when source-backed
- no use of nonexistent tasks_total
- Daily Brief rich rendering retained
- attention queue still state-safe

### P4 — Sprints
Use one source-ready sprint.

Require:
- scope/completed/velocity/predictability populated when backend provides them
- throughput/WIP/readiness populated from final capability payload
- risk queue exact vs backend payload
- no false "Риски не выявлены" caused by wrong nesting
- source-limited result still renders state panel, not zero

### P5 — Releases
Use:
- one known source-conditional release
- one source-ready release identity/search case where applicable

Require:
- nested payload is unwrapped correctly when present
- SOURCE_CONDITIONAL remains state panel, never fake 0/empty
- dependencies/blockers/risk queue exact when source-backed
- no pseudo forecast

### P6 — Team
Require:
- workload metrics populate from real nested payload
- active_tasks/WIP/blocked rows exact
- bottlenecks/distribution exact
- capacity still source-safe
- no hardcoded 40h
- competency/recommendation note and drawer behavior retained

### P7 — Tasks
Run:
- non-empty search
- source-proven empty search
- clarification case

Require:
- task grid uses unwrapped payload
- REAL_EMPTY only when source-proven
- clarification still state panel
- local-task and details drawers unaffected

### P8 — chat/V4 panel regression
Repeat:
- daily brief markdown/table
- competency recommendation table

Require:
- no raw markdown syntax
- structured V4ResultPanel rows still render
- evidence/feedback/clarification controls preserved

### P9 — audit
Require:
- 0 mutations
- 0 local factual fallback reads
- 0 tenant-wide broadening introduced by UI
- backend skill behavior unchanged from A222R2

### Verdict
Use exactly one:
- AGENT_CORE_V4_UI_STATE_LINEAGE_GREEN_A223R
- AGENT_CORE_V4_UI_STATE_LINEAGE_RED_A223R

If GREEN:
- recommend checkpoint/v4-ui-state-lineage-green-a223r
- next owner phase = visual design system + slide-derived page backgrounds
- do NOT start Learning Reviewer yet

If RED:
- first failing UI boundary only
- preserve screenshot + exact backend payload
- STOP

Do not modify code.
