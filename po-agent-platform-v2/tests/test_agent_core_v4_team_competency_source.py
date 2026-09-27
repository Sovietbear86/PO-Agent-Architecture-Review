from __future__ import annotations

import asyncio
from types import SimpleNamespace

from po_agent.harness.v4_plugin_registry import discover_v4_plugins
from po_agent.harness.v4_plugins.wave_batch3 import (
    build_team_assignee_recommendation,
    build_team_competency_match,
)


def _task(key: str, title: str, *, assignee: str | None = "Moiseev.A.N", blocked: bool = False):
    return SimpleNamespace(
        key=key,
        title=title,
        description=title,
        status_raw="In progress",
        status=SimpleNamespace(value="In progress"),
        is_completed=False,
        is_open=True,
        is_blocked=blocked,
        assignee_login=assignee,
        assignee_id=assignee,
        assignee=assignee,
        status_type="progress",
        status_category=SimpleNamespace(value="active_work"),
    )


class FakeAdapter:
    def __init__(self):
        self.point_reads = []
        self.current_reads = []
        self.sprint_reads = []
        self.target = _task("DMS-380", "Go DataMarts code review")
        self.sprint_tasks = [
            _task("DMS-1", "Go backend", assignee="Moiseev.A.N"),
            _task("DMS-2", "DataMarts", assignee="Zhdanov.A.Ni"),
            _task("DMS-3", "Code Review", assignee="Agataeva.A.Z", blocked=True),
        ]

    async def get_task(self, key: str):
        self.point_reads.append(key)
        return self.target if key == "DMS-380" else None

    async def get_current_sprint_id(self, space: str):
        self.current_reads.append(space)
        return "DMS-SPRNT-3"

    async def get_sprint_tasks(self, sprint_id: str, space: str | None = None):
        self.sprint_reads.append((sprint_id, space))
        return list(self.sprint_tasks)


def test_team_competency_match_uses_repository_profiles_and_point_task_read(monkeypatch):
    profiles = [
        {
            "login": "Moiseev.A.N",
            "full_name": "Моисеев Андрей Николаевич",
            "products": ["DMS"],
            "professional_profile": "Ведущий Go-разработчик",
            "competencies": ["Go"],
        },
        {
            "login": "Zhdanov.A.Ni",
            "full_name": "Жданов Александр Николаевич",
            "products": ["DMS"],
            "professional_profile": "Delivery Lead",
            "competencies": ["Go", "C++", "DataMarts", "Code Review"],
        },
    ]
    monkeypatch.setattr(
        "po_agent.harness.v4_plugins.wave_batch3.get_real_team_members",
        lambda: profiles,
    )
    adapter = FakeAdapter()
    result = asyncio.run(
        build_team_competency_match(SimpleNamespace(adapter=adapter))(
            {"space": "DMS", "task_key": "DMS-380"}
        )
    )

    assert result.data["source"] == "REAL_AS21_PLUS_TEAM_CONFIG"
    assert result.data["competency_source"] == "task-api/config/team_members.yaml"
    assert result.data["matches"][0]["member"] == "Zhdanov.A.Ni"
    assert result.data["matches"][0]["match_count"] >= result.data["matches"][1]["match_count"]
    assert adapter.point_reads == ["DMS-380"]
    assert adapter.current_reads == []
    assert adapter.sprint_reads == []


def test_assignee_recommendation_combines_declared_competence_with_bounded_current_sprint_load(monkeypatch):
    profiles = [
        {
            "login": "Moiseev.A.N",
            "full_name": "Моисеев Андрей Николаевич",
            "products": ["DMS"],
            "professional_profile": "Ведущий Go-разработчик",
            "competencies": ["Go", "DataMarts", "Code Review"],
        },
        {
            "login": "Zhdanov.A.Ni",
            "full_name": "Жданов Александр Николаевич",
            "products": ["DMS"],
            "professional_profile": "Delivery Lead",
            "competencies": ["Go", "DataMarts", "Code Review"],
        },
    ]
    monkeypatch.setattr(
        "po_agent.harness.v4_plugins.wave_batch3.get_real_team_members",
        lambda: profiles,
    )
    adapter = FakeAdapter()
    result = asyncio.run(
        build_team_assignee_recommendation(SimpleNamespace(adapter=adapter))(
            {"space": "DMS", "task_key": "DMS-380"}
        )
    )

    assert result.data["load_scope"] == "authoritative_current_sprint"
    assert result.data["recommendation"] in {"Moiseev.A.N", "Zhdanov.A.Ni"}
    assert adapter.point_reads == ["DMS-380"]
    assert adapter.current_reads == ["DMS"]
    assert adapter.sprint_reads == [("DMS-SPRNT-3", "DMS")]


def test_batch3_contracts_require_task_key_for_competency_skills():
    registry = discover_v4_plugins()
    skills = {skill.id: skill for skill in registry.skills()}
    assert skills["team.competency_match"].completion[0].data_keys == ("space", "task_key", "matches")
    assert skills["team.assignee_recommendation"].completion[0].data_keys == ("space", "task_key", "candidates")
