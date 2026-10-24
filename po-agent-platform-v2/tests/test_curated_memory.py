"""Tests for Curated Memory."""

import pytest

from po_agent.knowledge.curated_memory import (
    CuratedMemoryEntry,
    CuratedMemoryStore,
    MemoryStatus,
    MemoryCategory,
)


@pytest.fixture
def store():
    """Create curated memory store."""
    s = CuratedMemoryStore(db_path=':memory:')
    yield s
    s.close()


class TestCuratedMemoryEntry:
    """Tests for CuratedMemoryEntry."""

    def test_entry_creation(self, store: CuratedMemoryStore):
        """Test entry creation."""
        entry = CuratedMemoryEntry(
            key="terminology:spint",
            category=MemoryCategory.TERMINOLOGY.value,
            content="Sprint is a time-boxed period for development",
        )

        assert entry.id is not None
        assert entry.key == "terminology:spint"
        assert entry.status == MemoryStatus.CANDIDATE.value

    def test_approve_entry(self, store: CuratedMemoryStore):
        """Test approving an entry."""
        entry = CuratedMemoryEntry(
            key="test_key",
            category="test",
            content="test content",
        )

        entry.approve("admin")

        assert entry.status == MemoryStatus.APPROVED.value
        assert entry.approved_by == "admin"
        assert entry.version >= 1  # Version starts at 1

    def test_reject_entry(self, store: CuratedMemoryStore):
        """Test rejecting an entry."""
        entry = CuratedMemoryEntry(
            key="test_key",
            category="test",
            content="test content",
        )

        entry.reject()

        assert entry.status == MemoryStatus.REJECTED.value

    def test_deprecate_entry(self, store: CuratedMemoryStore):
        """Test deprecating an entry."""
        entry = CuratedMemoryEntry(
            key="test_key",
            category="test",
            content="test content",
        )

        entry.deprecate()

        assert entry.status == MemoryStatus.DEPRECATED.value

    def test_to_dict(self, store: CuratedMemoryStore):
        """Test conversion to dictionary."""
        entry = CuratedMemoryEntry(
            key="test_key",
            category="test",
            content="test content",
            evidence_trace_ids=["trace-1"],
            source="manual",
        )

        d = entry.to_dict()

        assert d["key"] == "test_key"
        assert d["category"] == "test"
        assert d["content"] == "test content"
        assert d["evidence_trace_ids"] == ["trace-1"]
        assert d["source"] == "manual"


class TestCuratedMemoryStore:
    """Tests for CuratedMemoryStore."""

    def test_add_candidate(self, store: CuratedMemoryStore):
        """Test adding a candidate entry."""
        entry = store.add_candidate(
            key="terminology:sprint",
            category=MemoryCategory.TERMINOLOGY.value,
            content="Sprint is a time-boxed period for development",
        )

        assert entry.status == MemoryStatus.CANDIDATE.value
        assert len(store.entries) == 1

    def test_get_by_key(self, store: CuratedMemoryStore):
        """Test getting entry by key."""
        store.add_candidate(
            key="terminology:sprint",
            category=MemoryCategory.TERMINOLOGY.value,
            content="Sprint content",
        )

        entry = store.get_by_key("terminology:sprint")
        assert entry is not None
        assert entry.content == "Sprint content"

    def test_get_approved_by_key(self, store: CuratedMemoryStore):
        """Test getting approved content by key."""
        store.add_candidate(
            key="terminology:sprint",
            category=MemoryCategory.TERMINOLOGY.value,
            content="Sprint content",
        )

        # Not approved yet
        assert store.get_approved_by_key("terminology:sprint") is None

        # Approve it
        entry = store.get_by_key("terminology:sprint")
        entry.approve("admin")

        # Now should return content
        assert store.get_approved_by_key("terminology:sprint") == "Sprint content"

    def test_get_approved_entries(self, store: CuratedMemoryStore):
        """Test getting approved entries."""
        for i in range(3):
            entry = store.add_candidate(
                key=f"test_{i}",
                category="test",
                content=f"content {i}",
            )
            entry.approve("admin")

        # Add a candidate that's not approved
        store.add_candidate(
            key="candidate_only",
            category="test",
            content="not approved",
        )

        approved = store.get_approved_entries()
        assert len(approved) == 3

    def test_get_candidates(self, store: CuratedMemoryStore):
        """Test getting candidate entries."""
        # Add approved entries
        for i in range(2):
            entry = store.add_candidate(
                key=f"approved_{i}",
                category="test",
                content=f"content {i}",
            )
            entry.approve("admin")

        # Add candidates
        for i in range(3):
            store.add_candidate(
                key=f"candidate_{i}",
                category="test",
                content=f"content {i}",
            )

        candidates = store.get_candidates()
        assert len(candidates) == 3

    def test_approve_entry(self, store: CuratedMemoryStore):
        """Test approving an entry."""
        store.add_candidate(
            key="test_key",
            category="test",
            content="test content",
        )

        result = store.approve_entry("test_key", "admin")

        assert result is not None
        assert result.status == MemoryStatus.APPROVED.value
        assert result.approved_by == "admin"

    def test_reject_entry(self, store: CuratedMemoryStore):
        """Test rejecting an entry."""
        store.add_candidate(
            key="test_key",
            category="test",
            content="test content",
        )

        result = store.reject_entry("test_key")

        assert result is not None
        assert result.status == MemoryStatus.REJECTED.value

    def test_deprecate_entry(self, store: CuratedMemoryStore):
        """Test deprecating an entry."""
        store.add_candidate(
            key="test_key",
            category="test",
            content="test content",
        )

        result = store.deprecate_entry("test_key")

        assert result is not None
        assert result.status == MemoryStatus.DEPRECATED.value

    def test_get_by_category(self, store: CuratedMemoryStore):
        """Test getting entries by category."""
        for i in range(3):
            store.add_candidate(
                key=f"term_{i}",
                category=MemoryCategory.TERMINOLOGY.value,
                content=f"content {i}",
            )

        for i in range(2):
            store.add_candidate(
                key=f"alias_{i}",
                category=MemoryCategory.ALIAS.value,
                content=f"content {i}",
            )

        terminology = store.get_by_category(MemoryCategory.TERMINOLOGY.value)
        assert len(terminology) == 3

        aliases = store.get_by_category(MemoryCategory.ALIAS.value)
        assert len(aliases) == 2


class TestCuratedMemoryIntegration:
    """Integration tests for curated memory."""

    def test_full_memory_lifecycle(self, store: CuratedMemoryStore):
        """Test full memory lifecycle."""
        # 1. Add candidate
        entry = store.add_candidate(
            key="terminology:sprint",
            category=MemoryCategory.TERMINOLOGY.value,
            content="Sprint is a time-boxed period",
            evidence_trace_ids=["trace-1", "trace-2"],
            source="trace_analysis",
            confidence=0.9,
        )

        # 2. Verify it's a candidate
        assert store.get_approved_by_key("terminology:sprint") is None

        # 3. Approve it
        store.approve_entry("terminology:sprint", "admin")

        # 4. Verify it's approved
        approved_content = store.get_approved_by_key("terminology:sprint")
        assert approved_content == "Sprint is a time-boxed period"

        # 5. Use it in runtime
        memory_entries = store.get_approved_entries()
        assert len(memory_entries) == 1
        assert memory_entries[0].key == "terminology:sprint"
