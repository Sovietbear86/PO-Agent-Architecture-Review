"""Tests for Shadow Mode with real SWTR data."""

import pytest

from po_agent.shadow.mode import (
    ShadowModeEntry,
    ShadowModeStore,
    ShadowModeStatus,
)


@pytest.fixture
def store():
    """Create shadow mode store."""
    s = ShadowModeStore(db_path=":memory:")
    yield s
    s.close()


class TestShadowModeBasic:
    """Tests for basic shadow mode operations."""

    def test_add_config(self, store: ShadowModeStore):
        """Test adding a shadow mode configuration."""
        entry = store.add_config(
            prompt_name="task_summarizer",
            shadow_version=2,
            comparison_threshold=0.85,
            created_by="Kalachanov.V.V",
        )

        assert entry.prompt_name == "task_summarizer"
        assert entry.shadow_version == 2
        assert entry.comparison_threshold == 0.85
        assert entry.enabled is True
        assert entry.status == ShadowModeStatus.ENABLED.value

    def test_get_by_prompt(self, store: ShadowModeStore):
        """Test getting shadow mode config by prompt name."""
        store.add_config(
            prompt_name="task_summarizer",
            shadow_version=2,
        )

        config = store.get_by_prompt("task_summarizer")
        assert config is not None
        assert config.prompt_name == "task_summarizer"

    def test_enable_disable_config(self, store: ShadowModeStore):
        """Test enabling and disabling shadow mode."""
        entry = store.add_config(
            prompt_name="task_summarizer",
            shadow_version=2,
        )

        assert entry.enabled is True

        store.disable_config("task_summarizer")
        disabled = store.get_by_prompt("task_summarizer")
        assert disabled.enabled is False
        assert disabled.status == ShadowModeStatus.DISABLED.value

        store.enable_config("task_summarizer", enabled_by="Garanin.R.V")
        enabled = store.get_by_prompt("task_summarizer")
        assert enabled.enabled is True
        assert enabled.status == ShadowModeStatus.ENABLED.value
        assert enabled.created_by == "Garanin.R.V"

    def test_complete_and_rollback(self, store: ShadowModeStore):
        """Test completing and rolling back shadow mode."""
        entry = store.add_config(
            prompt_name="task_summarizer",
            shadow_version=2,
        )

        store.complete_config("task_summarizer")
        completed = store.get_by_prompt("task_summarizer")
        assert completed.status == ShadowModeStatus.COMPLETED.value

        store.rollback_config("task_summarizer")
        rolled_back = store.get_by_prompt("task_summarizer")
        assert rolled_back.status == ShadowModeStatus.ROLLED_BACK.value


class TestShadowModeSWTR:
    """Tests for Shadow Mode with real SWTR data."""

    def test_config_with_real_team_member(self, store: ShadowModeStore):
        """Test shadow mode config with real team member."""
        entry = store.add_config(
            prompt_name="sprint_explainer",
            shadow_version=3,
            comparison_threshold=0.9,
            created_by="Kalachanov.V.V",  # Real team member
        )

        assert entry.created_by == "Kalachanov.V.V"

    def test_multiple_prompt_configs(self, store: ShadowModeStore):
        """Test shadow mode for multiple prompts."""
        prompts = [
            ("task_summarizer", 2),
            ("sprint_explainer", 3),
            ("task_quality_analyzer", 1),
        ]

        for prompt_name, version in prompts:
            store.add_config(
                prompt_name=prompt_name,
                shadow_version=version,
            )

        configs = store.get_all_configs()
        assert len(configs) == 3

        # Check all are enabled
        enabled = store.get_enabled()
        assert len(enabled) == 3

    def test_comparison_threshold_with_real_team(self, store: ShadowModeStore):
        """Test comparison threshold with real team members."""
        entry = store.add_config(
            prompt_name="velocity_calculator",
            shadow_version=2,
            comparison_threshold=0.95,
            created_by="Garanin.R.V",
        )

        assert entry.comparison_threshold == 0.95
        assert "Garanin" in entry.created_by


class TestShadowModeRealTeamIntegration:
    """Integration tests with real SWTR team data."""

    def test_full_shadow_lifecycle(self, store: ShadowModeStore):
        """Test full shadow mode lifecycle with real team members."""
        # 1. Create shadow mode config
        entry = store.add_config(
            prompt_name="sprint_health_explainer",
            shadow_version=2,
            comparison_threshold=0.9,
            created_by="Kalachanov.V.V",
        )

        assert entry.status == ShadowModeStatus.ENABLED.value
        assert entry.enabled is True

        # 2. Disable config
        store.disable_config("sprint_health_explainer")
        disabled = store.get_by_prompt("sprint_health_explainer")
        assert disabled.enabled is False

        # 3. Enable again
        store.enable_config("sprint_health_explainer", enabled_by="Garanin.R.V")
        enabled = store.get_by_prompt("sprint_health_explainer")
        assert enabled.enabled is True
        assert enabled.created_by == "Garanin.R.V"

        # 4. Complete shadow mode
        store.complete_config("sprint_health_explainer")
        completed = store.get_by_prompt("sprint_health_explainer")
        assert completed.status == ShadowModeStatus.COMPLETED.value

    def test_shadow_configs_with_real_team_members(self, store: ShadowModeStore):
        """Test shadow mode configs with real team member references."""
        configs_data = [
            {
                "prompt_name": "task_summarizer",
                "shadow_version": 2,
                "comparison_threshold": 0.85,
                "created_by": "Kalachanov.V.V",
            },
            {
                "prompt_name": "sprint_explainer",
                "shadow_version": 3,
                "comparison_threshold": 0.9,
                "created_by": "Garanin.R.V",
            },
            {
                "prompt_name": "task_quality_analyzer",
                "shadow_version": 1,
                "comparison_threshold": 0.95,
                "created_by": "Agataeva.A.Z",
            },
        ]

        for data in configs_data:
            store.add_config(**data)

        # Verify all configs
        configs = store.get_all_configs()
        assert len(configs) == 3

        # Verify team members
        creators = {c.created_by for c in configs}
        assert "Kalachanov.V.V" in creators
        assert "Garanin.R.V" in creators
        assert "Agataeva.A.Z" in creators


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
