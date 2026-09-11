# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_179_AGENT_CORE_V4_BINDING_CONTINUATION`

## Mission
Continue the V4 skill-native POC from the Assignment 178 checkpoint. **Do not restart from zero.** Do not return to V3/H1B semantic-prepass work.

Assignment 178 proved major V4 gates GREEN:
- REAL current-sprint source path GREEN;
- `semantic_prepass_used=false`;
- Garanin 5/5 exact Oracle parity;
- Moiseev 5/5 exact Oracle parity;
- PVM-Guru benchmark 5/5 terminally Oracle-correct;
- current DMS sprint 5/5 exact;
- progressive skill loading works;
- most generalized compound and cross-skill cases work.

First RED boundary was **capability binding**:
`task.lookup(DMS-380) -> task.search(assignee=Semavin.M.M)` failed because the trusted lookup observation exposed only the human display name and not a canonical bindable assignee login/id.

Assignment 178 also exposed two generalized precision gaps:
- unrelated surname `Гарановых` was over-fuzzily normalized to `Garanin.R.V`;
- sprint-context identity `Шиднева` did not resolve although `Sidneva.Y.S` is present in the authoritative sprint rows.

Owner commits under test:
- `ba7f453cdc8f9e01696833c5a71156881d773b9a` — V4 task.lookup now uses REAL AS21 canonical Task data, surfaces `assignee_login/assignee_id` for downstream binding, tightens morphology matching, and intersects source identity candidates with authoritative sprint-context assignees;
- `d7ebcd283ac3152941cad85f2c702460206bb903` — focused regression tests for canonical lookup binding and false-positive identity matching.

QA ONLY. Do not modify production/backend/frontend/test code, prompts, `.env`, model config, skill registry, or learning data.

## Absolute rules
- First: `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
- Verify both owner commits are ancestors of HEAD.
- Keep current Qwen 3.8/provider unchanged.
- Runtime env only: `PO_AGENT_AGENT_CORE_V4_ENABLED=true`.
- Restart/reuse a fresh PO Agent process that definitely runs current HEAD; do not test stale port/process code.
- Oracle B = fresh direct REAL MCP-SWTR/AS21 only. Never `/api/v1/tasks`, local DB, sync, fake/frozen data, prior Agent A output.
- Concurrency=1. Source timeout >=300s; long E2E/agent call <=600s.
- Exact task-key-set parity for factual collections.
- Fresh session per independent run.
- Reuse Assignment 178 evidence where source state has not changed, but refresh the specific Oracle facts needed for the cases below.
- If a new production defect appears, capture FIRST FAILING BOUNDARY and STOP. Do not patch code.
- Commit/push only the final QA report.

## Retained checkpoint — do NOT rerun broadly
Treat the following 178 results as retained evidence unless a refreshed source read contradicts them:
- sprint.current source wiring GREEN;
- Phase 2 Garanin/Moiseev/PVM-Guru benchmark GREEN;
- current sprint GREEN;
- generalization 5/6 exact;
- cross-skill task lookup/summary/quality/acceptance/blockers/sprint health/current sprint GREEN;
- release health is source-limited/fail-closed because live release-task linkage is unavailable; this is not fabrication and should be terminally classified as source-capability unavailable rather than treated as an agent reasoning failure.

## Phase 0 — Focused build/unit gate
Run only the focused V4 tests and affected factory/API smoke tests.

Require proof that:
1. production V4 factory still instantiates `ReliableAgentCoreV4Runtime`;
2. `task.lookup` handler in V4 is the new source-backed handler, not the legacy observation shape;
3. lookup observation exposes canonical `assignee_login` and/or `assignee_id` directly from the authoritative canonical Task;
4. downstream trusted identity extraction accepts only those source-backed fields;
5. `Гарановых` no longer matches Garanin by fuzzy team normalization;
6. no person/task/sprint entity facts were hardcoded.

Any unit/build/runtime-construction failure => `V4_BUILD_RUNTIME_RED` and STOP.

## Phase 1 — Canonical lookup -> assignee -> tasks binding gate
Refresh Oracle B for:
- `DMS-380` canonical task assignee;
- all current tasks for that canonical assignee across approved PO Agent spaces.

Then run 5x fresh sessions:
`Покажи DMS-380 и затем задачи его исполнителя`

For every run capture full V4 trajectory and observations.
Require:
- `task.lookup` returns `DMS-380` from REAL AS21;
- lookup observation contains canonical assignee identity (expected from live source, do not hardcode it in QA logic);
- subsequent task.search assignee is either `$obs.N.assignee_login/$obs.N.assignee_id` or a literal exactly equal to that trusted observation;
- no login is inferred from Russian display-name text;
- task.search returns the complete exact Oracle task-key set;
- 5/5 terminally correct.

Any `V4ContractError` at this boundary => `V4_CAPABILITY_BINDING_RED` and STOP.

## Phase 2 — Identity safety precision gate
Fresh sessions, minimum 3x each:
1. `Задачи Гарановых`
2. `Задачи Гаранина`
3. one additional invented/nonexistent surname sharing only a partial prefix with a real roster surname.

Require:
- unrelated/nonexistent names do NOT resolve to a real colleague merely by common prefix;
- real inflected names still resolve correctly and exact Oracle parity is preserved;
- no fabricated identities/tasks.

If unrelated name maps to a real colleague => `V4_SAFETY_RED` and STOP.

## Phase 3 — Context identity generalization gate
Refresh Oracle B for `OLP-SPRNT-5` (or the same still-populated sprint if source changed) and canonical assignees present in it.

Re-run 5x:
`Открытые задачи Шидневой в спринте OLP-SPRNT-5`

Acceptance:
- if exactly one source identity matching the natural reference is present in the authoritative sprint context, V4 must resolve it and return exact open-task key parity;
- source resolver candidates may be intersected with sprint canonical ids, but an identity absent from the sprint may never be accepted;
- true ambiguity remains typed clarification;
- no transliteration/name hardcode.

Also re-run one previously GREEN sprint-only non-roster person case (e.g. the live equivalent of Shaldunov) as regression.

## Phase 4 — Focused cross-skill closure
Do not repeat all nine cases blindly. Re-run:
- `Покажи DMS-380` — prove canonical identity fields now appear in trusted observation;
- `Покажи DMS-380 и затем задачи его исполнителя` — 5/5 exact parity;
- `Какой текущий спринт в DMS?` — 5x, underlying data AND user-visible sprint id must be exactly the canonical id (no duplicated `SPRNT` text);
- one sprint.health case;
- one task.quality or task.summary case.

For release.health, retain Assignment 178's source-limited classification unless a fresh live source check proves release-task linkage is now available. Source-unavailable/fail-closed is a terminally correct classification; do not fabricate data just to make the scenario GREEN.

## Phase 5 — Mini generalized POC decision gate
Using retained 178 evidence plus Phases 0-4, GREEN requires all:
- task lookup -> canonical assignee -> full task search works 5/5 exact;
- Garanin/Moiseev critical search remains GREEN from retained checkpoint or one smoke recheck each;
- PVM-Guru benchmark remains GREEN from retained checkpoint or one smoke recheck;
- current sprint exact source-backed behavior remains GREEN;
- contextual sprint-only identity now works when source context is unique;
- false-positive unrelated surname safety defect is closed;
- progressive skill loading visible;
- semantic pre-pass absent;
- no entity-specific hardcodes;
- no local task DB/sync accepted as truth.

If all pass, this is sufficient to mark the **Agent Core v4 API POC architecture gate GREEN**. Next owner step is Browser C/UI V4 wiring and then progressive expansion toward the mandatory 54/54 A/B/C catalog certification.

Do not block V4 architecture GREEN merely because a capability is proven unavailable from the live source contract (for example release health with no live release-task linkage); classify it explicitly and carry it into the 54-skill source-capability matrix.

## Phase 6 — Report
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_BINDING_CONTINUATION_179.md`

Allowed verdicts:
- `AGENT_CORE_V4_API_POC_GREEN`
- `V4_CAPABILITY_BINDING_RED`
- `V4_CONTEXT_IDENTITY_RED`
- `V4_SAFETY_RED`
- `V4_RESPONSE_SYNTHESIS_RED`
- `V4_AGENT_ORACLE_PARITY_RED`
- `V4_SOURCE_ADAPTER_RED`
- `V4_BUILD_RUNTIME_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

If RED: include exact first failing function/boundary, raw trajectory, expected source truth, actual result and smallest generalized owner fix. No surname/phrase/semantic-prepass patch proposals.

If GREEN explicitly state:
- V4 raw-query -> progressive skill -> typed capability -> REAL AS21 observation -> re-plan -> validated answer API POC is proven;
- multi-step observation binding is proven without deriving ids from display text;
- unknown/context-only people are handled source-backed;
- V3 semantic-prepass is not required for this POC;
- next = Browser C/UI V4 POC, then progressive migration and mandatory 54/54 A/B/C certification.

Commit/push only the report and STOP.

## Start now
Resume from Assignment 178 checkpoint and execute Assignment 179. Do not restart the entire V4 POC.