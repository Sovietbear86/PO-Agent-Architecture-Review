"""Promotion & Rollback for PO Agent Platform v2.

Manages version deployments:
- Promotion: deploy shadow version to production
- Rollback: revert to previous production version
"""

import sqlite3
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional


class PromotionAction(Enum):
    """Type of promotion action."""
    PROMOTION = "promotion"
    ROLLBACK = "rollback"


class PromotionStatus(Enum):
    """Status of promotion."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class PromotionRecord:
    """Single promotion/rollback record."""

    def __init__(
        self,
        action_type: str,
        prompt_name: str,
        from_version: int,
        to_version: int,
        requested_by: Optional[str] = None,
        rollback_reason: Optional[str] = None,
        status: str = PromotionStatus.PENDING.value,
        created_at: Optional[datetime] = None,
    ):
        """Initialize promotion record.

        Args:
            action_type: Type of action (promotion/rollback)
            prompt_name: Name of the prompt
            from_version: Source version
            to_version: Target version
            requested_by: User who requested
            rollback_reason: Reason for rollback (if rollback)
            status: Promotion status
            created_at: Creation timestamp
        """
        self.id = str(uuid.uuid4())
        self.action_type = action_type
        self.prompt_name = prompt_name
        self.from_version = from_version
        self.to_version = to_version
        self.requested_by = requested_by
        self.rollback_reason = rollback_reason
        self.status = status
        self.approved_by: Optional[str] = None
        self.deployed_at: Optional[datetime] = None
        self.created_at = created_at or datetime.now()

    def approve(self, approved_by: str) -> None:
        """Approve the promotion."""
        self.status = PromotionStatus.COMPLETED.value
        self.approved_by = approved_by
        self.deployed_at = datetime.now()

    def fail(self, reason: Optional[str] = None) -> None:
        """Mark promotion as failed."""
        self.status = PromotionStatus.FAILED.value
        if reason:
            self.rollback_reason = reason

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "action_type": self.action_type,
            "prompt_name": self.prompt_name,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "requested_by": self.requested_by,
            "rollback_reason": self.rollback_reason,
            "status": self.status,
            "approved_by": self.approved_by,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "created_at": self.created_at.isoformat(),
        }


class PromotionManager:
    """Promotion & Rollback manager with SQLite persistence."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize promotion manager.

        Args:
            db_path: SQLite database path (":memory:" for in-memory, or file path)
        """
        self.db_path = db_path
        self.promotions: list[PromotionRecord] = []
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promotions (
                id TEXT PRIMARY KEY,
                action_type TEXT NOT NULL,
                prompt_name TEXT NOT NULL,
                from_version INTEGER NOT NULL,
                to_version INTEGER NOT NULL,
                requested_by TEXT,
                rollback_reason TEXT,
                status TEXT NOT NULL,
                approved_by TEXT,
                deployed_at TEXT,
                created_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_promotions_prompt ON promotions(prompt_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_promotions_action ON promotions(action_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_promotions_status ON promotions(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_promotions_created ON promotions(created_at)
        """)
        self._conn.commit()

    def create_promotion(
        self,
        prompt_name: str,
        from_version: int,
        to_version: int,
        requested_by: Optional[str] = None,
    ) -> PromotionRecord:
        """Create a promotion record.

        Args:
            prompt_name: Name of the prompt
            from_version: Source version
            to_version: Target version
            requested_by: User who requested

        Returns:
            Promotion record
        """
        record = PromotionRecord(
            action_type=PromotionAction.PROMOTION.value,
            prompt_name=prompt_name,
            from_version=from_version,
            to_version=to_version,
            requested_by=requested_by,
        )
        self.promotions.append(record)
        self.save_record(record)
        return record

    def create_rollback(
        self,
        prompt_name: str,
        from_version: int,
        to_version: int,
        rollback_reason: str,
        requested_by: Optional[str] = None,
    ) -> PromotionRecord:
        """Create a rollback record.

        Args:
            prompt_name: Name of the prompt
            from_version: Source version
            to_version: Target version
            rollback_reason: Reason for rollback
            requested_by: User who requested

        Returns:
            Promotion record
        """
        record = PromotionRecord(
            action_type=PromotionAction.ROLLBACK.value,
            prompt_name=prompt_name,
            from_version=from_version,
            to_version=to_version,
            requested_by=requested_by,
            rollback_reason=rollback_reason,
        )
        self.promotions.append(record)
        self.save_record(record)
        return record

    def save_record(self, record: PromotionRecord) -> None:
        """Save promotion record to database."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO promotions
            (id, action_type, prompt_name, from_version, to_version,
             requested_by, rollback_reason, status, approved_by, deployed_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.action_type,
                record.prompt_name,
                record.from_version,
                record.to_version,
                record.requested_by,
                record.rollback_reason,
                record.status,
                record.approved_by,
                record.deployed_at.isoformat() if record.deployed_at else None,
                record.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def approve_promotion(
        self,
        record_id: str,
        approved_by: str,
    ) -> Optional[PromotionRecord]:
        """Approve a promotion record."""
        record = self.get_by_id(record_id)
        if record:
            record.approve(approved_by)
            self.save_record(record)
        return record

    def fail_promotion(
        self,
        record_id: str,
        reason: Optional[str] = None,
    ) -> Optional[PromotionRecord]:
        """Mark a promotion as failed."""
        record = self.get_by_id(record_id)
        if record:
            record.fail(reason)
            self.save_record(record)
        return record

    def get_by_id(self, record_id: str) -> Optional[PromotionRecord]:
        """Get promotion record by ID."""
        for r in self.promotions:
            if r.id == record_id:
                return r
        return None

    def get_by_prompt(self, prompt_name: str) -> list[PromotionRecord]:
        """Get promotion records by prompt name."""
        return [r for r in self.promotions if r.prompt_name == prompt_name]

    def get_by_action(self, action_type: str) -> list[PromotionRecord]:
        """Get promotion records by action type."""
        return [r for r in self.promotions if r.action_type == action_type]

    def get_pending(self) -> list[PromotionRecord]:
        """Get pending promotion records."""
        return [r for r in self.promotions if r.status == PromotionStatus.PENDING.value]

    def get_completed(self) -> list[PromotionRecord]:
        """Get completed promotion records."""
        return [r for r in self.promotions if r.status == PromotionStatus.COMPLETED.value]

    def get_failed(self) -> list[PromotionRecord]:
        """Get failed promotion records."""
        return [r for r in self.promotions if r.status == PromotionStatus.FAILED.value]

    def get_latest(self, prompt_name: str, limit: int = 10) -> list[PromotionRecord]:
        """Get latest promotion records for a prompt."""
        prompt_promotions = self.get_by_prompt(prompt_name)
        return sorted(prompt_promotions, key=lambda r: r.created_at, reverse=True)[:limit]

    def get_statistics(self, prompt_name: Optional[str] = None) -> dict:
        """Get promotion statistics.

        Args:
            prompt_name: Optional prompt name to filter

        Returns:
            Dictionary with statistics
        """
        promotions = self.promotions
        if prompt_name:
            promotions = self.get_by_prompt(prompt_name)

        total = len(promotions)
        if total == 0:
            return {
                "total": 0,
                "promotions": 0,
                "rollbacks": 0,
                "pending": 0,
                "completed": 0,
                "failed": 0,
            }

        promotions_count = len([r for r in promotions if r.action_type == PromotionAction.PROMOTION.value])
        rollbacks_count = len([r for r in promotions if r.action_type == PromotionAction.ROLLBACK.value])
        pending = len([r for r in promotions if r.status == PromotionStatus.PENDING.value])
        completed = len([r for r in promotions if r.status == PromotionStatus.COMPLETED.value])
        failed = len([r for r in promotions if r.status == PromotionStatus.FAILED.value])

        return {
            "total": total,
            "promotions": promotions_count,
            "rollbacks": rollbacks_count,
            "pending": pending,
            "completed": completed,
            "failed": failed,
        }

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
