# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_218_SELF_INTROSPECTION_UX_GATE

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT start another migration batch.
Commit/push only the QA report.

## Frozen baseline
A217D = GREEN.
Rollback checkpoint:
`checkpoint/v4-batch4-green-a217d`

Production robust runtime, Batch 4 release routing and portfolio overview are frozen GREEN.

## Owner implementation
Commits:
- `5c0ed1642ec6c7d3e4c0d669946121123242d365`
- `f4d03e37bec6bbe952a8ca646d286fe6255168be`

New plugin-only user-facing skill:
- `agent.help`

Capability:
- `agent.help`

No Agent Core/planner/runtime/session-context code changed.

## Intended behavior

### Full skill catalog
Queries such as:
- "покажи полный список навыков, которые ты поддерживаешь"
- "какие навыки ты умеешь"
- "что ты умеешь"
- "show all supported skills"

must load `agent.help` and call `agent.help mode=skills`.

The capability reads the LIVE runtime `SkillCatalogV4`.
It must never maintain a second hardcoded skill list.

Returned data must include:
- exact `skill_count`;
- every current skill id exactly once;
- summary for each skill;
- family;
- plugin ids/count;
- `catalog_source=LIVE_V4_SKILL_CATALOG`;
- `availability_semantics=DECLARED_NOT_EQUAL_SOURCE_READY`.

Important:
catalog presence means declared capability only.
It must NOT claim that every source-backed skill is currently executable.
Sparse release-source skills may remain SOURCE_CONDITIONAL on invocation.

### Presence / conversational ping
Queries like:
- "ты тут?"
- "ты на связи?"
- "are you there?"

should route to `agent.help mode=ping` and return a short presence acknowledgement.
No AS21 call is necessary.

## Phase 0 — architecture invariant
1. Pull branch; record START_HEAD and clean worktree.
2. Diff only owner implementation commits from Batch 4 checkpoint.
3. Prove:
   - plugin + focused test only;
   - zero Agent Core/planner/runtime/session-context changes;
   - registry discovery remains deterministic;
   - dummy-55 invariant GREEN.

Any core routing special case => RED.

## Phase 1 — focused/unit tests
Run:
- tests/test_agent_core_v4_agent_help.py
- tests/test_agent_core_v4_plugin_registry.py
- tests/test_agent_core_v4_planner_signature_parity.py
- full relevant V4 suites

Require zero unexplained failures.

## Phase 2 — registry truth / 54-target reconciliation
Independently enumerate the live registry after plugin discovery.

Report:
- exact plugin_count;
- exact skill_count;
- sorted skill ids;
- duplicates = 0;
- whether `agent.help` is present exactly once.

Compare exact live skill_count with the authoritative V4 target of 54 user-facing skills.

Important classification:
- if count == 54: mark `V4_54_INVENTORY_COUNT_RECONCILED`;
- if count != 54: do NOT fabricate a missing/extra skill and do NOT fail the self-introspection implementation merely because historical scope/count needs reconciliation. Mark `V4_54_INVENTORY_RECONCILIATION_REQUIRED` and identify exact delta/list for owner review.

## Phase 3 — natural-language full catalog gate
Run each >=3:
- "покажи полный список навыков, которые ты поддерживаешь"
- "какие навыки ты умеешь"
- "что ты умеешь"
- "show all supported skills"

Require:
- agent.help loads;
- agent.help(mode=skills) executes;
- terminal COMPLETED;
- no task/sprint/release/business skill executes;
- no AS21/source call;
- answer/data derived from live catalog;
- exact skill_count equals independent registry count;
- exact id set equals independent registry id set.

No partial catalog is acceptable for the explicit "полный список" form.

## Phase 4 — Browser C catalog UX
Real UI:
- explicit full-list query;
- one short "что ты умеешь" query.

Require:
- SUCCESS_WITH_DATA/COMPLETED;
- no V4 ERROR;
- every skill id from the live registry is inspectable/visible in the response payload/UI;
- no silent truncation that makes "полный список" false;
- note/semantics make clear that catalog presence != source readiness.

If prose summarization omits ids but the dedicated rendered catalog exposes all ids, that is acceptable.
If neither prose nor rendered data exposes all ids, RED.

## Phase 5 — conversational ping
Run >=5:
- "ты тут?"
- "ты на связи?"
- "are you there?"

Require:
- agent.help(mode=ping);
- concise acknowledgement;
- COMPLETED;
- zero AS21/source calls;
- zero clarification;
- no stale session resurrection;
- no "могу работать со спринтами..." boilerplate unless the user asks for capabilities.

## Phase 6 — source-free audit
For all agent.help runs:
- GET/POST to task-api/MCP-SWTR caused by the turn = 0;
- local factual reads = 0;
- mutations = 0;
- tenant scans = 0.

## Phase 7 — retained regression
At minimum:
- ordinary task lookup DMS-380;
- current sprint DMS;
- member time Semavin;
- portfolio.overview;
- standalone release identity;
- release progress typed SOURCE_CONDITIONAL;
- release health typed SOURCE_CONDITIONAL;
- dummy-55.

Require A217D parity and zero planner signature/runtime failures.

## Phase 8 — safety/semantics
Ask:
- "умеешь анализировать здоровье релиза?"
- "умеешь считать утилизацию команды?"

Expected:
- agent may describe declared capability conditionally;
- must not equate catalog declaration with current source readiness;
- must not fabricate release source maturity;
- no business source call is required merely to list declared capabilities unless planner deliberately executes the requested business skill.

## Verdict
Use exactly one:
- `AGENT_SELF_INTROSPECTION_GREEN_A218`
- `AGENT_SELF_INTROSPECTION_RED_A218`

Report separately:
- `V4_54_INVENTORY_COUNT_RECONCILED` OR
- `V4_54_INVENTORY_RECONCILIATION_REQUIRED`

If GREEN:
recommend immutable self-introspection checkpoint.
Then stop and return the exact registry count/list delta so the owner can decide whether the next step is full V4-54 A/B/C certification or a narrowly identified missing-skill implementation.

If RED:
identify first failing boundary and STOP.

Do not modify code.
