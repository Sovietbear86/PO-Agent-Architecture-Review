"""Action Contracts for PO Agent Platform v2.

Action contracts for controlled self-improvement:
- ActionProposal: Propose an action (create, update, delete)
- ActionConfirmation: Confirm an action proposal
- ActionResult: Result of action execution
- AuditRecord: Audit trail for all actions

No real writes yet - just models.
"""

import sqlite3
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class ActionStatus(Enum):
    """Status of an action."""
    PROPOSAL = "proposal"
    CONFIRMED = "confirmed"
    EXECUTED = "executed"
    REJECTED = "rejected"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ActionType(Enum):
    """Type of action."""
    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    DELETE_TASK = "delete_task"
    CREATE_PROMOTION = "create_promotion"
    CREATE_ROLLBACK = "create_rollback"
    CREATE_SHADOW_CONFIG = "create_shadow_config"
    PROMPT_CHANGE = "prompt_change"
    ROUTER_RULE_CHANGE = "router_rule_change"
    CONFIG_CHANGE = "config_change"


class ActionProposal:
    """Proposal for an action."""

    def __init__(
        self,
        action_type: str,
        target: str,
        details: Dict[str, Any],
        requested_by: Optional[str] = None,
        status: str = ActionStatus.PROPOSAL.value,
        created_at: Optional[datetime] = None,
    ):
        """Initialize action proposal.

        Args:
            action_type: Type of action (create_task, update_task, etc.)
            target: Target of the action
            details: Action details
            requested_by: User who requested
            status: Action status
            created_at: Creation timestamp
        """
        self.id = str(uuid.uuid4())
        self.action_type = action_type
        self.target = target
        self.details = details
        self.requested_by = requested_by
        self.status = status
        self.created_at = created_at or datetime.now()
        self.confirmed_by: Optional[str] = None
        self.confirmed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None

    def confirm(self, confirmed_by: str, reason: Optional[str] = None) -> None:
        """Confirm the proposal."""
        self.status = ActionStatus.CONFIRMED.value
        self.confirmed_by = confirmed_by
        self.confirmed_at = datetime.now()
        if reason:
            self.details["confirmation_reason"] = reason

    def reject(self, confirmed_by: str, reason: str) -> None:
        """Reject the proposal."""
        self.status = ActionStatus.REJECTED.value
        self.confirmed_by = confirmed_by
        self.confirmed_at = datetime.now()
        self.details["rejection_reason"] = reason

    def execute(self, success: bool, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
        """Mark action as executed."""
        self.status = ActionStatus.EXECUTED.value if success else ActionStatus.FAILED.value
        self.result = result
        self.error = error

    def rollback(self, reason: str) -> None:
        """Mark action as rolled back."""
        self.status = ActionStatus.ROLLED_BACK.value
        self.details["rollback_reason"] = reason

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "action_type": self.action_type,
            "target": self.target,
            "details": self.details,
            "requested_by": self.requested_by,
            "status": self.status,
            "confirmed_by": self.confirmed_by,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "created_at": self.created_at.isoformat(),
            "result": self.result,
            "error": self.error,
        }


class AuditRecord:
    """Audit record for action execution."""

    def __init__(
        self,
        action_id: str,
        user_id: str,
        action_type: str,
        timestamp: Optional[datetime] = None,
        status: str = "pending",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize audit record.

        Args:
            action_id: ID of the action
            user_id: User who performed the action
            action_type: Type of action
            timestamp: Timestamp
            status: Status of the action
            details: Additional details
        """
        self.id = str(uuid.uuid4())
        self.action_id = action_id
        self.user_id = user_id
        self.action_type = action_type
        self.timestamp = timestamp or datetime.now()
        self.status = status
        self.details = details or {}

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "action_id": self.action_id,
            "user_id": self.user_id,
            "action_type": self.action_type,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "details": self.details,
        }


class ActionManager:
    """Manager for action proposals and execution."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize action manager.

        Args:
            db_path: SQLite database path
        """
        self.db_path = db_path
        self.proposals: list[ActionProposal] = []
        self.audit_records: list[AuditRecord] = []
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_proposals (
                id TEXT PRIMARY KEY,
                action_type TEXT NOT NULL,
                target TEXT NOT NULL,
                details TEXT NOT NULL,
                requested_by TEXT,
                status TEXT NOT NULL,
                confirmed_by TEXT,
                confirmed_at TEXT,
                created_at TEXT NOT NULL,
                result TEXT,
                error TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_records (
                id TEXT PRIMARY KEY,
                action_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_proposals_status ON action_proposals(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_proposals_type ON action_proposals(action_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_records(action_id)
        """)
        self._conn.commit()

    def create_proposal(
        self,
        action_type: str,
        target: str,
        details: Dict[str, Any],
        requested_by: Optional[str] = None,
    ) -> ActionProposal:
        """Create a new action proposal.

        Args:
            action_type: Type of action
            target: Target of the action
            details: Action details
            requested_by: User who requested

        Returns:
            ActionProposal object
        """
        proposal = ActionProposal(
            action_type=action_type,
            target=target,
            details=details,
            requested_by=requested_by,
        )
        self.proposals.append(proposal)
        self.save_proposal(proposal)
        self.log_audit(
            action_id=proposal.id,
            user_id=requested_by or "unknown",
            action_type=action_type,
            status="proposed",
        )
        return proposal

    def save_proposal(self, proposal: ActionProposal) -> None:
        """Save proposal to database."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO action_proposals
            (id, action_type, target, details, requested_by, status,
             confirmed_by, confirmed_at, created_at, result, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal.id,
                proposal.action_type,
                proposal.target,
                str(proposal.details),
                proposal.requested_by,
                proposal.status,
                proposal.confirmed_by,
                proposal.confirmed_at.isoformat() if proposal.confirmed_at else None,
                proposal.created_at.isoformat(),
                str(proposal.result) if proposal.result else None,
                proposal.error,
            ),
        )
        self._conn.commit()

    def log_audit(
        self,
        action_id: str,
        user_id: str,
        action_type: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditRecord:
        """Log an audit record.

        Args:
            action_id: ID of the action
            user_id: User who performed the action
            action_type: Type of action
            status: Status of the action
            details: Additional details

        Returns:
            AuditRecord object
        """
        record = AuditRecord(
            action_id=action_id,
            user_id=user_id,
            action_type=action_type,
            status=status,
            details=details,
        )
        self.audit_records.append(record)
        self.save_audit(record)
        return record

    def save_audit(self, record: AuditRecord) -> None:
        """Save audit record to database."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO audit_records
            (id, action_id, user_id, action_type, timestamp, status, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.action_id,
                record.user_id,
                record.action_type,
                record.timestamp.isoformat(),
                record.status,
                str(record.details),
            ),
        )
        self._conn.commit()

    def get_proposal(self, proposal_id: str) -> Optional[ActionProposal]:
        """Get proposal by ID."""
        for p in self.proposals:
            if p.id == proposal_id:
                return p
        return None

    def get_proposals_by_status(self, status: str) -> list[ActionProposal]:
        """Get proposals by status."""
        return [p for p in self.proposals if p.status == status]

    def get_proposals_by_type(self, action_type: str) -> list[ActionProposal]:
        """Get proposals by type."""
        return [p for p in self.proposals if p.action_type == action_type]

    def get_audit_records(self, action_id: Optional[str] = None) -> list[AuditRecord]:
        """Get audit records."""
        if action_id:
            return [r for r in self.audit_records if r.action_id == action_id]
        return self.audit_records

    def get_statistics(self) -> dict:
        """Get action statistics."""
        total = len(self.proposals)
        if total == 0:
            return {
                "total": 0,
                "proposed": 0,
                "confirmed": 0,
                "executed": 0,
                "rejected": 0,
                "failed": 0,
                "rolled_back": 0,
            }

        by_status = {}
        for p in self.proposals:
            by_status[p.status] = by_status.get(p.status, 0) + 1

        return {
            "total": total,
            **by_status,
        }

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
