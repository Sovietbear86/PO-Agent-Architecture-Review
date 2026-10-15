# GigaCode — Current Action

## ACTIVE: A229M2.2F — Safe Continuation feasibility (DESIGN / FORENSICS ONLY)

**Role: independent QA / architecture investigator. NO production, test, config or frontend code edits.**
Do not modify Agent Core, runtime, planner, plugin handlers, API, settings, tests or feature flags. This gate decides whether continuation can safely re-use validated observations through the existing V4 dialogue seam; it does not implement it.

### Context and invariants

- A229M2.1R independent verdict: `AGENT_CORE_V4_GOAL_COVERAGE_STAGE1_GREEN_A229M21`; TESTED_HEAD `a6f3fd4`, report commit `025679a`. 282/282 V4, 27/27 Task API, frontend build green; Core 6/6 byte-identical against checkpoint `6fb335d`.
- A229M2.1 stage 1 is a **conservative guard**, NOT general language understanding or multi-goal execution.
- `PO_AGENT_V4_GOAL_COVERAGE_GUARD=false` and `PO_AGENT_V4_SYNTHESIS_ELISION=false` must remain default OFF.
- Earlier clarification continuation already supports `resume_loaded_skills`, `resume_observations` and `required_completion_skills`; determine exact contracts, provenance, lifecycle and limits rather than assuming they support arbitrary multi-goal state.
- Existing goal guard currently deletes public `data.results`/evidence on incomplete coverage. **Do not confuse stripped public payload with retaining safe source-proven internal observations.** Existing `_remember_clarification` stores state only from dedicated `_agent_core_v4.continuation_observations` etc. Verify whether goal guard actually supplies this state; do not invent resume guarantees.
- No new checkpoints and no Core modifications.

### P0 — baseline & architecture map

1. Pull branch; record HEAD, clean worktree, current A229M2.1R report and core 6 hashes.
2. Run focused goal coverage/clarification tests + relevant full V4/Task API regression; require no new baseline RED.
3. Read actual implementations with line locations:
   - `api/v1/__init__.py`: `PendingClarification`, `_remember_clarification`, `_prepare_query`, `_guard_completed_constraint_coverage`, `guard_completed_goal_coverage`, session TTL and failure cleanup;
   - `harness/contracts.py`: `HarnessRequest`, `HarnessResponse`, statuses and semantics;
   - `harness/agent_core_v4.py`, `agent_core_v4_completion.py`, reliable/robust wrappers: actual `V4Observation`, restored observation validation, completion frontier;
   - `api/v1/goal_coverage.py`: detector, `check_goal_coverage`, metadata/payload stripping;
   - UI clarification continuation, result state and evidence exposure boundaries.
4. Produce a sequenced diagram of current request -> guard -> pending clarification -> response -> follow-up -> restored execution, and identify which variables actually survive.

### P1 — concrete data-survival and security proof

For scenarios M1 (Kalachanov WMB + Semavin DMS), M2 (lookup DMS-267 + hierarchy), M4 (lookup + hierarchy + person collection), C5 (lookup + related tasks):
- Replay independently source-proven A229M1 observations, with exact real capability names and argument/data shapes.
- Trace what is kept before `data.results` is stripped and after `_remember_clarification`; determine if successful goal observations survive securely for continuation.
- Confirm provenance (`REAL_AS21`), source completeness, immutable parameters, canonical identity, and distinction between `REAL_EMPTY` and `SOURCE_UNAVAILABLE`.
- Check that copying prior observations cannot be manipulated via browser request, session collision, stale TTL, other user/tenant, or stale source. Verify existing controls or record missing ones.
- Evaluate token/data size bounds, truncation, persistence beyond process restart, concurrent requests in one session and whether clarification ID enforces ownership.
- **Do not** reuse observations whose source lineage or binding cannot be proven. Do not claim state survives if code drops it.

### P2 — supported continuation options (NO IMPLEMENTATION)

Evaluate three alternatives:
A. Reuse existing `resume_observations` plus pending clarification (strict validated facts), with per-goal IDs and remaining-goal completion requirements.
B. A bounded **API-side orchestrator** using existing governed capabilities/skills, preserving executed goal evidence and running missing goals only; assess legality of invoking underlying capability handlers without Core/skill governance bypass.
C. A separate sidecar execution orchestrator for deep multi-goal work, sharing governed tool and source plane, but no new planner Core.

For each provide:
- exact file/API seams;
- ability to execute missing goals rather than merely saying they are missing;
- policy to avoid rerunning already proven goals and prevent stale evidence;
- mechanism to request clarification for genuinely ambiguous missing goals;
- retry budget, time/LLM budget and 429 handling;
- no source/tenant leakage; read-only/permission model;
- rollback flag (OFF default);
- whether Core files change (preference ZERO).
- risk of false positives from current conservative lexical goal detector and practical mitigation.

Explicitly distinguish:
`NEEDS_CLARIFICATION` for genuine ambiguity;
`PARTIAL` (if semantically supported) for clearly understood but unexecuted goals;
`FAILED`/source-unavailable for infrastructure failure.
Do not ask user to clarify information that was already unambiguous merely because planner skipped an action.

### P3 — counterfactual end-to-end replay

Using captured A229M1 traces only, produce end-to-end proposed execution for:
1. M1: first person WMB proven, second person DMS missing;
2. M2: lookup proven, hierarchy missing (DMS-253 parent cannot be denied based on lookup);
3. M4: one of three proven, two missing;
4. C5: lookup proven, link traversal missing;
5. M5: comparison DMS vs OLP (one analytical goal needing two source corpora);
6. C1/C3 composed-filter single-goal controls (must remain ONE goal, never split);
7. ambiguous underspecified request (clarification required).

Per case specify exact typed `RequestGoals`, immutable constraints, goal-to-capability mapping, source-backed evidence retained, missing-goal execution sequence, completion and merged result eligibility, and fallback if a step cannot execute.
Count model calls, source calls and bytes retained; no result fabrication.

### P4 — explicit feasibility verdict and owner implementation plan

Answer with evidence:
1. Can the existing continuation carry validated observations across turns without changes to Core and without duplicating source reads?
2. Can it **guarantee** all missing goals are attempted/completed, or does completion remain per-skill with single-terminal convergence?
3. If a plugin/API sidecar is needed, can it call the same governed capability registry safely, preserving contracts/source/auth?
4. What exact missing checks (session binding, fresh evidence, typed goal extraction, bounded retry, negative facts, partial status) block implementation today?
5. What is the smallest *reversible* out-of-Core change that permits M1+M2 safe continuation first, with M4/C5/M5 deferred until proven?

Recommend exactly one:
- `REUSE_CLARIFICATION_CONTINUATION` (only if proven end-to-end);
- `BOUNDED_API_ORCHESTRATOR`;
- `ISOLATED_SIDECAR`;
- `NO_SAFE_OUT_OF_CORE_PATH`.

Propose an owner implementation specification (files and tests) but **do not implement it**. Include A/B oracle, browser, restart, recovery, privacy, concurrency and regression gate, 0 false completed and 0 unauthorized mutations.

### P5 — stop rule / report

GREEN = `AGENT_CORE_V4_SAFE_CONTINUATION_FEASIBILITY_GREEN_A229M22F` ONLY if architecture seams are measured, alternatives compared, risks explicit and one valid implementation boundary specified; it does **NOT** certify working multi-intent continuation.

RED = `AGENT_CORE_V4_SAFE_CONTINUATION_FEASIBILITY_RED_A229M22F` when no safe boundary is established or baseline is broken; preserve first failing boundary and STOP.

Commit only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_SAFE_CONTINUATION_FEASIBILITY_A229M22F.md`.

Return TESTED_HEAD, REPORT_COMMIT, Core hashes, evidence state-survival table, recommended option, exact owner next action and residual open risks. No production code edits, flag flips or new checkpoint.
