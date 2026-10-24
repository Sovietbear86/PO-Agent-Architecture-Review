"""Tests for Clarification Engine."""

import pytest
from datetime import datetime, timedelta

from po_agent.clarification.engine import ClarificationEngine
from po_agent.clarification.models import (
    ClarificationRequest,
    ClarificationResponse,
    ClarificationStatus,
)
from po_agent.memory.session_memory import SessionMemory
from po_agent.models.resolved_context import ResolvedContext, ContextSource


class TestClarificationEngineBasic:
    """Basic ClarificationEngine functionality."""

    def test_init_with_defaults(self):
        """Test initialization with defaults."""
        engine = ClarificationEngine()
        assert engine.session_memory is not None
        assert engine.available_products == []

    def test_init_with_products(self):
        """Test initialization with products list."""
        products = ["WMB", "OLP"]
        engine = ClarificationEngine(available_products=products)
        assert engine.available_products == products

    def test_needs_clarification_no_missing(self):
        """Test when no clarification needed."""
        engine = ClarificationEngine()
        context = ResolvedContext(
            product="OLP",
            sprint_id="OLP-SPRNT-1",
            needs_clarification=False,
        )
        required = ["product", "sprint_id"]

        result = engine.needs_clarification(context, required)
        assert result is None

    def test_needs_clarification_with_missing(self):
        """Test when clarification is needed."""
        engine = ClarificationEngine(available_products=["OLP", "DMS"])
        context = ResolvedContext(
            product=None,
            sprint_id="OLP-SPRNT-1",
            needs_clarification=True,
            missing_fields=["product"],
        )
        required = ["product", "sprint_id"]

        result = engine.needs_clarification(context, required)
        assert result is not None
        assert isinstance(result, ClarificationRequest)
        assert "product" in result.missing_fields
        assert result.question == "По какому продукту показать результаты?"


class TestClarificationEngineOptions:
    """Options generation tests."""

    def test_options_from_products(self):
        """Test options from products list."""
        engine = ClarificationEngine(available_products=["WMB", "OLP", "DMS"])
        context = ResolvedContext(
            product=None,
            needs_clarification=True,
            missing_fields=["product"],
        )

        result = engine.needs_clarification(context, ["product"])
        assert result is not None
        assert len(result.options) == 3
        assert result.options[0].label == "WMB"
        assert result.options[0].value == "WMB"

    def test_options_from_sprints(self):
        """Test options from sprints list."""
        engine = ClarificationEngine(available_sprints=["DMS-SPRNT-1", "OLP-SPRNT-1"])
        context = ResolvedContext(
            sprint_id=None,
            needs_clarification=True,
            missing_fields=["sprint_id"],
        )

        result = engine.needs_clarification(context, ["sprint_id"])
        assert result is not None
        assert len(result.options) == 2
        assert result.options[0].label == "DMS-SPRNT-1"

    def test_no_session_value_skips_clarification(self):
        """Test that session value skips clarification."""
        session = SessionMemory()
        session.set("current_product", "OLP")

        engine = ClarificationEngine(
            session_memory=session,
            available_products=["WMB", "OLP"],
        )
        context = ResolvedContext(
            product=None,
            needs_clarification=True,
            missing_fields=["product"],
        )

        # Should skip clarification because session has value
        result = engine.needs_clarification(context, ["product"])
        assert result is None

    def test_question_generation(self):
        """Test question generation for different fields."""
        engine = ClarificationEngine()

        assert "продукт" in engine._generate_question("product").lower()
        assert "спринт" in engine._generate_question("sprint_id").lower()
        assert "участник" in engine._generate_question("member_login").lower()


class TestClarificationResponse:
    """ClarificationResponse tests."""

    def test_needs_clarification_response(self):
        """Test needs_clarification response."""
        response = ClarificationResponse.needs_clarification(
            clarification_id="clar-123",
            question="Какой спринт?",
        )
        assert response.status == ClarificationStatus.PENDING
        assert response.clarification_id == "clar-123"
        assert response.question == "Какой спринт?"

    def test_completed_response(self):
        """Test completed response."""
        resolution = {"field": "product", "value": "OLP"}
        response = ClarificationResponse.completed(resolution)

        assert response.status == ClarificationStatus.ANSWERED
        assert response.resolution == resolution

    def test_cancelled_response(self):
        """Test cancelled response."""
        response = ClarificationResponse.cancelled()
        assert response.status == ClarificationStatus.CANCELLED


class TestClarificationEngineProcessAnswer:
    """Answer processing tests."""

    def test_process_answer_with_option(self):
        """Test processing answer with selected option."""
        engine = ClarificationEngine()

        request = ClarificationRequest(
            clarification_id="clar-123",
            reason="Missing product",
            missing_fields=["product"],
            question="Какой продукт?",
            original_query="покажи задачи",
        )

        result = engine.process_answer(request, "", selected_option="OLP")

        assert result.status == ClarificationStatus.ANSWERED
        assert result.resolution is not None
        assert result.resolution["value"] == "OLP"

    def test_process_answer_with_text(self):
        """Test processing answer with text."""
        engine = ClarificationEngine()

        request = ClarificationRequest(
            clarification_id="clar-123",
            reason="Missing product",
            missing_fields=["product"],
            question="Какой продукт?",
            original_query="покажи задачи",
        )

        result = engine.process_answer(request, "DataMarts", None)

        assert result.status == ClarificationStatus.ANSWERED
        assert result.resolution is not None
        assert result.resolution["value"] == "DataMarts"


class TestClarificationEngineIntegration:
    """Integration tests."""

    def test_full_clarification_flow(self):
        """Test full clarification flow."""
        engine = ClarificationEngine(available_products=["WMB", "OLP", "DMS"])
        context = ResolvedContext(
            product=None,
            needs_clarification=True,
            missing_fields=["product"],
        )

        # Step 1: Check if clarification needed
        request = engine.needs_clarification(context, ["product"])
        assert request is not None

        # Step 2: Process answer
        result = engine.process_answer(request, "OLP", None)
        assert result.status == ClarificationStatus.ANSWERED
        assert result.resolution["value"] == "OLP"
