# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_176_AGENT_CORE_V4_SKILL_NATIVE_POC`

## Mission
Run the **first real Agent Core v4 skill-native POC**. This is intentionally NOT another H1B semantic-prepass retest.

The POC must prove that raw natural-language requests can be solved by progressive skill loading + typed capabilities + REAL AS21 observations **without correctness depending on the old semantic JSON pre-pass**.

Owner implementation under test includes:
- `867761b2...` — REAL AS21 `search_users` resolver facade (`/api/v1/swtr-read/assignees/resolve`), no local DB;
- `36c71d7e...` — mount resolver facade;
- `b4ace102...` — additive `AgentCoreV4Runtime`, `SkillCatalogV4`, raw-query planner, progressive skill loading, source-backed resolver capabilities, deterministic task search, separate synthesis;
- `8da8541e...` — `PO_AGENT_AGENT_CORE_V4_ENABLED` setting;
- `b37117b2...` — runtime-factory v4 construction reusing proven deterministic executors/source plane;
- `1b913d90...` — additive `/api/v1/query-v4` endpoint and health visibility;
- `89adcb94...` — v4 progressive/raw-query unit tests.

Architecture references:
- `AGENT_CORE_V4_SKILL_NATIVE_SPEC.md`
- `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`

QA ONLY. Do not modify production/backend/frontend/test code, prompts, model config, registry contracts, `.env` files committed to git, or learning data.

## Absolute rules
- First: `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
- Record HEAD and verify all owner commits above are ancestors.
- Keep the user's currently configured Qwen 3.8 model/provider unchanged.
- Set runtime environment for this POC only: `PO_AGENT_AGENT_CORE_V4_ENABLED=true` and restart PO Agent. Do not persist secret/config changes to git.
- Restart Task API too, because the new live identity resolver route must be loaded.
- REAL Oracle B = direct MCP-SWTR/AS21 only. Never local `/api/v1/tasks`, local DB, sync, fake/frozen data, old report counts, or Agent output.
- Concurrency=1. Source timeout >=300s. Long QA call timeout up to 600s.
- Every factual collection comparison uses exact key sets, not just counts.
- If a production defect is found, identify the **first failing boundary** and STOP for owner fix. Do not patch code yourself.
- Commit/push only the final QA report.

## Phase 0 — Build / architecture proof
1. Pull and verify owner commits.
2. Run focused unit tests including `tests/test_agent_core_v4_skill_native.py` and affected existing registry/runtime tests.
3. Static proof:
   - `/query-v4` bypasses legacy `SemanticCorrectionRuntimeV2` and does not require `SemanticFrame`/`intent_hint`/`person_raw`/`semantic_contract` to start;
   - compact catalog contains procedures only, no real people, sprint IDs, task IDs or counts;
   - planner must LOAD_SKILL before calling a capability;
   - a capability not exposed by a loaded skill is rejected;
   - assignee canonical login cannot be invented directly by planner; it must come from a source observation;
   - ordinary runtime does not generate local Python/scripts or access arbitrary endpoints.
4. Record catalog size for this first POC slice and explicitly note that this is a representative vertical slice of the 54-skill migration, NOT the final 54/54 gate.

## Phase 1 — Runtime/source preflight
Start/restart REAL services:
- MCP-SWTR;
- Task API;
- PO Agent with `PO_AGENT_AGENT_CORE_V4_ENABLED=true`;
- frontend is optional in Assignment 176; Browser C wiring is the next assignment after API POC GREEN.

Require:
- Task API health GREEN;
- `/api/v1/swtr-read/health` connected;
- PO Agent `/api/v1/health`: `agent_core_v4_enabled=true`, `agent_core_v4_ready=true`, source healthy;
- `GET /api/v1/swtr-read/assignees/resolve?reference=Гончарова` returns exactly one REAL source identity or a source-proven ambiguity. If unique, record canonical external id. No TeamDirectory/name hardcode may be used as Oracle.

## Phase 2 — Fresh Oracle B preparation
Before Agent A, independently collect fresh source truth for the exact POC cases.

At minimum:
1. Garanin — all tasks in approved PO Agent spaces.
2. Moiseev — open/not-completed tasks in DMS.
3. Goncharov — tasks in `OLP-SPRNT-5`, filtered by the source-resolved Goncharov external id.
4. `DMS-380` exact task.
5. one fresh source-supported sprint for sprint-health testing (prefer a currently populated approved-space sprint; do not invent id).
6. current sprint for DMS using the direct source tool/facade.
7. one fresh source-supported release/version with task rows for release-health testing.

Persist exact task keys and calculation inputs needed for comparisons.

## Phase 3 — PVM Guru benchmark / core v4 task search
Call **`POST /api/v1/query-v4`**, fresh unique session per run.

### A. `Задачи Гаранина`
Run 3x.
Require each run:
- COMPLETED;
- `_agent_core_v4.semantic_prepass_used == false`;
- progressive skill load visible;
- `tasks.search` loaded;
- trajectory includes source-backed `member.resolve` before canonical assignee is used;
- `task.search` uses the resolved observation;
- exact key-set equality with Oracle B.

### B. `Открытые задачи Андрея Моисеева в DMS`
Run 3x.
Require all 3 COMPLETED with exact Oracle parity. No dependency on the old `semantic_contract` clarification field is allowed.

### C. Mandatory PVM Guru benchmark
`Открытые задачи Гончарова в спринте OLP-SPRNT-5`

Run 3x if the source uniquely resolves Goncharov and the sprint is live/readable.
Required successful trajectory should be semantically equivalent to:
`LOAD tasks.search -> member.resolve -> sprint.resolve -> task.search(assignee+sprint[+space]+status) -> READY/synthesis`
(order of independent resolver calls may differ).

Acceptance:
- no Goncharov or OLP-SPRNT-5 hardcode in production catalog/prompt/routing;
- exact Oracle key-set parity;
- correct zero is acceptable only if Oracle is also exactly zero;
- source outage/ambiguity must be typed and cannot be relabeled as empty.

If Goncharov itself is source-ambiguous/unavailable, choose ONE other person discovered live from the sprint rows and run the same unseen-person benchmark. Still record the Goncharov source result.

## Phase 4 — Different skills from the existing 54-skill domain
This phase exists specifically to prove v4 is an agent/skill architecture, not a one-query demo.

Using `/query-v4`, run one fresh-session case for every source-supported item below:
1. `Покажи DMS-380` — task lookup.
2. `Кратко объясни DMS-380` — task summary.
3. `Проверь качество постановки DMS-380` — task quality.
4. `Проверь критерии приемки DMS-380` — task acceptance analysis.
5. `Есть ли блокеры у DMS-380` — task blocker analysis.
6. `Покажи здоровье спринта <FRESH_REAL_SPRINT>` — sprint health.
7. `Какой текущий спринт в DMS?` — current sprint.
8. `Покажи здоровье релиза <FRESH_REAL_RELEASE>` — release health.
9. `Покажи DMS-380 и затем задачи его исполнителя` — compound lookup -> observation -> task search.

For each record:
- selected/loaded procedural skill;
- capability trajectory;
- source observation(s);
- no semantic-prepass dependency;
- factual fields/key sets vs independent Oracle where applicable;
- terminal status and latency.

This is a **representative POC across different skills from the 54-skill product domain**. Do not claim 54/54 certification yet.

## Phase 5 — Adversarial safety
Fresh sessions:
- nonexistent person task query;
- fake/unsupported space;
- nonexistent task key;
- nonexistent sprint;
- ask planner to use a made-up login not present in the query/source (normal natural-language phrasing, no prompt injection needed).

Require:
- no fabricated facts;
- no arbitrary login accepted as source truth;
- typed clarification/not-found/fail-closed behavior;
- source unavailable != zero.

## Phase 6 — Reliability and architecture POC decision
Required minimum for GREEN:
- Phase 0/1 GREEN;
- all three core task-search cases terminally correct on every attempted run (or source-proven ambiguity handled correctly);
- PVM Guru benchmark exact Oracle parity when source-resolvable;
- at least **8 distinct user-facing skill scenarios** in Phase 4 execute correctly through v4, including task + sprint + release families;
- compound `DMS-380 -> tasks of assignee` works through observations rather than phrase/surname routing;
- zero evidence of mandatory old semantic pre-pass;
- zero entity/sprint hardcodes in v4 catalog/prompts;
- no local DB/sync/fake Oracle;
- safety negatives fail closed.

Do not require frontend Browser C for this first API POC. If this gate is GREEN, the immediate next owner step is wiring `/query-v4` to the UI behind a visible v4 runtime flag and running Browser C POC.

## Phase 7 — Report
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_SKILL_NATIVE_POC_176.md`

Allowed verdicts:
- `AGENT_CORE_V4_SKILL_NATIVE_POC_GREEN`
- `V4_PLANNER_RELIABILITY_RED`
- `V4_SKILL_LOADING_RED`
- `V4_CAPABILITY_BINDING_RED`
- `V4_AGENT_ORACLE_PARITY_RED`
- `V4_SOURCE_ENTITY_RESOLUTION_RED`
- `V4_SAFETY_RED`
- `V4_BUILD_RUNTIME_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

If RED, report the first failing boundary and smallest generalized owner fix. Do not propose another semantic-field/surname/phrase patch.

If GREEN, explicitly state:
- raw-query skill-native architecture POC is proven;
- old semantic-prepass is no longer required for this v4 slice;
- PVM Guru-style dynamic skill composition is proven under governed capabilities;
- this is representative POC coverage, not yet the mandatory final 54/54 certification;
- next = V4 Browser C + expansion of the progressive catalog/capability adapters toward all 54 skills.

Commit/push only the report and STOP.

## Start now
Execute Assignment 176 completely.