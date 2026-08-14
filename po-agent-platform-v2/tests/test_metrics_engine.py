"""Tests for MetricsEngine."""

from datetime import datetime, timedelta

import pytest

from po_agent.domain.models import (
    StatusCategory,
    StatusTransition,
    Task,
    TaskStatus,
)
from po_agent.metrics.engine import MetricsEngine


@pytest.fixture
def engine():
    """Create MetricsEngine instance."""
    return MetricsEngine()


@pytest.fixture
def sample_tasks():
    """Create sample tasks for testing."""
    now = datetime.now()

    return [
        # Completed task with transitions
        Task(
            key="WMB-101",
            id="task-001",
            title="Completed Task",
            description="Task that was completed",
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
            source="test",
        ),
        # Task currently in progress
        Task(
            key="WMB-102",
            id="task-002",
            title="In Progress Task",
            description="Task currently in progress",
            status=TaskStatus.IN_PROGRESS,
            status_category=StatusCategory.ACTIVE_WORK,
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(days=2),
            source="test",
        ),
        # Task waiting for info
        Task(
            key="WMB-103",
            id="task-003",
            title="Waiting Task",
            description="Task waiting for information",
            status=TaskStatus.NEED_INFO,
            status_category=StatusCategory.WAITING,
            status_transitions=[
                StatusTransition(
                    from_status=TaskStatus.OPEN,
                    to_status=TaskStatus.IN_PROGRESS,
                    timestamp=now - timedelta(days=8),
                ),
                StatusTransition(
                    from_status=TaskStatus.IN_PROGRESS,
                    to_status=TaskStatus.NEED_INFO,
                    timestamp=now - timedelta(days=5),
                ),
            ],
            created_at=now - timedelta(days=10),
            updated_at=now - timedelta(days=5),
            source="test",
        ),
    ]


class TestCalculateThroughput:
    """Tests for calculate_throughput."""

    def test_throughput_calculation(self, engine, sample_tasks):
        """Test throughput calculation."""
        metrics = engine.calculate_throughput(sample_tasks, period_days=30)

        assert "completed_count" in metrics
        assert "throughput" in metrics
        assert metrics["completed_count"] >= 0
        assert metrics["throughput"] >= 0

    def test_throughput_empty_tasks(self, engine):
        """Test throughput with empty task list."""
        metrics = engine.calculate_throughput([], period_days=30)

        assert metrics["completed_count"] == 0
        assert metrics["throughput"] == 0

    def test_throughput_all_completed(self, engine):
        """Test throughput when all tasks are completed."""
        now = datetime.now()
        tasks = [
            Task(
                key="WMB-104",
                id="task-004",
                title="Task 1",
                status=TaskStatus.RESOLVED,
                status_category=StatusCategory.COMPLETED_PENDING,
                status_transitions=[
                    StatusTransition(
                        from_status=TaskStatus.OPEN,
                        to_status=TaskStatus.RESOLVED,
                        timestamp=now - timedelta(days=5),
                    ),
                ],
                created_at=now - timedelta(days=7),
                updated_at=now - timedelta(days=5),
                source="test",
            ),
            Task(
                key="WMB-105",
                id="task-005",
                title="Task 2",
                status=TaskStatus.RESOLVED,
                status_category=StatusCategory.COMPLETED_PENDING,
                status_transitions=[
                    StatusTransition(
                        from_status=TaskStatus.OPEN,
                        to_status=TaskStatus.RESOLVED,
                        timestamp=now - timedelta(days=3),
                    ),
                ],
                created_at=now - timedelta(days=5),
                updated_at=now - timedelta(days=3),
                source="test",
            ),
        ]

        metrics = engine.calculate_throughput(tasks, period_days=30)

        assert metrics["completed_count"] == 2
        assert metrics["avg_cycle_time"] > 0


class TestCalculateWIP:
    """Tests for calculate_wip."""

    def test_wip_calculation(self, engine, sample_tasks):
        """Test WIP calculation."""
        metrics = engine.calculate_wip(sample_tasks, period_days=30)

        assert "active_tasks" in metrics
        assert "in_progress" in metrics
        assert "waiting" in metrics
        assert metrics["active_tasks"] >= 0

    def test_wip_empty_tasks(self, engine):
        """Test WIP with empty task list."""
        metrics = engine.calculate_wip([], period_days=30)

        assert metrics["active_tasks"] == 0
        assert metrics["wip_limit_recommendation"] >= 3


class TestCalculateCycleTime:
    """Tests for calculate_cycle_time."""

    def test_cycle_time_calculation(self, engine, sample_tasks):
        """Test cycle time calculation."""
        metrics = engine.calculate_cycle_time(sample_tasks)

        assert "count" in metrics
        assert "avg" in metrics
        assert metrics["count"] >= 0

    def test_cycle_time_no_tasks(self, engine):
        """Test cycle time with no tasks."""
        metrics = engine.calculate_cycle_time([])

        assert metrics["count"] == 0
        assert metrics["avg"] == 0

    def test_cycle_time_only_in_progress(self, engine):
        """Test cycle time when all tasks are in progress."""
        now = datetime.now()
        tasks = [
            Task(
                key="WMB-106",
                id="task-006",
                title="Task 1",
                status=TaskStatus.IN_PROGRESS,
                status_category=StatusCategory.ACTIVE_WORK,
                created_at=now - timedelta(days=5),
                updated_at=now - timedelta(days=5),
                source="test",
            ),
        ]

        metrics = engine.calculate_cycle_time(tasks)

        # In progress tasks should not have cycle time yet
        assert metrics["count"] == 0


class TestCalculateLeadTime:
    """Tests for calculate_lead_time."""

    def test_lead_time_calculation(self, engine, sample_tasks):
        """Test lead time calculation."""
        metrics = engine.calculate_lead_time(sample_tasks)

        assert "count" in metrics
        assert "avg" in metrics
        assert metrics["count"] >= 0

    def test_lead_time_no_tasks(self, engine):
        """Test lead time with no tasks."""
        metrics = engine.calculate_lead_time([])

        assert metrics["count"] == 0
        assert metrics["avg"] == 0


class TestCalculateFlowEfficiency:
    """Tests for calculate_flow_efficiency."""

    def test_flow_efficiency_calculation(self, engine, sample_tasks):
        """Test flow efficiency calculation."""
        metrics = engine.calculate_flow_efficiency(sample_tasks)

        assert "count" in metrics
        assert "avg" in metrics

    def test_flow_efficiency_empty_tasks(self, engine):
        """Test flow efficiency with no tasks."""
        metrics = engine.calculate_flow_efficiency([])

        assert metrics["count"] == 0
        assert metrics["avg"] == 0


class TestCalculateVelocity:
    """Tests for calculate_velocity."""

    def test_velocity_calculation(self, engine, sample_tasks):
        """Test velocity calculation."""
        metrics = engine.calculate_velocity(sample_tasks, period_days=30)

        assert "completed_tasks" in metrics
        assert "total_points" in metrics
        assert "avg_velocity" in metrics

    def test_velocity_empty_tasks(self, engine):
        """Test velocity with no tasks."""
        metrics = engine.calculate_velocity([], period_days=30)

        assert metrics["completed_tasks"] == 0
        assert metrics["avg_velocity"] == 0


class TestCalculateBlockedTime:
    """Tests for calculate_blocked_time."""

    def test_blocked_time_calculation(self, engine, sample_tasks):
        """Test blocked time calculation."""
        metrics = engine.calculate_blocked_time(sample_tasks)

        assert "total_blocked_days" in metrics
        assert "blocked_tasks" in metrics

    def test_blocked_time_no_blocked(self, engine):
        """Test blocked time with no blocked tasks."""
        now = datetime.now()
        tasks = [
            Task(
                key="WMB-107",
                id="task-007",
                title="Active Task",
                status=TaskStatus.IN_PROGRESS,
                status_category=StatusCategory.ACTIVE_WORK,
                created_at=now - timedelta(days=5),
                updated_at=now - timedelta(days=5),
                source="test",
            ),
        ]

        metrics = engine.calculate_blocked_time(tasks)

        assert metrics["total_blocked_days"] == 0


class TestCalculateCompletionRatio:
    """Tests for calculate_completion_ratio."""

    def test_completion_ratio_calculation(self, engine, sample_tasks):
        """Test completion ratio calculation."""
        metrics = engine.calculate_completion_ratio(sample_tasks, period_days=30)

        assert "completed" in metrics
        assert "total" in metrics
        assert "ratio" in metrics
        assert 0 <= metrics["ratio"] <= 1

    def test_completion_ratio_empty_tasks(self, engine):
        """Test completion ratio with no tasks."""
        metrics = engine.calculate_completion_ratio([], period_days=30)

        assert metrics["completed"] == 0
        assert metrics["total"] == 0
        assert metrics["ratio"] == 0


class TestGetAllMetrics:
    """Tests for get_all_metrics."""

    def test_all_metrics(self, engine, sample_tasks):
        """Test getting all metrics at once."""
        metrics = engine.get_all_metrics(sample_tasks, period_days=30)

        assert "throughput" in metrics
        assert "wip" in metrics
        assert "cycle_time" in metrics
        assert "lead_time" in metrics
        assert "flow_efficiency" in metrics
        assert "velocity" in metrics
        assert "blocked_time" in metrics
        assert "completion_ratio" in metrics


class TestMetricsEngineLifecycle:
    """Tests for MetricsEngine lifecycle."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = MetricsEngine()
        assert engine is not None
