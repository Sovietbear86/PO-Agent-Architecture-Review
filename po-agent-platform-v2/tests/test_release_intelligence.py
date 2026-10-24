"""Tests for ReleaseIntelligence."""

import asyncio
from datetime import datetime, timedelta

import pytest

from po_agent.domain.models import (
    StatusCategory,
    Task,
    TaskPriority,
    TaskStatus,
)
from po_agent.llm.mock import MockLLMClient
from po_agent.release.intelligence import ReleaseIntelligence


@pytest.fixture
def sample_release_tasks():
    """Create sample release tasks for testing."""
    now = datetime.now()

    return [
        Task(
            key="WMB-101",
            id="task-001",
            title="Implement authentication",
            description="Add OAuth2 support for user login",
            status=TaskStatus.RESOLVED,
            status_category=StatusCategory.COMPLETED_PENDING,
            created_at=now - timedelta(days=10),
            updated_at=now - timedelta(days=2),
            assignee="Ivanov.I.I",
            priority=TaskPriority.HIGH,
            estimate_hours=8,
            source="test",
        ),
        Task(
            key="WMB-102",
            id="task-002",
            title="Fix login bug on mobile",
            description="Users cannot log in on mobile devices",
            status=TaskStatus.IN_PROGRESS,
            status_category=StatusCategory.ACTIVE_WORK,
            created_at=now - timedelta(days=7),
            updated_at=now - timedelta(days=1),
            assignee="Petrov.P.P",
            priority=TaskPriority.CRITICAL,
            estimate_hours=4,
            source="test",
        ),
        Task(
            key="WMB-103",
            id="task-003",
            title="Update documentation",
            description="Update user documentation",
            status=TaskStatus.NEED_INFO,
            status_category=StatusCategory.WAITING,
            created_at=now - timedelta(days=5),
            updated_at=now,
            assignee="Sidorov.S.S",
            priority=TaskPriority.LOW,
            estimate_hours=2,
            source="test",
        ),
        Task(
            key="WMB-104",
            id="task-004",
            title="Performance optimization",
            description="Improve query performance",
            status=TaskStatus.OPEN,
            status_category=StatusCategory.BACKLOG,
            created_at=now - timedelta(days=3),
            updated_at=now,
            priority=TaskPriority.MEDIUM,
            estimate_hours=16,
            source="test",
        ),
    ]


@pytest.fixture
def release_service():
    """Create release intelligence service."""
    return ReleaseIntelligence()


@pytest.fixture
def release_service_with_llm():
    """Create release intelligence service with mock LLM."""
    return ReleaseIntelligence(llm_client=MockLLMClient())


class TestCalculateReleaseScope:
    """Tests for calculate_release_scope."""

    def test_scope_calculation(self, release_service, sample_release_tasks):
        """Test scope calculation."""
        scope = release_service.calculate_release_scope(sample_release_tasks)

        assert scope["total_tasks"] == 4
        assert scope["total_estimate_hours"] == 30
        assert "spaces" in scope

    def test_scope_empty_tasks(self, release_service):
        """Test scope calculation with no tasks."""
        scope = release_service.calculate_release_scope([])

        assert scope["total_tasks"] == 0
        assert scope["total_estimate_hours"] == 0
        assert scope["spaces"] == []


class TestCalculateCompletionStatus:
    """Tests for calculate_completion_status."""

    def test_completion_status(self, release_service, sample_release_tasks):
        """Test completion status calculation."""
        completion = release_service.calculate_completion_status(sample_release_tasks)

        assert completion["total"] == 4
        assert completion["completed"] == 1
        assert completion["remaining"] == 3
        assert completion["percentage"] == 25.0
        assert len(completion["completed_tasks"]) == 1
        assert len(completion["remaining_tasks"]) == 3

    def test_completion_status_empty(self, release_service):
        """Test completion status with no tasks."""
        completion = release_service.calculate_completion_status([])

        assert completion["total"] == 0
        assert completion["percentage"] == 0


class TestAnalyzeBlockedTasks:
    """Tests for analyze_blocked_tasks."""

    def test_blocked_analysis(self, release_service, sample_release_tasks):
        """Test blocked tasks analysis."""
        blocked = release_service.analyze_blocked_tasks(sample_release_tasks)

        assert "total_blocked" in blocked
        assert "blocked_tasks" in blocked
        assert "blocking_reasons" in blocked

    def test_blocked_empty(self, release_service):
        """Test blocked analysis with no tasks."""
        blocked = release_service.analyze_blocked_tasks([])

        assert blocked["total_blocked"] == 0
        assert blocked["blocked_tasks"] == []


class TestCalculateDeliveryRisk:
    """Tests for calculate_delivery_risk."""

    def test_risk_analysis(self, release_service, sample_release_tasks):
        """Test delivery risk analysis."""
        risk = release_service.calculate_delivery_risk(sample_release_tasks)

        assert "overall_risk" in risk
        assert "risk_score" in risk
        assert "risks" in risk
        assert "recommendations" in risk

    def test_risk_empty(self, release_service):
        """Test risk analysis with no tasks."""
        risk = release_service.calculate_delivery_risk([])

        assert risk["overall_risk"] == "none"
        assert risk["risk_score"] == 0

    def test_risk_high_completion(self, release_service):
        """Test risk with high completion rate."""
        now = datetime.now()
        tasks = [
            Task(
                key="WMB-201",
                id="task-201",
                title="Done task",
                status=TaskStatus.CLOSED,
                status_category=StatusCategory.COMPLETED,
                created_at=now,
                updated_at=now,
                source="test",
            ),
            Task(
                key="WMB-202",
                id="task-202",
                title="Done task 2",
                status=TaskStatus.RESOLVED,
                status_category=StatusCategory.COMPLETED_PENDING,
                created_at=now,
                updated_at=now,
                source="test",
            ),
        ]

        risk = release_service.calculate_delivery_risk(tasks)

        assert risk["risk_score"] == 0
        assert risk["overall_risk"] == "none"


class TestGenerateReleaseReport:
    """Tests for generate_release_report_with_llm."""

    async def _test_release_report_async(self, release_service, sample_release_tasks):
        """Test release report generation (async)."""
        report = await release_service.generate_release_report_with_llm(sample_release_tasks)

        assert "release_summary" in report
        assert "scope" in report["release_summary"]
        assert "completion" in report["release_summary"]
        assert "risk" in report["release_summary"]

    def test_release_report(self, release_service, sample_release_tasks):
        """Test release report generation (async wrapper)."""
        asyncio.run(self._test_release_report_async(release_service, sample_release_tasks))

    async def _test_release_report_with_llm_async(self, release_service_with_llm, sample_release_tasks):
        """Test release report generation with LLM (async)."""
        report = await release_service_with_llm.generate_release_report_with_llm(sample_release_tasks)

        assert "release_summary" in report
        assert "llm_insights" in report
        assert report["llm_insights"] is not None

    def test_release_report_with_llm(self, release_service_with_llm, sample_release_tasks):
        """Test release report generation with LLM (async wrapper)."""
        asyncio.run(self._test_release_report_with_llm_async(release_service_with_llm, sample_release_tasks))


class TestReleaseIntelligenceLifecycle:
    """Tests for ReleaseIntelligence lifecycle."""

    def test_service_initialization(self):
        """Test service initialization."""
        service = ReleaseIntelligence()
        assert service is not None

    def test_service_initialization_with_llm(self):
        """Test service initialization with LLM."""
        service = ReleaseIntelligence(llm_client=MockLLMClient())
        assert service is not None
