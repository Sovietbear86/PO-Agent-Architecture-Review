"""Append-only operational history for the recovery Harness.

This is deliberately separate from conversation memory. It records executions
for reproducibility/evaluation and is never injected wholesale into prompts.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from .contracts import Evidence, HarnessRequest, HarnessResponse


@dataclass(frozen=True)
class ActiveVersions:
    agent: str = "2.1-recovery"
    router: str = "deterministic-v1"
    prompt: str | None = None
    capability: str = "1.0.0"
    metrics: str = "deterministic-v1"
    model: str | None = None
    config: str = "recovery-fixtures-v1"


@dataclass(frozen=True)
class ExecutionRecord:
    trace_id: str
    session_id: str
    timestamp: str
    request: str
    status: str
    intent: str | None
    skill_id: str | None
    skill_version: str | None
    capability_id: str | None
    evidence: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    latency_ms: float = 0.0
    llm_used: bool = False
    versions: ActiveVersions = field(default_factory=ActiveVersions)
    error_category: str | None = None


class HistoryStore(Protocol):
    def append(self, record: ExecutionRecord) -> None: ...
    def get(self, trace_id: str) -> ExecutionRecord | None: ...
    def by_session(self, session_id: str, limit: int = 100) -> list[ExecutionRecord]: ...
    def recent(self, limit: int = 100) -> list[ExecutionRecord]: ...


class SQLiteHistoryStore:
    """Small append-only SQLite store suitable for local/dev and tests."""

    def __init__(self, path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS harness_executions (
                trace_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                request TEXT NOT NULL,
                status TEXT NOT NULL,
                intent TEXT,
                skill_id TEXT,
                skill_version TEXT,
                capability_id TEXT,
                evidence_json TEXT NOT NULL,
                warnings_json TEXT NOT NULL,
                latency_ms REAL NOT NULL,
                llm_used INTEGER NOT NULL,
                versions_json TEXT NOT NULL,
                error_category TEXT
            )
            """
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_harness_session ON harness_executions(session_id, timestamp)")
        self._conn.commit()

    def append(self, record: ExecutionRecord) -> None:
        """Append exactly once; duplicate trace IDs are contract violations."""
        try:
            self._conn.execute(
                """INSERT INTO harness_executions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.trace_id,
                    record.session_id,
                    record.timestamp,
                    record.request,
                    record.status,
                    record.intent,
                    record.skill_id,
                    record.skill_version,
                    record.capability_id,
                    json.dumps(record.evidence, ensure_ascii=False, default=str),
                    json.dumps(record.warnings, ensure_ascii=False),
                    record.latency_ms,
                    1 if record.llm_used else 0,
                    json.dumps(asdict(record.versions), ensure_ascii=False),
                    record.error_category,
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"trace already exists: {record.trace_id}") from exc

    @staticmethod
    def _decode(row: tuple[Any, ...]) -> ExecutionRecord:
        versions = ActiveVersions(**json.loads(row[13]))
        return ExecutionRecord(
            trace_id=row[0], session_id=row[1], timestamp=row[2], request=row[3],
            status=row[4], intent=row[5], skill_id=row[6], skill_version=row[7],
            capability_id=row[8], evidence=json.loads(row[9]), warnings=json.loads(row[10]),
            latency_ms=row[11], llm_used=bool(row[12]), versions=versions,
            error_category=row[14],
        )

    def get(self, trace_id: str) -> ExecutionRecord | None:
        row = self._conn.execute("SELECT * FROM harness_executions WHERE trace_id = ?", (trace_id,)).fetchone()
        return self._decode(row) if row else None

    def by_session(self, session_id: str, limit: int = 100) -> list[ExecutionRecord]:
        rows = self._conn.execute(
            "SELECT * FROM harness_executions WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [self._decode(row) for row in rows]

    def recent(self, limit: int = 100) -> list[ExecutionRecord]:
        rows = self._conn.execute(
            "SELECT * FROM harness_executions ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._decode(row) for row in rows]

    def close(self) -> None:
        self._conn.close()


def record_from_response(
    request: HarnessRequest,
    response: HarnessResponse,
    *,
    capability_id: str | None,
    versions: ActiveVersions | None = None,
    llm_used: bool = False,
    error_category: str | None = None,
) -> ExecutionRecord:
    return ExecutionRecord(
        trace_id=response.trace_id,
        session_id=response.session_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        request=request.query,
        status=response.status.value,
        intent=response.intent,
        skill_id=response.skill_id,
        skill_version=response.skill_version,
        capability_id=capability_id,
        evidence=[item.to_dict() if isinstance(item, Evidence) else dict(item) for item in response.evidence],
        warnings=list(response.warnings),
        latency_ms=round(response.latency_ms, 3),
        llm_used=llm_used,
        versions=versions or ActiveVersions(),
        error_category=error_category,
    )
