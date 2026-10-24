"""Session Memory for PO Agent Platform v2.

Store short-lived state:
- current sprint
- current product
- selected member
- referenced task
- clarification state

Requirements:
- TTL or lifecycle
- explicit keys
- no automatic permanent promotion
"""

from datetime import datetime, timedelta
from typing import Optional


class SessionMemory:
    """Session memory with TTL support.

    Short-lived state for current conversation/session.
    """

    def __init__(self, ttl_seconds: int = 3600):
        """Initialize session memory.

        Args:
            ttl_seconds: Time-to-live in seconds (default 1 hour)
        """
        self.ttl_seconds = ttl_seconds
        self._data: dict[str, any] = {}
        self._timestamps: dict[str, datetime] = {}

    def set(self, key: str, value: any) -> None:
        """Set a value with current timestamp.

        Args:
            key: Key to store
            value: Value to store
        """
        self._data[key] = value
        self._timestamps[key] = datetime.now()

    def get(self, key: str) -> Optional[any]:
        """Get a value if not expired.

        Args:
            key: Key to retrieve

        Returns:
            Value or None if not found or expired
        """
        if key not in self._data:
            return None

        if key not in self._timestamps:
            return None

        # Check TTL
        elapsed = (datetime.now() - self._timestamps[key]).total_seconds()
        if elapsed > self.ttl_seconds:
            # Expired, remove
            self.delete(key)
            return None

        return self._data[key]

    def delete(self, key: str) -> bool:
        """Delete a key.

        Args:
            key: Key to delete

        Returns:
            True if key existed, False otherwise
        """
        if key in self._data:
            del self._data[key]
        if key in self._timestamps:
            del self._timestamps[key]
        return True

    def clear(self) -> None:
        """Clear all data."""
        self._data.clear()
        self._timestamps.clear()

    def keys(self) -> list[str]:
        """Get all keys (non-expired only)."""
        return [k for k in self._data.keys() if self.get(k) is not None]

    def has(self, key: str) -> bool:
        """Check if key exists and is not expired.

        Args:
            key: Key to check

        Returns:
            True if exists and not expired
        """
        return self.get(key) is not None

    def get_sprint(self) -> Optional[str]:
        """Get current sprint from session memory.

        Returns:
            Sprint ID or None
        """
        return self.get("current_sprint")

    def set_sprint(self, sprint_id: str) -> None:
        """Set current sprint.

        Args:
            sprint_id: Sprint ID
        """
        self.set("current_sprint", sprint_id)

    def get_product(self) -> Optional[str]:
        """Get current product from session memory.

        Returns:
            Product ID or None
        """
        return self.get("current_product")

    def set_product(self, product_id: str) -> None:
        """Set current product.

        Args:
            product_id: Product ID
        """
        self.set("current_product", product_id)

    def get_member(self) -> Optional[str]:
        """Get selected member from session memory.

        Returns:
            Member login or None
        """
        return self.get("selected_member")

    def set_member(self, member_login: str) -> None:
        """Set selected member.

        Args:
            member_login: Member login
        """
        self.set("selected_member", member_login)

    def get_referenced_task(self) -> Optional[str]:
        """Get referenced task from session memory.

        Returns:
            Task key or None
        """
        return self.get("referenced_task")

    def set_referenced_task(self, task_key: str) -> None:
        """Set referenced task.

        Args:
            task_key: Task key
        """
        self.set("referenced_task", task_key)

    def get_clarification_state(self) -> Optional[dict]:
        """Get clarification state from session memory.

        Returns:
            Clarification state dict or None
        """
        return self.get("clarification_state")

    def set_clarification_state(self, state: dict) -> None:
        """Set clarification state.

        Args:
            state: Clarification state dict
        """
        self.set("clarification_state", state)
