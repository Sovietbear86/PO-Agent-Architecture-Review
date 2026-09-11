# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_177_AGENT_CORE_V4_RELIABILITY_POC_RETEST`

## Mission
Continue the Agent Core v4 skill-native POC after generalized owner fixes. Do **not** return to H1B/V3 semantic-prepass patching.

Assignment 176 proved the skill-native architecture itself is viable, but exposed several narrow runtime seams: global person ambiguity, brittle observation binding, morphology-normalized references, and `sprint.current` source wiring. The fixes below address those seams without surname rules, phrase routers, semantic JSON gates, or entity-fact hardcodes.

Owner commits under test:
- `de75115dafc04134a7c7eb8d48f946e71b07885b` — V4 reliability overlay: team-scoped source validation, trusted-observation literal binding, source-backed current sprint;
- `a8b8d6321673911e55c53b097be44c3c68b9d637` — wire `ReliableAgentCoreV4Runtime` in production V4 runtime factory;
- `57e9bcd5a5cbe96ec9eecd3d494096773a5885f2` — focused reliability tests;
- `9241f4e18d3dc9cfa328fcb92a9ff73bf585afcb` — contextual identity resolution inside authoritative sprint/task context for globally ambiguous people;
- `0a934d9d63917de7746a9f7e2c7042d0e3c073a2` — corrected fixtures + contextual identity regression test.

Architecture intent:
`raw user query -> progressive skill load -> typed capability CALL -> REAL AS21 observation -> re-plan -> validated FINAL`

Semantic pre-pass is not an execution prerequisite. TeamDirectory may narrow/disambiguate, but REAL AS21 remains identity truth. When a global name is ambiguous and the user supplies a sprint, the agent may resolve that person from authoritative assignee identities actually present in that sprint. Canonical values repeated by the LLM may be reused only if they exactly match a prior trusted observation.

QA ONLY. Do not modify production/backend/frontend/test code, prompts, `.env`, model config, skill registry, `GIGACODE.md`, or learning data.

## Absolute rules
- First: `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
- Record HEAD/status and verify all five owner commits above are ancestors.
- Keep current Qwen 3.8/provider unchanged.
- Runtime env only: `PO_AGENT_AGENT_CORE_V4_ENABLED=true`.
- Restart MCP-SWTR, Task API, and PO Agent so the new runtime is definitely loaded.
- Oracle B = fresh direct REAL MCP-SWTR/AS21 only. Never `/api/v1/tasks`, local DB, sync, fake/frozen data, prior QA counts, or Agent A output.
- Concurrency=1. Source timeout >=300s; whole agent/E2E call may use 600s.
- Collections require exact task-key-set equality, not counts only.
- Fresh session per independent run.
- If a production defect appears, locate FIRST FAILING BOUNDARY and STOP for owner fix. Do not patch it yourself.
- Commit/push only the final QA report.

## Phase 0 — Build/static architecture gate
1. Pull and verify provenance.
2. Run at minimum:
   - `tests/test_agent_core_v4_skill_native.py`
   - `tests/test_agent_core_v4_reliable.py`
   - affected runtime factory/API tests.
3. Require all focused tests PASS.
4. Prove statically/runtime:
   - production V4 instantiates `ReliableAgentCoreV4Runtime`;
   - `/query-v4` bypasses legacy semantic/correction runtime;
   - `_agent_core_v4.semantic_prepass_used == false`;
   - `member.resolve` exposes optional sprint/space context only after progressive skill load;
   - arbitrary assignee literals remain rejected unless exactly present in prior trusted observation values;
   - no person name, sprint id, task id or count is embedded in production V4 catalog/prompt/routing;
   - ordinary V4 execution remains read-only and does not generate local scripts.

STOP `V4_BUILD_RUNTIME_RED` on any import/test/runtime-construction failure.

## Phase 1 — Fresh REAL Oracle B
Before Agent A, independently collect live source truth for:
1. Garanin — all tasks in approved PO Agent spaces.
2. Moiseev — open/not-completed tasks in DMS.
3. `OLP-SPRNT-5` — exact sprint task set and canonical assignee identity fields present in those rows.
4. Goncharov/Goncharova natural reference:
   - record global `search_users` result;
   - independently inspect assignees actually present in `OLP-SPRNT-5`;
   - if exactly one sprint assignee matches, record that as contextual Oracle identity;
   - if none match, contextual Oracle result is zero; do not manufacture a global identity;
   - if >1 match in the sprint itself, ambiguity remains real.
5. `DMS-380` exact task and canonical assignee.
6. current DMS sprint from fresh source rows.
7. one populated source-supported sprint for health.
8. one populated source-supported release/version for health.

Persist exact task keys and canonical ids used in comparisons.

## Phase 2 — Critical identity/search reliability gate
Use `/api/v1/query-v4`.

### A — Garanin
Run 5x fresh sessions:
`Задачи Гаранина`

Require 5/5 COMPLETED + exact Oracle key-set parity.

### B — Moiseev morphology + observation binding
Run 5x fresh sessions, using at least two natural variants including:
- `Открытые задачи Андрея Моисеева в DMS`
- nominative/alternative natural full-name wording.

Require 5/5 COMPLETED + exact Oracle parity.
For each run capture member.resolve observation and task.search assignee binding.

Accepted binding only:
- `$obs.N.member_login` / equivalent trusted observation reference, OR
- literal canonical login that exactly equals a value already returned in a trusted REAL AS21 observation.

Any invented/different login => RED.

### C — Mandatory PVM Guru benchmark
Run 5x fresh sessions:
`Открытые задачи Гончарова в спринте OLP-SPRNT-5`

Desired trajectory is semantically equivalent to:
`LOAD tasks.search -> validate sprint/context -> contextual/global member.resolve -> task.search(person+sprint+open) -> READY`

Order of independent resolution may differ, but every user constraint must survive.

Acceptance follows current source truth:
- if exactly one matching assignee exists inside the sprint, V4 must resolve that canonical identity from authoritative sprint rows even if global `search_users` is ambiguous;
- if no matching assignee exists in that sprint, exact zero is correct only if derived from the authoritative sprint context;
- if >1 matching assignees remain inside the sprint context, typed clarification is correct;
- global ambiguity alone must not force failure when the sprint context uniquely disambiguates;
- exact returned open-task key set must equal Oracle B;
- no Goncharov/OLP-SPRNT-5 hardcode.

Require 5/5 terminally Oracle-correct outcomes under the live state.

If A, B, or C fails for a production reason, STOP RED and identify the first failing boundary.

## Phase 3 — Current sprint regression
Run 5x:
`Какой текущий спринт в DMS?`

Require 5/5 exact equality with fresh Oracle B.
Confirm V4 uses the full source collection (`project = "DMS"`, non-truncated) and not the legacy default/small scan.

## Phase 4 — Generalization beyond named benchmark
Prove this is not tuned to Garanin/Moiseev/Goncharov.

Discover live from AS21:
- one different configured team member;
- one person present in a sprint who need not be in TeamDirectory;
- one different approved-space sprint.

Run at least 6 compound task queries covering:
- surname vs full name;
- person + space;
- person + sprint;
- open/not-completed constraint.

No code/config changes between cases. Require exact Oracle parity for every factual collection.

## Phase 5 — Representative multi-skill POC
Do not run all 54 yet. Run fresh-session source-supported cases for at least these 9 scenarios:
1. `Покажи DMS-380`
2. `Кратко объясни DMS-380`
3. `Проверь качество постановки DMS-380`
4. `Проверь критерии приемки DMS-380`
5. `Есть ли блокеры у DMS-380`
6. `Покажи здоровье спринта <FRESH_REAL_SPRINT>`
7. `Какой текущий спринт в DMS?`
8. `Покажи здоровье релиза <FRESH_REAL_RELEASE>`
9. `Покажи DMS-380 и затем задачи его исполнителя`

For each record loaded skill(s), typed capability trajectory, source observations, terminal status, latency and Oracle comparison where factual.

The compound lookup -> assignee -> tasks case must obtain assignee from the task observation and return the full exact assignee task set; no phrase/surname router.

Require all source-supported scenarios terminally correct. A truly unavailable source fact must be typed source-capability unavailable, never fabricated.

## Phase 6 — Safety/adversarial controls
Fresh sessions:
- nonexistent person;
- fake space;
- nonexistent sprint;
- nonexistent task key;
- natural request that tempts planner to use an invented login;
- normalization toward an unrelated real person;
- if live data provides one, surname still ambiguous even inside the bounded sprint context.

Require:
- no fabricated ids/facts;
- assignee literal not present in trusted observations rejected;
- contextual identity accepted only for exactly one authoritative match;
- ambiguity remains clarification/fail-closed;
- source unavailable != zero.

## Phase 7 — Architecture decision gate
GREEN requires all:
- Phase 0 GREEN;
- Garanin 5/5 exact parity;
- Moiseev 5/5 exact parity;
- PVM Guru benchmark 5/5 terminally Oracle-correct;
- DMS current sprint 5/5;
- >=6 generalized compound cases GREEN;
- >=9 representative skill scenarios terminally correct;
- lookup -> assignee -> tasks exact parity;
- semantic pre-pass absent from V4 execution;
- progressive skill loading visible;
- zero entity-specific hardcodes;
- safety negatives GREEN.

If GREEN: conclude the V4 skill-native API POC has passed the first meaningful architecture decision gate. Next owner step = Browser C/UI V4 wiring, then progressive expansion toward mandatory 54/54 A/B/C certification.

If RED: classify the first generalized boundary as one of planner / skill loading / capability binding / contextual identity / source adapter / Oracle parity / safety. Do **not** recommend V3 rollback merely because one seam remains. Recommend architectural rollback only if evidence shows the skill-native plan-act-observe loop itself is non-viable after these generalized fixes.

## Phase 8 — Report
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_RELIABILITY_POC_177.md`

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

If RED: include exact first failing function/boundary, raw trajectory/arguments, expected source truth, actual result and smallest generalized owner fix. No semantic-field/surname/phrase patch proposals.

If GREEN explicitly state:
- Agent Core v4 skill-native API POC is proven;
- PVM-Guru-style dynamic composition is demonstrated under governed capabilities;
- contextual unknown/ambiguous identity handling is source-backed;
- old semantic pre-pass is not required for this V4 slice;
- next = Browser C/UI V4 POC + progressive expansion toward mandatory 54/54 A/B/C certification.

Commit/push only the report and STOP.

## Start now
Execute Assignment 177 completely.