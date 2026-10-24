"""Tests for Knowledge Layer V1 with real SWTR data."""

import pytest
import tempfile
import yaml
from pathlib import Path

from po_agent.knowledge.layer import (
    KnowledgeLoader,
    KnowledgeLayer,
    WorkflowConfig,
    TeamConfig,
    ProductConfig,
    MetricDefinition,
    ReleaseRule,
    CuratedMemoryEntry,
)


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir)

        # Create workflow.yaml
        workflow = {
            "statuses": {
                "Open": {"display_name": "Открыта", "category": "backlog", "description": "Задача создана"},
                "In progress": {"display_name": "В работе", "category": "active_work", "description": "Активная работа"},
                "In review": {"display_name": "На ревью", "category": "review", "description": "Code review"},
                "QA": {"display_name": "Тестирование", "category": "testing", "description": "Тестирование"},
                "Closed": {"display_name": "Закрыта", "category": "completed", "description": "Завершена"},
            },
            "analytics": {
                "active_work_statuses": ["In progress"],
                "waiting_statuses": [],
                "review_statuses": ["In review"],
                "testing_statuses": ["QA"],
                "completed_statuses": ["Closed"],
            },
            "cycle_time": {"start_status": "In progress"},
            "wip": {"basic": ["In progress", "In review", "QA"]},
            "throughput": {"successful_statuses": ["Closed"]},
            "blockage": {"blocked_statuses": [], "thresholds": {}},
        }
        with open(config_path / "workflow.yaml", "w") as f:
            yaml.dump(workflow, f)

        # Create team.yaml with real team members
        team = {
            "team": {
                "name": "WMB Team",
                "description": "Web Metrics Backend team",
                "domain": "wmb",
                "sprints": {"current": {"id": "WMB-SPRNT-4"}},
                "members": [
                    {"login": "Kalachanov.V.V", "name": "Vladimir Kalachanov", "role": "PO", "capacity_hours": 40, "skills": ["Python", "FastAPI"], "team_affiliation": "backend"},
                    {"login": "Garanin.R.V", "name": "Roman Garanin", "role": "Developer", "capacity_hours": 40, "skills": ["Python", "FastAPI"], "team_affiliation": "backend"},
                    {"login": "Agataeva.A.Z", "name": "Anastasia Agataeva", "role": "Developer", "capacity_hours": 40, "skills": ["Python", "FastAPI"], "team_affiliation": "backend"},
                    {"login": "Dolgovskoy.E.N", "name": "Evgeny Dolgovskoy", "role": "Developer", "capacity_hours": 40, "skills": ["Python", "FastAPI"], "team_affiliation": "backend"},
                ],
                "capacity": {"weekly_hours": 160, "sprint_capacity_hours": 320},
                "settings": {"velocity_history_sprints": 6, "max_tasks_per_member": 8},
            }
        }
        with open(config_path / "team.example.yaml", "w") as f:
            yaml.dump(team, f)

        yield config_path


class TestKnowledgeLayerBasic:
    """Tests for basic knowledge layer operations."""

    def test_load_workflow(self, temp_config_dir: Path):
        """Test loading workflow configuration."""
        loader = KnowledgeLoader(str(temp_config_dir))
        workflow = loader.load_workflow()

        assert isinstance(workflow, WorkflowConfig)
        assert "Open" in workflow.statuses
        assert "In progress" in workflow.statuses

    def test_load_team(self, temp_config_dir: Path):
        """Test loading team configuration."""
        loader = KnowledgeLoader(str(temp_config_dir))
        team = loader.load_team()

        assert isinstance(team, TeamConfig)
        assert len(team.members) == 4
        assert team.name == "WMB Team"

    def test_load_all(self, temp_config_dir: Path):
        """Test loading all knowledge sources."""
        loader = KnowledgeLoader(str(temp_config_dir))
        knowledge = loader.load_all()

        assert "workflow" in knowledge
        assert "team" in knowledge
        assert "products" in knowledge
        assert "metrics" in knowledge


class TestKnowledgeLayerSWTR:
    """Tests for Knowledge Layer with real SWTR data."""

    def test_load_real_team_members(self, temp_config_dir: Path):
        """Test loading real team members from team.example.yaml."""
        loader = KnowledgeLoader(str(temp_config_dir))
        team = loader.load_team()

        logins = [m.login for m in team.members]

        # Verify real team members
        assert "Kalachanov.V.V" in logins
        assert "Garanin.R.V" in logins
        assert "Agataeva.A.Z" in logins
        assert "Dolgovskoy.E.N" in logins

    def test_get_active_statuses_with_real_workflow(self, temp_config_dir: Path):
        """Test getting active statuses with real workflow."""
        layer = KnowledgeLayer(str(temp_config_dir))
        layer.initialize()

        active_statuses = layer.get_active_statuses()

        # Should contain active work statuses
        assert len(active_statuses) >= 1

    def test_get_team_members_with_real_data(self, temp_config_dir: Path):
        """Test getting team members with real data."""
        layer = KnowledgeLayer(str(temp_config_dir))
        layer.initialize()

        members = layer.get_team_members()

        assert len(members) == 4

        # Verify team member details
        kalachanov = next((m for m in members if m.login == "Kalachanov.V.V"), None)
        assert kalachanov is not None
        assert kalachanov.role == "PO"
        assert "Python" in kalachanov.skills


class TestKnowledgeLayerRealTeamIntegration:
    """Integration tests with real SWTR team data."""

    def test_full_knowledge_layer_with_real_team(self, temp_config_dir: Path):
        """Test full knowledge layer with real team members."""
        layer = KnowledgeLayer(str(temp_config_dir))
        layer.initialize()

        # Get workflow
        workflow = layer.get_workflow_config()
        assert workflow is not None
        assert "In progress" in workflow.statuses

        # Get team
        team = layer.get_team_config()
        assert team is not None
        assert len(team.members) >= 4

        # Get members
        members = layer.get_team_members()
        assert len(members) == 4

        # Get active statuses
        active = layer.get_active_statuses()
        assert len(active) >= 1

    def test_multiple_real_team_members_query(self, temp_config_dir: Path):
        """Test knowledge layer with multiple real team members."""
        layer = KnowledgeLayer(str(temp_config_dir))
        layer.initialize()

        members = layer.get_team_members()

        # Verify all 4 real team members
        expected_members = ["Kalachanov.V.V", "Garanin.R.V", "Agataeva.A.Z", "Dolgovskoy.E.N"]
        actual_logins = [m.login for m in members]

        for expected in expected_members:
            assert expected in actual_logins, f"{expected} not found in members"

    def test_curated_memory_loading(self, temp_config_dir: Path):
        """Test loading curated memory entries."""
        # Create curated_memory.yaml
        curated = {
            "entries": [
                {
                    "key": "sprint_terminology",
                    "category": "terminology",
                    "content": "Sprint is a time-boxed period of 2 weeks",
                    "evidence_trace_ids": ["trace-1", "trace-2"],
                    "source": "team_convention",
                    "confidence": 0.95,
                    "status": "approved",
                    "created_at": "2024-01-01T00:00:00",
                    "approved_by": "Kalachanov.V.V",
                },
                {
                    "key": "wip_limit",
                    "category": "process",
                    "content": "Maximum WIP is 8 tasks per member",
                    "evidence_trace_ids": ["trace-3"],
                    "source": "workflow_config",
                    "confidence": 0.85,
                    "status": "approved",
                    "created_at": "2024-01-02T00:00:00",
                    "approved_by": "Garanin.R.V",
                },
            ]
        }

        curated_path = temp_config_dir / "curated_memory.yaml"
        with open(curated_path, "w") as f:
            yaml.dump(curated, f)

        loader = KnowledgeLoader(str(temp_config_dir))
        memory = loader.load_curated_memory()

        assert len(memory) == 2

        # Verify approved entries
        approved = loader.get_approved_curated_memory()
        assert len(approved) == 2

        # Verify content
        sprint_entry = next((e for e in approved if e.key == "sprint_terminology"), None)
        assert sprint_entry is not None
        assert "2 weeks" in sprint_entry.content
        assert sprint_entry.approved_by == "Kalachanov.V.V"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
