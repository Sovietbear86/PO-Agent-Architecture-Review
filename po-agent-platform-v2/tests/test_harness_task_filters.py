import pytest

from po_agent.harness import HarnessRequest, ResponseStatus, build_fake_runtime


@pytest.mark.asyncio
async def test_search_by_assignee_uses_executable_skill():
    response = await build_fake_runtime().process(
        HarnessRequest(query="Покажи задачи исполнителя Ivanov.I.I")
    )
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "task-search-assignee"
    assert response.data["count"] == 1
    assert response.data["tasks"][0]["key"] == "WMB-101"
    assert response.evidence


@pytest.mark.asyncio
async def test_search_by_status_is_deterministic():
    response = await build_fake_runtime().process(
        HarnessRequest(query="Покажи задачи в статусе In progress")
    )
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "task-search-status"
    assert response.data["count"] == 1
    assert response.data["tasks"][0]["key"] == "WMB-102"


@pytest.mark.asyncio
async def test_search_tasks_in_sprint_does_not_become_sprint_health():
    response = await build_fake_runtime().process(
        HarnessRequest(query="Покажи задачи спринта WMB-SPRNT-1")
    )
    assert response.skill_id == "task-search-sprint"
    assert response.data["count"] == 2
    assert {task["key"] for task in response.data["tasks"]} == {"WMB-101", "WMB-102"}


@pytest.mark.asyncio
async def test_plain_sprint_health_still_uses_health_skill():
    response = await build_fake_runtime().process(
        HarnessRequest(query="Как идет WMB-SPRNT-1")
    )
    assert response.skill_id == "sprint-health"
    assert response.data["total"] == 2


@pytest.mark.asyncio
async def test_search_tasks_in_release_does_not_become_release_health():
    response = await build_fake_runtime().process(
        HarnessRequest(query="Покажи состав задач WMB-2024-Q3")
    )
    assert response.skill_id == "task-search-release"
    assert response.data["count"] == 3


@pytest.mark.asyncio
async def test_search_by_product_uses_adapter_project_filter():
    response = await build_fake_runtime().process(
        HarnessRequest(query="Покажи задачи в продукте DMS")
    )
    assert response.skill_id == "task-search-product"
    assert response.data["count"] == 2
    assert {task["key"] for task in response.data["tasks"]} == {"DMS-201", "DMS-202"}
