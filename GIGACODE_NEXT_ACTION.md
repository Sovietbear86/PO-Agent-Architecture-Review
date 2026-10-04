# GigaCode — Current Action

## ACTIVE: Assignment A229R1 — Low-risk latency verification

Role: QA/performance tester only. Do not modify production/plugin/frontend/backend/test/config code.

Current certified functional baseline:

`checkpoint/v4-created-period-status-green-a229f2r3@aa78e52c9e311eb6e7f0357001afe5bc4843068a`

A229 latency baseline:

`checkpoint/v4-latency-baseline-green-a229@f1141aade7bffcd8cfd376174544d3f1172da08c`

This assignment verifies already-implemented low-risk latency changes only.

Do NOT implement:
- planner-turn reduction;
- caching of factual business data;
- Core/planner/runtime changes;
- source weakening;
- query-specific shortcuts.

## P0 — integrity / correctness guard

1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD and clean worktree.
2. Prove stable Core/Harness/API session files are byte-identical to the latest certified stable baseline.
3. Run focused latency-remediation regressions:
   - sprint single-read;
   - assignee+space source pushdown;
   - UI snapshot concurrency;
   - capability timing instrumentation.
4. Run full V4 blast-radius.
5. Require retained functional correctness including A229F2R3 created-period/status tests.
6. Any correctness regression => RED STOP.

## P1 — R1 sprint single-read verification

Scenario:
`Задачи в работе в сентябрьском спринте по DMS`

Build a fresh independent REAL AS21 oracle first.

Run 10 warm sequential valid samples.

Require:
- exact source parity every valid run;
- one and only one complete sprint-corpus source read per request;
- no duplicate `get_sprint_tasks` / equivalent full sprint collection read;
- no local fallback;
- no tenant-wide scan.

Measure:
- end-to-end wall;
- capability duration;
- source-read duration;
- LLM/planner call count.

Compare against A229 baseline:
- B p50 ≈ 39.3s;
- duplicate sprint read cost ≈ 1.4s/request.

Report before → after:
- p50;
- p90;
- source calls/request;
- planner calls/request.

## P2 — R2 assignee + space source pushdown

Use a live person+space query equivalent to the A229 WMB/Kalachanov case, but keep the exact same person/space through all 10 samples.

Before timing:
- independently inspect the Task API/MCP request and prove the source predicate contains BOTH canonical assignee AND explicit space.

Require:
- client-side validation remains;
- result is exact and source-backed;
- no broad whole-assignee/whole-tenant scan.

Run:
- direct bounded source route 10 times;
- end-to-end Agent query 10 times.

A229 baseline:
- direct source route p50 ≈ 34.5s, max ≈ 46.9s;
- end-to-end D p50 ≈ 61.7s, p90 ≈ 165.3s.

Primary success criterion:
- source query is demonstrably narrower and exact.

Performance target:
- direct source route p50 <= 10s, preferred <= 5s;
- end-to-end p50 <= 45s.

If the source remains slow despite proven pushdown, classify the remaining time as source/provider bound. Do not recommend factual caching.

## P3 — R3 UI bounded snapshot fan-out

For each page that performs snapshot loading:
- Overview;
- Sprint;
- Releases;
- Team;
- Quality;

record all `/api/v1/query` start/end timestamps on a fresh page/session load.

Require:
- max simultaneously in-flight snapshot Agent POSTs <= 2;
- all expected snapshots eventually complete or surface typed source failure;
- no snapshot silently skipped;
- Tasks explicit submit remains one request;
- navigation back does not create unintended auto-POSTs beyond the existing certified snapshot contract.

A229 baseline:
- 4–5 concurrent full Agent trajectories were launched almost simultaneously.

Report:
- max concurrency per page;
- total page snapshot completion time;
- any queueing effect.

## P4 — R5 stage timing observability

For representative scenarios A–E from A229, confirm executed governed capabilities emit structured timing with:
- capability_id;
- duration_ms;
- outcome.

Also record:
- total wall;
- LLM/planner time/call count where observable;
- Task API/MCP/source duration where observable.

Require:
- no secrets or factual payload dumps in timing logs;
- instrumentation does not alter capability results.

Recompute stage decomposition and state which share is:
- LLM/planner;
- governed capability excluding source;
- Task API/MCP/source;
- unexplained residual.

Target:
- unexplained residual <= 15% for representative median runs when complete logs are available.
If not achieved, identify the missing timing boundary precisely.

## P5 — before/after representative latency matrix

Run 5 valid warm samples each for:

A. person + text;
B. sprint + status;
C. sprint list;
D. open + attachments + person + space;
E. exact task lookup;
F. created-period + open;
G. created-period + in-progress.

For each scenario report:
- p50/p90;
- LLM/planner calls;
- capability calls;
- source calls;
- exact source parity.

Use fresh independent Oracle for factual scenarios.

Provider outage / 429 / transient connectivity runs:
- fail closed;
- are documented separately;
- are not counted as optimization measurements;
- are re-run after recovery.

## P6 — correctness/source audit

Across A229R1 require:
- exact source parity for every factual completed run;
- 0 false zero;
- 0 local factual fallback;
- 0 unauthorized mutations;
- 0 tenant-wide scans;
- 0 hidden truncation;
- 0 cross-request factual cache;
- 0 Agent Core changes.

## P7 — decision gate

Answer these questions from evidence only:

1. Did R1 remove duplicate sprint reads?
2. Did R2 narrow the source query and materially improve direct-route latency?
3. Did R3 reduce simultaneous full Agent trajectories to <=2 without losing snapshots?
4. Does R5 explain enough wall time to identify the real remaining bottleneck?
5. Is ordinary interactive latency now acceptable enough to avoid planner changes?

Do NOT implement R4.

If latency is still unacceptable, quantify:
- current planner calls/request;
- planner/LLM share of wall;
- removable expected time if calls were reduced by exactly one;
- which certified A205/A227/A229F2 trajectories would need re-gating.

Then recommend either:
- `SKIP_R4_PROCEED_A230`, or
- `CONSIDER_A229R2_PLANNER_TURN_REDUCTION`.

## Verdict

Exactly one:
- `AGENT_CORE_V4_LATENCY_GREEN_A229R1`
- `AGENT_CORE_V4_LATENCY_RED_A229R1`

GREEN requires:
- P0 correctness GREEN;
- R1/R2/R3/R5 implementation verified;
- source/correctness guards GREEN.

Missing an aspirational wall-clock target due solely to independently measured provider/source variance is not automatically RED if the intended technical optimization is proven and correctness remains exact. Report the variance explicitly.

If GREEN:
- provide the P7 recommendation;
- do not modify code.

If RED:
- preserve first failing boundary and STOP.

Do not modify code.
