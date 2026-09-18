# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_198_V4_EXISTING_CATALOG_FINAL_REGRESSION_REGATE`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code. Do not start Wave S. If a defect is found, classify/report only.

## Context
A197 executed the complete 27-skill catalog and returned RED only because `task.aging` produced a false complete zero. Root cause was proven: SWTR raw TQL rows expose `unit.createdAt` / `unit.updatedAt`, while the source bridge only looked for snake_case `created_at` / `updated_at`.

A197 also found a generic completion-safety issue in one person+sprint scenario: the planner could emit READY after only `member.resolve`, before the loaded skill's declared completion contract was satisfied.

Owner fixes after A197:
- `3ab768ad4b4d6731d9377ba466dff88a22d9176e` — map SWTR camelCase timestamps into canonical task-query fields;
- `5aeb5b3c108b1bb0a0761920314f80a15d686413` — preserve timestamp provenance in Task API adapter;
- `4c79bc43be0256e0d47cbfd60c4446b72e2a8951` — aging ignores/fails closed on adapter fallback timestamps;
- `630b536def8ffc22483fd618f656ee3a8cec052f` — generic runtime guard rejects planner READY when every loaded skill has a declared typed completion contract and the contract is still unmet;
- `e30ec7ddeb1d80caa0ad63818e0aa98c1fed9516` — completion regression test;
- `afaa7e048c45b5de33d7e43bd03eb8bfa2ad4fcd` — fix A197 F1 test logic to validate cross-plugin bindings against the full registry;
- `a65eba6f10489d033ae4cde532545827eb336f9f` — timestamp-provenance aging test.

The READY fix is **generic orchestration safety**, not a business-skill route: no surname/person/space/task hardcode and no semantic prepass.

Permanent rollback:
`0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`.

## Mission
Deliver one final pre-Wave-S regression verdict for the entire existing 27-skill catalog. A198 is GREEN only if:
- aging is exact against live timestamp Oracle;
- no premature planner-ready completion remains in the tested contracted flows;
- all previous A196/A197 protections remain intact;
- zero RED rows remain.

## Phase 0 — start / architecture audit
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record exact START_HEAD; tracked worktree clean.
3. Read A196 and A197 reports plus owner diff since A197 START_HEAD.
4. Confirm:
   - camelCase timestamp fix is source-boundary only;
   - timestamp provenance prevents fallback `datetime.now()` from becoming an aging fact;
   - READY rejection is generic and applies only where all loaded skills have typed completion contracts;
   - contractless skills retain normal planner READY behavior;
   - no new business/entity hardcode;
   - Hermes/plugin extension model remains intact;
   - no local-store truth/fallback.

Any violation => RED.

## Phase 1 — automated suites
Run at minimum:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4*.py -v
python -m pytest tests/test_v4*.py -v
```

Run relevant Task API tests.

Require:
- A197 F1 task-catalog test fixed;
- completion-contract test proving premature READY is rejected until required capability executes;
- aging source-timestamp provenance test GREEN;
- dummy-55/plugin gate GREEN.

Record exact totals.

## Phase 2 — fresh Oracle B
Refresh, do not reuse stale counts:
- DMS raw/source rows with `unit.createdAt`;
- canonical task-query rows with `created_at`;
- open DMS tasks >=7 days old;
- DMS-380;
- current sprint and complete sprint task set;
- assignee/identity cases;
- WMB-30000 attachments;
- release/history source availability.

Mandatory timestamp proof:
- show at least 3 concrete DMS task keys where raw `unit.createdAt` equals canonical `created_at`;
- count how many DMS rows have source timestamp provenance;
- if a source row lacks creation time, prove aging excludes/fails closed rather than assigning age=0 as a fact.

## Phase 3 — task.aging final gate
Run `Застоявшиеся открытые задачи в DMS` at least 5x, fresh sessions, concurrency 1.

Require each run:
- skill `task.aging`;
- live bounded `task-query?space=DMS`;
- zero tenant-wide search;
- exact count and key-set parity with the fresh Oracle using REAL source timestamps;
- no adapter-fallback timestamp counted;
- deterministic completion via runtime contract;
- practical bounded latency.

Any false zero or key mismatch => RED.

## Phase 4 — completion-gate adversarial
Repeat at least 10x:
- `задачи Гаранина в сентябрьском спринте`
and at least 5x:
- one equivalent full-name + current/period sprint multi-step query.

For every run:
- no `completion=planner_ready` before the primary factual capability required by the loaded completion contract executes;
- typed clarification is acceptable when source/entity context is genuinely missing;
- completed runs must end via `runtime_contract` when the loaded skills have declared contracts;
- no answer may claim completion from resolver-only observations.

Also run a control skill without a declared completion contract, if one exists, to prove normal READY semantics were not globally disabled.

## Phase 5 — full 27-skill API matrix
Repeat **all 27** currently exposed skills from A197. No row skipped.

For each record:
- NL query;
- expected/actual skill;
- capability trajectory;
- status;
- completion mode;
- source provenance;
- fresh Oracle parity;
- evidence;
- UIContract;
- GREEN/SOURCE_CONDITIONAL/RED.

Broad space-wide Excel/PDF/MSG may remain SOURCE_CONDITIONAL only if they fail closed quickly before N+1 fan-out exactly as A197 proved.

Overall GREEN requires **zero RED rows**.

## Phase 6 — retained high-risk regression
Repeat:
- DMS-380 -> assignee tasks 5x exact;
- inflected full-name assignee 5x exact;
- non-team identity exact;
- ambiguous surname -> source candidates -> same-session continuation;
- invented person safe;
- person+sprint 5x;
- current sprint 3x;
- WMB-30000 attachments 3x;
- similar DMS-380 3x deterministic bounded;
- zero stale source-error text for normal ambiguity/not-found.

Explicitly audit task-api logs for local `/api/v1/tasks` reads during the matrix. Any factual path relying on local truth => RED. Incidental unexplained local reads must be traced/classified, not ignored.

## Phase 7 — Browser C spot/full gate
At minimum:
- task.quality -> `task_analysis` widget;
- aging DMS -> factual collection/count matching backend;
- similar DMS-380 -> similar-task widget;
- history source-unavailable;
- identity clarification + continuation;
- person+sprint multi-step query;
- safe not-found.

No Legacy Harness execution for the tested query.

## Phase 8 — plugin/extensibility
Re-run A190 dummy-55 gate. No new skill/core coupling.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_GREEN`
- `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires:
- 27/27 skills explicitly tested;
- zero RED;
- aging exact and timestamp provenance proven;
- no premature planner-ready completion in contracted trajectories;
- factual GREEN rows exact;
- SOURCE_CONDITIONAL rows truly source-limited and fail-closed;
- Browser C, identity, clarification and dummy-55 GREEN;
- zero local-store truth.

If GREEN recommendation must be:
**Freeze A198 as the clean pre-Wave-S checkpoint and proceed to owner Wave S #23–32 through the existing plugin surface.**

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_FULL_EXISTING_CATALOG_REGRESSION_198.md`

## Service keepalive
Leave tested current-HEAD UI/backend/Task API/MCP running. Return URLs, ports, PIDs, health and exact START_HEAD. Then stop.
