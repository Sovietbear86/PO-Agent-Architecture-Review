# GigaCode — Current Action

## Status

`ACTIVE_QA_ASSIGNMENT_072F`

## Role boundary — mandatory

You are QA/tester only.

**DO NOT modify production code, prompts, tests, fixtures, runtime configuration, credentials, AS21/SWTR data, GIGACODE.md, PO_AGENT_HARNESS_EVOLUTION_PLAN.md, or this file.**

The current production candidate is immutable. Do not improve, refactor or repair it.

If any production file becomes dirty during this assignment: STOP and report RED.

## Assignment 072F — cold-restart certification only

### Important correction to the previous run

The previous GigaCode run did **not** satisfy 072F even though it marked 072E GREEN. It updated the wrong report and its cold-restart evidence was internally invalid:

- it modified `CORE8_PERSISTENT_LEARNING_PROOF_072E.md` instead of creating the required 072F report;
- after restart, policy `v2` was shown as `rolled_back`, not active/promoted;
- the post-restart query FAILED because AS21 was unavailable;
- therefore the same active policy was **not proven to be reloaded and applied by the new runtime**;
- exact old/new PID evidence was not shown;
- the report simultaneously contained GREEN claims and leftover contradictory RED text.

Do not reuse that GREEN verdict. Treat 072E as prior evidence only.

### Goal

Prove exactly one missing contract:

`ACTIVE persisted policy Vn`
`-> old runtime PID recorded`
`-> old runtime terminated`
`-> genuinely NEW runtime PID`
`-> same policy Vn still ACTIVE after restart`
`-> same policy Vn applied by new runtime to a qualifying query`
`-> REAL AS21 read succeeds`
`-> rollback only AFTER this proof`

Do not start Assignment 095. Do not implement fixes.

Production mode: `task-api` + REAL read-only AS21(SWTR).

## Phase 0 — clean provenance

1. Fetch/pull `feat/core8-real-query-hardening-v2`.
2. Record exact tested HEAD SHA.
3. Record `git status --short`; production files must be clean.
4. Record PO Agent and task-api PID/start timestamps before the test.
5. Record exact production policy-store path/backend.
6. Record current active policy state.

## Phase 1 — create one fresh ACTIVE promoted policy

Create exactly one fresh persistent learned policy using the already-proven production Learning Loop for an applicable skill and allow-listed behaviour `authoritative_recheck_on_negative`.

Capture:
- policy ID;
- version;
- skill_id;
- behaviour;
- `state = promoted/active`;
- persistence-store entry;
- REAL AS21 authoritative read evidence;
- AS21 writes = 0.

**Do not rollback this policy before or during restart.** It must remain ACTIVE through Phase 4.

## Phase 2 — pre-restart application control

Run one different qualifying query and prove the active policy is selected/applied before restart.

Capture query, application trace/metadata, exact policy ID/version and successful REAL AS21 evidence.

## Phase 3 — genuine process replacement

1. Record exact old PO Agent PID and start timestamp.
2. Stop that process.
3. Prove old PID is no longer running/listening.
4. Start a new process from the exact same HEAD with the normal production launch command/configuration.
5. Record exact new PID and start timestamp.
6. Prove `NEW_PID != OLD_PID`.
7. Do not reconstruct, re-promote, edit or rollback the policy.
8. Immediately inspect the production policy store: the same policy ID/version must still be `promoted/active`.
9. Prove the new runtime resolves that existing persisted active policy through the normal runtime path.

If the policy is already `rolled_back` at this point, this phase is RED. Do not claim persistence/reload success from the mere presence of a rolled-back record.

## Phase 4 — post-restart reuse (mandatory)

Using a NEW session, execute another qualifying query different from the learning query and pre-restart query.

GREEN requires all of the following:
- query completes successfully;
- REAL AS21 authoritative read succeeds;
- same policy ID/version from Phase 1 is applied by the NEW runtime;
- application trace/metadata ties the response to that policy;
- no new policy promotion occurred after restart;
- policy remained active until this proof completed;
- AS21 writes = 0.

A failed query, timeout, unavailable AS21, inferred reload, or inspection of the file alone is **not PASS**. If AS21 is unavailable, verdict is `BLOCKED_BY_ENVIRONMENT`, not GREEN.

## Phase 5 — cleanup rollback

Only after Phase 4 is proven GREEN:
- rollback/deactivate the test policy using the supported production mechanism;
- prove active policy count/state after cleanup;
- verify AS21 writes = 0.

## Phase 6 — counters

Record:
- HTTP 500 count;
- HTTP 502 count with endpoint/time mapping;
- fake/mock/frozen authoritative-call count;
- AS21 write-call count;
- successful REAL AS21 read evidence before and after restart.

## Acceptance matrix

| Contract step | PASS condition |
|---|---|
| Fresh active policy | identifiable policy ID/version is promoted/active |
| Pre-restart application | same active policy demonstrably applied |
| Old process proof | exact old PID/start timestamp recorded and terminated |
| New process proof | exact different new PID/start timestamp from same HEAD |
| Active persistence | same policy ID/version remains promoted/active after restart |
| Runtime reload | new runtime resolves existing active policy without re-promotion |
| Post-restart reuse | same policy ID/version applied to successful new query |
| REAL source | post-restart query has successful REAL AS21 grounding |
| Cleanup | rollback occurs only after post-restart proof |
| Integrity | AS21 writes=0, fake authoritative calls=0 |

Every row needs concrete evidence.

## Output — exact file only

Create **only**:

`po-agent-platform-v2/qa_reports/CORE8_PERSISTENT_LEARNING_COLD_RESTART_072F.md`

**Do not edit or overwrite `CORE8_PERSISTENT_LEARNING_PROOF_072E.md`.**

The 072F report must contain:
- exact commands;
- tested HEAD SHA;
- clean-worktree proof;
- exact old PID/start timestamp;
- proof old PID terminated;
- exact new PID/start timestamp;
- production restart command;
- active policy ID/version/store entry before restart;
- pre-restart application trace;
- active policy store state immediately after restart;
- new-runtime reload/resolution evidence;
- successful post-restart query trace tied to same policy ID/version;
- successful REAL AS21 post-restart read evidence;
- cleanup rollback evidence;
- HTTP 500/502 mapping;
- fake/mock/frozen authoritative-call count;
- AS21 write-call count;
- completed acceptance matrix;
- remaining failures.

### Final verdict

`GREEN` only if the same ACTIVE policy survives a genuine process replacement and is actually applied by the new runtime to a successful REAL-AS21-grounded query before rollback.

If AS21 is unavailable during the required post-restart query: `BLOCKED_BY_ENVIRONMENT`.

If the policy is not active/reloaded/applied after restart: `RED` with `FIRST_FAILING_BOUNDARY`.

Do not fix anything.

Commit and push ONLY the new 072F QA report. Verify the exact file exists in remote HEAD after push. Report final SHA and STOP.

Do not start Assignment 073 or 095.