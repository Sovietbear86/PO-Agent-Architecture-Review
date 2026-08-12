import pytest
from po_agent.harness import HarnessRequest, ResponseStatus, build_fake_runtime

@pytest.mark.asyncio
async def test_sprint_health_is_deterministic_and_evidenced():
    r=await build_fake_runtime().process(HarnessRequest(query="Покажи состояние WMB-SPRNT-1"))
    assert r.status is ResponseStatus.COMPLETED
    assert r.skill_id=="sprint-health"
    assert r.data["total"]==2
    assert r.data["completed"]==1
    assert r.data["completion_percent"]==50.0
    assert len(r.evidence)==2

@pytest.mark.asyncio
async def test_release_health_uses_release_tasks():
    r=await build_fake_runtime().process(HarnessRequest(query="Риски WMB-2024-Q3"))
    assert r.skill_id=="release-health"
    assert r.data["total"]==3
    assert r.data["completed"]==1
    assert r.data["completion_percent"]==33.3

@pytest.mark.asyncio
async def test_portfolio_overview_exposes_risk_queue():
    r=await build_fake_runtime().process(HarnessRequest(query="Дай обзор и риски"))
    assert r.skill_id=="portfolio-overview"
    assert r.data["tasks_total"]==5
    assert r.data["blocked"]==1
    assert r.data["active"]==1
    assert r.data["adapter"]=="fake-as21"
    assert {x["key"] for x in r.data["risks"]} >= {"WMB-102","DMS-202"}
