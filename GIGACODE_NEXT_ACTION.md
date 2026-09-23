# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_208B_PRE_S2_COMPLETION_CONTRACT_REGATE`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT start Wave S2.
Do NOT add skills.

## Stable rollback
Wave S1 remains GREEN at:
`checkpoint/v4-wave-s1-green@ce64264c868afd73743d5daafdeaee767e07adef`

## A208 result
A208 re-run closed the originally reported manual gaps:
- blocked drill-down = 10/10 exact;
- blocked ↔ sprint.health parity exact;
- raw source status filtering exact, including `На исправлении`;
- source/local safety retained.

It found one new deterministic owner defect:
- `sprint.scope` and `sprint.wip` completion contracts required `task_keys`;
- V4 observation compaction intentionally converts `task_keys` to `task_keys_sample` + `task_key_count` and removes the full array;
- therefore the completion contract could never be satisfied on compacted observations whenever the runtime contract gate was active.

This is a contract/compaction shape mismatch, not a metric-source or planner-routing defect.

## Owner fix
The owner fix deliberately preserves compact observation behavior and aligns the plugin contracts to the stable compacted shape:
- `sprint.scope`: completion requires `sprint_id,total,task_key_count`;
- `sprint.wip`: completion requires `sprint_id,wip,task_key_count`;
- no change to `_compact_data`;
- no restoration of full task arrays into planner context;
- regression test proves real handler-style data -> `_compact_data` -> completion contract = satisfied.

Owner commits:
- `98c06bd2bec1959782a2173b55b91cd108772fe2`
- `8f7197faa6392cf3b0776b09df147f9a8aba1569`

## Phase 0 — pull / diff
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record START_HEAD; tracked worktree clean.
3. Diff from A208 START `6519b87885314076942dfb2eb09f35c67a5fecd8`.
4. Confirm new owner delta after A208 report is limited to:
   - Wave S1 completion contract keys;
   - focused test proving compatibility with compacted observations;
   - docs/spec.
5. Confirm:
   - no Agent Core/planner/runtime business edit;
   - no change to `_compact_data`;
   - no full `task_keys` restoration into planner context;
   - no per-query/entity hardcode.

Any architecture drift => RED.

## Phase 1 — automated tests
Run at minimum:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4_wave_s1.py -v
python -m pytest tests/test_agent_core_v4_task_search_source_status.py -v
python -m pytest tests/test_agent_core_v4*.py -v
python -m pytest tests/test_v4*.py -v
```

Require zero unexplained failures.

Explicitly prove:
- raw output with task_keys compacts to task_key_count/task_keys_sample;
- sprint.scope completion contract satisfies on compacted observation;
- sprint.wip completion contract satisfies on compacted observation;
- wip=0 would still be contract-valid if total/source task set is otherwise valid.

## Phase 2 — LLM preflight
Run 3 planner-sized probes.

If all 3 are within current 60s runtime budget, continue.
If the endpoint is again degraded beyond runtime budget, stop as:
`BLOCKED_BY_PROVEN_SOURCE_OUTAGE`.

Do NOT raise the production timeout just to make QA pass.

## Phase 3 — re-run exact failing A208 forms
Fresh sessions, at least:
- `wip спринта по DMS` ×5
- `WIP спринта DMS-SPRNT-3` ×3
- `scope спринта по DMS` ×5
- `scope спринта DMS-SPRNT-3` ×3

Require:
- actual metric capability executes;
- no `ready_rejected=unsatisfied_completion_contract` loop;
- completion = runtime_contract or otherwise contract-satisfied governed completion;
- exact metric/key-count parity vs fresh REAL AS21 oracle;
- no planner-ready bypass through unrelated contract-less skills is required for success.

Any deterministic contract failure => RED.

## Phase 4 — period/current parity
Run:
- `WIP сентябрьского спринта по DMS` ×3
- `scope сентябрьского спринта по DMS` ×3
- `WIP текущего спринта DMS` ×3
- `scope текущего спринта DMS` ×3

Require all forms resolve to the same authoritative sprint and produce exact parity with explicit-id forms.

## Phase 5 — retain blocked/status fixes
Fresh Oracle, then re-run:
- blocked tasks explicit sprint ×3;
- blocked tasks period form ×2;
- blocked tasks current form ×2;
- `На исправлении` ×3;
- one known-enum status;
- not_completed;
- completed.

Require exact source parity and blocked count = sprint.health blocked count for the same source moment.

## Phase 6 — full S1 metric sanity
Run:
- sprint.velocity short form;
- sprint.throughput short form;
- sprint.wip;
- sprint.scope.

Require all four GREEN and no semantic drift in units/formulas.

## Phase 7 — retained high-risk regression
At minimum:
- sprint.health;
- task.history;
- task.time_in_status;
- person+status;
- unassigned;
- attachments;
- same-session `этот спринт`;
- DMS-380 lookup;
- Browser C representative queries.

Release.search may remain SOURCE_CONDITIONAL if /versions is independently still 502.

## Phase 8 — architecture/source audit
Require:
- local factual `/api/v1/tasks` reads = 0;
- no fake/frozen/local factual fallback;
- no tenant-wide scan;
- dummy-55/plugin invariant GREEN;
- no hardcoded people/spaces/sprint ids/status labels;
- compact planner observations remain bounded.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_PRE_S2_COMPLETION_CONTRACT_GREEN`
- `AGENT_CORE_V4_PRE_S2_COMPLETION_CONTRACT_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

If GREEN recommend exactly:
`PROCEED_TO_WAVE_S2_OWNER_IMPLEMENTATION`

If RED:
STOP. Do not fix production code. Do not start S2.

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_PRE_S2_COMPLETION_CONTRACT_REGATE_208B.md`

Leave UI/backend/Task API/MCP running.
Return verdict, START_HEAD, report commit, scope/wip matrix, blocked-health parity, raw-status parity, service health.
Then stop.
