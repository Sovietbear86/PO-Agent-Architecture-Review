"""Tests for ContextResolver."""

import pytest

from po_agent.context.resolver import ContextResolver
from po_agent.models.resolved_context import ResolvedContext, ContextSource
from po_agent.memory.session_memory import SessionMemory


class TestContextResolverBasic:
    """Basic ContextResolver functionality."""

    def test_init_without_session(self):
        """Test initialization without session memory."""
        resolver = ContextResolver()
        assert resolver.session_memory is not None

    def test_full_resolution_with_entities(self):
        """Test full resolution flow with query entities."""
        resolver = ContextResolver()
        entities = [
            {"type": "sprint", "value": "DMS-SPRNT-1"},
            {"type": "member", "value": "Ivanov.A.B"},
        ]

        # Create context
        context = ResolvedContext()

        # Extract from query
        resolver._extract_from_query(context, "покажи задачи Иванова в спринте DMS-SPRNT-1", entities)

        assert context.sprint_id == "DMS-SPRNT-1"
        assert context.member_login == "Ivanov.A.B"
        assert context.sprint_id_source == ContextSource.CURRENT_REQUEST

    def test_session_fallback(self):
        """Test session memory fallback when no query entity."""
        session = SessionMemory()
        session.set_sprint("SESSION-SPRNT")

        resolver = ContextResolver(session_memory=session)

        context = ResolvedContext()
        resolver._extract_from_session_memory(context)

        # Session memory value should be set
        assert context.sprint_id == "SESSION-SPRNT"
        assert context.sprint_id_source == ContextSource.SESSION_MEMORY

    def test_current_request_overrides_session(self):
        """Test that current request overrides session memory."""
        session = SessionMemory()
        session.set_sprint("SESSION-SPRNT")

        resolver = ContextResolver(session_memory=session)

        context = ResolvedContext()
        entities = [{"type": "sprint", "value": "QUERY-SPRNT"}]
        resolver._extract_from_query(context, "покажи задачи в QUERY-SPRNT", entities)

        # Query should override session
        assert context.sprint_id == "QUERY-SPRNT"
        assert context.sprint_id_source == ContextSource.CURRENT_REQUEST


class TestContextResolverDeterministic:
    """ContextResolver with deterministic lookup."""

    def test_single_product_lookup(self):
        """Test single product is used when only one available."""
        resolver = ContextResolver(available_products=["OLP"])

        context = ResolvedContext()
        resolver._extract_from_deterministic_lookup(context)

        # Should use the only available product
        assert context.product == "OLP"
        assert context.product_source == ContextSource.DETERMINISTIC_LOOKUP

    def test_single_sprint_lookup(self):
        """Test single sprint is used when only one available."""
        resolver = ContextResolver(available_sprints=["OLP-SPRNT-1"])

        context = ResolvedContext()
        resolver._extract_from_deterministic_lookup(context)

        # Should use the only available sprint
        assert context.sprint_id == "OLP-SPRNT-1"
        assert context.sprint_id_source == ContextSource.DETERMINISTIC_LOOKUP


class TestContextResolverPrecedence:
    """Precedence policy tests."""

    def test_precedence_order(self):
        """Test full precedence order."""
        session = SessionMemory()
        session.set_sprint("SESSION-SPRNT")

        resolver = ContextResolver(
            session_memory=session,
            available_products=["DMS"],
            available_sprints=["SESSION-SPRNT", "QUERY-SPRNT"],
        )

        context = ResolvedContext()
        entities = [{"type": "sprint", "value": "QUERY-SPRNT"}]

        # Extract from query first (highest priority)
        resolver._extract_from_query(context, "покажи задачи в QUERY-SPRNT", entities)
        # Then session memory (should be skipped)
        resolver._extract_from_session_memory(context)
        # Then deterministic lookup (should be skipped)
        resolver._extract_from_deterministic_lookup(context)

        # Query should win
        assert context.sprint_id == "QUERY-SPRNT"
        assert context.sprint_id_source == ContextSource.CURRENT_REQUEST

    def test_session_fallback_when_no_query(self):
        """Test session memory fallback when no query entity."""
        session = SessionMemory()
        session.set_sprint("SESSION-SPRNT")

        resolver = ContextResolver(session_memory=session)

        context = ResolvedContext()
        entities = []
        resolver._extract_from_query(context, "покажи задачи", entities)
        resolver._extract_from_session_memory(context)

        # Session should be used since no query entity
        assert context.sprint_id == "SESSION-SPRNT"

    def test_deterministic_fallback(self):
        """Test deterministic lookup as final fallback."""
        resolver = ContextResolver(available_sprints=["DMS-SPRNT-1"])

        context = ResolvedContext()
        entities = []
        resolver._extract_from_query(context, "покажи задачи", entities)
        resolver._extract_from_session_memory(context)
        resolver._extract_from_deterministic_lookup(context)

        # Deterministic should be used
        assert context.sprint_id == "DMS-SPRNT-1"
        assert context.sprint_id_source == ContextSource.DETERMINISTIC_LOOKUP


class TestContextResolverValidation:
    """Validation tests for ContextResolver."""

    def test_missing_required_fields(self):
        """Test that missing fields are detected."""
        resolver = ContextResolver()

        context = ResolvedContext()
        entities = []
        resolver._extract_from_query(context, "покажи задачи", entities)
        resolver._extract_from_session_memory(context)
        resolver._extract_from_deterministic_lookup(context)

        # Validate for task_search intent (requires sprint_id, member_login)
        resolver._validate_context(context, ["task_search"])

        assert context.needs_clarification is True
        assert "sprint_id" in context.missing_fields
        assert "member_login" in context.missing_fields

    def test_complete_context_no_clarification(self):
        """Test that complete context doesn't need clarification."""
        resolver = ContextResolver()

        context = ResolvedContext(
            sprint_id="DMS-SPRNT-1",
            member_login="Ivanov.A.B",
        )

        # Validate for task_search intent
        resolver._validate_context(context, ["task_search"])

        assert context.needs_clarification is False
        assert context.confidence == 0.9
