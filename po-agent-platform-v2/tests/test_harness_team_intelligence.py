import pytest
from po_agent.harness.contracts import HarnessRequest, ResponseStatus
from po_agent.harness.runtime import build_fake_runtime

@pytest.mark.asyncio
@pytest.mark.parametrize("query,skill", [
    ("Покажи нагрузку команды", "team-workload"),
    ("Покажи WIP команды", "team-wip"),
    ("Покажи блокировки команды", "team-blocked"),
    ("Покажи capacity команды 40 часов", "team-capacity"),
    ("Покажи узкие места команды", "team-bottlenecks"),
    ("Покажи распределение задач команды", "team-distribution"),
])
async def test_team_routes_are_executable(query, skill):
    response = await build_fake_runtime().process(HarnessRequest(query=query))
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == skill
    assert response.evidence

@pytest.mark.asyncio
async def test_team_wip_is_grounded_in_active_work():
    response = await build_fake_runtime().process(HarnessRequest(query="Покажи WIP команды"))
    assert response.data["total_wip"] == 1
    assert response.data["by_member"][0]["member"] == "Sidorov.S.S"

@pytest.mark.asyncio
async def test_team_blocked_finds_waiting_task():
    response = await build_fake_runtime().process(HarnessRequest(query="Покажи блокировки команды"))
    assert response.data["total_blocked"] == 1
    assert "DMS-202" in response.data["tasks"]

@pytest.mark.asyncio
async def test_team_capacity_exposes_configured_baseline_warning():
    response = await build_fake_runtime().process(HarnessRequest(query="Покажи capacity команды 40 часов"))
    assert response.data["capacity_hours_per_member"] == 40.0
    assert "configured_capacity_baseline" in response.warnings
