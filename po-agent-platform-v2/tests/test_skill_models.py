"""Tests for Skill models."""

import pytest

from po_agent.skill.models import (
    SkillDefinition,
    SkillStatus,
    ClarificationPolicy,
    WorkflowStep,
)


class TestSkillDefinition:
    """SkillDefinition model tests."""

    def test_create_skill(self):
        """Test creating a skill definition."""
        skill = SkillDefinition(
            skill_id="task_search",
            name="Поиск задач",
            version="1.0.0",
        )
        assert skill.skill_id == "task_search"
        assert skill.name == "Поиск задач"
        assert skill.version == "1.0.0"
        assert skill.status == SkillStatus.ACTIVE
        assert skill.required_context == []
        assert skill.optional_context == []

    def test_skill_with_all_fields(self):
        """Test creating skill with all fields."""
        skill = SkillDefinition(
            skill_id="sprint_health",
            name="Здоровье спринта",
            version="1.0.0",
            status=SkillStatus.ACTIVE,
            intents=["sprint_health"],
            description="Метрики спринта",
            required_context=["sprint_id"],
            optional_context=["member_login"],
            clarification_policy=ClarificationPolicy.AUTO,
            allowed_capabilities=["get_sprint"],
            fallback_policy="return_error",
            eval_tags=["metrics", "sprint"],
        )

        assert skill.description == "Метрики спринта"
        assert skill.required_context == ["sprint_id"]
        assert skill.clarification_policy == ClarificationPolicy.AUTO

    def test_skill_to_dict(self):
        """Test converting skill to dictionary."""
        skill = SkillDefinition(
            skill_id="task_search",
            name="Поиск задач",
            version="1.0.0",
        )

        result = skill.to_dict()

        assert result["skill_id"] == "task_search"
        assert result["version"] == "1.0.0"
        assert result["status"] == "active"

    def test_activate_skill(self):
        """Test activating a skill."""
        skill = SkillDefinition(
            skill_id="task_search",
            name="Поиск задач",
            version="1.0.0",
        )
        skill.activate(approved_by="user123")

        assert skill.status == SkillStatus.ACTIVE
        assert skill.approved_by == "user123"

    def test_deprecate_skill(self):
        """Test deprecating a skill."""
        skill = SkillDefinition(
            skill_id="task_search",
            name="Поиск задач",
            version="1.0.0",
        )
        skill.deprecate()

        assert skill.status == SkillStatus.DEPRECATED

    def test_reject_skill(self):
        """Test rejecting a skill."""
        skill = SkillDefinition(
            skill_id="task_search",
            name="Поиск задач",
            version="1.0.0",
        )
        skill.reject()

        assert skill.status == SkillStatus.REJECTED

    def test_add_version(self):
        """Test adding a new version."""
        skill = SkillDefinition(
            skill_id="task_search",
            name="Поиск задач",
            version="1.0.0",
        )
        skill.add_version("1.1.0", "Added new features", approved_by="admin")

        assert skill.version == "1.1.0"
        assert len(skill.version_history) == 1
        assert skill.version_history[0]["version"] == "1.1.0"


class TestWorkflowStep:
    """WorkflowStep model tests."""

    def test_create_workflow_step(self):
        """Test creating a workflow step."""
        step = WorkflowStep(
            name="load_data",
            description="Load data from source",
        )
        assert step.name == "load_data"
        assert step.description == "Load data from source"
        assert step.capability is None

    def test_workflow_step_with_mapping(self):
        """Test workflow step with mappings."""
        step = WorkflowStep(
            name="transform",
            description="Transform data",
            capability="transform_data",
            input_mapping={"source_field": "target_field"},
            output_mapping={"result": "output_field"},
        )
        assert step.capability == "transform_data"
        assert step.input_mapping == {"source_field": "target_field"}
        assert step.output_mapping == {"result": "output_field"}


class TestSkillStatus:
    """SkillStatus enum tests."""

    def test_all_statuses(self):
        """Test all status values."""
        assert SkillStatus.CANDIDATE.value == "candidate"
        assert SkillStatus.ACTIVE.value == "active"
        assert SkillStatus.DEPRECATED.value == "deprecated"
        assert SkillStatus.REJECTED.value == "rejected"
