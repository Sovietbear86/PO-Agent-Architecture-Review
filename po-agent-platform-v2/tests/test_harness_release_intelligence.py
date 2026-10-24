import pytest

from po_agent.harness.contracts import HarnessRequest, ResponseStatus
from po_agent.harness.runtime import build_fake_runtime


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query,skill",
    [
        ("Покажи scope WMB-2024-Q3", "release-scope"),
        ("Покажи прогресс WMB-2024-Q3", "release-progress"),
        ("Покажи блокеры DMS-2024-Q3", "release-blockers"),
        ("Покажи зависимости WMB-2024-Q3", "release-dependencies"),
        ("Покажи риски релиза WMB-2024-Q3", "release-risk-queue"),
    ],
)
async def test_release_routes_are_executable(query, skill):
    response = await build_fake_runtime().process(HarnessRequest(query=query))
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == skill
    assert response.evidence


@pytest.mark.asyncio
async def test_release_progress_has_task_and_effort_completion():
    response = await build_fake_runtime().process(HarnessRequest(query="Покажи прогресс WMB-2024-Q3"))
    assert response.data["total"] == 3
    assert response.data["completed"] == 1
    assert response.data["task_completion_percent"] == 33.3
    assert response.data["estimated_hours_total"] == 26.0
    assert response.data["estimated_hours_completed"] == 8.0
    assert response.data["effort_completion_percent"] == 30.8


@pytest.mark.asyncio
async def test_release_blockers_are_grounded():
    response = await build_fake_runtime().process(HarnessRequest(query="Покажи блокеры DMS-2024-Q3"))
    assert response.data["count"] == 1
    assert response.data["tasks"][0]["key"] == "DMS-202"


@pytest.mark.asyncio
async def test_release_risk_queue_is_deterministic():
    response = await build_fake_runtime().process(HarnessRequest(query="Покажи риски релиза WMB-2024-Q3"))
    queue = response.data["risk_queue"]
    assert response.data["scoring_version"] == "release_risk_v1"
    assert queue[0]["task"]["key"] == "WMB-102"
    assert queue[0]["risk_score"] >= 30
