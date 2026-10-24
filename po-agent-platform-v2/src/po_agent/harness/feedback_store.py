"""Trace-linked append-only feedback store for the recovery Harness."""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass(frozen=True)
class FeedbackRecord:
    feedback_id: str
    trace_id: str
    session_id: str | None
    timestamp: str
    rating: str
    correction: str | None = None
    expected_intent: str | None = None
    expected_entity: str | None = None
    comment: str | None = None
    metadata: dict[str, object] | None = None


class FeedbackStore(Protocol):
    def append(self, record: FeedbackRecord) -> None: ...
    def by_trace(self, trace_id: str) -> list[FeedbackRecord]: ...


class SQLiteFeedbackStore:
    """Small append-only SQLite store; JSON is used instead of eval/str(dict)."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                feedback_id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                session_id TEXT,
                timestamp TEXT NOT NULL,
                rating TEXT NOT NULL,
                correction TEXT,
                expected_intent TEXT,
                expected_entity TEXT,
                comment TEXT,
                metadata_json TEXT NOT NULL
            )
            """
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_harness_feedback_trace ON feedback(trace_id)")
        self._conn.commit()

    def append(self, record: FeedbackRecord) -> None:
        try:
            self._conn.execute(
                "INSERT INTO feedback VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record.feedback_id, record.trace_id, record.session_id, record.timestamp,
                    record.rating, record.correction, record.expected_intent,
                    record.expected_entity, record.comment,
                    json.dumps(record.metadata or {}, ensure_ascii=False, sort_keys=True),
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"feedback already exists: {record.feedback_id}") from exc

    def by_trace(self, trace_id: str) -> list[FeedbackRecord]:
        rows = self._conn.execute(
            "SELECT * FROM feedback WHERE trace_id = ? ORDER BY timestamp ASC", (trace_id,)
        ).fetchall()
        return [
            FeedbackRecord(
                feedback_id=row[0], trace_id=row[1], session_id=row[2], timestamp=row[3],
                rating=row[4], correction=row[5], expected_intent=row[6],
                expected_entity=row[7], comment=row[8], metadata=json.loads(row[9]),
            )
            for row in rows
        ]


def make_feedback(
    *,
    trace_id: str,
    session_id: str | None,
    rating: str,
    correction: str | None = None,
    expected_intent: str | None = None,
    expected_entity: str | None = None,
    comment: str | None = None,
    metadata: dict[str, object] | None = None,
) -> FeedbackRecord:
    normalized = rating.casefold().strip()
    if normalized not in {"up", "down"}:
        raise ValueError("rating must be 'up' or 'down'")
    return FeedbackRecord(
        feedback_id=str(uuid.uuid4()),
        trace_id=trace_id,
        session_id=session_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        rating=normalized,
        correction=correction,
        expected_intent=expected_intent,
        expected_entity=expected_entity,
        comment=comment,
        metadata=metadata or {},
    )
