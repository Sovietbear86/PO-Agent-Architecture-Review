"""Tests for Feedback Store."""

import uuid

import pytest

from po_agent.feedback.store import FeedbackStore, FeedbackType


@pytest.fixture
def store():
    """Create feedback store with in-memory SQLite."""
    s = FeedbackStore(db_path=":memory:")
    yield s
    s.close()


class TestFeedbackStoreBasic:
    """Tests for basic operations."""

    def test_add_and_get_feedback(self, store):
        """Test adding and getting feedback."""
        feedback_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())

        store.add_feedback(
            feedback_id=feedback_id,
            trace_id=trace_id,
            session_id="session-1",
            feedback_type=FeedbackType.THUMBS_UP,
            data={"note": "good answer"},
        )

        feedback = store.get_feedback_by_trace(trace_id)
        assert len(feedback) == 1
        assert feedback[0].feedback_id == feedback_id
        assert feedback[0].feedback_type == FeedbackType.THUMBS_UP

    def test_feedback_links_to_trace(self, store):
        """Test feedback links to trace."""
        trace_id = str(uuid.uuid4())

        store.add_feedback(
            feedback_id=str(uuid.uuid4()),
            trace_id=trace_id,
            session_id=None,
            feedback_type=FeedbackType.THUMBS_DOWN,
            data={"note": "bad"},
        )

        feedback = store.get_feedback_by_trace(trace_id)
        assert len(feedback) == 1
        assert feedback[0].trace_id == trace_id


class TestFeedbackStoreQueries:
    """Tests for query operations."""

    def test_get_all_feedback(self, store):
        """Test getting all feedback."""
        for i in range(3):
            store.add_feedback(
                feedback_id=str(uuid.uuid4()),
                trace_id=str(uuid.uuid4()),
                session_id=None,
                feedback_type=FeedbackType.THUMBS_UP,
                data={"index": i},
            )

        all_feedback = store.get_all_feedback()
        assert len(all_feedback) == 3

    def test_feedback_types(self, store):
        """Test different feedback types."""
        store.add_feedback(
            feedback_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            session_id=None,
            feedback_type=FeedbackType.CORRECTION,
            data={"correction": "right answer"},
        )
        store.add_feedback(
            feedback_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            session_id=None,
            feedback_type=FeedbackType.EXPECTED_INTENT,
            data={"intent": "task_search"},
        )

        all_feedback = store.get_all_feedback()
        types = {f.feedback_type for f in all_feedback}
        assert FeedbackType.CORRECTION in types
        assert FeedbackType.EXPECTED_INTENT in types


class TestFeedbackStoreSession:
    """Tests for session-based queries."""

    def test_feedback_by_session(self, store):
        """Test feedback by session."""
        session_id = "session-1"

        store.add_feedback(
            feedback_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            session_id=session_id,
            feedback_type=FeedbackType.THUMBS_UP,
            data={},
        )
        store.add_feedback(
            feedback_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            session_id=session_id,
            feedback_type=FeedbackType.THUMBS_DOWN,
            data={},
        )

        all_feedback = store.get_all_feedback()
        assert len(all_feedback) == 2
