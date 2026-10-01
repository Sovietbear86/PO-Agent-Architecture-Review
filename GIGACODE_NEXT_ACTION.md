# GigaCode — Current Action

## ACTIVE: Assignment A229F1R2 — Created-period functional pre-gate re-run

Role: QA/adversarial tester only. Do not modify code.

Owner fix is intentionally minimal:
- added missing `CapabilitySpecV4("task.search_created", ...)`;
- refreshed one stale status-normalization fixture;
- no Core/Harness/API session changes.

## P0 — registry/integrity

1. Pull current branch; record START_HEAD and clean worktree.
2. Prove these files remain byte-identical to `c41b00c972e3710bd45d59744196e3c0d63ec327`:
   - `src/po_agent/harness/contracts.py`
   - `src/po_agent/harness/agent_core_v4.py`
   - `src/po_agent/harness/agent_core_v4_robust.py`
   - `src/po_agent/api/v1/__init__.py`
3. Instantiate/discover the production V4 plugin registry and prove:
   - `task.search_created` exists in CAPABILITIES;
   - binding mismatch = none;
   - agent runtime initializes successfully.
4. Run:
   - focused created-period tests;
   - status-normalization tests;
   - task catalog/plugin registry tests;
   - full V4 blast-radius;
   - frontend tsc/build;
   - focused Task API tests.
5. Run a live smoke `Спринты в DMS` and require normal V4 execution, not runtime_init_error.

Any RED => preserve evidence and STOP.

## P1 — explicit created-period search

Query:
`Покажи задачи Калачанова в пространстве STS созданные за период с 29.09.2026 по 01.10.2026`

Build a fresh independent REAL AS21 oracle from the bounded canonical Kalachanov+STS corpus using authoritative source created_at.

Run 5 times.

Require:
- planner selects `task.search_created`;
- created_period is raw user wording;
- source-backed person resolution;
- STS preserved;
- exact task-key/count parity 5/5;
- all returned rows fall inside the inclusive date interval;
- created_at exposed in result/evidence;
- 0 local factual fallback;
- 0 tenant-wide scans.

## P2 — relative period search

Query:
`Покажи задачи Калачанова в пространстве STS созданные за последние 2 дня`

Immediately before each batch, record Europe/Moscow current time and build the oracle using:
- start = 00:00 MSK of previous calendar day;
- end = execution time.

Because STS is active, document oracle drift protocol and re-probe if the source changes during the 5-run matrix.

Require exact source parity 5/5 after accounting only for documented source drift.

## P3 — fail-closed provenance

Using test fixtures only, prove that missing authoritative created_at provenance produces typed fail-closed/source-unavailable behavior.

No production/source mutation.

## P4 — architecture audit

Require:
- canonical 54 unchanged;
- `task.search_created` is extra plugin-owned capability;
- zero dialogue-context/Core changes;
- zero phrase/name/space hardcode;
- zero local factual date cache;
- no planner-invented dates;
- no unbounded scan.

## Verdict

Exactly one:
- `AGENT_CORE_V4_CREATED_PERIOD_GREEN_A229F1R2`
- `AGENT_CORE_V4_CREATED_PERIOD_RED_A229F1R2`

If GREEN:
- resume A229R1 latency re-gate on this certified functional HEAD.

If RED:
- preserve first failing evidence and STOP.

Do not modify code.
