# A217B — Agent Core v4 Batch 4 Release-Routing Re-Gate

**Verdict:** `AGENT_CORE_V4_BATCH4_ROUTING_RED_A217B`
**Classification:** `RED_DEFERRED_TURN_OVEREXTENSION`
**START_HEAD / test base:** `022daf6fd478e9da91fbd99552046dd4daea3603`
**Date:** 2026-09-26

---

## Owner fix under test

Commits `ca2d190` (deferred runtime completion for resolver skills), `ae348a0`
(completion metadata behind catalog API), `944bf0f` (release.search scope
hardening + `runtime_autocomplete=False` + procedure), `d96fef2` (2 regression tests).
Diff vs A217 base `17a7a0d` touches exactly: `agent_core_v4.py`, `wave_s1.py`,
`test_agent_core_v4_batch4.py` (+ docs/spec).

Services: UI 5175 (PID 47416, [::1]), agent 8212 (PID 46506 @ 022daf6),
task-api 8241 (PID 81954, SSE 48 tools), MCP-SWTR 3000 (PID 29268).

## Phase 0 — architecture invariant: GREEN

1. Generic declarative metadata: `SkillSpecV4.runtime_autocomplete` (default `True`);
   `SkillCatalogV4.runtime_autocomplete_allowed(loaded)` API. Deterministic READY mint
   (`agent_core_v4.py:1308`) now gated on `completion_satisfied AND runtime_autocomplete_allowed`;
   when deferred, a synthetic `decision="continue"` (`completion="runtime_contract_deferred"`)
   is appended and the planner gets one more bounded turn.
2. Genericity proven: of 61 registry skills, **only `release.search`** declares
   `runtime_autocomplete=False`; defaults verified (unknown skill → allowed, empty → allowed,
   marked skill → deferred, mixed → deferred). No release-metric skill-id branch in Agent Core;
   no semantic pre-pass or phrase router added.
3. release.search hardening is argument normalization in the capability: a unique approved
   product-space token inside `query` is promoted to `space` and stripped from the release
   query; missing/ambiguous space → typed `V4NeedsClarification` **before any source call**;
   values restricted to `APPROVED_PRODUCT_SPACES`.
4. dummy-55 / plugin registry: 13/13 GREEN.

## Phase 1 — tests: GREEN

`test_agent_core_v4*.py` + `test_v4*.py` = **192/192** (190 retained + 2 new owner tests:
declarative non-autocomplete resolver; unique-space recovery from query arg). Zero unexplained failures.

## Phase 2 — standalone release.search regression: **RED (first failing boundary)**

| form | runs | outcome |
|---|---|---|
| `релизы WMB` | 2 | 2/2 COMPLETED, exact catalog [24Q1, 24Q2, 25Q1], no exhaustion |
| `покажи версии WMB` | 2 | 2/2 COMPLETED, exact catalog |
| `релизы OLP` (probe) | 3 | 3/3 COMPLETED |
| `релиз 24Q1 в WMB` (probe, singular) | 3 | 3/3 COMPLETED |
| `релиз 25Q1 в WMB` (probe, singular) | 3 | 1/3 COMPLETED, 2/3 FAILED (pivot → release.health) |
| **`релиз 1.6.0 в OLP` (spec-named)** | **5** | **0/5 FAILED** |

**D-A217B-1.** The spec-named standalone identity goal `релиз 1.6.0 в OLP` fails 5/5:
trajectory = space.resolve → release.search (correct, space-scoped, identity resolved) →
deferred continue → **planner loads `release.scope` (1/5) or `release.health` (4/5) and invokes
it** → typed `v4_capability_unavailable` FAILED. No `release.search` data in the response
(`data.results` empty for the goal; completion=None). Spec requirement "release.search still
completes successfully" violated; pre-fix behavior (auto-completion) returned the identity
COMPLETED for exactly this goal class — the deferred turn regressed standalone singular
identity goals (non-deterministic: 4/12 singular-goal runs complete, 8/12 pivot).

Root cause: the deferred turn hands the terminal decision to the planner; for a bare
single-release reference the planner frequently over-extends to a deeper analytics skill
whose empty-membership guard then fails the whole request. The procedure update ("release.search
alone is only identity/directory output") does not constrain the planner's choice on the
deferred turn.

## Phase 3 — A217 failing progress forms: D-A217-1 CLOSED (10/15 by strict trajectory)

- `прогресс релиза 24Q1 в WMB` **5/5**: space.resolve → release.search → `release.progress`
  with canonical UUID `7a84006f-…` → typed `v4_capability_unavailable`
  ("release-to-task membership"). A217: 7/7 early-termination → now 0.
- `release progress for 24Q1 in WMB` **5/5**: same exact trajectory.
- `готовность релиза OLP 1.6.0` 5/5: space.resolve → release.search (space recovered from
  query — A217's no-space 400 gone) → **`release.health`** (not `release.progress`) → typed
  SC. Deviates from the spec's literal "release.progress MUST" (see F2), but the analytics
  capability executes and terminates typed; no early termination, no no-space call.
- Across all 15 P3 runs: **0 release.search-only terminal answers, 0 no-space `/versions` calls**
  (both A217 RED signatures eliminated).

## Phase 4 — retained release.health: GREEN 6/6

`здоровье релиза 24Q1 в WMB` 3/3 + `здоровье релиза 1.6.0 в OLP` 3/3: `release.health`
actually executes (A217: 2/2 early-terminated), canonical UUID, typed `v4_capability_unavailable`
("release.health requires authoritative release-to-task membership").

## Phase 5 — sibling Batch 4 retained: GREEN 8/8

release.blockers 2/2, release.dependencies 2/2, release.risk_queue 2/2 (all typed SC,
canonical UUIDs, no zero-as-proof), portfolio.overview 2/2 exact parity
(DMS-SPRNT-3 73/18/55/2/31, OLP-SPRNT-8 70/2/68/6/52, WMB-SPRNT-2 1/1/0/0/0,
CRPV+STS NO_CURRENT_SPRINT) — A217 parity unchanged.

## Phase 6 — source-scope hardening: GREEN 17/17

QA capability-level probe against the REAL production adapter (live task-api), recording
every source-boundary `search_versions_bounded` call:
- `{query:"OLP 1.6.0", require_single:true}` (no space) → normalized source call
  `(query="1.6.0", space="OLP")`, canonical id `20ba588e-…`, zero no-space calls.
- `{query:"WMB 24Q1", require_single:true}` → `(24Q1, WMB)`, canonical `7a84006f-…`.
- `{}` / `{query:""}` → typed clarification, **zero source calls**.
- `{query:"WMB OLP 1.0"}` (multi-space) → typed clarification with options {OLP, WMB}, zero calls.
- `{query:"FOO 1.0"}` (non-approved token) → typed clarification, never guessed as space.
- Explicit `{space:"OLP", query:"1.6.0"}` → unchanged normal path.

## Phase 7 — Browser C: GREEN 4/4

- progress WMB 24Q1: FAILED typed, `release.progress` in trajectory, source limitation visible.
- health WMB 24Q1: FAILED typed, `release.health` executed, limitation visible.
- readiness OLP 1.6.0: FAILED typed via `release.health`, limitation visible (F2 routing).
- standalone `релизы WMB`: COMPLETED, full catalog [24Q1, 24Q2, 25Q1] rendered.
- No generic errors, no identity-only early answers on analytics forms, no leaks, no fake zeros.
- Screenshots: `qa_217b_browser_c/`.

## Phase 8 — retained regression: GREEN 6/6

Fresh in-window oracle (sprint window 2026-09-13..27): bottlenecks DMS active=55 EXACT;
distribution total=73 EXACT; member.time_spent Semavin **64.0h/8** EXACT;
sprint.time_spent DMS-SPRNT-3 **428.5h/65** EXACT; DMS-380 **48.0h/6** EXACT (A215D parity);
team.capacity guard typed `v4_capability_unavailable` (estimates precondition). dummy-55 13/13.

## Audit (post-fix task-api window, 1042 lines): GREEN

- local factual `GET /api/v1/tasks` reads: **0**
- mutations (POST/PUT/DELETE/PATCH): **0**
- no-space `/versions` calls: **0** (all 7 pre-fix, A217 "готовность" runs, line ≤6671)
- `task-query`: 44 calls, **44/44 space-scoped**, 44/44 release-scoped (bounded membership path)
- sprint reads: all `complete=true` (bounded); 0 5xx in window.

## Findings

**D-A217B-1 (blocking, first failing boundary — Phase 2):**
Deferred-autocomplete turn over-extension on standalone singular release-identity goals.
`релиз 1.6.0 в OLP` 0/5 FAILED (planner pivots to release.scope/release.health on the deferred
turn → typed fail-closed, identity data not surfaced). Singular-goal completion is
non-deterministic (24Q1/WMB 3/3, 25Q1/WMB 1/3, 1.6.0/OLP 0/5); list goals 10/10.
Proposed owner fix (declarative, no intent routing): strengthen the release.search skill
procedure for the deferred turn — "if the user's goal is the release itself (identity/directory)
and no analytics goal is present, finish with the release.search results" — and/or make the
deferred-continue decision carry a hint that terminal planner READY is an accepted outcome;
add a non-mocked regression: bare single-release reference must end COMPLETED with
release.search data (or an explicit analytics pivot the user asked for).

**F2 (spec-literal deviation, non-blocking on its own):** `готовность релиза OLP 1.6.0` routes
to `release.health` 6/6 (API+UI) instead of `release.progress`. Both are release analytics
capabilities terminating in the same typed SOURCE_CONDITIONAL; safe, no fabrication. If the
owner requires progress specifically, that is procedure-wording territory (health/readiness
synonyms), same LLM-sibling-routing class as A215/A216 F1.

**F3 (observation):** the deferred-continue mechanism works exactly as designed
(synthetic `continue` observed in trajectories, zero loop exhaustion, zero budget failures);
the failure mode is the planner's free choice on that turn, not the mechanism.

## Verdict

`AGENT_CORE_V4_BATCH4_ROUTING_RED_A217B` — STOP. No Batch 5.

D-A217-1 (the A217 blocker) is CLOSED at the protocol level: 0 early release.search-only
terminals across 21+ analytics runs, release.progress/health/blockers/dependencies/risk_queue
all execute and terminate typed, no-space source calls eliminated (Phase 6 17/17), portfolio
and all retained regressions exact. The re-gate fails on a new first-failing boundary —
Phase 2 standalone singular release-identity goals (D-A217B-1): the deferred turn lets the
planner over-extend to an analytics skill and fail the request, where pre-fix behavior
returned the identity COMPLETED. Owner fix is a bounded procedure/deferred-hint change on
release.search (no Agent Core routing), then re-gate Phase 2 (incl. `релиз 1.6.0 в OLP` ≥5)
and re-confirm Phases 3–5.
