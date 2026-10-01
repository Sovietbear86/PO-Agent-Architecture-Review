# GigaCode — Current Action

## ACTIVE: Assignment A229 — Release Hardening: Latency Baseline & Bottleneck Analysis

Role: QA/performance tester only. Do not modify production/frontend/backend/plugin/test/config code.

Baseline:
- A227R3 PO acceptance GREEN;
- A228 restart/recovery GREEN;
- checkpoint: `checkpoint/v4-release-recovery-green-a228`;
- functional behavior and source contracts are frozen.

This assignment is **measurement first**. Do not optimize code. Return a stage-by-stage latency report and the first proven bottleneck(s).

## P0 — integrity / warm baseline

1. Pull current branch; record START_HEAD and clean worktree.
2. Verify checkpoint exists.
3. Run full V4 regression and frontend build.
4. Start/confirm all services on START_HEAD.
5. Let services reach steady state before measuring; record process PIDs, CPU/memory if available, and source health.
6. Record whether each sample is cold, reconnect, or warm steady-state.

Any correctness/source regression => RED STOP.

## P1 — representative query matrix

Measure at least 10 warm runs per scenario, sequentially unless a concurrency phase explicitly says otherwise:

A. Single-capability text+person:
`Задачи Семавина по рискам`

B. Multi-step sprint+status:
`Задачи в работе в сентябрьском спринте по DMS`

C. Sprint list:
`Спринты в DMS`

D. Attachment/person/status:
`Открытые задачи Калачанова с вложениями в пространстве WMB`

E. One exact task lookup/summary using a real known task key.

For every run record:
- total wall-clock;
- status and exact factual parity;
- planner decision count / LLM call count;
- capability call count;
- source call count;
- terminal capability;
- trace id.

Compute P50, P90/P95, min, max per scenario.

## P2 — stage decomposition

For representative runs A-E, derive or instrument from existing logs/traces without code changes:

- request/API overhead;
- planner/LLM time per turn;
- capability handler time;
- Task API time;
- MCP-SWTR / REAL AS21 time;
- deterministic validation/normalization;
- synthesis time;
- total unaccounted overhead.

If logs cannot expose an exact stage, mark it UNKNOWN rather than guessing.

Goal: identify where the top 80% of latency sits.

## P3 — duplicate/redundant work audit

For each scenario determine:
- repeated identical planner calls;
- repeated resolver calls for the same entity inside one request;
- duplicate Task API/MCP reads;
- unnecessary source rereads after a source-backed observation already exists;
- UI-generated duplicate query fan-out.

Classify each duplicate as:
- required by correctness;
- retry/recovery;
- avoidable technical duplication;
- unknown.

No code changes.

## P4 — cold vs warm / reconnect penalty

Using the A228 restart procedures, measure:
- first factual request after Agent restart;
- first factual request after task-api restart;
- first factual request after MCP reconnect;
- second and third identical request after each recovery.

Compare warm vs cold/reconnect delta and identify initialization/connection costs separately from normal query cost.

Do not count service boot time as request latency; report boot readiness separately.

## P5 — UI snapshot fan-out

On each UI route, especially Sprint/Release/Team/Quality:
- count automatic POSTs on first submitted context;
- measure concurrency and completion spread;
- identify whether requests contend on the same LLM/source bottleneck;
- verify revisits use snapshot semantics correctly;
- flag obviously redundant calls that return overlapping source facts.

Do not propose merging metrics unless their source/skill contracts genuinely allow it.

## P6 — source-plane timing

For source-backed operations used above:
- independently measure direct Task API route latency;
- where feasible, measure MCP-SWTR call latency beneath Task API;
- distinguish server processing from planner latency;
- capture pagination/page counts and result sizes.

This phase must remain bounded and must not introduce tenant-wide scans.

## P7 — correctness guard

Across all latency tests:
- exact source parity preserved;
- 0 false zero;
- 0 local factual fallback;
- 0 unauthorized mutations;
- 0 tenant-wide scans;
- 0 source-result truncation hidden as success.

Any performance measurement that violates correctness is invalid and RED.

## P8 — bottleneck verdict

Produce a ranked **bottleneck list by measured time contribution**, not subjective guess.

For each bottleneck include:
- scenario(s);
- median/p95 impact;
- evidence;
- whether it is Agent/LLM, plugin/runtime, Task API, MCP/AS21, frontend concurrency, or environment;
- safest optimization candidate;
- expected risk to correctness;
- whether owner code change is actually warranted.

Also identify "do not optimize" areas where latency is source/provider-bound and local optimization would risk architecture quality.

## Verdict

Exactly one:
- `AGENT_CORE_V4_LATENCY_BASELINE_GREEN_A229`
- `AGENT_CORE_V4_LATENCY_BASELINE_RED_A229`

GREEN means the latency baseline/bottleneck diagnosis is trustworthy and correctness stayed GREEN. It does **not** mean latency is already acceptable.

If GREEN:
- do not create performance fixes yourself;
- recommend a prioritized owner remediation list for A229R;
- include clear before-values and target-values.

If RED:
- preserve first failing evidence and STOP.

Do not modify code.
