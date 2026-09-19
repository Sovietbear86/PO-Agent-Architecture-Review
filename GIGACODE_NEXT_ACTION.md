# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_200_V4_PRE_WAVE_S_ZERO_RED_REGRESSION`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT start Wave S.
Do NOT add new skills.
If any RED appears, classify/report only and stop progression.

## Context
A199 tested 27/27 existing V4 skills. The canonical matrix itself was 20 GREEN / 7 SOURCE_CONDITIONAL / 0 RED, but the new cross-skill person-scope gate found one deterministic blocking defect:

- planner loaded broad `tasks.search`;
- then pivoted to specialized `task.search_attachments` or `task.search_text`;
- the specialized capability executed correctly with canonical REAL AS21 identity;
- deterministic completion still required the abandoned broad skill contract because completion was scoped to every loaded skill;
- result: READY rejection/repair loop and eventual failure.

Owner fixes after A199:
- `da24608e65be966a24d348c4d0f8c3fd6dcd14bd` — generic completion frontier: latest loaded contracted skill is required; earlier contracted skills remain required only after one of their required capabilities has actually executed; earlier loaded-but-unengaged skills are treated as superseded planner registration attempts;
- `41569149d243bc2b4002500f466ce4cbaf2c6925` — Agent Core deterministic completion now uses the generic completion frontier;
- `f359ae2843a44db7ff1c94acc9b47459a764fc97` — unit tests for superseded broad skill, engaged earlier skill retention, and latest-unexecuted skill fail-closed.

The fix is generic and entity-free:
- no query parsing;
- no person/task/space literals;
- no specific skill-id branch;
- no source bypass;
- no weakening of the premature-READY guard;
- a latest skill with an unmet contract still blocks;
- an earlier skill that has actually begun its required capability work still remains on the completion frontier.

Permanent rollback checkpoint remains:
`0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`.

## Mission
Prove **zero RED** across the entire existing V4 surface before any new skill is allowed.

A200 is the hard freeze gate. No Wave S until A200 GREEN.

## Phase 0 — architecture audit
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record exact START_HEAD; tracked worktree must be clean.
3. Read A199 report and owner diff since A199 START_HEAD.
4. Confirm:
   - completion frontier logic is generic and entity-free;
   - no `if skill_id == ...` or capability-specific orchestration was added to Agent Core;
   - latest contracted skill cannot auto-complete without its requirement;
   - an earlier engaged skill remains required;
   - an earlier unengaged/superseded skill may not poison a later specialized completed skill;
   - READY safety guard remains intact;
   - person-scoped capabilities still use governed `member.resolve`;
   - zero local-store factual fallback;
   - plugin/dummy-55 extensibility invariant remains intact.

Any violation => RED.

## Phase 1 — automated suites
Run:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4*.py -v
python -m pytest tests/test_v4*.py -v
```

Run relevant Task API suites.

Mandatory named proofs:
- completion frontier superseded broad skill test GREEN;
- earlier engaged skill retained test GREEN;
- latest unexecuted skill still blocks GREEN;
- premature READY safety tests GREEN;
- deterministic resolved-constraint injection GREEN;
- universal person-resolution tests GREEN;
- dummy-55/plugin registry GREEN.

Record exact totals.

## Phase 2 — A199 blocking defect re-gate
Use fresh REAL AS21 Oracle.

### K1 person-scoped attachments
Run at least 10x:
`Задачи Калачанова с вложениями в WMB`

Require every valid run:
- natural person reference resolves through generic `member.resolve`;
- canonical source identity = REAL AS21-confirmed identity;
- specialized `task.search_attachments` executes;
- if planner previously loaded `tasks.search` but never executed its terminal `task.search`, that broad skill must not block specialized completion;
- completion = `runtime_contract`;
- exact task/file parity against fresh WMB+person Oracle;
- no rejected-READY loop;
- no bounded-repair loop;
- no step-budget exhaustion;
- no 180/300s hang caused by completion logic.

### K2 person-scoped text
Run at least 10x:
`Найди задачи Калачанова про 2027 в WMB`

Same requirements, with exact task-key parity against fresh scoped Oracle.

### Negative frontier controls
Prove synthetically and/or live:
- latest loaded contracted skill with no required observation still cannot complete;
- an earlier skill whose required capability has executed remains required and cannot be silently abandoned.

Any false completion => RED.

## Phase 3 — cross-skill person-scope gate
Re-run all:
- person attachments;
- person text;
- person status;
- person aging;
- task.search_assignee;
- non-team unique identity;
- ambiguous surname -> typed clarification -> same-session continuation;
- invented identity safe.

For every capability accepting a natural person/reference:
- no raw surname/full name may be used directly as canonical source assignee;
- governed source-backed resolution first;
- team roster is hint only, never population boundary.

## Phase 4 — multi-filter retained gate
Repeat:
- `Открытые задачи Жданова в текущем спринте DMS` 10x;
- full-name + current sprint 5x;
- period sprint clarification/continuation.

Require:
- deterministic resolved constraint injection retained;
- exact Oracle parity;
- runtime_contract;
- zero step-budget/READY regression.

## Phase 5 — complete 27-skill regression
Repeat **all 27 existing V4 skills**. No skips.

For every row capture:
- NL query;
- expected/actual skill;
- loaded skills;
- executed capabilities;
- computed completion frontier;
- trajectory;
- final arguments;
- source routes;
- completion mode;
- fresh Oracle parity;
- evidence;
- UIContract;
- GREEN / SOURCE_CONDITIONAL / RED.

GREEN overall requires **0 RED**.

SOURCE_CONDITIONAL is allowed only for proven source limitations and must fail closed without local truth or fabrication.

## Phase 6 — local-store/source audit
Across the whole run:
- audit task-api logs;
- factual V4 paths must have **0 reliance** on `/api/v1/tasks`;
- release routes must fail closed if live release source is unavailable;
- no factual local rows may be labeled REAL AS21.

Any local factual dependency => RED.

## Phase 7 — Browser C
At minimum:
1. `Задачи Калачанова с вложениями в WMB`
2. `Найди задачи Калачанова про 2027 в WMB`
3. person status in WMB
4. person+sprint multi-filter
5. aging DMS
6. similar DMS-380
7. task quality
8. ambiguity -> option-click continuation
9. release SOURCE_CONDITIONAL
10. safe invented/not-found

K1/K2 must render successful V4 results, not generic V4 ERROR.

## Phase 8 — stability
Repeat high-risk scenarios:
- K1 attachments ×5 additional;
- K2 text ×5 additional;
- DMS-380 -> assignee ×5;
- full-name assignee ×5;
- person+sprint ×5;
- aging ×3;
- attachments exact-task ×3.

No stochastic regression may be hidden. If a run fails, retain it and classify root cause.

## Phase 9 — plugin/extensibility
Re-run A190 dummy-55 gate.

Adding a synthetic new skill must still require zero Agent Core/planner/runtime business-logic edits.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_GREEN`
- `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires:
- all 27 skills tested;
- cross-skill person-scope gate tested;
- **0 RED**;
- A199 K1/K2 closed;
- no false completion from completion-frontier logic;
- no premature planner READY;
- factual GREEN rows exact;
- source limitations fail closed;
- zero local-store factual truth;
- Browser C GREEN for supported cases;
- dummy-55 GREEN.

If any RED exists:
**STOP. Do not recommend Wave S. Do not add skills. Return the defect for owner remediation and another full re-gate.**

If GREEN:
**Freeze A200 as the clean pre-Wave-S checkpoint. Do not start Wave S automatically; wait for explicit owner/user instruction.**

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_FULL_EXISTING_CATALOG_REGRESSION_200.md`

## Service keepalive
Leave tested current-HEAD UI/backend/Task API/MCP running.
Return URL, port, PID, health, exact START_HEAD, report commit, and GREEN/SOURCE_CONDITIONAL/RED counts.
Then stop.
