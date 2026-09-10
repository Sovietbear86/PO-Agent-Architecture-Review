# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_173_H1B_CANONICAL_GROUNDED_LITERAL_CERTIFICATION`

## Mission
Certify the owner fix for the final exposed H1B identity boundary from Assignment 172.

Assignment 172 proved two important facts:
1. The previous identity-source defect is CLOSED: TeamDirectory now seeds production `assignee_identities`, and empty semantic frames can recover `person_raw`, `member_login`, and `assignee` from source/config-backed team identities.
2. The remaining RED is downstream: when Qwen copies the already-grounded canonical login literally into a typed CALL (for example `assignee="Garanin.R.V"`) instead of emitting `$ground.assignee`, H1B rejected that value even though it is exactly equal to the authoritative grounded value.

The owner fix under test makes literal validation symmetric: a planner literal is source-safe if and only if it exactly equals the corresponding authoritative grounded value. This is validation only — no fuzzy inference, no surname→login mapping, no capability routing.

QA ONLY. Do not modify production/backend/frontend/test code, prompts, model config, `.env`, registry contracts, or runtime learning data.

## Required owner commits
Both MUST be ancestors before testing:
- `b95cd24ecc777342bd514a9dae5d47ca8e2be7bf` — H1B accepts planner literals that exactly equal authoritative grounded values; assignee accepts exact grounded `assignee`/`member_login`.
- `5c4473f90ca6aa21ddcf168309ef81cfc097ae6b` — regression tests for canonical grounded literal acceptance and rejection of fuzzy/wrong-field literals.

Accepted evidence — DO NOT repeat long historical forensics:
- Assignment 172 closed the empty identity-pool defect.
- Assignment 169 already proved compact multi-step Challenge A can reach 5/5 when identity/constraint safety passes.
- Typed CALL/FINAL protocol, compact observations, no `response_format`, and token budget fix are already accepted.
- REAL AS21/MCP-SWTR is the only Oracle B.

## Absolute rules
- Oracle B = fresh direct REAL AS21/MCP-SWTR only. Never `/api/v1/tasks`, local DB, sync, fake, frozen, cached surrogate, or report counts.
- Keep Qwen 3.8 and the current endpoint unchanged.
- Concurrency=1.
- Source timeout=300s. End-to-end QA timeout may be 600s.
- Only a proven source outage gets exactly 2 retries with 30s backoff.
- Exact task-key-set equality is mandatory for every collection result.
- No hardcoded surname/login mappings.
- No regex/keyword-to-capability routing.
- A planner literal may be accepted as grounded only when it exactly equals the authoritative grounded value for that field. Partial/fuzzy matches remain unsafe.
- Existing `$ground.*` and `$obs.*` references must continue to work.
- Commit/push only the final QA report.

## Phase 0 — pull / provenance / healthy runtime
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
2. Print HEAD, git status, and this Status line.
3. Verify both required owner commits are ancestors.
4. Restart/reuse REAL MCP-SWTR + Task API + PO Agent v3 + frontend so the new code is loaded.
5. `/health` must show v3=true, semantic LLM healthy, REAL source healthy; frontend reachable.
6. Static proof from loaded `agent_core_v3_h1b.py`:
   - `_literal_matches_grounded()` exists;
   - matching is exact/case-insensitive equality only;
   - it does not perform entity inference or capability routing;
   - `assignee` may match grounded `assignee` or `member_login`;
   - non-assignee fields may match only their same-name grounded field;
   - fuzzy partial names are not accepted.

If runtime/source is unhealthy, STOP with a proven environment/source verdict before expensive tests.

## Phase 1 — unit / build / safety gate
Run the focused H1/H1B suites including:
- `tests/test_agent_core_v3_h1b_grounding.py`
- `tests/test_production_entity_grounding_recovery.py`
- typed planner / loop / registry / foundation tests used by Assignment 172.

Require all PASS. Run frontend typecheck/build required by the project; require PASS.

Static safety checks must prove no new literal mappings for known users and no capability-selection logic was added to grounding/guard code.

## Phase 2 — primary recovery reliability gate: Garanin 10/10
Fetch fresh Oracle B for Garanin from REAL AS21 approved spaces and record exact current task keys.

Run exactly TEN fresh-session requests, concurrency=1:
`Задачи Гаранина`

Acceptance for EVERY run:
- COMPLETED;
- canonical assignee sent to Task API/AS21 is the source-backed login;
- exact task-key set equals same-window Oracle B;
- `llm_used=True` path remains correct;
- `llm_used=False`/empty semantic-frame path still recovers identity from TeamDirectory/source context;
- if planner emits `$ground.assignee` or `$ground.member_login`, it works;
- if planner instead copies the canonical grounded login literally, it is accepted only because it exactly equals the grounded value;
- raw Cyrillic display name is never sent as the source identifier;
- no `UNRESOLVED_CONSTRAINT` solely because the planner chose literal-vs-reference syntax.

Record per run: latency, llm_used, raw semantic slots, grounded `person_raw/member_login/assignee`, planner raw constraint form (reference vs literal), final canonical assignee, status, exact parity.

Acceptance = **10/10**. Any failure caused by this literal/reference asymmetry => STOP `H1B_GROUNDED_LITERAL_RED`.

## Phase 3 — cross-member 10/10
Fresh Oracle B and fresh sessions:
- 5× `Задачи Семавина`
- 5× `Задачи Калачанова`

All 10 must COMPLETED with exact Oracle parity and canonical source-backed identity regardless of whether the semantic pre-pass returned the person or fallback recovery supplied it.

## Phase 4 — literal safety negatives
Prove all of the following:
1. Partial/fuzzy `Garanin` is NOT accepted merely because grounded login is `Garanin.R.V`.
2. An invented login-like literal not present in the query and not equal to any grounded value is rejected.
3. A grounded value from the wrong field cannot authorize another field (for example grounded `member_login` must not authorize `space=Garanin.R.V`).
4. `$ground.*` valid reference path still works.
5. `$obs.*` observation-derived path still works.
6. Ambiguous/nonexistent identity remains fail-closed/clarify.

No fabricated execution is acceptable.

## Phase 5 — protected H1B regression
Using fresh Oracle B where applicable, run:
- 3× `Проверь DMS-380 и затем покажи задачи его исполнителя`
- `Задачи Гаранина в DMS`
- `Задачи Калачанова в WMB`
- `Покажи DMS-380`
- `Найди задачи Гаранина в DMS и затем покажи подробности DMS-380`

Require:
- all COMPLETED;
- exact collection parity;
- real typed multi-step loop for compound cases;
- observation-derived/source-grounded constraints preserved;
- no heuristic single-shot routing regression.

## Phase 6 — Browser C H0 regression
Run existing:
`npm run e2e:h0`

Require **5/5 PASS**.

## Phase 7 — Browser C real multi-step
In fresh Playwright Chromium conversation run:
`Проверь DMS-380 и затем покажи задачи его исполнителя`

Persist screenshot, browser session id, correlated backend trace, loop steps, rendered answer, and fresh Oracle exact parity.
Require Browser C == Agent A == Oracle B.

## Phase 8 — H1B closure decision
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_CANONICAL_GROUNDED_LITERAL_173.md`

Allowed verdicts ONLY:
- `AGENT_CORE_V3_H1B_LOOP_GREEN`
- `H1B_GROUNDED_LITERAL_RED`
- `H1B_IDENTITY_RECOVERY_RED`
- `H1B_AGENT_ORACLE_PARITY_RED`
- `H1B_MULTI_STEP_REGRESSION_RED`
- `H1B_BROWSER_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires ALL phases 0–7. If GREEN, explicitly state:
- H1B Agent Loop is CLOSED/certified;
- next architecture stage is H1C Progressive Skill Loading;
- no further H1B prompt/identity patching is required unless a future regression reproduces with evidence.

Commit/push only the final QA report and STOP.

## Start now
Execute Assignment 173 completely. Pull first, verify owner commits, load fresh runtime, then run the 10/10 primary gate before any expensive browser work.
