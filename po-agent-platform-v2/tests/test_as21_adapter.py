"""Contract tests for AS21 adapter."""

import asyncio

import pytest

from po_agent.adapters.as21 import AS21Adapter
from po_agent.adapters.fake import FakeAS21Adapter


@pytest.fixture
def adapter() -> AS21Adapter:
    """Create fake adapter for testing."""
    return FakeAS21Adapter()


class TestGetTask:
    """Tests for get_task operation."""

    def test_get_existing_task(self, adapter):
        """Test getting an existing task."""
        task = asyncio.run(adapter.get_task("WMB-101"))

        assert task is not None
        assert task.key == "WMB-101"
        assert task.title == "Implement user authentication"
        assert task.status.value == "Resolved"

    def test_get_nonexistent_task(self, adapter):
        """Test getting a nonexistent task returns None."""
        task = asyncio.run(adapter.get_task("WMB-999"))

        assert task is None

    def test_get_task_by_different_key(self, adapter):
        """Test getting task with different key patterns."""
        task = asyncio.run(adapter.get_task("DMS-201"))

        assert task is not None
        assert task.key == "DMS-201"
        assert task.status.value == "Closed"


class TestSearchTasks:
    """Tests for search_tasks operation."""

    def test_search_all_tasks(self, adapter):
        """Test searching with no JQL returns all tasks."""
        tasks = asyncio.run(adapter.search_tasks("project = WMB ORDER BY created DESC"))

        assert len(tasks) > 0

    def test_search_by_project(self, adapter):
        """Test searching by project."""
        tasks = asyncio.run(adapter.search_tasks("project = WMB"))

        assert len(tasks) == 3
        for task in tasks:
            assert task.key.startswith("WMB-")

    def test_search_by_assignee(self, adapter):
        """Test searching by assignee."""
        tasks = asyncio.run(adapter.search_tasks("assignee = Ivanov"))

        assert len(tasks) >= 1
        for task in tasks:
            assert task.assignee is not None
            assert "Ivanov" in task.assignee

    def test_search_by_sprint(self, adapter):
        """Test searching by sprint."""
        tasks = asyncio.run(adapter.search_tasks("sprint = WMB-SPRNT-1"))

        assert len(tasks) == 2
        for task in tasks:
            assert task.key in ("WMB-101", "WMB-102")

    def test_search_by_key(self, adapter):
        """Test searching by specific key."""
        tasks = asyncio.run(adapter.search_tasks("key = WMB-101"))

        assert len(tasks) == 1
        assert tasks[0].key == "WMB-101"

    def test_search_with_max_results(self, adapter):
        """Test max_results parameter."""
        tasks = asyncio.run(adapter.search_tasks("project = WMB", max_results=2))

        assert len(tasks) <= 2


class TestGetTaskHistory:
    """Tests for get_task_history operation."""

    def test_get_task_history(self, adapter):
        """Test getting task history."""
        history = asyncio.run(adapter.get_task_history("WMB-101"))

        assert len(history) == 2
        assert history[0].from_status.value == "Open"
        assert history[0].to_status.value == "In progress"
        assert history[1].from_status.value == "In progress"
        assert history[1].to_status.value == "Resolved"

    def test_get_history_for_task_with_no_transitions(self, adapter):
        """Test getting history for task with no transitions."""
        history = asyncio.run(adapter.get_task_history("WMB-103"))

        assert len(history) == 0

    def test_get_history_for_nonexistent_task(self, adapter):
        """Test getting history for nonexistent task."""
        history = asyncio.run(adapter.get_task_history("WMB-999"))

        assert len(history) == 0


class TestGetSprintTasks:
    """Tests for get_sprint_tasks operation."""

    def test_get_sprint_tasks(self, adapter):
        """Test getting tasks for a sprint."""
        tasks = asyncio.run(adapter.get_sprint_tasks("WMB-SPRNT-1"))

        assert len(tasks) == 2
        task_keys = {t.key for t in tasks}
        assert task_keys == {"WMB-101", "WMB-102"}

    def test_get_sprint_tasks_empty(self, adapter):
        """Test getting tasks for nonexistent sprint."""
        tasks = asyncio.run(adapter.get_sprint_tasks("NONEXISTENT-SPRNT-1"))

        assert len(tasks) == 0


class TestGetReleaseTasks:
    """Tests for get_release_tasks operation."""

    def test_get_release_tasks(self, adapter):
        """Test getting tasks for a release."""
        tasks = asyncio.run(adapter.get_release_tasks("WMB-2024-Q3"))

        assert len(tasks) == 3
        task_keys = {t.key for t in tasks}
        assert task_keys == {"WMB-101", "WMB-102", "WMB-103"}

    def test_get_release_tasks_empty(self, adapter):
        """Test getting tasks for nonexistent release."""
        tasks = asyncio.run(adapter.get_release_tasks("NONEXISTENT-2024-Q4"))

        assert len(tasks) == 0


class TestGetAttachmentMetadata:
    """Tests for get_attachment_metadata operation."""

    def test_get_task_attachments(self, adapter):
        """Test getting attachments for a task."""
        attachments = asyncio.run(adapter.get_attachment_metadata("WMB-101"))

        assert len(attachments) == 1
        assert attachments[0].name == "requirements.xlsx"
        assert attachments[0].type.value == "excel"

    def test_get_task_attachment_by_id(self, adapter):
        """Test getting specific attachment by ID."""
        attachments = asyncio.run(adapter.get_attachment_metadata("WMB-101", "att-001"))

        assert len(attachments) == 1
        assert attachments[0].id == "att-001"

    def test_get_attachments_for_task_with_none(self, adapter):
        """Test getting attachments for task without attachments."""
        attachments = asyncio.run(adapter.get_attachment_metadata("DMS-202"))

        assert len(attachments) == 0

    def test_get_attachments_for_nonexistent_task(self, adapter):
        """Test getting attachments for nonexistent task."""
        attachments = asyncio.run(adapter.get_attachment_metadata("WMB-999"))

        assert len(attachments) == 0


class TestAdapterLifecycle:
    """Tests for adapter lifecycle."""

    def test_close_adapter(self, adapter):
        """Test closing adapter."""
        asyncio.run(adapter.close())
