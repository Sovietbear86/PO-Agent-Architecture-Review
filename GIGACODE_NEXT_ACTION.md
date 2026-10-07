# GigaCode — Current Action

## ACTIVE: Assignment A229S1R1 — Task type + hierarchy owner-fix re-gate

Role: QA/source-forensics/browser tester only. **Do not modify production code.**

Previous result:
- A229S1 = RED
- first failing boundary = P2
- root cause = relations facade used `read_unit` field-name heuristics while REAL AS21 hierarchy lives in MCP `get_unit_links`.

Owner fix now applied:
1. `/api/v1/swtr-read/tasks/{key}/relations` uses authoritative MCP `get_unit_links`.
2. Source-proven link semantics:
   - `decomposition`: source = structural parent, destination = child;
   - `realized_in`: source points to epic target; treat as epic relation, NOT structural parent;
   - other link types = related.
3. Empty complete `get_unit_links` response is now a proven empty relation set.
4. task type composition now uses direct bounded `assignee-tasks` for person-scoped analysis instead of the generic task-query path.
5. Naive "10 hierarchy levels" test fixed; 10 remains UNPROVEN. Safety cap 20 is operational only.

Keep Agent Core V4 frozen and canonical 54 unchanged.

---

## P0 — integrity / focused regression

1. Pull latest `feat/core8-real-query-hardening-v2`.
2. Record START_HEAD and clean worktree.
3. Prove byte identity vs checkpoint `checkpoint/v4-task-details-richtext-green-a229u2r@be5131c83b7fd666c79af0e69e1b5cefd0961e62` for Core/planner/runtime/session files.
4. Prove canonical 54/54 unchanged; `task.type_analysis` and `task.hierarchy` remain extra plugin skills.
5. Run:
   - `test_agent_core_v4_task_catalog.py`
   - `test_agent_core_v4_task_semantics_hierarchy.py`
   - `test_task_api_as21_adapter.py`
   - `task-api/tests/test_swtr_assignee_canonical.py`
   - `task-api/tests/test_swtr_task_relations.py`
6. Full V4 blast + frontend build.
7. First product regression => RED STOP.

---

## P1 — task type re-gate

Re-use the previously discovered REAL AS21 type source:
- `unit.suit` is authoritative;
- observed examples include `bug/Дефект`, `epic/Эпик`, `task/Задача`, `task_wmb_v3/Task (Управленческие задачи)`.

Run live Agent/Oracle B tests using source-proven examples:

A. distribution: `Покажи распределение типов задач <person> в <space>`
B. type + person + space
C. type + person + status + space
D. type + person + another certified constraint where a non-empty oracle exists.

Require:
- terminal skill/capability = `task.type_analysis`;
- exact type code/name and task-key parity;
- direct person-bounded source path, no broad space scan;
- all user constraints preserved in one capability;
- unknown source-defined type remains generic;
- no title-tag inference.

Any task-query 502 caused by broad scan for a person-scoped request => RED STOP.

---

## P2 — authoritative relations facade re-gate

Use the same source-proven controls from A229S1:

### DMS-253
Expected direct MCP facts include:
- incoming `CRPV-90180 -> DMS-253 (decomposition)` => structural parent `CRPV-90180`;
- outgoing decomposition children including DMS-453, DMS-403, DMS-331, DMS-348, DMS-337, DMS-336, DMS-275, DMS-267, DMS-266, DMS-265, DMS-264;
- incoming `CRPV-90180 -> DMS-253 (realized_in)` is NOT a structural parent/epic of DMS-253; it is a related realized child from DMS-253's perspective.

### CRPV-90180
Expected:
- `CRPV-90180 -> DMS-253 (decomposition)` => DMS-253 is child/related, not parent;
- `CRPV-90180 -> DMS-253 (realized_in)` => epic relation `DMS-253`;
- `CRPV-90180 -> CRPV-154341 (dependend)` => related/dependency.

### DMS-267
Expected:
- `DMS-253 -> DMS-267 (decomposition)` => parent = DMS-253.

Call both:
- direct MCP `get_unit_links`;
- `GET /api/v1/swtr-read/tasks/{key}/relations`.

Require exact parity for:
- parent_key;
- epic_key;
- related_keys;
- relation type + direction;
- deleted links excluded;
- `relation_source = mcp:get_unit_links`;
- empty-control relation endpoint remains `schema_proven=true`, not unknown.

No `read_unit` relation-field heuristic may contribute parent/epic/related facts.

---

## P3 — hierarchy skill

Run each at least 3 times:
- `Покажи родительские задачи DMS-267`
- `Какие задачи связаны с DMS-253?`
- `Покажи иерархию DMS-267`

Require:
- terminal skill = `task.hierarchy`;
- mode = inspect;
- exact chain DMS-267 -> DMS-253 -> CRPV-90180 when supported by current live links;
- DMS-253 recognized as Epic from source suit when encountered as ancestor;
- exact one-hop related keys;
- no cycles invented from coexistence of `decomposition` and `realized_in`;
- root correct;
- max hierarchy remains `UNPROVEN`; deepest observed reported separately.

If current source data changed, build Oracle B from live MCP at test time and compare to that, not to stale counts.

---

## P4 — group by epic

Find a bounded source-backed corpus <=200 tasks with a real epic relationship.

Run:
1. group by epic for person + space;
2. same + status;
3. same + source task type if available.

Require:
- terminal capability = `task.hierarchy`, mode=group_by_epic;
- exact membership per epic vs independently traversed MCP oracle;
- exact NO_EPIC set;
- no duplication/drop;
- person/status/type/space all preserved;
- relation fan-out <=200;
- >200 control fails closed.

---

## P5 — retained architecture/regression

Require all:
- canonical 54 unchanged;
- 2 intended extra skills only;
- 0 Core/planner/runtime/session changes;
- type source = REAL AS21 `unit.suit`;
- hierarchy source = REAL AS21 `get_unit_links`;
- 0 hardcoded person/product/task keys in production;
- 0 phrase router;
- no tenant-wide scans;
- safety traversal cap 20 not claimed as AS21 maximum;
- public/community still not synced.

Re-run protected controls:
- assignee;
- assignee + status;
- created-period + open;
- created-period + in-progress;
- sprint task collection;
- exact task lookup;
- task drawer rich description.

---

## Verdict

Return exactly one:
- `AGENT_CORE_V4_TASK_SEMANTICS_HIERARCHY_GREEN_A229S1R1`
- `AGENT_CORE_V4_TASK_SEMANTICS_HIERARCHY_RED_A229S1R1`
- `SOURCE_SAMPLE_BLOCKED_A229S1R1`

GREEN requires P0-P5 all GREEN.

If GREEN:
- recommend checkpoint `checkpoint/v4-task-semantics-hierarchy-green-a229s1r1`;
- owner may sync certified changes to public/community;
- then resume A229R1 latency verification.

If RED:
- preserve first failing boundary and STOP.

**GigaCode is QA only. Do not modify production code.**
