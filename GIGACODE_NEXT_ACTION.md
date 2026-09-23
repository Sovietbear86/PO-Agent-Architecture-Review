# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_209_WAVE_S2_FIVE_SKILL_BATCH`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT add skills.
Do NOT start the next batch.

## Stable rollback
A208B is GREEN and frozen at:
`checkpoint/v4-a208b-green@2e284fdab79072d95ba0bf86058b4648f4bb9d6c`

## Owner S2 batch
Five plugin-only skills:
1. `sprint.cycle_time`
2. `sprint.lead_time`
3. `sprint.carryover`
4. `sprint.predictability`
5. `sprint.risk_queue`

Owner commits:
- `186c1c6662a493371328d9a188488c12f0e66e66` — five-skill S2 plugin;
- `54bfe2932702b17b536ce9a2e71e6dbe7fd62924` — focused tests.

Batch policy is now 5 skills by default; architecture standards are unchanged.

## Important semantics

### sprint.cycle_time
Population: completed tasks only.
Formula:
`terminal workflow transition timestamp - first workflow status transition timestamp`.
Do not substitute current time for completed tasks.
If any completed task lacks history, fail closed rather than bias the aggregate.

### sprint.lead_time
Population: completed tasks only.
Formula:
`terminal workflow transition timestamp - authoritative task.created_at`.
Same completeness rule: no partial aggregate if completed-task history is missing.

### sprint.carryover
Formula:
intersection of complete previous-sprint membership and complete current-sprint membership.
If previous_sprint_id is omitted, resolve immediate predecessor from authoritative sprint dates.
No snapshot/local cache inference.

### sprint.predictability
Formula:
`completed / authoritative committed baseline`.
Current sprint scope is **not** an acceptable substitute for a missing baseline.
If REAL AS21 sprint metadata does not expose a committed/baseline scope, skill must be SOURCE_CONDITIONAL/fail-closed.

### sprint.risk_queue
Task ranking only:
1. blocked tasks first;
2. then overdue_days descending;
3. then age_days descending;
4. stable task-key tie-break.

Every row must expose reasons/evidence.
No employee/person performance scoring.

## Phase 0 — pull / diff / plugin architecture
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record START_HEAD; tracked worktree clean.
3. Diff from A208B checkpoint.
4. Prove:
   - all 5 skills live only in registry-discovered plugin code;
   - no Agent Core/planner/runtime skill-specific branch;
   - no hardcoded DMS/person/task ids/status names;
   - no local/fake/cache source truth;
   - completion/UI contracts exist for all 5.

Any architecture drift => RED.

## Phase 1 — automated tests
Run:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4_wave_s2.py -v
python -m pytest tests/test_agent_core_v4_wave_s1.py -v
python -m pytest tests/test_agent_core_v4*.py -v
python -m pytest tests/test_v4*.py -v
```

Zero unexplained failures.

## Phase 2 — fresh REAL AS21 oracle
Build fresh Oracle for:
- DMS current/September sprint;
- one prior DMS sprint;
- complete task memberships for both;
- all completed current-sprint tasks;
- raw task.created_at;
- raw `get_task_history` for every completed task used by cycle/lead;
- due dates, blocked state and age for current open tasks;
- sprint metadata fields relevant to committed baseline.

Do not reuse A208B counts.

## Phase 3 — sprint.cycle_time
Run explicit-id, period and current/product-only forms, minimum 3 each.

Independently calculate from raw MCP history:
- first workflow-status transition;
- terminal workflow transition;
- per-task cycle hours;
- average/median/min/max.

Require:
- exact completed task population;
- exact per-task timestamps;
- exact aggregate within rounding tolerance;
- no use of current time for completed tasks;
- no partial aggregate when a completed history is missing.

Any fabricated/missing-history average => RED.

## Phase 4 — sprint.lead_time
Same matrix as P3.

Oracle:
`terminal transition - raw authoritative created_at`.

Require exact population, per-task duration and aggregate.
No use of updated_at/current time as substitute.

## Phase 5 — sprint.carryover
Fresh previous/current sprint memberships.

Run:
- explicit current sprint, auto-previous;
- explicit previous_sprint_id if UI/API allows;
- period/current short forms.

Require exact set intersection by task key.
No task title/fuzzy matching.
No current-only approximation.

## Phase 6 — sprint.predictability
Inspect live sprint metadata first.

If committed/baseline scope exists:
- independently compute completed/baseline;
- run 5x and require exact result.

If baseline does NOT exist:
- expected result = typed SOURCE_UNAVAILABLE/SOURCE_CONDITIONAL;
- prove no current-scope substitution;
- zero fabricated predictability percentage.

Source absence here is acceptable SOURCE_CONDITIONAL, not overall RED, if the other source-backed skills are exact.

## Phase 7 — sprint.risk_queue
Fresh Oracle on current DMS sprint.

Require:
- queue contains only open tasks with at least one reason: blocked, overdue, aging>=14d;
- blocked first;
- overdue descending;
- age descending;
- stable task key tie-break;
- exact reasons/evidence per task;
- no ranking/scoring of people.

Cross-check blocked subset against sprint.health and task.search(status=blocked).

## Phase 8 — short-form/period/current resolution
At least 3x each representative:
- `cycle time спринта DMS`
- `lead time сентябрьского спринта DMS`
- `carryover текущего спринта DMS`
- `predictability спринта DMS`
- `риски текущего спринта DMS`

Identity-only resolution may not terminate the metric request.

## Phase 9 — Browser C
Real UI representative for all 5 skills.
Expected presentation:
- cycle/lead: sprint_metric;
- carryover/risk queue: task-table style;
- predictability: metric or typed source-unavailable.

No V4 ERROR for healthy-source cases.

## Phase 10 — retained regression
At minimum:
- Wave S1 four sprint metrics;
- blocked tasks;
- raw status `На исправлении`;
- sprint.health;
- task.history;
- task.time_in_status;
- DMS-380 lookup;
- person+status;
- attachments;
- same-session context;
- dummy-55.

## Phase 11 — source/local/perf audit
Require:
- local factual `/api/v1/tasks` reads = 0;
- no tenant-wide task scan;
- histories bounded/concurrency-bounded;
- no fake/frozen cache;
- source outages fail closed;
- plugin invariant GREEN.

Note: `release.search` is still independently SOURCE_CONDITIONAL because /versions/search_versions returns 502. This known outage must not be counted as an S2 code RED, but should be re-probed once.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_WAVE_S2_FIVE_SKILL_GREEN`
- `AGENT_CORE_V4_WAVE_S2_FIVE_SKILL_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

Overall GREEN may include `sprint.predictability = SOURCE_CONDITIONAL` if committed-baseline source absence is independently proven and all other skills pass.

If GREEN recommend exactly:
`FREEZE_WAVE_S2_CHECKPOINT_AND_PROCEED_TO_NEXT_FIVE_SKILL_OWNER_BATCH`

If RED:
STOP. Do not modify production code. Do not start next batch.

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_WAVE_S2_FIVE_SKILL_209.md`

Leave UI/backend/Task API/MCP running.
Return verdict, START_HEAD, report commit, 5-skill matrix, Oracle parity, source-conditional classification, URLs/PIDs/health.
Then stop.
