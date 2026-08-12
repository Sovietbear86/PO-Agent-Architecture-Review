"""Tests for Skill Executor."""

import pytest

from po_agent.skill.executor import SkillExecutor, SkillExecutionError
from po_agent.skill.registry import SkillRegistry
from po_agent.skill.models import SkillDefinition, SkillStatus, WorkflowStep
from po_agent.models.resolved_context import ResolvedContext, ContextSource


class TestSkillExecutor:
    """SkillExecutor tests."""

    def test_init(self):
        """Test executor initialization."""
        registry = SkillRegistry()
        executor = SkillExecutor(registry)
        assert executor.registry == registry
        assert executor.capability_resolver is None

    def test_execute_valid_skill(self):
        """Test executing a valid skill."""
        registry = SkillRegistry()
        skill = SkillDefinition(
            skill_id="task_search",
            name="Поиск задач",
            version="1.0.0",
            required_context=[],
        )
        registry._add_skill(skill)

        context = ResolvedContext()
        executor = SkillExecutor(registry)

        result = executor.execute("task_search", context)

        assert result["skill_id"] == "task_search"
        assert result["version"] == "1.0.0"
        assert result["status"] == "completed"

    def test_execute_missing_required_context(self):
        """Test execution with missing required context."""
        registry = SkillRegistry()
        skill = SkillDefinition(
            skill_id="task_search",
            name="Поиск задач",
            version="1.0.0",
            required_context=["sprint_id"],
        )
        registry._add_skill(skill)

        context = ResolvedContext()  # No sprint_id
        executor = SkillExecutor(registry)

        with pytest.raises(SkillExecutionError) as exc_info:
            executor.execute("task_search", context)

        assert "sprint_id" in str(exc_info.value)

    def test_execute_nonexistent_skill(self):
        """Test executing nonexistent skill."""
        registry = SkillRegistry()
        context = ResolvedContext()
        executor = SkillExecutor(registry)

        with pytest.raises(SkillExecutionError) as exc_info:
            executor.execute("nonexistent", context)

        assert "not found" in str(exc_info.value).lower()

    def test_execute_with_error_handling(self):
        """Test execution with error handling."""
        registry = SkillRegistry()
        skill = SkillDefinition(
            skill_id="task_search",
            name="Поиск задач",
            version="1.0.0",
            required_context=["sprint_id"],
        )
        registry._add_skill(skill)

        context = ResolvedContext()
        executor = SkillExecutor(registry)

        result = executor.execute_with_error_handling("task_search", context)

        assert result["status"] == "error"
        assert "sprint_id" in result["error"]


class TestSkillExecutorWithInitialSkills:
    """Tests with initial skills."""

    def test_execute_sprint_health_skill(self):
        """Test executing sprint_health skill."""
        from po_agent.skill.skills import SKILL_SPRINT_HEALTH

        registry = SkillRegistry()
        registry.load_skills_from_dict([SKILL_SPRINT_HEALTH])

        context = ResolvedContext(
            sprint_id="DMS-SPRNT-1",
        )
        executor = SkillExecutor(registry)

        result = executor.execute("sprint_health", context)

        assert result["skill_id"] == "sprint_health"
        assert result["version"] == "1.0.0"


class TestSkillExecutionError:
    """SkillExecutionError tests."""

    def test_error_message(self):
        """Test error message."""
        error = SkillExecutionError("Test error")
        assert str(error) == "Test error"
