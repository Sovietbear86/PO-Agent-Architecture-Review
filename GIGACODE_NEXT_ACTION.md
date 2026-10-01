# GigaCode — Current Action

## ACTIVE: Assignment A229F1 — Functional pre-gate before latency re-gate

Role: QA/adversarial tester only. Do not modify production/frontend/backend/plugin/test/config code.

A229R1 latency measurement is PAUSED. First certify two manual-PO findings:
1. one-turn conversational continuation;
2. task creation-period filtering.

## P0 — integrity / regression

1. Pull current branch; record START_HEAD and clean worktree.
2. Run focused tests:
   - dialogue-context planner/API tests;
   - task created-period tests;
   - task catalog/plugin registry tests;
   - retained task search tests.
3. Run full V4 blast-radius.
4. Run frontend tsc/build and focused Task API tests.
5. Any unexplained regression => RED STOP.

## P1 — dialogue continuation

Use one browser session.

Turn 1:
`Покажи задачи Калачанова в пространстве STS созданные за последние 2 дня`

After the response, send:
`Помоги`

Require:
- same session_id;
- planner payload contains one previous completed dialogue turn separately from source entity context;
- second turn is interpreted as continuation of the previous conversational intent/offer, not as a generic standalone ping;
- previous answer/query is NOT used as source evidence;
- no capability argument may be grounded solely from dialogue_context;
- factual entities used in source calls must still come from current query or source-validated session_context/resolver observations;
- new unrelated standalone query after that must not inherit the previous intent.

Also run:
`а за неделю?`
after a completed person+space created-period query.

Require:
- prior source-validated person/space may be reused through session_context;
- new relative period is taken from the current user turn;
- exact source-backed result;
- no phrase-specific router.

## P2 — explicit created-period task search

Query:
`Покажи задачи Калачанова в пространстве STS созданные за период с 29.09.2026 по 01.10.2026`

Build an independent REAL AS21 oracle from the same bounded canonical person+STS corpus using authoritative source created_at.

Require:
- planner loads/calls `task.search_created`;
- created_period is passed as raw user wording, not planner-invented ISO literals;
- person resolves source-backed;
- space=STS preserved;
- exact task-key/count parity vs independent timestamp oracle;
- returned rows expose created_at evidence;
- zero unrelated tasks outside the inclusive date range;
- 0 local factual fallback;
- 0 tenant-wide scan.

Run 5 times.

## P3 — relative created-period search

Query:
`Покажи задачи Калачанова в пространстве STS созданные за последние 2 дня`

Immediately before test, record Moscow-local current time and construct the oracle using the documented semantics:
- current calendar day plus the previous calendar day;
- from 00:00 Europe/Moscow of day N-1 through current time.

Require 5/5 exact parity and same source guards as P2.

## P4 — timestamp fail-closed control

Find or inject only through existing test fixtures a bounded corpus row with missing authoritative created_at provenance.

Require:
- capability does not use adapter fallback datetime as factual creation time;
- returns typed source-unavailable/fail-closed behavior;
- never silently excludes/retains the row to manufacture an exact period count.

No production/source mutation.

## P5 — architecture audit

Require:
- canonical 54 coverage unchanged;
- task.search_created is plugin-owned extra live skill/capability;
- no name/space/phrase-specific router;
- dialogue_context contains only one prior completed turn and is TTL/session bounded;
- dialogue_context is absent from literal-grounding authority;
- no previous response text becomes Evidence;
- no cross-session continuation leakage.

## Verdict

Exactly one:
- `AGENT_CORE_V4_FUNCTIONAL_PRE_GATE_GREEN_A229F1`
- `AGENT_CORE_V4_FUNCTIONAL_PRE_GATE_RED_A229F1`

If GREEN:
- resume A229R1 latency re-gate on this START_HEAD;
- all latency before/after measurements must use the new functional HEAD.

If RED:
- preserve first failing evidence and STOP.

Do not modify code.
