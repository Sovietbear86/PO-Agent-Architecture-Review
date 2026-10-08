# GigaCode — Current Action

## ACTIVE: Assignment A229R1 — Low-risk latency verification

Role: QA/performance tester only. Do not modify production/plugin/frontend/backend/test/config code.

Current certified functional baseline:
`checkpoint/v4-task-semantics-hierarchy-green-a229s1r4@afb6fa1d9b6e5d13a5d743f0d45afef94d1821a1`

A229 latency baseline:
`AGENT_CORE_V4_LATENCY_BASELINE_GREEN_A229`

This assignment verifies already-implemented low-risk latency changes only.

Do NOT implement:
- planner-turn reduction;
- factual-data caching;
- Core/planner/runtime changes;
- source weakening;
- query-specific shortcuts.

## P0 — integrity / correctness guard

1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD and clean worktree.
2. Prove Agent Core 6/6 byte-identical to the certified checkpoint above.
3. Run focused latency-remediation regressions:
   - sprint single-read;
   - assignee+space source pushdown;
   - UI snapshot concurrency;
   - capability timing instrumentation.
4. Run full V4 blast-radius and relevant Task API SWTR suites.
5. Retain A229S1R4R correctness: task.type_analysis + latest sprint composition, hierarchy, Overview KPI, task drawer.
6. Any correctness regression => RED STOP.

## P1 — R1 sprint single-read verification

Scenario:
`Задачи в работе в сентябрьском спринте по DMS`

Build a fresh independent REAL AS21 oracle first.

Run 10 warm sequential valid samples.

Require:
- exact source parity every valid run;
- one and only one complete sprint-corpus source read per request;
- no duplicate get_sprint_tasks/equivalent full sprint collection read;
- no local fallback;
- no tenant-wide scan.

Measure:
- end-to-end wall;
- capability duration;
- source-read duration;
- LLM/planner call count.

Compare against A229 baseline:
- B p50 ~39.3s;
- duplicate sprint read cost ~1.4s/request.

Report before -> after:
- p50;
- p90;
- source calls/request;
- planner calls/request.

## P2 — R2 assignee + space source pushdown

Use the same live person+space class as A229 WMB/Kalachanov for 10 valid samples.

Before timing, prove the Task API/MCP request source predicate contains BOTH canonical assignee and explicit space.

Require:
- client-side validation remains;
- result exact/source-backed;
- no broad whole-assignee/whole-tenant scan.

Run:
- direct bounded source route 10x;
- end-to-end Agent query 10x.

A229 baseline:
- direct route p50 ~34.5s, max ~46.9s;
- end-to-end p50 ~61.7s, p90 ~165.3s.

Targets:
- direct route p50 <=10s, preferred <=5s;
- end-to-end p50 <=45s.

If source remains slow despite proven pushdown, classify remaining time as source/provider bound. Do not recommend factual caching.

## P3 — R3 UI bounded snapshot fan-out

For Overview, Sprint, Releases, Team, Quality record /api/v1/query start/end timestamps on fresh page/session load.

Require:
- max simultaneously in-flight snapshot Agent POSTs <=2;
- all expected snapshots complete or surface typed source failure;
- no snapshot silently skipped;
- Tasks explicit submit remains one request;
- navigation back does not create unintended auto-POSTs beyond certified snapshot semantics.

A229 baseline: 4-5 simultaneous full Agent trajectories per page.

Report:
- max concurrency per page;
- total snapshot completion time;
- queueing effect.

## P4 — R5 stage timing observability

For representative A-E scenarios from A229, confirm governed capabilities emit structured timing:
- capability_id;
- duration_ms;
- outcome.

Record:
- total wall;
- LLM/planner time + call count;
- Task API/MCP/source duration.

Recompute stage decomposition:
- LLM/planner;
- governed capability excluding source;
- Task API/MCP/source;
- unexplained residual.

Target: unexplained residual <=15% for representative median runs when logs are complete.

## P5 — before/after latency matrix

Run 5 valid warm samples each:

A. person + text;
B. sprint + status;
C. sprint list;
D. open + attachments + person + space;
E. exact task lookup;
F. created-period + open;
G. created-period + in-progress;
H. person + latest sprint + status + task type.

For every scenario report:
- p50/p90;
- planner calls;
- capability calls;
- source calls;
- exact source parity.

Provider outage / 429 / transient-connectivity samples fail closed, are documented separately and re-run after recovery; do not count them as optimization measurements.

## P6 — source/correctness audit

Require:
- exact source parity for every factual completed run;
- 0 false zero;
- 0 local factual fallback;
- 0 unauthorized mutations;
- 0 tenant-wide scans;
- 0 hidden truncation;
- 0 cross-request factual cache;
- 0 Agent Core changes.

## P7 — decision gate

Answer from evidence:
1. Did R1 remove duplicate sprint reads?
2. Did R2 narrow source query and materially improve direct-route latency?
3. Did R3 reduce simultaneous Agent trajectories to <=2 without losing snapshots?
4. Does R5 explain enough wall time to identify the remaining bottleneck?
5. Is ordinary interactive latency acceptable enough to avoid planner changes?

Do NOT implement planner-turn reduction in this assignment.

If latency remains unacceptable, quantify:
- current planner calls/request;
- planner/LLM share of wall;
- expected removable time from exactly one fewer planner call;
- which certified trajectories require re-gating.

Recommend exactly one:
- `SKIP_R4_PROCEED_A230`
- `CONSIDER_A229R2_PLANNER_TURN_REDUCTION`

## Verdict

Return exactly one:
- `AGENT_CORE_V4_LATENCY_GREEN_A229R1`
- `AGENT_CORE_V4_LATENCY_RED_A229R1`

GREEN requires correctness/source guards GREEN and R1/R2/R3/R5 implementation verified.

If GREEN, provide P7 recommendation and do not modify code.
If RED, preserve first failing boundary and STOP.

GigaCode is QA only. Do not modify code.
