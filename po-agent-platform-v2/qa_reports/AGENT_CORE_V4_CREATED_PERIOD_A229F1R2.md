# A229F1R2 — Created-period functional pre-gate re-run

**Verdict:** `AGENT_CORE_V4_CREATED_PERIOD_GREEN_A229F1R2`
**Date:** 2026-10-01
**QA role:** QA/adversarial tester only, zero code changes
**Branch:** `feat/core8-real-query-hardening-v2`
**START_HEAD:** `73d5011ad37e5409b5d30d4d08fc454e3325305d`
**Owner fix under re-gate:** `e35db21` (register `CapabilitySpecV4("task.search_created")`) + `3610144` (refresh status-normalization fixture) — plugin-only, minimal.

---

## P0 — registry / integrity — GREEN

| # | Item | Result |
|---|---|---|
| 1 | Pull + START_HEAD + clean worktree | `73d5011` (ff from `9598258`); tracked worktree clean (untracked QA artifacts only) |
| 2 | Core byte-identical vs `c41b00c` | **PASS 4/4** (git blob hashes): `contracts.py` 20d93d5d, `agent_core_v4.py` 52100ca1, `agent_core_v4_robust.py` 3bdb4d09, `api/v1/__init__.py` 8f4b1663 — dialogue-context revert stays real at byte level |
| 3 | Production registry init | **PASS** — `discover_v4_plugins()` succeeds, **no binding mismatch**, `task.search_created` present in CAPABILITIES (args `created_period`/`reference`/`space`) and in SKILLS; 71 capabilities / 69 skills / 13 plugins |
| 4 | Focused + full test battery | created-period 5/5, sprint single-read 1/1, status-normalization 2/2 (refreshed fixture), **full V4 blast 238/238** (was 51F/187P at A229F1R), frontend tsc + vite build GREEN, task-api `test_swtr_assignee_canonical` 12/12 |
| 5 | Live smoke `Спринты в DMS` | **COMPLETED** `skill_native_v4`, `space.resolve`→`sprint.list` (3 sprints), **no `runtime_init_error`** — the A229F1R init failure is gone |

Agent restarted on `73d5011` (PID 49693, V4-enabled, task-api mode). Runtime initializes cleanly.

## P1 — explicit created-period — GREEN 5/5

Query: `Покажи задачи Калачанова в пространстве STS созданные за период с 29.09.2026 по 01.10.2026`
Independent REAL AS21 oracle: direct MCP-SWTR `find_units_by_filter` (`assigned_to="Kalachanov.V.V" AND space="STS"`, 28 pages / 2800 rows, authoritative raw `unit.createdAt`), window `2026-09-29T00:00:00+03:00 .. 2026-10-01T23:59:59.999+03:00` (inclusive) → **96 tasks, 0 missing created_at**.

| Run | status | capability | keys | parity | in-window | created_at exposed | local | tenant |
|---|---|---|---|---|---|---|---|---|
| 1 | COMPLETED | task.search_created | 96 | **exact** | yes | yes | 0 | 0 |
| 2 | COMPLETED | task.search_created | 96 | **exact** | yes | yes | 0 | 0 |
| 3 | COMPLETED | task.search_created | 96 | **exact** | yes | yes | 0 | 0 |
| 4 | COMPLETED | task.search_created | 96 | **exact** | yes | yes | 0 | 0 |
| 5 | COMPLETED | task.search_created | 96 | **exact** | yes | yes | 0 | 0 |

Requirement checks: planner selects `task.search_created` (5/5); `created_period` passed as **raw user wording** `"с 29.09.2026 по 01.10.2026"` (no planner-invented ISO); person resolved source-backed (`source_assignee=Kalachanov.V.V` via `assignees/resolve`); STS preserved; resolved window `2026-09-29T00:00:00+03:00 .. 2026-10-01T23:59:59.999999+03:00`, `period_kind=explicit_inclusive_dates`; source scan bounded (`task-query?space=STS&assignee=Kalachanov.V.V`, 0 tenant-wide, 0 local fallback); `source=REAL_AS21`.
**Drift protocol:** post-batch oracle rebuild → 96→96, **zero drift** (no added/removed keys during the matrix).

## P2 — relative period «последние 2 дня» — GREEN 5/5 (drift-aware)

Query: `Покажи задачи Калачанова в пространстве STS созданные за последние 2 дня`
Before-batch oracle (T0 `2026-10-01T17:20:30+03:00`): window `2026-09-30T00:00:00+03:00 .. T0` → **76 tasks, 0 missing created_at**.

| Run | status | capability | keys | parity vs before | in-window | created_at | local | tenant |
|---|---|---|---|---|---|---|---|---|
| 1 | COMPLETED | task.search_created | 76 | exact | yes | exposed | 0 | 0 |
| 2 | COMPLETED | task.search_created | 76 | exact | yes | exposed | 0 | 0 |
| 3 | COMPLETED | task.search_created | 76 | exact | yes | exposed | 0 | 0 |
| 4 | COMPLETED | task.search_created | 76 | exact | yes | exposed | 0 | 0 |
| 5 | COMPLETED | task.search_created | 76 | exact | yes | exposed | 0 | 0 |

Semantics verified: `created_period` raw `"последние 2 дня"`; `period_kind=last_2_calendar_days`; `created_from=2026-09-30T00:00:00+03:00` (00:00 MSK of previous calendar day) and `created_to` = **each run's own execution time** (17:20:51 → 17:32:58 across runs, monotonically advancing as required).
**Drift protocol:** post-batch oracle (T1 `17:36:49`) → 76→76, **zero drift**; per-run rule `before.keys ⊆ run.keys ⊆ after.keys` holds for all 5 (no lost in-window tasks, no phantom keys). STS is active (corpus moved 2800→2780 over the session), so drift could not be excluded a priori — the re-probe protocol was exercised and no drift occurred in the window.

## P3 — fail-closed timestamp provenance — GREEN (fixtures only)

- One bounded row lacking `_canonical_created_at_from_source` → **typed `AS21SourceUnavailable`** ("cannot prove an exact created-period result (1 rows missing created_at)") — no partial/false result. Owner's fixture test `test_created_period_search_fails_closed_if_created_at_is_not_source_backed` passes.
- All-provenance corpus with an out-of-window row → `count=0`, `source=REAL_AS21` (legit REAL_EMPTY, not fail-closed).
- Unparseable period wording → typed `ValueError` (generic message; no silent pass, no invented dates).

## P4 — architecture audit — GREEN

- Canonical 54 catalog **unchanged** (zero diff `f1141aa..73d5011` on `skill_catalog.py` + all Agent Core files); registry now 69 skills = canonical + 15 extra live plugin capabilities incl. the new one.
- `task.search_created` is **extra plugin-owned** — referenced only under `v4_plugins/` (zero hits outside).
- **Zero dialogue-context/Core/Harness/API session changes** (Core 4/4 byte-identical to `c41b00c`; no `api/` diff).
- **Zero phrase/person/space hardcode** in the created-period handler (generic calendar parsing only; the only "WMB" hit is an unrelated A196 comment in the attachments handler).
- **Zero local factual date cache** (no `lru_cache`/TTL/memoization in the handler; every execution re-reads the bounded source).
- **No planner-invented dates** (skill procedure: "pass created_period as the raw user wording exactly; do not invent ISO dates"; live runs confirm raw wording in all 10 runs).
- **No unbounded scan** (corpus bounded by person+space; `limit=100&max_pages=100`; 0 tenant-wide scans across all 10 live runs).

## Operational note (non-blocking, environmental)

The `api.ai.sbt` LLM endpoint imposed a **429 rate-limit penalty** during this session: back-to-back multi-turn runs (≈25-30 LLM calls/min) tripped it, failing runs with `planner failed robust bounded repair: ['HTTPStatusError' x4]` (fail-closed, 0 source calls, no data). After a ~5-7 min cooldown the endpoint recovered and all runs succeeded. Mitigation used: **75 s spacing between matrix runs**. This is an environmental constraint, not a defect in the created-period capability; recommend the owner keep an LLM backoff/pace guard in the harness (A229 R6 lineage) before any high-frequency re-gates.

## Services left running

agent 8004 (PID 49693 @ `73d5011`), task-api 8241 (PID 96598), MCP-SWTR 3000 (PID 97012), vite 5175 [::1] (PID 39280). Agent log `/private/tmp/qa229f1r2_agent.log`; evidence `/private/tmp/qa229f1r2/` (oracle_p1/p2 before+after, p1_runs.json, p2_runs.json, per-run segments).

**Recommendation:** certify `73d5011` as the functional created-period checkpoint and **resume the A229R1 latency re-gate** on this HEAD.
