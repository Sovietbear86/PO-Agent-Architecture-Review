# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_096A_EXACT_SPRINT_BASELINE_PROOF`

## Role boundary — mandatory
You are QA/tester only. **Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

Do not fix anything. Do not start another broad marathon.

## Why 096A exists

Owner code review after Assignment 096 found a material contradiction that must be resolved before any production fix:

1. `skill_catalog.py` marks both `sprint-carryover` and `sprint-scope-change` as `implemented`.
2. `SprintIntelligenceCapabilities` currently has no `carryover()` or `scope_change()` implementation.
3. The executable `HarnessRuntime` capability registry does not register `sprint.carryover` or `sprint.scope_change`.
4. The authoritative comprehensive test plan explicitly says carryover/scope-change require an authoritative sprint commitment/scope snapshot and that missing sprint snapshot must result in unavailable behavior, not an invented metric.
5. Assignment 096 nevertheless classified both as `DETERMINISTIC_CALCULATION` defects and asserted that current task data was sufficient, but the report did not provide the exact committed-scope baseline, source route/fields, independent formula, or expected numeric value.

Therefore **do not assume the fix is a metric formula change**. First prove the exact source/input contract.

## Scope — only two skills
- `sprint-carryover`
- `sprint-scope-change`

## Phase 0 — provenance
1. Pull current branch and record exact HEAD.
2. Record `git status --short`; production files must remain clean.
3. Confirm production `task-api` + REAL AS21(SWTR).
4. fake/mock/frozen authoritative calls = 0.
5. AS21 writes = 0.
6. Use a known-valid REAL sprint, preferably `DMS-SPRNT-2` if still valid.

## Phase 1 — prove executable implementation state

From the exact tested HEAD, capture concrete code evidence for each skill:
- catalog entry and status;
- capability ID;
- whether an executable handler exists;
- whether the handler is registered in the production runtime;
- whether deterministic routing/semantic dispatch can reach that handler;
- exact runtime behavior when invoked.

Explicitly reconcile:
`catalog status = implemented`
vs
`handler/registry availability`.

If a catalog skill is marked implemented but has no executable registered handler, classify this separately as:
`IMPLEMENTATION_CONTRACT_MISMATCH`.

Do not call that `DETERMINISTIC_CALCULATION` unless an actual calculation function is reached and returns an incorrect result.

## Phase 2 — recover authoritative metric semantics

For each metric, state the exact business definition and required inputs.

### sprint-carryover
At minimum determine whether the intended metric is based on:
- committed scope at sprint start;
- tasks carried from previous sprint;
- unfinished committed tasks at sprint end/current time;
- another explicitly documented definition.

### sprint-scope-change
At minimum determine whether the intended metric is based on:
- committed scope at sprint start;
- tasks added after sprint start;
- tasks removed after sprint start;
- effort-weighted or task-count semantics;
- another explicitly documented definition.

Use repository product/test contracts as the definition source. Do not invent a formula from current task list alone.

For each required input, mark `REQUIRED / OPTIONAL / NOT_REQUIRED`.

## Phase 3 — independent REAL source inventory

Independently query REAL AS21/SWTR/task-api and prove whether the following authoritative facts are actually available for the selected sprint:
- current sprint scope exact task-key set;
- sprint start timestamp;
- sprint end timestamp/status where applicable;
- committed scope exact task-key set at sprint start;
- membership/change history or equivalent event stream;
- tasks added after sprint start;
- tasks removed after sprint start;
- previous-sprint membership/carryover evidence;
- effort/story-point baseline if the contract is effort-weighted.

For every fact, provide:
- exact endpoint/tool/read path;
- source field(s);
- example value/count/key set summary;
- authoritative vs derived status.

A current task list is NOT proof of a historical commitment baseline.

## Phase 4 — exact Oracle calculation proof

Only if all required authoritative inputs exist, independently calculate both metrics without using Harness metric code.

Report exact reproducible formulas and values.

For carryover include at minimum:
- committed baseline key set/count;
- carryover/unfinished/carried key set according to the proven definition;
- numerator/denominator;
- expected exact value.

For scope-change include at minimum:
- committed baseline key set/count;
- added key set/count;
- removed key set/count;
- numerator/denominator or exact count semantics;
- expected exact value.

If required authoritative inputs do NOT exist, do not fabricate expected values. Classify:
`SOURCE_CAPABILITY_UNAVAILABLE`.

## Phase 5 — reclassify FIRST_FAILING_BOUNDARY

For each skill choose exactly one evidence-backed classification:

- `DETERMINISTIC_CALCULATION_DEFECT_PROVEN`
  - handler exists and is reached;
  - all required authoritative inputs exist;
  - Oracle independently derives an exact expected value;
  - product calculation produces a different exact value.

- `IMPLEMENTATION_CONTRACT_MISMATCH`
  - catalog promises implemented behavior but production handler/registration is absent or unreachable.

- `SOURCE_CAPABILITY_UNAVAILABLE`
  - authoritative snapshot/history required by the metric is not exposed by current production source contract.

- `MIXED_IMPLEMENTATION_AND_SOURCE_GAP`
  - executable implementation is missing/incomplete AND the authoritative inputs required for a correct implementation are also unavailable.

- `AB_PASS`
  - current implementation is executable and matches independently derived authoritative result.

Do not reuse the Assignment 096 boundary label without new evidence.

## Phase 6 — desired fail-closed behavior

If the source baseline is unavailable, determine from current product/test contracts the correct production response contract:
- typed unavailable/source-capability-unavailable;
- warning/evidence expectations;
- whether the skill should remain catalog `implemented`, become source-not-ready/blocked, or be executable but return typed unavailable.

Do not change code. Give an owner recommendation only.

## Source integrity
Record:
- HTTP 500;
- HTTP 502 + endpoint mapping;
- timeouts/retries;
- REAL AS21 reads;
- fake/mock/frozen authoritative calls = 0;
- AS21 writes = 0.

Use >=120 s timeout; 40–60+ s source latency is normal.

## Output
Create only:
`po-agent-platform-v2/qa_reports/SPRINT_BASELINE_CONTRACT_PROOF_096A.md`

The report must include:
- exact commands and tested HEAD;
- executable implementation/registration proof;
- repository contract evidence;
- REAL source fact inventory;
- exact key sets/formulas/expected values if calculable;
- explicit proof when snapshot/history is unavailable;
- corrected FIRST_FAILING_BOUNDARY classification for each skill;
- exact minimal owner-fix recommendation, but no code;
- source-integrity counters;
- final verdict.

Allowed final verdicts:
- `DETERMINISTIC_CALCULATION_DEFECTS_PROVEN`
- `IMPLEMENTATION_CONTRACT_MISMATCH_PROVEN`
- `SOURCE_CAPABILITY_UNAVAILABLE`
- `MIXED_IMPLEMENTATION_AND_SOURCE_GAP`
- `AB_PASS`
- `BLOCKED_BY_ENVIRONMENT`

Commit and push only the allowed QA report, verify it exists in remote HEAD, report final SHA and STOP.

Do not start any later assignment.