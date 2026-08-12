import pytest

from po_agent.harness import HarnessRequest, ResponseStatus, build_fake_runtime


@pytest.mark.asyncio
async def test_current_sprint_is_resolved_from_source_task_metadata():
    response = await build_fake_runtime().process(HarnessRequest(query="Текущий спринт в продукте WMB"))
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "sprint-current"
    assert response.data["sprint_id"] == "WMB-SPRNT-2"
    assert response.evidence


@pytest.mark.asyncio
async def test_sprint_scope_is_source_grounded():
    response = await build_fake_runtime().process(HarnessRequest(query="Покажи scope WMB-SPRNT-1"))
    assert response.skill_id == "sprint-scope"
    assert response.data["count"] == 2
    assert {item["key"] for item in response.data["tasks"]} == {"WMB-101", "WMB-102"}
    assert all(item.type == "sprint_scope_task" for item in response.evidence)


@pytest.mark.asyncio
async def test_velocity_uses_explicit_estimate_unit_and_deterministic_values():
    response = await build_fake_runtime().process(HarnessRequest(query="Velocity WMB-SPRNT-1"))
    assert response.skill_id == "sprint-velocity"
    assert response.data["unit"] == "hours"
    assert response.data["committed"] == 13
    assert response.data["velocity"] == 8


@pytest.mark.asyncio
async def test_throughput_and_wip_are_task_count_metrics():
    runtime = build_fake_runtime()
    throughput = await runtime.process(HarnessRequest(query="Throughput WMB-SPRNT-1"))
    wip = await runtime.process(HarnessRequest(query="WIP WMB-SPRNT-1"))
    assert throughput.skill_id == "sprint-throughput"
    assert throughput.data["throughput_tasks"] == 1
    assert throughput.data["unit"] == "tasks"
    assert wip.skill_id == "sprint-wip"
    assert wip.data["wip"] == 1


@pytest.mark.asyncio
async def test_cycle_and_lead_time_use_completion_history_not_llm():
    runtime = build_fake_runtime()
    cycle = await runtime.process(HarnessRequest(query="Cycle time WMB-SPRNT-1"))
    lead = await runtime.process(HarnessRequest(query="Lead time WMB-SPRNT-1"))
    assert cycle.skill_id == "sprint-cycle-time"
    assert cycle.data["unit"] == "hours"
    assert cycle.data["sample_size"] == 1
    assert cycle.data["average_hours"] == 168.0
    assert lead.skill_id == "sprint-lead-time"
    assert lead.data["sample_size"] == 1
    assert lead.data["average_hours"] == 216.0


@pytest.mark.asyncio
async def test_predictability_exposes_current_scope_baseline_warning():
    response = await build_fake_runtime().process(HarnessRequest(query="Предсказуемость WMB-SPRNT-1"))
    assert response.skill_id == "sprint-predictability"
    assert response.data["predictability_percent"] == 61.5
    assert "current_scope_used_as_commitment_baseline" in response.warnings


@pytest.mark.asyncio
async def test_risk_queue_is_ranked_by_explicit_deterministic_rules():
    response = await build_fake_runtime().process(HarnessRequest(query="Риски спринта WMB-SPRNT-1"))
    assert response.skill_id == "sprint-risk-queue"
    assert response.data["risks"][0]["key"] == "WMB-102"
    assert "critical" in response.data["risks"][0]["reasons"]
    assert response.evidence[0].type == "sprint_risk"
