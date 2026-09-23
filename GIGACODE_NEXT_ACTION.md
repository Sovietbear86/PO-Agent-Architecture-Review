# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_207_V4_WAVE_S1_SPRINT_FLOW_RELEASE_SEARCH`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT add skills.
Do NOT start Wave S2.
Any RED blocks progression.

## Stable rollback
A206B is GREEN and frozen at:
`checkpoint/v4-a206b-green@f7f846dee71b676fb0fc8d1d8f0d8aa23d521eaf`

## Owner Wave S1 delta
New plugin-only skills/capabilities:
- `sprint.scope`
- `sprint.velocity`
- `sprint.throughput`
- `sprint.wip`
- `release.search`

Owner commits:
- `2f110dc6c2cb22513dcc4bd4e660b54f8b53d058` — new registry-discovered Wave S1 plugin;
- `6a2373683bbf8a541ba7ff666168eb87d86a84e1` — bounded live release/version directory adapter surface (no task-scan fallback);
- `91f7e18adafbb3c549f436922bdc75ecac04857e` — release.health plugin contract can use release.search;
- `2a7e9caf8cf0c77c052934ac9d0c8dd2e4eef42a` — focused Wave S1 tests.

No Agent Core/planner/runtime business-skill code was added.

## Metric contracts to verify
### sprint.scope
Source = complete live sprint task set.
Required facts:
- total;
- completed;
- open;
- undecodable_status;
- unassigned;
- exact task_keys.

### sprint.velocity
Explicit unit = `tasks/sprint`.
Formula = completed tasks in the current complete sprint snapshot.
Must explicitly state that story points are **not** source-backed.
Never label task-count velocity as story-point velocity.

### sprint.throughput
Explicit unit = `completed_tasks/calendar_day`.
Formula = completed tasks in current snapshot / max(1, elapsed calendar days from authoritative sprint start).
Must expose start/measurement_end and warn that this is a current snapshot rate, not historical completion-event throughput.

### sprint.wip
Formula = current non-terminal sprint tasks excluding source backlog/open/todo/registered states.
Must return exact task_keys and source statuses.

### release.search
Must use bounded live version/release directory only.
No tenant-wide task scan.
No local task store.
DMS/OLP/etc are product spaces, never release ids.
Ambiguity for a single-release need must become typed clarification.
If authoritative release directory is unavailable, fail closed / SOURCE_CONDITIONAL.

## Phase 0 — pull / architecture diff
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record START_HEAD; tracked worktree clean.
3. Diff from A206B checkpoint `f7f846dee71b676fb0fc8d1d8f0d8aa23d521eaf..START_HEAD`.
4. Prove:
   - new skills are entirely plugin registry additions;
   - no skill-specific Agent Core/planner/runtime branch;
   - no per-space/release/sprint hardcode;
   - release.search does not use `_task_backed_versions` or any broad task scan;
   - existing core release.health change is declarative plugin contract only.

Any architecture violation => RED.

## Phase 1 — automated tests
Run at minimum:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4_wave_s1.py -v
python -m pytest tests/test_agent_core_v4_plugin_registry.py -v
python -m pytest tests/test_agent_core_v4*.py -v
python -m pytest tests/test_v4*.py -v
```

Also run affected adapter/source tests.

Require zero unexplained failures.

## Phase 2 — fresh REAL AS21 Oracle
Immediately before live tests build fresh source oracles for:
- DMS current/September sprint;
- OLP current sprint;
- complete task keys/statuses for selected sprint(s);
- source sprint start/finish timestamps;
- release/version directory availability + returned rows if healthy.

Do not reuse A205/A206 counts.

## Phase 3 — sprint.scope
Run at least 5x on DMS and 3x on OLP.

Example natural-language requests:
- `объем сентябрьского спринта по DMS`
- `scope текущего спринта OLP`

Require:
- actual `sprint.scope` capability;
- exact total/task key parity;
- completed/open/unassigned exact vs fresh Oracle;
- identity-only sprint resolution cannot terminate the request;
- no local reads.

## Phase 4 — sprint.velocity
Run at least 5x:
- `скорость сентябрьского спринта по DMS`
- `velocity текущего спринта OLP`

Require:
- actual `sprint.velocity`;
- value = exact count of currently completed source-backed sprint tasks;
- unit exactly `tasks/sprint`;
- answer warns/no claim of story points;
- exact completed key parity available in evidence/data.

Any invented points => RED.

## Phase 5 — sprint.throughput
Run at least 5x on a source-backed active sprint.

Require:
- actual `sprint.throughput`;
- authoritative sprint start timestamp;
- elapsed-days formula exact;
- completed count exact;
- rounded throughput matches independent Oracle;
- unit `completed_tasks/calendar_day`;
- current-snapshot limitation visible.

If sprint dates are unavailable/malformed, fail closed; do not substitute task timestamps.

## Phase 6 — sprint.wip
Run at least 5x:
- `WIP сентябрьского спринта DMS`
- `сколько задач сейчас в работе в текущем спринте OLP`

Require:
- exact WIP key parity;
- completed/terminal tasks excluded;
- backlog/open/todo/registered source states excluded by documented formula;
- no custom source status is silently discarded if it is source-classified as active work;
- task statuses/evidence source-backed.

## Phase 7 — release.search
Test all states.

### 7A direct list/search
- `найди релизы DMS`
- `найди релиз <source-backed text/name> в DMS`

If source directory is healthy:
- actual `release.search`;
- exact source ids/names;
- product-space scoping exact;
- bounded route provenance;
- zero task-scan fallback.

### 7B ambiguity
When several source releases match and one is required:
- typed clarification options;
- no guessing.

### 7C no-match
- typed no-match/clarification;
- no fabricated id.

### 7D source unavailable
If live `search_versions` is still 502:
- typed SOURCE_UNAVAILABLE/SOURCE_CONDITIONAL;
- zero broad task scan;
- zero local reads.
This is acceptable SOURCE_CONDITIONAL, not RED, if provenance proves source outage.

## Phase 8 — release.health hand-off
If release.search source is healthy:
1. query `здоровье релиза по DMS`;
2. prove release.search is used when no concrete release id is supplied;
3. if multiple -> typed release options;
4. after user picks one, release.resolve/release.health executes with the selected source-backed id.

If search_versions is unavailable, health may remain SOURCE_CONDITIONAL but must fail closed without binding DMS as release id.

## Phase 9 — Browser C
Use real UI for representative:
- scope;
- velocity;
- throughput;
- WIP;
- release search (or source-unavailable state);
- release health hand-off if source-supported.

No raw internal contract leakage beyond existing debug/evidence UI behavior.

## Phase 10 — retained regression
At minimum re-run:
- DMS-380 lookup;
- person search;
- sprint health;
- same-session `этот спринт`;
- multi-hop clarification;
- unassigned;
- task.history;
- task.time_in_status;
- attachments;
- ordinary status search.

Require no regression from A206B/A205.

## Phase 11 — plugin invariant
Re-run dummy-55.
Must remain GREEN with zero Agent Core/planner/runtime edits.

## Phase 12 — source/local/performance audit
Across run:
- local `GET /api/v1/tasks` factual reads = 0;
- no fake/frozen/local Oracle;
- no tenant-wide task scan for release.search;
- sprint task sets use complete source-backed route;
- no N+1 sprint membership regression;
- source outages fail closed.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_WAVE_S1_GREEN`
- `AGENT_CORE_V4_WAVE_S1_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

Overall GREEN may include `release.search = SOURCE_CONDITIONAL` only if the release directory is independently proven unavailable and all four sprint skills are GREEN.

If any logic/architecture RED:
STOP. Do not fix production code. Do not start S2.

If GREEN:
recommend exactly:
`FREEZE_WAVE_S1_CHECKPOINT_AND_PROCEED_TO_S2_OWNER_IMPLEMENTATION`

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_WAVE_S1_207.md`

Leave UI/backend/Task API/MCP running.
Return verdict, START_HEAD, report commit, skill matrix, Oracle parity, release-source classification, URLs/PIDs/health.
Then stop.
