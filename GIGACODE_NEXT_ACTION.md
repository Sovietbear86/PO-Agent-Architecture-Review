# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_174_H1B_FULL_COLLECTION_PARITY_CERTIFICATION`

## Mission
Certify the owner fix for the final data-fidelity defect exposed by Assignment 173: H1B `task-search-v3` silently inherited the adapter default `max_results=50`, so large assignee collections were truncated and the answer incorrectly reported 50 as the total.

Assignment 173 already proved and ACCEPTED:
- canonical grounded-literal identity safety is fixed;
- `Задачи Гаранина` primary identity gate = 10/10 exact REAL AS21 parity;
- literal safety negatives = 6/6;
- typed multi-step loop and observation-derived assignee are working;
- Browser H0 = 5/5;
- the remaining RED is collection fidelity for H1B task search when result cardinality > 50.

The owner fix under test makes the H1B collection contract explicit: the H1B task-search executor requests the full certified live assignee window (`max_results=10000`) instead of inheriting the adapter's display-oriented default 50. This does NOT change the adapter default globally and does NOT change source authority.

QA ONLY. Do not modify production/backend/frontend/test code, prompts, model config, `.env`, registry contracts or runtime learning data.

## Required owner commits
Both MUST be ancestors before testing:
- `700b4f0dcb930c1f16e269b791e4904bd0bdedee` — H1B task-search executor explicitly requests the full 10,000-row certified collection window.
- `9fe2992f87850564561e19b67a2d45dd79f528ec` — regression test proving H1B does not inherit the adapter default 50.

## Absolute rules
- Oracle B = fresh direct REAL AS21/MCP-SWTR only. Never `/api/v1/tasks`, local DB, sync, fake, frozen, cached surrogate or an old QA report.
- Keep Qwen 3.8 and current endpoint unchanged.
- Concurrency = 1.
- Source timeout = 300s; end-to-end QA timeout may be 600s for large collections.
- Proven source outage only: 2 retries with 30s backoff.
- Exact task-key-set equality is mandatory for collection certification. Subset parity is FAIL.
- Do not accept a reported `count` unless it equals the actual returned task-key count and the fresh Oracle count.
- Do not change production code if a defect is found; localize and STOP for owner fix.
- Commit/push only the final QA report.

## Phase 0 — pull / provenance / healthy runtime
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
2. Print HEAD, git status, and this Status line.
3. Verify both required owner commits are ancestors.
4. Restart/reuse REAL MCP-SWTR + Task API + PO Agent v3 + frontend so new code is loaded.
5. `/health` must prove v3=true, semantic LLM healthy, REAL source healthy; frontend reachable.
6. Static proof from loaded production code:
   - H1B `_execute_search()` calls `adapter.search_tasks(..., max_results=10000)` (or the named H1B collection constant equal to 10000);
   - adapter's global/default `search_tasks` limit remains unchanged at 50;
   - no local DB/sync path was introduced;
   - H1B `count` is derived from the actual complete returned rows, not a fixed/capped constant.

If environment/source unhealthy, STOP before expensive tests with a proven blocker verdict.

## Phase 1 — focused unit/build gate
Run the H1/H1B unit suites, including the new:
`tests/test_agent_core_v3_h1b_full_collection.py`

Also include the previously accepted H1B grounding/planner/loop/registry tests needed to detect regressions. Require all PASS.
Run frontend typecheck/build required by the project; require PASS.

## Phase 2 — large-collection Oracle B baseline
Fetch fresh REAL Oracle B via the authoritative live assignee route for at least:
- `Kalachanov.V.V` across approved spaces;
- `Semavin.M.M` across approved spaces;
- `Garanin.R.V` across approved spaces.

Record exact current counts and exact task-key sets. Do not reuse Assignment 173 counts because source data may have changed.

At least one tested identity MUST have >50 tasks and one MUST have >300 tasks. If current live data no longer satisfies that, use another real configured team member with sufficient cardinality; record why.

## Phase 3 — H1B full-collection gate
Run fresh-session Agent A queries, concurrency=1:
- 3× `Задачи Калачанова`
- 3× `Задачи Гаранина`

For every run require:
- COMPLETED;
- canonical grounded assignee;
- H1B path when selected exposes `task-search-v3` executor metadata;
- exact task-key set == same-window Oracle B;
- returned row count == Oracle count;
- answer count == returned row count == Oracle count;
- no silent `50` cap;
- no duplicate task keys.

Any H1B run returning exactly 50 while Oracle >50 is immediate `H1B_COLLECTION_TRUNCATION_RED`.

## Phase 4 — cross-route fidelity / legacy seam observation
Run 3× `Задачи Семавина` with fresh sessions and fresh Oracle B.

The current H1B pilot selector/legacy seam may still route this query outside H1B. Do NOT modify routing in QA.
Requirements regardless of route:
- exact full collection parity;
- correct authoritative count;
- canonical identity;
- record selected runtime path/skill each run.

If fidelity differs by route, verdict `H1B_ROUTE_FIDELITY_RED`.
If both routes are exact but selector coverage differs, record it as a known H1C migration seam, not an H1B data-parity failure.

## Phase 5 — multi-step high-cardinality regression
Fresh Oracle B for the assignee of DMS-380 and the full assignee collection.
Run 3× fresh-session:
`Проверь DMS-380 и затем покажи задачи его исполнителя`

Require each run:
- real typed 2-step loop: task lookup -> task search;
- step-2 assignee comes from authoritative observation/source-backed binding;
- full step-2 task-key set == fresh Oracle B for that assignee (NOT only first 50);
- count == full Oracle count;
- no duplicate keys;
- postconditions pass.

This phase is mandatory because Assignment 173 showed Challenge A was structurally capped at 50/308.

## Phase 6 — space-filter regression
Using fresh Oracle B, run:
- `Задачи Гаранина в DMS`
- `Задачи Калачанова в WMB`
- one real high-cardinality assignee + approved space where the result remains >50, if such a current source case exists.

Require exact same-window key-set parity and constraint preservation. If no >50 per-space case exists, explicitly state that and do not invent one.

## Phase 7 — Browser C H0 regression
Run existing:
`npm run e2e:h0`

Require 5/5 PASS.

## Phase 8 — Browser C real full-collection multi-step
In real Playwright Chromium, fresh conversation:
`Проверь DMS-380 и затем покажи задачи его исполнителя`

Persist screenshot/artifacts, UI session id, correlated backend trace, loop steps and source evidence.
Require Browser C == Agent A == fresh Oracle B for the COMPLETE step-2 collection and count.

If rendering thousands of rows is intentionally summarized by UI, backend exact collection parity is still mandatory and UI must not falsely report a truncated count as total. Record rendered/sample semantics explicitly.

## Phase 9 — H1B closure decision
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_FULL_COLLECTION_PARITY_174.md`

Allowed verdicts ONLY:
- `AGENT_CORE_V3_H1B_LOOP_GREEN`
- `H1B_COLLECTION_TRUNCATION_RED`
- `H1B_AGENT_ORACLE_PARITY_RED`
- `H1B_ROUTE_FIDELITY_RED`
- `H1B_MULTI_STEP_REGRESSION_RED`
- `H1B_BROWSER_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires phases 0–8 all certified, including full >50 collection parity and Challenge A full-collection parity.

If GREEN, explicitly state:
- H1B Hermes Agent Loop is CLOSED/certified for the task lookup/search slice;
- the old selector/legacy coverage seam (if observed but fidelity-safe) moves to H1C Progressive Skill Loading;
- next architecture stage = H1C Progressive Skill Loading.

Commit/push only the final QA report and STOP.

## Start now
Execute Assignment 174 completely. Pull first, load the owner commits into a fresh runtime, establish fresh Oracle baselines, then prove that H1B no longer silently truncates large assignee collections.