# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_205_V4_FULL_EXISTING_CATALOG_AND_ADVERSARIAL_ZERO_RED`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT add skills.
Do NOT start Wave S.
Any RED blocks progression.

## Context
A204 returned RED and isolated four classes:
1. sprint health / period task-list requests could terminate on identity-only `sprints.discover`;
2. sprint collection guard used the capability id `sprint.list` instead of skill id `sprints.list` and false-triggered on task-list wording;
3. ordinary same-session references such as `этом спринте / этом релизе` had no validated completed-turn entity context;
4. release health had both bad grounding (space treated as release id) and no bounded live release-task path.

Manual Browser testing also exposed:
- two-hop clarification (space -> ambiguous sprint -> selected sprint) can lose the original terminal goal;
- unsupported workload analytics can falsely look like source data is missing after only sprint identity resolution;
- `без исполнителя` could return the entire sprint while admitting the filter was not applied;
- history/time-in-status are declared skills but their live source can be unavailable;
- explicit sprint task collections were slowed by N+1 raw-unit membership revalidation.

Owner remediation since A204 is **generic/plugin-preserving**. Key changes include:
- generic source-validated completed-turn session context: `e7881bed`, `52d43616`, `6beab796`;
- sprint cardinality fix: `b1d548d8`, `2855f615`;
- typed `unassigned` constraint and exact filtering: `fcbd65cc`, `cd2f439d`;
- sprint resolver is identity-only and cannot deterministic-auto-complete a health/analytics deliverable: `f542c399`, `c3178c01`;
- planner contract explicitly forbids resolver-only substitution for requested collection/metric/analysis: `4b6befd5`;
- release id validation + bounded REAL AS21 release filter: `85c772b6`, `5238b423`, `fffd148e`, `cfd5a3eb`;
- source-dependent capability wording/readiness hardened for history/time-in-status: `97fdefff`, `958155aa`;
- completed-session context, unassigned, release-filter and multi-hop clarification tests: `18185e3c`, `a2cc17c6`, `d6fc9ff2`, `e8e1fd1a`, `7bc4863d`;
- sprint collection N+1 removal on source-proven complete rows: `18e483d8`, `cb855e60`, `30582611`;
- V4 DoD now locks generic session-context / multi-hop / deliverable / source-readiness invariants.

Permanent rollback checkpoint remains:
`checkpoint/v4-pre-wave-s-a202` @ `e580489950e5a149a6a740cb8779dfdb0351d471`.

## Mission
Run one consolidated **zero-RED full existing-catalog re-gate** after A204 remediation.

A205 must prove:
- every existing skill still works or fails only for a proven source limitation;
- the user's manual adversarial cases are closed;
- Harness/plugin extensibility is intact;
- no local-store factual truth;
- no resolver-only false success;
- no dropped filters;
- no conversational-context fabrication.

## Phase 0 — start / architecture audit
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record exact START_HEAD; tracked worktree must be clean except known QA artifacts.
3. Diff A204 START `5b42e5930d6e2b64f85925f35bb15c2167becf0b..START_HEAD`.
4. Confirm:
   - no person/sprint/release literal hardcode;
   - no query-specific branch such as `if "Гаранин"` / `if "здоровье"` in Agent Core;
   - completed-turn context contains only canonical source-validated entities and is TTL/session bounded;
   - multi-hop clarification preserves generic loaded skills, observations and completion goals;
   - new task/release/sprint behavior is expressed through capability schemas, plugin procedures, generic Harness controls and live adapters;
   - dummy-55 still requires zero core business changes;
   - local `/api/v1/tasks` is never a factual V4 truth source.

Any architecture violation => RED.

## Phase 1 — automated suites
Run at minimum:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4*.py -v
python -m pytest tests/test_v4*.py -v
cd ../task-api
python -m pytest tests/test_swtr_read_sprint_collection.py -v
python -m pytest tests/test_swtr_task_query_release.py -v
```

Also run relevant task-api/history/source tests.

Mandatory named proofs:
- sprint collection guard maps to `sprints.list`, never `sprint.list`;
- task-list wording does not trigger sprint-collection remap;
- completed-turn session context is internal + reused;
- multi-hop clarification keeps the original query/filters and pinned goal;
- `unassigned=true` returns only tasks with no assignee;
- release filter reaches source-side MCP/TQL, no local-store fallback;
- source-proven sprint rows avoid N+1 raw-unit membership reads;
- completion/frontier/premature-READY protections remain GREEN;
- dummy-55/plugin registry GREEN.

Zero unexplained test failures.

## Phase 2 — fresh REAL AS21 Oracle
Immediately before factual batches build fresh source oracles for:
- DMS September sprint and full tasks/status set;
- OLP current sprint and September sprint candidates;
- exact unassigned set in OLP current sprint;
- DMS-380 history endpoint state;
- DMS-399 history/time-in-status endpoint state;
- release/version inventory for DMS if source allows it;
- one concrete REAL release id + exact release task set if obtainable.

Never reuse A204 counts when source has drifted.

## Phase 3 — sprint health / period task-list
### H1
Run 10x fresh:
`здоровье сентябрьского спринта по DMS`

Require:
- correct period sprint resolution;
- actual `sprint.health` capability executes;
- final skill/UI = health/analysis, not identity-only `sprint_summary`;
- health task counts/progress exact vs fresh sprint oracle;
- `sprints.discover` may resolve identity but MUST NOT be the terminal deliverable;
- completion runtime_contract or safe source failure, never identity-only success.

### H2
Run 10x fresh:
`Покажи список задач сентябрьского спринта DMS и их статусы`

Require actual task collection + statuses and exact key parity. Identity-only completion is RED.

### H3 — performance
Run explicit:
`Покажи список задач в DMS-SPRNT-3 и их статусы` at least 3x.

Audit Task API logs:
- no per-task N+1 raw membership validation caused by the Agent adapter when the sprint route returns `complete=true, membership_proven=true`;
- exact parity retained;
- record latency before/after. A regression back to ~65 extra raw task reads is RED_PERFORMANCE.

## Phase 4 — same-session completed-turn context
At least 10 pairs:
1. `здоровье сентябрьского спринта по DMS`
2. same session: `Покажи список задач в этом спринте и их статусы`

Require:
- turn 1 establishes canonical DMS sprint;
- API persists only validated `space/sprint_id` internally;
- turn 2 receives that session_context;
- `этом спринте` resolves to the validated sprint, not current-sprint guessing;
- task collection exact;
- no `unknown skill: sprint.list`;
- context does not leak in public payload.

Negative:
- same phrase in a new session must not inherit the old sprint;
- unrelated new query in same session must not silently receive old sprint filter.

## Phase 5 — multi-hop clarification
Reproduce user's OLP case at least 10 times:
`покажи активные задачи у Гаранина в сентябрьском спринте по OLAP`

Expected flow when source requires it:
1. typed clarification of space -> choose `OLP`;
2. if multiple September sprints overlap -> typed sprint options;
3. choose a source-backed sprint, e.g. one of the offered OLP-SPRNT-* ids;
4. terminal task collection executes.

Require:
- same session + clarification ids at every hop;
- original goal `active tasks of person` remains pinned through both clarifications;
- `status=not_completed` remains applied;
- person + OLP + selected sprint + active status all covered by final arguments;
- exact Oracle parity;
- no V4 ERROR after second option click.

Any loss of the active/person constraint => RED.

## Phase 6 — unassigned constraint
Run:
1. `найди задачи без исполнителя в OLP` -> if sprint needed, answer with current sprint through typed continuation;
2. `найди задачи без исполнителя в текущем спринте OLP`;
3. same for DMS as control.

Require:
- terminal task.search arguments include `unassigned=true`;
- result contains **only** rows whose assignee/login/id are empty;
- exact key-set parity vs fresh sprint oracle;
- never return all sprint tasks while warning that filter was not applied;
- if filter cannot be applied, fail closed / unsupported, never SUCCESS_WITH_DATA.

## Phase 7 — unsupported analytics honesty
Run at least 5x:
`кто больше всех загружен в сентябрьском спринте по DMS?`

Current catalog does not yet contain the future workload skill.
Require:
- may resolve sprint identity as an intermediate observation;
- MUST NOT claim that source lacks assignee/task distribution merely because only sprint identity was loaded;
- MUST NOT present sprint_summary as if workload analysis was delivered;
- acceptable outcome: explicit honest statement that this analytical skill is not implemented/migrated yet, without fabricated result; or a genuinely supported governed path if one exists.
- no invented ranking/person.

Classify any identity-only SUCCESS_WITH_DATA masquerading as analysis as RED.

## Phase 8 — history and time-in-status readiness
Run:
- `покажи историю статусов задачи DMS-380`
- `сколько времени DMS-399 провела в каждом статусе?`
- `Ты умеешь определять длительность задач?`

For DMS-380/DMS-399:
- if authoritative history endpoint works, exact history/time calculations must be returned;
- if endpoint is unavailable, typed SOURCE_UNAVAILABLE/SOURCE_CONDITIONAL is correct;
- empty history must not be fabricated from outage.

For capability question:
- catalog definition must not be stated as guaranteed current live availability;
- answer should distinguish “skill is defined” from “authoritative history source is currently available”.

## Phase 9 — release health / release tasks
### R1 missing release identity
Run 10x:
`здоровье релиза по DMS`
and
`задачи в релизе по DMS`

Because no release id is supplied:
- DMS must be treated as space, never as release id;
- expected = typed clarification asking which release, preferably source options if reliable inventory is available;
- generic AS21-unavailable caused by trying `release=DMS` is RED.

### R2 concrete release
If a REAL release id can be obtained from source:
- `здоровье релиза <REAL_ID> по DMS`
- `задачи релиза <REAL_ID> по DMS`

Require:
- bounded source-side release predicate (`fix_version_s` / task-query `release`);
- zero full-tenant client-side release scan;
- zero local-store reads;
- exact release task parity;
- release.health actual metrics, not resolver-only completion.

If the source version inventory itself is genuinely unavailable, mark only the explicit-release discovery control SOURCE_CONDITIONAL; do not turn `DMS` into a release id.

## Phase 10 — full existing 27-skill matrix
Run **all 27 current V4 skills**, no skips.

For every row record:
- natural-language request;
- expected/actual skill;
- loaded skills;
- capabilities;
- arguments/constraints;
- completion mode;
- source route;
- exact Oracle parity where factual;
- UIContract;
- Browser state where applicable;
- GREEN / SOURCE_CONDITIONAL / RED.

Overall A205 cannot be GREEN with any RED.

## Phase 11 — Browser C adversarial pack
Use real UI for at least:
1. sprint health;
2. same-session `этом спринте` task follow-up;
3. two-hop OLP clarification;
4. unassigned current-sprint query;
5. unsupported workload question;
6. task history/time-in-status;
7. release health missing-release clarification;
8. concrete release path if source-supported.

No internal session/continuation state leak.

## Phase 12 — global source/local audit
Across all runs:
- `GET /api/v1/tasks` factual reads = 0;
- no fake/frozen/local Oracle;
- no broad release client-side scan;
- no unexplained N+1 sprint membership reads;
- source outages fail closed;
- model/429 timeout runs are retained and classified, never silently discarded.

## Phase 13 — plugin/Harness invariant
Re-run dummy-55 gate.
Prove a synthetic skill can still be added/discovered/bound/completed/UI-propagated with zero Agent Core/planner/runtime business edits.

Static audit must show the A204 fixes did not introduce skill-specific core branching.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_EXISTING_CATALOG_ADVERSARIAL_GREEN`
- `AGENT_CORE_V4_EXISTING_CATALOG_ADVERSARIAL_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires:
- automated gates clean;
- all 27 skills tested;
- **0 RED**;
- all manual adversarial cases above closed or correctly SOURCE_CONDITIONAL;
- no resolver-only false success;
- no dropped unassigned/status/person/sprint constraints;
- same-session context safe;
- multi-hop clarification safe;
- release grounding correct;
- local factual reads = 0;
- plugin gate GREEN.

If any RED:
**STOP. No Wave S, no new skills. Do not fix production code. Return exact root cause to owner for another remediation/re-gate.**

If GREEN:
recommend:
**Freeze A205 as a new clean rollback checkpoint. Do not start Wave S automatically; wait for explicit owner/user approval.**

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_FULL_EXISTING_CATALOG_ADVERSARIAL_205.md`

## Service keepalive
Leave UI/backend/Task API/MCP running.
Return:
- verdict;
- START_HEAD;
- report commit;
- 27-skill counts;
- adversarial case matrix;
- service URL/port/PID/health;
- key latency and route-provenance stats.
Then stop.
