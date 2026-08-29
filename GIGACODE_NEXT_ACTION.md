# GigaCode — Current Action

## Status

`ACTIVE_QA_ASSIGNMENT_072E`

## Role boundary — mandatory

You are QA/tester only.

**DO NOT modify production code, prompts, tests, fixtures, runtime configuration, credentials, AS21/SWTR data, GIGACODE.md, PO_AGENT_HARNESS_EVOLUTION_PLAN.md, or this file.**

The current production candidate is immutable for this assignment. Do not improve, refactor or repair it.

If any production file becomes dirty during this assignment: STOP and report RED.

## Assignment 072E — factual persistent Learning Loop proof

### Why this assignment exists

Assignment 072D established useful correction/clarification evidence, but its Learning Loop section is not sufficient for acceptance. The report showed `source_recheck_performed=true` while also showing `persistent_behavior_learning=false`, then inferred promotion/persistence/restart/rollback without supplying the required concrete artifacts.

072E is deliberately narrow. **Do not repeat correction, clarification or the full 1274-test regression unless required to execute the learning trace.** The only goal is to prove or disprove the actual persistent Learning Loop end to end.

Do not start Assignment 095. Do not implement fixes.

Production mode: `task-api` + REAL read-only AS21(SWTR). Fake/mock/frozen source data cannot be used as authoritative acceptance evidence.

## Phase 0 — provenance

1. Fetch/pull `feat/core8-real-query-hardening-v2`.
2. Record exact tested HEAD SHA.
3. Record `git status --short`; production worktree must be clean.
4. Restart PO Agent and task-api from that exact HEAD.
5. Prove REAL AS21 mode and record process IDs/start timestamps so the later cold restart is independently verifiable.
6. Identify the exact production persistent-learning implementation and policy-store location/API used by the running runtime. Do not create an alternative test-only learning path.

## Phase 1 — establish policy-store baseline

Before triggering learning, capture the active learned-policy state for the selected production skill:
- policy count;
- active policy IDs/versions;
- policy type/behaviour;
- skill_id;
- audit/provenance fields;
- persistence location/backend.

Do not expose secrets. Entity/source facts may be redacted, but structural fields must remain visible.

If a policy for the exact intended test behaviour already exists, either safely roll it back through the supported production mechanism before the test or choose another applicable skill/session so that a newly promoted policy can be distinguished from pre-existing state. Record what was done.

## Phase 2 — trigger real bounded learning

Use an applicable production skill and the allow-listed generalized behaviour `authoritative_recheck_on_negative`.

Prove with exact runtime evidence:

`initial execution`
`-> explicit negative feedback/correction`
`-> fresh authoritative REAL AS21 recheck`
`-> source-grounded validation`
`-> generalized policy candidate/promotion`
`-> persistent active policy record`

Mandatory evidence:
- request/response or trace showing the negative feedback event;
- `source_recheck_performed == true` (or exact equivalent production evidence);
- successful REAL AS21 read used by the authoritative recheck;
- exact promotion event/decision;
- policy store state BEFORE and AFTER promotion;
- newly created/activated policy ID + version + skill_id + generalized policy type;
- persisted policy payload/schema sufficient to prove it does not contain a task ID, member login, sprint ID, stored answer, correction prose or entity truth.

**Critical rule:** if the production response says `persistent_behavior_learning=false`, do not call the phase GREEN unless you separately prove that a persistent policy was actually promoted by the same event through another production surface. If no persistent policy appears, verdict is RED and identify the first failing boundary.

If a safe initial negative requires an existing QA fault-injection mechanism, it may be used only to create the initial negative condition. The authoritative recheck and validation must still hit REAL read-only AS21. Do not modify fixtures or source facts.

## Phase 3 — prove generalization

After promotion, execute a **different query/entity/input** that is eligible for the same learned behaviour.

Prove:
- the learned policy is selected/applied;
- the second request is not the original memorized query;
- no entity-specific stored truth is required;
- REAL AS21 remains authoritative for business facts;
- behavior differs in the expected generalized way because of the policy.

Capture policy-selection/application evidence tied to the policy ID/version from Phase 2.

## Phase 4 — genuine cold restart

1. Record current PO Agent/task-api process IDs.
2. Stop the relevant runtime process(es).
3. Start genuinely new process(es) from the same tested HEAD without reconstructing the learned policy manually.
4. Record new process IDs/start timestamps.
5. Prove the persisted policy is loaded from the production policy store after restart.
6. Re-run a qualifying different query and prove the same policy ID/version is applied after restart.

Reusing the same Python object, interpreter session, in-memory singleton or cached runtime is NOT a cold restart.

## Phase 5 — rollback and negative proof

Use the supported production learning-policy rollback/deactivation mechanism for the policy created in Phase 2.

Prove:
- rollback/deactivation command/API/event;
- policy-store state after rollback;
- policy is no longer active/selectable;
- another qualifying request after rollback does **not** apply that policy;
- REAL AS21 behavior remains correct and read-only.

Do not delete/edit the policy-store file manually unless manual file editing is itself the documented production rollback mechanism. If no supported rollback exists, report RED.

## Phase 6 — idempotency and safety

Where possible without recreating the rolled-back policy incorrectly, prove from the captured trace/store history that:
- repeated identical feedback does not create unbounded duplicate active policies;
- promotion/audit history is versioned or otherwise traceable;
- learned payload contains generalized behavior only;
- AS21 write calls = 0;
- fake/mock/frozen authoritative calls = 0.

Record HTTP 500 and HTTP 502 counts observed during this narrow test. Any 502 must be mapped to the exact endpoint/time and state whether it affected the learning chain. Do not dismiss 502 as external without evidence.

## Acceptance matrix — every row needs concrete evidence

| Contract step | Required evidence | PASS condition |
|---|---|---|
| Negative feedback | request/trace | event reached production correction/feedback path |
| Authoritative recheck | runtime trace + REAL AS21 read | fresh source validation occurred |
| Promotion | promotion event/decision | generalized allow-listed policy promoted |
| Persistence | store BEFORE/AFTER | new active policy ID/version persisted |
| Safety | persisted payload | no entity/answer memorization |
| Generalization | different query + policy application trace | same policy applies beyond original query |
| Cold restart | old/new PID + reload evidence | persisted policy reloads in new runtime |
| Post-restart reuse | query + application trace | same policy works after restart |
| Rollback | supported rollback + store state | policy becomes inactive |
| Post-rollback negative | qualifying query trace | rolled-back policy no longer applies |
| Source integrity | counters + REAL reads | writes=0, fake authoritative calls=0 |

A checkbox or statement such as "mechanism exists", "verified from code review", "rollback mechanism in place" or "cold restart supported" is **not evidence**.

## Output

Create only:

`po-agent-platform-v2/qa_reports/CORE8_PERSISTENT_LEARNING_PROOF_072E.md`

The report must include:
- exact commands;
- tested HEAD SHA;
- clean-worktree proof;
- runtime/process provenance;
- exact policy-store backend/location;
- policy state BEFORE learning;
- full learning trace;
- policy state AFTER promotion;
- policy ID/version/skill_id/type and safe payload excerpt;
- different-query generalization trace;
- old/new PID cold-restart evidence;
- post-restart policy reload/application evidence;
- rollback evidence;
- post-rollback negative evidence;
- idempotency/safety evidence;
- REAL AS21 reads;
- HTTP 500/502 counts and endpoint mapping;
- fake/mock/frozen authoritative-call count;
- AS21 write-call count;
- the completed acceptance matrix above;
- remaining known failures.

### Final verdict

`GREEN` only if **every acceptance-matrix row is concretely proven**.

If any step is absent, inferred, unsupported, or reports `persistent_behavior_learning=false` without separate proof of actual promotion/persistence from the same production event, verdict must be `RED` and the report must identify `FIRST_FAILING_BOUNDARY`.

Do not fix the failure.

Commit and push ONLY the QA report. Verify that the report exists in remote HEAD after push. Report final SHA and STOP.

Do not start Assignment 073 or 095.