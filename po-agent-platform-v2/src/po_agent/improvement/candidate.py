"""Improvement Candidate Model for PO Agent Platform v2.

Support candidate types:
- prompt_change: prompt change
- router_rule: router rule
- alias_mapping: alias mapping
- knowledge_entry: knowledge entry
- golden_test: golden test
- capability_change: capability change
- config_change: config change

Candidate fields:
- reason: reason for candidate
- linked_failures: linked failure trace IDs
- expected_benefit: expected benefit
- affected_version: affected version
- risk: risk level
- proposed_diff: proposed diff or content
- status: candidate/approved/rejected

No auto-promotion.
"""

import sqlite3
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from po_agent.evaluation.failure import FailureStore, FailureCategory


class CandidateStatus(Enum):
    """Status of improvement candidate."""
    CANDIDATE = "candidate"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class CandidateType(Enum):
    """Type of improvement candidate."""
    PROMPT_CHANGE = "prompt_change"
    ROUTER_RULE = "router_rule"
    ALIAS_MAPPING = "alias_mapping"
    KNOWLEDGE_ENTRY = "knowledge_entry"
    GOLDEN_TEST = "golden_test"
    CAPABILITY_CHANGE = "capability_change"
    CONFIG_CHANGE = "config_change"


class ImprovementCandidate:
    """Single improvement candidate."""

    def __init__(
        self,
        candidate_type: str,
        reason: str,
        linked_failures: Optional[list[str]] = None,
        expected_benefit: Optional[str] = None,
        affected_version: Optional[str] = None,
        risk: Optional[str] = None,
        proposed_diff: Optional[str] = None,
        proposed_content: Optional[dict] = None,
        status: str = CandidateStatus.CANDIDATE.value,
        created_by: Optional[str] = None,
        version: int = 1,
    ):
        """Initialize improvement candidate.

        Args:
            candidate_type: Type of candidate
            reason: Reason for candidate
            linked_failures: Linked failure trace IDs
            expected_benefit: Expected benefit
            affected_version: Affected version
            risk: Risk level
            proposed_diff: Proposed diff
            proposed_content: Proposed content
            status: Candidate status
            created_by: User who created
            version: Candidate version
        """
        self.id = str(uuid.uuid4())
        self.candidate_type = candidate_type
        self.reason = reason
        self.linked_failures = linked_failures or []
        self.expected_benefit = expected_benefit
        self.affected_version = affected_version
        self.risk = risk
        self.proposed_diff = proposed_diff
        self.proposed_content = proposed_content or {}
        self.status = status
        self.created_by = created_by
        self.approved_by: Optional[str] = None
        self.version = version
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def approve(self, approved_by: str) -> None:
        """Approve this candidate."""
        self.status = CandidateStatus.APPROVED.value
        self.approved_by = approved_by
        self.updated_at = datetime.now()
        self.version += 1

    def reject(self) -> None:
        """Reject this candidate."""
        self.status = CandidateStatus.REJECTED.value
        self.updated_at = datetime.now()

    def deprecate(self) -> None:
        """Deprecate this candidate."""
        self.status = CandidateStatus.DEPRECATED.value
        self.updated_at = datetime.now()
        self.version += 1

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "candidate_type": self.candidate_type,
            "reason": self.reason,
            "linked_failures": self.linked_failures,
            "expected_benefit": self.expected_benefit,
            "affected_version": self.affected_version,
            "risk": self.risk,
            "proposed_diff": self.proposed_diff,
            "proposed_content": self.proposed_content,
            "status": self.status,
            "created_by": self.created_by,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ImprovementCandidateStore:
    """Store for improvement candidates with SQLite persistence."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize candidate store.

        Args:
            db_path: SQLite database path (":memory:" for in-memory, or file path)
        """
        self.db_path = db_path
        self.candidates: list[ImprovementCandidate] = []
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id TEXT PRIMARY KEY,
                candidate_type TEXT NOT NULL,
                reason TEXT NOT NULL,
                linked_failures TEXT,
                expected_benefit TEXT,
                affected_version TEXT,
                risk TEXT,
                proposed_diff TEXT,
                proposed_content TEXT,
                status TEXT NOT NULL,
                created_by TEXT,
                approved_by TEXT,
                version INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_candidates_type ON candidates(candidate_type)
        """)
        self._conn.commit()

    def add_candidate(
        self,
        candidate_type: str,
        reason: str,
        linked_failures: Optional[list[str]] = None,
        expected_benefit: Optional[str] = None,
        affected_version: Optional[str] = None,
        risk: Optional[str] = None,
        proposed_diff: Optional[str] = None,
        proposed_content: Optional[dict] = None,
        created_by: Optional[str] = None,
    ) -> ImprovementCandidate:
        """Add a candidate.

        Args:
            candidate_type: Type of candidate
            reason: Reason for candidate
            linked_failures: Linked failure trace IDs
            expected_benefit: Expected benefit
            affected_version: Affected version
            risk: Risk level
            proposed_diff: Proposed diff
            proposed_content: Proposed content
            created_by: User who created

        Returns:
            Created candidate
        """
        candidate = ImprovementCandidate(
            candidate_type=candidate_type,
            reason=reason,
            linked_failures=linked_failures or [],
            expected_benefit=expected_benefit,
            affected_version=affected_version,
            risk=risk,
            proposed_diff=proposed_diff,
            proposed_content=proposed_content or {},
            created_by=created_by,
        )
        self.candidates.append(candidate)
        self.save_candidate(candidate)
        return candidate

    def save_candidate(self, candidate: ImprovementCandidate) -> None:
        """Save candidate to database."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO candidates
            (id, candidate_type, reason, linked_failures, expected_benefit,
             affected_version, risk, proposed_diff, proposed_content,
             status, created_by, approved_by, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate.id,
                candidate.candidate_type,
                candidate.reason,
                str(candidate.linked_failures) if candidate.linked_failures else None,
                candidate.expected_benefit,
                candidate.affected_version,
                candidate.risk,
                candidate.proposed_diff,
                str(candidate.proposed_content) if candidate.proposed_content else None,
                candidate.status,
                candidate.created_by,
                candidate.approved_by,
                candidate.version,
                candidate.created_at.isoformat(),
                candidate.updated_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get_by_id(self, candidate_id: str) -> Optional[ImprovementCandidate]:
        """Get candidate by ID."""
        for c in self.candidates:
            if c.id == candidate_id:
                return c
        return None

    def get_by_status(self, status: str) -> list[ImprovementCandidate]:
        """Get candidates by status."""
        return [c for c in self.candidates if c.status == status]

    def get_candidates(self) -> list[ImprovementCandidate]:
        """Get all candidates (not approved/rejected)."""
        return [
            c for c in self.candidates
            if c.status in [CandidateStatus.CANDIDATE.value, CandidateStatus.DEPRECATED.value]
        ]

    def get_approved(self) -> list[ImprovementCandidate]:
        """Get all approved candidates."""
        return [
            c for c in self.candidates
            if c.status == CandidateStatus.APPROVED.value
        ]

    def approve_candidate(
        self,
        candidate_id: str,
        approved_by: str,
    ) -> Optional[ImprovementCandidate]:
        """Approve a candidate."""
        candidate = self.get_by_id(candidate_id)
        if candidate:
            candidate.approve(approved_by)
            self.save_candidate(candidate)
        return candidate

    def reject_candidate(self, candidate_id: str) -> Optional[ImprovementCandidate]:
        """Reject a candidate."""
        candidate = self.get_by_id(candidate_id)
        if candidate:
            candidate.reject()
            self.save_candidate(candidate)
        return candidate

    def create_prompt_change_candidate(
        self,
        prompt_name: str,
        reason: str,
        linked_failures: list[str],
        proposed_diff: str,
        created_by: Optional[str] = None,
    ) -> ImprovementCandidate:
        """Create prompt change candidate."""
        return self.add_candidate(
            candidate_type=CandidateType.PROMPT_CHANGE.value,
            reason=reason,
            linked_failures=linked_failures,
            expected_benefit=f"Improve {prompt_name} prompt",
            proposed_diff=proposed_diff,
            created_by=created_by,
        )

    def create_router_rule_candidate(
        self,
        intent: str,
        reason: str,
        linked_failures: list[str],
        proposed_rule: dict,
        created_by: Optional[str] = None,
    ) -> ImprovementCandidate:
        """Create router rule candidate."""
        return self.add_candidate(
            candidate_type=CandidateType.ROUTER_RULE.value,
            reason=reason,
            linked_failures=linked_failures,
            expected_benefit=f"Add routing rule for {intent}",
            proposed_diff=str(proposed_rule),
            created_by=created_by,
        )

    def create_knowledge_entry_candidate(
        self,
        key: str,
        category: str,
        content: str,
        reason: str,
        linked_failures: list[str],
        created_by: Optional[str] = None,
    ) -> ImprovementCandidate:
        """Create knowledge entry candidate."""
        return self.add_candidate(
            candidate_type=CandidateType.KNOWLEDGE_ENTRY.value,
            reason=reason,
            linked_failures=linked_failures,
            expected_benefit=f"Add knowledge entry {key}",
            proposed_content={
                "key": key,
                "category": category,
                "content": content,
            },
            created_by=created_by,
        )

    def create_golden_test_candidate(
        self,
        test_name: str,
        reason: str,
        linked_failures: list[str],
        test_code: str,
        created_by: Optional[str] = None,
    ) -> ImprovementCandidate:
        """Create golden test candidate."""
        return self.add_candidate(
            candidate_type=CandidateType.GOLDEN_TEST.value,
            reason=reason,
            linked_failures=linked_failures,
            expected_benefit=f"Add golden test {test_name}",
            proposed_diff=test_code,
            created_by=created_by,
        )

    def create_capability_change_candidate(
        self,
        capability_name: str,
        reason: str,
        linked_failures: list[str],
        proposed_changes: dict,
        created_by: Optional[str] = None,
    ) -> ImprovementCandidate:
        """Create capability change candidate."""
        return self.add_candidate(
            candidate_type=CandidateType.CAPABILITY_CHANGE.value,
            reason=reason,
            linked_failures=linked_failures,
            expected_benefit=f"Change {capability_name} capability",
            proposed_content=proposed_changes,
            created_by=created_by,
        )

    def create_config_change_candidate(
        self,
        config_name: str,
        reason: str,
        linked_failures: list[str],
        proposed_changes: dict,
        created_by: Optional[str] = None,
    ) -> ImprovementCandidate:
        """Create config change candidate."""
        return self.add_candidate(
            candidate_type=CandidateType.CONFIG_CHANGE.value,
            reason=reason,
            linked_failures=linked_failures,
            expected_benefit=f"Change {config_name} config",
            proposed_content=proposed_changes,
            created_by=created_by,
        )
    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()

