# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_217C_STANDALONE_RELEASE_IDENTITY_REGATE

## Role lock
GigaCode is QA/adversarial tester only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT start Batch 5.
Commit/push only the QA report.

## Baseline
A217B verdict:
AGENT_CORE_V4_BATCH4_ROUTING_RED_A217B
Classification:
RED_DEFERRED_TURN_OVEREXTENSION

A217 original blocker is CLOSED:
- release analytics no longer terminate at release.search;
- no-space /versions calls eliminated;
- progress/health sibling analytics execute typed fail-closed.

A217B introduced one new blocking boundary:
standalone singular release identity such as "релиз 1.6.0 в OLP" over-extends on the deferred turn into release.scope/release.health instead of finishing with release.search identity data.

## Owner fix
Commits:
- 08e8f96b93c720ed62a27714d1d59a1625f13267
- 3e483d6604f88854ab6eb903846cc898ea899155
- 68c6d986dc9148f2cd38a6ba07b3291d873d2ab5

Design:
1. No new query router and no release metric skill-id branch.
2. Generic planner payload now receives one-turn runtime_guidance only when a declaratively non-autocomplete resolver contract is already source-satisfied.
3. Generic planner rule: READY is explicitly valid for a standalone resolver/identity/directory goal; deeper skill may load only if the original query explicitly asks for that deeper deliverable.
4. Loaded skill detail exposes runtime_autocomplete metadata.
5. release.search procedure explicitly defines a direct single-release identity request as terminal and forbids inventing scope/health/progress/risk analysis.
6. Existing analytics requests must still continue beyond release.search.

## Phase 0 — architecture invariant
1. Pull branch, record START_HEAD, clean worktree.
2. Diff owner fix commits.
3. Prove:
   - no phrase router / semantic pre-pass added;
   - no hard-coded release.progress/release.health branch in runtime;
   - runtime_guidance mechanism is generic and only populated after a source-satisfied deferred resolver contract;
   - default skills unaffected;
   - dummy-55 GREEN.

## Phase 1 — tests
Run:
- tests/test_agent_core_v4_batch4.py
- full tests/test_agent_core_v4*.py
- tests/test_v4*.py

Zero unexplained failures.

## Phase 2 — standalone singular identity gate
Run each >=5:
- "релиз 1.6.0 в OLP"
- "релиз 24Q1 в WMB"
- "релиз 25Q1 в WMB"

Required:
- space.resolve as needed;
- release.search source-backed identity;
- then planner READY;
- status COMPLETED;
- release.search result data surfaced;
- zero release.scope/health/progress/blockers/dependencies/risk_queue calls;
- zero source-conditional failure;
- deterministic >=5/5 each.

List goals retained >=3 each:
- "релизы WMB"
- "покажи версии OLP"
Exact catalog parity, COMPLETED.

## Phase 3 — analytics non-regression
Re-run:
- "прогресс релиза 24Q1 в WMB" >=5
- "release progress for 24Q1 in WMB" >=3
- "здоровье релиза 24Q1 в WMB" >=3
- "очередь рисков релиза 1.6.0 в OLP" >=3
- blockers/dependencies representative forms

Requirements:
- release.search identity does NOT terminate analytics;
- requested analytics skill executes;
- current missing release membership => typed SOURCE_CONDITIONAL;
- zero standalone identity COMPLETED answers for analytics intents.

For "готовность релиза OLP 1.6.0":
release.health or release.progress is acceptable if typed SOURCE_CONDITIONAL and no fabricated metric; record routing.

## Phase 4 — runtime guidance proof
Inspect trajectories for standalone identity and analytics:
- after release.search, synthetic runtime_contract_deferred exists;
- next planner turn receives/acts consistently with deferred guidance;
- standalone => READY;
- analytics => requested deeper skill.
No planner-loop exhaustion.

## Phase 5 — source-scope hardening retained
Capability-level:
- query="OLP 1.6.0", no space => normalized to space OLP / query 1.6.0;
- missing space with no approved token => clarification, zero source calls;
- ambiguous multiple spaces => clarification;
- no no-space /versions calls.

## Phase 6 — Browser C
Real UI:
- standalone "релиз 1.6.0 в OLP" => COMPLETED identity data;
- progress WMB => typed source limitation;
- health WMB => typed source limitation;
- release list WMB => COMPLETED catalog.

No generic ERROR and no fabricated analytics.

## Phase 7 — retained regression
- portfolio.overview exact
- member/sprint/team time accounting
- DMS-380 48h/6
- team.capacity guard
- dummy-55

## Audit
0 local factual reads.
0 tenant-wide scans.
0 mutations.
0 no-space /versions for queries containing a unique approved space.

## Verdict
Use exactly one:
- AGENT_CORE_V4_BATCH4_ROUTING_GREEN_A217C
- AGENT_CORE_V4_BATCH4_ROUTING_RED_A217C

If GREEN:
recommend immutable Batch 4 checkpoint, then execute queued agent self-introspection UX patch before Batch 5.

If RED:
identify first failing boundary and STOP.

Do not modify code.
