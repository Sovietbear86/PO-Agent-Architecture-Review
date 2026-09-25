# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_217B_RELEASE_ROUTING_REGATE

## Role lock
GigaCode is QA/adversarial tester only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT start Batch 5.
Commit/push only the QA report.

## Baseline
A217 verdict:
AGENT_CORE_V4_BATCH4_FIVE_SKILL_RED
Classification:
RED_NL_ROUTING_EARLY_READY_BYPASSES_TYPED_SC

Batch 4 plugin logic itself was GREEN; the blocker was platform completion/routing around release.search.

## Owner fix
Owner commits:
- ca2d190093dce497b969d431120f70c7b681000f
- ae348a05ca05f7f48e455c08fd262d383e4c8235
- 944bf0f3ad12ecf6eb4bdad230839f4c96bfeb7b
- d96fef29ca2006d6a30368ec1a64958fcec208a8

Fix design:
1. generic SkillSpecV4 metadata `runtime_autocomplete` (default true);
2. SkillCatalog exposes a generic runtime_autocomplete_allowed API;
3. deterministic runtime-contract READY is deferred when a loaded resolver skill declares runtime_autocomplete=false;
4. release.search declares runtime_autocomplete=false because it can be a standalone goal OR an identity step for deeper release analytics;
5. release.search procedure explicitly says it does not satisfy health/progress/risk/blocker/dependency goals;
6. release.search locally normalizes a unique approved product-space token from its query argument if planner preserved it there but omitted `space`;
7. missing/ambiguous space fails typed clarification before any no-space source call.

No release-progress/health skill-id branch was added to Agent Core.
No semantic pre-pass or phrase router was added.

## Phase 0 — architecture invariant
1. Pull branch, record START_HEAD, clean worktree.
2. Diff owner fix commits.
3. Prove generic metadata/default behavior:
   - existing skills retain runtime_autocomplete=true by default;
   - only declaratively marked resolver behavior is deferred;
   - no query phrase routing in Agent Core;
   - no release metric skill-id branch in Agent Core.
4. dummy-55 GREEN.

## Phase 1 — tests
Run:
- tests/test_agent_core_v4_batch4.py
- full tests/test_agent_core_v4*.py
- tests/test_v4*.py

Require zero unexplained failures.

## Phase 2 — standalone release.search regression
Test direct directory goals, e.g.:
- "релизы WMB"
- "релиз 1.6.0 в OLP"
- "покажи версии WMB"

Requirements:
- release.search still completes successfully;
- one extra planner turn is allowed because runtime autocomplete is deferred;
- no planner-loop exhaustion;
- exact release catalog parity;
- bounded space-scoped source reads only.

## Phase 3 — A217 failing progress forms
Run repeatedly:
- "прогресс релиза 24Q1 в WMB" >=5
- "готовность релиза OLP 1.6.0" >=5
- "release progress for 24Q1 in WMB" >=3

Required trajectory:
- release identity resolution;
- then release.progress MUST load/invoke;
- current empty release membership => typed V4CapabilityUnavailable / SOURCE_CONDITIONAL;
- zero early terminal COMPLETED answers from release.search alone;
- zero no-space /versions 400 calls.

Any release.search-only terminal answer => RED.

## Phase 4 — retained release.health
Run:
- "здоровье релиза 24Q1 в WMB" >=3
- equivalent OLP form >=2

Require release.health actually executes and terminates typed SOURCE_CONDITIONAL under current linkage.
No release.search-only early completion.

## Phase 5 — sibling Batch 4 retained
Re-run:
- release.blockers
- release.dependencies
- release.risk_queue
- portfolio.overview

Require A217 parity unchanged.

## Phase 6 — source-scope hardening
Explicitly test planner-omission shape at capability level:
release.search args = {query:"OLP 1.6.0", require_single:true}, no space.

Require:
- normalized source call query="1.6.0", space="OLP";
- no no-space source request.

Also test:
- missing space/query with no approved space => typed clarification;
- multiple approved spaces in one query => typed clarification;
- no guessing outside APPROVED_PRODUCT_SPACES.

## Phase 7 — Browser C
UI:
- progress WMB 24Q1
- health WMB 24Q1
- readiness OLP 1.6.0
- standalone release list WMB

Require typed source limitation for analytics, correct list for standalone search, no generic error.

## Phase 8 — retained regression
At minimum:
- Batch 3
- member/sprint/team time accounting
- team.capacity guard
- portfolio.overview
- DMS-380 48h / 6 worklogs
- dummy-55

## Audit
0 local factual reads.
0 tenant-wide scans.
0 mutations.
No no-space /versions call for queries that contain a unique approved space.

## Verdict
Use exactly one:
- AGENT_CORE_V4_BATCH4_ROUTING_GREEN_A217B
- AGENT_CORE_V4_BATCH4_ROUTING_RED_A217B

If GREEN:
recommend immutable Batch 4 checkpoint, then perform the queued self-introspection UX patch before Batch 5.

If RED:
identify first failing boundary and STOP.

Do not modify code.
