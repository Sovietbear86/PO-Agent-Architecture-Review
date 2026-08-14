import pytest

from po_agent.adapters.fake import FakeAS21Adapter
from po_agent.harness.contracts import HarnessRequest, ResponseStatus
from po_agent.harness.runtime import HarnessRuntime
from po_agent.harness.runtime_factory import build_runtime_bundle
from po_agent.harness.source_contracts import TeamMemberProfile
from po_agent.harness.team_matching import TeamMatchingCapabilities
from po_agent.harness.team_matching_wiring import enable_team_matching


class Profiles:
    def __init__(self, profiles):
        self._profiles = tuple(profiles)

    def list_profiles(self):
        return self._profiles


@pytest.mark.asyncio
async def test_competency_match_uses_only_declared_profile_evidence():
    source = Profiles([
        TeamMemberProfile("backend.dev", ("WMB",), "Backend OAuth2 authentication developer", ("OAuth2", "Python"), 11),
        TeamMemberProfile("writer", ("WMB",), "Technical writer", (), 10),
    ])
    cap = TeamMatchingCapabilities(FakeAS21Adapter(), source)
    result = await cap.competency_match({"task_key": "WMB-101"})
    assert result.data["matches"][0]["member"] == "backend.dev"
    assert "oauth2" in result.data["matches"][0]["matched_terms"]
    assert all(row["member"] != "writer" for row in result.data["matches"])
    assert any(e.type == "team_profile" and e.entity_id == "backend.dev" for e in result.evidence)


@pytest.mark.asyncio
async def test_assignee_recommendation_breaks_equal_match_by_current_active_load():
    source = Profiles([
        TeamMemberProfile("Sidorov.S.S", ("WMB",), "Mobile login developer", ("login",), 11),
        TeamMemberProfile("free.dev", ("WMB",), "Mobile login developer", ("login",), 11),
    ])
    cap = TeamMatchingCapabilities(FakeAS21Adapter(), source)
    result = await cap.assignee_recommendation({"task_key": "WMB-102"})
    assert result.data["recommendation"] == "free.dev"
    assert result.data["candidates"][0]["active_tasks"] == 0
    assert result.data["candidates"][1]["active_tasks"] == 1


@pytest.mark.asyncio
async def test_assignee_recommendation_refuses_to_guess_without_declared_match():
    source = Profiles([TeamMemberProfile("writer", ("DMS",), "Technical writer", (), 10)])
    cap = TeamMatchingCapabilities(FakeAS21Adapter(), source)
    result = await cap.assignee_recommendation({"task_key": "WMB-101"})
    assert result.data["recommendation"] is None
    assert "insufficient_declared_competency_evidence" in result.warnings


@pytest.mark.asyncio
async def test_team_matching_is_executable_through_versioned_harness_skill():
    source = Profiles([TeamMemberProfile("backend.dev", ("WMB",), "OAuth2 authentication developer", ("OAuth2",), 11)])
    runtime = enable_team_matching(HarnessRuntime(FakeAS21Adapter()), source)
    response = await runtime.process(HarnessRequest(query="Кто подходит по компетенциям для WMB-101?"))
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "team-competency-match"
    assert response.skill_version == "1.0.0"
    assert response.data["matches"][0]["member"] == "backend.dev"
    assert response.evidence


@pytest.mark.asyncio
async def test_assignee_recommendation_is_executable_through_router_and_allowlist():
    source = Profiles([
        TeamMemberProfile("Sidorov.S.S", ("WMB",), "Mobile login developer", ("login",), 11),
        TeamMemberProfile("free.dev", ("WMB",), "Mobile login developer", ("login",), 11),
    ])
    runtime = enable_team_matching(HarnessRuntime(FakeAS21Adapter()), source)
    response = await runtime.process(HarnessRequest(query="Кому назначить WMB-102?"))
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "team-assignee-recommendation"
    assert response.data["recommendation"] == "free.dev"


@pytest.mark.asyncio
async def test_runtime_factory_registers_team_matching_only_with_declared_profiles():
    bundle = build_runtime_bundle("fake", team_config_path="config/team.example.yaml")

    competency = await bundle.runtime.process(
        HarnessRequest(query="Кто подходит по компетенциям для WMB-101?", session_id="factory-comp")
    )
    assert competency.status is ResponseStatus.COMPLETED
    assert competency.skill_id == "team-competency-match"
    assert competency.data["method"] == "declared_profile_token_overlap"
    assert competency.evidence

    recommendation = await bundle.runtime.process(
        HarnessRequest(query="Кому назначить WMB-102?", session_id="factory-rec")
    )
    assert recommendation.status is ResponseStatus.COMPLETED
    assert recommendation.skill_id == "team-assignee-recommendation"
    assert recommendation.data["method"] == "declared_profile_then_active_task_load"
