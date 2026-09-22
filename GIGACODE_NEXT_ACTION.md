# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_205_FULL_RERUN_AFTER_GREEN_PREFLIGHT`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT add new skills.
Do NOT start Wave S.
Any RED blocks progression.

## Context
The dedicated runtime-interface preflight is GREEN:
- verdict: `AGENT_CORE_V4_A205_PREFLIGHT_GREEN`;
- START_HEAD: `a4b8a25c613b117a8bdd20e648079e6b11a6d02`;
- report commit: `61abf6f`;
- focused interface tests: 30/30 GREEN;
- full V4/V4-related test glob: 131/131 GREEN;
- production-chain smoke: 7/7 reached real capability execution;
- zero TypeError/signature mismatch;
- same-session `этом спринте` context works;
- clarification continuation works;
- dummy-55 GREEN;
- local factual reads = 0.

Therefore the two A205 framework-boundary defects are closed:
1. robust planner session_context signature/payload;
2. pluginized literal-guard session_context signature/forwarding.

Now run the **full A205 from scratch**. Do not reuse previous A205 verdicts or counts.

Permanent rollback:
`checkpoint/v4-pre-wave-s-a202@e580489950e5a149a6a740cb8779dfdb0351d471`.

## Mission
Execute the complete existing-catalog + adversarial zero-RED gate against current HEAD.

This is the decisive gate before any new skill wave.

## Phase 0 — start
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record exact START_HEAD; tracked production worktree clean.
3. Verify preflight report exists and is GREEN.
4. Confirm no production changes occurred after the preflight START_HEAD except this spec/report bookkeeping.

## Phase 1 — automated gates
Run:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4*.py -v
python -m pytest tests/test_v4*.py -v
cd ../task-api
python -m pytest tests/test_swtr_read_sprint_collection.py -v
python -m pytest tests/test_swtr_task_query_release.py -v
```

Also run relevant history/source/readiness tests.

Require zero unexplained failures.

## Phase 2 — fresh Oracle
Build fresh REAL AS21 oracles immediately before factual batches for:
- DMS September sprint + exact tasks/statuses;
- OLP current sprint + exact unassigned set;
- DMS/OLP September sprint candidates;
- DMS-380 history availability;
- DMS-399 time-in-status availability;
- one concrete REAL release id and exact release task set if source allows it.

No stale A204/A205 counts.

## Phase 3 — all 27 current V4 skills
Run **27/27**, no skips.

For every row capture:
- natural-language query;
- expected/actual skill;
- loaded skills;
- capabilities;
- final arguments;
- completion mode;
- source route;
- exact Oracle parity where factual;
- UIContract;
- GREEN / SOURCE_CONDITIONAL / RED.

Overall must be **0 RED**.

## Phase 4 — adversarial pack
Run all manual/problem cases:

### Sprint health
- `здоровье сентябрьского спринта по DMS` ×10.
Require actual `sprint.health`, not identity-only completion.

### Period sprint task list
- `Покажи список задач сентябрьского спринта DMS и их статусы` ×10.
Require exact task/status collection.

### Same-session context
Pair ×10:
1. establish September sprint in DMS;
2. `Покажи список задач в этом спринте и их статусы`.
Require exact reuse of source-validated sprint context.

### Multi-hop clarification
`покажи активные задачи у Гаранина в сентябрьском спринте по OLAP`
through:
space clarification -> sprint clarification -> terminal task collection.
Require person + OLP + selected sprint + active/not_completed preserved.

### Unassigned
- `найди задачи без исполнителя в текущем спринте OLP`
- same for DMS.
Require `unassigned=true` and exact null-assignee key parity.

### Unsupported workload analytics
- `кто больше всех загружен в сентябрьском спринте по DMS?`
Require no identity-only false success and no invented ranking. If not implemented, say so honestly.

### History / time in status
- `покажи историю статусов задачи DMS-380`
- `сколько времени DMS-399 провела в каждом статусе?`
- `Ты умеешь определять длительность задач?`
Require exact result when source-supported; otherwise typed SOURCE_UNAVAILABLE/SOURCE_CONDITIONAL and honest capability availability.

### Release health/tasks
- `здоровье релиза по DMS`
- `задачи в релизе по DMS`
Require DMS treated as space, never release id. Missing release identity -> typed clarification.
If a REAL release id is available, test explicit health/tasks with bounded source-side release filter and exact parity.

## Phase 5 — performance/provenance
For explicit sprint task list, confirm source-proven complete rows avoid per-task N+1 raw membership validation.
Record latency and raw-unit call count.

For attachments, record latency separately; do not classify pure external LLM slowness as a logic defect unless it causes unsafe behavior.

## Phase 6 — Browser C
Use actual UI for at least:
- sprint health;
- same-session `этом спринте`;
- multi-hop OLP clarification;
- unassigned;
- unsupported workload;
- history/time-in-status;
- release health;
- concrete release path if source-supported.

No internal session_context leakage.

## Phase 7 — source/local audit
Across whole run:
- local `GET /api/v1/tasks` factual reads = 0;
- no fake/frozen/local Oracle;
- no broad client-side release scan;
- no false success on source outage;
- retain and classify timeout/429/model flakes, never silently discard.

## Phase 8 — plugin invariant
Re-run dummy-55.
Must remain GREEN with zero Agent Core/planner/runtime business edits.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_EXISTING_CATALOG_ADVERSARIAL_GREEN`
- `AGENT_CORE_V4_EXISTING_CATALOG_ADVERSARIAL_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires:
- 27/27 tested;
- 0 RED;
- adversarial pack closed or correctly SOURCE_CONDITIONAL;
- no resolver-only false success;
- no dropped constraints;
- same-session context safe;
- multi-hop clarification safe;
- release grounding correct;
- local factual reads = 0;
- dummy-55 GREEN.

If any RED:
STOP. Do not fix production code. Return exact root cause.

If GREEN:
recommend:
`FREEZE_NEW_CHECKPOINT_AND_AWAIT_EXPLICIT_WAVE_S_APPROVAL`

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_FULL_EXISTING_CATALOG_ADVERSARIAL_205.md`

Leave UI/backend/Task API/MCP running.
Return verdict, START_HEAD, report commit, 27-skill matrix, adversarial matrix, service health, latency/provenance stats.
Then stop.
