# AGENT_CORE_V4 Batch 6 release.forecast Gate — A220

**Verdict: `AGENT_CORE_V4_BATCH6_FORECAST_GREEN_A220`**

| Field | Value |
|---|---|
| Date | 2026-09-26 |
| START_HEAD | `6d7c08c` (full: `6d7c08cca6c95e1bd3f9adb6f8db1ae77efe5de2`) |
| Baseline (A219R GREEN) | `1bafa10` |
| Owner Batch 6 commits | `4784b20` (feat plugin), `e718d27` (tests) |
| Branch | `feat/core8-real-query-hardening-v2` |

**Reported inventory (required):**
- exact live skill/plugin count: **68 skills / 13 plugins / 0 duplicates**
- canonical coverage: **54/54**
- exact canonical missing list: **`[]`**
- release.forecast source maturity classification: **`release_linkage_unpopulated`** — release-to-task membership is empty for all live releases (WMB/OLP/DMS), therefore live NL requests terminate in the certified typed `SOURCE_CONDITIONAL` (`v4_capability_unavailable`) with zero fabrication.

## Phase 0 — architecture invariant: PASS

- `git tag -l checkpoint/*` → the referenced `checkpoint/v4-batch5-green-a219r` tag does not
  exist; effective baseline = A219R report commit `1bafa10`.
- `git diff --stat 1bafa10..HEAD` = exactly 4 files:
  1. `po-agent-platform-v2/src/po_agent/harness/v4_plugins/wave_batch6_release_forecast.py` (new plugin)
  2. `po-agent-platform-v2/tests/test_agent_core_v4_batch6_release_forecast.py` (new focused tests)
  3. `V4_DOD_LOCK.md` (docs)
  4. `GIGACODE_NEXT_ACTION.md` (assignment doc)
- **Zero** Agent Core / planner / runtime / session-context / adapter / task-api edits.
- Registry discovers exactly one new plugin `builtin.batch6.release_forecast`;
  `release.forecast` appears exactly once; no dummy plugin in production discovery.
- dummy-55 invariant test GREEN (registry extensibility test passes in the full V4 run).

## Phase 1 — tests: PASS

- Focused (`batch6_release_forecast` + `batch4` + `planner_signature_parity`): **15 passed**
- Full `test_agent_core_v4*.py` + `test_v4*.py`: **211 passed** (= 205 A219R baseline + 6 new)
- 0 unexplained failures.

## Phase 2 — current REAL AS21 source oracle: state confirmed

Independent bounded probes (version directory + `task-query?space=&release=`):

| Release | Canonical id | Directory count | Membership rows |
|---|---|---|---|
| WMB 24Q1 | `7a84006f-7823-4052-ae46-b94f5165518e` | 3 | **0** |
| OLP 1.6.0 | `20ba588e-9b7e-43b2-b78a-465bdec0669a` | 1 | **0** |

Source has **not** evolved since A214/A217: membership remains unpopulated. Therefore the
expected live behavior = typed SOURCE_CONDITIONAL before any forecast math (proven in P3/P7).
Completed-timestamp inspection is moot (no membership rows to inspect).

## Phase 3 — live NL routing: PASS 15/15

5 runs × 3 forms ("прогноз завершения релиза 24Q1 в WMB", "когда ориентировочно закончится
релиз OLP 1.6.0", "release forecast for WMB 24Q1"), fresh sessions, agent freshly restarted
on `6d7c08c` (PID 79889):

Every run (15/15, fully deterministic, 8.5–17.1s):
- identity resolved first: `space.resolve` → `release.search(require_single='True')` →
  `release.forecast` with the **canonical UUID** (WMB: `7a84006f…`, OLP: `20ba588e…`)
- `release.forecast` actually loads AND executes
- typed terminal: `warnings=['v4_capability_unavailable']`, honest answer
  "Необходимая возможность не подтверждена источником данных и не выполняется."
- **0** identity-only early terminals; **0** release.progress/health substitution;
  **0** fabricated date/percentage; **0** `v4_runtime_failure`; **0** generic failure text

This is the user-emphasized guarantee: **live WMB/OLP fail closed on insufficient
release membership/history — no invented forecast.**

## Phases 4–6 — controlled fixture verification: PASS 5/5 (independent re-implementation)

Own probe (`qa_220_p456_probe.py`) invoking the capability directly with a source-shaped
adapter, independent of the owner test file:

- **P4** (projection): 4 tasks, 2 completed with `closed_at` 2026-09-06 / `resolved_at`
  2026-09-11, 2 remaining, all created 2026-09-01 →
  `state=FORECAST`, `observation_days=10.0`, `throughput=0.2`,
  `forecast_days_remaining=10.0`, `method=linear_task_throughput_v1`,
  `completion_timestamp_policy=closed_at_or_resolved_at_only`,
  warning `forecast_is_operational_projection_not_commitment` present. **All exact.**
- **P5** (updated_at anti-fabrication): completed tasks with `updated_at` but no
  `closed_at`/`resolved_at` → typed `V4CapabilityUnavailable`
  ("requires at least two completed release tasks with authoritative resolved/closed
  timestamps"); **zero forecast leaked**.
- **P6** (completed release): all tasks completed with authoritative ts →
  `state=COMPLETED`, `forecast_kind=actual_completion`,
  `method=authoritative_latest_completion_timestamp`, `forecast_date` = latest
  authoritative timestamp (2026-09-11), `remaining_tasks=0`, no projected future date.
- **P6b** (completed but no authoritative ts): typed `V4CapabilityUnavailable`
  ("cannot prove an actual completion date") — no date minted.
- **P2c** (empty membership): typed `V4CapabilityUnavailable` naming
  release-to-task membership — empty membership is never treated as a zero-task release.

## Phase 7 — Browser C: PASS 2/2

Real UI (vite 5175 → agent 8212), Playwright capture + screenshots
(`qa_220_browser_c/`):

- C1 "прогноз завершения релиза 24Q1 в WMB": typed SC presentation
  (`v4_capability_unavailable`), UI message = honest source-unavailable text,
  **no** generic "не смог безопасно завершить", **no** fake date/percentage,
  **no** internal leak, **no** stale-source error text.
- C2 "когда ориентировочно закончится релиз OLP 1.6.0": identical typed presentation.
- No dedicated `release_forecast` widget exists in the UI; the typed state is clear via
  the standard V4 panel (permitted by spec: typed state + no-fabrication semantics clear).

## Phase 8 — retained regression: PASS 13/13

| Case | Result |
|---|---|
| po.attention_queue (DMS) | PASS — count=108 (A219 parity) |
| po.daily_brief (DMS) | PASS — active=127, COMPLETED (A219: 126, +1 live drift) |
| po.status_report (DMS) | PASS — total=148, active=127 (A219: 147/126, +1 live drift) |
| po.reminder_draft (DMS-379) | PASS — draft_created=true, write_performed=false |
| po.local_task_draft (DMS-434) | PASS — REAL_AS21, approval-gated, wp=false |
| agent.help | PASS — skill_count=**68** (updated live registry) |
| task DMS-380 (task.lookup) | PASS — COMPLETED |
| current sprint DMS | PASS — `sprint.current` → DMS-SPRNT-3 |
| Semavin time accounting | PASS — `member.time_spent`: **64.0h / 8 worklogs**, by_task DMS-411 24 / DMS-408 16 / DMS-267 8 / DMS-390 8 / DMS-403 8 (A215G exact parity; data at `results[3]`) |
| portfolio.overview | PASS — COMPLETED |
| standalone release identity ("релиз 24Q1 в WMB") | PASS — identity-only `release.search` COMPLETED, no analytic over-extension |
| release.progress ("прогресс релиза 24Q1 в WMB") | PASS — executed + typed `v4_capability_unavailable` |
| release.health ("здоровье релиза 24Q1 в WMB") | PASS — executed + typed `v4_capability_unavailable` |

Known non-blocking nuance (A217B F2, pre-existing): the phrasing "готовность релиза"
routes to `release.health` instead of `release.progress`; both terminate in the same typed
SOURCE_CONDITIONAL. Explicit "прогресс" phrasing routes correctly (re-probed live).

## Phase 9 — source/write audit: PASS

A220 task-api log window (lines 9886–10159, 274 lines):

- local factual reads (`GET /api/v1/tasks`): **0**
- mutations (POST/PUT/PATCH/DELETE): **0**
- task-query calls: 23, **all** `space=`-scoped, **all** release-membership
  (`space=`+`release=`) — exactly the bounded membership route
- unscoped task-query: **0**; `assignee-tasks` (tenant-scan) calls: **0**
- `/versions` calls: 24, all space-scoped
- no forecast path performs any task search outside the release membership query

## Phase 10 — inventory / canonical closure: PASS

Fresh registry enumeration:
- live registry = **68 skills / 13 plugins / 0 duplicates**; `release.forecast` ×1;
  no dummy in production discovery
- canonical coverage = **54/54**; missing canonical list = **`[]`**
- 54/54 means every canonical requirement has an implemented, tested terminal source
  contract; release.forecast counts as correctly covered because its fail-closed
  SOURCE_CONDITIONAL contract is certified (Phases 2/3/7) while live linkage is unpopulated.

## Non-blocking findings

1. **"готовность" → release.health routing** (A217B F2, pre-existing): spec-literal
   routing nuance; both terminal states are the same typed SC. No action required.
2. **`release_forecast` widget absent in UI** — typed state is still unambiguously
   presented via the standard V4 panel; a dedicated widget is a future UX nicety.
3. **Checkpoint tag `checkpoint/v4-batch5-green-a219r` does not exist** — effective
   baseline for this gate was the A219R report commit `1bafa10` (docs noted the tag).

## Services

| Service | Address | PID |
|---|---|---|
| agent | 127.0.0.1:8212 @ `6d7c08c` | 79889 (fresh) |
| task-api | 127.0.0.1:8241 | 81954 (system py3) |
| MCP-SWTR | 127.0.0.1:3000 | 29268 |
| UI | [::1]:5175 | 47416 |

## Artifacts

- `qa_220_p3_results.json` / `qa_220_p3_run.log` — 15-run NL routing
- `qa_220_p456_results.json` — independent fixture verification (5/5)
- `qa_220_p7_browser.json` / `qa_220_browser_c/*.png` — Browser C
- `qa_220_p8_results.json` / `qa_220_p8_run.log` — retained regression
- runners: `qa_220_p3_runner.py`, `qa_220_p456_probe.py`, `qa_220_p8_runner.py`,
  `qa_220_start_agent.sh`, `frontend/e2e/qa220-browser-c.spec.ts`

## Recommendation

**Freeze the immutable canonical-54 checkpoint** (effective base = this GREEN gate on
`6d7c08c`; publish the missing `checkpoint/*` tags so future gates have real anchors).
**Next step = full V4 54/54 A/B/C certification matrix** (per spec).
