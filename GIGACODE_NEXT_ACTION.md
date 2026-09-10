# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_174_H1B_FULL_COLLECTION_AND_UI_ROUTING_CERTIFICATION`

## Mission
Certify BOTH:
1. the owner fix for the full-collection defect exposed by Assignment 173 (`max_results=50` silent truncation), and
2. the newly observed Browser/UI routing inconsistency where semantically equivalent task queries can take different runtime paths (H1B vs legacy/composite vs early fail) depending on member/space wording.

Do NOT declare H1B closed merely because backend focused cases are green. The real UI must prove stable routing, stable grounding, and exact source parity for equivalent task-search requests.

Observed real UI anomalies that MUST be reproduced or disproved:
- `Открытые задачи Гаранина в DMS` -> H1B, correct-looking detailed result.
- `Открытые задачи Андрея Моисеева в OLAP` -> legacy/composite-looking `Составной поиск: найдено задач: 25` very quickly.
- `Открытые задачи Андрея Моисеева в DMS` -> early `FAILED` / `Не удалось безопасно интерпретировать запрос` in ~133 ms.
- UI also showed a stale-looking top runtime line `Agent Core v3 · ready · NEEDS_CLARIFICATION · 0 ms` while subsequent turns completed.

These behaviors are not acceptable as an unexamined selector seam. Equivalent task requests must not silently produce different truth semantics depending on surname or wording.

QA ONLY. Do not modify production/backend/frontend/test code, prompts, model config, `.env`, registry contracts or runtime learning data.

## Required owner commits
Both MUST be ancestors before testing:
- `700b4f0dcb930c1f16e269b791e4904bd0bdedee` — H1B task-search executor explicitly requests full collection window (`max_results=10000`).
- `9fe2992f87850564561e19b67a2d45dd79f528ec` — regression test proving H1B does not inherit adapter default 50.

## Absolute rules
- Oracle B = fresh direct REAL AS21/MCP-SWTR only. Never `/api/v1/tasks`, local DB, sync, fake, frozen, cached surrogate or old QA report counts.
- Keep Qwen 3.8 and current endpoint unchanged.
- Concurrency = 1.
- Source timeout = 300s; end-to-end QA timeout may be 600s for large collections.
- Proven source outage only: 2 retries with 30s backoff.
- Exact task-key-set equality is mandatory for every collection certification. Subset parity is FAIL.
- Do not accept a reported `count` unless it equals actual returned task-key count and fresh Oracle count.
- Record the ACTUAL selected runtime path for every UI/backend request: selector result, `skill_id`, `intent`, H1B vs legacy/composite, raw semantic frame, grounded values, accepted contract, actual source query/JQL/TQL, result count, exact keys.
- A semantically equivalent request must not silently change source semantics merely because the member name changes.
- `OLAP` must NOT be silently treated as an arbitrary space. If an explicit supported alias exists in code/config, prove it and show canonicalization to `OLP`; otherwise expected behavior is clarification/fail-closed, never fabricated data.
- Do not change production code if a defect is found; localize and STOP for owner fix.
- Commit/push only final QA report.

## Phase 0 — pull / provenance / healthy runtime
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
2. Print HEAD, git status, and this Status line.
3. Verify both required owner commits are ancestors.
4. Restart/reuse REAL MCP-SWTR + Task API + PO Agent v3 + frontend so new code is loaded.
5. `/health` must prove v3=true, semantic LLM healthy, REAL source healthy; frontend reachable.
6. Static proof from loaded production code:
   - H1B `_execute_search()` calls `adapter.search_tasks(..., max_results=10000)` (or equivalent named H1B constant =10000);
   - adapter global/default search limit remains 50;
   - no local DB/sync path introduced;
   - H1B `count` is derived from complete returned rows;
   - identify and print the current task selector / strangler routing logic that decides H1B vs legacy.

If environment/source unhealthy, STOP before expensive tests with proven blocker verdict.

## Phase 1 — focused unit/build gate
Run H1/H1B unit suites, including:
`tests/test_agent_core_v3_h1b_full_collection.py`

Also include previously accepted H1B grounding/planner/loop/registry tests needed to detect regressions. Require all PASS.
Run frontend typecheck/build required by project; require PASS.

## Phase 2 — large-collection Oracle B baseline
Fetch fresh REAL Oracle B via authoritative live assignee route for at least:
- `Kalachanov.V.V` across approved spaces;
- `Semavin.M.M` across approved spaces;
- `Garanin.R.V` across approved spaces;
- `Moiseev` / Андрей Моисеев: resolve source-backed canonical identity first, then fetch all approved-space tasks.

Record exact current counts and exact key sets. Do not reuse prior report counts.

At least one tested identity MUST have >50 tasks and one MUST have >300 tasks. If current source data no longer satisfies that, use another real configured team member and explain why.

## Phase 3 — H1B full-collection gate
Run fresh-session Agent A queries, concurrency=1:
- 3× `Задачи Калачанова`
- 3× `Задачи Гаранина`

For every run require:
- COMPLETED;
- canonical grounded assignee;
- H1B path when selected exposes `task-search-v3` executor metadata;
- exact task-key set == same-window Oracle B;
- returned row count == Oracle count;
- answer count == returned row count == Oracle count;
- no silent 50 cap;
- no duplicate task keys.

Any H1B run returning exactly 50 while Oracle >50 is immediate `H1B_COLLECTION_TRUNCATION_RED`.

## Phase 4 — cross-route fidelity / selector consistency
Run fresh sessions for ALL of the following, three times each where practical:
- `Задачи Семавина`
- `Открытые задачи Гаранина в DMS`
- `Открытые задачи Андрея Моисеева в DMS`
- `Открытые задачи Андрея Моисеева в OLP`
- `Открытые задачи Калачанова в WMB`

For every request capture:
- selected selector/path;
- `skill_id` and version;
- raw semantic intent/slots and `llm_used`;
- grounded member_login/person/space/status;
- accepted turn contract;
- actual source query/JQL/TQL sent downstream;
- status/latency;
- returned count and exact keys;
- fresh Oracle exact parity.

Acceptance:
- all source-backed cases must be truth-equivalent to Oracle B regardless of H1B/legacy path;
- same semantic class of query must not fail only because the member is Moiseev while Garanin succeeds;
- no path may report a different count/key set for the same canonical constraints;
- if selector coverage differs but facts remain exact, record seam explicitly as H1C migration debt;
- if routing difference changes result semantics, status behavior, source authority, or parity -> `H1B_ROUTE_FIDELITY_RED`.

## Phase 5 — explicit OLAP/OLP ambiguity gate
Run in fresh sessions:
- `Открытые задачи Андрея Моисеева в OLP`
- `Открытые задачи Андрея Моисеева в OLAP`

First inspect code/config for an explicit alias mapping `OLAP -> OLP`.

Acceptance:
- If explicit alias exists: `OLAP` must deterministically canonicalize to `OLP`, and both queries must have identical canonical constraints and exact Oracle key set.
- If no explicit alias exists: `OLAP` must produce clarification/fail-closed; it MUST NOT execute against an arbitrary project or return an unexplained task set.
- Silent `OLAP` interpretation without explicit alias evidence is FAIL: `H1B_SPACE_ALIAS_RED`.

## Phase 6 — multi-step high-cardinality regression
Fresh Oracle B for assignee of DMS-380 and full assignee collection.
Run 3× fresh-session:
`Проверь DMS-380 и затем покажи задачи его исполнителя`

Require each run:
- real typed 2-step loop: task lookup -> task search;
- step-2 assignee from authoritative observation/source-backed binding;
- full step-2 task-key set == fresh Oracle B (not first 50);
- count == full Oracle count;
- no duplicate keys;
- postconditions pass.

## Phase 7 — space-filter regression
Using fresh Oracle B, run:
- `Задачи Гаранина в DMS`
- `Задачи Калачанова в WMB`
- `Открытые задачи Андрея Моисеева в DMS`
- `Открытые задачи Андрея Моисеева в OLP`
- one real high-cardinality assignee + approved space where result remains >50, if such current source case exists.

Require exact same-window key-set parity, status filtering parity and constraint preservation. If no >50 per-space case exists, state that; do not invent one.

## Phase 8 — Browser C H0 + routing consistency regression
Run existing:
`npm run e2e:h0`
Require 5/5 PASS.

Then use REAL Playwright Chromium, fresh conversation/session per case, for:
1. `Открытые задачи Гаранина в DMS`
2. `Открытые задачи Андрея Моисеева в DMS`
3. `Открытые задачи Андрея Моисеева в OLP`
4. `Открытые задачи Андрея Моисеева в OLAP`
5. `Открытые задачи Семавина в DMS` or another approved space with live data
6. `Открытые задачи Калачанова в WMB`

Persist for each:
- screenshot;
- browser session id;
- correlated backend trace id;
- rendered runtime label (`Agent Core v3/H1B` vs other);
- backend `skill_id`, semantic frame, grounded constraints, selected path;
- actual downstream source query;
- rendered count;
- backend count;
- fresh Oracle count and exact key parity.

Acceptance:
- Browser C == Agent A == Oracle B for every valid supported query;
- no equivalent request may randomly use incompatible truth semantics;
- Moiseev/DMS must not early-fail if the same canonical identity+space can be grounded and queried through source;
- stale `NEEDS_CLARIFICATION · 0 ms` UI state must be investigated: prove whether it is harmless initial/stale presentation or a real session contamination signal. Capture exact request/response/session evidence.

If stale state corresponds to prior session/turn leakage, verdict `H1B_BROWSER_SESSION_STATE_RED`.
If it is presentation-only while request isolation is correct, record as frontend UX debt for later H6.

## Phase 9 — Browser C real full-collection multi-step
Fresh Playwright Chromium conversation:
`Проверь DMS-380 и затем покажи задачи его исполнителя`

Persist screenshot/artifacts, UI session id, correlated backend trace, loop steps and source evidence.
Require Browser C == Agent A == fresh Oracle B for COMPLETE step-2 collection and count.

If UI intentionally summarizes thousands of rows, backend exact full collection is still mandatory and UI must clearly distinguish displayed sample from total; it must never present a truncated sample count as total.

## Phase 10 — closure decision
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_FULL_COLLECTION_UI_ROUTING_174.md`

Allowed verdicts ONLY:
- `AGENT_CORE_V3_H1B_LOOP_GREEN`
- `H1B_COLLECTION_TRUNCATION_RED`
- `H1B_AGENT_ORACLE_PARITY_RED`
- `H1B_ROUTE_FIDELITY_RED`
- `H1B_SPACE_ALIAS_RED`
- `H1B_MULTI_STEP_REGRESSION_RED`
- `H1B_BROWSER_REGRESSION_RED`
- `H1B_BROWSER_SESSION_STATE_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires phases 0–9 all certified.

If GREEN, explicitly state:
- H1B Hermes Agent Loop is CLOSED/certified for task lookup/search slice;
- full collection parity is proven beyond the old 50-row cap;
- Browser C and backend use truth-equivalent semantics for tested team members/spaces;
- any remaining selector implementation seam is fidelity-safe and moves to H1C Progressive Skill Loading;
- next architecture stage = H1C Progressive Skill Loading.

If RED due routing/UI anomaly, identify FIRST FAILING BOUNDARY and exact file/function responsible. Do not patch it in QA.

Commit/push only final QA report and STOP.

## Start now
Execute Assignment 174 completely. Pull first, load fresh runtime, establish fresh Oracle baselines, prove full-collection parity, then explicitly reproduce/disprove the UI anomalies before any H1B closure verdict.