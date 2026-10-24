"""Tests for WorkflowEngine."""

from datetime import datetime, timedelta

import pytest

from po_agent.domain.models import (
    StatusCategory,
    StatusTransition,
    Task,
    TaskPriority,
    TaskStatus,
)
from po_agent.workflow.engine import WorkflowEngine


@pytest.fixture
def engine():
    """Create WorkflowEngine instance."""
    return WorkflowEngine()


@pytest.fixture
def sample_task():
    """Create sample task with transitions."""
    now = datetime.now()

    return Task(
        key="WMB-101",
        id="task-001",
        title="Sample Task",
        description="Sample task for testing",
        status=TaskStatus.RESOLVED,
        status_category=StatusCategory.COMPLETED_PENDING,
        status_transitions=[
            StatusTransition(
                from_status=TaskStatus.OPEN,
                to_status=TaskStatus.IN_PROGRESS,
                timestamp=now - timedelta(days=10),
                author="Ivanov.I.I",
            ),
            StatusTransition(
                from_status=TaskStatus.IN_PROGRESS,
                to_status=TaskStatus.RESOLVED,
                timestamp=now - timedelta(days=3),
                author="Petrov.P.P",
            ),
        ],
        created_at=now - timedelta(days=12),
        updated_at=now - timedelta(days=3),
        assignee="Ivanov.I.I",
        priority=TaskPriority.HIGH,
        source="test",
    )


@pytest.fixture
def task_with_waiting():
    """Create task with waiting states."""
    now = datetime.now()

    return Task(
        key="WMB-102",
        id="task-002",
        title="Task with Waiting",
        description="Task that spent time waiting",
        status=TaskStatus.NEED_INFO,
        status_category=StatusCategory.WAITING,
        status_transitions=[
            StatusTransition(
                from_status=TaskStatus.OPEN,
                to_status=TaskStatus.IN_PROGRESS,
                timestamp=now - timedelta(days=12),
            ),
            StatusTransition(
                from_status=TaskStatus.IN_PROGRESS,
                to_status=TaskStatus.NEED_INFO,
                timestamp=now - timedelta(days=10),
            ),
        ],
        created_at=now - timedelta(days=15),
        updated_at=now - timedelta(days=10),
        source="test",
    )


@pytest.fixture
def task_without_transitions():
    """Create task without transitions."""
    now = datetime.now()

    return Task(
        key="WMB-103",
        id="task-003",
        title="Task Without Transitions",
        description="Task never left initial status",
        status=TaskStatus.OPEN,
        status_category=StatusCategory.BACKLOG,
        created_at=now - timedelta(days=5),
        updated_at=now - timedelta(days=5),
        source="test",
    )


class TestCalculateStatusTimeline:
    """Tests for calculate_status_timeline."""

    def test_timeline_with_transitions(self, engine, sample_task):
        """Test timeline calculation for task with transitions."""
        timeline = engine.calculate_status_timeline(sample_task)

        assert len(timeline) == 2
        assert timeline[0]["status"] == "In progress"
        assert timeline[1]["status"] == "Resolved"
        assert timeline[0]["days_in_status"] is not None
        assert timeline[1]["days_in_status"] is not None

    def test_timeline_without_transitions(self, engine, task_without_transitions):
        """Test timeline for task without transitions."""
        timeline = engine.calculate_status_timeline(task_without_transitions)

        assert len(timeline) == 1
        assert timeline[0]["status"] == "Open"
        assert timeline[0]["days_in_status"] is not None

    def test_timeline_sorted_by_timestamp(self, engine, sample_task):
        """Test timeline is sorted by timestamp."""
        timeline = engine.calculate_status_timeline(sample_task)

        timestamps = [t["timestamp"] for t in timeline]
        assert timestamps == sorted(timestamps)


class TestCalculateTimeInStatus:
    """Tests for calculate_time_in_status."""

    def test_time_in_status_with_transitions(self, engine, sample_task):
        """Test time calculation for task with transitions."""
        times = engine.calculate_time_in_status(sample_task)

        assert "in progress" in times
        assert "resolved" in times
        assert times["in progress"] >= 0
        assert times["resolved"] >= 0

    def test_time_in_specific_status(self, engine, sample_task):
        """Test time in specific status."""
        times = engine.calculate_time_in_status(sample_task, status="in progress")

        assert "in progress" in times
        assert len(times) == 1

    def test_time_in_status_without_transitions(self, engine, task_without_transitions):
        """Test time in status for task without transitions."""
        times = engine.calculate_time_in_status(task_without_transitions)

        assert "open" in times
        assert times["open"] >= 0


class TestCalculateBlockedTime:
    """Tests for calculate_blocked_time."""

    def test_blocked_time_with_waiting(self, engine, task_with_waiting):
        """Test blocked time calculation for waiting task."""
        blocked = engine.calculate_blocked_time(task_with_waiting)

        # Need info status should be considered blocked
        assert blocked >= 0

    def test_blocked_time_active_task(self, engine, sample_task):
        """Test blocked time for active task."""
        blocked = engine.calculate_blocked_time(sample_task)

        # Resolved task should have minimal blocked time
        assert blocked >= 0

    def test_blocked_time_no_transitions(self, engine, task_without_transitions):
        """Test blocked time for task without transitions."""
        blocked = engine.calculate_blocked_time(task_without_transitions)

        # Open task should have minimal blocked time
        assert blocked >= 0


class TestCalculateCycleTime:
    """Tests for calculate_cycle_time."""

    def test_cycle_time_with_transitions(self, engine, sample_task):
        """Test cycle time calculation."""
        cycle_time = engine.calculate_cycle_time(sample_task)

        assert cycle_time is not None
        assert cycle_time >= 0
        # Should be approximately 7 days (10 to 3 days ago)
        assert cycle_time <= 10

    def test_cycle_time_no_transitions_in_progress(self, engine):
        """Test cycle time for task in progress without transitions."""
        now = datetime.now()
        task = Task(
            key="WMB-104",
            id="task-004",
            title="In Progress Task",
            description="Task in progress",
            status=TaskStatus.IN_PROGRESS,
            status_category=StatusCategory.ACTIVE_WORK,
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(days=5),
            source="test",
        )

        cycle_time = engine.calculate_cycle_time(task)
        assert cycle_time is not None
        assert cycle_time >= 0

    def test_cycle_time_no_work_yet(self, engine, task_without_transitions):
        """Test cycle time for task never started."""
        cycle_time = engine.calculate_cycle_time(task_without_transitions)

        # Open task that never started should return None
        assert cycle_time is None


class TestCalculateLeadTime:
    """Tests for calculate_lead_time."""

    def test_lead_time_completed_task(self, engine, sample_task):
        """Test lead time for completed task."""
        lead_time = engine.calculate_lead_time(sample_task)

        assert lead_time is not None
        assert lead_time >= 0
        # Should be approximately 12 days
        assert lead_time <= 15

    def test_lead_time_incomplete_task(self, engine, task_without_transitions):
        """Test lead time for incomplete task."""
        lead_time = engine.calculate_lead_time(task_without_transitions)

        # Open task should return None
        assert lead_time is None


class TestCalculateThroughput:
    """Tests for calculate_throughput."""

    def test_throughput_calculation(self, engine, sample_task):
        """Test throughput calculation."""
        now = datetime.now()
        tasks = [
            sample_task,
            Task(
                key="WMB-105",
                id="task-005",
                title="Completed Task",
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
        ]

        metrics = engine.calculate_throughput(tasks, period_days=30)

        assert metrics["completed_count"] >= 0
        assert metrics["throughput"] >= 0
        assert "completed_tasks" in metrics

    def test_throughput_empty_tasks(self, engine):
        """Test throughput with empty task list."""
        metrics = engine.calculate_throughput([], period_days=30)

        assert metrics["completed_count"] == 0
        assert metrics["throughput"] == 0


class TestCalculateWIP:
    """Tests for calculate_wip."""

    def test_wip_calculation(self, engine, sample_task):
        """Test WIP calculation."""
        now = datetime.now()
        tasks = [
            sample_task,  # Completed
            Task(
                key="WMB-106",
                id="task-006",
                title="In Progress Task",
                status=TaskStatus.IN_PROGRESS,
                status_category=StatusCategory.ACTIVE_WORK,
                created_at=now - timedelta(days=2),
                updated_at=now - timedelta(days=2),
                source="test",
            ),
        ]

        metrics = engine.calculate_wip(tasks, period_days=30)

        assert metrics["active_tasks"] >= 0
        assert metrics["in_progress"] >= 0
        assert metrics["wip_limit_recommendation"] > 0

    def test_wip_empty_tasks(self, engine):
        """Test WIP with empty task list."""
        metrics = engine.calculate_wip([], period_days=30)

        assert metrics["active_tasks"] == 0
        assert metrics["wip_limit_recommendation"] >= 3


class TestGetWorkflowHealth:
    """Tests for get_workflow_health."""

    def test_healthy_task(self, engine, sample_task):
        """Test health check for healthy task."""
        health = engine.get_workflow_health(sample_task)

        assert "status" in health
        assert "score" in health
        assert "issues" in health
        assert "recommendations" in health
        assert health["score"] >= 0

    def test_task_with_issues(self, engine, task_with_waiting):
        """Test health check for task with issues."""
        health = engine.get_workflow_health(task_with_waiting)

        assert health["score"] < 100  # Should have some issues

    def test_empty_task_health(self, engine):
        """Test health check for new task."""
        now = datetime.now()
        task = Task(
            key="WMB-107",
            id="task-007",
            title="New Task",
            status=TaskStatus.OPEN,
            status_category=StatusCategory.BACKLOG,
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(days=1),
            source="test",
        )

        health = engine.get_workflow_health(task)

        assert health["score"] == 100  # No issues yet
        assert len(health["issues"]) == 0


class TestWorkflowEngineLifecycle:
    """Tests for WorkflowEngine lifecycle."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = WorkflowEngine()
        assert engine is not None
