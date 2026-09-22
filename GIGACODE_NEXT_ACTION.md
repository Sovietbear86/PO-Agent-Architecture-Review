# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_205_V4_FULL_EXISTING_CATALOG_AND_ADVERSARIAL_ZERO_RED_RERUN`

## Critical owner remediation after first A205 attempt
The first A205 attempt did **not** exercise any skill. It failed at the planner interface boundary:
`RobustSkillNativePlannerV4.next_decision()` did not accept the new generic `session_context` parameter that the runtime now passes.

Owner fixes:
- `66549adac0d6efa3bbc7b04df6c944147131ecab` — robust planner now accepts `session_context: Mapping[str, str] | None` and includes it in the LLM payload exactly like the base planner.
- `0a6db2a1ceb62b3d775659904106952134be40d2` — regression proving robust planner API/payload parity with the base planner.

This is an interface-parity fix only:
- no skill logic changed;
- no Agent Core business branching added;
- no source routing changed;
- no completion semantics changed;
- no plugin contract changed.

The previous A205 report is **not** a valid 27-skill result because all 27 failed before skill loading, with 0 LLM/source trajectory execution. Re-run A205 **from scratch** after pulling current HEAD.

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT add new skills.
Do NOT start Wave S.
If any RED is found, classify/report only and stop progression.

## Context
A204 returned RED with four bounded defect classes plus manual adversarial findings:
- D-A204-1: sprint health / NL sprint-task requests could terminate on sprint identity only;
- D-A204-2: cardinality guard mapped `sprint.current -> sprint.list` although the skill id is `sprints.list`, and falsely treated "list of tasks in sprint" as a sprint-collection request;
- D-A204-3: completed turns had no generic source-validated entity context, so "в этом спринте / в этом релизе" could not resolve safely;
- D-A204-4: release health bound a product space as release id and release-task reads lacked a bounded live source filter.

Manual Browser cases additionally exposed:
- multi-hop clarification (space -> sprint -> original task goal) could fail;
- "кто больше всех загружен..." could false-complete on sprint identity and incorrectly claim data absence;
- "задачи без исполнителя" returned the unfiltered sprint collection as SUCCESS;
- task.history / task.time_in_status were declared but their live history path returned SOURCE_UNAVAILABLE;
- explicit sprint task collections suffered N+1 raw-unit validation latency.

Owner remediation bundle after A204 is intentionally generic / plugin-safe:
- generic completed-turn `session_context` added to HarnessRequest and planner payload; it contains only unique source-validated canonical entity facts and is TTL/session bounded;
- public API stores this internal context per session and never exposes it to Browser payloads;
- reliable grounding accepts a session-context literal only when it exactly equals a validated prior canonical value;
- multi-hop typed clarification contract remains pinned across every hop;
- sprint discovery is now an identity-only helper with no deterministic auto-completion contract; resolver identity alone must not satisfy health/task-list/analysis deliverables;
- cardinality guard now maps to `sprints.list` and does not interpret "список задач в спринте" as a sprint collection;
- `task.search` has typed `unassigned=true`; bounded space/sprint collections are actually filtered by null assignee before SUCCESS;
- product-space tokens are forbidden as release ids; missing release identity yields typed clarification;
- Task API live `task-query` now accepts a bounded `release` filter pushed to MCP TQL (`fix_version_s`), with no local-store fallback;
- history MCP arguments are schema-aware for flat/nested schemas;
- history/time-in-status catalog text is source-conditional rather than claiming current availability from catalog presence;
- certified sprint collection rows preserve sprint/release relation proof so hardened adapter can avoid per-task N+1 re-reads when proof is already present;
- no new production skill was added.

Permanent safe rollback remains:
`checkpoint/v4-pre-wave-s-a202@e580489950e5a149a6a740cb8779dfdb0351d471`.

## Mission
Prove that the complete existing V4 surface is again **zero RED**, including the user's real Browser adversarial cases.

A205 is the hard freeze gate.
**No new skill may be added until A205 GREEN and explicit owner/user approval.**

## Phase 0 — start + architecture audit
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record exact START_HEAD; tracked production worktree must be clean.
3. Read A204 report and diff `5b42e5930d6e2b64f85925f35bb15c2167becf0b..START_HEAD`.
4. Confirm:
   - no new business skill ids were added;
   - no surname/person/sprint/release literals or query-specific business branches were added to Agent Core;
   - session context is generic, source-validated, TTL/session bounded and public-response-hidden;
   - same-session context does NOT itself satisfy a completion contract;
   - multi-hop clarification still pins original required completion goals;
   - sprint-discovery change is plugin/catalog semantics, not a hardcoded health router;
   - release filter is pushed to live MCP query and never local store;
   - unassigned is a typed task constraint, not a phrase-specific branch;
   - dummy-55/plugin extension architecture remains intact;
   - semantic_prepass remains false.

Any violation => RED.

## Phase 1 — automated suites
Run at minimum:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4*.py -v
python -m pytest tests/test_v4*.py -v
cd ../task-api
python -m pytest tests/test_swtr_read_facade.py tests/test_swtr_read_sprint_collection.py tests/test_swtr_task_query_release.py -v
```

Mandatory named proofs:
- sprint collection guard maps to `sprints.list`;
- "список задач в этом спринте" is NOT a sprint-collection cardinality signal;
- completed-turn session context is internal and reused only in same session;
- validated context drops ambiguous entity values;
- multi-hop clarification preserves the original goal;
- unassigned filtering returns only truly unassigned tasks;
- product space cannot be accepted as release id;
- explicit release id uses live release collection;
- history MCP schema helper works for flat and nested request schemas;
- canonical sprint rows preserve relation proof;
- plugin/dummy-55 tests GREEN.

Record exact totals.

## Phase 2 — sprint health hard gate
Fresh REAL AS21 Oracle immediately before each batch.

Run at least 10 fresh sessions:
`здоровье сентябрьского спринта по DMS`

Require every supported completed run:
- period resolves to the source sprint;
- `sprint.health` capability **actually executes**;
- completion cannot occur on `sprint.search` / sprint identity alone;
- final data contains actual health fields: at minimum sprint_id + total and available progress/status metrics;
- exact total/status parity vs fresh sprint-task Oracle;
- UI uses `sprint_health` / analysis contract, not identity-only `sprint_summary`;
- answer must not say metrics are unavailable when the live sprint-task set was successfully read.

Any identity-only COMPLETED => RED.

## Phase 3 — completed-turn dialogue context
For at least 10 same-session pairs:

Turn 1:
`здоровье сентябрьского спринта по DMS`

Turn 2:
`Покажи список задач в этом спринте и их статусы`

Require:
- turn 2 request carries same session_id but no fabricated business state from UI;
- Harness receives internal validated session_context including prior sprint_id/space;
- `этом спринте` resolves to the exact source-confirmed prior sprint;
- task collection executes and matches fresh key/status Oracle;
- no `unknown skill: sprint.list`;
- no fallback to current sprint merely because it happens to be the same;
- session context does not leak to public response.

Controls:
- same turn 2 in a new session must NOT inherit the old sprint;
- explicit `DMS-SPRNT-3` query must remain exact.

## Phase 4 — multi-hop clarification
Use a real case where period+space yields more than one candidate sprint, e.g. the user's OLP September case when source still returns OLP-SPRNT-7 / OLP-SPRNT-6.

Query:
`покажи активные задачи у Гаранина в сентябрьском спринте по OLAP`

Follow the actual Browser flow:
1. typed clarification for product space -> choose `OLP`;
2. typed clarification for sprint -> choose one real candidate, e.g. `OLP-SPRNT-7`;
3. original task goal must resume and execute.

Run at least 5 full chains.
Require:
- same original task completion goal pinned across both clarification hops;
- already resolved space preserved;
- selected sprint preserved;
- member identity source-backed;
- terminal task collection executes with person + space + sprint + active/not_completed constraint;
- exact Oracle parity;
- no generic V4 ERROR after second clarification.

Any loss of original goal => RED.

## Phase 5 — unassigned tasks
Test both:
1. `найди задачи без исполнителя в OLP`
2. `найди задачи без исполнителя в текущем спринте OLP`

If the first requires a bounded clarification, follow it exactly.
For every COMPLETED result:
- final task.search arguments contain `unassigned=true`;
- every returned task has null/empty canonical assignee identity;
- no assigned task may appear;
- count/key parity vs fresh REAL AS21 Oracle;
- unfiltered sprint/space collection must NEVER be returned as SUCCESS for an unassigned request.

Any "filter was not applied" + COMPLETED => RED.

## Phase 6 — unsupported analytics safety
Run at least 5x:
`кто больше всех загружен в сентябрьском спринте по DMS?`

Current V4 catalog does not yet add a new workload-aggregation skill in this remediation.
Therefore acceptable behavior is:
- source-safe explicit statement that this analytical capability is not yet implemented / not available in the current catalog, OR
- an existing governed capability truly computes the requested aggregate from source and exact Oracle parity is proven.

Forbidden:
- identity-only sprint result marked COMPLETED as if it answered workload;
- claim "source has no assignee distribution" merely because only sprint.search executed;
- invented ranking.

False resolver-only answer => RED.

## Phase 7 — release health + release tasks
### Missing release identity
Run at least 10x:
- `здоровье релиза по DMS`
- `задачи в релизе по DMS`

Require:
- DMS must be treated as product space, never as release_id;
- if no unique current release semantics are source-backed, return typed clarification asking for a concrete release id;
- no full-tenant release scan;
- no local `/api/v1/tasks` read;
- no generic SOURCE_UNAVAILABLE merely because the user omitted the release id.

### Explicit release identity
If `/versions` / MCP search_versions is healthy, discover one REAL release id and run:
- `здоровье релиза <REAL_ID> по DMS`
- `задачи релиза <REAL_ID> по DMS`

Require:
- live task-query receives bounded space=DMS + release=<REAL_ID>;
- MCP query contains `space = "DMS"` and `fix_version_s = "<REAL_ID>"`;
- exact release task key/status parity;
- release.health executes for health request.

If release inventory remains a proven external source outage:
- explicit-id discovery subsection may be SOURCE_CONDITIONAL;
- bounded release route unit tests must still be GREEN;
- do not invent an id.

## Phase 8 — task history and duration
Run:
- `покажи историю статусов задачи DMS-380` at least 5x;
- `сколько времени задача DMS-399 провела в каждом статусе` at least 5x;
- `Ты умеешь определять длительность задач?` at least 3x.

Require:
- history route uses live MCP `get_unit_change_history` with its actual schema (flat or nested request);
- if source is available, exact chronological transitions/durations from source;
- if source is genuinely unavailable, typed SOURCE_CONDITIONAL/fail-closed, never empty history;
- capability-description answer must be conditional: declared capability != proof that live source is currently available;
- no unconditional "да, умею" that implies current source availability when the following call cannot be served.

## Phase 9 — sprint collection performance / N+1
Run explicit:
`Покажи список задач в DMS-SPRNT-3 и их статусы`

At least 3x with fresh Oracle.
Audit Task API/agent logs:
- complete sprint route returns canonical relation proof;
- hardened adapter must not perform one raw `GET /tasks/{code}` validation call per task when the certified row already carries matching sprint/space relation;
- per-task raw proof is allowed only for rows missing canonical relation metadata;
- exact task/status parity retained;
- record backend collection latency and total agent latency.

Any correctness weakening => RED.
A persistent 65-task -> 65 raw-read N+1 after canonical relation proof exists => RED performance regression.

## Phase 10 — canonical 27-skill full regression
Re-run **all 27 existing V4 skills**, no skips.

For each row record:
- NL request;
- expected/actual skill;
- loaded skills;
- capabilities;
- completion mode;
- source route;
- Oracle parity;
- evidence;
- UIContract;
- GREEN / SOURCE_CONDITIONAL / RED.

Overall A205 GREEN requires **0 RED**.

SOURCE_CONDITIONAL is allowed only for a proven external/source limitation and must fail closed without fabrication.

## Phase 11 — Browser C adversarial suite
Use the real UI for at minimum:
1. sprint health;
2. same-session "этом спринте" follow-up;
3. multi-hop OLP clarification;
4. unassigned current-sprint tasks;
5. unsupported workload question;
6. release health without release id;
7. explicit release test if source inventory permits;
8. history/time-in-status;
9. person attachments;
10. person+sprint multi-filter;
11. ambiguity continuation;
12. safe not-found.

No internal session_context / continuation observations may leak into UI.

## Phase 12 — source/local-store audit
Across all A205 runs:
- factual V4 paths: zero `GET /api/v1/tasks` truth;
- no tenant-wide release scan;
- no false REAL_EMPTY from source outage;
- exact source provenance logged.

## Phase 13 — plugin/extensibility
Re-run A190 dummy-55 gate.
Adding the synthetic skill must still require **zero business-logic edits to Agent Core/planner/runtime**.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_EXISTING_CATALOG_ADVERSARIAL_GREEN`
- `AGENT_CORE_V4_EXISTING_CATALOG_ADVERSARIAL_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires:
- Phase 1 tests clean;
- A204 defects D1-D4 closed or correctly SOURCE_CONDITIONAL only where source itself is proven unavailable;
- manual multi-hop/unassigned/history/release cases safe;
- full 27-skill matrix has 0 RED;
- Browser C supported paths GREEN;
- zero local truth;
- dummy-55 GREEN;
- no Harness/plugin architecture regression.

If any RED:
**STOP. Do not add skills or start Wave S. Return root cause for owner remediation and another full re-gate.**

If GREEN:
**Freeze the tested HEAD as a new post-A205 rollback checkpoint. Do not start Wave S automatically; wait for explicit owner/user approval.**

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_EXISTING_CATALOG_ADVERSARIAL_205.md`

## Service keepalive
Leave UI/backend/Task API/MCP running.
Return:
- verdict;
- exact START_HEAD;
- report commit;
- GREEN/SOURCE_CONDITIONAL/RED totals;
- service URLs/ports/PIDs/health;
- key trajectory evidence for sprint health, same-session context, multi-hop clarification, unassigned, release, history.
Then stop.
