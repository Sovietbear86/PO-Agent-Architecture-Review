"""Tests for TaskSummaryService."""

from datetime import datetime, timedelta

import pytest

from po_agent.domain.models import (
    StatusCategory,
    StatusTransition,
    Task,
    TaskPriority,
    TaskStatus,
)
from po_agent.llm.mock import MockLLMClient
from po_agent.summary.task_summary import TaskSummaryService


@pytest.fixture
def sample_task():
    """Create sample task for testing."""
    now = datetime.now()

    return Task(
        key="WMB-101",
        id="task-001",
        title="Implement user authentication",
        description="Add OAuth2 support for user login",
        status=TaskStatus.RESOLVED,
        status_category=StatusCategory.COMPLETED_PENDING,
        status_transitions=[
            StatusTransition(
                from_status=TaskStatus.OPEN,
                to_status=TaskStatus.IN_PROGRESS,
                timestamp=now - timedelta(days=10),
            ),
            StatusTransition(
                from_status=TaskStatus.IN_PROGRESS,
                to_status=TaskStatus.RESOLVED,
                timestamp=now - timedelta(days=3),
            ),
        ],
        created_at=now - timedelta(days=12),
        updated_at=now - timedelta(days=3),
        assignee="Ivanov.I.I",
        priority=TaskPriority.HIGH,
        source="test",
    )


@pytest.fixture
def service_with_llm():
    """Create service with mock LLM."""
    return TaskSummaryService(llm_client=MockLLMClient())


@pytest.fixture
def service_without_llm():
    """Create service without LLM."""
    return TaskSummaryService()


class TestGenerateStructuredSummary:
    """Tests for generate_structured_summary."""

    def test_structured_summary(self, service_without_llm, sample_task):
        """Test generating structured summary."""
        summary = service_without_llm.generate_structured_summary(sample_task)

        assert summary["key"] == "WMB-101"
        assert summary["title"] == "Implement user authentication"
        assert summary["status"]["value"] == "Resolved"
        assert summary["assignee"] == "Ivanov.I.I"
        assert "metrics" in summary
        assert "workflow_timeline" in summary

    def test_structured_summary_no_assignee(self, service_without_llm):
        """Test structured summary for task without assignee."""
        now = datetime.now()
        task = Task(
            id="task-002",
            key="WMB-102",
            title="Task without assignee",
            status=TaskStatus.OPEN,
            status_category=StatusCategory.BACKLOG,
            created_at=now,
            updated_at=now,
            source="test",
        )

        summary = service_without_llm.generate_structured_summary(task)

        assert summary["assignee"] is None


class TestGenerateLLMSummary:
    """Tests for generate_llm_summary."""

    async def _test_llm_summary(self, service_with_llm, sample_task):
        """Test generating LLM-based summary."""
        summary = await service_with_llm.generate_llm_summary(sample_task)

        assert isinstance(summary, str)
        assert len(summary) > 0

    async def _test_llm_summary_with_context(self, service_with_llm, sample_task):
        """Test generating LLM-based summary with context."""
        context = {"velocity": 5, "throughput": 10}
        summary = await service_with_llm.generate_llm_summary(sample_task, context)

        assert isinstance(summary, str)

    async def _test_llm_summary_without_llm(self, service_without_llm, sample_task):
        """Test LLM summary falls back to fallback when no LLM."""
        summary = await service_without_llm.generate_llm_summary(sample_task)

        assert isinstance(summary, str)
        assert "WMB-101" in summary


class TestGenerateFallbackSummary:
    """Tests for generate_fallback_summary."""

    def test_fallback_summary(self, service_without_llm, sample_task):
        """Test generating fallback summary."""
        summary = service_without_llm.generate_fallback_summary(sample_task)

        assert isinstance(summary, str)
        assert "WMB-101" in summary
        assert "Resolved" in summary
        assert "High" in summary

    def test_fallback_summary_no_transitions(self, service_without_llm):
        """Test fallback summary for task without transitions."""
        now = datetime.now()
        task = Task(
            id="task-003",
            key="WMB-103",
            title="New Task",
            status=TaskStatus.OPEN,
            status_category=StatusCategory.BACKLOG,
            created_at=now,
            updated_at=now,
            source="test",
        )

        summary = service_without_llm.generate_fallback_summary(task)

        assert isinstance(summary, str)
        assert "New Task" in summary


class TestGenerateBatchSummaries:
    """Tests for generate_batch_summaries."""

    def test_batch_summaries_structured(self, service_without_llm, sample_task):
        """Test generating batch structured summaries."""
        tasks = [sample_task]
        summaries = service_without_llm.generate_batch_summaries(tasks, "structured")

        assert len(summaries) == 1
        assert summaries[0]["key"] == "WMB-101"

    def test_batch_summaries_fallback(self, service_without_llm, sample_task):
        """Test generating batch fallback summaries."""
        tasks = [sample_task]
        summaries = service_without_llm.generate_batch_summaries(tasks, "fallback")

        assert len(summaries) == 1
        assert "summary" in summaries[0]


class TestGenerateBatchLLMSummaries:
    """Tests for generate_batch_llm_summaries."""

    async def _test_batch_llm_summaries(self, service_with_llm, sample_task):
        """Test generating batch LLM summaries."""
        tasks = [sample_task]
        summaries = await service_with_llm.generate_batch_llm_summaries(tasks)

        assert len(summaries) == 1
        assert isinstance(summaries[0], str)

    async def _test_batch_llm_summaries_without_llm(self, service_without_llm, sample_task):
        """Test batch LLM summaries falls back without LLM."""
        tasks = [sample_task]
        summaries = await service_without_llm.generate_batch_llm_summaries(tasks)

        assert len(summaries) == 1
        assert isinstance(summaries[0], str)


class TestTaskSummaryServiceLifecycle:
    """Tests for TaskSummaryService lifecycle."""

    def test_service_initialization(self):
        """Test service initialization."""
        service = TaskSummaryService()
        assert service is not None

    def test_service_initialization_with_params(self):
        """Test service initialization with parameters."""
        service = TaskSummaryService(llm_client=MockLLMClient(), api_port=8003)
        assert service is not None
