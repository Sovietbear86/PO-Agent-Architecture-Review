# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_217D_ROBUST_SIGNATURE_PARITY_REGATE

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT start Batch 5.
Commit/push only the QA report.

## Baseline
A217C verdict:
AGENT_CORE_V4_BATCH4_ROUTING_RED_A217C
Classification:
RED_ROBUST_PLANNER_SIGNATURE_DRIFT

The first failing boundary was platform-wide:
RobustSkillNativePlannerV4.next_decision did not accept runtime_guidance while the base runtime now passes it.
Result: 100% V4 queries failed before LLM/source execution.

## Owner fix
Commits:
- b2c531993fa94eeed220f758cb465b007702d72e
- 1c0fa65f89f9c158be85e3e2c26d93cfc8e01460
- fd6ba94cb057c713eb95e6ab21508fa17a247460

Fix:
1. RobustSkillNativePlannerV4.next_decision now mirrors the base keyword contract including runtime_guidance.
2. Robust planner payload forwards runtime_guidance.
3. Broken Batch4 metadata test now constructs SkillCatalogV4 from registry.skills()/capability_specs().
4. Permanent signature-parity regression test added so future base/robust drift fails immediately.

No new release routing logic was added.

## Goal
Restore production V4 runtime first, then fully re-run the A217C release-routing gate.

## Phase 0 — production runtime recovery
1. Pull branch, record START_HEAD, clean worktree.
2. Run planner signature-parity test.
3. Construct the production robust/pluginized runtime and execute at least 3 ordinary non-release queries.
4. Require:
   - zero TypeError;
   - normal planner call reaches LLM;
   - normal source calls execute;
   - no v4_runtime_failure.

If any generic query fails at planner entry => RED and STOP.

## Phase 1 — full V4 regression
Run:
- tests/test_agent_core_v4_planner_signature_parity.py
- tests/test_agent_core_v4_batch4.py
- tests/test_agent_core_v4*.py
- tests/test_v4*.py

Zero unexplained failures.

## Phase 2 — standalone release identity
Run >=5 each:
- "релиз 1.6.0 в OLP"
- "релиз 24Q1 в WMB"
- "релиз 25Q1 в WMB"

Require:
- release.search source-backed identity;
- standalone identity => COMPLETED;
- zero release.scope/health/progress/risk/blockers/dependencies calls;
- deterministic >=5/5.

List goals:
- "релизы WMB"
- "покажи версии OLP"
must remain exact catalog COMPLETED.

## Phase 3 — requested release analytics
Run:
- progress WMB 24Q1 >=5
- health WMB 24Q1 >=3
- readiness OLP 1.6.0 >=3
- blockers/dependencies/risk representative forms

Require:
- release.search may resolve identity;
- explicitly requested deeper skill executes;
- current sparse release source => typed SOURCE_CONDITIONAL;
- no fabricated zero metrics;
- no early identity-only completion for analytical intents.

## Phase 4 — no-space hardening
Capability-level:
- query="OLP 1.6.0" with no space => normalize to OLP/1.6.0
- no approved space token => typed clarification, zero source calls
- multiple approved spaces => typed clarification
- zero no-space /versions calls when unique space exists in query.

## Phase 5 — sibling Batch 4 + portfolio
Re-run:
- portfolio.overview
- release.blockers
- release.dependencies
- release.risk_queue
Require A217 parity.

## Phase 6 — Browser C
UI:
- ordinary sprint query (proves generic V4 health)
- standalone release identity
- release progress source limitation
- release health source limitation
- portfolio overview

No generic V4 ERROR.

## Phase 7 — retained regression
- sprint current/search/health
- member/sprint/team time accounting
- DMS-380 48h/6 worklogs
- team.capacity guard
- dummy-55

## Audit
0 local factual reads.
0 tenant-wide scans.
0 mutations.

## Verdict
Use exactly one:
- AGENT_CORE_V4_BATCH4_ROUTING_GREEN_A217D
- AGENT_CORE_V4_BATCH4_ROUTING_RED_A217D

If GREEN:
recommend immutable Batch 4 checkpoint, then queued self-introspection UX patch before Batch 5.

If RED:
identify first failing boundary and STOP.

Do not modify code.
