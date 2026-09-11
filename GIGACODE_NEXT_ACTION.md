# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_177_AGENT_CORE_V4_RELIABILITY_RETEST`

## Mission
Re-test Agent Core v4 after the generalized reliability fixes from Assignment 176. This remains a **skill-native raw-query POC**, not an H1B/semantic-prepass test.

Owner fixes under test:
- `a8b8d632...` — runtime factory now instantiates `ReliableAgentCoreV4Runtime` for the v4 production path;
- `57e9bcd5...` — focused reliability unit tests added;
- `9241f4e1...` — reliability tests corrected to the real `V4Observation` contract;
- existing reliability overlay `agent_core_v4_reliable.py` provides:
  - team-roster scoped disambiguation followed by REAL AS21 identity validation;
  - safe reuse of a canonical assignee literal only when it exactly matches a trusted prior observation;
  - morphology-safe person normalization without hardcoded names;
  - source-backed `sprint.current` using the full REAL AS21 collection.

QA ONLY. Do not modify production/backend/frontend/test code, prompts, model configuration, registry contracts, `.env`, `GIGACODE.md`, or learning data.

## Absolute rules
- First: `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
- Record HEAD and verify the owner commits above are ancestors.
- Keep the user's currently configured Qwen 3.8 model/provider unchanged.
- Set only runtime env `PO_AGENT_AGENT_CORE_V4_ENABLED=true`; restart Task API and PO Agent so the new v4 runtime is actually loaded.
- REAL Oracle B = direct MCP-SWTR/AS21 only. Never local `/api/v1/tasks`, local DB, sync, fake/frozen data, prior report counts, or Agent A output.
- Concurrency=1. Source timeout >=300s; long agent calls up to 600s.
- Exact task-key sets are mandatory for factual collection comparisons.
- Fresh unique session for every reliability run unless a case explicitly tests multi-step continuity.
- If a production defect is found, identify the first failing boundary and STOP. Do not patch code.
- Commit/push only the final QA report.

## Phase 0 — Build/runtime proof
1. Run focused tests:
   - `tests/test_agent_core_v4_skill_native.py`
   - `tests/test_agent_core_v4_reliable.py`
   - affected runtime factory/API tests.
2. Prove `/api/v1/query-v4` is backed by `ReliableAgentCoreV4Runtime`, not base `AgentCoreV4Runtime`.
3. Prove `semantic_prepass_used == false` for v4.
4. Prove no person name, sprint id, task id or task count was added to catalog/prompts/routing.
5. Health must show v4 enabled/ready and REAL source connected.

## Phase 1 — Fresh Oracle B
Independently read REAL AS21 before Agent A for:
1. all approved-space tasks for Garanin;
2. open/not-completed DMS tasks for Moiseev;
3. Goncharov tasks in `OLP-SPRNT-5` after source identity resolution;
4. exact `DMS-380`;
5. current DMS sprint;
6. one source-supported sprint for health;
7. one source-supported release/version for health.

Persist canonical identities and exact key sets.

## Phase 2 — Critical identity/search gate
Run each case **5 times**, fresh session each time.

### A. `Задачи Гаранина`
Require 5/5 COMPLETED and exact Oracle key-set parity.

### B. `Открытые задачи Андрея Моисеева в DMS`
Require 5/5 COMPLETED and exact Oracle parity.
Test at least two natural variants in the five runs, including an inflected full-name form. No hardcoded name rule is allowed.

### C. PVM Guru benchmark
`Открытые задачи Гончарова в спринте OLP-SPRNT-5`

Require, when source-resolvable:
- 5/5 COMPLETED;
- member resolution source-backed;
- sprint validation source-backed;
- task.search retains person+sprint+open constraints;
- exact Oracle task-key parity;
- no Goncharov or OLP-SPRNT-5 hardcode.

If the REAL source proves Goncharov ambiguous, record that and repeat the same unseen-person+sprint test with one person discovered live from that sprint. Do not use a preconfigured surname workaround.

### Identity-binding invariant
For every successful person search, verify either:
- task.search assignee uses `$obs.N.member_login`, OR
- a literal canonical login is accepted only because it exactly equals a trusted prior observation.
An invented login must still be rejected.

If any of A/B/C is below 5/5 for a production reason, STOP RED.

## Phase 3 — Current sprint regression
Run `Какой текущий спринт в DMS?` 5 times.
Require 5/5 terminal correctness against Oracle B.
Confirm the v4 handler uses the REAL source full collection and does not depend on the legacy small/default scan.

## Phase 4 — Cross-skill POC retest
Run the following through `/api/v1/query-v4` with REAL data:
1. `Покажи DMS-380`
2. `Кратко объясни DMS-380`
3. `Проверь качество постановки DMS-380`
4. `Проверь критерии приемки DMS-380`
5. `Есть ли блокеры у DMS-380`
6. `Покажи здоровье спринта <FRESH_REAL_SPRINT>`
7. `Покажи здоровье релиза <FRESH_REAL_RELEASE>`
8. `Покажи DMS-380 и затем задачи его исполнителя`

Require at least 8/8 correct or a source-proven capability-unavailable result for genuinely unsupported source facts. For collections, exact key-set parity is mandatory.

## Phase 5 — Safety negatives
Fresh sessions:
- nonexistent person;
- fake space;
- nonexistent sprint;
- nonexistent task key;
- planner attempt with made-up login not present in query/source;
- person normalization to an unrelated real team member.

Require fail-closed/no fabrication. Source unavailable must never become zero tasks.

## Phase 6 — V4 architecture decision gate
GREEN requires all of:
- Phase 0 GREEN;
- critical identity/search gate A/B/C = 5/5 each or source-proven ambiguity handled correctly;
- DMS current sprint = 5/5;
- cross-skill POC >=8/8 source-supported scenarios;
- compound lookup -> assignee -> tasks works through observations;
- exact Oracle parity on all factual collections;
- `semantic_prepass_used=false` throughout;
- zero person/sprint phrase hardcodes;
- safety negatives GREEN.

If GREEN, explicitly conclude that the v4 branch has passed the first meaningful decision gate and the next owner step is Browser C/UI wiring followed by expansion toward the mandatory 54/54 certification.

If RED, identify the first failing generalized boundary. Do **not** recommend returning to semantic-field/surname routing unless the entire v4 architecture gate is proven non-viable.

## Phase 7 — Report
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_RELIABILITY_RETEST_177.md`

Allowed verdicts:
- `AGENT_CORE_V4_RELIABILITY_GREEN`
- `V4_SOURCE_ENTITY_RESOLUTION_RED`
- `V4_OBSERVATION_BINDING_RED`
- `V4_PLANNER_RELIABILITY_RED`
- `V4_CURRENT_SPRINT_RED`
- `V4_AGENT_ORACLE_PARITY_RED`
- `V4_SKILL_COMPOSITION_RED`
- `V4_SAFETY_RED`
- `V4_BUILD_RUNTIME_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

Commit/push only the report and STOP.

## Start now
Execute Assignment 177 completely.