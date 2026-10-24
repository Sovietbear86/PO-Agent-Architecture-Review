"""Tests for Prompt Registry with real SWTR data."""

import pytest

from po_agent.versions.prompt_registry import (
    PromptRegistry,
    PromptEntry,
    PromptStatus,
)


@pytest.fixture
def registry():
    """Create prompt registry."""
    r = PromptRegistry(db_path=":memory:")
    yield r
    r.close()


class TestPromptRegistryBasic:
    """Tests for basic prompt registry operations."""

    def test_add_prompt(self, registry: PromptRegistry):
        """Test adding a prompt."""
        entry = registry.add_prompt(
            prompt_name="task_summarizer",
            version=1,
            content="Summarize the task description...",
            model_compatibility=["Qwen-Coder-3.7", "GPT-4"],
            created_by="Kalachanov.V.V",
        )

        assert entry.prompt_name == "task_summarizer"
        assert entry.version == 1
        assert "Kalachanov" in entry.created_by

    def test_get_by_name(self, registry: PromptRegistry):
        """Test getting prompts by name."""
        registry.add_prompt(
            prompt_name="task_summarizer",
            version=1,
            content="v1 content",
        )
        registry.add_prompt(
            prompt_name="task_summarizer",
            version=2,
            content="v2 content",
        )

        versions = registry.get_by_name("task_summarizer")
        assert len(versions) == 2

    def test_activate_prompt(self, registry: PromptRegistry):
        """Test activating a prompt."""
        registry.add_prompt(
            prompt_name="task_summarizer",
            version=1,
            content="v1",
        )
        entry = registry.add_prompt(
            prompt_name="task_summarizer",
            version=2,
            content="v2",
        )

        activated = registry.activate_prompt(
            prompt_name="task_summarizer",
            version=2,
            activated_by="Garanin.R.V",
        )

        assert activated is not None
        assert activated.status == PromptStatus.ACTIVE.value
        assert activated.version == 2
        assert activated.created_by == "Garanin.R.V"

        # Check old version is deprecated
        old_versions = registry.get_by_name("task_summarizer")
        old_v1 = next((p for p in old_versions if p.version == 1), None)
        assert old_v1.status == PromptStatus.DEPRECATED.value

    def test_get_active_prompt(self, registry: PromptRegistry):
        """Test getting active prompt."""
        registry.add_prompt(
            prompt_name="task_summarizer",
            version=1,
            content="v1",
        )
        registry.add_prompt(
            prompt_name="task_summarizer",
            version=2,
            content="v2",
        )

        active = registry.get_active("task_summarizer")
        assert active is None  # No active yet

        registry.activate_prompt(
            prompt_name="task_summarizer",
            version=2,
        )

        active = registry.get_active("task_summarizer")
        assert active is not None
        assert active.version == 2

    def test_get_all_active(self, registry: PromptRegistry):
        """Test getting all active prompts."""
        registry.add_prompt(
            prompt_name="task_summarizer",
            version=1,
            content="v1",
        )
        registry.activate_prompt(
            prompt_name="task_summarizer",
            version=1,
        )

        registry.add_prompt(
            prompt_name="sprint_explainer",
            version=1,
            content="v1",
        )
        registry.activate_prompt(
            prompt_name="sprint_explainer",
            version=1,
        )

        active = registry.get_all_active()
        assert len(active) == 2


class TestPromptRegistrySWTR:
    """Tests for Prompt Registry with real SWTR data."""

    def test_prompt_with_real_team_member(self, registry: PromptRegistry):
        """Test prompt creation with real team member."""
        entry = registry.add_prompt(
            prompt_name="task_quality_explainer",
            version=1,
            content="Analyze task completeness...",
            model_compatibility=["Qwen-Coder-3.7"],
            created_by="Kalachanov.V.V",  # Real team member
        )

        assert entry.created_by == "Kalachanov.V.V"

    def test_version_history_with_real_team(self, registry: PromptRegistry):
        """Test version history with real team references."""
        # Create multiple versions
        registry.add_prompt(
            prompt_name="sprint_explainer",
            version=1,
            content="v1 - initial",
            created_by="Kalachanov.V.V",
        )
        registry.add_prompt(
            prompt_name="sprint_explainer",
            version=2,
            content="v2 - added metrics",
            created_by="Garanin.R.V",
        )
        registry.add_prompt(
            prompt_name="sprint_explainer",
            version=3,
            content="v3 - added risk analysis",
            created_by="Agataeva.A.Z",
        )

        # Activate version 2
        registry.activate_prompt(
            prompt_name="sprint_explainer",
            version=2,
        )

        # Get history
        history = registry.get_prompt_history("sprint_explainer")
        assert len(history) == 3

        # Check version 2 is active
        active = registry.get_active("sprint_explainer")
        assert active.version == 2

    def test_model_compatibility_tracking(self, registry: PromptRegistry):
        """Test model compatibility tracking."""
        entry = registry.add_prompt(
            prompt_name="intent_classifier",
            version=1,
            content="Classify user intent...",
            model_compatibility=["Qwen-Coder-3.7", "GPT-4o-mini"],
        )

        assert "Qwen-Coder-3.7" in entry.model_compatibility
        assert "GPT-4o-mini" in entry.model_compatibility

    def test_deprecate_prompt(self, registry: PromptRegistry):
        """Test deprecating a prompt."""
        entry = registry.add_prompt(
            prompt_name="task_summarizer",
            version=1,
            content="v1",
        )
        registry.activate_prompt(prompt_name="task_summarizer", version=1)

        deprecated = registry.deprecate_prompt("task_summarizer", 1)
        assert deprecated is not None
        assert deprecated.status == PromptStatus.DEPRECATED.value


class TestPromptRegistryRealTeamIntegration:
    """Integration tests with real SWTR team data."""

    def test_full_prompt_lifecycle(self, registry: PromptRegistry):
        """Test full prompt lifecycle with real team members."""
        # 1. Create prompt (candidate)
        entry = registry.add_prompt(
            prompt_name="sprint_health_explainer",
            version=1,
            content="Explain sprint health metrics...",
            model_compatibility=["Qwen-Coder-3.7"],
            created_by="Kalachanov.V.V",
        )

        assert entry.status == PromptStatus.CANDIDATE.value

        # 2. Review and activate
        activated = registry.activate_prompt(
            prompt_name="sprint_health_explainer",
            version=1,
            activated_by="Garanin.R.V",
        )

        assert activated.status == PromptStatus.ACTIVE.value

        # 3. Update with new version (candidate)
        new_version = registry.add_prompt(
            prompt_name="sprint_health_explainer",
            version=2,
            content="v2 - added velocity metrics",
            created_by="Agataeva.A.Z",
        )

        assert new_version.status == PromptStatus.CANDIDATE.value
        assert new_version.version == 2

        # 4. Activate new version
        registry.activate_prompt(
            prompt_name="sprint_health_explainer",
            version=2,
        )

        # Verify old version is deprecated
        old = registry.get_by_name_version("sprint_health_explainer", 1)
        assert old.status == PromptStatus.DEPRECATED.value

    def test_prompt_registry_with_multiple_real_prompts(self, registry: PromptRegistry):
        """Test registry with multiple prompts from real team."""
        prompts_data = [
            {
                "prompt_name": "task_summarizer",
                "version": 1,
                "content": "Summarize task...",
                "model_compatibility": ["Qwen-Coder-3.7"],
                "created_by": "Kalachanov.V.V",
            },
            {
                "prompt_name": "task_quality_explainer",
                "version": 1,
                "content": "Explain quality analysis...",
                "model_compatibility": ["Qwen-Coder-3.7"],
                "created_by": "Garanin.R.V",
            },
            {
                "prompt_name": "sprint_explainer",
                "version": 1,
                "content": "Explain sprint metrics...",
                "model_compatibility": ["Qwen-Coder-3.7"],
                "created_by": "Agataeva.A.Z",
            },
            {
                "prompt_name": "release_explainer",
                "version": 1,
                "content": "Explain release health...",
                "model_compatibility": ["Qwen-Coder-3.7"],
                "created_by": "Dolgovskoy.E.N",
            },
        ]

        for data in prompts_data:
            registry.add_prompt(**data)

        # Verify all added
        all_prompts = registry.get_all_active()  # None active yet
        assert len(all_prompts) == 0

        # Activate all
        for data in prompts_data:
            registry.activate_prompt(
                prompt_name=data["prompt_name"],
                version=data["version"],
            )

        active = registry.get_all_active()
        assert len(active) == 4

        # Verify team members
        creators = {p.created_by for p in active}
        assert "Kalachanov.V.V" in creators
        assert "Garanin.R.V" in creators
        assert "Agataeva.A.Z" in creators
        assert "Dolgovskoy.E.N" in creators


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
