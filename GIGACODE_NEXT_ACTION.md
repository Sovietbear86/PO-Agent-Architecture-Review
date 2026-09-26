# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_220_BATCH6_RELEASE_FORECAST_GATE

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT start full 54-skill certification.
Commit/push only the QA report.

## Frozen baseline
A219R = GREEN.
Rollback checkpoint:
`checkpoint/v4-batch5-green-a219r`

Baseline inventory:
- live registry before Batch 6 = 67 skills / 12 plugins;
- canonical coverage = 53/54;
- only missing canonical skill = release.forecast.

## Owner Batch 6
Commits:
- `4784b20c9ad7fa7c35dc9bc5e128d34f83baaa48`
- `e718d27b69820b36240887f5a7e273ec9d577f59`

New plugin-only skill:
- release.forecast

No Agent Core/planner/runtime/session-context changes.

## Forecast source contract
release.forecast is deliberately conservative.

Required chain:
space.resolve -> release.search(require_single=true) -> release.forecast

Forecast may execute only if:
1. authoritative release-to-task membership exists and is non-empty;
2. for an unfinished release, >=2 completed tasks have authoritative closed_at/resolved_at timestamps;
3. task creation timestamps form a positive observation window.

Never:
- treat empty release membership as a zero-task release;
- infer a completion timestamp from updated_at;
- invent a forecast from status percentages alone;
- use LLM prose as forecast math;
- present the result as a commitment.

Controlled deterministic method:
- observation_start = earliest authoritative task created_at in release scope;
- observation_end = latest authoritative closed_at/resolved_at among completed tasks;
- throughput = completed tasks with authoritative completion timestamps / observation_days;
- remaining_days = remaining task count / throughput;
- forecast_date = current time + remaining_days;
- method = linear_task_throughput_v1.

If release is already complete:
- forecast_kind=actual_completion;
- forecast_date = latest authoritative completion timestamp;
- no projection.

## Phase 0 — architecture invariant
1. Pull branch; record START_HEAD and clean worktree.
2. Diff from checkpoint/v4-batch5-green-a219r.
3. Prove only Batch 6 plugin/tests/docs changed.
4. Zero Agent Core/planner/runtime/session-context edits.
5. Registry discovers exactly one new plugin and release.forecast exactly once.
6. dummy-55 invariant GREEN.

## Phase 1 — tests
Run:
- tests/test_agent_core_v4_batch6_release_forecast.py
- tests/test_agent_core_v4_batch4.py
- tests/test_agent_core_v4_planner_signature_parity.py
- full tests/test_agent_core_v4*.py
- tests/test_v4*.py

Zero unexplained failures.

## Phase 2 — current REAL AS21 source oracle
Use at least:
- WMB release 24Q1
- OLP release 1.6.0

Independently:
1. resolve release via version directory;
2. query bounded release membership with canonical release UUID/code;
3. if membership exists, inspect source-backed completion timestamps.

Expected current source state based on A214/A217:
- release membership is empty/unpopulated;
- therefore release.forecast must terminate typed SOURCE_CONDITIONAL before forecast math.

If source has evolved and membership is now populated, continue exact source inspection rather than assuming the historical state.

## Phase 3 — live NL routing
Run >=5 each:
- "прогноз завершения релиза 24Q1 в WMB"
- "когда ориентировочно закончится релиз OLP 1.6.0"
- "release forecast for WMB 24Q1"

Require:
- release identity resolved first;
- release.forecast actually loads/executes;
- current insufficient source => typed SOURCE_CONDITIONAL;
- zero identity-only early terminal;
- zero release.progress/health substitution unless user asked for them;
- zero fabricated date/percentage.

## Phase 4 — controlled membership/history fixture
Use the focused controlled fixture or equivalent source-shaped adapter.

Require exact:
- authoritative membership;
- two completed tasks with closed/resolved timestamps;
- two remaining tasks;
- 10-day observation window;
- throughput 0.2 tasks/day;
- remaining_days 10.0;
- method linear_task_throughput_v1;
- completion_timestamp_policy closed_at_or_resolved_at_only;
- warning says operational projection/not commitment.

## Phase 5 — updated_at anti-fabrication
Controlled case:
- tasks marked completed;
- updated_at present;
- closed_at/resolved_at absent.

Require typed capability unavailable.
Any forecast derived from updated_at => RED.

## Phase 6 — completed-release case
Controlled source-backed completed release.

Require:
- state=COMPLETED;
- forecast_kind=actual_completion;
- method=authoritative_latest_completion_timestamp;
- date = latest authoritative closed/resolved timestamp;
- no projected future date.

## Phase 7 — Browser C
Real UI:
- forecast WMB 24Q1;
- forecast OLP 1.6.0.

Current sparse-source expected:
- typed SOURCE_UNAVAILABLE/SOURCE_CONDITIONAL presentation;
- no generic V4 ERROR;
- no fake date;
- release identity may be visible as grounded context.

If a dedicated release_forecast widget is absent, JSON fallback is acceptable only if the typed state and no-fabrication semantics are clear.

## Phase 8 — retained regression
At minimum:
- Batch 5 PO five skills
- agent.help
- task DMS-380
- current sprint DMS
- Semavin time accounting
- portfolio.overview
- standalone release identity
- release.progress/health SOURCE_CONDITIONAL
- dummy-55

Zero planner/runtime signature regressions.

## Phase 9 — audit
Require:
- local factual reads = 0;
- tenant-wide scans = 0;
- mutations = 0;
- release lookup/membership only bounded source routes;
- no forecast path performs task search outside the release membership query.

## Phase 10 — inventory / canonical closure
Fresh registry enumeration.

Expected if no unrelated drift:
- live registry = 68 skills / 13 plugins;
- duplicates = 0;
- canonical coverage = 54/54;
- canonical missing list = [].

Important:
54/54 means every canonical requirement has an implemented, tested terminal source contract.
It does NOT mean every live request has rich data.
release.forecast may be SOURCE_CONDITIONAL on current AS21 and still count as correctly covered if its fail-closed contract is certified.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_BATCH6_FORECAST_GREEN_A220`
- `AGENT_CORE_V4_BATCH6_FORECAST_RED_A220`

Also report:
- exact live skill/plugin count;
- canonical coverage x/54;
- exact canonical missing list;
- current source maturity classification for release.forecast.

If GREEN:
recommend immutable canonical-54 checkpoint and next step = full V4 54/54 A/B/C certification matrix.

If RED:
identify first failing boundary and STOP.

Do not modify code.
