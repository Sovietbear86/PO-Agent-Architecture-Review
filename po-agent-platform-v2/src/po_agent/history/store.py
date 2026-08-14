"""Operational History Store for PO Agent Platform v2.

Storage interface + SQLite implementation.
Persist traces and execution metadata.
"""

import sqlite3
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TraceEntry(BaseModel):
    """Trace entry for history storage."""
    trace_id: str
    request_id: str
    session_id: Optional[str] = None
    timestamp: datetime
    request: str
    intent: str
    intent_confidence: float
    latency_ms: float
    error_count: int = 0
    warning_count: int = 0
    # Version tracking for reproducibility
    agent_version: Optional[str] = None
    router_version: Optional[str] = None
    prompt_version: Optional[str] = None
    capability_version: Optional[str] = None
    model_version: Optional[str] = None
    config_version: Optional[str] = None
    # Skill tracking (ADDENDUM 01)
    skill_id: Optional[str] = None
    skill_version: Optional[str] = None
    skill_status: Optional[str] = None  # completed, failed, clarification_required


class OperationalHistory:
    """Operational history storage interface."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize operational history.

        Args:
            db_path: SQLite database path (":memory:" for in-memory)
        """
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                trace_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                session_id TEXT,
                timestamp TEXT NOT NULL,
                request TEXT NOT NULL,
                intent TEXT NOT NULL,
                intent_confidence REAL NOT NULL,
                latency_ms REAL NOT NULL,
                error_count INTEGER DEFAULT 0,
                warning_count INTEGER DEFAULT 0,
                agent_version TEXT,
                router_version TEXT,
                prompt_version TEXT,
                capability_version TEXT,
                model_version TEXT,
                config_version TEXT,
                skill_id TEXT,
                skill_version TEXT,
                skill_status TEXT
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_traces_session ON traces(session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_traces_intent ON traces(intent)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_traces_timestamp ON traces(timestamp)
        """)
        self._conn.commit()

    def add_trace(self, entry: TraceEntry) -> None:
        """Add a trace entry.

        Args:
            entry: Trace entry to add
        """
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO traces
            (trace_id, request_id, session_id, timestamp, request, intent,
             intent_confidence, latency_ms, error_count, warning_count,
             agent_version, router_version, prompt_version,
             capability_version, model_version, config_version,
             skill_id, skill_version, skill_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.trace_id,
                entry.request_id,
                entry.session_id,
                entry.timestamp.isoformat(),
                entry.request,
                entry.intent,
                entry.intent_confidence,
                entry.latency_ms,
                entry.error_count,
                entry.warning_count,
                entry.agent_version,
                entry.router_version,
                entry.prompt_version,
                entry.capability_version,
                entry.model_version,
                entry.config_version,
                entry.skill_id,
                entry.skill_version,
                entry.skill_status,
            ),
        )
        self._conn.commit()

    def get_trace(self, trace_id: str) -> Optional[TraceEntry]:
        """Get a trace by ID.

        Args:
            trace_id: Trace ID

        Returns:
            Trace entry or None
        """
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM traces WHERE trace_id = ?",
            (trace_id,),
        )
        row = cursor.fetchone()
        if row:
            return TraceEntry(
                trace_id=row[0],
                request_id=row[1],
                session_id=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                request=row[4],
                intent=row[5],
                intent_confidence=row[6],
                latency_ms=row[7],
                error_count=row[8],
                warning_count=row[9],
                agent_version=row[10],
                router_version=row[11],
                prompt_version=row[12],
                capability_version=row[13],
                model_version=row[14],
                config_version=row[15],
            )
        return None

    def get_traces_by_session(self, session_id: str, limit: int = 100) -> list[TraceEntry]:
        """Get all traces for a session.

        Args:
            session_id: Session ID
            limit: Maximum number of results

        Returns:
            List of trace entries
        """
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM traces WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit),
        )
        rows = cursor.fetchall()
        return [
            TraceEntry(
                trace_id=row[0],
                request_id=row[1],
                session_id=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                request=row[4],
                intent=row[5],
                intent_confidence=row[6],
                latency_ms=row[7],
                error_count=row[8],
                warning_count=row[9],
                agent_version=row[10],
                router_version=row[11],
                prompt_version=row[12],
                capability_version=row[13],
                model_version=row[14],
                config_version=row[15],
            )
            for row in rows
        ]

    def get_traces_by_intent(self, intent: str, limit: int = 100) -> list[TraceEntry]:
        """Get all traces for an intent.

        Args:
            intent: Intent name
            limit: Maximum number of results

        Returns:
            List of trace entries
        """
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM traces WHERE intent = ? ORDER BY timestamp DESC LIMIT ?",
            (intent, limit),
        )
        rows = cursor.fetchall()
        return [
            TraceEntry(
                trace_id=row[0],
                request_id=row[1],
                session_id=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                request=row[4],
                intent=row[5],
                intent_confidence=row[6],
                latency_ms=row[7],
                error_count=row[8],
                warning_count=row[9],
                agent_version=row[10],
                router_version=row[11],
                prompt_version=row[12],
                capability_version=row[13],
                model_version=row[14],
                config_version=row[15],
            )
            for row in rows
        ]

    def get_recent_traces(self, limit: int = 100) -> list[TraceEntry]:
        """Get recent traces.

        Args:
            limit: Maximum number of results

        Returns:
            List of trace entries
        """
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM traces ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
        return [
            TraceEntry(
                trace_id=row[0],
                request_id=row[1],
                session_id=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                request=row[4],
                intent=row[5],
                intent_confidence=row[6],
                latency_ms=row[7],
                error_count=row[8],
                warning_count=row[9],
                agent_version=row[10],
                router_version=row[11],
                prompt_version=row[12],
                capability_version=row[13],
                model_version=row[14],
                config_version=row[15],
            )
            for row in rows
        ]

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
