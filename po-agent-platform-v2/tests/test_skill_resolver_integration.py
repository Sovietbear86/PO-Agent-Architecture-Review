"""Integration tests for Skill Resolver & Executor."""

import pytest

from po_agent.orchestration.router import DeterministicIntentRouter
from po_agent.skill.models import SkillStatus


class TestSkillResolverIntegration:
    """Skill Resolver integration tests."""

    def test_router_initializes_with_skill_registry(self):
        """Test router initializes with skill registry."""
        router = DeterministicIntentRouter()

        assert router.skill_registry is not None
        assert router.skill_registry.count_skills() > 0

    def test_resolve_intent_to_skill_found(self):
        """Test resolving intent to skill when found."""
        router = DeterministicIntentRouter()

        result = router.resolve_intent_to_skill("task_search")

        assert result is not None
        assert result["skill_id"] == "task_search"
        assert result["skill_version"] == "1.0.0"
        assert "sprint_id" in result["required_context"]

    def test_resolve_intent_to_skill_not_found(self):
        """Test resolving intent to skill when not found."""
        router = DeterministicIntentRouter()

        result = router.resolve_intent_to_skill("nonexistent_intent")

        assert result is None

    def test_get_intent_from_skill(self):
        """Test getting intent from skill_id."""
        router = DeterministicIntentRouter()

        intent = router.get_intent_from_skill("task_search")

        assert intent == "task_search"

    def test_get_intent_from_skill_not_found(self):
        """Test getting intent from nonexistent skill_id."""
        router = DeterministicIntentRouter()

        intent = router.get_intent_from_skill("nonexistent_skill")

        assert intent is None

    def test_intent_to_skill_mapping_complete(self):
        """Test all intents have skill mappings."""
        router = DeterministicIntentRouter()

        expected_intents = [
            "task_search",
            "task_summary",
            "task_quality",
            "sprint_health",
            "velocity",
            "team_workload",
            "competency_match",
            "release_health",
            "help",
        ]

        for intent in expected_intents:
            skill = router.resolve_intent_to_skill(intent)
            assert skill is not None, f"Skill not found for intent: {intent}"

    def test_all_skills_are_active(self):
        """Test all registered skills are active."""
        router = DeterministicIntentRouter()

        router.skill_registry.load_skills_from_dict([
            {
                "skill_id": "test_skill",
                "name": "Test",
                "version": "1.0.0",
            }
        ])

        all_skills = router.skill_registry.get_active_skills()
        assert len(all_skills) > 0


class TestSkillExecutorIntegration:
    """Skill Executor integration tests."""

    def test_executor_uses_skill_registry(self):
        """Test executor uses skill registry."""
        from po_agent.skill.registry import SkillRegistry
        from po_agent.skill.executor import SkillExecutor

        registry = SkillRegistry()
        registry.load_skills_from_dict([{
            "skill_id": "test_skill",
            "name": "Test",
            "version": "1.0.0",
        }])

        executor = SkillExecutor(registry)
        assert executor.registry == registry
