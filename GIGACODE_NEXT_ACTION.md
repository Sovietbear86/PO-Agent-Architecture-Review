# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_201_V4_CLARIFICATION_CONTINUATION_ZERO_RED_REGATE`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT start Wave S.
Do NOT add new skills.
If any RED appears, classify/report only and stop progression.

## Context
A200 certified the A199 completion-frontier fix and again proved the canonical 27-skill matrix itself is healthy:
- 20 GREEN / 7 SOURCE_CONDITIONAL / 0 RED;
- Browser C 10/10;
- local-store factual reads = 0;
- dummy-55/plugin gate = 11/11.

The sole blocking defect was D-A200-1:
`задачи Гаранина в сентябрьском спринте` -> typed space clarification -> option `DMS` could be replanned as a narrower sprint-identity/assignee-only task and falsely finish without the original requested task collection.

Owner remediation after A200 is intentionally **Harness-generic**, not skill-specific:

- `374675873b60ded28b566870d23900f37b5384d6` — HarnessRequest gets generic typed continuation fields: prior loaded skills, validated observations, required completion skills.
- `463535837265b7fde34f9de14674680cfe1d8ee0` — completion frontier can pin generic continuation objectives; latest/unengaged safety semantics remain.
- `5655d18d26b71a4370135bd2f18baa95c8271948` — Agent Core resumes typed observations/loaded skills and requires pinned continuation completion goals; clarification responses expose generic internal resume state to API only.
- `be7eccaafd72186ee6922ffefc4079eec764bd41` + `4055d71d675e6349bd5ff504ab5776bb6f9ac326` — API stores/restores typed continuation state by `session_id + clarification_id`; no skill/entity routing.
- `0dbbcd75679d4d084917a72f3a0529ef5f6a9afd` — continuation execution state is captured internally and removed from the public response payload.
- completion-frontier regression test: original pinned task objective cannot be satisfied by a sprint-identity helper alone.
- `cf7d75c91e988ac1cbd9427b8227f84bd8a30c99` — Browser/API contract test proves generic Harness state round-trips through clarification without leaking internal state.

Architecture invariant:
clarification continuation is now:
`same original Harness goal + validated observations + newly confirmed constraint -> continue execution`
not:
`answer token -> fresh independent planning problem`.

No query-specific person/sprint/DMS branches are permitted.

Permanent rollback checkpoint:
`0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`.

## Mission
Prove the existing V4 catalog has **zero RED** after the generic clarification-continuation fix.

A201 is still a hard freeze gate:
**no Wave S and no new skills until A201 GREEN.**

## Phase 0 — architecture/static audit
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record exact START_HEAD; tracked worktree clean.
3. Read A200 report and owner diff since A200 START_HEAD.
4. Confirm:
   - continuation state is generic Harness execution state only;
   - no specific skill ID, surname, sprint, space or period special-case was added to API/runtime;
   - public UI payload does not expose internal continuation observations/goals;
   - continuation state is keyed by session + clarification id and TTL behavior remains;
   - pinned completion goals are contract-driven from loaded plugin skills;
   - a helper skill cannot complete the continuation while the original pinned goal is unmet;
   - latest-unexecuted / engaged-earlier / superseded-skill frontier protections remain;
   - dynamic plugin discovery and dummy-55 invariant remain unchanged;
   - zero local-store factual fallback.

Any architecture violation => RED.

## Phase 1 — automated tests
Run:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4*.py -v
python -m pytest tests/test_v4*.py -v
```
and relevant API/Browser contract tests.

Mandatory named proofs:
- pinned continuation objective remains required;
- superseded broad skill still does not poison specialized completion;
- engaged earlier skill remains required;
- latest unexecuted skill still blocks;
- premature READY guard retained;
- resolved-constraint injection retained;
- API clarification continuation restores loaded skills/observations/required completion skills;
- continuation state does not leak into public response;
- dummy-55/plugin tests GREEN.

## Phase 2 — D-A200-1 focused re-gate
Build a fresh REAL AS21 Oracle immediately before each batch.

### P2a period-sprint continuation
Run at least 10 fresh sessions:
1. `задачи Гаранина в сентябрьском спринте`
2. receive typed `NEEDS_CLARIFICATION` when space is genuinely ambiguous;
3. choose `DMS` using the exact Browser payload shape:
   `session_id + clarification_id + clarification_option`.

For every continuation that completes:
- original `tasks.search` goal remains pinned;
- prior validated observations are restored, not discarded;
- helper `sprints.discover/sprint.search` alone MUST NOT satisfy completion;
- terminal factual task collection MUST execute;
- final task search must cover confirmed person + DMS + resolved September sprint;
- completion = `runtime_contract`;
- exact task-key parity with fresh Oracle;
- no answer may say it completed while admitting the task list was not retrieved.

Any sprint-only false completion => RED.

### P2b direct no-clarification adversarial variant
Run the same original query at least 10 additional fresh sessions.

If planner happens to skip clarification:
- it still must not return assignee-only/all-space tasks for a sprint-constrained request;
- completed result must be fully constrained and exact;
- if required constraints cannot be established, typed clarification/fail-closed is acceptable.

Any all-space/assignee-only false completion => RED and record trajectory.

## Phase 3 — clarification framework regression
Test multiple unrelated clarification classes to ensure the fix is generic:
- ambiguous person -> choose source candidate -> original task request completes;
- ambiguous space for period sprint -> continue;
- any existing release/source clarification path if available;
- invalid clarification option;
- expired/lost clarification id;
- new session must not inherit old pending continuation;
- manual option text with correct clarification_id if supported.

Require no context loss and no cross-session state leak.

## Phase 4 — retained completion/frontier regression
Repeat:
- K1 person attachments WMB 10x;
- K2 person text WMB 10x;
- person status;
- person aging;
- multi-filter current-sprint query 10x;
- DMS-380 -> assignee 5x;
- full-name assignee 5x;
- non-team identity;
- ambiguity + continuation;
- invented identity.

No regression from A199/A200 fixes.

## Phase 5 — full 27-skill matrix
Run **all 27 existing V4 skills**, no skips.

For each capture:
- NL request;
- expected/actual skill;
- loaded skills;
- resumed/pinned goal state where applicable;
- executed capabilities;
- completion frontier;
- final arguments;
- source route;
- completion mode;
- fresh Oracle parity;
- evidence;
- UIContract;
- GREEN / SOURCE_CONDITIONAL / RED.

Overall GREEN requires **0 RED**.

## Phase 6 — Browser C
At minimum:
1. period-sprint clarification + DMS option-click -> exact task collection;
2. person attachments WMB;
3. person text WMB;
4. current-sprint multi-filter;
5. identity ambiguity continuation;
6. aging DMS;
7. similar DMS-380;
8. task quality;
9. release/source-unavailable;
10. safe not-found.

No public payload may reveal `continuation_observations` or `continuation_required_skills`.

## Phase 7 — local-store/source audit
During entire run:
- factual V4 paths must have 0 reliance on `/api/v1/tasks`;
- release/source limitations fail closed;
- no local row may be presented as REAL AS21.

## Phase 8 — stability
Repeat high-risk successful paths with fresh sessions, concurrency 1:
- period-sprint continuation ×5 additional;
- person attachments ×5;
- person text ×5;
- current-sprint multi-filter ×5;
- exact attachments ×3;
- aging ×3.

Distinguish endpoint ReadTimeout from logic defects, but never hide failed runs.

## Phase 9 — plugin/extensibility
Re-run dummy-55 / A190 gate.
A synthetic new skill must still register and execute with **zero business-logic changes to Agent Core/planner/runtime**.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_GREEN`
- `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires:
- 27/27 existing skills tested;
- D-A200-1 closed;
- direct adversarial variant has no false completion;
- clarification framework retained across unrelated cases;
- 0 RED;
- exact factual parity for GREEN rows;
- source limitations fail closed;
- 0 local-store factual truth;
- Browser C supported paths GREEN;
- dummy-55 GREEN.

If any RED:
**STOP. No Wave S, no new skills. Return root cause for owner remediation and another full regression.**

If GREEN:
**Freeze A201 as the clean zero-RED pre-Wave-S checkpoint. Do not start Wave S automatically; wait for explicit owner/user instruction.**

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_FULL_EXISTING_CATALOG_REGRESSION_201.md`

## Service keepalive
Leave tested current-HEAD UI/backend/Task API/MCP running.
Return exact START_HEAD, report commit, verdict, GREEN/SOURCE_CONDITIONAL/RED counts, URLs/ports/PIDs/health.
Then stop.
