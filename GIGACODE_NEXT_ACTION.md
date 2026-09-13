# GigaCode — Current Action

## Status
`ACTIVE_OWNER_ASSIGNMENT_187_V4_STRUCTURED_COMPLETION_RELIABILITY`

## Mission
Assignment 186 certified the A185 B1/B2 fixes and proved the remaining blocker is **not source correctness and not an A185 regression**. The remaining V4 POC blocker is a recurring Qwen3.8 control-plane reliability defect on **post-observation completion** of multi-step trajectories:

- `task.lookup -> task.search` reaches the correct source-backed collection;
- the planner then intermittently fails to emit a valid terminal `READY` JSON decision;
- bounded repair may hallucinate a new action (for example count-as-task-key), repeat a capability without required arguments, or otherwise fail closed;
- A/B on the old A184 HEAD reproduces the same failure against today's shared Qwen endpoint, proving endpoint/model-output instability rather than a code regression.

Assignment 187 is a **bounded V4 production reliability hardening**. Do not redesign V4, do not change the model/provider, and do not introduce multi-agent/GVS5H orchestration. GVS5H-style orchestration is explicitly deferred to the **V5 milestone**.

## Product priority / roadmap lock
V4 priority is now:
1. reliable governed backend;
2. Browser/UI with all required widgets/states;
3. progressive migration of the complete 54-skill catalog;
4. full V4 E2E gate.

`DEFERRED_TO_V5`: GVS5H-inspired multi-agent orchestration (fresh workers + typed shared ledger + verifier) must NOT be implemented during V4. Preserve this note in durable planning docs you touch.

## Mandatory pre-read
First:
```bash
git pull --ff-only origin feat/core8-real-query-hardening-v2
```
Then read:
- `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_REPRESENTATIVE_POC_REGATE_186.md`
- `po-agent-platform-v2/docs/v4_dod/V4_DOD_LOCK.md`
- `AGENT_CORE_V4_SKILL_NATIVE_SPEC.md`
- current robust planner/runtime implementation and the A179-A182/A186 reliability lineage in `GIGACODE.md` / QA reports.

## Scope
Implement the **smallest generalized reliability mechanism** that removes dependence on a stochastic model successfully minting terminal `READY` after the runtime already has sufficient trusted observations to satisfy the loaded skill.

Preferred direction:
- deterministic / contract-driven completion from **skill procedure state + validated observations**;
- optional structured-output hardening only where generic and model-agnostic;
- preserve the LLM for planning/reasoning where a further action is actually needed.

This must be a generic control-plane rule, not a query-specific fallback.

## Non-negotiable invariants
- Keep `Qwen/Qwen3.8-27B` and current provider unchanged.
- No semantic prepass.
- No surname/person/task/sprint/query-phrase hardcode.
- No DMS-380/DMS-99-specific branch.
- No fabricated source facts.
- REAL AS21 remains authoritative.
- Recovery-time `READY` remains forbidden unless the new completion mechanism is **runtime-generated from verified completion state**, not model-recovered text.
- Existing fail-closed behavior for missing/ambiguous source facts remains intact.
- Do not weaken capability governance or literal grounding.
- Do not silently terminate a trajectory when required user constraints are not satisfied.
- Do not introduce GVS5H/multi-agent orchestration in V4.

## Required design
Create a generic notion of **skill completion contract / satisfaction state** for V4.

At minimum it must support the currently loaded representative skills without encoding user-specific examples. For example:
- a task lookup skill is complete after its required authoritative task observation exists;
- `tasks.lookup_then_assignee` is complete only after the authoritative lookup observation exists **and** a downstream assignee-bound task collection exists;
- person/space/sprint task-search skills are complete only after a `task.search` observation satisfying all resolved user constraints exists;
- sprint list/search/current and analytical skills must not be prematurely auto-completed before their required observation exists.

The runtime may synthesize/return after the contract is satisfied without another planner terminal turn. The completion rule must inspect typed trajectory/observations, not natural-language entity literals.

If a skill cannot be safely proven complete from typed state, retain normal planner behavior.

## Phase 1 — Design and tests first
Before production edits, add focused tests that prove at least:
1. `tasks.lookup_then_assignee` becomes complete after the correct lookup + assignee-bound `task.search` observation.
2. It does **not** complete after lookup alone.
3. It does **not** complete after a `task.search` for the wrong/unbound assignee.
4. It does **not** complete when an additional user constraint (space/sprint/status) is not represented in the downstream observation.
5. Single-step skills complete only after their required authoritative observation.
6. Analytical skills are not auto-completed before their analytical capability result exists.
7. Invented/ambiguous/source-failure paths never auto-complete.
8. Runtime-generated completion does not use model `READY` recovery and cannot fabricate an answer without observations.
9. Existing action-only recovery safety remains intact.
10. No semantic-prepass or entity-specific routing appears.

Tests must be generic fixtures, not DMS-380-only tests.

## Phase 2 — Implement bounded completion hardening
Implement the minimum production changes needed for the completion contract.

Expected shape (names may differ if a cleaner design exists):
- typed `SkillCompletionState` / `is_skill_satisfied(...)` helper;
- generic constraint-satisfaction check against resolved call arguments + observations;
- runtime short-circuit **after a successful capability observation** when the active skill is provably satisfied;
- deterministic final synthesis using the existing validated observation path.

Do NOT create a new semantic interpreter or query router.

## Phase 3 — Focused regression
Run at minimum:
- V4 robust protocol/reliable/skill-native suites;
- new completion-contract tests;
- B1/B2 regression suites from A185;
- identity/sprint discovery suites from A183.

Then run the broader po-agent suite and prove no new failure node IDs versus the A186 baseline.

## Phase 4 — Live owner verification against fresh REAL AS21
Use fresh task-api + fresh PO Agent runtime, concurrency 1, fresh session per run.

Refresh Oracle B live; hardcode no counts.

Mandatory owner verification:
1. `10x` `Покажи DMS-380 и затем задачи его исполнителя` — **10/10 exact key parity**.
2. `5x` another lookup→assignee→tasks case discovered live (DMS-99 may be used only if still source-valid) — **5/5 exact parity**.
3. `5x` person collection and `5x` person+space/status queries — exact parity.
4. current-sprint task query on a source-valid sprint — exact parity.
5. three A183 scenarios remain green:
   - human-period sprint resolution;
   - plural active-sprint list;
   - source-authority non-roster identity.
6. negative controls:
   - invented task/person/sprint;
   - ambiguous identity;
   - source unavailable path if practical.

For every multi-step lookup→collection run record:
- trajectory;
- whether completion was runtime-generated or model `READY`;
- exact Oracle parity;
- latency;
- zero extra model terminal-repair turns after the satisfaction boundary.

Owner acceptance for the new mechanism:
- 10/10 + 5/5 multi-step exact parity;
- no count→task-key hallucination;
- no post-satisfaction planner repair loop;
- zero fabricated facts;
- safety/fail-closed retained.

If the completion contract itself causes a new correctness/safety defect, STOP and report the exact boundary instead of layering another fallback.

## Phase 5 — Documentation / roadmap
Update the durable V4 planning/DoD documentation as needed to record:
- the generic deterministic post-observation completion rule;
- that V4 remains single-planner / skill-native / governed;
- `DEFERRED_TO_V5`: GVS5H-inspired multi-agent orchestration POC after V4 is fully working (54 skills + UI/widgets + E2E).

Do not claim full 54-skill completion yet.

## Phase 6 — Prepare Assignment 188 QA-only re-gate
After owner verification is GREEN, replace this file with a **QA-only Assignment 188** specification that independently re-tests:
- build/static invariants;
- 10x DMS-380 multi-step exact parity;
- at least one second lookup→assignee→tasks family;
- mixed matrix / unseen combinations;
- B1/B2 retained exactness;
- A183 scenarios;
- safety/fail-closed;
- proof that satisfied trajectories no longer depend on stochastic model terminal `READY`.

Final QA verdict must allow:
- `AGENT_CORE_V4_REPRESENTATIVE_POC_GREEN` only if all mandatory gates pass;
- otherwise a precisely attributed bounded RED / source block / planner strategy review.

If Assignment 188 is GREEN, recommendation must be:
**STOP backend POC remediation → proceed to Browser C/UI → progressively migrate all 54 skills → full V4 E2E gate.**

Do not run Assignment 188 in this same session.

## Commit discipline
Commit production changes/tests/docs in coherent commits. Then commit the Assignment 188 `GIGACODE_NEXT_ACTION.md` update separately.

Never commit secrets, `.env`, QA scratch outputs, or unrelated changes.

## Completion response
Return:
- commit SHAs;
- focused/broader test results;
- live owner verification matrix;
- confirmation that the runtime completion rule is generic and source-safe;
- confirmation that V5/GVS5H is deferred and not implemented;
- confirmation that Assignment 188 is prepared but **not started**.

Then **STOP**.