# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_104_SPRINT_SNAPSHOT_SOURCE_PROOF`

## Role boundary
You are QA/research executor only. **Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

The history block is structurally at 51/54. We now target the next two unavailable skills:
1. `sprint-carryover`
2. `sprint-scope-change`

Both currently require the missing source fact `sprint_snapshots`. Assignment 101 suggested that the authoritative sprint-start baseline may be reconstructable from existing REAL task-history events, but that claim is not yet proven strongly enough for owner implementation.

Do not accept a guessed `/snapshot` endpoint and do not accept current sprint membership as a historical baseline.

## Goal
Prove, using REAL AS21/SWTR data, whether a deterministic authoritative sprint-start membership snapshot can be reconstructed for at least one validated sprint. The output must be implementation-grade evidence for the owner.

Target if proof succeeds: owner can implement `sprint_snapshots` and move readiness from `51/54` to `53/54`.

## Phase 0 — provenance and live-source gate
1. Pull current branch; record exact HEAD and clean tracked worktree.
2. Fresh production task-api + REAL AS21/SWTR.
3. Establish at least 3 successful REAL reads in this run, including one sprint scope and one task history read.
4. fake/mock/frozen authoritative calls = 0; AS21 writes = 0.
5. concurrency = 1; timeout >=180 s for history-heavy calls; retry timeout/502/503 up to 2 times with 20–30 s backoff.

If live source cannot be established, stop `BLOCKED_BY_ENVIRONMENT`.

## Phase 1 — recover exact business definitions
Recover from repository code/contracts/tests the exact definitions of:
- `sprint-carryover`;
- `sprint-scope-change`.

For each, state exact required sets and formula. Do not infer from skill name alone.

At minimum determine whether the metric requires:
- committed task set at sprint start;
- current task set;
- tasks added after start;
- tasks removed after start;
- previous sprint membership;
- completion state at a particular boundary.

## Phase 2 — prove authoritative sprint timing
Select at least one REAL sprint with live scope. Prefer a sprint for which start/end timestamps can be independently obtained now.

Trace the actual task-api/MCP-SWTR path that provides sprint metadata. Capture raw payload and prove:
- sprint ID;
- start timestamp;
- end timestamp if available;
- space/project;
- status if available.

If only current-sprint metadata is exposed, say so explicitly. Do not use metadata from a different sprint as proof for the target sprint.

Classification for sprint timing:
- `TIMING_AVAILABLE_FOR_TARGET_SPRINT`
- `TIMING_ONLY_FOR_CURRENT_SPRINT`
- `TIMING_NOT_AVAILABLE`

## Phase 3 — prove raw sprint-membership history events
The existing PO Agent `get_task_history()` normalizes only workflow status transitions, so it is insufficient by itself for sprint-membership reconstruction.

Inspect and independently call the underlying REAL history endpoint/tool in a way that preserves raw events. For valid tasks, search specifically for sprint-assignment field changes such as `scrum_board_plugin_sprint` or equivalent.

Capture at least one real membership event if one exists:
- task key;
- changed_at;
- field code;
- old sprint value;
- new sprint value;
- actor if present.

Do not fabricate or infer an event from current task attributes.

Classify raw membership history:
- `MEMBERSHIP_EVENTS_PROVEN`
- `HISTORY_EXISTS_NO_MEMBERSHIP_EVENTS_IN_SAMPLE`
- `RAW_HISTORY_NOT_EXPOSED`
- `BLOCKED_BY_ENVIRONMENT`

## Phase 4 — reconstruct one sprint baseline if possible
Only if Phase 2 provides authoritative target sprint start time and Phase 3 provides sufficient membership events, reconstruct the target sprint state at start.

Use the event stream and current membership to derive exact sets:
- `current_task_keys`;
- `committed_at_start_task_keys`;
- `added_after_start_task_keys`;
- `removed_after_start_task_keys`.

Show the deterministic reverse/forward reconstruction algorithm and apply it to REAL task keys. Exact sets are required, not just counts.

Independently validate internal consistency:
`committed_at_start + additions - removals == current_scope` (set algebra, with direction documented).

If full reconstruction cannot be proven, do not invent a baseline. State the exact missing raw input.

## Phase 5 — carryover source proof
Recover the repository definition of carryover and determine whether the proven data is enough.

If previous sprint membership is required, prove how it is obtained for the same tasks/sprints. If unavailable, classify the exact gap.

Allowed classification:
- `CARRYOVER_DERIVABLE_NOW`
- `CARRYOVER_NEEDS_PREVIOUS_SPRINT_MEMBERSHIP`
- `CARRYOVER_NEEDS_MISSING_TIMING`
- `CARRYOVER_SOURCE_GAP`

## Phase 6 — scope-change source proof
Determine whether the reconstructed start baseline + event stream is enough to compute scope-change exactly.

If yes, independently calculate the expected metric and exact added/removed sets for the target sprint.

Allowed classification:
- `SCOPE_CHANGE_DERIVABLE_NOW`
- `SCOPE_CHANGE_NEEDS_MISSING_TIMING`
- `SCOPE_CHANGE_NEEDS_RAW_MEMBERSHIP_EVENTS`
- `SCOPE_CHANGE_SOURCE_GAP`

## Phase 7 — owner implementation contract
Do not change code. Produce the smallest owner implementation plan with exact modules and normalized schema.

Preferred contract shape if evidence supports it:
```text
get_sprint_membership_snapshot(sprint_id, space?) -> {
  sprint_id,
  started_at,
  current_task_keys,
  committed_at_start_task_keys,
  added_after_start_task_keys,
  removed_after_start_task_keys,
  evidence
}
```

Specify:
- which existing REAL endpoint/tool supplies each field;
- whether a new task-api facade endpoint is actually needed;
- pagination/retry behavior;
- fail-closed behavior when timing or raw events are unavailable;
- whether `SourceFact.SPRINT_SNAPSHOTS` can honestly be advertised after implementation;
- projected readiness (`51/54 -> 52/54` or `53/54`) based only on proven contracts.

## Phase 8 — no hardcoding / no learning
Verify no production IDs/answers are proposed for hardcoding and no Learning Loop policy is created/promoted/changed.

## Source integrity
Report exact numeric counts from this run only:
- successful REAL sprint reads;
- successful REAL task/history reads;
- successful raw membership-event reads;
- HTTP 500;
- HTTP 502/503;
- timeouts/retries;
- fake/mock/frozen = 0;
- AS21 writes = 0.

## Output
Create only QA/research artifacts under `po-agent-platform-v2/qa_reports/`.

Primary report:
`po-agent-platform-v2/qa_reports/SPRINT_SNAPSHOT_SOURCE_PROOF_104.md`

Allowed final verdicts:
- `SPRINT_SNAPSHOT_DERIVATION_PROVEN_READY_FOR_OWNER`
- `PARTIAL_SPRINT_SNAPSHOT_PATH_PROVEN`
- `UPSTREAM_SPRINT_HISTORY_GAP_PROVEN`
- `BLOCKED_BY_ENVIRONMENT`

GREEN-like proof is allowed only when target-sprint timing + raw membership events + deterministic baseline reconstruction are all demonstrated on REAL data. Commit/push only allowed QA/research artifacts, report SHA, then STOP.