# GigaCode — Current Action

## ACTIVE: Assignment A229F1R — Created-period functional pre-gate

Role: QA/adversarial tester only. Do not modify production/frontend/backend/plugin/test/config code.

Important:
- the dialogue-context experiment has been fully reverted;
- stable Harness/Core/API session behavior must remain identical to pre-experiment A229R1 state;
- conversational continuity is NOT part of this assignment;
- only the new plugin-owned `task.search_created` capability is under functional re-gate.

## P0 — integrity

1. Pull current branch; record START_HEAD and clean worktree.
2. Prove these files are byte-identical to commit `c41b00c972e3710bd45d59744196e3c0d63ec327`:
   - `src/po_agent/harness/contracts.py`
   - `src/po_agent/harness/agent_core_v4.py`
   - `src/po_agent/harness/agent_core_v4_robust.py`
   - `src/po_agent/api/v1/__init__.py`
   - `tests/test_agent_core_v4_robust_protocol.py`
3. Run focused created-period tests + task catalog/plugin registry tests.
4. Run full V4 blast-radius.
5. Run frontend tsc/build and focused Task API tests.

Any unexplained regression => RED STOP.

## P1 — explicit created-period search

Query:
`Покажи задачи Калачанова в пространстве STS созданные за период с 29.09.2026 по 01.10.2026`

Build an independent REAL AS21 oracle from the same bounded canonical person+STS corpus using authoritative source created_at.

Run 5 times.

Require:
- planner loads/calls `task.search_created`;
- `created_period` is passed as raw user wording;
- person resolves source-backed;
- STS constraint preserved;
- exact task-key/count parity;
- every returned row lies inside the inclusive source timestamp range;
- returned payload exposes created_at;
- 0 local factual fallback;
- 0 tenant-wide scans.

## P2 — relative created-period search

Query:
`Покажи задачи Калачанова в пространстве STS созданные за последние 2 дня`

Immediately before testing, record Europe/Moscow current time and independently build the oracle with the documented semantics:
- current calendar day + previous calendar day;
- start = 00:00 Europe/Moscow of previous calendar day;
- end = current execution time.

Run 5 times.

Require exact parity and the same source guards as P1.

## P3 — fail-closed timestamp provenance

Using existing test fixtures only, verify a bounded row lacking authoritative created_at provenance does not participate in an exact period result.

Require typed SOURCE_UNAVAILABLE/fail-closed behavior.

No production/source mutation.

## P4 — architecture audit

Require:
- canonical 54 unchanged;
- `task.search_created` is extra plugin-owned live capability;
- no phrase/person/space-specific router;
- no Harness/Core/API session changes from this fix;
- no local factual date cache;
- no invented ISO date literals by planner;
- no unbounded source scan.

## Verdict

Exactly one:
- `AGENT_CORE_V4_CREATED_PERIOD_GREEN_A229F1R`
- `AGENT_CORE_V4_CREATED_PERIOD_RED_A229F1R`

If GREEN:
- resume A229R1 latency re-gate from the current functional HEAD.

If RED:
- preserve first failing evidence and STOP.

Do not modify code.
