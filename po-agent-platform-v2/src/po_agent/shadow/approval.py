"""Human Approval Gate for PO Agent Platform v2.

Manual override for failed regression gates:
1. Flag gate failures requiring review
2. Manual approval by team member
3. Log approval with reason
4. Override the gate decision
"""

import sqlite3
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional


class ApprovalStatus(Enum):
    """Status of human approval."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class HumanApprovalRecord:
    """Single human approval record."""

    def __init__(
        self,
        gate_record_id: str,
        prompt_name: str,
        shadow_version: int,
        requested_by: Optional[str] = None,
        approval_reason: Optional[str] = None,
        status: str = ApprovalStatus.PENDING.value,
        created_at: Optional[datetime] = None,
    ):
        """Initialize human approval record.

        Args:
            gate_record_id: ID of the regression gate record
            prompt_name: Name of the prompt
            shadow_version: Version to deploy
            requested_by: User who requested approval
            approval_reason: Reason for approval request
            status: Approval status
            created_at: Creation timestamp
        """
        self.id = str(uuid.uuid4())
        self.gate_record_id = gate_record_id
        self.prompt_name = prompt_name
        self.shadow_version = shadow_version
        self.requested_by = requested_by
        self.approval_reason = approval_reason
        self.status = status
        self.approved_by: Optional[str] = None
        self.approved_at: Optional[datetime] = None
        self.created_at = created_at or datetime.now()

    def approve(self, approved_by: str, reason: Optional[str] = None) -> None:
        """Approve the record."""
        self.status = ApprovalStatus.APPROVED.value
        self.approved_by = approved_by
        self.approved_at = datetime.now()
        if reason:
            self.approval_reason = reason

    def reject(self, approved_by: str, reason: Optional[str] = None) -> None:
        """Reject the record."""
        self.status = ApprovalStatus.REJECTED.value
        self.approved_by = approved_by
        self.approved_at = datetime.now()
        if reason:
            self.approval_reason = reason

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "gate_record_id": self.gate_record_id,
            "prompt_name": self.prompt_name,
            "shadow_version": self.shadow_version,
            "requested_by": self.requested_by,
            "approval_reason": self.approval_reason,
            "status": self.status,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "created_at": self.created_at.isoformat(),
        }


class HumanApprovalGate:
    """Human approval gate for manual override."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize human approval gate.

        Args:
            db_path: SQLite database path (":memory:" for in-memory, or file path)
        """
        self.db_path = db_path
        self.approvals: list[HumanApprovalRecord] = []
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS human_approvals (
                id TEXT PRIMARY KEY,
                gate_record_id TEXT NOT NULL,
                prompt_name TEXT NOT NULL,
                shadow_version INTEGER NOT NULL,
                requested_by TEXT,
                approval_reason TEXT,
                status TEXT NOT NULL,
                approved_by TEXT,
                approved_at TEXT,
                created_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_approvals_gate ON human_approvals(gate_record_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_approvals_prompt ON human_approvals(prompt_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_approvals_status ON human_approvals(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_approvals_created ON human_approvals(created_at)
        """)
        self._conn.commit()

    def request_approval(
        self,
        gate_record_id: str,
        prompt_name: str,
        shadow_version: int,
        requested_by: Optional[str] = None,
        approval_reason: Optional[str] = None,
    ) -> HumanApprovalRecord:
        """Request human approval for a gate record.

        Args:
            gate_record_id: ID of the regression gate record
            prompt_name: Name of the prompt
            shadow_version: Version to deploy
            requested_by: User who requested approval
            approval_reason: Reason for approval request

        Returns:
            Approval record
        """
        record = HumanApprovalRecord(
            gate_record_id=gate_record_id,
            prompt_name=prompt_name,
            shadow_version=shadow_version,
            requested_by=requested_by,
            approval_reason=approval_reason,
        )
        self.approvals.append(record)
        self.save_record(record)
        return record

    def save_record(self, record: HumanApprovalRecord) -> None:
        """Save approval record to database."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO human_approvals
            (id, gate_record_id, prompt_name, shadow_version, requested_by, 
             approval_reason, status, approved_by, approved_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.gate_record_id,
                record.prompt_name,
                record.shadow_version,
                record.requested_by,
                record.approval_reason,
                record.status,
                record.approved_by,
                record.approved_at.isoformat() if record.approved_at else None,
                record.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def approve(
        self,
        record_id: str,
        approved_by: str,
        reason: Optional[str] = None,
    ) -> Optional[HumanApprovalRecord]:
        """Approve a record."""
        record = self.get_by_id(record_id)
        if record:
            record.approve(approved_by, reason)
            self.save_record(record)
        return record

    def reject(
        self,
        record_id: str,
        approved_by: str,
        reason: Optional[str] = None,
    ) -> Optional[HumanApprovalRecord]:
        """Reject a record."""
        record = self.get_by_id(record_id)
        if record:
            record.reject(approved_by, reason)
            self.save_record(record)
        return record

    def get_by_id(self, record_id: str) -> Optional[HumanApprovalRecord]:
        """Get approval record by ID."""
        for r in self.approvals:
            if r.id == record_id:
                return r
        return None

    def get_by_gate_record(self, gate_record_id: str) -> Optional[HumanApprovalRecord]:
        """Get approval record by gate record ID."""
        for r in self.approvals:
            if r.gate_record_id == gate_record_id:
                return r
        return None

    def get_by_prompt(self, prompt_name: str) -> list[HumanApprovalRecord]:
        """Get approval records by prompt name."""
        return [r for r in self.approvals if r.prompt_name == prompt_name]

    def get_pending(self) -> list[HumanApprovalRecord]:
        """Get pending approval records."""
        return [r for r in self.approvals if r.status == ApprovalStatus.PENDING.value]

    def get_approved(self) -> list[HumanApprovalRecord]:
        """Get approved records."""
        return [r for r in self.approvals if r.status == ApprovalStatus.APPROVED.value]

    def get_rejected(self) -> list[HumanApprovalRecord]:
        """Get rejected records."""
        return [r for r in self.approvals if r.status == ApprovalStatus.REJECTED.value]

    def get_statistics(self, prompt_name: Optional[str] = None) -> dict:
        """Get approval statistics.

        Args:
            prompt_name: Optional prompt name to filter

        Returns:
            Dictionary with statistics
        """
        approvals = self.approvals
        if prompt_name:
            approvals = self.get_by_prompt(prompt_name)

        total = len(approvals)
        if total == 0:
            return {
                "total": 0,
                "pending": 0,
                "approved": 0,
                "rejected": 0,
                "approval_rate": 0.0,
            }

        pending = len([r for r in approvals if r.status == ApprovalStatus.PENDING.value])
        approved = len([r for r in approvals if r.status == ApprovalStatus.APPROVED.value])
        rejected = len([r for r in approvals if r.status == ApprovalStatus.REJECTED.value])

        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "approval_rate": approved / total if total > 0 else 0.0,
        }

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
