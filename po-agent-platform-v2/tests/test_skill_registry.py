"""Tests for Skill Registry."""

import pytest

from po_agent.skill.registry import SkillRegistry
from po_agent.skill.models import SkillDefinition, SkillStatus
from po_agent.skill.skills import INITIAL_SKILLS


class TestSkillRegistry:
    """SkillRegistry tests."""

    def test_init(self):
        """Test registry initialization."""
        registry = SkillRegistry()
        assert registry._skills == {}
        assert registry._loaded_at is None

    def test_load_skills_from_dict(self):
        """Test loading skills from dict."""
        registry = SkillRegistry()
        skills = [
            {
                "skill_id": "task_search",
                "name": "Поиск задач",
                "version": "1.0.0",
            },
            {
                "skill_id": "sprint_health",
                "name": "Здоровье спринта",
                "version": "1.0.0",
            },
        ]

        count = registry.load_skills_from_dict(skills)

        assert count == 2
        assert registry.count_skills() == 2

    def test_load_initial_skills(self):
        """Test loading initial skills."""
        registry = SkillRegistry()
        count = registry.load_skills_from_dict(INITIAL_SKILLS)

        assert count == len(INITIAL_SKILLS)
        assert registry.count_skills() == len(INITIAL_SKILLS)

    def test_get_active_skill(self):
        """Test getting active skill."""
        registry = SkillRegistry()
        registry.load_skills_from_dict(INITIAL_SKILLS)

        skill = registry.get_active_skill("task_summary")  # Use task_summary which won't be modified

        assert skill is not None
        assert skill.skill_id == "task_summary"
        assert skill.status == SkillStatus.ACTIVE

    def test_get_skill_version(self):
        """Test getting specific version."""
        registry = SkillRegistry()
        registry.load_skills_from_dict(INITIAL_SKILLS)

        skill = registry.get_skill_version("task_summary", "1.0.0")

        assert skill is not None
        assert skill.version == "1.0.0"

    def test_get_all_versions(self):
        """Test getting all versions."""
        registry = SkillRegistry()
        registry.load_skills_from_dict(INITIAL_SKILLS)

        versions = registry.get_all_versions("task_summary")

        assert len(versions) >= 1

    def test_get_all_skills(self):
        """Test getting all skills."""
        registry = SkillRegistry()
        registry.load_skills_from_dict(INITIAL_SKILLS)

        all_skills = registry.get_all_skills()

        assert len(all_skills) >= 1
        assert "task_summary" in all_skills

    def test_get_active_skills(self):
        """Test getting only active skills."""
        registry = SkillRegistry()
        registry.load_skills_from_dict(INITIAL_SKILLS)

        active = registry.get_active_skills()

        # All initial skills should be active
        assert len(active) == len(INITIAL_SKILLS)

    def test_promote_candidate(self):
        """Test promoting candidate to active."""
        registry = SkillRegistry()

        # Create a clean skill
        base_skill = SkillDefinition(
            skill_id="test_skill",
            name="Test Skill",
            version="1.0.0",
            status=SkillStatus.ACTIVE,
        )
        registry._add_skill(base_skill)

        # Create candidate version
        candidate_skill = SkillDefinition(
            skill_id="test_skill",
            name="Test Skill",
            version="1.1.0",
            status=SkillStatus.CANDIDATE,
        )
        registry._add_skill(candidate_skill)

        # Promote
        result = registry.promote_candidate("test_skill", "1.1.0", "admin")

        assert result is True
        new_skill = registry.get_skill_version("test_skill", "1.1.0")
        assert new_skill.status == SkillStatus.ACTIVE

    def test_count_active_skills(self):
        """Test counting active skills."""
        registry = SkillRegistry()
        # Load only a clean skill
        skill = SkillDefinition(
            skill_id="test_skill",
            name="Test Skill",
            version="1.0.0",
        )
        registry.load_skills_from_dict([skill])

        count = registry.count_active_skills()

        assert count == 1

    def test_has_skill(self):
        """Test checking if skill exists."""
        registry = SkillRegistry()
        registry.load_skills_from_dict(INITIAL_SKILLS)

        assert registry.has_skill("task_summary") is True
        assert registry.has_skill("nonexistent") is False

    def test_register_new_version(self):
        """Test registering new version."""
        registry = SkillRegistry()

        # Create a clean skill
        base_skill = SkillDefinition(
            skill_id="test_skill",
            name="Test Skill",
            version="1.0.0",
            status=SkillStatus.ACTIVE,
        )
        registry._add_skill(base_skill)

        new_skill = registry.register_new_version(
            "test_skill",
            "2.0.0",
            "Major changes",
            approved_by="admin"
        )

        assert new_skill is not None
        assert new_skill.version == "2.0.0"
        assert new_skill.status == SkillStatus.CANDIDATE


class TestSkillRegistryEdgeCases:
    """Edge case tests for SkillRegistry."""

    def test_get_nonexistent_skill(self):
        """Test getting nonexistent skill."""
        registry = SkillRegistry()
        result = registry.get_active_skill("nonexistent")
        assert result is None

    def test_load_empty_skills(self):
        """Test loading empty skills list."""
        registry = SkillRegistry()
        count = registry.load_skills_from_dict([])
        assert count == 0

    def test_deactivate_current_active(self):
        """Test deactivating current active version."""
        registry = SkillRegistry()

        # Create a clean skill
        base_skill = SkillDefinition(
            skill_id="test_skill",
            name="Test Skill",
            version="1.0.0",
            status=SkillStatus.ACTIVE,
        )
        registry._add_skill(base_skill)

        # Get current active
        active = registry.get_active_skill("test_skill")
        assert active.status == SkillStatus.ACTIVE

        # Deprecate
        active.deprecate()
        assert active.status == SkillStatus.DEPRECATED
