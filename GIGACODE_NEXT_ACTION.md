# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_171_H1B_IDENTITY_RECOVERY_CERTIFICATION`

## Mission
Certify the focused H1B owner fix derived from Assignment 170: when the semantic LLM pre-pass omits the person entity entirely, the grounding layer may recover exactly one uniquely source-backed team identity from the raw query without changing intent/capability routing.

Assignment 170 proved:
- `Задачи Гаранина` failed 8/10 because semantic pre-pass returned `llm_used=False`, empty intent and empty slots;
- when the LLM did return a person slot, the full chain was exact 24/24 Oracle parity;
- Garanin, Semavin and Kalachanov each resolve uniquely from REAL source-backed identity data;
- the blocker is entity omission, not AS21/source failure and not downstream grounding loss.

QA ONLY. Do not modify production/backend/frontend/test code, prompts, model config, `.env`, registry contracts or runtime learning data.

## Required owner commits
Both MUST be ancestors before testing:
- `429cf51316c03b7ebd913249b56fcb4bcd203e7b` — source-backed identity recovery no longer depends on a non-empty semantic intent; it annotates identity only and does not route capabilities.
- `9f3a7a30b61607249c8b68e57d7b863a7251c282` — regression tests for unique recovery with empty semantic frame, ambiguity fail-closed, and non-overwrite of an existing LLM person slot.

Accepted evidence (DO NOT re-prove with long marathons unless a required parity check says so):
- Challenge A compact multi-step replan was 5/5 GREEN in Assignment 169;
- typed CALL/FINAL protocol and compact observation projection are already accepted;
- Browser `llm_used` metadata assertion fix is accepted;
- REAL AS21/MCP-SWTR is the only Oracle B.

## Absolute rules
- Oracle B = fresh direct REAL AS21/MCP-SWTR only. No local DB/sync/fake/frozen/surrogate truth.
- Keep Qwen 3.8 and current endpoint.
- Concurrency=1.
- Source timeout = 300s. End-to-end QA timeout may be 600s.
- Only a proven source outage gets exactly 2 retries with 30s backoff.
- Exact task-key-set equality is mandatory for every collection.
- No hardcoded surname→login mappings.
- No regex/keyword-to-capability routing.
- Identity recovery may only bind a value if exactly ONE source/config-backed identity matches the user's wording.
- Zero or multiple identity matches must remain fail-closed/clarify.
- An existing successful LLM person slot must never be overwritten by fallback recovery.
- Commit/push only the final QA report.

## Phase 0 — pull / preflight
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
2. Print HEAD, git status and this Status line.
3. Verify both required owner commits are ancestors.
4. Restart/reuse REAL MCP-SWTR + Task API + PO Agent v3 + frontend so new code is loaded.
5. `/health` must prove v3=true, semantic LLM healthy, REAL source healthy; frontend reachable.
6. Static proof from loaded production code:
   - `_infer_missing_person_from_query` does NOT require a non-empty `intent_hint`;
   - it changes only entity slots, not intent/capability selection;
   - matching comes from `assignee_identities` built from source/config context, not hardcoded names;
   - only exactly one unique identity is accepted;
   - existing `person_raw`/`member_login` causes fallback to return without overwriting it.

If environment unhealthy, STOP `BLOCKED_BY_PROVEN_ENVIRONMENT` before expensive tests.

## Phase 1 — unit/build safety gate
Run H1/H1B unit suites including:
- typed planner tests;
- grounding tests;
- `test_production_entity_grounding_recovery.py`.

Require all PASS. Run frontend build/typecheck required by the project; require PASS.

Static safety must additionally prove:
- no new literal `Garanin.R.V`, `Semavin.M.M`, `Kalachanov.V.V` mappings in production code;
- no task capability selection was added to the entity resolver;
- ambiguous identity recovery remains fail-closed.

## Phase 2 — primary identity recovery gate: Garanin 10/10
Fresh Oracle B first for Garanin across approved spaces; record exact current task keys.
Then run exactly TEN fresh-session requests, concurrency=1:
`Задачи Гаранина`

Acceptance for EVERY run:
- COMPLETED;
- canonical assignee sent to Task API/AS21 is source-backed Garanin login, never raw `Гаранина`;
- exact task-key set == same-window fresh Oracle B;
- if semantic pre-pass returns a person slot, normal LLM grounding path remains intact;
- if semantic pre-pass returns empty intent/slots or `llm_used=False`, source-backed identity recovery still yields the same canonical login;
- no hardcoded identity facts;
- no `UNRESOLVED_CONSTRAINT` caused solely by LLM entity omission.

Acceptance = **10/10**. Any identity omission failure => STOP `H1B_IDENTITY_RECOVERY_RED`.

Record per run: latency, llm_used, raw intent, raw person slot, grounded member_login, recovery-used yes/no, final canonical assignee, exact parity.

## Phase 3 — cross-member recovery gate
Use fresh Oracle B and fresh sessions for:
- 5× `Задачи Семавина`
- 5× `Задачи Калачанова`

Each run must COMPLETED with exact Oracle parity and unique source-backed canonical identity.
The gate is 10/10 total.

If the LLM omits the entity in any run, fallback recovery must still succeed only through source-backed identity data.

## Phase 4 — ambiguity and negative safety
Prove all of the following without production changes:
1. A deliberately ambiguous surname/person query that can match >1 configured/source identity does NOT auto-bind a login.
2. A nonexistent person does NOT auto-bind a login.
3. A query where the LLM already returned a valid person slot preserves that slot; fallback does not overwrite it.
4. A non-task natural-language query mentioning a team member does not gain a task capability merely because the entity resolver annotated the person.

Allowed outcomes for 1/2/4: fail-closed, clarification, or unsupported — never fabricated execution.

## Phase 5 — protected H1B regression
Fresh Oracle B and Agent A for:
1. 3× Challenge A: `Проверь DMS-380 и затем покажи задачи его исполнителя`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`
5. Challenge B: `Найди задачи Гаранина в DMS и затем покажи подробности DMS-380`

Requirements:
- all COMPLETED;
- exact same-window Oracle parity for task collections;
- Challenge A/B show real typed multi-step loop and preserve observation-derived/source-backed facts;
- no regression to heuristic single-shot routing.

## Phase 6 — Browser C H0 regression
Run existing:
`npm run e2e:h0`

Require **5/5 PASS**.
The `Задачи Гаранина` and `Задачи Гаранина в DMS` browser cases must succeed even if semantic pre-pass omits the person entity on that run, because source-backed identity recovery is now responsible for reliability.

## Phase 7 — Browser C real multi-step
Use real Playwright Chromium in a fresh conversation:
`Проверь DMS-380 и затем покажи задачи его исполнителя`

Persist screenshot, browser session id, correlated backend trace, loop steps, rendered answer and fresh Oracle exact parity.
Require Browser C == Agent A == Oracle B.

## Phase 8 — final H1B decision
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_IDENTITY_RECOVERY_CERT_171.md`

Allowed verdicts ONLY:
- `AGENT_CORE_V3_H1B_LOOP_GREEN`
- `H1B_IDENTITY_RECOVERY_RED`
- `H1B_IDENTITY_AMBIGUITY_SAFETY_RED`
- `H1B_AGENT_ORACLE_PARITY_RED`
- `H1B_MULTI_STEP_REGRESSION_RED`
- `H1B_BROWSER_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires ALL phases 0–7, including Garanin 10/10, Semavin/Kalachanov 10/10, safety controls, protected regression, H0 Browser 5/5 and real Browser C multi-step parity.

If GREEN, explicitly state in the report that H1B is ready to close and the next planned architecture stage is H1C Progressive Skill Loading.

Commit/push only the final QA report and STOP.

## Start now
Execute Assignment 171 completely. First pull, print HEAD + Status, verify both owner commits, then healthy preflight before any expensive test.