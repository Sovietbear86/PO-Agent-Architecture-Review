"""Tests for Version Registry with real SWTR data."""

import pytest
from datetime import datetime, timedelta

from po_agent.versions.registry import (
    VersionRegistry,
    VersionEntry,
    VersionStatus,
)


@pytest.fixture
def registry():
    """Create version registry."""
    r = VersionRegistry(db_path=":memory:")
    yield r
    r.close()


class TestVersionRegistryBasic:
    """Tests for basic version registry operations."""

    def test_add_version(self, registry: VersionRegistry):
        """Test adding a version."""
        entry = registry.add_version(
            component_type="prompt",
            component_name="task_summarizer",
            version=1,
            release_notes="Initial release",
            created_by="Kalachanov.V.V",
        )

        assert entry.component_type == "prompt"
        assert entry.component_name == "task_summarizer"
        assert entry.version == 1
        assert "Kalachanov" in entry.created_by

    def test_get_by_name(self, registry: VersionRegistry):
        """Test getting versions by name."""
        registry.add_version(
            component_type="prompt",
            component_name="task_summarizer",
            version=1,
        )
        registry.add_version(
            component_type="prompt",
            component_name="task_summarizer",
            version=2,
        )

        versions = registry.get_by_name("prompt", "task_summarizer")
        assert len(versions) == 2

    def test_activate_version(self, registry: VersionRegistry):
        """Test activating a version."""
        registry.add_version(
            component_type="prompt",
            component_name="task_summarizer",
            version=1,
        )
        entry = registry.add_version(
            component_type="prompt",
            component_name="task_summarizer",
            version=2,
        )

        activated = registry.activate_version(
            component_type="prompt",
            component_name="task_summarizer",
            version=2,
            activated_by="Garanin.R.V",
        )

        assert activated is not None
        assert activated.status == VersionStatus.ACTIVE.value
        assert activated.version == 2

        # Check old version is deprecated
        old_versions = registry.get_by_name("prompt", "task_summarizer")
        old_v1 = next((v for v in old_versions if v.version == 1), None)
        assert old_v1.status == VersionStatus.DEPRECATED.value

    def test_get_active_version(self, registry: VersionRegistry):
        """Test getting active version."""
        registry.add_version(
            component_type="prompt",
            component_name="task_summarizer",
            version=1,
            status="candidate",  # Not active by default
        )
        registry.add_version(
            component_type="prompt",
            component_name="task_summarizer",
            version=2,
            status="candidate",
        )

        active = registry.get_active("prompt", "task_summarizer")
        assert active is None  # No active yet

        registry.activate_version(
            component_type="prompt",
            component_name="task_summarizer",
            version=2,
        )

        active = registry.get_active("prompt", "task_summarizer")
        assert active is not None
        assert active.version == 2


class TestVersionRegistrySWTR:
    """Tests for Version Registry with real SWTR data."""

    def test_version_with_real_team_member(self, registry: VersionRegistry):
        """Test version creation with real team member."""
        entry = registry.add_version(
            component_type="capability",
            component_name="task_quality_analyzer",
            version=1,
            release_notes="First quality analysis capability",
            created_by="Kalachanov.V.V",  # Real team member
        )

        assert entry.created_by == "Kalachanov.V.V"

    def test_version_history_with_real_components(self, registry: VersionRegistry):
        """Test version history with real component references."""
        # Create multiple versions for real components
        registry.add_version(
            component_type="prompt",
            component_name="sprint_explainer",
            version=1,
            release_notes="Initial sprint explainer",
            created_by="Kalachanov.V.V",
        )
        registry.add_version(
            component_type="prompt",
            component_name="sprint_explainer",
            version=2,
            release_notes="Added velocity metrics",
            created_by="Garanin.R.V",
        )
        registry.add_version(
            component_type="prompt",
            component_name="sprint_explainer",
            version=3,
            release_notes="Added risk analysis",
            created_by="Agataeva.A.Z",
        )

        # Activate version 2
        registry.activate_version(
            component_type="prompt",
            component_name="sprint_explainer",
            version=2,
        )

        # Get history
        history = registry.get_version_history("prompt", "sprint_explainer")
        assert len(history) == 3

        # Check version 2 is active
        active = registry.get_active("prompt", "sprint_explainer")
        assert active.version == 2

    def test_breaking_changes_tracking(self, registry: VersionRegistry):
        """Test breaking changes tracking."""
        entry = registry.add_version(
            component_type="schema",
            component_name="task_schema",
            version=1,
            breaking_changes=False,
        )

        assert entry.breaking_changes is False

        new_entry = registry.add_version(
            component_type="schema",
            component_name="task_schema",
            version=2,
            breaking_changes=True,
        )

        assert new_entry.breaking_changes is True

    def test_supported_until_date(self, registry: VersionRegistry):
        """Test supported until date tracking."""
        from datetime import timedelta

        future_date = datetime.now() + timedelta(days=365)

        entry = registry.add_version(
            component_type="model",
            component_name="Qwen-Coder-3.7",
            version=1,
            supported_until=future_date,
        )

        assert entry.supported_until is not None
        assert entry.supported_until >= future_date


class TestVersionRegistryRealTeamIntegration:
    """Integration tests with real SWTR team data."""

    def test_full_version_lifecycle(self, registry: VersionRegistry):
        """Test full version lifecycle with real team members."""
        # 1. Create version (active by default)
        entry = registry.add_version(
            component_type="config",
            component_name="team_members",
            version=1,
            release_notes="Initial team config",
            created_by="Kalachanov.V.V",
        )

        assert entry.status == VersionStatus.ACTIVE.value

        # 2. Update with new version (candidate)
        new_version = registry.add_version(
            component_type="config",
            component_name="team_members",
            version=2,
            release_notes="Updated team members",
            created_by="Garanin.R.V",
        )

        assert new_version.version == 2

        # 3. Activate new version
        registry.activate_version(
            component_type="config",
            component_name="team_members",
            version=2,
        )

        # Verify old version is deprecated
        old = registry.get_by_name_version("config", "team_members", 1)
        assert old.status == VersionStatus.DEPRECATED.value

    def test_multiple_component_types_with_real_team(self, registry: VersionRegistry):
        """Test registry with multiple component types from real team."""
        versions_data = [
            {
                "component_type": "prompt",
                "component_name": "task_summarizer",
                "version": 1,
                "release_notes": "Initial",
                "created_by": "Kalachanov.V.V",
            },
            {
                "component_type": "capability",
                "component_name": "task_quality_analyzer",
                "version": 1,
                "release_notes": "First quality capability",
                "created_by": "Garanin.R.V",
            },
            {
                "component_type": "config",
                "component_name": "team_members",
                "version": 1,
                "release_notes": "Team config",
                "created_by": "Agataeva.A.Z",
            },
            {
                "component_type": "schema",
                "component_name": "task_schema",
                "version": 1,
                "release_notes": "Task schema",
                "created_by": "Dolgovskoy.E.N",
            },
        ]

        for data in versions_data:
            registry.add_version(**data)

        # Verify all added
        all_active = registry.get_all_active()
        assert len(all_active) == 4

        # Verify team members
        creators = {v.created_by for v in all_active}
        assert "Kalachanov.V.V" in creators
        assert "Garanin.R.V" in creators
        assert "Agataeva.A.Z" in creators
        assert "Dolgovskoy.E.N" in creators


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
