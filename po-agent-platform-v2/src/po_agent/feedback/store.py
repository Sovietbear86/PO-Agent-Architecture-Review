"""User Feedback Store for PO Agent Platform v2.

Support:
- thumbs up/down
- correction text
- expected intent
- expected entity
- expected answer fact
- optional comment

Feedback links to trace_id.
"""

import sqlite3
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class FeedbackType(Enum):
    """Feedback type."""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    CORRECTION = "correction"
    EXPECTED_INTENT = "expected_intent"
    EXPECTED_ENTITY = "expected_entity"
    EXPECTED_FACT = "expected_fact"
    COMMENT = "comment"


class FeedbackEntry(BaseModel):
    """Feedback entry."""
    feedback_id: str
    trace_id: str
    session_id: Optional[str] = None
    timestamp: datetime
    feedback_type: FeedbackType
    data: dict
    # Skill tracking (ADDENDUM 01)
    skill_id: Optional[str] = None
    skill_version: Optional[str] = None
    skill_rating: Optional[int] = None  # 1-5 rating for skill performance


class FeedbackStore:
    """User feedback storage interface."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize feedback store.

        Args:
            db_path: SQLite database path
        """
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                feedback_id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                session_id TEXT,
                timestamp TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                data TEXT NOT NULL,
                skill_id TEXT,
                skill_version TEXT,
                skill_rating INTEGER
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_trace ON feedback(trace_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_session ON feedback(session_id)
        """)
        self._conn.commit()

    def add_feedback(
        self,
        feedback_id: str,
        trace_id: str,
        session_id: Optional[str],
        feedback_type: FeedbackType,
        data: dict,
    ) -> None:
        """Add feedback entry.

        Args:
            feedback_id: Unique feedback ID
            trace_id: Linked trace ID
            session_id: Session ID
            feedback_type: Feedback type
            data: Feedback data
        """
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO feedback
            (feedback_id, trace_id, session_id, timestamp, feedback_type, data,
             skill_id, skill_version, skill_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feedback_id,
                trace_id,
                session_id,
                datetime.now().isoformat(),
                feedback_type.value,
                str(data),
                data.get("skill_id"),
                data.get("skill_version"),
                data.get("skill_rating"),
            ),
        )
        self._conn.commit()

    def get_feedback_by_trace(self, trace_id: str) -> list[FeedbackEntry]:
        """Get feedback for a trace.

        Args:
            trace_id: Trace ID

        Returns:
            List of feedback entries
        """
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM feedback WHERE trace_id = ?",
            (trace_id,),
        )
        rows = cursor.fetchall()
        return [
            FeedbackEntry(
                feedback_id=row[0],
                trace_id=row[1],
                session_id=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                feedback_type=FeedbackType(row[4]),
                data=eval(row[5]),
            )
            for row in rows
        ]

    def get_all_feedback(self, limit: int = 100) -> list[FeedbackEntry]:
        """Get all feedback.

        Args:
            limit: Maximum number of results

        Returns:
            List of feedback entries
        """
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM feedback ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
        return [
            FeedbackEntry(
                feedback_id=row[0],
                trace_id=row[1],
                session_id=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                feedback_type=FeedbackType(row[4]),
                data=eval(row[5]),
            )
            for row in rows
        ]

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
