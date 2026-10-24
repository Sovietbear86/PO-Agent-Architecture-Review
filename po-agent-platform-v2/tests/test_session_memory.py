"""Tests for Session Memory."""

import time

import pytest

from po_agent.memory.session_memory import SessionMemory


@pytest.fixture
def memory():
    """Create session memory with short TTL for testing."""
    return SessionMemory(ttl_seconds=2)


class TestSessionMemoryBasic:
    """Tests for basic session memory operations."""

    def test_set_and_get(self, memory):
        """Test set and get operation."""
        memory.set("key1", "value1")
        assert memory.get("key1") == "value1"

    def test_get_nonexistent(self, memory):
        """Test getting non-existent key."""
        assert memory.get("nonexistent") is None

    def test_delete(self, memory):
        """Test delete operation."""
        memory.set("key1", "value1")
        assert memory.has("key1")
        memory.delete("key1")
        assert not memory.has("key1")

    def test_clear(self, memory):
        """Test clear operation."""
        memory.set("key1", "value1")
        memory.set("key2", "value2")
        memory.clear()
        assert not memory.has("key1")
        assert not memory.has("key2")

    def test_keys(self, memory):
        """Test keys method."""
        memory.set("key1", "value1")
        memory.set("key2", "value2")
        keys = memory.keys()
        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys


class TestSessionMemoryTTL:
    """Tests for TTL behavior."""

    def test_ttl_expiration(self, memory):
        """Test that entries expire after TTL."""
        memory.set("key1", "value1")
        assert memory.get("key1") == "value1"

        # Wait for TTL to expire
        time.sleep(3)

        assert memory.get("key1") is None

    def test_ttl_not_expired(self, memory):
        """Test that entries don't expire before TTL."""
        memory.set("key1", "value1")
        time.sleep(1)

        assert memory.get("key1") == "value1"


class TestSessionMemoryKeys:
    """Tests for session memory key-specific methods."""

    def test_sprint_lifecycle(self, memory):
        """Test sprint lifecycle methods."""
        memory.set_sprint("DMS-SPRNT-1")
        assert memory.get_sprint() == "DMS-SPRNT-1"

    def test_product_lifecycle(self, memory):
        """Test product lifecycle methods."""
        memory.set_product("DMS")
        assert memory.get_product() == "DMS"

    def test_member_lifecycle(self, memory):
        """Test member lifecycle methods."""
        memory.set_member("Ivanov.I.I")
        assert memory.get_member() == "Ivanov.I.I"

    def test_task_lifecycle(self, memory):
        """Test task lifecycle methods."""
        memory.set_referenced_task("WMB-123")
        assert memory.get_referenced_task() == "WMB-123"

    def test_clarification_lifecycle(self, memory):
        """Test clarification lifecycle methods."""
        state = {"question": "What?", "answer": "This"}
        memory.set_clarification_state(state)
        retrieved = memory.get_clarification_state()
        assert retrieved == state


class TestSessionMemoryHas:
    """Tests for has method."""

    def test_has_existing(self, memory):
        """Test has with existing key."""
        memory.set("key1", "value1")
        assert memory.has("key1")

    def test_has_nonexistent(self, memory):
        """Test has with non-existent key."""
        assert not memory.has("nonexistent")

    def test_has_expired(self, memory):
        """Test has with expired key."""
        memory.set("key1", "value1")
        time.sleep(3)
        assert not memory.has("key1")


class TestSessionMemoryEmpty:
    """Tests for empty state."""

    def test_empty_memory(self):
        """Test new memory is empty."""
        memory = SessionMemory()
        assert not memory.has("any_key")
        assert memory.keys() == []

    def test_empty_keys_after_clear(self, memory):
        """Test keys after clear."""
        memory.set("key1", "value1")
        memory.clear()
        assert memory.keys() == []
