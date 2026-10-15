# AGENT_CORE_V4_GOAL_STATE_PRESERVATION_REGATE_A229M22AR2

**Verdict:** `AGENT_CORE_V4_GOAL_STATE_PRESERVATION_GREEN_A229M22AR2`
**TESTED_HEAD:** `1cd644618fcda5e9db633528ca097d5ab1d4751d`
(owner credit-gap fix `0309d7d` private cross-turn credit + `d4af643` pass server-owned
continuation evidence into coverage only + `b46a658` three two-turn regressions)
**Role:** QA only; zero production/test/config edits. STOP-at-first-RED; no first RED found.

## Executive summary

D-A229M2.2AR-1 (carried REAL_AS21 observations restored to the planner but never credited by
the coverage guard → structural NEEDS_CLARIFICATION dead-loop) is **CLOSED**. The API now
feeds server-stored `continuation.observations` into `guard_completed_goal_coverage` as a
**private credit-only** evidence view, re-validated for REAL_AS21 provenance, canonical
compact shape and size/quantity bounds. On the real DMS-267 card, a two-turn
lookup→hierarchy continuation now returns **COMPLETED** crediting both goals, with **no
duplicate lookup read**, **public `data.results` current-turn only**, and a **user-facing
answer that addresses both requested goals**. Negative/parity/security all hold.

## P0 — baseline + full regression: GREEN

- TESTED_HEAD `1cd6446`. Delta `072d5b4..1cd6446` confined to
  `api/v1/__init__.py` (+1: `trusted_prior_observations=continuation.observations`),
  `api/v1/goal_coverage.py` (+48/−3: `_credit_prior_observations` + guard/carry wiring),
  `tests/test_v4_goal_coverage.py` (+60). **No planner / no registry / no Core / no UI edit.**
- **Core 6/6 byte-identical** to certified `6fb335d`: agent_core_v4 `52100ca1`, robust
  `3bdb4d09`, reliable `1f7562dc`, completion `cf75a6d6`, plugin registry `d82929d1`,
  llm/real `1cc10e12`.
- Focused `test_v4_goal_coverage.py`: **20/20** (incl. the 3 new two-turn tests
  `..._credit_is_private_and_does_not_repeat_lookup`,
  `..._prior_observation_with_unknown_source_cannot_gain_credit`,
  `..._second_turn_still_fails_closed_if_hierarchy_not_executed`).
- Synthesis + browser-API-contract: **23/23**. Full V4 blast
  `test_agent_core_v4*.py` + `test_v4*.py`: **290 passed / 0 failed** (was 287 + 3 new).
  Task API SWTR canonical/timestamps/partial: **16 passed**. Frontend build: exit 0.
- Worktree clean apart from documented pre-existing `M GIGACODE.md`.

## P1 — first boundary (3× REAL AS21 M2, BOTH_ON isolated stack): GREEN 3/3

Isolated QA agent on `1cd6446`, `PO_AGENT_V4_GOAL_COVERAGE_GUARD=true` +
`PO_AGENT_V4_GOAL_CONTINUATION=true`, synthesis elision OFF. Source oracle: DMS-267 parent
DMS-253 (decomposition, `get_unit_links`). Each trial: T1 `Покажи задачу DMS-267 и её
иерархию` → T2 continuation `иерархию DMS-267` inside TTL. **All 3 trials, all 9 assertions:**

| assertion | trial0 | trial1 | trial2 |
|---|---|---|---|
| A T2 COMPLETED | ✓ | ✓ | ✓ |
| B both goals credited (no `v4_goal_coverage_incomplete`) | ✓ | ✓ | ✓ |
| C no duplicate lookup read (files Δ=0) | ✓ | ✓ | ✓ |
| D hierarchy executed this turn | ✓ | ✓ | ✓ |
| E public `results` this-turn only (`task.lookup` absent) | ✓ | ✓ | ✓ |
| F answer contains parent DMS-253 | ✓ | ✓ | ✓ |
| F answer contains lookup facts (Resolved/Semavin/DMS/Задача) | ✓ | ✓ | ✓ |
| G no raw-card/source_data/valueAsString/backgroundColor/parameters | ✓ | ✓ | ✓ |
| H no `continuation_*` keys in public JSON | ✓ | ✓ | ✓ |

Observed T2 shape each trial: `status=COMPLETED`, `goal_coverage=None`,
`loaded_skills=[task.lookup, task.hierarchy]`, public `results=[task.hierarchy]`; answer
renders both the DMS-267 lookup table (Key/Название/Статус Resolved/Исполнитель Семавин/
Проект DMS/Тип Задача) **and** the `## Иерархия` chain rooted at CRPV-90180 via DMS-253.
The previous false «Не удалось подтвердить: task_lookup: DMS-267» claim is gone.

## P2 — generalization + negative/parity/security: GREEN

- **M1** (two people) — planner executed both person collections in one turn → COMPLETED with
  all goals proven → guard inert (correct: no continuation needed).
- **M4** (3 goals) — T1 NC (lookup g2 proven); single-option continuation executed hierarchy
  only → lookup credited (g2 ∈ proven) but the person goal genuinely remained unexecuted →
  correct NEEDS_CLARIFICATION (fail-closed, not a credit gap; `files Δ=0`).
- **C5** (links) — with a relations-naming continuation: T1 NC (lookup g1 proven, relations g2
  unproven) → T2 **COMPLETED**, `goal_coverage=None`, `loaded=[task.lookup, task.hierarchy]`,
  public `results=[task.hierarchy]`, answer covers **both** lookup facts and «Связанные
  задачи»; lookup credited from prior even where current results were sparse. A weaker
  phrasing that did not execute a relations-proving capability correctly stayed NC.
- **Offline credit-safety (production guard, 10 cases):** valid prior REAL_AS21 + this-turn
  hierarchy → COMPLETED, public=this-turn only; **private envelope** (returned COMPLETED
  response never contains the prior row; answer intact; no continuation keys); unknown
  `source`, `source_unavailable`, `source_complete=false`, **non-canonical raw-card fields**,
  >6 priors, >8192 B priors → **credit refused, still NC**; `preserve_state=false` →
  prior entirely ignored (flag-OFF parity); prior-lookup-alone with hierarchy not executed →
  still NC; FAILED response passes through unchanged (never converted to COMPLETED).
- **Security/continuation battery (unchanged by delta, re-verified):** TTL 15 min, expiry
  sweep on insertion, 100-entry bound with oldest eviction, one-shot consumed token
  (replay → typed `clarification_context_lost`, state destroyed), fresh query pops pending,
  invalid option keeps state; client request surface limited to
  `query`, `session_id`, `clarification_id`, `clarification_option` (observations not
  injectable).
- **Source audit (BOTH_ON session):** 0 local `/api/v1/tasks` reads, 0 task-api mutations,
  0 unscoped task-query (both task-query calls assignee+space-scoped), 0
  `continuation_observations` in any HTTP response, 42 LLM 200 / 0 429 this session.

## OPEN deployment blocker (unchanged, openly stated)

Session authentication/ownership is still absent: `session_id` is client-chosen and
unauthenticated service-wide; a client that can present a matching `session_id` +
`clarification_id` within TTL could consume another user's continuation. Fail-safe behavior
on wrong/expired/consumed tokens is correct, but the feature is **not deployment-secure**
until authenticated session ownership exists. This remains a release blocker independent of
this fix.

## Services after QA

- agent 8004 restored on `1cd6446`, **both goal flags false** (public default), synthesis OFF,
  healthy; task-api 8241; MCP-SWTR 3000.
- QA artifacts (untracked): `/private/tmp/qa229m22ar2_*` (p1/p2a/p2b/c5/security scripts +
  JSON evidence), `qa_229m22a_agent.sh` (QA launcher).

## Verdict

`AGENT_CORE_V4_GOAL_STATE_PRESERVATION_GREEN_A229M22AR2` — P0, P1 (first boundary, 3/3), and
P2 all pass; the credit-only continuation is private, bounded, provenance-validated and
generalizes across lookup/hierarchy/relations/person-collection goals with correct answer
coverage; flag-OFF and security semantics preserved. Session-auth blocker remains OPEN.
Per spec: no checkpoint, no feature-default flip, no A229M2.2B until owner review.
