"""Eval Case Model for PO Agent Platform v2.

Fields may include:
- case_id, source, query
- fixture/reference
- expected_intent, expected_entities
- expected_structured_result
- tags, severity
- status, created_from_trace, approved
"""

import sqlite3
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EvalCaseStatus(Enum):
    """Status of eval case."""
    CANDIDATE = "candidate"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class EvalCaseSeverity(Enum):
    """Severity of eval case."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvalCaseSource(Enum):
    """Source of eval case."""
    USER_FEEDBACK = "user_feedback"
    TRACE_ANALYSIS = "trace_analysis"
    FAILURE_MINING = "failure_mining"
    MANUAL_CREATION = "manual_creation"
    AUTO_GENERATED = "auto_generated"


class EvalCase(BaseModel):
    """Eval case for testing capabilities."""
    case_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str = Field(default=EvalCaseSource.MANUAL_CREATION.value)

    # Query and expected results
    query: str = Field(..., description="User query to test")
    fixture: Optional[str] = Field(None, description="Fixture data path")
    reference: Optional[str] = Field(None, description="Reference answer")

    # Expected outputs
    expected_intent: Optional[str] = Field(None, description="Expected intent")
    expected_entities: list[dict] = Field(default_factory=list)
    expected_structured_result: Optional[dict] = Field(None)

    # Metadata
    tags: list[str] = Field(default_factory=list)
    severity: str = Field(default=EvalCaseSeverity.MEDIUM.value)
    status: str = Field(default=EvalCaseStatus.CANDIDATE.value)

    created_from_trace: Optional[str] = Field(None)
    approved: bool = Field(default=False)
    approved_by: Optional[str] = Field(None)
    approved_at: Optional[datetime] = Field(None)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class EvalCaseStore:
    """Store for eval cases with SQLite persistence."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize eval case store.

        Args:
            db_path: SQLite database path (":memory:" for in-memory, or file path)
        """
        self.db_path = db_path
        self.cases: list[EvalCase] = []
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eval_cases (
                case_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                query TEXT NOT NULL,
                expected_intent TEXT,
                expected_entities TEXT,
                tags TEXT,
                status TEXT NOT NULL,
                approved_by TEXT,
                approved_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cases_status ON eval_cases(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cases_source ON eval_cases(source)
        """)
        self._conn.commit()

    def add_case(self, case: EvalCase) -> EvalCase:
        """Add a new eval case.

        Args:
            case: Eval case to add

        Returns:
            Added eval case
        """
        self.cases.append(case)
        self.save_case(case)
        return case

    def save_case(self, case: EvalCase) -> None:
        """Save case to database."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO eval_cases
            (case_id, source, query, expected_intent, expected_entities,
             tags, status, approved_by, approved_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case.case_id,
                case.source,
                case.query,
                case.expected_intent,
                str(case.expected_entities) if case.expected_entities else None,
                str(case.tags) if case.tags else None,
                case.status,
                case.approved_by,
                case.approved_at.isoformat() if case.approved_at else None,
                case.created_at.isoformat(),
                case.updated_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get_case(self, case_id: str) -> Optional[EvalCase]:
        """Get a case by ID.

        Args:
            case_id: Case ID

        Returns:
            Eval case or None
        """
        for case in self.cases:
            if case.case_id == case_id:
                return case
        return None

    def get_cases_by_status(self, status: str) -> list[EvalCase]:
        """Get cases by status.

        Args:
            status: Case status

        Returns:
            List of eval cases
        """
        return [c for c in self.cases if c.status == status]

    def get_approved_cases(self) -> list[EvalCase]:
        """Get all approved cases.

        Returns:
            List of approved eval cases
        """
        return [c for c in self.cases if c.approved and c.status == "approved"]

    def approve_case(
        self,
        case_id: str,
        approved_by: str,
    ) -> Optional[EvalCase]:
        """Approve an eval case.

        Args:
            case_id: Case ID
            approved_by: User who approved

        Returns:
            Updated case or None
        """
        case = self.get_case(case_id)
        if case:
            case.approved = True
            case.approved_by = approved_by
            case.approved_at = datetime.now()
            case.status = EvalCaseStatus.APPROVED.value
            case.updated_at = datetime.now()
        return case

    def reject_case(self, case_id: str) -> Optional[EvalCase]:
        """Reject an eval case.

        Args:
            case_id: Case ID

        Returns:
            Updated case or None
        """
        case = self.get_case(case_id)
        if case:
            case.status = EvalCaseStatus.REJECTED.value
            case.updated_at = datetime.now()
        return case

    def create_from_trace(
        self,
        trace_id: str,
        query: str,
        expected_intent: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> EvalCase:
        """Create eval case from trace.

        Args:
            trace_id: Source trace ID
            query: User query
            expected_intent: Expected intent (if known)
            tags: Tags for the case

        Returns:
            New eval case
        """
        return EvalCase(
            source=EvalCaseSource.TRACE_ANALYSIS.value,
            query=query,
            expected_intent=expected_intent,
            tags=tags or [],
            created_from_trace=trace_id,
            severity=EvalCaseSeverity.MEDIUM.value,
        )

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()

    def create_from_feedback(
        self,
        feedback_id: str,
        trace_id: str,
        query: str,
        expected_intent: Optional[str] = None,
        expected_entities: Optional[list[dict]] = None,
    ) -> EvalCase:
        """Create eval case from user feedback.

        Args:
            feedback_id: Source feedback ID
            trace_id: Source trace ID
            query: User query
            expected_intent: Expected intent
            expected_entities: Expected entities

        Returns:
            New eval case
        """
        return EvalCase(
            source=EvalCaseSource.USER_FEEDBACK.value,
            query=query,
            expected_intent=expected_intent,
            expected_entities=expected_entities or [],
            tags=["feedback"],
            severity=EvalCaseSeverity.HIGH.value,
            created_from_trace=trace_id,
        )
