"""Tests for workflow module."""

import pytest
from pathlib import Path

from po_agent.domain.models import StatusCategory
from po_agent.workflow.config import (
    load_workflow_config,
    get_workflow_status_mapping,
)
from po_agent.workflow.status import (
    normalize_status,
    is_terminal,
    is_active,
    is_waiting,
    is_blocked,
    get_status_category,
)


class TestLoadWorkflowConfig:
    """Tests for load_workflow_config function."""

    def test_load_config_from_default_path(self):
        """Test loading config from default path."""
        config = load_workflow_config()

        assert config is not None
        assert config.statuses is not None
        assert len(config.statuses) > 0

        # Check some expected statuses
        assert "Open" in config.statuses
        assert "In progress" in config.statuses
        assert "Closed" in config.statuses

    def test_load_config_with_custom_path(self):
        """Test loading config from custom path."""
        # Use a test config file path
        script_dir = Path(__file__).parent
        config_path = script_dir.parent / "config" / "workflow.yaml"

        if config_path.exists():
            config = load_workflow_config(str(config_path))
            assert config.statuses is not None
        else:
            # Skip if file doesn't exist
            pytest.skip(f"Config file not found at {config_path}")


class TestGetWorkflowStatusMapping:
    """Tests for get_workflow_status_mapping function."""

    def test_mapping_contains_russian_translations(self):
        """Test that mapping includes Russian status names."""
        mapping = get_workflow_status_mapping()

        assert "открыта" in mapping
        assert "закрыта" in mapping
        assert "в работе" in mapping

    def test_mapping_values_are_as21_codes(self):
        """Test that mapping returns valid AS21 codes."""
        mapping = get_workflow_status_mapping()

        valid_codes = [
            "Open",
            "In progress",
            "Closed",
            "Resolved",
            "Cancelled",
            "Need info",
            "Reopened",
            "Ready for review",
            "In review",
            "Ready for QA",
            "QA",
        ]

        for code in valid_codes:
            assert code in mapping.values()


class TestNormalizeStatus:
    """Tests for normalize_status function."""

    def test_normalize_english_status(self):
        """Test normalizing English status."""
        assert normalize_status("Open") == "Open"
        assert normalize_status("IN PROGRESS") == "In progress"
        assert normalize_status("  Closed  ") == "Closed"

    def test_normalize_russian_status(self):
        """Test normalizing Russian status."""
        assert normalize_status("Открыта") == "Open"
        assert normalize_status("открыта") == "Open"
        assert normalize_status("В работе") == "In progress"
        assert normalize_status("Закрыта") == "Closed"

    def test_normalize_unknown_status(self):
        """Test normalizing unknown status returns Open."""
        assert normalize_status("Unknown Status") == "Open"
        assert normalize_status("") == "Open"


class TestIsTerminal:
    """Tests for is_terminal function."""

    def test_terminal_statuses(self):
        """Test terminal status detection."""
        assert is_terminal("Closed") is True
        assert is_terminal("Resolved") is True
        assert is_terminal("Cancelled") is True

    def test_non_terminal_statuses(self):
        """Test non-terminal status detection."""
        assert is_terminal("Open") is False
        assert is_terminal("In progress") is False
        assert is_terminal("Need info") is False
        assert is_terminal("QA") is False


class TestIsActive:
    """Tests for is_active function."""

    def test_active_statuses(self):
        """Test active status detection."""
        assert is_active("In progress") is True
        assert is_active("Reopened") is True

    def test_non_active_statuses(self):
        """Test non-active status detection."""
        assert is_active("Open") is False
        assert is_active("Closed") is False
        assert is_active("Need info") is False


class TestIsWaiting:
    """Tests for is_waiting function."""

    def test_waiting_statuses(self):
        """Test waiting status detection."""
        assert is_waiting("Need info") is True

    def test_non_waiting_statuses(self):
        """Test non-waiting status detection."""
        assert is_waiting("In progress") is False
        assert is_waiting("Open") is False
        assert is_waiting("Closed") is False


class TestIsBlocked:
    """Tests for is_blocked function."""

    def test_blocked_statuses(self):
        """Test blocked status detection."""
        assert is_blocked("Need info") is True

    def test_non_blocked_statuses(self):
        """Test non-blocked status detection."""
        assert is_blocked("In progress") is False
        assert is_blocked("Open") is False
        assert is_blocked("Closed") is False


class TestGetStatusCategory:
    """Tests for get_status_category function."""

    def test_backlog_category(self):
        """Test backlog category."""
        assert get_status_category("Open") == StatusCategory.BACKLOG

    def test_waiting_category(self):
        """Test waiting category."""
        assert get_status_category("Need info") == StatusCategory.WAITING

    def test_active_work_category(self):
        """Test active work category."""
        assert get_status_category("In progress") == StatusCategory.ACTIVE_WORK
        assert get_status_category("Reopened") == StatusCategory.ACTIVE_WORK

    def test_review_queue_category(self):
        """Test review queue category."""
        assert get_status_category("Ready for review") == StatusCategory.REVIEW_QUEUE

    def test_review_category(self):
        """Test review category."""
        assert get_status_category("In review") == StatusCategory.REVIEW

    def test_qa_queue_category(self):
        """Test QA queue category."""
        assert get_status_category("Ready for QA") == StatusCategory.QA_QUEUE

    def test_testing_category(self):
        """Test testing category."""
        assert get_status_category("QA") == StatusCategory.TESTING

    def test_completed_pending_category(self):
        """Test completed pending category."""
        assert get_status_category("Resolved") == StatusCategory.COMPLETED_PENDING

    def test_completed_category(self):
        """Test completed category."""
        assert get_status_category("Closed") == StatusCategory.COMPLETED

    def test_cancelled_category(self):
        """Test cancelled category."""
        assert get_status_category("Cancelled") == StatusCategory.CANCELLED

    def test_unknown_category(self):
        """Test unknown category."""
        assert get_status_category("Unknown Status") == StatusCategory.UNKNOWN
