# GigaCode — Current Action

## ACTIVE: Assignment A229R1 — Low-risk latency remediation re-gate

Role: QA/performance tester only. Do not modify code.

Baseline:
- A229 latency checkpoint = `checkpoint/v4-latency-baseline-green-a229` @ `f1141aad`;
- owner changes are limited to plugin/task-api/frontend scheduling/observability;
- planner-turn reduction R4 is NOT part of this assignment.

## P0 — integrity

1. Pull current branch; record START_HEAD and clean worktree.
2. Verify latency baseline checkpoint exists.
3. Verify stable Agent Core/robust/reliable/LLM files are unchanged vs A229 baseline.
4. Run:
   - focused new regression tests;
   - full V4 blast-radius;
   - task-api focused tests;
   - frontend tsc + vite build.
5. Any correctness/build regression => RED STOP.

## P1 — R1 sprint single-read proof

Scenario:
`Задачи в работе в сентябрьском спринте по DMS`

Run 10 warm sequential samples with fresh oracle.

Require:
- exact 11-key source parity on every valid run;
- exactly ONE `sprints/DMS-SPRNT-3/tasks?complete=true...` source collection read per request;
- zero duplicate sprint-corpus reads;
- zero local fallback / tenant-wide scan.

Compare to A229 baseline:
- baseline B p50 = 39.3s;
- baseline duplicate cost ≈ 1.4s/request.

Target:
- duplication = 0/10;
- B p50 <= 38.0s unless LLM variance statistically dominates; if wall target misses but source duplicate is eliminated, report both facts separately rather than hiding the variance.

## P2 — R2 assignee+space source pushdown

Use the same WMB/Kalachanov source scope from A229 scenario D.

First independently inspect Task API/MCP request arguments.

Require:
- TQL contains BOTH source predicates: `assigned_to = <canonical id>` AND `space = "WMB"`;
- client-side space validation still applies;
- factual result remains exact and grounded;
- no status/source semantics weakened.

Measure direct route 10 times and end-to-end D 10 times.

Baseline:
- direct source route p50 34.5s / max 46.9s;
- D wall p50 61.7s / p90 165.3s.

Targets:
- direct route p50 <= 10s, preferred <= 5s;
- D wall p50 <= 45s;
- exact parity 10/10.

If source still spends ~30s despite proven narrower TQL, classify it source/provider-bound; do not suggest local factual caching.

## P3 — R3 UI bounded fan-out

For Overview, Sprint, Releases, Team, Quality:
- use fresh session/load;
- record all /api/v1/query start/end times;
- verify at most **2** snapshot Agent POSTs are simultaneously in flight;
- eventual snapshot count/contents must match the pre-fix page contract;
- no snapshot silently skipped;
- Tasks explicit submit remains one request;
- SPA navigation back must preserve the existing zero-auto-POST snapshot behavior.

Compare to A229 baseline: 4–5 concurrent POSTs/page within <=1ms.

Target: max active snapshot trajectories <=2 on every route.

## P4 — R5 capability stage logging

For scenarios A-E:
- confirm each executed governed capability emits one structured `V4 capability completed` log with capability_id, duration_ms and outcome;
- no secret/user payload dumping is introduced;
- correlate capability timings with LLM/source/total timing.

Recompute stage decomposition.
Target: unexplained residual <=15% of wall for representative median runs where logs are complete. If not achievable from current events, state exactly which stage remains unobservable.

## P5 — focused before/after matrix

Run 5 valid warm samples each for A-E from A229:
A text+person;
B sprint+status;
C sprint list;
D open+attachments WMB;
E exact task.

Report before -> after:
- p50/p90;
- LLM calls;
- capability calls;
- source calls;
- exact parity.

Do NOT attribute provider outage samples to optimization results; re-run them after endpoint recovery as A229 did.

## P6 — correctness/source guard

Across the whole assignment require:
- exact source parity;
- 0 false zero;
- 0 local factual fallback;
- 0 unauthorized mutations;
- 0 tenant-wide scans;
- 0 hidden truncation;
- no cross-request factual cache.

## P7 — decision on R4

Based only on measured A229R1 results, answer:
- Is ordinary latency now acceptable enough to avoid touching planner-turn behavior?
- If not, quantify the remaining removable Agent-side LLM call-count cost.
- Do not implement R4.
- If recommending R4, define the smallest generic planner-turn reduction and the exact A205R/A227 regression matrix it would require.

## Verdict

Exactly one:
- `AGENT_CORE_V4_LATENCY_GREEN_A229R1`
- `AGENT_CORE_V4_LATENCY_RED_A229R1`

GREEN requires correctness GREEN plus verified implementation of R1/R2/R3/R5. Missing an aspirational wall-clock target due solely to measured provider variance is not automatically RED if the targeted technical duplication/contention is proven removed; report it explicitly.

If GREEN:
- recommend whether to proceed to A229R2 (planner-turn reduction) or skip R4 and continue release hardening/security;
- do not modify code.

If RED:
- preserve first failing evidence and STOP.
