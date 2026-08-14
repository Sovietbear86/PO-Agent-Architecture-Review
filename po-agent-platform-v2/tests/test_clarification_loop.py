"""Tests for Clarification Loop."""

import pytest
from datetime import datetime, timedelta

from po_agent.clarification.loop import ClarificationLoop
from po_agent.clarification.models import (
    ClarificationRequest,
    ClarificationResponse,
    ClarificationStatus,
)
from po_agent.memory.session_memory import SessionMemory


class TestClarificationLoopBasic:
    """Basic ClarificationLoop functionality."""

    def test_init_with_defaults(self):
        """Test initialization with defaults."""
        loop = ClarificationLoop()
        assert loop.session_memory is not None
        assert loop.ttl_seconds == 3600

    def test_start_clarification(self):
        """Test starting clarification."""
        loop = ClarificationLoop()
        session = SessionMemory()
        loop.session_memory = session

        request = ClarificationRequest(
            clarification_id="clar-123",
            reason="Missing product",
            missing_fields=["product"],
            question="Какой продукт?",
            original_query="покажи задачи OLP",
        )

        response = loop.start_clarification(request)

        assert response.status == ClarificationStatus.PENDING
        assert response.clarification_id == "clar-123"
        assert response.pending_request is not None
        assert response.pending_request["original_query"] == "покажи задачи OLP"

        # Check session memory was set
        pending = session.get("pending_request")
        assert pending is not None
        assert pending["clarification_id"] == "clar-123"

    def test_has_pending(self):
        """Test checking for pending request."""
        loop = ClarificationLoop()
        session = SessionMemory()
        loop.session_memory = session

        # No pending initially
        assert loop.has_pending() is False

        # Set pending
        request = ClarificationRequest(
            clarification_id="clar-123",
            reason="Missing product",
            missing_fields=["product"],
            question="Какой продукт?",
            original_query="покажи задачи",
        )
        loop.start_clarification(request)

        assert loop.has_pending() is True

    def test_clear_pending(self):
        """Test clearing pending request."""
        loop = ClarificationLoop()
        session = SessionMemory()
        loop.session_memory = session

        request = ClarificationRequest(
            clarification_id="clar-123",
            reason="Missing product",
            missing_fields=["product"],
            question="Какой продукт?",
            original_query="покажи задачи",
        )
        loop.start_clarification(request)

        # Clear pending
        result = loop.clear_pending()

        assert result is True
        assert loop.has_pending() is False

    def test_get_pending(self):
        """Test getting pending request."""
        loop = ClarificationLoop()
        session = SessionMemory()
        loop.session_memory = session

        request = ClarificationRequest(
            clarification_id="clar-123",
            reason="Missing product",
            missing_fields=["product"],
            question="Какой продукт?",
            original_query="покажи задачи",
        )
        loop.start_clarification(request)

        pending = loop.get_pending()
        assert pending is not None
        assert pending["clarification_id"] == "clar-123"


class TestClarificationLoopResume:
    """Resume request tests."""

    def test_resume_request(self):
        """Test resuming request with answer."""
        loop = ClarificationLoop()
        session = SessionMemory()
        loop.session_memory = session

        request = ClarificationRequest(
            clarification_id="clar-123",
            reason="Missing product",
            missing_fields=["product"],
            question="Какой продукт?",
            original_query="покажи задачи OLP",
        )
        loop.start_clarification(request)

        # Resume with answer
        result = loop.resume_request("DataMarts")

        assert result is not None
        assert result["original_query"] == "покажи задачи OLP"
        assert result["answer"] == "DataMarts"
        assert result["clarification_id"] == "clar-123"

    def test_resume_request_with_option(self):
        """Test resuming request with selected option."""
        loop = ClarificationLoop()
        session = SessionMemory()
        loop.session_memory = session

        request = ClarificationRequest(
            clarification_id="clar-123",
            reason="Missing product",
            missing_fields=["product"],
            question="Какой продукт?",
            options=[{"label": "OLP", "value": "OLP"}],
            original_query="покажи задачи",
        )
        loop.start_clarification(request)

        # Resume with option
        result = loop.resume_request("", selected_option="OLP")

        assert result is not None
        assert result["selected_option"] == "OLP"


class TestClarificationLoopExpiration:
    """Expiration tests."""

    def test_expired_pending(self):
        """Test expired pending request."""
        loop = ClarificationLoop(ttl_seconds=1)
        session = SessionMemory()
        loop.session_memory = session

        # Create request that expires immediately
        request = ClarificationRequest(
            clarification_id="clar-123",
            reason="Missing product",
            missing_fields=["product"],
            question="Какой продукт?",
            original_query="покажи задачи",
            created_at=datetime.now() - timedelta(hours=2),
            expires_at=datetime.now() - timedelta(hours=1),
        )
        loop.start_clarification(request)

        # Should be expired
        assert loop.has_pending() is False
        assert loop.get_pending() is None


class TestClarificationLoopCleanup:
    """Cleanup tests."""

    def test_cleanup_expired(self):
        """Test cleaning up expired requests."""
        loop = ClarificationLoop()
        session = SessionMemory()
        loop.session_memory = session

        # Manually set an expired request in session
        expired_pending = {
            "original_query": "покажи задачи",
            "original_intent": None,
            "missing_fields": ["product"],
            "clarification_id": "clar-123",
            "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            "expires_at": (datetime.now() - timedelta(hours=1)).isoformat(),
        }
        session.set("pending_request", expired_pending)

        # Cleanup
        count = loop.cleanup_expired()

        assert count == 1
        assert loop.has_pending() is False
