import json

import httpx
import pytest

from po_agent.adapters.hardened_production_task_api import HardenedProductionTaskApiAS21Adapter
from po_agent.harness.contracts import HarnessRequest, HarnessResponse, ResponseStatus
from po_agent.harness.correction_runtime import CorrectionAwareHarnessRuntime


def task_row(code: str, login: str = "Garanin.R.V"):
    return {
        "id": code,
        "source_id": code,
        "title": f"Task {code}",
        "description": "demo",
        "assignee": "Гаранин Родион",
        "status": "in_progress",
        "created_at": "2026-08-01T10:00:00+03:00",
        "updated_at": "2026-08-20T10:00:00+03:00",
        "source": "swtr",
        "source_data": {
            "workflow_status": "in_progress",
            "swtr_attributes": [
                {
                    "code": "assigned_to",
                    "value": {
                        "externalId": login,
                        "login": login,
                        "lastName": "Гаранин",
                        "firstName": "Родион",
                    },
                }
            ],
        },
        "sprint": None,
    }


@pytest.mark.asyncio
async def test_live_sprint_membership_joins_by_task_key_not_missing_cached_sprint():
    rows = [task_row("DMS-101"), task_row("DMS-102")]

    async def handler(request: httpx.Request):
        if request.url.path == "/api/v1/tasks":
            return httpx.Response(200, json=rows)
        if request.url.path == "/api/v1/swtr-read/sprints/DMS-SPRNT-2/tasks":
            return httpx.Response(
                200,
                json={
                    "complete": True,
                    "tasks": {"content": [{"unit": {"code": "DMS-101"}}, {"unit": {"code": "DMS-102"}}]},
                },
            )
        raise AssertionError(f"unexpected request: {request.url}")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = HardenedProductionTaskApiAS21Adapter(client=client)
    tasks = await adapter.get_sprint_tasks("DMS-SPRNT-2", space="DMS")
    assert [task.key for task in tasks] == ["DMS-101", "DMS-102"]
    assert all(task.sprint_id == "DMS-SPRNT-2" for task in tasks)
    assert all(task.project_space == "DMS" for task in tasks)
    await client.aclose()


@pytest.mark.asyncio
async def test_project_filter_hydrates_raw_space_when_cache_dropped_relation():
    rows = [task_row("DMS-101"), task_row("OLP-999", login="Other.User")]

    async def handler(request: httpx.Request):
        if request.url.path == "/api/v1/tasks":
            return httpx.Response(200, json=rows)
        if request.url.path == "/api/v1/swtr-read/tasks/DMS-101":
            return httpx.Response(
                200,
                json={
                    "task_code": "DMS-101",
                    "unit": {
                        "code": "DMS-101",
                        "summary": "Task DMS-101",
                        "space": {"code": "DMS"},
                        "attributes": [],
                    },
                },
            )
        raise AssertionError(f"unexpected request: {request.url}")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = HardenedProductionTaskApiAS21Adapter(client=client)
    tasks = await adapter.search_tasks('project = DMS AND assignee = Garanin.R.V', max_results=100)
    assert [task.key for task in tasks] == ["DMS-101"]
    assert tasks[0].project_space == "DMS"
    await client.aclose()


class CountingRuntime:
    def __init__(self):
        self.calls = []

    async def process(self, request: HarnessRequest):
        self.calls.append(request.query)
        return HarnessResponse(
            status=ResponseStatus.COMPLETED,
            trace_id=f"trace-{len(self.calls)}",
            session_id=request.session_id or "s",
            answer="0 tasks",
            data={"count": 0},
        )


@pytest.mark.asyncio
async def test_negative_feedback_forces_recheck_then_targeted_clarification():
    inner = CountingRuntime()
    runtime = CorrectionAwareHarnessRuntime(inner)
    query = "Покажи открытые задачи Гаранина в последнем спринте по DMS"
    await runtime.process(HarnessRequest(query=query, session_id="s1"))
    response = await runtime.process(HarnessRequest(query="Ты не прав, проверь ещё раз", session_id="s1"))
    assert len(inner.calls) == 2
    assert inner.calls[-1] == query
    assert response.status == ResponseStatus.NEEDS_CLARIFICATION
    assert "открытыми" in response.question
    assert "последним спринтом" in response.question
    assert response.data["_harness"]["correction"]["source_recheck_performed"] is True
    assert response.data["_harness"]["correction"]["persistent_skill_mutation"] is False


@pytest.mark.asyncio
async def test_explicit_correction_rechecks_and_preserves_original_query_context():
    inner = CountingRuntime()
    runtime = CorrectionAwareHarnessRuntime(inner)
    query = "Покажи открытые задачи Гаранина в последнем спринте по DMS"
    await runtime.process(HarnessRequest(query=query, session_id="s2"))
    response = await runtime.process(
        HarnessRequest(
            query="Ты не прав. У Гаранина точно есть задачи в DMS-SPRNT-1 и DMS-SPRNT-2. Проверь через спринты.",
            session_id="s2",
        )
    )
    assert len(inner.calls) == 3  # initial + fresh recheck + corrected execution
    assert query in inner.calls[-1]
    assert "DMS-SPRNT-1" in inner.calls[-1]
    assert response.data["_harness"]["correction"]["negative_feedback"] is True
    assert response.data["_harness"]["correction"]["persistent_skill_mutation"] is False
