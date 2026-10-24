"""Curated Memory for PO Agent Platform v2.

Create Curated Memory store.

Candidate entry fields:
- key, category, content
- evidence_trace_ids, source
- confidence, status
- created_at, approved_by, version

Statuses:
- candidate, approved, rejected, deprecated

Runtime may only use approved entries.
"""

import sqlite3
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional


class MemoryStatus(Enum):
    """Status of curated memory entry."""
    CANDIDATE = "candidate"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class MemoryCategory(Enum):
    """Category of curated memory."""
    TERMINOLOGY = "terminology"
    CONVENTION = "convention"
    ROUTING_EXCEPTION = "routing_exception"
    OPERATIONAL_PATTERN = "operational_pattern"
    ALIAS = "alias"
    KNOWLEDGE = "knowledge"


class CuratedMemoryEntry:
    """Single curated memory entry."""

    def __init__(
        self,
        key: str,
        category: str,
        content: str,
        evidence_trace_ids: Optional[list[str]] = None,
        source: Optional[str] = None,
        confidence: float = 0.0,
        status: str = MemoryStatus.CANDIDATE.value,
        approved_by: Optional[str] = None,
        version: int = 1,
    ):
        """Initialize curated memory entry.

        Args:
            key: Unique key for the entry
            category: Category of memory
            content: Memory content
            evidence_trace_ids: Traces supporting this memory
            source: Source of memory
            confidence: Confidence level (0-1)
            status: Entry status
            approved_by: User who approved
            version: Entry version
        """
        self.id = str(uuid.uuid4())
        self.key = key
        self.category = category
        self.content = content
        self.evidence_trace_ids = evidence_trace_ids or []
        self.source = source
        self.confidence = confidence
        self.status = status
        self.approved_by = approved_by
        self.version = version
        self.created_by: Optional[str] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def approve(self, approved_by: str) -> None:
        """Approve this entry.

        Args:
            approved_by: User who approved
        """
        self.status = MemoryStatus.APPROVED.value
        self.approved_by = approved_by
        self.approved_at = datetime.now()
        self.updated_at = datetime.now()

    def reject(self) -> None:
        """Reject this entry."""
        self.status = MemoryStatus.REJECTED.value
        self.updated_at = datetime.now()

    def deprecate(self) -> None:
        """Deprecate this entry."""
        self.status = MemoryStatus.DEPRECATED.value
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "key": self.key,
            "category": self.category,
            "content": self.content,
            "evidence_trace_ids": self.evidence_trace_ids,
            "source": self.source,
            "confidence": self.confidence,
            "status": self.status,
            "approved_by": self.approved_by,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class CuratedMemoryStore:
    """Store for curated memory entries with SQLite persistence."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize curated memory store.

        Args:
            db_path: SQLite database path (":memory:" for in-memory, or file path)
        """
        self.db_path = db_path
        self.entries: list[CuratedMemoryEntry] = []
        self._conn = sqlite3.connect(db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_entries (
                key TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                evidence_trace_ids TEXT,
                source TEXT,
                confidence REAL,
                status TEXT NOT NULL,
                created_by TEXT,
                approved_by TEXT,
                approved_at TEXT,
                version INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_status ON memory_entries(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_category ON memory_entries(category)
        """)
        self._conn.commit()

    def add_candidate(
        self,
        key: str,
        category: str,
        content: str,
        evidence_trace_ids: Optional[list[str]] = None,
        source: Optional[str] = None,
        confidence: float = 0.0,
    ) -> CuratedMemoryEntry:
        """Add a candidate memory entry.

        Args:
            key: Unique key for the entry
            category: Category of memory
            content: Memory content
            evidence_trace_ids: Traces supporting this memory
            source: Source of memory
            confidence: Confidence level (0-1)

        Returns:
            Created entry
        """
        entry = CuratedMemoryEntry(
            key=key,
            category=category,
            content=content,
            evidence_trace_ids=evidence_trace_ids or [],
            source=source,
            confidence=confidence,
        )
        self.entries.append(entry)
        self.save_entry(entry)
        return entry

    def save_entry(self, entry: CuratedMemoryEntry) -> None:
        """Save entry to database."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO memory_entries
            (key, category, content, evidence_trace_ids, source, confidence,
             status, created_by, approved_by, approved_at, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.key,
                entry.category,
                entry.content,
                str(entry.evidence_trace_ids) if entry.evidence_trace_ids else None,
                entry.source,
                entry.confidence,
                entry.status,
                entry.created_by,
                entry.approved_by,
                entry.approved_at.isoformat() if getattr(entry, 'approved_at', None) else None,
                entry.version,
                entry.created_at.isoformat(),
                entry.updated_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get_by_key(self, key: str) -> Optional[CuratedMemoryEntry]:
        """Get entry by key.

        Args:
            key: Entry key

        Returns:
            Entry or None
        """
        for entry in self.entries:
            if entry.key == key:
                return entry
        return None

    def get_approved_by_key(self, key: str) -> Optional[str]:
        """Get approved content by key.

        Args:
            key: Entry key

        Returns:
            Content or None if not approved
        """
        entry = self.get_by_key(key)
        if entry and entry.status == MemoryStatus.APPROVED.value:
            return entry.content
        return None

    def get_approved_entries(self) -> list[CuratedMemoryEntry]:
        """Get all approved entries.

        Returns:
            List of approved entries
        """
        return [
            e for e in self.entries
            if e.status == MemoryStatus.APPROVED.value
        ]

    def get_candidates(self) -> list[CuratedMemoryEntry]:
        """Get all candidate entries.

        Returns:
            List of candidate entries
        """
        return [
            e for e in self.entries
            if e.status == MemoryStatus.CANDIDATE.value
        ]

    def get_by_category(self, category: str) -> list[CuratedMemoryEntry]:
        """Get entries by category.

        Args:
            category: Category name

        Returns:
            List of entries
        """
        return [e for e in self.entries if e.category == category]

    def approve_entry(
        self,
        key: str,
        approved_by: str,
    ) -> Optional[CuratedMemoryEntry]:
        """Approve an entry.

        Args:
            key: Entry key
            approved_by: User who approved

        Returns:
            Updated entry or None
        """
        entry = self.get_by_key(key)
        if entry:
            entry.approve(approved_by)
            entry.version += 1
        return entry

    def reject_entry(self, key: str) -> Optional[CuratedMemoryEntry]:
        """Reject an entry.

        Args:
            key: Entry key

        Returns:
            Updated entry or None
        """
        entry = self.get_by_key(key)
        if entry:
            entry.reject()
        return entry

    def deprecate_entry(self, key: str) -> Optional[CuratedMemoryEntry]:
        """Deprecate an entry.

        Args:
            key: Entry key

        Returns:
            Updated entry or None
        """
        entry = self.get_by_key(key)
        if entry:
            entry.deprecate()
        return entry

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()