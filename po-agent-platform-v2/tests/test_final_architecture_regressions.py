import httpx
import pytest

from po_agent.harness import HarnessRequest, ResponseStatus
from po_agent.harness.runtime_factory import build_runtime_bundle


@pytest.mark.asyncio
async def test_runtime_factory_runtime_records_production_execution_history():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    bundle = build_runtime_bundle("task-api")
    bundle.adapter._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://task-api"
    )
    response = await bundle.runtime.process(HarnessRequest(query="Найди login", session_id="prod-history"))
    record = bundle.runtime.history.get(response.trace_id)
    await bundle.adapter._client.aclose()

    assert response.status is ResponseStatus.COMPLETED
    assert record is not None
    assert record.session_id == "prod-history"
    assert record.request == "Найди login"
    assert record.skill_id == "task-search"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "fact"),
    [
        ("Покажи историю WMB-101", "history"),
        ("Найди PDF вложения", "attachments"),
        ("Покажи carryover DMS-SPRNT-1", "sprint_snapshots"),
        ("Кто подходит для задачи WMB-101 по компетенциям?", "team_competencies"),
        ("Прогноз релиза WMB-2026-Q3", "release_timeline"),
    ],
)
async def test_source_dependent_request_cannot_be_reinterpreted_when_fact_is_missing(query, fact):
    bundle = build_runtime_bundle("task-api", team_config_path="/definitely/missing/team.yaml")
    response = await bundle.runtime.process(HarnessRequest(query=query, session_id="source-gate"))

    assert response.status is ResponseStatus.FAILED
    assert response.warnings == ["source_capability_unavailable"]
    assert response.data["missing_source_fact"] == fact
    assert bundle.runtime.history.get(response.trace_id) is not None


@pytest.mark.asyncio
async def test_portfolio_overview_never_labels_task_api_data_as_fake():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    bundle = build_runtime_bundle("task-api")
    bundle.adapter._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://task-api"
    )
    response = await bundle.runtime.process(HarnessRequest(query="Обзор"))
    await bundle.adapter._client.aclose()

    assert response.status is ResponseStatus.COMPLETED
    assert response.data["adapter"] == "task-api"
