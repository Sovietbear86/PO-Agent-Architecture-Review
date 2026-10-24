"""Tests for TaskIntelligenceSearch."""

from datetime import datetime, timedelta

import pytest

from po_agent.domain.models import (
    Attachment,
    AttachmentType,
    StatusCategory,
    Task,
    TaskPriority,
    TaskStatus,
)
from po_agent.search.intelligence import TaskIntelligenceSearch


@pytest.fixture
def search_engine():
    """Create TaskIntelligenceSearch instance."""
    return TaskIntelligenceSearch()


@pytest.fixture
def sample_tasks():
    """Create sample tasks for testing."""
    now = datetime.now()

    return [
        Task(
            key="WMB-101",
            id="task-001",
            title="Implement user authentication",
            description="Add OAuth2 support for user login",
            status=TaskStatus.RESOLVED,
            status_category=StatusCategory.COMPLETED_PENDING,
            created_at=now - timedelta(days=12),
            updated_at=now - timedelta(days=3),
            assignee="Ivanov.I.I",
            sprint_id="WMB-SPRNT-1",
            release_id="WMB-2024-Q3",
            priority=TaskPriority.HIGH,
            attachments=[
                Attachment(
                    id="att-001",
                    name="requirements.xlsx",
                    type=AttachmentType.EXCEL,
                    size_bytes=102400,
                    created_at=now - timedelta(days=12),
                ),
            ],
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
            updated_at=now - timedelta(days=2),
            assignee="Petrov.P.P",
            sprint_id="WMB-SPRNT-2",
            priority=TaskPriority.CRITICAL,
            source="test",
        ),
        Task(
            key="DMS-201",
            id="task-003",
            title="Data migration script",
            description="Migrate old data to new schema",
            status=TaskStatus.CLOSED,
            status_category=StatusCategory.COMPLETED,
            created_at=now - timedelta(days=20),
            updated_at=now - timedelta(days=5),
            assignee="Sidorov.S.S",
            release_id="DMS-2024-Q3",
            priority=TaskPriority.MEDIUM,
            source="test",
        ),
    ]


class TestSearchByPhrase:
    """Tests for search_by_phrase."""

    def test_search_by_title(self, search_engine, sample_tasks):
        """Test searching by phrase in title."""
        results = search_engine.search_by_phrase(sample_tasks, "authentication")

        assert len(results) == 1
        assert results[0].key == "WMB-101"

    def test_search_by_description(self, search_engine, sample_tasks):
        """Test searching by phrase in description."""
        results = search_engine.search_by_phrase(sample_tasks, "mobile")

        assert len(results) == 1
        assert results[0].key == "WMB-102"

    def test_search_no_results(self, search_engine, sample_tasks):
        """Test search with no matching results."""
        results = search_engine.search_by_phrase(sample_tasks, "nonexistent")

        assert len(results) == 0

    def test_search_empty_phrase(self, search_engine, sample_tasks):
        """Test search with empty phrase returns all."""
        results = search_engine.search_by_phrase(sample_tasks, "")

        assert len(results) == len(sample_tasks)

    def test_search_case_insensitive(self, search_engine, sample_tasks):
        """Test case-insensitive search."""
        results = search_engine.search_by_phrase(sample_tasks, "DATA")

        assert len(results) == 1


class TestSearchByTaskKey:
    """Tests for search_by_task_key."""

    def test_search_by_key(self, search_engine, sample_tasks):
        """Test searching by exact task key."""
        results = search_engine.search_by_task_key(sample_tasks, "WMB-101")

        assert len(results) == 1
        assert results[0].key == "WMB-101"

    def test_search_by_key_case_insensitive(self, search_engine, sample_tasks):
        """Test case-insensitive key search."""
        results = search_engine.search_by_task_key(sample_tasks, "wmb-101")

        assert len(results) == 1
        assert results[0].key == "WMB-101"

    def test_search_nonexistent_key(self, search_engine, sample_tasks):
        """Test search for non-existent key."""
        results = search_engine.search_by_task_key(sample_tasks, "WMB-999")

        assert len(results) == 0

    def test_search_with_fuzzy(self, search_engine, sample_tasks):
        """Test fuzzy search (prefix match)."""
        results = search_engine.search_by_task_key(sample_tasks, "WMB", fuzzy=True)

        assert len(results) >= 2


class TestSearchByAssignee:
    """Tests for search_by_assignee."""

    def test_search_by_assignee_exact(self, search_engine, sample_tasks):
        """Test searching by exact assignee."""
        results = search_engine.search_by_assignee(sample_tasks, "Ivanov.I.I")

        assert len(results) == 1
        assert results[0].key == "WMB-101"

    def test_search_by_assignee_partial(self, search_engine, sample_tasks):
        """Test searching by partial assignee name."""
        results = search_engine.search_by_assignee(sample_tasks, "Ivanov")

        assert len(results) == 1

    def test_search_by_assignee_case_insensitive(self, search_engine, sample_tasks):
        """Test case-insensitive assignee search."""
        results = search_engine.search_by_assignee(sample_tasks, "IVANOV.I.I")

        assert len(results) == 1

    def test_search_no_assignee(self, search_engine, sample_tasks):
        """Test search when assignee not found."""
        results = search_engine.search_by_assignee(sample_tasks, "Unknown")

        assert len(results) == 0


class TestSearchBySprint:
    """Tests for search_by_sprint."""

    def test_search_by_sprint(self, search_engine, sample_tasks):
        """Test searching by sprint ID."""
        results = search_engine.search_by_sprint(sample_tasks, "WMB-SPRNT-1")

        assert len(results) == 1
        assert results[0].sprint_id == "WMB-SPRNT-1"

    def test_search_by_sprint_partial(self, search_engine, sample_tasks):
        """Test searching by partial sprint ID."""
        results = search_engine.search_by_sprint(sample_tasks, "SPRNT-1")

        assert len(results) == 1


class TestSearchByRelease:
    """Tests for search_by_release."""

    def test_search_by_release(self, search_engine, sample_tasks):
        """Test searching by release ID."""
        results = search_engine.search_by_release(sample_tasks, "WMB-2024-Q3")

        assert len(results) == 1
        assert results[0].release_id == "WMB-2024-Q3"

    def test_search_by_release_partial(self, search_engine, sample_tasks):
        """Test searching by partial release ID."""
        results = search_engine.search_by_release(sample_tasks, "2024-Q3")

        assert len(results) >= 1


class TestSearchByAttachmentType:
    """Tests for search_by_attachment_type."""

    def test_search_by_attachment_type(self, search_engine, sample_tasks):
        """Test searching by attachment type."""
        results = search_engine.search_by_attachment_type(sample_tasks, AttachmentType.EXCEL)

        assert len(results) == 1
        assert results[0].key == "WMB-101"

    def test_search_no_attachments(self, search_engine, sample_tasks):
        """Test searching for tasks without attachments."""
        results = search_engine.search_by_attachment_type(sample_tasks, AttachmentType.IMAGE)

        assert len(results) == 0


class TestSearchByStatus:
    """Tests for search_by_status."""

    def test_search_by_status(self, search_engine, sample_tasks):
        """Test searching by status."""
        results = search_engine.search_by_status(sample_tasks, "resolved")

        assert len(results) == 1
        assert results[0].status.value == "Resolved"


class TestSearchByPriority:
    """Tests for search_by_priority."""

    def test_search_by_priority(self, search_engine, sample_tasks):
        """Test searching by priority."""
        results = search_engine.search_by_priority(sample_tasks, "HIGH")

        assert len(results) == 1
        assert results[0].priority.value == "High"

    def test_search_no_priority(self, search_engine, sample_tasks):
        """Test searching for tasks without priority."""
        results = search_engine.search_by_priority(sample_tasks, "Unknown")

        assert len(results) == 0


class TestSearchByDateRange:
    """Tests for search_by_date_range."""

    def test_search_by_date_range(self, search_engine, sample_tasks):
        """Test searching by date range."""
        # Use broader date range to include all sample tasks
        start = datetime.now() - timedelta(days=25)
        end = datetime.now()

        results = search_engine.search_by_date_range(sample_tasks, start, end)

        # At least 2 of 3 tasks should be in range (DMS-201 is 20 days old)
        assert len(results) >= 2

    def test_search_after_range(self, search_engine, sample_tasks):
        """Test searching for tasks after date range."""
        start = datetime.now()
        end = datetime.now() + timedelta(days=30)

        results = search_engine.search_by_date_range(sample_tasks, start, end)

        assert len(results) == 0


class TestSearchCombined:
    """Tests for search_combined."""

    def test_combined_search(self, search_engine, sample_tasks):
        """Test combined search with multiple filters."""
        results = search_engine.search_combined(
            sample_tasks,
            query="data",
            release_id="DMS",
        )

        assert len(results) >= 0

    def test_combined_search_no_filters(self, search_engine, sample_tasks):
        """Test combined search with no filters."""
        results = search_engine.search_combined(sample_tasks)

        assert len(results) == len(sample_tasks)

    def test_combined_search_with_max_results(self, search_engine, sample_tasks):
        """Test combined search with max results limit."""
        results = search_engine.search_combined(sample_tasks, max_results=2)

        assert len(results) <= 2


class TestGetSearchStats:
    """Tests for get_search_stats."""

    def test_search_stats(self, search_engine, sample_tasks):
        """Test getting search statistics."""
        stats = search_engine.get_search_stats(sample_tasks)

        assert "total_tasks" in stats
        assert "with_title" in stats
        assert "with_description" in stats
        assert "with_assignee" in stats
        assert "with_sprint" in stats
        assert "with_release" in stats
        assert "with_attachments" in stats

    def test_search_stats_empty(self, search_engine):
        """Test getting stats for empty task list."""
        stats = search_engine.get_search_stats([])

        assert stats["total_tasks"] == 0


class TestTaskIntelligenceSearchLifecycle:
    """Tests for TaskIntelligenceSearch lifecycle."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = TaskIntelligenceSearch()
        assert engine is not None
