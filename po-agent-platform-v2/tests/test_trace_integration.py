"""Integration tests for Trace/Feedback/Eval with Skill Registry."""

import pytest

from po_agent.history.store import TraceEntry
from po_agent.feedback.store import FeedbackEntry, FeedbackType


class TestTraceSkillIntegration:
    """Trace Skill Registry integration tests."""

    def test_trace_entry_with_skill_fields(self):
        """Test TraceEntry includes skill fields."""
        from datetime import datetime

        trace = TraceEntry(
            trace_id="test-1",
            request_id="req-1",
            timestamp=datetime.now(),
            request="test query",
            intent="task_search",
            intent_confidence=0.9,
            latency_ms=100.0,
            skill_id="task_search",
            skill_version="1.0.0",
            skill_status="completed",
        )

        assert trace.skill_id == "task_search"
        assert trace.skill_version == "1.0.0"
        assert trace.skill_status == "completed"

    def test_trace_entry_skill_fields_optional(self):
        """Test skill fields are optional."""
        from datetime import datetime

        trace = TraceEntry(
            trace_id="test-2",
            request_id="req-2",
            timestamp=datetime.now(),
            request="test query",
            intent="help",
            intent_confidence=1.0,
            latency_ms=50.0,
        )

        assert trace.skill_id is None
        assert trace.skill_version is None
        assert trace.skill_status is None


class TestFeedbackSkillIntegration:
    """Feedback Skill Registry integration tests."""

    def test_feedback_entry_with_skill_fields(self):
        """Test FeedbackEntry includes skill fields."""
        from datetime import datetime

        feedback = FeedbackEntry(
            feedback_id="fb-1",
            trace_id="trace-1",
            timestamp=datetime.now(),
            feedback_type=FeedbackType.THUMBS_UP,
            data={"comment": "Great answer!"},
            skill_id="task_search",
            skill_version="1.0.0",
            skill_rating=5,
        )

        assert feedback.skill_id == "task_search"
        assert feedback.skill_version == "1.0.0"
        assert feedback.skill_rating == 5

    def test_feedback_entry_skill_fields_optional(self):
        """Test skill fields are optional in feedback."""
        from datetime import datetime

        feedback = FeedbackEntry(
            feedback_id="fb-2",
            trace_id="trace-2",
            timestamp=datetime.now(),
            feedback_type=FeedbackType.COMMENT,
            data={"comment": "Nice"},
        )

        assert feedback.skill_id is None
        assert feedback.skill_version is None
        assert feedback.skill_rating is None

    def test_feedback_data_skill_info(self):
        """Test feedback data includes skill info."""
        from datetime import datetime

        feedback = FeedbackEntry(
            feedback_id="fb-3",
            trace_id="trace-3",
            timestamp=datetime.now(),
            feedback_type=FeedbackType.THUMBS_UP,
            data={
                "comment": "Good",
                "skill_id": "sprint_health",
                "skill_version": "1.0.0",
                "skill_rating": 4,
            },
        )

        assert feedback.data["skill_id"] == "sprint_health"
        assert feedback.data["skill_version"] == "1.0.0"
        assert feedback.data["skill_rating"] == 4


class TestSkillEvaluation:
    """Skill Evaluation metrics tests."""

    def test_skill_metrics_calculation(self):
        """Test skill metrics calculations."""
        from po_agent.evaluation.metrics import SkillEvaluation

        evaluation = SkillEvaluation()

        # Record some requests
        evaluation.record_request(
            skill_id="task_search",
            skill_version="1.0.0",
            latency_ms=100,
            confidence=0.9,
            success=True,
        )
        evaluation.record_request(
            skill_id="task_search",
            skill_version="1.0.0",
            latency_ms=150,
            confidence=0.8,
            success=True,
        )
        evaluation.record_request(
            skill_id="task_search",
            skill_version="1.0.0",
            latency_ms=200,
            confidence=0.7,
            success=False,
        )

        # Check the internal metrics storage
        key = "task_search:1.0.0"
        metrics = evaluation._metrics[key]["1.0.0"]

        assert metrics.total_requests == 3
        assert metrics.successful_requests == 2
        assert metrics.failed_requests == 1
        assert metrics.accuracy == pytest.approx(2/3, rel=1e-3)

    def test_skill_metrics_clarification(self):
        """Test clarification tracking."""
        from po_agent.evaluation.metrics import SkillEvaluation

        evaluation = SkillEvaluation()

        evaluation.record_request(
            skill_id="task_search",
            skill_version="1.0.0",
            latency_ms=100,
            confidence=0.9,
            success=False,
            clarification_required=True,
        )
        evaluation.record_request(
            skill_id="task_search",
            skill_version="1.0.0",
            latency_ms=100,
            confidence=0.9,
            success=True,
            clarification_required=False,
        )

        # Check the internal metrics storage
        key = "task_search:1.0.0"
        metrics = evaluation._metrics[key]["1.0.0"]

        assert metrics.clarification_required == 1
        assert metrics.clarification_rate == pytest.approx(0.5, rel=1e-3)

    def test_skill_metrics_rating(self):
        """Test rating tracking."""
        from po_agent.evaluation.metrics import SkillEvaluation

        evaluation = SkillEvaluation()

        # First record a request to initialize metrics
        evaluation.record_request(
            skill_id="task_search",
            skill_version="1.0.0",
            latency_ms=100,
            confidence=0.9,
            success=True,
        )

        evaluation.record_rating("task_search", "1.0.0", 5)
        evaluation.record_rating("task_search", "1.0.0", 4)
        evaluation.record_rating("task_search", "1.0.0", 3)

        # Check the internal metrics storage
        key = "task_search:1.0.0"
        metrics = evaluation._metrics[key]["1.0.0"]

        assert metrics.ratings == [5, 4, 3]
        assert metrics.avg_rating == 4.0

    def test_get_all_skills_metrics(self):
        """Test getting metrics for all skills."""
        from po_agent.evaluation.metrics import SkillEvaluation

        evaluation = SkillEvaluation()

        evaluation.record_request("task_search", "1.0.0", 100, 0.9, True)
        evaluation.record_request("sprint_health", "1.0.0", 200, 0.8, True)

        all_metrics = evaluation.get_all_skills_metrics()

        assert len(all_metrics) == 2
        skill_ids = [m.skill_id for m in all_metrics]
        assert "task_search" in skill_ids
        assert "sprint_health" in skill_ids


class TestOrchestratorTraceIntegration:
    """Orchestrator Trace integration tests."""

    @pytest.mark.asyncio
    async def test_orchestrator_processes_request(self):
        """Test orchestrator processes request with skill tracking."""
        from po_agent.orchestration.orchestrator import POOrchestratorV1

        orchestrator = POOrchestratorV1()

        query = "покажи задачи"

        result = await orchestrator.process_request(query)

        # Check that response contains required fields
        assert "query" in result
        assert "intent" in result
        assert "result" in result
