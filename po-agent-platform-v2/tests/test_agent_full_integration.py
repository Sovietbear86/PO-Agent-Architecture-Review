"""Full Integration Tests for PO Agent Platform v2 with ADDENDUM 01.

Tests all skills with real SWTR data, member name recognition,
and Skill Evolution pipeline for skill improvement.
"""

import pytest
from datetime import datetime


class TestAgentFullIntegration:
    """Full integration tests for PO Agent Platform v2."""

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization with all skills."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1
        from po_agent.skill.registry import SkillRegistry
        from po_agent.skill.skills import INITIAL_SKILLS

        orchestrator = POOrchestratorV1()

        # Verify skill registry initialized
        assert orchestrator._skill_registry is not None
        assert orchestrator._skill_executor is not None

        # Verify all initial skills loaded
        active_skills = orchestrator._skill_registry.get_active_skills()
        assert len(active_skills) == len(INITIAL_SKILLS)

    @pytest.mark.asyncio
    async def test_get_tasks_skill_member_login(self):
        """Test get_tasks skill with member login from SWTR."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        # Query with Kalachanov login (from team_members.yaml)
        result = await orchestrator.process_request(
            query="покажи задачи Kalachanov.V.V из спринта DMS-SPRNT-1"
        )

        assert result["intent"] == "task_search"
        assert result["result"]["type"] == "task_search"

    @pytest.mark.asyncio
    async def test_get_tasks_skill_member_surname_russian(self):
        """Test get_tasks skill with Russian surname."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        # Query with Russian surname Гаранин (genitive case)
        result = await orchestrator.process_request(
            query="задачи Гаранина"
        )

        assert result["intent"] == "task_search"

    @pytest.mark.asyncio
    async def test_get_tasks_skill_member_genitive_case(self):
        """Test get_tasks skill with member name in genitive case."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        # Multiple genitive case patterns
        queries = [
            ("задачи Шалдунова", "genitive"),
            ("задачи Долговского", "genitive"),
            ("задачи Агатаевой", "genitive"),
        ]

        for query, _ in queries:
            result = await orchestrator.process_request(query)
            assert result["intent"] == "task_search"

    @pytest.mark.asyncio
    async def test_sprint_health_skill(self):
        """Test sprint_health skill with real sprint ID."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        queries = [
            "здоровье спринта OLP-SPRNT-3",
            "метрики спринта DMS-SPRNT-1",
            "OLP-SPRNT-2",  # Sprint selection pattern
        ]

        for query in queries:
            result = await orchestrator.process_request(query)
            assert result["intent"] in ["sprint_health", "task_search"]


class TestMemberNameRecognition:
    """Tests for member name recognition patterns."""

    @pytest.mark.asyncio
    async def test_member_login_patterns(self):
        """Test all member login patterns from team_members.yaml."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        # Member logins from team_members.yaml
        member_logins = [
            "Kalachanov.V.V",
            "Garanin.R.V",
            "Agataeva.A.Z",
            "Dolgovskoy.E.N",
            "Moiseev.A.N",
            "Shaldunov.A.V",
            "Goncharov.A.O",
            "Reshetnik.A",
            "Bezrukov.P.S",
        ]

        for login in member_logins:
            result = await orchestrator.process_request(f"задачи {login}")
            assert result["intent"] == "task_search"

    @pytest.mark.asyncio
    async def test_member_surname_patterns(self):
        """Test all member surname patterns (Russian genitive case)."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        # Surnames from team_members.yaml in genitive case
        surnames = [
            ("Калачанова", "Kalachanov"),
            ("Гаранина", "Garanin"),
            ("Агатаеву", "Agataeva"),
            ("Долговского", "Dolgovskoy"),
            ("Моисеева", "Moiseev"),
            ("Шалдунова", "Shaldunov"),
            ("Гончарова", "Goncharov"),
            ("Решетника", "Reshetnik"),
            ("Безрукова", "Bezrukov"),
            ("Гальцова", "Galtsov"),
            ("Алексеева", "Alekseev"),
            ("Крюкова", "Kryukov"),
        ]

        for surname, _ in surnames:
            result = await orchestrator.process_request(f"задачи {surname}")
            assert result["intent"] == "task_search"


class TestSprintIdentification:
    """Tests for sprint ID identification."""

    @pytest.mark.asyncio
    async def test_sprint_id_patterns(self):
        """Test all supported sprint ID patterns."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        # Sprint ID patterns from team_members.yaml spaces
        sprint_ids = [
            "DMS-SPRNT-1",
            "DMS-SPRNT-2",
            "OLP-SPRNT-1",
            "OLP-SPRNT-2",
            "OLP-SPRNT-3",
            "WMB-SPRNT-1",
            "WMB-SPRNT-2",
            "STS-SPRNT-1",
        ]

        for sprint_id in sprint_ids:
            # Direct sprint selection
            result = await orchestrator.process_request(sprint_id)
            # Should detect as task_search (for sprint selection)
            assert result["intent"] in ["task_search", "sprint_health"]


class TestAllSkills:
    """Tests for all skills defined in ADDENDUM 01."""

    @pytest.mark.asyncio
    async def test_task_search_skill(self):
        """Test task_search skill."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        queries = [
            "покажи задачи из спринта DMS-SPRNT-1",
            "задачи по всем спринтам",
        ]

        for query in queries:
            result = await orchestrator.process_request(query)
            assert result["intent"] == "task_search"

    @pytest.mark.asyncio
    async def test_task_summary_skill(self):
        """Test task_summary skill with specific patterns."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        # Use patterns that specifically match task_summary
        # "что по задаче" is more specific than "что умеешь"
        queries = [
            "что по задаче WMB-123",
            "описание задачи",
            "анализ задачи",
        ]

        for query in queries:
            result = await orchestrator.process_request(query)
            assert result["intent"] == "task_summary"

    @pytest.mark.asyncio
    async def test_task_quality_skill(self):
        """Test task_quality skill with specific patterns."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        # Use patterns that specifically match task_quality
        # Avoid generic patterns like "качество" which could be part of other queries
        queries = [
            "качество задачи",
            "дефекты в задаче",
            "анализ качества",
        ]

        for query in queries:
            result = await orchestrator.process_request(query)
            assert result["intent"] == "task_quality"

    @pytest.mark.asyncio
    async def test_velocity_skill(self):
        """Test velocity skill."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        queries = [
            "скорость команды",
            "velocity за последние 6 спринтов",
            "производительность команды",
        ]

        for query in queries:
            result = await orchestrator.process_request(query)
            assert result["intent"] == "velocity"

    @pytest.mark.asyncio
    async def test_team_workload_skill(self):
        """Test team_workload skill."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        queries = [
            "баланс загрузки команды",
            "загрузка сотрудников",
            "распределение задач",
        ]

        for query in queries:
            result = await orchestrator.process_request(query)
            assert result["intent"] == "team_workload"

    @pytest.mark.asyncio
    async def test_competency_match_skill(self):
        """Test competency_match skill."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        # Use patterns that match the actual router patterns
        queries = [
            "кто подходит для задачи",
            "совпадение навыков",
            "кто умеет",
        ]

        for query in queries:
            result = await orchestrator.process_request(query)
            assert result["intent"] == "competency_match"

    @pytest.mark.asyncio
    async def test_release_health_skill(self):
        """Test release_health skill."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        # Use patterns that match the actual router patterns
        queries = [
            "релизные задачи",
            "релиз готов",
            "статус релиза?",
        ]

        for query in queries:
            result = await orchestrator.process_request(query)
            assert result["intent"] == "release_health"

    @pytest.mark.asyncio
    async def test_help_skill(self):
        """Test help skill."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        queries = [
            "что ты умеешь",
            "какие скиллы есть",
            "помощь",
        ]

        for query in queries:
            result = await orchestrator.process_request(query)
            assert result["intent"] == "help"


class TestSkillEvolutionIntegration:
    """Tests for Skill Evolution integration."""

    def test_skill_improvement_candidate_creation(self):
        """Test creating skill improvement candidate."""
        from po_agent.evolution.models import (
            SkillImprovementCandidate,
            ImprovementType,
            CandidateStatus,
        )

        candidate = SkillImprovementCandidate(
            candidate_id="improve-task_search-123",
            skill_id="task_search",
            skill_version="1.0.0",
            improvement_type=ImprovementType.LOW_ACCURACY,
            threshold_value=0.7,
            current_value=0.5,
        )

        assert candidate.status == CandidateStatus.IDENTIFIED
        assert candidate.skill_id == "task_search"
        assert candidate.current_value < candidate.threshold_value

    def test_skill_evolution_pipeline_initialization(self):
        """Test SkillEvolutionPipeline initialization."""
        from po_agent.skill.registry import SkillRegistry
        from po_agent.evolution.pipeline import SkillEvolutionPipeline

        registry = SkillRegistry()
        pipeline = SkillEvolutionPipeline(registry)

        assert pipeline.registry == registry
        assert pipeline.config is not None

    def test_evolution_thresholds(self):
        """Test evolution thresholds configuration."""
        from po_agent.evolution.models import (
            EvolutionThresholds,
            SkillEvolutionConfig,
        )

        thresholds = EvolutionThresholds()

        assert thresholds.accuracy_threshold == 0.7
        assert thresholds.clarification_rate_threshold == 0.3
        assert thresholds.rating_threshold == 3.0
        assert thresholds.error_rate_threshold == 0.15
        assert thresholds.latency_threshold_ms == 500.0

    def test_feedback_analyzer_negative_text(self):
        """Test FeedbackAnalyzer with negative text."""
        from po_agent.evolution.feedback_analyzer import FeedbackAnalyzer

        analyzer = FeedbackAnalyzer()

        result = analyzer.analyze_text("Неправильно, ошибка!")

        assert result["is_negative"] is True
        assert result["negative_count"] > 0

    def test_feedback_analyzer_positive_text(self):
        """Test FeedbackAnalyzer with positive text."""
        from po_agent.evolution.feedback_analyzer import FeedbackAnalyzer

        analyzer = FeedbackAnalyzer()

        result = analyzer.analyze_text("Отлично, очень помогло!")

        assert result["is_negative"] is False
        assert result["positive_count"] > 0


class TestRealSWTRDataIntegration:
    """Tests for real SWTR data integration."""

    @pytest.mark.asyncio
    async def test_dms_sprint_queries(self):
        """Test queries with DMS space data."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        # DMS space queries
        queries = [
            ("задачи из спринта DMS-SPRNT-1", "task_search"),
            ("здоровье спринта DMS-SPRNT-1", "sprint_health"),
        ]

        for query, expected_intent in queries:
            result = await orchestrator.process_request(query)
            assert result["intent"] == expected_intent

    @pytest.mark.asyncio
    async def test_olap_sprint_queries(self):
        """Test queries with OLAP (OLP) space data."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        # OLP space queries
        queries = [
            ("задачи из спринта OLP-SPRNT-3", "task_search"),
            ("скорость команды OLP", "velocity"),
        ]

        for query, expected_intent in queries:
            result = await orchestrator.process_request(query)
            assert result["intent"] == expected_intent

    @pytest.mark.asyncio
    async def test_multiline_team_member_queries(self):
        """Test queries with multiple team members."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        queries = [
            "задачи Гаранина и Шалдунова из спринта OLP-SPRNT-5",
            "баланс загрузки команды (Калачанов, Долговской, Агатаева)",
        ]

        for query in queries:
            result = await orchestrator.process_request(query)
            # Should process query and return appropriate intent
            assert result["intent"] is not None


class TestClarificationPipeline:
    """Tests for clarification pipeline integration."""

    def test_clarification_request_generation(self):
        """Test clarification request generation."""
        from po_agent.clarification.engine import ClarificationEngine
        from po_agent.clarification.options import OptionsGenerator
        from po_agent.clarification.models import ClarificationRequest, ClarificationStatus
        from po_agent.models.resolved_context import ResolvedContext, ContextSource

        engine = ClarificationEngine()

        # Create context that needs clarification (explicitly set needs_clarification)
        context = ResolvedContext(
            query="покажи задачи Гаранина",
            intent="task_search",
            sprint_id=None,  # Missing required field
            source=ContextSource.CURRENT_REQUEST,
            needs_clarification=True,
            missing_fields=["sprint_id"],
        )

        # Check if clarification is needed
        request = engine.needs_clarification(context, ["sprint_id"])

        assert request is not None
        # ClarificationRequest doesn't have status - that's on ClarificationResponse
        assert request.missing_fields == ["sprint_id"]
        assert "sprint" in request.question.lower() or "спринт" in request.question.lower()

    @pytest.mark.asyncio
    async def test_clarification_loop_management(self):
        """Test clarification loop management."""
        from po_agent.clarification.loop import ClarificationLoop
        from po_agent.clarification.models import (
            ClarificationRequest,
            ClarificationStatus,
        )
        from po_agent.memory.session_memory import SessionMemory

        session_memory = SessionMemory()
        loop = ClarificationLoop(session_memory=session_memory)

        # Create proper clarification request with all required fields
        from po_agent.clarification.options import OptionsGenerator

        options = OptionsGenerator.from_sprints(
            ["Вариант 1", "Вариант 2"]
        )

        request = ClarificationRequest(
            question="Уточните спринт",
            options=options,
            context={"member": "Гаранин"},
            reason="sprint_id_required",
            missing_fields=["sprint_id"],
            original_query="покажи задачи Гаранина",
        )

        # Start clarification
        response = loop.start_clarification(request)

        # Note: status is PENDING when stored, but the response has needs_clarification
        # Check pending_request is stored
        assert "pending_request" in response.model_dump()
        assert response.clarification_id == request.clarification_id
