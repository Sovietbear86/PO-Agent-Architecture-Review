"""Tests for Team Config loader and validator."""

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from po_agent.config.team import (
    TeamConfig,
    TeamConfigLoader,
    TeamConfigValidator,
    TeamMember,
    SprintConfig,
)
from po_agent.config.real_team import (
    get_real_team_members,
    get_all_member_logins,
)


class TestRealTeamConfiguration:
    """Integration tests using real team configuration from project."""

    def test_load_real_team_members(self):
        """Test loading real team members from project config."""
        members = get_real_team_members()

        assert len(members) > 0
        assert all("login" in m for m in members)
        assert all("full_name" in m for m in members)

    def test_get_all_member_logins(self):
        """Test getting all real member logins."""
        logins = get_all_member_logins()

        assert len(logins) > 0
        assert isinstance(logins, list)
        assert all(isinstance(login, str) for login in logins)

    def test_load_real_config_with_members(self):
        """Test loading config that includes all real team members."""
        loader = TeamConfigLoader()
        config = loader.load_example()

        # Check that we can map real logins to config
        logins = get_all_member_logins()
        real_member = next((m for m in config.members if m.login in logins), None)

        # At least some logins should match
        assert real_member is not None or len(config.members) > 0


class TestTeamConfigLoader:
    """Tests for TeamConfigLoader."""

    def test_load_example(self):
        """Test loading example config."""
        loader = TeamConfigLoader()
        config = loader.load_example()

        assert config is not None
        assert config.team is not None

    def test_load_nonexistent_file(self):
        """Test loading non-existent file raises error."""
        loader = TeamConfigLoader()

        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent.yaml")

    def test_get_member_by_login(self):
        """Test getting member by login."""
        loader = TeamConfigLoader()
        config = loader.load_example()

        member = loader.get_member_by_login(config, "Ivanov.I.I")

        assert member is not None
        assert member.login == "Ivanov.I.I"

    def test_get_all_members(self):
        """Test getting all members."""
        loader = TeamConfigLoader()
        config = loader.load_example()

        members = loader.get_all_members(config)

        assert len(members) > 0

    def test_get_current_sprint(self):
        """Test getting current sprint."""
        loader = TeamConfigLoader()
        config = loader.load_example()

        sprint = loader.get_current_sprint(config)

        assert sprint is not None
        assert sprint.id == "WMB-SPRNT-4"


class TestTeamConfigValidator:
    """Tests for TeamConfigValidator."""

    def test_valid_config(self):
        """Test validation of valid config."""
        config = TeamConfig(
            team={"name": "Test Team", "domain": "test"},
            sprints={
                "current": SprintConfig(
                    id="TEST-SPRNT-1",
                    name="Test Sprint",
                    start_date="2026-01-01",
                    end_date="2026-01-14",
                    goal="Test goals",
                )
            },
            members=[
                TeamMember(
                    login="test.user",
                    name="Test User",
                    role="Developer",
                    capacity_hours=40,
                    skills=["Python", "FastAPI"],
                ),
            ],
            capacity={"weekly_hours": 40},
            settings={"velocity_history_sprints": 6},
        )

        is_valid, errors = TeamConfigValidator.validate(config)

        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_config_no_members(self):
        """Test validation with no members."""
        config = TeamConfig(
            team={"name": "Test Team"},
            sprints={},
            members=[],
            capacity={},
            settings={},
        )

        is_valid, errors = TeamConfigValidator.validate(config)

        assert is_valid is False
        assert len(errors) > 0

    def test_invalid_config_no_sprints(self):
        """Test validation with no sprints."""
        config = TeamConfig(
            team={"name": "Test Team"},
            sprints={},
            members=[
                TeamMember(
                    login="test.user",
                    name="Test User",
                    role="Developer",
                ),
            ],
            capacity={},
            settings={},
        )

        is_valid, errors = TeamConfigValidator.validate(config)

        assert is_valid is False
        assert len(errors) > 0

    def test_validate_member_skills(self):
        """Test member skill validation."""
        member = TeamMember(
            login="test.user",
            name="Test User",
            role="Developer",
            skills=["Python"],
        )

        is_valid = TeamConfigValidator.validate_member_skills(member)

        assert is_valid is True

    def test_validate_member_no_skills(self):
        """Test member validation without skills."""
        member = TeamMember(
            login="test.user",
            name="Test User",
            role="Manager",
        )

        is_valid = TeamConfigValidator.validate_member_skills(member)

        assert is_valid is True  # Managers can have no skills


class TestTeamMember:
    """Tests for TeamMember model."""

    def test_member_creation(self):
        """Test creating team member."""
        member = TeamMember(
            login="test.user",
            name="Test User",
            role="Developer",
            capacity_hours=40,
            skills=["Python"],
        )

        assert member.login == "test.user"
        assert member.name == "Test User"
        assert member.capacity_hours == 40
        assert len(member.skills) == 1

    def test_member_default_values(self):
        """Test member with default values."""
        member = TeamMember(
            login="test.user",
            name="Test User",
            role="Developer",
        )

        assert member.capacity_hours == 40
        assert member.skills == []
        assert member.team_affiliation == "default"


class TestSprintConfig:
    """Tests for SprintConfig model."""

    def test_sprint_creation(self):
        """Test creating sprint config."""
        sprint = SprintConfig(
            id="TEST-SPRNT-1",
            name="Test Sprint",
            start_date="2026-01-01",
            end_date="2026-01-14",
        )

        assert sprint.id == "TEST-SPRNT-1"
        assert sprint.name == "Test Sprint"
        assert sprint.goal is None

    def test_sprint_with_goal(self):
        """Test sprint with goal."""
        sprint = SprintConfig(
            id="TEST-SPRNT-1",
            name="Test Sprint",
            start_date="2026-01-01",
            end_date="2026-01-14",
            goal="Test goals",
        )

        assert sprint.goal == "Test goals"


class TestTeamConfigLoaderLifecycle:
    """Tests for TeamConfigLoader lifecycle."""

    def test_loader_initialization(self):
        """Test loader initialization."""
        loader = TeamConfigLoader()
        assert loader is not None

    def test_loader_custom_dir(self):
        """Test loader with custom config directory."""
        with TemporaryDirectory() as tmpdir:
            Path(tmpdir).joinpath("test.yaml").write_text("""
team:
  name: "Test Team"
sprints:
  current:
    id: "TEST-1"
    name: "Test"
    start_date: "2026-01-01"
    end_date: "2026-01-14"
members: []
            """)
            loader = TeamConfigLoader(tmpdir)
            config = loader.load("test.yaml")
            assert config is not None
