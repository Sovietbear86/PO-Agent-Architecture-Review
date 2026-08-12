"""Shadow Mode for PO Agent Platform v2.

Shadow Mode allows testing new prompt versions without affecting production:
1. Shadow config specifies which prompts to test
2. Shadow execution runs prod and shadow versions in parallel
3. Results are compared and logged
4. Automatic promotion based on comparison threshold
"""

import sqlite3
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional


class ShadowModeStatus(Enum):
    """Status of shadow mode configuration."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"


class ShadowModeEntry:
    """Single shadow mode configuration."""

    def __init__(
        self,
        prompt_name: str,
        shadow_version: int,
        comparison_threshold: float = 0.9,
        enabled: bool = True,
        created_by: Optional[str] = None,
        status: Optional[str] = None,
    ):
        """Initialize shadow mode configuration.

        Args:
            prompt_name: Name of the prompt to test
            shadow_version: Version to test in shadow mode
            comparison_threshold: Threshold for automatic promotion (0-1)
            enabled: Is shadow mode enabled
            created_by: User who created
            status: Shadow mode status
        """
        self.id = str(uuid.uuid4())
        self.prompt_name = prompt_name
        self.shadow_version = shadow_version
        self.comparison_threshold = comparison_threshold
        self.enabled = enabled
        self.created_by = created_by
        self.status = status or (ShadowModeStatus.ENABLED.value if enabled else ShadowModeStatus.DISABLED.value)
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def enable(self) -> None:
        """Enable shadow mode."""
        self.enabled = True
        self.status = ShadowModeStatus.ENABLED.value
        self.updated_at = datetime.now()

    def disable(self) -> None:
        """Disable shadow mode."""
        self.enabled = False
        self.status = ShadowModeStatus.DISABLED.value
        self.updated_at = datetime.now()

    def complete(self) -> None:
        """Mark shadow mode as completed."""
        self.status = ShadowModeStatus.COMPLETED.value
        self.updated_at = datetime.now()

    def rollback(self) -> None:
        """Rollback shadow mode."""
        self.status = ShadowModeStatus.ROLLED_BACK.value
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "prompt_name": self.prompt_name,
            "shadow_version": self.shadow_version,
            "comparison_threshold": self.comparison_threshold,
            "enabled": self.enabled,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ShadowModeStore:
    """Store for shadow mode configurations with SQLite persistence."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize shadow mode store.

        Args:
            db_path: SQLite database path (":memory:" for in-memory, or file path)
        """
        self.db_path = db_path
        self.configs: list[ShadowModeEntry] = []
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shadow_modes (
                id TEXT PRIMARY KEY,
                prompt_name TEXT NOT NULL,
                shadow_version INTEGER NOT NULL,
                comparison_threshold REAL NOT NULL,
                enabled INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_shadow_modes_prompt 
            ON shadow_modes(prompt_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_shadow_modes_status ON shadow_modes(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_shadow_modes_enabled ON shadow_modes(enabled)
        """)
        self._conn.commit()

    def add_config(
        self,
        prompt_name: str,
        shadow_version: int,
        comparison_threshold: float = 0.9,
        enabled: bool = True,
        created_by: Optional[str] = None,
    ) -> ShadowModeEntry:
        """Add a shadow mode configuration.

        Args:
            prompt_name: Name of the prompt to test
            shadow_version: Version to test in shadow mode
            comparison_threshold: Threshold for automatic promotion
            enabled: Is shadow mode enabled
            created_by: User who created

        Returns:
            Created shadow mode entry
        """
        entry = ShadowModeEntry(
            prompt_name=prompt_name,
            shadow_version=shadow_version,
            comparison_threshold=comparison_threshold,
            enabled=enabled,
            created_by=created_by,
        )
        self.configs.append(entry)
        self.save_config(entry)
        return entry

    def save_config(self, entry: ShadowModeEntry) -> None:
        """Save configuration to database."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO shadow_modes
            (id, prompt_name, shadow_version, comparison_threshold, enabled, status, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.id,
                entry.prompt_name,
                entry.shadow_version,
                entry.comparison_threshold,
                1 if entry.enabled else 0,
                entry.status,
                entry.created_by,
                entry.created_at.isoformat(),
                entry.updated_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get_by_prompt(self, prompt_name: str) -> Optional[ShadowModeEntry]:
        """Get shadow mode config by prompt name."""
        for c in self.configs:
            if c.prompt_name == prompt_name:
                return c
        return None

    def get_enabled(self) -> list[ShadowModeEntry]:
        """Get all enabled shadow mode configs."""
        return [c for c in self.configs if c.enabled]

    def get_by_status(self, status: str) -> list[ShadowModeEntry]:
        """Get configs by status."""
        return [c for c in self.configs if c.status == status]

    def enable_config(self, prompt_name: str, enabled_by: Optional[str] = None) -> Optional[ShadowModeEntry]:
        """Enable shadow mode for a prompt."""
        entry = self.get_by_prompt(prompt_name)
        if entry:
            entry.enable()
            entry.created_by = enabled_by or entry.created_by
            self.save_config(entry)
        return entry

    def disable_config(self, prompt_name: str) -> Optional[ShadowModeEntry]:
        """Disable shadow mode for a prompt."""
        entry = self.get_by_prompt(prompt_name)
        if entry:
            entry.disable()
            self.save_config(entry)
        return entry

    def complete_config(self, prompt_name: str) -> Optional[ShadowModeEntry]:
        """Mark shadow mode as completed."""
        entry = self.get_by_prompt(prompt_name)
        if entry:
            entry.complete()
            self.save_config(entry)
        return entry

    def rollback_config(self, prompt_name: str) -> Optional[ShadowModeEntry]:
        """Rollback shadow mode."""
        entry = self.get_by_prompt(prompt_name)
        if entry:
            entry.rollback()
            self.save_config(entry)
        return entry

    def get_all_configs(self) -> list[ShadowModeEntry]:
        """Get all shadow mode configurations."""
        return self.configs

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
