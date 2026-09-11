# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_178_AGENT_CORE_V4_RELIABILITY_CONTINUATION`

## Mission
Continue the V4 skill-native POC after the Assignment 177 source-wiring RED. Do **not** restart from the beginning and do **not** return to V3/H1B semantic-prepass work.

Assignment 177 proved the first failing boundary exactly:
`sprint.current -> ReliableAgentCoreV4Runtime._sprint_current_source_backed -> adapter.search_tasks(project=...) -> /api/v1/tasks -> local ~/.task-tracker/tasks.json`.
That path violated the REAL AS21 source contract.

Owner fix under test:
- `9fa53e90c53c42b407851aa20712748f21303d4f` — `sprint.current` now calls `adapter.get_current_sprint_id(product)`, which routes to `/api/v1/swtr-read/spaces/{space}/current-sprint` -> MCP-SWTR -> REAL AS21.
- `9b9a29299ed69f7a485f98df7a37299078980e22` — regression tests explicitly fail if `sprint.current` uses generic/local-cache `search_tasks` and require `get_current_sprint_id`.

QA ONLY. Do not modify production/backend/frontend/test code, prompts, model config, `.env`, registry or learning files.

## Absolute rules
- `git pull --ff-only origin feat/core8-real-query-hardening-v2` first.
- Verify both owner commits are ancestors of HEAD.
- Keep current Qwen 3.8/provider unchanged.
- Runtime env only: `PO_AGENT_AGENT_CORE_V4_ENABLED=true`.
- REAL AS21/MCP-SWTR is Oracle B. Never local DB, `/api/v1/tasks`, sync, fake/frozen or previous counts.
- Concurrency=1. Source timeout >=300s; long Agent A call <=600s.
- Exact task-key-set equality for factual collections.
- Fresh session per independent run.
- If a new production defect appears, capture FIRST FAILING BOUNDARY and STOP; do not patch it.
- Commit/push only the final QA report.

## Checkpoint reuse
Do NOT repeat the already certified static work from 177 except a short smoke verification.
Treat these as retained evidence:
- focused V4 tests were GREEN before the source-wiring discovery;
- production factory uses `ReliableAgentCoreV4Runtime`;
- `/query-v4` bypasses legacy semantic/correction runtime;
- `semantic_prepass_used=false`;
- no hardcoded person/sprint/task ids in V4 runtime.

Run only the focused tests necessary to certify the two new owner commits, then continue from the first previously blocked phase.

## Phase 0 — Focused owner-fix gate
1. Run `tests/test_agent_core_v4_reliable.py` and affected V4 runtime factory/API tests.
2. Prove statically/runtime that `sprint.current` calls `get_current_sprint_id(product)` and does not call `search_tasks`/`/api/v1/tasks`.
3. Direct Oracle B: resolve current DMS sprint via REAL MCP-SWTR.
4. Agent A: run `Какой текущий спринт в DMS?` 3x fresh sessions.
Require 3/3 exact equality to Oracle B and source trace through `swtr-read/current-sprint`.

Any local-cache access => `V4_SOURCE_ADAPTER_RED` and STOP.

## Phase 1 — Resume fresh Oracle B set
Collect fresh REAL source truth for:
- Garanin all tasks in approved spaces;
- Moiseev open/not-completed DMS tasks;
- `OLP-SPRNT-5` exact task set + assignee identities;
- contextual Goncharov/Goncharova match inside `OLP-SPRNT-5`;
- `DMS-380` exact task + assignee;
- current DMS sprint;
- one populated sprint for health;
- one populated release/version for health.
Persist exact task keys/canonical ids.

## Phase 2 — Critical identity/search gate
5x fresh sessions each:
1. `Задачи Гаранина`
2. `Открытые задачи Андрея Моисеева в DMS`
3. `Открытые задачи Гончарова в спринте OLP-SPRNT-5`

Requirements:
- terminally correct 5/5 per case;
- exact Oracle parity for task collections;
- progressive skill loading visible;
- person resolution source-backed;
- no surname/phrase hardcode;
- trusted observation binding only.

## Phase 3 — Current sprint full reliability gate
Run 5x fresh sessions:
`Какой текущий спринт в DMS?`
Require 5/5 exact Oracle parity and authoritative `swtr-read` path.

## Phase 4 — Generalization
Discover live source entities and run >=6 compound queries covering:
- a different configured team member;
- a person not required to exist in TeamDirectory but present in a sprint;
- person+space;
- person+sprint;
- full name vs surname;
- open/not-completed constraint.
No code/config changes between cases. Exact Oracle parity required.

## Phase 5 — Representative cross-skill POC
Run at least these 9 source-supported scenarios:
1. `Покажи DMS-380`
2. `Кратко объясни DMS-380`
3. `Проверь качество постановки DMS-380`
4. `Проверь критерии приемки DMS-380`
5. `Есть ли блокеры у DMS-380`
6. `Покажи здоровье спринта <FRESH_REAL_SPRINT>`
7. `Какой текущий спринт в DMS?`
8. `Покажи здоровье релиза <FRESH_REAL_RELEASE>`
9. `Покажи DMS-380 и затем задачи его исполнителя`

Capture loaded skill(s), typed trajectory, source observations, status, latency and Oracle comparison where factual.

## Phase 6 — Safety controls
Fresh sessions:
- nonexistent person;
- fake space;
- nonexistent sprint;
- nonexistent task key;
- invented login temptation;
- unrelated-person normalization;
- context ambiguity if live data permits.
Require fail-closed/no fabrication/source-unavailable != zero.

## Phase 7 — Decision gate
GREEN requires:
- focused source fix GREEN;
- Garanin 5/5 exact;
- Moiseev 5/5 exact;
- PVM Guru benchmark 5/5 terminally Oracle-correct;
- current sprint 5/5 exact;
- >=6 generalized compound cases GREEN;
- >=9 cross-skill cases terminally correct;
- lookup -> assignee -> tasks exact parity;
- semantic pre-pass absent;
- progressive skill loading visible;
- safety controls GREEN.

If GREEN: next owner step = Browser C/UI V4 wiring, then progressive expansion toward 54/54 A/B/C.
If RED: stop at first generalized production boundary and classify planner / skill loading / capability binding / identity / source adapter / Oracle parity / safety.

## Phase 8 — Report
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_RELIABILITY_POC_178.md`

Allowed verdicts:
- `AGENT_CORE_V4_RELIABILITY_POC_GREEN`
- `V4_PLANNER_RELIABILITY_RED`
- `V4_SKILL_LOADING_RED`
- `V4_CAPABILITY_BINDING_RED`
- `V4_CONTEXT_IDENTITY_RED`
- `V4_CURRENT_SPRINT_RED`
- `V4_AGENT_ORACLE_PARITY_RED`
- `V4_SOURCE_ADAPTER_RED`
- `V4_SAFETY_RED`
- `V4_BUILD_RUNTIME_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

Commit/push only the final report and STOP.

## Start now
Resume from the 177 checkpoint and execute Assignment 178 completely. Do not rerun unrelated completed static phases.