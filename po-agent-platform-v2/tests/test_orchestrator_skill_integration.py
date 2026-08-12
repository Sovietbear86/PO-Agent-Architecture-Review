"""Integration tests for POOrchestrator with Skill Registry."""

import pytest

from po_agent.domain.models import Task


class TestPOOrchestratorSkillIntegration:
    """POOrchestrator Skill Registry integration tests."""

    @pytest.mark.asyncio
    async def test_orchestrator_uses_skill_registry(self):
        """Test orchestrator initializes with skill registry."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        assert orchestrator._skill_registry is not None
        assert orchestrator._skill_executor is not None

    @pytest.mark.asyncio
    async def test_orchestrator_resolve_intent_to_skill(self):
        """Test orchestrator uses skill resolver."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        # Simulate intent classification
        intent = "task_search"
        skill_info = orchestrator._router.resolve_intent_to_skill(intent)

        assert skill_info is not None
        assert skill_info["skill_id"] == "task_search"

    @pytest.mark.asyncio
    async def test_orchestrator_execute_with_skill(self):
        """Test orchestrator executes with skill info."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        skill_info = {
            "skill_id": "task_search",
            "skill_name": "Поиск задач",
            "skill_version": "1.0.0",
            "required_context": ["sprint_id"],
            "optional_context": ["member_login"],
            "allowed_capabilities": ["search_tasks"],
            "workflow": [],
        }

        entities = []

        result = await orchestrator._execute_with_skill(skill_info, entities, [])

        assert result is not None
        assert "type" in result

    @pytest.mark.asyncio
    async def test_orchestrator_execute_with_missing_context(self):
        """Test orchestrator handles missing required context."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        skill_info = {
            "skill_id": "task_search",
            "skill_name": "Поиск задач",
            "skill_version": "1.0.0",
            "required_context": ["sprint_id"],
            "optional_context": [],
            "allowed_capabilities": ["search_tasks"],
            "workflow": [],
        }

        entities = []  # No sprint_id

        result = await orchestrator._execute_with_skill(skill_info, entities, [])

        assert result["type"] == "clarification_required"
        assert "sprint_id" in result["missing_context"]


class TestPOOrchestratorIntegration:
    """POOrchestrator integration tests."""

    @pytest.mark.asyncio
    async def test_process_request_with_skill_registry(self):
        """Test full request processing with skill registry."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        query = "покажи задачи из спринта DMS-SPRNT-1"

        result = await orchestrator.process_request(query)

        assert "query" in result
        assert "intent" in result
        assert "result" in result
        assert result["intent"] == "task_search"

    @pytest.mark.asyncio
    async def test_process_request_help_intent(self):
        """Test help intent processing."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        query = "помощь"

        result = await orchestrator.process_request(query)

        assert result["intent"] == "help"
        assert result["result"]["type"] == "help"

    @pytest.mark.asyncio
    async def test_process_request_sprint_health(self):
        """Test sprint health intent processing."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        query = "покажи здоровье спринта DMS-SPRNT-1"

        result = await orchestrator.process_request(query)

        assert result["intent"] == "sprint_health"
        assert result["result"]["type"] == "sprint_health"
