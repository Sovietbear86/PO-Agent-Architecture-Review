# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_199_V4_PRE_WAVE_S_FINAL_REGRESSION`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code. Do not start Wave S. If a defect is found, classify/report only.

## Context
A198 returned `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_RED` with one blocking functional defect:

- multi-filter person+sprint(+status) queries could execute a legitimate `task.search` without repeating an already-resolved optional `space` argument;
- `covers_resolved_constraints` therefore remained unmet;
- the A198 READY safety guard correctly rejected premature READY;
- the planner then looped until step-budget exhaustion / client timeout.

A198 also proved:
- task.aging is now exact against REAL AS21 timestamps;
- attachment D2 and task.similar are closed;
- no premature resolver-only completion;
- 27/27 existing skills were exercised;
- identity/clarification/browser/plugin gates remain healthy.

Owner fixes after A198:
- `65f995150ab427afeadf400057618275fa7a9d6d` — generic typed resolved-constraint argument derivation;
- `c01186dde22c5160192c0a0f5c7dfe62b3e8eda0` — runtime injects uniquely resolved constraints only when the target capability schema accepts the argument;
- `f75f70a3739d1d2059590be9c68229b171908969` — regression proving omitted resolved space is injected and completes without an extra planner repair turn;
- `83df8f87359975056f2c1f091087c22e6be312a6` — project+release searches fail closed instead of falling through to local `/api/v1/tasks`;
- `9413702aebae22823b944b9f231f14b01167c1ee` — fixes A198 F1 composite-skill registry test.

Architecture rule:
The new injection is generic typed orchestration, not skill/entity hardcode:
- no query parsing;
- no surname/task/space literals;
- only values from typed resolver observations;
- only unique values;
- only roles accepted by the target capability schema;
- ambiguous/multiple values are never injected.

Permanent rollback:
`0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`.

## Mission
Produce the final clean pre-Wave-S verdict after the A198 sole RED fix. A199 may be GREEN only with zero RED rows and no local-store factual path.

## Phase 0 — start / architecture audit
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record exact START_HEAD; tracked worktree clean.
3. Read A198 report and owner diff since A198 START_HEAD.
4. Confirm:
   - resolved-constraint injection is generic and entity-free;
   - only unique typed resolver values can be injected;
   - target capability schema must explicitly accept the role;
   - no semantic prepass/entity hardcode;
   - READY guard remains intact;
   - release project-only path no longer falls through to local `/api/v1/tasks`;
   - Hermes/plugin/dummy-55 architecture remains intact.

Any architecture violation => RED.

## Phase 1 — automated suites
Run:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4*.py -v
python -m pytest tests/test_v4*.py -v
```

Run relevant Task API tests.

Require:
- composite task-catalog binding test GREEN;
- deterministic resolved-constraint injection test GREEN;
- premature READY guard tests GREEN;
- aging timestamp-provenance tests GREEN;
- dummy-55/plugin gate GREEN.

Record exact totals.

## Phase 2 — focused D1 multi-filter gate
Build a fresh REAL AS21 Oracle immediately before runs.

Run at least 10x:
- `Открытые задачи Жданова в текущем спринте DMS`

Run at least 10x:
- `задачи Гаранина в сентябрьском спринте`

For completed runs require:
- actual loaded skill = `tasks.search`;
- resolver observations may establish `space`, `member`, `sprint`;
- terminal `task.search` must contain every uniquely resolved compatible constraint after runtime argument completion;
- if planner omitted `space`, record proof that runtime injected `space=DMS` before capability execution;
- completion = `runtime_contract`;
- exact key-set parity vs fresh person+sprint(+status) Oracle;
- no repeated rejected READY loop;
- no step-budget exhaustion caused by missing optional resolved arguments;
- practical bounded latency.

Typed NEEDS_CLARIFICATION remains valid only where source ambiguity genuinely exists.

Any false completion, missing constraint, 300s loop or step-budget regression => RED.

## Phase 3 — local-store release-path audit
Exercise:
- `Задачи релиза Q3-2026 в DMS`
- `Здоровье релиза Q3-2026 в DMS`

Audit Task API logs.
Require:
- zero `GET /api/v1/tasks` reads caused by these release queries;
- if REAL AS21 release source remains unavailable, result is typed SOURCE_CONDITIONAL/fail-closed;
- no local rows can be returned as REAL AS21 facts.

Any release factual local-store path => RED.

## Phase 4 — full 27-skill matrix
Repeat all 27 existing V4 skills from A198. No row skipped.

For each record:
- NL query;
- expected/actual skill;
- trajectory;
- final executed arguments;
- completion mode;
- source route;
- fresh Oracle parity;
- evidence;
- UIContract;
- classification.

Allowed:
- GREEN_SOURCE_SUPPORTED
- SOURCE_CONDITIONAL
- RED

Overall GREEN requires zero RED.

## Phase 5 — retained regressions
Repeat:
- DMS-380 -> assignee tasks 5x exact;
- full-name assignee 5x exact;
- non-team identity exact;
- ambiguous surname -> clarification -> same-session continuation;
- invented identity safe;
- task.aging DMS 3x exact against fresh timestamp oracle;
- task.similar DMS-380 3x deterministic;
- WMB-30000 attachments 3x exact;
- current sprint 3x;
- no stale source-error text.

## Phase 6 — Browser C
At minimum:
- person+sprint multi-filter query;
- aging DMS;
- task.quality widget;
- similar-task widget;
- identity clarification continuation;
- release SOURCE_CONDITIONAL;
- safe not-found.

For the person+sprint case, capture backend trajectory and prove the UI result matches the injected resolved constraints and Oracle.

## Phase 7 — plugin/extensibility
Re-run dummy-55 / A190 gate. No core changes required for adding a skill.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_GREEN`
- `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires:
- 27/27 skills tested;
- zero RED;
- multi-filter D1 closed;
- no premature planner READY;
- no local-store factual path;
- factual rows exact;
- SOURCE_CONDITIONAL rows truly source-limited and fail-closed;
- Browser C + identity + clarification + dummy-55 GREEN.

If GREEN recommendation must be:
**Freeze A199 as the clean pre-Wave-S checkpoint and proceed to owner Wave S #23–32 through the existing plugin surface.**

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_FULL_EXISTING_CATALOG_REGRESSION_199.md`

## Service keepalive
Leave tested current-HEAD UI/backend/Task API/MCP running. Return URLs, ports, PIDs, health and exact START_HEAD. Then stop.
