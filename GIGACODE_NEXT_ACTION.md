# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_169_H1B_COMPACT_REPLAN_GROUNDING_RECOVERY`

## Mission
Certify the focused owner fixes for the three defects proven by Assignment 168 after the token-budget gate itself became GREEN:
1. multi-step Challenge A planner instability caused by feeding multi-KB executor payloads back into the LLM planner;
2. space-less person grounding gap (`Задачи Гаранина`);
3. stale Browser C assertion path for semantic LLM usage metadata.

Accepted evidence from Assignment 168 (DO NOT re-prove unless needed for parity):
- Phase 2 token-budget target is GREEN 10/10;
- `max_tokens=1600` is sufficient for protected single-step FINAL generation;
- REAL AS21 source was healthy;
- typed CALL/FINAL protocol remains valid;
- Challenge B already completed successfully once;
- Browser C failure included a stale `llm_used` assertion path plus the same grounding defect seen in API testing.

QA ONLY. Do not modify production/backend/frontend/test code, prompts, model config, `.env`, registry contracts or runtime learning data.

## Required owner commits
All MUST be ancestors before testing:
- `266aac3cba5b94cc5956ba8d0eac31e1ce3801b7` — compact authoritative observation projection for planner re-planning; descriptions/source_data are excluded from planner prompt while remaining in executor/evidence response state.
- `fed7aeb0fcde1ae08982fd6033db57defe56fb34` — model literals identical to authoritative observation facts are rebound to `$obs` references (for example source-backed project_space/assignee) instead of being treated as invented literals.
- `0f1d08656c5d9766c8d4f15601fc3430a01d4a1f` — unique source/team-backed person grounding no longer requires an explicit space filter.
- `645f81a7a99976cc7fb8bcc240f2bb1292d50956` — H0 Browser assertion accepts the current v3 semantic metadata schema (`llm_used` direct or under `semantic_prepass`).

## Absolute rules
- Oracle B = fresh direct REAL AS21/MCP-SWTR only. No local DB/sync/fake/frozen/surrogate truth.
- Keep target model Qwen 3.8 and current endpoint.
- Concurrency=1.
- Source timeout remains 300s. Test-harness end-to-end timeout may be 600s.
- Only proven source outage gets exactly 2 retries with 30s backoff.
- Exact task-key-set equality mandatory for collections.
- No caveat GREEN.
- Commit/push only the final QA report.

## Phase 0 — pull / preflight
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
2. Print HEAD, git status and this Status line.
3. Verify all four owner commits above are ancestors.
4. Restart/reuse REAL MCP-SWTR + Task API + PO Agent v3 + frontend so new code is loaded.
5. `/health` must prove v3=true, semantic LLM healthy, REAL source healthy; frontend reachable.
6. Static proof from loaded code:
   - planner prompt observations are compact and exclude full `description` and `source_data`;
   - task lookup compact observation still preserves `key`, `assignee_login`, `project_space`, status/title and other routing facts needed by `$obs`;
   - literal observation binding does not invent values: it rewrites only exact values already present in authoritative observation data;
   - person fallback is only entity grounding for an already selected task-search intent and succeeds only on exactly one source-backed identity match;
   - Browser H0 assertion checks current semantic metadata schema rather than requiring a stale top-level field.

If environment unhealthy, STOP `BLOCKED_BY_PROVEN_ENVIRONMENT` before expensive tests.

## Phase 1 — unit/build safety gate
Run existing H1/H1B unit suites including typed planner and grounding tests. Require all PASS.
Run frontend build/typecheck required by the project. Require PASS.
Do not add or edit tests.

Static safety must prove:
- no regex/keyword routing from specific DMS-380/Garanin phrases to capabilities;
- full authoritative executor result is not deleted or truncated from response/evidence merely because planner receives compact projection;
- `$obs.1.task.assignee_login` and `$obs.1.task.project_space` paths remain resolvable;
- ambiguous person matches still fail closed/clarify.

## Phase 2 — Challenge A reliability gate (5/5 STOPPING GATE)
Fresh Oracle B first for DMS-380 executor and that executor's current exact task-key set.
Then run exactly FIVE fresh-session requests, concurrency=1:
`Проверь DMS-380 и затем покажи задачи его исполнителя`

Every run MUST:
- COMPLETED;
- architecture_stage=H1B_AGENT_LOOP;
- typed CALL `task-lookup-v3` for DMS-380;
- authoritative observation contains real assignee and project_space;
- second typed CALL `task-search-v3` uses source-backed assignee from observation;
- if planner proposes a literal equal to an observation fact (e.g. DMS), trace must prove it was rebound to an authoritative `$obs` value before source execution;
- 2–4 capability calls only;
- all postconditions PASS;
- exact final task-key set == same-window fresh Oracle B;
- no invalid_json/no_typed_branch/UNRESOLVED_CONSTRAINT caused by the DMS-380 observation;
- planner prompt/evidence demonstrates the ~6KB description was NOT sent back as planning context.

Acceptance = 5/5. If any non-source planner/constraint failure occurs, STOP `H1B_COMPACT_REPLAN_RELIABILITY_RED`.

Record per run latency and planner attempt counts, but latency is observational here, not yet a GREEN gate.

## Phase 3 — space-less person grounding gate (5/5)
Fresh Oracle B for Garanin across approved spaces, exact current task keys.
Run exactly FIVE fresh-session requests:
`Задачи Гаранина`

Every run MUST:
- COMPLETED;
- semantic interpreter remains LLM-used;
- person identity grounds uniquely to authoritative Garanin login without requiring DMS/OLP/etc in the query;
- no hardcoded surname/login mapping;
- exact task-key set == fresh Oracle B;
- raw Russian name is never sent to AS21 as canonical assignee identifier.

Acceptance = 5/5. Any grounding miss/ambiguity for this known unique member => `H1B_SPACELESS_GROUNDING_RED`.

## Phase 4 — protected API regression
Fresh Oracle B and Agent A for:
1. `Задачи Гаранина в DMS`
2. `Задачи Калачанова в WMB`
3. `Покажи DMS-380`
4. Challenge B: `Найди задачи Гаранина в DMS и затем покажи подробности DMS-380`

Require COMPLETED and exact same-window Oracle parity. Challenge B must contain two typed capability calls and preserve both outcomes.

## Phase 5 — safety / unsupported behavior
Verify existing typed safety controls remain GREEN.
Specifically rerun:
`Проверь DMS-380 и затем покажи историю его статусов`

It must explicitly expose that status-history capability is unavailable. It must NOT silently pretend the full request was satisfied. Record whether current status is FAILED/NEEDS_CLARIFICATION/COMPLETED-with-explicit-unsupported; do not call silent partial success GREEN.

Also prove ambiguous/non-team person wording does not get auto-grounded merely through loose token matching.

## Phase 6 — Browser C H0 regression
Run existing:
`npm run e2e:h0`

Require **5/5 PASS**.
For all four v3 pilot queries prove:
- same browser/backend session correlation;
- COMPLETED;
- semantic LLM usage is present through the current metadata schema;
- no stale `meta.llm_used` path failure;
- `Задачи Гаранина` now succeeds through the real browser path.

## Phase 7 — Browser C real multi-step
Use real Playwright Chromium in a fresh conversation for Challenge A:
`Проверь DMS-380 и затем покажи задачи его исполнителя`

Persist screenshot, browser session id, correlated backend trace, loop steps, rendered answer and fresh Oracle exact parity.
Require Browser C result == Agent A == Oracle B.

## Phase 8 — report
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_COMPACT_REPLAN_GROUNDING_169.md`

Allowed verdicts ONLY:
- `AGENT_CORE_V3_H1B_LOOP_GREEN`
- `H1B_COMPACT_REPLAN_RELIABILITY_RED`
- `H1B_SPACELESS_GROUNDING_RED`
- `H1B_OBSERVATION_BINDING_RED`
- `H1B_AGENT_ORACLE_PARITY_RED`
- `H1B_TYPED_PROTOCOL_SAFETY_RED`
- `H1B_BROWSER_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires ALL phases including Challenge A 5/5, space-less grounding 5/5, H0 Browser 5/5 and Browser multi-step parity.

Commit/push only this QA report and STOP.

## Start now
Execute Assignment 169 completely. First pull, print HEAD + Status, verify the four owner commits, then healthy preflight before any expensive test.