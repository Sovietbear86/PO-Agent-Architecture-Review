# GigaCode — Current Action

## ACTIVE: Assignment A229S1R2 — Task semantics + hierarchy DTO re-gate

Role: QA/source-forensics/browser tester only. **Do not modify production code.**

Previous verdict:
`AGENT_CORE_V4_TASK_SEMANTICS_HIERARCHY_RED_A229S1R`

Previous first failing boundary:
`_get_unit_links_complete()` called live MCP `get_unit_links` with the wrong nested DTO and the relations facade returned HTTP 502.

Owner fix is now on current `feat/core8-real-query-hardening-v2`.

### Owner changes to verify

1. `_get_unit_links_complete()` now sends the live-proven flat `GetUnitLinksRequest`:
   - `unit_code`
   - `link_types`
   - `page: int`
   - `size: int`
2. Nested `unitId/type/page.page` request shape is gone.
3. Regression tests now exercise the actual helper call arguments and pagination, not only the pure relation parser.
4. Relation semantics remain unchanged:
   - `decomposition`: source=parent, destination=child;
   - `realized_in`: source task -> epic/realization target;
   - other connected types, including `dependend`, remain related.
5. Agent Core must remain byte-identical; canonical 54 must remain unchanged.

---

## P0 — integrity + focused regression

Record START_HEAD and clean worktree.

Prove Core/planner/runtime/session byte identity vs:
`checkpoint/v4-task-details-richtext-green-a229u2r`.

Run at minimum:
- `task-api/tests/test_swtr_task_relations.py`
- task semantics/hierarchy focused tests
- Task API adapter tests
- SWTR assignee canonicalization tests
- full V4 blast-radius
- frontend build

Require:
- new flat-DTO regression tests GREEN;
- no Core diff;
- canonical 54/54 unchanged;
- exactly 2 extra skills remain `task.type_analysis` and `task.hierarchy`.

Any Core diff or retained regression => RED STOP.

---

## P2 FIRST — live relations facade contract re-gate

Run this before P1/P3/P4 because it was the previous first failing boundary.

For each of:
- `DMS-253`
- `CRPV-90180`
- `DMS-267`

A/B compare:

A. direct MCP `get_unit_links` using the **live schema-proven flat request**:
```json
{
  "request": {
    "unit_code": "<TASK>",
    "link_types": [],
    "page": 0,
    "size": 100
  }
}
```

B. `GET /api/v1/swtr-read/tasks/{key}/relations`

Require:
- no HTTP 502;
- exact source/destination;
- exact link type;
- exact parent candidates;
- exact epic candidates;
- exact related keys;
- exact incoming/outgoing direction.

Re-check live evidence, do not hardcode it as truth:
- `CRPV-90180 -> DMS-253` decomposition;
- `DMS-253 -> DMS-267` decomposition;
- `DMS-253 -> DMS-349` realized_in;
- dependency spelling observed as `dependend`.

Also verify:
- one source-proven root/no-parent task;
- pagination cannot silently truncate;
- if `hasNext=true`, pages advance as flat integer `page=0,1,...`;
- max-pages guard fails closed rather than returning partial hierarchy.

If P2 RED, preserve first failing boundary and STOP.

---

## P1 — task.type_analysis re-gate

Reuse source inventory already proven:
- DMS `bug / Дефект`
- DMS `epic / Эпик`
- DMS `task / Задача`
- WMB `task_wmb_v3 / Task (Управленческие задачи)`

Run live agent cases:
1. type distribution for real person+space;
2. exact source type + person+space;
3. source type + person+space+status;
4. one extra constraint: sprint or created_period with a non-empty oracle.

Independent direct-source oracle for every case.

Require:
- terminal skill `task.type_analysis`;
- no task-query 502 for person-scoped cases;
- exact task-key/count parity;
- exact source type code/name;
- all constraints preserved;
- no title/label inference;
- no local fallback;
- no tenant-wide scan.

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
- expected observed chain includes `CRPV-90180 -> DMS-253 -> DMS-267` only if still present live;
- linked tasks exact;
- epic only when source semantics/type prove it;
- no duplicate structural nodes in generic related set;
- no fabricated empty relations.

Report:
- `DEEPEST_OBSERVED_DEPTH`;
- `MAX_HIERARCHY_DEPTH_UNPROVEN` unless authoritative schema/metadata proves a maximum;
- safety cap 20 is operational only, not a product maximum.

---

## P4 — group by epics

Find bounded live corpus <=200 tasks containing source-proven hierarchy.

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
- person/space/status/type preservation;
- bounded point reads only.

>200 candidate control must fail closed / require narrower scope.

---

## P5 — retained + architecture audit

Require:
- Core byte-identical;
- canonical 54 unchanged;
- exactly 2 extra skills;
- hierarchy authority = MCP `get_unit_links`;
- task type authority = `unit.suit`;
- no phrase routing;
- no hardcoded people/products/task IDs/type inventories;
- no local fallback;
- no tenant-wide scans;
- no fake relation/type metrics;
- public/community repo still untouched.

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

- `AGENT_CORE_V4_TASK_SEMANTICS_HIERARCHY_GREEN_A229S1R2`
- `AGENT_CORE_V4_TASK_SEMANTICS_HIERARCHY_RED_A229S1R2`
- `SOURCE_SAMPLE_BLOCKED_A229S1R2`

GREEN requires P0 + P2 + P1 + P3 + P4 + P5 GREEN.

If GREEN:
- recommend checkpoint `checkpoint/v4-task-semantics-hierarchy-green-a229s1r2`;
- owner may then sync the certified delta to public/community;
- next assignment returns to A229R1 latency verification.

If RED:
- preserve the first failing boundary;
- STOP;
- do not modify production code.

**GigaCode is QA only. Do not modify production code.**
