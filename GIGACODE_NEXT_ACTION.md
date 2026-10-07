# GigaCode — Current Action

## ACTIVE: Assignment A229S1R — Task semantics + hierarchy owner-fix re-gate

Role: QA/source-forensics/browser tester only. **Do not modify production code.**

Previous verdict:
`AGENT_CORE_V4_TASK_SEMANTICS_HIERARCHY_RED_A229S1`

Previous first failing boundary:
the relations facade incorrectly searched `read_unit` fields, while live AS21 relations are authoritative only through MCP `get_unit_links`.

Owner fix is now on current `feat/core8-real-query-hardening-v2`.

### Owner changes to verify

1. `/api/v1/swtr-read/tasks/{key}/relations`
   - uses MCP `get_unit_links`;
   - parses `content[].source/destination/type`;
   - `decomposition`: source=parent, destination=child;
   - `realized_in`: source=task, destination=epic/realization target;
   - other connected types, including source `dependend`, remain related;
   - reads all pages with a bounded pagination guard;
   - `read_unit` is used only for the task's own `suit`, not as relation authority.

2. `task.type_analysis`
   - person/person+space bounded scopes use the already-working assignee source path instead of the 502-prone full task-query scan;
   - status/type/period/text constraints remain composable.

3. False-positive unit test for the phrase about “10 hierarchy levels” is corrected. No production rule of 10 was added.

4. Agent Core remains byte-identical to checkpoint and canonical 54 remains unchanged.

---

## P0 — integrity/regression

- record START_HEAD and clean worktree;
- prove Core/planner/runtime/session byte identity vs `checkpoint/v4-task-details-richtext-green-a229u2r`;
- prove canonical 54/54 unchanged and the 2 skills remain extras;
- run focused tests for task catalog, task semantics/hierarchy, Task API adapter, SWTR assignee canonicalization and SWTR relations;
- run full V4 blast-radius + frontend build.

Any Core diff or retained regression => RED STOP.

---

## P1 — task.type_analysis re-gate

Reuse the REAL source inventory already discovered in A229S1:
- DMS `bug / Дефект`
- DMS `epic / Эпик`
- DMS `task / Задача`
- WMB `task_wmb_v3 / Task (Управленческие задачи)`

Run live agent tests for:
1. type distribution for a real person+space;
2. exact source type + person+space;
3. source type + person+space+status;
4. one additional constraint: sprint or created_period when a non-empty oracle exists.

For every case build an independent direct-source oracle.

Require:
- terminal skill `task.type_analysis`;
- no task-query 502 for person-scoped cases;
- exact task-key/count parity;
- exact type code/name;
- every constraint preserved;
- no title/label inference;
- no local fallback or tenant-wide scan.

---

## P2 — relations facade re-gate

Use the same live oracle examples from A229S1:

- `DMS-253`
- `CRPV-90180`
- `DMS-267`

Directly call MCP `get_unit_links` and compare with:
`GET /api/v1/swtr-read/tasks/{key}/relations`.

Require exact preservation of:
- source/destination;
- link type;
- parent candidates;
- epic candidates;
- related keys;
- incoming/outgoing direction.

Known live evidence to re-check, not hardcode:
- CRPV-90180 → DMS-253 `decomposition`;
- DMS-253 → DMS-267 `decomposition`;
- DMS-253 → DMS-349 `realized_in`;
- dependency type observed as source spelling `dependend`.

Also verify a source-proven root/no-parent task.

Pagination:
- verify the route cannot silently truncate links;
- if `hasNext=true`, next pages must be read;
- operational max-pages guard must fail closed rather than return a partial hierarchy.

---

## P3 — live task.hierarchy

Run at least 3 times each:

1. `Покажи иерархию DMS-267`
2. `Покажи родительские задачи DMS-267`
3. `Какие задачи связаны с DMS-253?`

Require:
- terminal skill `task.hierarchy`;
- mode `inspect`;
- exact parent chain vs independent `get_unit_links` oracle;
- expected observed chain includes `CRPV-90180 → DMS-253 → DMS-267` if still present in live source;
- linked tasks exact;
- epic only when source semantics/type prove it;
- no duplicate structural nodes in generic related set;
- no fabricated empty relations.

Hierarchy depth:
- report `DEEPEST_OBSERVED_DEPTH`;
- keep `MAX_HIERARCHY_DEPTH_UNPROVEN` unless authoritative schema/metadata proves a maximum;
- safety cap 20 is not a product maximum.

---

## P4 — group by epics

Find a bounded live corpus <=200 tasks containing source-proven hierarchy.

Run:
1. person+space grouped by epic;
2. same + status;
3. same + source task type when available.

Build independent oracle using `get_unit_links` for every candidate.

Require exact:
- group membership;
- no-epic set;
- counts;
- no duplicates/drops;
- preservation of person/space/status/type;
- bounded point reads only.

>200 candidate control must fail closed/narrow scope.

---

## P5 — retained + architecture audit

Require:
- Core byte-identical;
- canonical 54 unchanged;
- exactly 2 extra skills;
- hierarchy authority = MCP `get_unit_links`;
- task type authority = `unit.suit`;
- no phrase routing/hardcoded people/products/task IDs/type inventory;
- no local fallback;
- no tenant-wide scans;
- no fake relation/type metrics;
- public/community still untouched.

Re-run protected controls:
- simple assignee;
- assignee+status;
- created-period open/in-progress;
- sprint tasks;
- exact lookup;
- task drawer description/intelligence smoke.

---

## Verdict

Return exactly one:

- `AGENT_CORE_V4_TASK_SEMANTICS_HIERARCHY_GREEN_A229S1R`
- `AGENT_CORE_V4_TASK_SEMANTICS_HIERARCHY_RED_A229S1R`
- `SOURCE_SAMPLE_BLOCKED_A229S1R`

GREEN requires P0-P5 GREEN.

If GREEN:
- recommend checkpoint `checkpoint/v4-task-semantics-hierarchy-green-a229s1r`;
- owner may then sync the certified delta to public/community;
- next assignment returns to A229R1 latency verification.

If RED: preserve first failing boundary and STOP.

**GigaCode is QA only. Do not modify production code.**
