import pytest

from po_agent.adapters.fake import FakeAS21Adapter
from po_agent.harness.source_contracts import TeamMemberProfile
from po_agent.harness.team_matching import TeamMatchingCapabilities


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
    assert "OAuth2" in result.data["matches"][0]["matched_terms"]
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
