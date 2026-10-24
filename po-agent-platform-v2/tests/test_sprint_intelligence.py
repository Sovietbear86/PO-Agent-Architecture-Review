"""Tests for SprintIntelligence."""

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
from po_agent.sprint.intelligence import SprintIntelligence


@pytest.fixture
def sample_sprint_tasks():
    """Create sample sprint tasks for testing."""
    now = datetime.now()

    return [
        Task(
            key="WMB-101",
            id="task-001",
            title="Implement authentication",
            description="Add OAuth2 support",
            status=TaskStatus.RESOLVED,
            status_category=StatusCategory.COMPLETED_PENDING,
            created_at=now - timedelta(days=10),
            updated_at=now - timedelta(days=2),
            assignee="Ivanov.I.I",
            priority=TaskPriority.HIGH,
            source="test",
        ),
        Task(
            key="WMB-102",
            id="task-002",
            title="Fix login bug",
            description="Users cannot log in",
            status=TaskStatus.IN_PROGRESS,
            status_category=StatusCategory.ACTIVE_WORK,
            created_at=now - timedelta(days=8),
            updated_at=now - timedelta(days=1),
            assignee="Petrov.P.P",
            priority=TaskPriority.CRITICAL,
            source="test",
        ),
        Task(
            key="WMB-103",
            id="task-003",
            title="Update docs",
            description="Update user documentation",
            status=TaskStatus.OPEN,
            status_category=StatusCategory.BACKLOG,
            created_at=now - timedelta(days=5),
            updated_at=now,
            assignee="Sidorov.S.S",
            priority=TaskPriority.LOW,
            source="test",
        ),
        Task(
            key="WMB-104",
            id="task-004",
            title="Security audit",
            description="Security review",
            status=TaskStatus.NEED_INFO,
            status_category=StatusCategory.WAITING,
            created_at=now - timedelta(days=3),
            updated_at=now,
            assignee=None,
            priority=TaskPriority.CRITICAL,
            source="test",
        ),
    ]


@pytest.fixture
def sprint_service():
    """Create sprint intelligence service."""
    return SprintIntelligence()


@pytest.fixture
def sprint_service_with_llm():
    """Create sprint intelligence service with mock LLM."""
    return SprintIntelligence(llm_client=MockLLMClient())


class TestCalculateSprintHealth:
    """Tests for calculate_sprint_health."""

    def test_health_with_completed_tasks(self, sprint_service, sample_sprint_tasks):
        """Test health calculation with mostly completed tasks."""
        health = sprint_service.calculate_sprint_health(sample_sprint_tasks)

        assert health["score"] >= 0
        assert health["score"] <= 100
        assert health["status"] in ["healthy", "watching", "at_risk", "in_danger"]
        assert "breakdown" in health
        assert "issues" in health

    def test_health_no_tasks(self, sprint_service):
        """Test health calculation with no tasks."""
        health = sprint_service.calculate_sprint_health([])

        assert health["score"] == 0
        assert health["status"] == "no_tasks"
        assert health["breakdown"] == {}

    def test_health_with_blocked_tasks(self, sprint_service):
        """Test health calculation with blocked tasks."""
        now = datetime.now()
        tasks = [
            Task(
                key="WMB-201",
                id="task-201",
                title="Blocked task",
                status=TaskStatus.NEED_INFO,
                status_category=StatusCategory.WAITING,
                created_at=now,
                updated_at=now,
                source="test",
            ),
        ]

        health = sprint_service.calculate_sprint_health(tasks)

        assert health["score"] < 80  # Blocked should lower score
        assert len(health["issues"]) > 0


class TestCalculateCompletionRatio:
    """Tests for calculate_completion_ratio."""

    def test_completion_ratio(self, sprint_service, sample_sprint_tasks):
        """Test completion ratio calculation."""
        ratio = sprint_service.calculate_completion_ratio(sample_sprint_tasks)

        assert ratio["total"] == 4
        assert ratio["completed"] == 1
        assert ratio["remaining"] == 3
        assert ratio["percentage"] == 25.0

    def test_completion_ratio_no_tasks(self, sprint_service):
        """Test completion ratio with no tasks."""
        ratio = sprint_service.calculate_completion_ratio([])

        assert ratio["total"] == 0
        assert ratio["completed"] == 0
        assert ratio["percentage"] == 0

    def test_completion_ratio_all_completed(self, sprint_service):
        """Test completion ratio with all tasks completed."""
        now = datetime.now()
        tasks = [
            Task(
                key="WMB-301",
                id="task-301",
                title="Done task",
                status=TaskStatus.CLOSED,
                status_category=StatusCategory.COMPLETED,
                created_at=now,
                updated_at=now,
                source="test",
            ),
            Task(
                key="WMB-302",
                id="task-302",
                title="Resolved task",
                status=TaskStatus.RESOLVED,
                status_category=StatusCategory.COMPLETED_PENDING,
                created_at=now,
                updated_at=now,
                source="test",
            ),
        ]

        ratio = sprint_service.calculate_completion_ratio(tasks)

        assert ratio["total"] == 2
        assert ratio["completed"] == 2
        assert ratio["percentage"] == 100.0


class TestPredictVelocity:
    """Tests for predict_velocity."""

    def test_velocity_current_sprint(self, sprint_service, sample_sprint_tasks):
        """Test velocity calculation for current sprint."""
        velocity = sprint_service.predict_velocity(sample_sprint_tasks)

        assert velocity["current_sprint"]["total"] == 4
        assert velocity["current_sprint"]["completed"] == 1
        assert velocity["current_sprint"]["velocity"] == 1

    def test_velocity_with_historical_data(self, sprint_service, sample_sprint_tasks):
        """Test velocity prediction with historical data."""
        now = datetime.now()
        historical = [
            [
                Task(
                    key="WMB-201",
                    id="hist-101",
                    title="Old task 1",
                    status=TaskStatus.RESOLVED,
                    status_category=StatusCategory.COMPLETED_PENDING,
                    created_at=now,
                    updated_at=now,
                    source="test",
                ),
                Task(
                    key="WMB-202",
                    id="hist-102",
                    title="Old task 2",
                    status=TaskStatus.CLOSED,
                    status_category=StatusCategory.COMPLETED,
                    created_at=now,
                    updated_at=now,
                    source="test",
                ),
            ],
            [
                Task(
                    key="WMB-203",
                    id="hist-103",
                    title="Old task 3",
                    status=TaskStatus.RESOLVED,
                    status_category=StatusCategory.COMPLETED_PENDING,
                    created_at=now,
                    updated_at=now,
                    source="test",
                ),
            ],
        ]

        velocity = sprint_service.predict_velocity(sample_sprint_tasks, historical)

        assert "historical" in velocity
        assert "average_velocity" in velocity["historical"]
        assert velocity["historical"]["average_velocity"] == 1.5

    def test_velocity_without_historical_data(self, sprint_service, sample_sprint_tasks):
        """Test velocity without historical data."""
        velocity = sprint_service.predict_velocity(sample_sprint_tasks, None)

        assert "historical" not in velocity or velocity.get("historical") is None
        assert "predictions" in velocity


class TestAnalyzeSprintRisks:
    """Tests for analyze_sprint_risks."""

    def test_risks_analysis(self, sprint_service, sample_sprint_tasks):
        """Test risk analysis."""
        risks = sprint_service.analyze_sprint_risks(sample_sprint_tasks)

        assert "overall_risk" in risks
        assert "risks" in risks
        assert "recommendations" in risks

    def test_risks_no_tasks(self, sprint_service):
        """Test risk analysis with no tasks."""
        risks = sprint_service.analyze_sprint_risks([])

        assert risks["overall_risk"] == "none"
        assert risks["risks"] == []
        assert risks["recommendations"] == []

    def test_risks_high_priority(self, sprint_service):
        """Test risk analysis with high priority tasks."""
        now = datetime.now()
        tasks = [
            Task(
                key="WMB-401",
                id="task-401",
                title="Critical task",
                status=TaskStatus.OPEN,
                status_category=StatusCategory.BACKLOG,
                created_at=now,
                updated_at=now,
                priority=TaskPriority.CRITICAL,
                source="test",
            ),
            Task(
                key="WMB-402",
                id="task-402",
                title="Critical task 2",
                status=TaskStatus.OPEN,
                status_category=StatusCategory.BACKLOG,
                created_at=now,
                updated_at=now,
                priority=TaskPriority.CRITICAL,
                source="test",
            ),
        ]

        risks = sprint_service.analyze_sprint_risks(tasks)

        assert risks["overall_risk"] in ["medium", "high"]
        assert any(r["type"] == "high_priority" for r in risks["risks"])


class TestGenerateSprintReport:
    """Tests for generate_sprint_report_with_llm."""

    async def _test_sprint_report(self, sprint_service, sample_sprint_tasks):
        """Test sprint report generation."""
        report = await sprint_service.generate_sprint_report_with_llm(sample_sprint_tasks)

        assert "sprint_summary" in report
        assert "detailed_metrics" in report
        assert report["sprint_summary"]["total_tasks"] == 4

    def test_sprint_report(self, sprint_service, sample_sprint_tasks):
        """Test sprint report generation (async wrapper)."""
        asyncio.run(self._test_sprint_report(sprint_service, sample_sprint_tasks))

    async def _test_sprint_report_with_llm(self, sprint_service_with_llm, sample_sprint_tasks):
        """Test sprint report generation with LLM."""
        report = await sprint_service_with_llm.generate_sprint_report_with_llm(sample_sprint_tasks)

        assert "sprint_summary" in report
        assert "llm_insights" in report
        assert report["llm_insights"] is not None

    def test_sprint_report_with_llm(self, sprint_service_with_llm, sample_sprint_tasks):
        """Test sprint report generation with LLM (async wrapper)."""
        asyncio.run(self._test_sprint_report_with_llm(sprint_service_with_llm, sample_sprint_tasks))


class TestSprintIntelligenceLifecycle:
    """Tests for SprintIntelligence lifecycle."""

    def test_service_initialization(self):
        """Test service initialization."""
        service = SprintIntelligence()
        assert service is not None

    def test_service_initialization_with_llm(self):
        """Test service initialization with LLM."""
        service = SprintIntelligence(llm_client=MockLLMClient())
        assert service is not None
