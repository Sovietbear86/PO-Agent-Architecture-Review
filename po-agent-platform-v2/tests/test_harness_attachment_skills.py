import pytest

from po_agent.harness import HarnessRequest, ResponseStatus, build_fake_runtime


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "skill_id", "expected_task", "expected_type"),
    [
        ("Найди задачи с Excel вложением", "task-search-excel", "WMB-101", "excel"),
        ("Найди задачи с PDF файлом", "task-search-pdf", "DMS-201", "pdf"),
        ("Найди задачи с MSG вложением", "task-search-msg", "DMS-202", "msg"),
    ],
)
async def test_typed_attachment_search(query, skill_id, expected_task, expected_type):
    response = await build_fake_runtime().process(HarnessRequest(query=query))

    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == skill_id
    assert response.data["attachment_type"] == expected_type
    assert response.data["count"] == 1
    assert response.data["results"][0]["task"]["key"] == expected_task
    assert response.data["results"][0]["attachments"][0]["type"] == expected_type
    assert response.evidence[0].type == "attachment"


@pytest.mark.asyncio
async def test_generic_attachment_search_returns_all_fixture_attachment_tasks():
    response = await build_fake_runtime().process(HarnessRequest(query="Найди задачи с вложениями"))

    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "task-search-attachments"
    assert response.data["count"] == 4
    assert {item["task"]["key"] for item in response.data["results"]} == {
        "WMB-101", "WMB-102", "DMS-201", "DMS-202"
    }
    assert len(response.evidence) == 4
