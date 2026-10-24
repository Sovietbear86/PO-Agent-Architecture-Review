"""Tests for ResolvedContext model."""

import pytest
from datetime import datetime, date

from po_agent.models.resolved_context import (
    ResolvedContext,
    ContextSource,
    ContextConflict,
)
from po_agent.domain.models import AttachmentType


class TestResolvedContextBasic:
    """Basic ResolvedContext functionality."""

    def test_context_creation(self):
        """Test creating a new context."""
        context = ResolvedContext()
        assert context.product is None
        assert context.sprint_id is None
        assert context.member_login is None
        assert context.missing_fields == []
        assert context.ambiguous_fields == []
        assert context.confidence == 0.0
        assert context.needs_clarification is False

    def test_context_with_values(self):
        """Test creating context with values."""
        context = ResolvedContext(
            product="OLP",
            sprint_id="OLP-SPRNT-1",
            member_login="Ivanov.A.B",
            confidence=0.9,
        )
        assert context.product == "OLP"
        assert context.sprint_id == "OLP-SPRNT-1"
        assert context.member_login == "Ivanov.A.B"
        assert context.confidence == 0.9

    def test_source_tracking(self):
        """Test source tracking for fields."""
        context = ResolvedContext()

        # Set product with source
        assert context.set_value("product", "OLP", ContextSource.CURRENT_REQUEST)
        value, source = context.get_value("product")
        assert value == "OLP"
        assert source == ContextSource.CURRENT_REQUEST

    def test_source_override_precedence(self):
        """Test that lower-priority sources don't override higher."""
        context = ResolvedContext()
        context.set_value("product", "OLP", ContextSource.CURRENT_REQUEST)

        # Session memory tries to set (should be skipped)
        assert not context.set_value("product", "DMS", ContextSource.SESSION_MEMORY)

        # But explicit override should work
        assert context.set_value("product", "DMS", ContextSource.CURRENT_REQUEST, override=True)
        assert context.product == "DMS"

    def test_mark_missing_fields(self):
        """Test marking fields as missing."""
        context = ResolvedContext()
        context.mark_missing("sprint_id")
        context.mark_missing("member_login")

        assert "sprint_id" in context.missing_fields
        assert "member_login" in context.missing_fields

    def test_mark_ambiguous_fields(self):
        """Test marking fields as ambiguous."""
        context = ResolvedContext()
        context.mark_ambiguous("product")

        assert "product" in context.ambiguous_fields

    def test_has_all_required(self):
        """Test checking required fields."""
        context = ResolvedContext(
            product="OLP",
            sprint_id="OLP-SPRNT-1",
        )

        required = ["product", "sprint_id"]
        assert context.has_all_required(required) is True

        # Add missing field
        context.mark_missing("member_login")
        required.append("member_login")
        assert context.has_all_required(required) is False

    def test_to_dict(self):
        """Test converting context to dict."""
        context = ResolvedContext(
            product="OLP",
            sprint_id="OLP-SPRNT-1",
            member_login="Ivanov.A.B",
            confidence=0.9,
        )
        context.set_value("product", "OLP", ContextSource.CURRENT_REQUEST)

        result = context.to_dict()

        assert result["product"] == "OLP"
        assert result["product_source"] == "current_request"
        assert result["sprint_id"] == "OLP-SPRNT-1"
        assert result["confidence"] == 0.9


class TestResolvedContextConflicts:
    """Conflict tracking in ResolvedContext."""

    def test_add_conflict(self):
        """Test adding a conflict."""
        context = ResolvedContext()
        conflict = ContextConflict(
            field="product",
            source1="current_request",
            value1="OLP",
            source2="session_memory",
            value2="DMS",
            resolved_by="current_request",
        )
        context.add_conflict(conflict)

        assert len(context.conflicts) == 1
        assert context.conflicts[0].field == "product"

    def test_multiple_conflicts(self):
        """Test multiple conflicts."""
        context = ResolvedContext()
        context.add_conflict(ContextConflict(
            field="product",
            source1="current_request",
            value1="OLP",
            source2="session_memory",
            value2="DMS",
            resolved_by="current_request",
        ))
        context.add_conflict(ContextConflict(
            field="member_login",
            source1="clarification_answer",
            value1="Petrov.V.V",
            source2="session_memory",
            value2="Ivanov.A.B",
            resolved_by="clarification_answer",
        ))

        assert len(context.conflicts) == 2


class TestResolvedContextPriorities:
    """Priority handling in ResolvedContext."""

    def test_current_request_wins_over_session(self):
        """Test that current_request takes priority over session_memory."""
        context = ResolvedContext()
        context.set_value("product", "DMS", ContextSource.SESSION_MEMORY)
        context.set_value("product", "OLP", ContextSource.CURRENT_REQUEST)

        assert context.product == "OLP"

    def test_clarification_wins_over_deterministic(self):
        """Test that clarification_answer takes priority over deterministic."""
        context = ResolvedContext()
        context.set_value("sprint_id", "DMS-SPRNT-1", ContextSource.DETERMINISTIC_LOOKUP)
        context.set_value("sprint_id", "OLP-SPRNT-1", ContextSource.CLARIFICATION_ANSWER)

        assert context.sprint_id == "OLP-SPRNT-1"

    def test_default_fallback(self):
        """Test that default is used when nothing else is available."""
        context = ResolvedContext()

        # No values set, all should be None
        assert context.product is None
        assert context.sprint_id is None
