# AS21 Source Contract Architecture Review

## Scope

Review of the pre-Harness SWTR/AS21 integration versus the current Harness production adapter, with learning-loop work intentionally excluded until source correctness is restored.

## Historical baseline

The earliest PO Agent integration commit inspected was:

- `6b3bee08c920f5ea32083313481385eb06935b48` — `feat: add PO Agent Tools - Task tracker with team analytics`

Its `task-api/src/s21_agent/connectors/s21_swtr_adapter.py` used an explicit filter contract:

```python
params = {"q": query, "limit": settings.max_results}
if filters:
    if "status" in filters:
        params["status"] = filters["status"]
    if "assignee" in filters:
        params["assignee"] = filters["assignee"]
    if "source" in filters:
        params["source"] = filters["source"]
```

The old Team Performance Agent extracted a team member from natural language and passed the resolved login into the task retrieval layer. Therefore assignee filtering happened as an explicit source filter, not by expecting task-api to understand arbitrary JQL.

The old mapper also preserved SWTR-specific source facts in `source_data`, including at least:

- `swtr_code`
- `swtr_summary`
- `swtr_space`
- `workflow_status`
- `priority`
- `assignee`
- source timestamps

## Current task-api contract

`task-api/app/routers/tasks.py` currently exposes:

```python
GET /api/v1/tasks/
    status: optional
    assignee: optional
    source: optional
    limit: int
    offset: int
```

There is **no `q` parameter** and no JQL parser in this endpoint.

This is the critical architectural fact.

## Regression introduced during Harness migration

The current production Harness adapter (`po-agent-platform-v2/src/po_agent/adapters/task_api.py`) previously did:

```python
response = await client.get(
    "/api/v1/tasks",
    params={"q": query, "limit": limit},
)
```

FastAPI ignores unknown query parameters by default. Consequently a request such as:

```text
assignee = Kalachanov.V.V
```

could become:

```text
GET /api/v1/tasks?q=assignee%20%3D%20Kalachanov.V.V&limit=50
```

and task-api would return an unfiltered list.

This exactly explains the observed behaviour where queries mentioning an assignee either returned zero after later semantic filtering or returned all WMB tasks without assignee filtering.

## Second regression: canonical attribute loss

The Harness migration also changed the domain boundary from the old S21 `Task` model to the canonical `po_agent.domain.models.Task`.

The legacy mapping path retained only a subset of source facts. In particular, the production boundary could lose or fail to populate:

- `assignee_id`
- `sprint_id`
- `release_id`
- `components`
- explicit `labels`
- `priority`
- `estimate_hours`

This weakens entity grounding and makes later Harness layers appear to have an NLP/learning problem when the source facts are actually missing.

## Architectural correction

Branch:

`feat/restore-as21-source-contract-v1`

The production `TaskApiAS21Adapter` now:

1. Never assumes `/api/v1/tasks` understands `q` or JQL.
2. Parses the small JQL-like subset used internally by Harness.
3. Sends native task-api filters (`assignee`, `source`) as explicit query parameters.
4. Performs unsupported filters (space/project, sprint, release, status, key, free text) deterministically after one bounded read.
5. Uses fail-closed semantics for malformed transport/payloads.
6. Restores canonical mapping of `assignee_id`, `sprint_id`, `release_id`, labels, components, priority and estimate.
7. Prevents unknown/mixed query clauses from silently broadening results.
8. Keeps source reads bounded to task-api's current maximum (`10_000`).

## Why learning loop is paused

A learning loop must not learn around a broken source boundary. If an assignee/source fact is absent or incorrectly filtered, feedback memory would encode compensating heuristics for a transport/mapping bug. That would make the system harder to reason about and could create false-green behaviour.

Source correctness must therefore be proven first.

## Required verification before returning to learning loop

### Unit/contract tests

Run:

```bash
cd po-agent-platform-v2
pytest -q tests/test_task_api_source_contract.py
pytest -q tests/test_as21_adapter.py
```

Then run the normal production/Harness regression suites used on the current branch.

### Real AS21 smoke tests

With task-api on `localhost:8003` and real SWTR data loaded, verify at least:

1. Exact task lookup for a known WMB task.
2. `assignee = <login>` returns only that assignee's tasks.
3. `project = WMB` returns only WMB tasks.
4. `project = WMB AND sprint = <real sprint>` returns the correct subset.
5. `status = Closed` returns only canonical Closed tasks.
6. A task object preserves `assignee`, `assignee_id`, `sprint_id`, `release_id`, priority and source metadata when present.
7. No `q` parameter is sent to `/api/v1/tasks` by the Harness production adapter.
8. Source outage produces an error, never an empty-success result.

### Regression gate

Do not resume learning-loop changes until:

```text
AS21_SOURCE_CONTRACT = GREEN
ASSIGNEE_FILTERING = GREEN
ATTRIBUTE_MAPPING = GREEN
NEW_CODE_REGRESSIONS_VS_BASE = 0
```

## Architectural conclusion

The observed defect is not primarily a learning-loop defect. The primary regression is a contract mismatch between the new Harness adapter and the unchanged task-api endpoint, compounded by loss of canonical AS21 attributes during mapping.

The correct architecture is:

```text
AS21/SWTR
   -> existing task-api source/sync boundary
   -> explicit task-api filters + canonical mapping
   -> Harness source adapter
   -> entity grounding / capabilities
   -> dialogue
   -> learning/evolution
```

Learning/evolution must remain downstream of a deterministic, source-correct AS21 boundary.
