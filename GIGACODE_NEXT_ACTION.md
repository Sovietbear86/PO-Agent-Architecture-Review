# GigaCode — NEXT ACTION

## A229M2.2B-D — Bounded Missing-Goal Execution: DESIGN GATE

**Your role: independent QA / architecture analyst ONLY. Do NOT change production code, tests, settings, prompts, registry, UI or Agent Core. No checkpoint. Stop on first baseline regression.**

### Context and immutable requirements
- Last certified result: `AGENT_CORE_V4_GOAL_STATE_PRESERVATION_GREEN_A229M22AR2` (TESTED_HEAD `1cd6446`, report commit `8697e68`). 290/290 V4, 16/16 Task API, three 2-turn REAL AS21 M2 continuations GREEN.
- Existing `goal_coverage` and `goal_continuation` flags both **OFF by default**, synthesis elision OFF; do not flip defaults.
- Core 6/6 must remain byte-identical to `checkpoint/v4-complex-task-clarification-green-a229f3r@6fb335d`.
- Stage A preserves already proven observations and credits them across turns; it does NOT guarantee execution of missing goals. Stage B must solve this outside Core.
- **Release blocker:** API currently trusts client-controlled `session_id` with no authenticated owner binding. Never label remote/multi-user deployment safe until fixed separately.
- Skills/capabilities must continue to use governed plugin execution and REAL AS21; no direct MCP bypass, local factual fallback, unscoped tenant scans, writes, hardcoded people/task IDs or phrase router.

### P0 — baselines and concrete wiring map
1. Pull current branch, record TESTED_HEAD, clean tracked state, six Core hashes. Check current A229M2.2AR2 report.
2. Run focused API/goal coverage suites and minimal V4+Task API smoke to confirm no new baseline defects (full suite only if needed to investigate). STOP on baseline RED.
3. Read exact implementations of API `_run_query`, `_prepare_query`, `_remember_clarification`, `guard_completed_goal_coverage`, `check_goal_coverage`, HarnessRequest/Response, runtime factory, governed plugin registry, type/catalog handlers and completion/frontier.
4. Map available **authorized** ways to execute a single missing goal without editing Core. Quote file+line and actual argument/status/data shape for each potential API seam.

### P1 — identify safe execution seam (no implementation)
Compare:
A. bounded repeated V4 `process(HarnessRequest)` for ONE typed missing goal, with prior source-proven observations carried and checked;
B. direct plugin-capability execution through an existing governed registry **only if** permissions, schema-validation, source scope and source-backed evidence contract remain identical;
C. sidecar using exactly the same governed capability executor, not a second uncontrolled source client.

For each document:
- how a goal maps to a capability **without name/space/phrase routing**;
- how task keys, resolved people, space, active sprint and constraints remain canonical;
- skill disclosure, policy checks, auth/source provenance and error taxonomy;
- exact request/response data and how goal evidence becomes creditable;
- source-read/LLM-call budget, termination condition, cancellation/timeouts and rollback;
- whether Core files need change (preferred result **ZERO**).
Reject options that skip permission/contract checks, infer missing source facts or depend on the model voluntarily completing all goals.

### P2 — deterministic goal frontier and bounded scheduler
Specify a typed goal frontier:
`goal_id, kind, immutable arguments, dependencies, required governed capability, evidence refs, status` with `PENDING | PROVEN | BLOCKED | FAILED` semantics.

Required rules:
- max 3 independent goals, max 2 missing-goal execution attempts, finite global deadline and explicit per-source/LLM rate budget (propose justified values rather than pretending they are current defaults);
- already PROVEN goals are credit-only and never re-executed in the same bounded continuation;
- only a missing goal can be launched; exact source facts/oracle and validation before marking PROVEN;
- one missing goal failed/outage => correct typed PARTIAL/FAILED if supported, otherwise safe explicit incomplete status, never false COMPLETED and never misleading NEEDS_CLARIFICATION for an unambiguous skipped action;
- genuinely ambiguous goals => clarification; do not ask user to repeat clear requests;
- no repeated resume loop, no quiet goal loss, no more than one controlled continuation in flight per session;
- private observations never appear as forged public `data.results`.
Prove whether current API statuses and UI can represent partial success without enum/protocol changes.

### P3 — counterfactual replay on exact REAL AS21 evidence
Use stored A229M1/M22AR2 traces/oracles; do not invent results. Require goal matrix, terminal capability traces, and expected user-visible completion behavior for:
- M1: Kalachanov WMB (6) + Semavin DMS (173); prove 2 goals.
- M2: DMS-267 lookup + hierarchy; REAL parent DMS-253; prior lookup must not be re-read.
- M4: lookup + hierarchy + Kalachanov WMB; 3 goals; current single-goal continuation frequently leaves person collection undone.
- C5: lookup + related tasks; hierarchy/relations evidence not interchangeable without verified coverage.
- M5: compare incomplete DMS vs OLP (comparison is one analytical goal with two source collections; do not misclassify as two independent lookup goals).
- C1/C3/C4: 1 goal with multiple filters, never split by `и`.
- One provider-429, one AS21 unavailable, expired state, cross-session replay, incomplete source snapshot, ambiguous question.
Show a no-code state-machine trace through bounded retries and coverage verification. Mark genuinely unsupported cases OPEN.

### P4 — security gate **before** implementation
Determine precise minimal authenticated ownership contract for pending state (user identity and server-issued session/continuation binding); avoid raw client-selected `session_id` as authority. Address per-principal quotas, TTL, eviction, restart-safe fail-closed and racing clarifications. Explain how local-only QA can proceed while remote deployment remains blocked. No token/secrets in report.

### P5 — owner-ready decision, no code
Recommend ONE:
`BOUNDED_V4_PER_GOAL_EXECUTOR`,
`GOVERNED_CAPABILITY_ORCHESTRATOR`,
`ISOLATED_GOVERNED_SIDECAR`, or
`NO_SAFE_OUT_OF_CORE_OPTION`.

Deliver minimal file-level implementation specification, feature flag `PO_AGENT_V4_MISSING_GOAL_EXECUTION=false` (proposal ONLY), test-before-code matrix, exact STOP/red boundaries, A/B REAL AS21 oracle, UI/clarification, restart, concurrency and rollback gates.
Explicitly separate (a) local feature behavior, (b) authenticated deployment readiness. Do not claim universal multi-intent support from limited goal detector.

### Verdict / report
- `AGENT_CORE_V4_MISSING_GOAL_EXECUTION_DESIGN_GREEN_A229M22BD` = a safe, detailed implementation path is PROVEN; **not** functional implementation GREEN.
- `AGENT_CORE_V4_MISSING_GOAL_EXECUTION_DESIGN_RED_A229M22BD` = safe boundary not proven, with first failing boundary.

Commit **QA report only**:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_MISSING_GOAL_EXECUTION_DESIGN_A229M22BD.md`.

Return TESTED_HEAD, REPORT_COMMIT, Core hashes, chosen alternative, exact next owner assignment and deployment blockers. NO production edits, NO flag flips, NO checkpoint.
