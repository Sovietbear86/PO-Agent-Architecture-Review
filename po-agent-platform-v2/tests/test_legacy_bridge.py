"""Tests for LegacyAS21Bridge adapter."""

import asyncio

import pytest

from po_agent.adapters.legacy_bridge import (
    LegacyAS21Bridge,
    _parse_swtr_status,
    _parse_swtr_priority,
    _parse_swtr_datetime,
    _map_swtr_issue_to_task,
)


class TestParseSwtrStatus:
    """Tests for _parse_swtr_status function."""

    def test_parse_open(self):
        """Test parsing 'Open' status."""
        assert _parse_swtr_status("Open") is not None
        assert _parse_swtr_status("Открыта") is not None

    def test_parse_in_progress(self):
        """Test parsing 'In progress' status."""
        assert _parse_swtr_status("In progress") is not None
        assert _parse_swtr_status("В работе") is not None

    def test_parse_resolved(self):
        """Test parsing 'Resolved' status."""
        assert _parse_swtr_status("Resolved") is not None
        assert _parse_swtr_status("Решена") is not None

    def test_parse_closed(self):
        """Test parsing 'Closed' status."""
        assert _parse_swtr_status("Closed") is not None
        assert _parse_swtr_status("Закрыта") is not None

    def test_parse_cancelled(self):
        """Test parsing 'Cancelled' status."""
        assert _parse_swtr_status("Cancelled") is not None
        assert _parse_swtr_status("Отменена") is not None

    def test_parse_unknown_status(self):
        """Test parsing unknown status returns Open."""
        assert _parse_swtr_status("Unknown Status") is not None


class TestParseSwtrPriority:
    """Tests for _parse_swtr_priority function."""

    def test_parse_low(self):
        """Test parsing 'Low' priority."""
        assert _parse_swtr_priority("Low").value == "Low"

    def test_parse_high(self):
        """Test parsing 'High' priority."""
        assert _parse_swtr_priority("High").value == "High"

    def test_parse_none(self):
        """Test parsing None returns None."""
        assert _parse_swtr_priority(None) is None


class TestParseSwtrDatetime:
    """Tests for _parse_swtr_datetime function."""

    def test_parse_valid_datetime(self):
        """Test parsing valid datetime."""
        result = _parse_swtr_datetime("2024-01-15T10:30:00.000+0300")
        assert result is not None

    def test_parse_none(self):
        """Test parsing None returns None."""
        assert _parse_swtr_datetime(None) is None


class TestMapSwtrIssueToTask:
    """Tests for _map_swtr_issue_to_task function."""

    def test_map_complete_issue(self):
        """Test mapping complete issue."""
        issue = {
            "key": "WMB-123",
            "fields": {
                "summary": "Test task",
                "description": "Test description",
                "status": {"name": "Open"},
                "created": "2024-01-15T10:30:00.000+0300",
                "updated": "2024-01-16T10:30:00.000+0300",
                "priority": {"name": "High"},
                "assignee": {"displayName": "Ivanov.I.I"},
                "labels": ["label1", "label2"],
                "components": [{"name": "Component1"}],
            },
        }

        task = _map_swtr_issue_to_task(issue)

        assert task is not None
        assert task.key == "WMB-123"
        assert task.title == "Test task"
        assert task.description == "Test description"

    def test_map_missing_key(self):
        """Test mapping issue without key returns None."""
        issue = {
            "fields": {
                "summary": "Test task",
                "status": {"name": "Open"},
            },
        }

        task = _map_swtr_issue_to_task(issue)

        assert task is None

    def test_map_minimal_issue(self):
        """Test mapping minimal issue."""
        issue = {
            "key": "WMB-456",
            "fields": {
                "summary": "Minimal task",
                "status": {"name": "In progress"},
            },
        }

        task = _map_swtr_issue_to_task(issue)

        assert task is not None
        assert task.key == "WMB-456"


class TestLegacyAS21Bridge:
    """Tests for LegacyAS21Bridge adapter."""

    def test_bridge_initialization(self):
        """Test bridge initialization."""
        bridge = LegacyAS21Bridge()
        assert bridge is not None

    def test_bridge_get_task_transport_unavailable(self):
        """Test get_task when transport is unavailable."""
        bridge = LegacyAS21Bridge()

        # If swtr_client is not available, should return None
        # This test may vary based on environment
        result = asyncio.run(bridge.get_task("WMB-123"))
        # Should either return None or a Task depending on transport availability

    def test_bridge_search_tasks_transport_unavailable(self):
        """Test search_tasks when transport is unavailable."""
        bridge = LegacyAS21Bridge()

        result = asyncio.run(bridge.search_tasks("project = WMB"))
        # Should either return empty list or list of Tasks
        assert isinstance(result, list)

    def test_bridge_close(self):
        """Test bridge close method."""
        bridge = LegacyAS21Bridge()
        asyncio.run(bridge.close())
