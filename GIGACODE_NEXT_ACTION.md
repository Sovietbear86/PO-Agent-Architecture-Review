# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_172_H1B_IDENTITY_SOURCE_RECOVERY_RETEST`

## Mission
Certify the owner fix for the exact production boundary proven by Assignment 171: `ProductionEntityResolverV2._infer_missing_person_from_query()` was correct, but its `assignee_identities` pool was empty because production task-api bulk `/api/v1/tasks` returns no rows. Identity recovery must now seed candidate identities from the configured TeamDirectory and only then enrich from any live task rows.

Assignment 171 accepted evidence — DO NOT re-run its full forensic:
- Garanin gate = 4/10; all 6 failures were `llm_used=False` + empty semantic frame + `UNRESOLVED_CONSTRAINT`;
- successful LLM runs had exact Oracle parity;
- REAL assignee route/source was healthy;
- first failing boundary was empty `assignee_identities` from the bulk task scan, not AS21 outage and not H1B loop loss.

QA ONLY. Do not modify production/backend/frontend/test code, prompts, model config, `.env`, registry contracts or learning data.

## Required owner commits
Both MUST be ancestors before testing:
- `3e26bace1f578e62683749708628aa40ccf35b53` — seed `assignee_identities` from TeamDirectory before enriching with live task rows; no hardcoded names and no capability routing.
- `c4f2d57381672284da90bdd50b9abf27af3d8e90` — regression test proving recovery works with an empty bulk task scan and populated TeamDirectory.

## Absolute rules
- Oracle B = fresh direct REAL AS21/MCP-SWTR only. Never use `/api/v1/tasks`, local DB, sync, fake/frozen/surrogate data as Oracle truth.
- Qwen 3.8/current endpoint unchanged.
- Concurrency=1.
- Source timeout=300s; end-to-end QA timeout may be 600s.
- Exact task-key-set equality mandatory for every collection.
- No hardcoded surname→login mappings; no regex/keyword capability routing.
- Identity recovery may bind only exactly one configured/source-backed identity. Zero or >1 matches must fail closed/clarify.
- Commit/push only the final QA report.

## Phase 0 — preflight
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
2. Print HEAD + git status + this Status.
3. Verify both owner commits are ancestors.
4. Restart/reuse REAL MCP-SWTR + Task API + PO Agent v3 + frontend so new code is loaded.
5. `/health`: v3=true, semantic LLM healthy, REAL source healthy, frontend reachable.
6. Static proof:
   - `semantic_context()` seeds identity candidates from `context["team_members"]` even if `adapter.search_tasks("")` returns [];
   - task-derived identities only enrich that pool;
   - resolver still never chooses intent/capability;
   - only exactly one identity is accepted.

If environment unhealthy, STOP `BLOCKED_BY_PROVEN_ENVIRONMENT`.

## Phase 1 — unit/build gate
Run H1/H1B unit suites including `test_production_entity_grounding_recovery.py`; all PASS.
Run frontend typecheck/build required by project; PASS.
Specifically prove the new non-mocked resolver test uses an adapter whose bulk `search_tasks("")` returns [] while TeamDirectory remains populated.

## Phase 2 — primary recovery gate: Garanin 10/10
Fresh Oracle B for Garanin across approved spaces, exact keys.
Run exactly TEN fresh-session requests:
`Задачи Гаранина`

Every run MUST:
- COMPLETED;
- exact task-key set == same-window Oracle B;
- canonical assignee == authoritative Garanin login;
- if `llm_used=False` / semantic frame empty, TeamDirectory-backed recovery still supplies person/login;
- raw Russian name never sent as canonical AS21 identifier;
- no `UNRESOLVED_CONSTRAINT` solely from semantic entity omission.

Acceptance = 10/10. If not, STOP `H1B_IDENTITY_SOURCE_RECOVERY_RED`.
Record latency, llm_used, raw slots, recovery-used, member_login, final assignee, key parity.

## Phase 3 — cross-member gate
Fresh Oracle B and fresh sessions:
- 5× `Задачи Семавина`
- 5× `Задачи Калачанова`

Require 10/10 COMPLETED + exact Oracle parity. Any LLM omission must be recovered from TeamDirectory under the same unique-only rule.

## Phase 4 — identity safety
Verify:
1. nonexistent person -> no auto-bind;
2. ambiguous identity -> no auto-bind;
3. existing valid LLM person slot is not overwritten;
4. non-task text mentioning a team member does not acquire a task capability because grounding recognized a person.

## Phase 5 — protected H1B regression
Fresh Oracle B and Agent A:
- 3× `Проверь DMS-380 и затем покажи задачи его исполнителя`
- `Задачи Гаранина в DMS`
- `Задачи Калачанова в WMB`
- `Покажи DMS-380`
- `Найди задачи Гаранина в DMS и затем покажи подробности DMS-380`

Require COMPLETED, exact parity, real typed CALL/FINAL loop for compound cases, no heuristic single-shot regression.

## Phase 6 — Browser C H0
Run `npm run e2e:h0`; require 5/5 PASS.

## Phase 7 — Browser C real multi-step
Fresh Playwright Chromium conversation:
`Проверь DMS-380 и затем покажи задачи его исполнителя`

Persist screenshot, browser session id, correlated backend trace, loop steps and fresh Oracle exact parity. Require Browser C == Agent A == Oracle B.

## Phase 8 — report
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_IDENTITY_SOURCE_RECOVERY_172.md`

Allowed verdicts:
- `AGENT_CORE_V3_H1B_LOOP_GREEN`
- `H1B_IDENTITY_SOURCE_RECOVERY_RED`
- `H1B_IDENTITY_AMBIGUITY_SAFETY_RED`
- `H1B_AGENT_ORACLE_PARITY_RED`
- `H1B_MULTI_STEP_REGRESSION_RED`
- `H1B_BROWSER_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires all phases 0–7. If GREEN, explicitly state H1B is CLOSED and next stage is H1C Progressive Skill Loading.

Commit/push only the final QA report and STOP.
