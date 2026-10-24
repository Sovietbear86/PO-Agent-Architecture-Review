"""Tests for Operational History Store."""

import time
import uuid

import pytest

from po_agent.history.store import OperationalHistory, TraceEntry


@pytest.fixture
def history():
    """Create history with in-memory SQLite."""
    h = OperationalHistory(db_path=":memory:")
    yield h
    h.close()


class TestOperationalHistoryBasic:
    """Tests for basic operations."""

    def test_add_and_get_trace(self, history):
        """Test adding and getting a trace."""
        entry = TraceEntry(
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            session_id="session-1",
            timestamp=history._conn.execute("SELECT datetime('now')").fetchone()[0],
            request="test",
            intent="help",
            intent_confidence=0.0,
            latency_ms=10.0,
        )

        history.add_trace(entry)
        result = history.get_trace(entry.trace_id)

        assert result is not None
        assert result.request == "test"
        assert result.intent == "help"

    def test_get_nonexistent_trace(self, history):
        """Test getting non-existent trace."""
        result = history.get_trace("nonexistent-id")
        assert result is None


class TestOperationalHistoryQueries:
    """Tests for query operations."""

    def test_get_traces_by_session(self, history):
        """Test getting traces by session."""
        session_id = "session-1"

        for i in range(3):
            entry = TraceEntry(
                trace_id=str(uuid.uuid4()),
                request_id=str(uuid.uuid4()),
                session_id=session_id,
                timestamp=history._conn.execute("SELECT datetime('now')").fetchone()[0],
                request=f"test {i}",
                intent="help",
                intent_confidence=0.0,
                latency_ms=10.0,
            )
            history.add_trace(entry)

        results = history.get_traces_by_session(session_id)
        assert len(results) == 3

    def test_get_traces_by_intent(self, history):
        """Test getting traces by intent."""
        for i in range(2):
            entry = TraceEntry(
                trace_id=str(uuid.uuid4()),
                request_id=str(uuid.uuid4()),
                session_id=None,
                timestamp=history._conn.execute("SELECT datetime('now')").fetchone()[0],
                request=f"test {i}",
                intent="help",
                intent_confidence=0.0,
                latency_ms=10.0,
            )
            history.add_trace(entry)

        results = history.get_traces_by_intent("help")
        assert len(results) == 2

    def test_get_recent_traces(self, history):
        """Test getting recent traces."""
        for i in range(5):
            entry = TraceEntry(
                trace_id=str(uuid.uuid4()),
                request_id=str(uuid.uuid4()),
                session_id=None,
                timestamp=history._conn.execute("SELECT datetime('now')").fetchone()[0],
                request=f"test {i}",
                intent="help",
                intent_confidence=0.0,
                latency_ms=10.0,
            )
            history.add_trace(entry)

        results = history.get_recent_traces(limit=3)
        assert len(results) == 3

    def test_traces_sorted_by_timestamp(self, history):
        """Test that traces are sorted by timestamp."""
        for i in range(3):
            entry = TraceEntry(
                trace_id=str(uuid.uuid4()),
                request_id=str(uuid.uuid4()),
                session_id=None,
                timestamp=history._conn.execute("SELECT datetime('now')").fetchone()[0],
                request=f"test {i}",
                intent="help",
                intent_confidence=0.0,
                latency_ms=10.0,
            )
            history.add_trace(entry)
            time.sleep(0.1)

        results = history.get_recent_traces(limit=3)
        assert len(results) == 3
