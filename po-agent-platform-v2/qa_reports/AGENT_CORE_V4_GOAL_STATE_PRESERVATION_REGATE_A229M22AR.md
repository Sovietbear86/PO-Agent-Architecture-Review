# AGENT_CORE_V4_GOAL_STATE_PRESERVATION_REGATE_A229M22AR

**Verdict:** `AGENT_CORE_V4_GOAL_STATE_PRESERVATION_RED_A229M22AR`
**Classification:** `RED_CARRIED_OBSERVATION_CREDIT_GAP` — first failing boundary P2 (continuation completion).
**TESTED_HEAD:** `b18cf17c7455ee2662e8c83c65f5e2ac4bfacaf9` (owner fix `09e4394` allowlist strip + `f599c52` recursive sanitize + `b2dc119` real-card tests)
**Role:** QA only; zero production/test/config edits. STOP at first RED per spec.

## Executive summary

The A229M2.2A blocking defect is **CLOSED and proven on the real card**: the REAL AS21
`task.lookup` DMS-267 observation (raw row **8 899 B**, nested `source_data.swtr_attributes`
card) now compacts+strips to a **965 B** carried observation (< 8 192 B cap) and is retained
by M2/M4/C5 with exact canonical lineage, zero raw-card markers, no parent inference and no
cross-goal binding. P0/P1 are fully GREEN.

A new first failing boundary was then found one layer deeper in the continuation loop
(D-A229M2.2AR-1): carried observations restore the **planner** correctly (the spec-mandated
"no duplicate source reads for proven goals" was observed live), but they never enter the
response `data.results` that `check_goal_coverage` inspects, so the guard deterministically
re-marks the previously-proven goal as unproven — with a false user-visible claim — and the
multi-goal continuation structurally cannot reach COMPLETED unless the planner violates the
no-duplicate-read requirement by re-executing the proven goal every turn.

## P0 — formerly failing boundary: GREEN (real-card, non-artificial)

- Focused `tests/test_v4_goal_coverage.py`: **17/17** (incl. new
  `test_realistic_dms_lookup_raw_source_card_is_stripped_and_lookup_retained` and
  `test_unknown_raw_cards_not_carried_even_when_under_8kb`). Owner's new fixtures now use the
  real card shape (masking class addressed).
- Production `_build_internal_continuation` driven with the **live-captured REAL AS21**
  DMS-267 lookup (captured from the production adapter, includes `source_data.swtr_attributes`):
  - raw row **8 899 B** → carried **965 B** (≤ 8192), `carried_count=1` for M2, M4, C5;
  - leak scan over serialized state: `source_data`, `swtr_attributes`, `valueAsString`,
    `backgroundColor`, `swtr_code`, `parameters`, `ORDER` — **zero** occurrences;
  - canonical lineage retained: `task_key=DMS-267`, status `Resolved`,
    `status_category=completed_pending`, `assignee_id=Semavin.M.M`,
    `assignee_login=semavin.m.m`, `project_space=DMS`, `source=REAL_AS21`;
  - **no hierarchy absence inferred**: no `parent_chain`/parent invented; the real parent
    DMS-253 (oracle via `get_unit_links`: DMS-253 --decomposition--> DMS-267) remains an
    unproven goal until `task.hierarchy` executes;
  - M4 carries only the DMS-267 lookup row; no cross-goal binding to the person goal;
  - M1 person collection carries 463 B, 173/6-key sampling semantics unchanged.

## P1 — full regression + OFF controls: GREEN

- Full V4 blast `test_agent_core_v4*.py` + `test_v4*.py`: **287 passed / 0 failed**.
- Task API SWTR canonical/timestamps/partial: **16 passed**. Frontend `npm run build`: exit 0.
- **Core 6/6 byte-identical** to certified `6fb335d`: agent_core_v4 `52100ca1`,
  robust `3bdb4d09`, reliable `1f7562dc`, completion `cf75a6d6`, plugin registry `d82929d1`,
  llm/real `1cc10e12`. Registry: 13 plugins / 72 skills / 74 capabilities, 0 duplicates
  (canonical 54 unaffected).
- Delta audit `a65da3d..b18cf17`: `goal_coverage.py` (+31/−1), tests (+42/−1) — plugin/API
  allowlist + recursive trim only; no Core/planner/registry/UI changes; caps unchanged
  (6 observations / 8 192 B / REAL_AS21 provenance / fail-closed).
- OFF controls: both flags OFF → public COMPLETED untouched (guard not invoked).
  Guard ON / continuation OFF (`preserve_state=False`) → A229M2.1R contract exactly
  (NC + goal_coverage meta + warning, **no** continuation keys).
- Fail-closed boundaries: canonical-field oversize (20 517 B candidate of pure canonical
  `related_keys`) → carried=null + `v4_goal_continuation_state_unavailable`; >6 candidate
  observations → fail closed; nested raw cards (50 dicts + 50 list items, 5 KB description)
  → carried 1 803 B, **zero leaks**; unknown raw card under 8 KB → not carried.
- `_remember_clarification` chain: stored pending carries 1 compact REAL_AS21 lookup
  observation; public payload contains **no** `continuation_observations` after remember;
  `_prepare_query` restores observation + loaded skill + original-based combined query and
  consumes the pending token.

## P2 — ON isolated live gate (BOTH_ON agent on b18cf17): RED at continuation completion

Fresh REAL AS21 oracles: Kalachanov WMB = 6 keys (WMB-30482/30000/29890/29995/29830/29242);
Semavin DMS = 173; DMS-267 status Resolved, parent DMS-253 (get_unit_links).

- First batch hit an LLM 429 outage window (12× 429): M1/M2/M4 → typed
  `FAILED [v4_runtime_failure]` with zero fabricated completion; C5 → NC with
  `goal_continuation_pending=true` and **no** `state_unavailable` (former A229M2.2A live
  defect confirmed closed on the wire). Retry batch after cooldown:
  - **M1** `COMPLETED` (259.7 s): both goals executed exactly (Kalachanov WMB 6 keys ==
    oracle; Semavin DMS), public `results` present (legitimate COMPLETED), zero raw markers,
    zero continuation keys — guard inert when all goals proven.
  - **M2** NC `proven=[g2(lookup)] unproven=[g1(hierarchy)]`, pending, no state_unavailable.
  - **M4** NC `proven=[g2] unproven=[g1,g3]`, pending.
  - No duplicate proven-goal reads; all source calls bounded.
- Live TTL proof: a continuation attempted ~61 min after storage → typed
  `clarification_context_lost` (15-min TTL enforced end-to-end).
- Consumed token: replaying a used `clarification_id` → typed context_lost, state destroyed.
- Negative invented key `DMS-999999`: point read → typed
  `v4_planner_needs_clarification`; no fake completion, no fabricated hierarchy.
- Client injection surface: `query`, `session_id`, `clarification_id`,
  `clarification_option` only — observations are not client-injectable.
- State-machine security (offline, same code path): TTL 15 min ✓, expiry sweep on insertion
  ✓, 100-entry global bound with oldest eviction ✓, one-shot consumed token ✓, invalid
  option keeps state ✓, fresh query pops pending ✓.
- Audit (BOTH_ON session log): 0 local `/api/v1/tasks` reads, 0 task-api mutations, 0
  unscoped task-query (all 2 task-query calls assignee+space-scoped; 0 tenant scans).

### D-A229M2.2AR-1 (BLOCKING) — carried observations are never credited by the coverage guard

Tight-window live continuation (T2 sent 5 s after T1's NC, well inside TTL):

- T1: NC, `proven=[g2 task_lookup:DMS-267]`, question names the missing hierarchy goal.
- T2 (`clarification_id` + option "иерархию DMS-267"): planner state restored correctly —
  `loaded_skills=[task.lookup, task.hierarchy]`; **only `task.hierarchy` executed**
  (source-delta: relations/get_unit_links +1, hierarchy-handler own unit read +1,
  **files read +0 ⇒ `task.lookup` was NOT re-executed** — exactly the spec's
  "no duplicate source reads for proven goals").
- Yet T2 response = `NEEDS_CLARIFICATION` with the **false** claim
  «Не удалось подтвердить: task_lookup: DMS-267» (the goal was proven in T1 and carried),
  `goal_coverage={requested:3, proven:[g1,g3], unproven:[g2]}`.

Root cause (code-exact, deterministic — not planner stochasticity):

1. `AgentCoreV4Runtime.process` seeds restored `resume_observations` into the planner
   `observations` list only (`agent_core_v4.py:1155-1174`); `full_results` — the rows
   serialized into `data.results` — is appended **only for capabilities executed in this run**
   (`agent_core_v4.py:1303`).
2. `check_goal_coverage` derives proof exclusively from `_terminal_results(response)` =
   `data.results` (`goal_coverage.py`). Restored REAL_AS21 observations are invisible to it.
3. Deterministic offline replay of the exact T2 shape reproduces the live outcome byte-exact
   (`proven=[g1,g3] unproven=[g2]`, identical Russian question). Counter-proof: injecting the
   carried lookup row into `results` flips coverage to `proven=[g1,g2,g3]`, COMPLETED path
   clear — the guard's own matcher already accepts the carried row shape.

Consequence: multi-goal continuation dead-loops at the completion frontier — each turn can
prove only what it re-executes; the carried proven goal is re-declared unproven. The only way
to COMPLETED is for the planner to re-execute proven goals on every continuation turn
(duplicate source reads the spec explicitly forbids), making the feature functionally
unreachable for its intended flow.

**Proposed owner fix (api/v1 seam only, Core untouched):** pass the already-validated
`continuation.observations` from `_prepare_query` into `guard_completed_goal_coverage` /
`check_goal_coverage` as trusted prior-run evidence (credit-only; do not surface them in
public `data.results`), and add a **two-turn non-mocked regression** (T1 NC → T2 executes
only the missing goal → COMPLETED crediting the carried lookup). Caps/provenance/fail-closed
semantics unchanged.

## OPEN blockers (deployment)

1. **D-A229M2.2AR-1** — carried-observation credit gap (above). Gate-blocking.
2. **Session authentication/ownership** — unchanged known blocker: `session_id` is
   client-chosen and unauthenticated service-wide; any client that observes a
   `clarification_id` + session can consume the continuation. Tested fail-safe behavior is
   correct (typed context-lost on wrong session/cid/expiry/consumption), but the feature is
   **not** deployment-secure without authenticated session ownership.
3. Environmental (non-code): api.ai.sbt LLM 429 rate-limit windows — typed fail-closed,
   re-run on cooldown; use ≥75-120 s spacing for multi-turn matrices.

## Services after QA

- agent 8004 PID 62483 on `b18cf17`, **both goal flags false** (public default restored),
  healthy `v4_ready=true`; task-api 8241; MCP-SWTR 3000.
- QA artifacts (untracked): `/private/tmp/qa229m22ar_*` (p03/p1/security/tight scripts +
  JSON evidence), `qa_229m22a_agent.sh` (QA launcher).

## Verdict

`AGENT_CORE_V4_GOAL_STATE_PRESERVATION_RED_A229M22AR` — P0 (former RED) and P1 GREEN;
first failing boundary P2 continuation completion (D-A229M2.2AR-1). Per spec: STOP; no
checkpoint, no feature-default flip, no A229M2.2B until owner review.
