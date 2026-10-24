"""Tests for canonical domain models."""

from datetime import datetime, timedelta

import pytest

from po_agent.domain.models import (
    Attachment,
    AttachmentType,
    Competency,
    Dependency,
    DependencyType,
    Release,
    ReleaseState,
    Sprint,
    SprintState,
    StatusCategory,
    StatusTransition,
    Task,
    TaskPriority,
    TaskStatus,
    TeamMember,
    TeamRole,
    normalize_task_status,
    get_status_category,
)


# =============================================================================
# Status and Workflow Tests
# =============================================================================

class TestStatusTransition:
    """Tests for StatusTransition model."""

    def test_status_transition_creation(self):
        """Test creating a status transition."""
        transition = StatusTransition(
            from_status=TaskStatus.OPEN,
            to_status=TaskStatus.IN_PROGRESS,
            timestamp=datetime.now(),
            author="Ivanov.I.I",
            transition_type="manual",
        )

        assert transition.from_status == TaskStatus.OPEN
        assert transition.to_status == TaskStatus.IN_PROGRESS
        assert transition.author == "Ivanov.I.I"
        assert transition.transition_type == "manual"

    def test_status_transition_default_author(self):
        """Test status transition with default author."""
        transition = StatusTransition(
            from_status=TaskStatus.OPEN,
            to_status=TaskStatus.IN_PROGRESS,
            timestamp=datetime.now(),
        )

        assert transition.author is None
        assert transition.transition_type is None


class TestNormalizeTaskStatus:
    """Tests for normalize_task_status function."""

    def test_normalize_open(self):
        """Test normalizing 'Open' status."""
        assert normalize_task_status("Open") == TaskStatus.OPEN
        assert normalize_task_status("open") == TaskStatus.OPEN
        assert normalize_task_status("Открыта") == TaskStatus.OPEN

    def test_normalize_in_progress(self):
        """Test normalizing 'In progress' status."""
        assert normalize_task_status("In progress") == TaskStatus.IN_PROGRESS
        assert normalize_task_status("в работе") == TaskStatus.IN_PROGRESS

    def test_normalize_resolved(self):
        """Test normalizing 'Resolved' status."""
        assert normalize_task_status("Resolved") == TaskStatus.RESOLVED
        assert normalize_task_status("решена") == TaskStatus.RESOLVED

    def test_normalize_closed(self):
        """Test normalizing 'Closed' status."""
        assert normalize_task_status("Closed") == TaskStatus.CLOSED
        assert normalize_task_status("закрыта") == TaskStatus.CLOSED

    def test_normalize_cancelled(self):
        """Test normalizing 'Cancelled' status."""
        assert normalize_task_status("Cancelled") == TaskStatus.CANCELLED
        assert normalize_task_status("отменена") == TaskStatus.CANCELLED

    def test_normalize_unknown_status(self):
        """Test normalizing unknown status."""
        assert normalize_task_status("Unknown Status") == TaskStatus.OPEN


class TestGetStatusCategory:
    """Tests for get_status_category function."""

    def test_category_backlog(self):
        """Test backlog category."""
        assert get_status_category(TaskStatus.OPEN) == StatusCategory.BACKLOG

    def test_category_waiting(self):
        """Test waiting category."""
        assert get_status_category(TaskStatus.NEED_INFO) == StatusCategory.WAITING

    def test_category_active_work(self):
        """Test active work category."""
        assert get_status_category(TaskStatus.IN_PROGRESS) == StatusCategory.ACTIVE_WORK
        assert get_status_category(TaskStatus.REOPENED) == StatusCategory.ACTIVE_WORK

    def test_category_review(self):
        """Test review category."""
        assert get_status_category(TaskStatus.READY_FOR_REVIEW) == StatusCategory.REVIEW_QUEUE
        assert get_status_category(TaskStatus.IN_REVIEW) == StatusCategory.REVIEW

    def test_category_completed(self):
        """Test completed category."""
        assert get_status_category(TaskStatus.CLOSED) == StatusCategory.COMPLETED
        assert get_status_category(TaskStatus.RESOLVED) == StatusCategory.COMPLETED_PENDING
        assert get_status_category(TaskStatus.CANCELLED) == StatusCategory.CANCELLED


# =============================================================================
# Attachment Tests
# =============================================================================

class TestAttachment:
    """Tests for Attachment model."""

    def test_attachment_creation(self):
        """Test creating an attachment."""
        attachment = Attachment(
            id="att-123",
            name="requirements.xlsx",
            type=AttachmentType.EXCEL,
            size_bytes=102400,
            created_at=datetime.now(),
            url="https://example.com/att-123",
            description="Requirements document",
        )

        assert attachment.id == "att-123"
        assert attachment.name == "requirements.xlsx"
        assert attachment.type == AttachmentType.EXCEL
        assert attachment.size_bytes == 102400
        assert attachment.description == "Requirements document"

    def test_attachment_minimal(self):
        """Test attachment with minimal fields."""
        attachment = Attachment(
            id="att-456",
            name="image.png",
            type=AttachmentType.IMAGE,
            size_bytes=2048,
            created_at=datetime.now(),
        )

        assert attachment.url is None
        assert attachment.description is None


# =============================================================================
# Task Tests
# =============================================================================

class TestTask:
    """Tests for Task model."""

    @pytest.fixture
    def base_task_data(self) -> dict:
        """Base task data fixture."""
        now = datetime.now()
        return {
            "key": "WMB-123",
            "id": "task-123",
            "title": "Implement feature X",
            "status": TaskStatus.IN_PROGRESS,
            "status_category": StatusCategory.ACTIVE_WORK,
            "status_transitions": [],
            "created_at": now - timedelta(days=5),
            "updated_at": now,
        }

    def test_task_creation(self, base_task_data):
        """Test creating a task."""
        task = Task(**base_task_data)

        assert task.key == "WMB-123"
        assert task.title == "Implement feature X"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.age_days == 5

    def test_task_with_assignee(self, base_task_data):
        """Test task with assignee."""
        task = Task(
            **base_task_data,
            assignee="Ivanov.I.I",
            assignee_id="Ivanov.I.I",
        )

        assert task.assignee == "Ivanov.I.I"
        assert task.assignee_id == "Ivanov.I.I"

    def test_task_with_dependencies(self, base_task_data):
        """Test task with dependencies."""
        task = Task(
            **base_task_data,
            depends_on=["WMB-122", "WMB-121"],
            parent_key="WMB-100",
        )

        assert len(task.depends_on) == 2
        assert task.parent_key == "WMB-100"

    def test_task_is_completed(self):
        """Test is_completed property."""
        base_task_data = {
            "key": "WMB-123",
            "id": "task-123",
            "title": "Implement feature X",
            "status_category": StatusCategory.ACTIVE_WORK,
            "status_transitions": [],
            "created_at": datetime.now() - timedelta(days=5),
            "updated_at": datetime.now(),
        }
        # Completed
        task_resolved = Task(**base_task_data, status=TaskStatus.RESOLVED)
        assert task_resolved.is_completed is True

        task_closed = Task(**base_task_data, status=TaskStatus.CLOSED)
        assert task_closed.is_completed is True

        # Not completed
        task_open = Task(**base_task_data, status=TaskStatus.OPEN)
        assert task_open.is_completed is False

    def test_task_is_blocked(self):
        """Test is_blocked property."""
        base_task_data = {
            "key": "WMB-123",
            "id": "task-123",
            "title": "Implement feature X",
            "status_category": StatusCategory.ACTIVE_WORK,
            "status_transitions": [],
            "created_at": datetime.now() - timedelta(days=5),
            "updated_at": datetime.now(),
        }
        task = Task(**base_task_data, status=TaskStatus.NEED_INFO)
        assert task.is_blocked is True

        task_not_blocked = Task(**base_task_data, status=TaskStatus.IN_PROGRESS)
        assert task_not_blocked.is_blocked is False

    def test_task_time_in_current_status(self):
        """Test time_in_current_status_hours property."""
        base_task_data = {
            "key": "WMB-123",
            "id": "task-123",
            "title": "Implement feature X",
            "status_category": StatusCategory.ACTIVE_WORK,
            "created_at": datetime.now() - timedelta(days=5),
            "updated_at": datetime.now(),
        }
        now = datetime.now()
        transition = StatusTransition(
            from_status=TaskStatus.OPEN,
            to_status=TaskStatus.IN_PROGRESS,
            timestamp=now - timedelta(hours=2),
        )
        task = Task(**base_task_data, status=TaskStatus.IN_PROGRESS, status_transitions=[transition])
        assert task.time_in_current_status_hours >= 2

    def test_task_cycle_time(self):
        """Test cycle_time_hours property."""
        base_task_data = {
            "key": "WMB-123",
            "id": "task-123",
            "title": "Implement feature X",
            "status_category": StatusCategory.ACTIVE_WORK,
            "created_at": datetime.now() - timedelta(days=5),
            "updated_at": datetime.now(),
        }
        now = datetime.now()
        in_progress = now - timedelta(days=3)
        transition = StatusTransition(
            from_status=TaskStatus.OPEN,
            to_status=TaskStatus.IN_PROGRESS,
            timestamp=in_progress,
        )
        task = Task(**base_task_data, status=TaskStatus.IN_PROGRESS, status_transitions=[transition])
        # Should be approximately 3 days = 72 hours
        assert 70 <= task.cycle_time_hours <= 80

    def test_task_without_in_progress_cycle_time(self):
        """Test cycle time when no In progress status."""
        base_task_data = {
            "key": "WMB-123",
            "id": "task-123",
            "title": "Implement feature X",
            "status": TaskStatus.IN_PROGRESS,
            "status_category": StatusCategory.ACTIVE_WORK,
            "status_transitions": [],
            "created_at": datetime.now() - timedelta(days=5),
            "updated_at": datetime.now(),
        }
        task = Task(**base_task_data)
        # Should use created_at
        assert task.cycle_time_hours > 0


# =============================================================================
# Sprint Tests
# =============================================================================

class TestSprint:
    """Tests for Sprint model."""

    def test_sprint_creation(self):
        """Test creating a sprint."""
        now = datetime.now()
        sprint = Sprint(
            id="DMS-SPRNT-1",
            name="Sprint 1",
            space="DMS",
            start_date=now - timedelta(days=7),
            end_date=now + timedelta(days=7),
            created_at=now - timedelta(days=14),
            state=SprintState.ACTIVE,
            committed_tasks=["DMS-101", "DMS-102"],
            completed_tasks=["DMS-101"],
        )

        assert sprint.id == "DMS-SPRNT-1"
        assert sprint.space == "DMS"
        assert sprint.duration_days == 14
        assert sprint.is_current is True
        assert len(sprint.committed_tasks) == 2
        assert len(sprint.completed_tasks) == 1

    def test_sprint_state_future(self):
        """Test sprint with future state."""
        now = datetime.now()
        sprint = Sprint(
            id="DMS-SPRNT-2",
            name="Sprint 2",
            space="DMS",
            start_date=now + timedelta(days=7),
            end_date=now + timedelta(days=21),
            created_at=now,
            state=SprintState.FUTURE,
        )

        assert sprint.is_upcoming is True
        assert sprint.is_current is False

    def test_sprint_state_closed(self):
        """Test sprint with closed state."""
        now = datetime.now()
        sprint = Sprint(
            id="DMS-SPRNT-0",
            name="Sprint 0",
            space="DMS",
            start_date=now - timedelta(days=21),
            end_date=now - timedelta(days=7),
            created_at=now - timedelta(days=28),
            closed_at=now - timedelta(days=7),
            state=SprintState.CLOSED,
        )

        assert sprint.is_past is True
        assert sprint.is_current is False


# =============================================================================
# Release Tests
# =============================================================================

class TestRelease:
    """Tests for Release model."""

    def test_release_creation(self):
        """Test creating a release."""
        now = datetime.now()
        release = Release(
            id="WMB-2024-Q3",
            name="Q3 2024 Release",
            space="WMB",
            target_date=now + timedelta(days=30),
            created_at=now - timedelta(days=90),
            state=ReleaseState.IN_PROGRESS,
            scheduled_tasks=["WMB-101", "WMB-102", "WMB-103", "WMB-104"],
            completed_tasks=["WMB-101", "WMB-102"],
            blocked_tasks=["WMB-103"],
            linked_sprints=["WMB-SPRNT-1", "WMB-SPRNT-2"],
        )

        assert release.id == "WMB-2024-Q3"
        assert release.space == "WMB"
        assert release.completion_ratio == 0.5
        # Release has 4 scheduled, 2 completed = 50% completion
        # But it's in progress state with only 50% completion
        # On track means >= 80%, so this should be False
        assert release.is_on_track is False

    def test_release_completed(self):
        """Test release completion."""
        now = datetime.now()
        release = Release(
            id="WMB-2024-Q2",
            name="Q2 2024 Release",
            space="WMB",
            created_at=now - timedelta(days=90),
            released_at=now - timedelta(days=7),
            state=ReleaseState.RELEASED,
            scheduled_tasks=["WMB-101", "WMB-102"],
            completed_tasks=["WMB-101", "WMB-102"],
        )

        assert release.completion_ratio == 1.0
        assert release.is_on_track is True

    def test_release_cancelled(self):
        """Test cancelled release."""
        now = datetime.now()
        release = Release(
            id="WMB-2024-Q1",
            name="Q1 2024 Release",
            space="WMB",
            created_at=now - timedelta(days=90),
            state=ReleaseState.CANCELLED,
            scheduled_tasks=["WMB-101"],
            completed_tasks=[],
        )

        assert release.completion_ratio == 0.0
        assert release.is_on_track is False


# =============================================================================
# Team Member Tests
# =============================================================================

class TestCompetency:
    """Tests for Competency model."""

    def test_competency_creation(self):
        """Test creating a competency."""
        competency = Competency(
            name="Python",
            level=8,
            years_experience=5,
            evidence="/path/to/evidence.md",
        )

        assert competency.name == "Python"
        assert competency.level == 8
        assert competency.years_experience == 5
        assert competency.evidence == "/path/to/evidence.md"

    def test_competency_minimal(self):
        """Test competency with minimal fields."""
        competency = Competency(name="Java", level=5)

        assert competency.years_experience is None
        assert competency.evidence is None


class TestTeamMember:
    """Tests for TeamMember model."""

    def test_team_member_creation(self):
        """Test creating a team member."""
        now = datetime.now()
        member = TeamMember(
            id="Ivanov.I.I",
            full_name="Иванов Иван Иванович",
            email="ivanov@company.com",
            grade=12,
            team_role=TeamRole.TECH_LEAD,
            products=["OLAP", "DTMS"],
            competencies={
                "Python": Competency(name="Python", level=8),
                "Java": Competency(name="Java", level=7),
            },
            allocation_percent=100,
            recommended_max_wip=5,
            is_active=True,
            planned_absences=[now + timedelta(days=14)],
        )

        assert member.id == "Ivanov.I.I"
        # Primary product is first in list
        assert member.primary_product == "OLAP"
        assert member.total_competency_level == 15
        assert len(member.planned_absences) == 1

    def test_team_member_no_competencies(self):
        """Test team member without competencies."""
        member = TeamMember(
            id="Petrov.P.P",
            full_name="Петров Петр Петрович",
            team_role=TeamRole.DEVELOPER,
            products=["WMB"],
        )

        assert member.total_competency_level == 0
        assert member.primary_product == "WMB"


# =============================================================================
# Dependency Tests
# =============================================================================

class TestDependency:
    """Tests for Dependency model."""

    def test_dependency_creation(self):
        """Test creating a dependency."""
        dependency = Dependency(
            task_key="WMB-123",
            depends_on="WMB-122",
            type=DependencyType.BLOCKED_BY,
            description="Waiting for API implementation",
        )

        assert dependency.task_key == "WMB-123"
        assert dependency.depends_on == "WMB-122"
        assert dependency.type == DependencyType.BLOCKED_BY
        assert dependency.description == "Waiting for API implementation"

    def test_dependency_blocking(self):
        """Test is_blocking property."""
        blocking = Dependency(
            task_key="WMB-123",
            depends_on="WMB-122",
            type=DependencyType.BLOCKING,
        )
        assert blocking.is_blocking is True

        not_blocking = Dependency(
            task_key="WMB-123",
            depends_on="WMB-122",
            type=DependencyType.RELATED,
        )
        assert not_blocking.is_blocking is False
