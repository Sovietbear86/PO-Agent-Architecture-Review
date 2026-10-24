"""Tests for Eval Case Model."""

import pytest

from po_agent.evaluation.case import (
    EvalCase,
    EvalCaseStore,
    EvalCaseStatus,
    EvalCaseSeverity,
    EvalCaseSource,
)


@pytest.fixture
def store():
    """Create eval case store."""
    s = EvalCaseStore(db_path=':memory:')
    yield s
    s.close()


class TestEvalCaseCreation:
    """Tests for eval case creation."""

    def test_eval_case_defaults(self, store):
        """Test eval case with defaults."""
        case = EvalCase(
            query="покажи задачи",
            expected_intent="task_search",
        )

        assert case.case_id is not None
        assert case.source == EvalCaseSource.MANUAL_CREATION.value
        assert case.query == "покажи задачи"
        assert case.expected_intent == "task_search"
        assert case.status == EvalCaseStatus.CANDIDATE.value

    def test_eval_case_full(self, store):
        """Test eval case with all fields."""
        case = EvalCase(
            query="что по спринту DMS-SPRNT-1",
            fixture="fixtures/sprint_test.json",
            reference="sprint health: 85%",
            expected_intent="sprint_health",
            expected_entities=[{"type": "sprint", "value": "DMS-SPRNT-1"}],
            tags=["sprint", "health"],
            severity=EvalCaseSeverity.HIGH.value,
            source=EvalCaseSource.USER_FEEDBACK.value,
        )

        assert case.case_id is not None
        assert case.fixture == "fixtures/sprint_test.json"
        assert case.reference == "sprint health: 85%"
        assert case.expected_intent == "sprint_health"
        assert len(case.expected_entities) == 1
        assert "sprint" in case.tags
        assert case.severity == EvalCaseSeverity.HIGH.value


class TestEvalCaseStore:
    """Tests for eval case store."""

    def test_add_case(self, store):
        """Test adding a case."""
        case = EvalCase(
            query="test query",
            expected_intent="help",
        )

        added = store.add_case(case)
        assert added.case_id == case.case_id
        assert len(store.cases) == 1

    def test_get_case(self, store):
        """Test getting a case by ID."""
        case = EvalCase(
            query="test query",
            expected_intent="help",
        )
        store.add_case(case)

        retrieved = store.get_case(case.case_id)
        assert retrieved is not None
        assert retrieved.query == "test query"

    def test_get_nonexistent_case(self, store):
        """Test getting non-existent case."""
        result = store.get_case("nonexistent")
        assert result is None

    def test_get_cases_by_status(self, store):
        """Test getting cases by status."""
        for i in range(3):
            case = EvalCase(
                query=f"test {i}",
                expected_intent="help",
                status=EvalCaseStatus.CANDIDATE.value,
            )
            store.add_case(case)

        for i in range(2):
            case = EvalCase(
                query=f"approved {i}",
                expected_intent="help",
                status=EvalCaseStatus.APPROVED.value,
                approved=True,
            )
            store.add_case(case)

        candidates = store.get_cases_by_status(EvalCaseStatus.CANDIDATE.value)
        assert len(candidates) == 3

        approved = store.get_cases_by_status(EvalCaseStatus.APPROVED.value)
        assert len(approved) == 2

    def test_approve_case(self, store):
        """Test approving a case."""
        case = EvalCase(
            query="test query",
            expected_intent="help",
        )
        store.add_case(case)

        result = store.approve_case(case.case_id, "admin")

        assert result is not None
        assert result.approved is True
        assert result.approved_by == "admin"
        assert result.status == EvalCaseStatus.APPROVED.value

    def test_reject_case(self, store):
        """Test rejecting a case."""
        case = EvalCase(
            query="test query",
            expected_intent="help",
        )
        store.add_case(case)

        result = store.reject_case(case.case_id)

        assert result is not None
        assert result.status == EvalCaseStatus.REJECTED.value

    def test_get_approved_cases(self, store):
        """Test getting approved cases."""
        for i in range(3):
            case = EvalCase(
                query=f"test {i}",
                expected_intent="help",
                status=EvalCaseStatus.CANDIDATE.value,
            )
            store.add_case(case)

        for i in range(2):
            case = EvalCase(
                query=f"approved {i}",
                expected_intent="help",
                status=EvalCaseStatus.APPROVED.value,
                approved=True,
            )
            store.add_case(case)

        approved = store.get_approved_cases()
        assert len(approved) == 2


class TestEvalCaseFromTrace:
    """Tests for creating cases from traces."""

    def test_create_from_trace(self, store):
        """Test creating case from trace."""
        case = store.create_from_trace(
            trace_id="trace-123",
            query="покажи задачи",
            expected_intent="task_search",
            tags=["sprint"],
        )

        assert case.source == EvalCaseSource.TRACE_ANALYSIS.value
        assert case.query == "покажи задачи"
        assert case.expected_intent == "task_search"
        assert "sprint" in case.tags
        assert case.created_from_trace == "trace-123"

    def test_create_from_feedback(self, store):
        """Test creating case from feedback."""
        case = store.create_from_feedback(
            feedback_id="feedback-123",
            trace_id="trace-456",
            query="скорость команды",
            expected_intent="velocity",
            expected_entities=[],
        )

        assert case.source == EvalCaseSource.USER_FEEDBACK.value
        assert case.query == "скорость команды"
        assert case.expected_intent == "velocity"
        assert "feedback" in case.tags
        assert case.severity == EvalCaseSeverity.HIGH.value


class TestEvalCaseStatusTransitions:
    """Tests for status transitions."""

    def test_candidate_to_approved(self, store):
        """Test transition from candidate to approved."""
        case = EvalCase(
            query="test",
            expected_intent="help",
            status=EvalCaseStatus.CANDIDATE.value,
        )
        store.add_case(case)

        result = store.approve_case(case.case_id, "admin")

        assert result.status == EvalCaseStatus.APPROVED.value
        assert result.approved is True

    def test_candidate_to_rejected(self, store):
        """Test transition from candidate to rejected."""
        case = EvalCase(
            query="test",
            expected_intent="help",
            status=EvalCaseStatus.CANDIDATE.value,
        )
        store.add_case(case)

        result = store.reject_case(case.case_id)

        assert result.status == EvalCaseStatus.REJECTED.value

    def test_timestamps(self, store):
        """Test that timestamps are set."""
        import time

        case = EvalCase(
            query="test",
            expected_intent="help",
        )

        # Small delay to ensure different timestamps
        time.sleep(0.01)

        # Create a new case to ensure different created_at
        case2 = EvalCase(
            query="test2",
            expected_intent="help",
        )

        assert case.created_at is not None
        assert case.updated_at is not None
        assert case2.created_at >= case.created_at
