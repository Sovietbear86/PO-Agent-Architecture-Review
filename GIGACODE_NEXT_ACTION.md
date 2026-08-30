# GigaCode — Current Action

## Status

`ACTIVE_QA_ASSIGNMENT_072F`

## Role boundary — mandatory

You are QA/tester only.

**DO NOT modify production code, prompts, tests, fixtures, runtime configuration, credentials, AS21/SWTR data, GIGACODE.md, PO_AGENT_HARNESS_EVOLUTION_PLAN.md, or this file.**

The current production candidate is immutable. Do not improve, refactor or repair it.

If any production file becomes dirty during this assignment: STOP and report RED.

## Assignment 072F — cold-restart certification only

### Why this assignment exists

Assignment 072E proved all protected Learning Loop stages except one: genuine cold-restart survival and post-restart policy reuse. Its final verdict was correctly RED because the same runtime process remained alive.

072F is intentionally minimal. **Do not repeat correction regression, clarification regression, full semantic matrix or the 1274-test suite.** Reuse 072E evidence for those already-proven stages. The only goal is to close the cold-restart gap with concrete process-level proof.

Do not start Assignment 095. Do not implement fixes.

Production mode: `task-api` + REAL read-only AS21(SWTR).

## Phase 0 — clean provenance

1. Fetch/pull `feat/core8-real-query-hardening-v2`.
2. Record exact tested HEAD SHA.
3. Record `git status --short`; production files must be clean.
4. Record PO Agent and task-api PID/start timestamps before the test.
5. Record exact production policy-store path/backend used by the runtime.
6. Record policy-store baseline.

Assignment 072E rolled back policy v2, so active policies may currently be zero. That is expected.

## Phase 1 — create one fresh promoted policy

Create exactly one fresh persistent learned policy using the already-proven production Learning Loop for an applicable skill and allow-listed behaviour `authoritative_recheck_on_negative`.

You may reuse the same safe 072E test pattern if valid against REAL AS21.

Capture only the minimum evidence needed to identify the policy that must survive restart:
- policy ID;
- version;
- skill_id;
- behaviour;
- state = promoted/active;
- persistence store entry;
- REAL AS21 authoritative read evidence;
- `AS21 writes = 0`.

Do not stop here. The purpose of this phase is only to create a known active persisted policy for restart verification.

## Phase 2 — pre-restart application proof

Run one **different qualifying query** and prove that the freshly promoted policy is selected/applied before restart.

Capture:
- query;
- policy application trace/metadata;
- exact policy ID/version;
- REAL AS21 read evidence.

This establishes the before-restart control.

## Phase 3 — genuine cold restart

This phase is mandatory and must be performed autonomously if ordinary process management permissions allow it.

1. Record old PID(s) and start timestamps for the PO Agent/runtime process that owns the learned-policy state.
2. Gracefully stop that process. If graceful stop fails, use the normal local process termination mechanism. Do not modify code/configuration.
3. Prove the old PID is no longer running/listening.
4. Start a **new process from the exact same tested HEAD and normal production command/configuration**.
5. Record the new PID and start timestamp.
6. Prove `NEW_PID != OLD_PID`.
7. Do not inject/reconstruct/re-promote the policy manually after restart.
8. Read the production policy store and prove the same policy ID/version from Phase 1 still exists as active/promoted.
9. Prove the new runtime has loaded/resolved that existing persisted policy through the normal production mechanism.

Reusing an old Python object, session, in-memory singleton, hot reload, thread, worker or child object without a genuinely new owning runtime process is RED.

### If restart cannot be executed

Do not write "manual intervention needed" and do not infer success.

Instead identify the exact blocker:
- permission denied;
- unknown production launch command;
- process supervisor constraint;
- port/process ownership conflict;
- another concrete environment limitation.

Capture exact command/error and verdict `BLOCKED_BY_ENVIRONMENT` or `RED` as appropriate. Do not fix product code.

## Phase 4 — post-restart policy reuse

Using a **new session** after the new process is running, execute another qualifying query different from the original learning query.

Prove:
- same persisted policy ID/version is applied by the NEW runtime;
- no new promotion was required;
- policy was loaded from persistence, not recreated in memory;
- REAL AS21 is still authoritative for task/business facts;
- AS21 writes remain 0.

Required evidence must tie together:

`OLD_PID + policy Vn active`
`-> process stopped`
`-> NEW_PID`
`-> same policy Vn loaded`
`-> same policy Vn applied to post-restart query`.

## Phase 5 — cleanup rollback

After successful post-restart proof, rollback/deactivate the test policy using the supported production mechanism so the repository/runtime is not left with QA learning state active.

Prove:
- rollback result;
- active policy count after cleanup;
- policy state = rolled_back/inactive;
- AS21 write calls = 0.

Do not manually delete the policy-store file.

## Phase 6 — source/environment counters

Record for this narrow run:
- HTTP 500 count;
- HTTP 502 count;
- endpoint/time mapping for any 502;
- fake/mock/frozen authoritative-call count;
- AS21 write-call count;
- successful REAL AS21 read evidence.

A 502 affecting the policy promotion or post-restart verification path is not PASS.

## Acceptance matrix

| Contract step | PASS condition |
|---|---|
| Fresh policy | one identifiable active persistent policy created |
| Pre-restart application | same policy ID/version demonstrably applied |
| Old process proof | old PID/start timestamp recorded and process terminated |
| New process proof | different new PID/start timestamp from same HEAD |
| Persistence | same policy ID/version remains in production store |
| Runtime reload | new runtime resolves existing policy without re-promotion |
| Post-restart reuse | same policy ID/version applied to new qualifying query |
| REAL source | business facts remain REAL AS21 grounded |
| Cleanup | test policy rolled back after proof |
| Integrity | AS21 writes=0, fake authoritative calls=0 |

Every row requires concrete evidence. Statements like "restart should work" or "store is persistent" are not acceptance evidence.

## Output

Create only:

`po-agent-platform-v2/qa_reports/CORE8_PERSISTENT_LEARNING_COLD_RESTART_072F.md`

The report must include:
- exact commands;
- tested HEAD SHA;
- clean-worktree proof;
- old PID/start timestamp;
- new PID/start timestamp;
- proof old PID terminated;
- production restart command;
- fresh policy ID/version/store entry;
- pre-restart policy application trace;
- post-restart policy-store state;
- new-runtime policy reload evidence;
- post-restart different-query application trace tied to same policy ID/version;
- REAL AS21 evidence;
- cleanup rollback evidence;
- HTTP 500/502 counts and endpoint mapping;
- fake/mock/frozen authoritative-call count;
- AS21 write-call count;
- completed acceptance matrix;
- remaining known failures.

### Final verdict

`GREEN` only if genuine process replacement and post-restart reuse of the **same persisted policy ID/version** are concretely proven and every acceptance row passes.

If the product fails to reload/apply the policy after a genuine restart: `RED` and identify `FIRST_FAILING_BOUNDARY`.

If the restart cannot be executed because of a proven external/environment constraint: `BLOCKED_BY_ENVIRONMENT` with exact evidence.

Do not fix anything.

Commit and push ONLY the QA report. Verify the report exists in remote HEAD after push. Report final SHA and STOP.

Do not start Assignment 073 or 095.