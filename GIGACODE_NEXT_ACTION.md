# GigaCode — Current Action

## ACTIVE: Assignment A229S1 — Task type + hierarchy plugin gate

Role: QA/source-forensics/browser tester only. **Do not modify production code.**

Owner added exactly two extra plugin skills before resuming latency work:

- `task.type_analysis`
- `task.hierarchy`

Architectural rule:
- Agent Core V4 is frozen;
- canonical 54 must remain unchanged;
- new behavior is plugin/adapter/read-only Task API only;
- A229R1 latency verification remains paused until this gate closes.

Certified baseline before this wave:

`checkpoint/v4-task-details-richtext-green-a229u2r@be5131c83b7fd666c79af0e69e1b5cefd0961e62`

---

## P0 — integrity / build / focused regressions

1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD and clean worktree.
2. Prove byte identity vs the certified checkpoint for:
   - `src/po_agent/harness/agent_core_v4.py`
   - `src/po_agent/harness/agent_core_v4_robust.py`
   - `src/po_agent/harness/agent_core_v4_reliable.py`
   - runtime/session orchestration files.
3. Prove canonical coverage is still exactly **54/54**.
4. Prove the two new skills are extra live-registry plugin skills, not canonical replacements.
5. Run focused tests:
   - `test_agent_core_v4_task_catalog.py`
   - `test_agent_core_v4_task_semantics_hierarchy.py`
   - `test_task_api_as21_adapter.py`
   - `task-api/tests/test_swtr_assignee_canonical.py`
   - `task-api/tests/test_swtr_task_relations.py`
6. Run full V4 blast-radius and frontend build.
7. Any Core change, registry break, build regression, or retained functional regression => **RED STOP**.

---

## P1 — REAL AS21 task-type source contract

Purpose: independently prove what AS21 actually uses for task type.

### Source discovery

Using direct MCP-SWTR / Task API oracle, inspect a bounded sample from approved product spaces. Start with DMS and one additional space; do not scan the tenant.

For each source unit capture:

- `unit.code`
- `unit.suit.code`
- `unit.suit.name`
- the task type shown in the AS21 card/UI if independently observable.

Required conclusions:

1. Is `unit.suit` the authoritative task-type field?
2. What distinct type code/name pairs exist in the bounded sample?
3. Are Story/Bug/Defect present? If some are absent, record that as corpus evidence — do not invent them.
4. Does `find_units_by_filter` preserve `suit` in the rows used by the new capability?

Record the discovered type inventory **as evidence only**, never as production hardcode.

### Agent tests

Choose source-proven examples dynamically from the discovery.

Run at least 5 times each:

A. type distribution in a bounded scope, e.g.
`Покажи распределение типов задач <person> в <space>`

B. exact type + person + space:
`Покажи <SOURCE_TYPE> задачи <person> в <space>`

C. exact type + status:
`Покажи открытые <SOURCE_TYPE> задачи <person> в <space>`

D. type + another certified constraint, preferably sprint or created period when a non-empty oracle exists.

Require:
- terminal skill/capability = `task.type_analysis`;
- source type code/name preserved;
- all user constraints preserved in the SAME capability trajectory;
- exact task-key/count parity vs independent REAL AS21 oracle;
- distribution counts exact;
- no local-store read;
- no tenant-wide scan;
- no type guessed from title labels such as `[doc]`;
- unknown source-defined types work without code changes.

Any false zero, dropped status/person/space/sprint/period, or title-based fake type => **RED STOP**.

---

## P2 — REAL AS21 hierarchy/relation source discovery

This phase is mandatory before judging `task.hierarchy`.

### Find real hierarchy samples

Use bounded source discovery only.

Inspect raw `read_unit` payloads for tasks likely to have:
- parent/child relationship;
- epic relationship;
- linked/related/dependency relationship.

Start in a small/medium approved space or bounded sprint. Do not perform a tenant-wide scan.

For every relation-bearing sample capture:

- exact field location: top-level vs attribute;
- field code/name;
- raw value shape;
- parent key;
- epic key if present;
- linked/related task keys;
- task `suit`.

Compare those fields with:
`GET /api/v1/swtr-read/tasks/{key}/relations`.

Require the facade to preserve exact source keys. If the real relation field exists but the owner parser does not recognize it, classify the exact missing field and **RED STOP**. Do not add code.

### Maximum hierarchy depth — verify, do not assume

The owner has intentionally NOT encoded “10 levels”.

Try to find authoritative evidence for a maximum hierarchy depth from:
- MCP tool schema/metadata;
- source validation metadata/error contract;
- available AS21 source documentation exposed in the environment.

Also traverse several real parent chains and record the **deepest observed** depth.

Report separately:

- `DEEPEST_OBSERVED_DEPTH = N`
- `AUTHORITATIVE_MAX_DEPTH = N` only if explicitly proven
- otherwise `MAX_HIERARCHY_DEPTH_UNPROVEN`

A sample chain of depth <=10 is **not** proof that the platform maximum is 10.

Production safety cap 20 must remain classified only as an operational guard.

---

## P3 — exact parent / related-task skill

Choose at least 3 REAL tasks:
- one with a parent chain;
- one with linked/related tasks;
- one root/no-parent control where the source relation contract is still observable.

Queries should naturally express:
- `Покажи родительские задачи <KEY>`
- `Какие задачи связаны с <KEY>?`
- `Покажи иерархию <KEY>`

Run each 3 times.

Require:
- terminal skill = `task.hierarchy`;
- mode = `inspect`;
- exact parent chain order vs direct `read_unit` oracle;
- exact related keys;
- exact epic key only when source proves it or an ancestor is source-typed Epic;
- root correctly identified;
- no invented empty hierarchy when source relation schema is unobservable;
- cycle/ambiguity stays fail-closed;
- no statement that AS21 maximum depth is 10 unless P2 proved it authoritatively.

---

## P4 — group by epics

Find a bounded REAL corpus with <=200 tasks and at least one source-proven epic relationship.

Preferred scopes:
- one sprint;
- one person + space;
- one person + status + space.

Build an independent oracle by resolving the source parent/epic relation for every task in that bounded corpus.

Run:

1. `Сгруппируй задачи <person> в <space> по эпикам`
2. same scope + status;
3. same scope + one source-proven task type when available.

Require:
- terminal skill/capability = `task.hierarchy`, mode=`group_by_epic`;
- exact membership per epic;
- exact ungrouped/no-epic set;
- type/status/person/space constraints preserved;
- no task duplicated across groups;
- no task silently dropped;
- no local fallback;
- relation reads bounded to the selected corpus;
- >200 candidate control fails closed and asks for/naturally requires a narrower scope rather than scanning further.

If no bounded corpus with any real epic relation can be found after reasonable approved-space discovery, return **SOURCE_SAMPLE_BLOCKED_A229S1**, with evidence. Do not manufacture a GREEN.

---

## P5 — architecture audit

Require all:

- canonical 54 unchanged;
- exactly two intended extra skills added;
- 0 Agent Core/planner/runtime/session changes;
- task type authority = REAL AS21 `unit.suit`;
- no fixed list limiting valid source types;
- hierarchy authority = REAL AS21 point reads;
- 0 phrase-specific routing;
- 0 person/product/task-key hardcodes;
- 0 fake relations / fake type metrics;
- no tenant-wide scans;
- broad hierarchy fan-out capped at 200;
- hierarchy traversal safety cap 20 is not presented as AS21 business maximum;
- public/community repo not updated yet.

---

## P6 — retained regression

Re-run protected controls:

- simple assignee search;
- assignee + status;
- created-period + open;
- created-period + in-progress;
- sprint task collection;
- exact task lookup;
- task drawer description/intelligence smoke.

Require exact retained behavior and no new false zero.

---

## Verdict

Return exactly one primary verdict:

- `AGENT_CORE_V4_TASK_SEMANTICS_HIERARCHY_GREEN_A229S1`
- `AGENT_CORE_V4_TASK_SEMANTICS_HIERARCHY_RED_A229S1`
- `SOURCE_SAMPLE_BLOCKED_A229S1`

### GREEN requires

- P0 GREEN;
- task-type source contract independently proven;
- type skill composition exact on live source;
- real relation field contract proven;
- exact hierarchy skill proven on real parent/linked examples;
- epic grouping proven on at least one non-trivial real bounded corpus;
- P5/P6 GREEN.

If GREEN:
- recommend checkpoint `checkpoint/v4-task-semantics-hierarchy-green-a229s1`;
- owner may sync the certified delta to public/community;
- then resume A229R1 latency verification.

If RED:
- preserve the first failing boundary and STOP.

If SOURCE_SAMPLE_BLOCKED:
- show the bounded searches performed and why no real hierarchy/epic sample was available;
- do not modify code.

**GigaCode is QA only. Do not modify production code.**
