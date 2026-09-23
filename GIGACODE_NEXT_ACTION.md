# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_208_PRE_S2_MANUAL_QUERY_CONSISTENCY`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT start Wave S2.
Do NOT add skills.

## Stable rollback
Wave S1 is GREEN at:
`checkpoint/v4-wave-s1-green@ce64264c868afd73743d5daafdeaee767e07adef`

A207 result:
- sprint.scope GREEN;
- sprint.velocity GREEN;
- sprint.throughput GREEN;
- sprint.wip GREEN;
- release.search SOURCE_CONDITIONAL due proven /versions 502;
- zero local factual reads;
- plugin invariant GREEN.

## Why A208 exists
Manual Browser C testing exposed three consistency gaps that must be closed before S2:

1. `wip спринта по DMS` could fail even though `показать текущий WIP сентябрьского спринта по DMS` succeeds.  
   Root boundary: Wave S1 metric skill contracts only exposed `sprint.resolve`, while product-only/current and period phrases need `sprint.current` or `sprint.search`.

2. `Заблокированные задачи спринта DMS-SPRNT-3` could fail or previously return an incorrect empty collection, while `sprint.health` reports blocked tasks.  
   Root boundary: task.search had no explicit `blocked` semantic predicate even though canonical Task/sprint risk logic has `task.is_blocked`.

3. Raw authoritative status names such as `На исправлении` were not matched by generic `task.search` when they normalize to TaskStatus.UNKNOWN.  
   Root boundary: task.search compared only normalized enum/category, not `status_raw/status_type`.

Owner fixes are intentionally generic:
- task.search status filtering now checks authoritative `status_raw` and `status_type` before normalized enum/category;
- status=blocked uses canonical `task.is_blocked`, not a phrase/status-name hardcode;
- tasks.search contract declares blocked and source-label semantics;
- all four Wave S1 metric skills expose generic sprint resolution paths:
  explicit id -> sprint.resolve;
  period/month -> space.resolve + sprint.search;
  product-only/current -> space.resolve + sprint.current.
- focused tests added.

Owner commits:
- `16bbae5606f2ce313ffe7084f1fa07e969fe6d7e`
- `fc8d269edd1f082fd2b30ac4346fdde977d24886`
- `3aa47ceee6a7d0d3fc6781bba6598762943e1268`
- `76c57d13779d65fee2291f4667d56ed7dd17a925`
- `d11dbe0fb5f85a8988a570fe56d46b804906a234`

## Phase 0 — pull / architecture diff
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record START_HEAD; tracked worktree clean.
3. Diff `ce64264c868afd73743d5daafdeaee767e07adef..START_HEAD`.
4. Confirm:
   - no per-person/space/sprint/status-name hardcode;
   - no new Agent Core routing branch by phrase/entity;
   - task.search change is generic predicate/source-field support only;
   - Wave S1 resolution changes are declarative plugin procedure/capability exposure;
   - no local/fake/cache fallback.

Architecture violation => RED.

## Phase 1 — automated tests
Run at minimum:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4_task_search_source_status.py -v
python -m pytest tests/test_agent_core_v4_wave_s1.py -v
python -m pytest tests/test_agent_core_v4_plugin_registry.py -v
python -m pytest tests/test_agent_core_v4*.py -v
python -m pytest tests/test_v4*.py -v
```
Zero unexplained failures.

## Phase 2 — fresh REAL AS21 Oracle
Build fresh source oracle for current DMS sprint:
- sprint id;
- full exact task key set;
- raw/source status name for every task;
- status_type/status_category;
- canonical `is_blocked`;
- sprint.health blocked count from the same fresh source run.

Do not reuse A207 counts; source has already drifted from 65 to 66 tasks.

## Phase 3 — blocked drill-down parity
Run at least 10 fresh sessions across:
- `Заблокированные задачи спринта DMS-SPRNT-3`
- `покажи заблокированные задачи сентябрьского спринта по DMS`
- `какие задачи заблокированы в текущем спринте DMS?`

Require:
- explicit/period/current sprint is resolved correctly;
- terminal collection uses task.search with `status=blocked` or an equivalent governed path preserving the canonical predicate;
- exact key parity against fresh `task.is_blocked` Oracle;
- blocked count exactly equals the blocked count reported by `sprint.health` for the same sprint/source moment;
- no result may say zero if health reports >0;
- no planner-ready completion before the blocked collection executes.

If sprint.health and canonical task.is_blocked disagree, classify RED and identify which implementation is inconsistent. Do not invent a reconciliation.

## Phase 4 — raw source status filtering
Use at least three real source status labels, including `На исправлении` if still present.

Examples:
- `задачи в статусе На исправлении в DMS-SPRNT-3`
- one source status that maps to a known enum;
- one custom/source label that maps to UNKNOWN internally.

Require exact key parity using `status_raw/status_type` source oracle.
No custom source label supplied by AS21 may incorrectly become empty merely because TaskStatus enum is UNKNOWN.

Retain:
- `status=not_completed` exact;
- `status=completed` exact.

## Phase 5 — short-form Wave S1 metric resolution
Fresh sessions, at least 5x each:
- `wip спринта по DMS`
- `velocity спринта по DMS`
- `scope спринта по DMS`
- `throughput спринта по DMS`

Expected product-only semantics:
- resolve the current source-backed DMS sprint with `sprint.current`;
- execute the requested metric;
- identity-only observation must not terminate.

Also run period forms:
- `WIP сентябрьского спринта по DMS`
- `velocity сентябрьского спринта по DMS`

Expected:
- `sprint.search(period=сентябрь)` then metric;
- exact parity with explicit-id query.

Any stochastic failure of product-only/period resolution => RED.

## Phase 6 — health/WIP semantics sanity
Manually verify that these labels are not conflated:
- `sprint.health.active` / “В работе” may be a narrower status class;
- `sprint.wip` is the documented set of all non-terminal started work excluding backlog/open/todo/registered;
- `blocked` is the canonical blocked subset.

Require the UI/answer not to imply that health “В работе” and WIP are the same metric if counts differ.

## Phase 7 — retained A207/A206B regression
At minimum:
- sprint.scope;
- sprint.velocity;
- sprint.throughput;
- sprint.wip explicit id;
- sprint.health;
- task.history;
- task.time_in_status;
- person+status;
- unassigned;
- attachments;
- same-session `этот спринт`;
- DMS-380 lookup;
- release.search fail-closed if /versions remains 502.

## Phase 8 — Browser C manual reproduction
Use real UI and reproduce the owner's screenshots:
- short WIP DMS;
- velocity DMS;
- health September DMS;
- blocked tasks explicit sprint;
- blocked tasks period/current form;
- raw status label query.

Require no V4 ERROR for supported healthy-source cases.
Release list may remain SOURCE_UNAVAILABLE if /versions is still independently 502.

## Phase 9 — architecture/source audit
Require:
- local factual `/api/v1/tasks` reads = 0;
- no tenant-wide scan;
- dummy-55/plugin invariant GREEN;
- no hardcoded people/spaces/sprint ids/status names;
- source outages fail closed.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_PRE_S2_MANUAL_CONSISTENCY_GREEN`
- `AGENT_CORE_V4_PRE_S2_MANUAL_CONSISTENCY_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires all supported healthy-source manual scenarios to be deterministic and exact.

If GREEN recommend exactly:
`PROCEED_TO_WAVE_S2_OWNER_IMPLEMENTATION`

If RED:
STOP. Do not fix code. Do not start S2. Return first exact root cause.

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_PRE_S2_MANUAL_CONSISTENCY_208.md`

Leave UI/backend/Task API/MCP running.
Return verdict, START_HEAD, report commit, blocked-health parity, raw-status parity, short-form metric matrix, service health.
Then stop.
