"""Prompt Registry for PO Agent Platform v2.

Version prompts.

Prompt metadata:
- prompt_name: prompt name
- version: version
- content/path: content or path to prompt
- schema: schema for structured output validation
- model_compatibility: compatible models
- created_at: creation timestamp
- status: candidate/active/deprecated

Runtime logs active prompt version.
"""

import sqlite3
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional


class PromptStatus(Enum):
    """Status of prompt."""
    CANDIDATE = "candidate"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class PromptEntry:
    """Single prompt entry."""

    def __init__(
        self,
        prompt_name: str,
        version: int,
        content: Optional[str] = None,
        schema: Optional[dict] = None,
        model_compatibility: Optional[list[str]] = None,
        status: str = PromptStatus.CANDIDATE.value,
        created_by: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        """Initialize prompt entry.

        Args:
            prompt_name: Name of the prompt
            version: Prompt version
            content: Prompt content (or path)
            schema: JSON schema for structured output
            model_compatibility: List of compatible models
            status: Prompt status
            created_by: User who created
            created_at: Creation timestamp
        """
        self.id = str(uuid.uuid4())
        self.prompt_name = prompt_name
        self.version = version
        self.content = content
        self.schema = schema or {}
        self.model_compatibility = model_compatibility or []
        self.status = status
        self.created_by = created_by
        self.created_at = created_at or datetime.now()
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Activate this prompt."""
        self.status = PromptStatus.ACTIVE.value
        self.updated_at = datetime.now()

    def deprecate(self) -> None:
        """Deprecate this prompt."""
        self.status = PromptStatus.DEPRECATED.value
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "prompt_name": self.prompt_name,
            "version": self.version,
            "content": self.content,
            "schema": self.schema,
            "model_compatibility": self.model_compatibility,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class PromptRegistry:
    """Registry for prompt versions."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize prompt registry.

        Args:
            db_path: SQLite database path (":memory:" for in-memory, or file path)
        """
        self.db_path = db_path
        self.prompts: list[PromptEntry] = []
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def add_prompt(
        self,
        prompt_name: str,
        version: int,
        content: Optional[str] = None,
        schema: Optional[dict] = None,
        model_compatibility: Optional[list[str]] = None,
        created_by: Optional[str] = None,
    ) -> PromptEntry:
        """Add a prompt version.

        Args:
            prompt_name: Name of the prompt
            version: Prompt version
            content: Prompt content
            schema: JSON schema for validation
            model_compatibility: Compatible models
            created_by: User who created

        Returns:
            Created prompt entry
        """
        entry = PromptEntry(
            prompt_name=prompt_name,
            version=version,
            content=content,
            schema=schema or {},
            model_compatibility=model_compatibility or [],
            created_by=created_by,
        )
        self.prompts.append(entry)
        self.save_prompt(entry)
        return entry

    def get_by_name(self, prompt_name: str) -> list[PromptEntry]:
        """Get all versions of a prompt by name."""
        return [p for p in self.prompts if p.prompt_name == prompt_name]

    def get_active(self, prompt_name: str) -> Optional[PromptEntry]:
        """Get active version of a prompt."""
        versions = self.get_by_name(prompt_name)
        active = [p for p in versions if p.status == PromptStatus.ACTIVE.value]
        return active[0] if active else None

    def get_all_active(self) -> list[PromptEntry]:
        """Get all active prompts."""
        return [p for p in self.prompts if p.status == PromptStatus.ACTIVE.value]

    def get_candidates(self) -> list[PromptEntry]:
        """Get all candidate prompts."""
        return [p for p in self.prompts if p.status == PromptStatus.CANDIDATE.value]

    def activate_prompt(
        self,
        prompt_name: str,
        version: int,
        activated_by: Optional[str] = None,
    ) -> Optional[PromptEntry]:
        """Activate a specific prompt version.

        Args:
            prompt_name: Name of the prompt
            version: Version to activate
            activated_by: User who activated

        Returns:
            Activated prompt entry
        """
        entry = self.get_by_name_version(prompt_name, version)
        if entry:
            # Deactivate other versions first
            for p in self.prompts:
                if p.prompt_name == prompt_name:
                    p.status = PromptStatus.DEPRECATED.value
                    self.save_prompt(p)

            entry.activate()
            entry.created_by = activated_by or entry.created_by
            self.save_prompt(entry)
        return entry

    def get_by_name_version(
        self,
        prompt_name: str,
        version: int,
    ) -> Optional[PromptEntry]:
        """Get prompt by name and version."""
        for p in self.prompts:
            if p.prompt_name == prompt_name and p.version == version:
                return p
        return None

    def deactivate_prompt(self, prompt_name: str, version: int) -> Optional[PromptEntry]:
        """Deactivate a prompt (alias for deprecate)."""
        return self.deprecate_prompt(prompt_name, version)

    def deprecate_prompt(self, prompt_name: str, version: int) -> Optional[PromptEntry]:
        """Deprecate a prompt."""
        entry = self.get_by_name_version(prompt_name, version)
        if entry:
            entry.deprecate()
            self.save_prompt(entry)
        return entry

    def _init_schema(self) -> None:
        """Initialize database schema."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id TEXT PRIMARY KEY,
                prompt_name TEXT NOT NULL,
                version INTEGER NOT NULL,
                content TEXT,
                schema TEXT,
                model_compatibility TEXT,
                status TEXT NOT NULL,
                created_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_prompts_name_version 
            ON prompts(prompt_name, version)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prompts_status ON prompts(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prompts_name ON prompts(prompt_name)
        """)
        self._conn.commit()

    def save_prompt(self, entry: PromptEntry) -> None:
        """Save prompt entry to database."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO prompts
            (id, prompt_name, version, content, schema, model_compatibility, 
             status, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.id,
                entry.prompt_name,
                entry.version,
                entry.content,
                str(entry.schema) if entry.schema else None,
                str(entry.model_compatibility) if entry.model_compatibility else None,
                entry.status,
                entry.created_by,
                entry.created_at.isoformat(),
                entry.updated_at.isoformat(),
            ),
        )
        self._conn.commit()

    def load_prompts(self) -> None:
        """Load prompts from database."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM prompts")
        rows = cursor.fetchall()
        self.prompts = []
        for row in rows:
            entry = PromptEntry(
                prompt_name=row[1],
                version=row[2],
                content=row[3],
                schema=eval(row[4]) if row[4] else {},
                model_compatibility=eval(row[5]) if row[5] else [],
                status=row[6],
                created_by=row[7],
                created_at=datetime.fromisoformat(row[8]),
            )
            entry.id = row[0]
            entry.updated_at = datetime.fromisoformat(row[9])
            self.prompts.append(entry)

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()

    def get_prompt_history(self, prompt_name: str) -> list[PromptEntry]:
        """Get history of a prompt."""
        return sorted(
            self.get_by_name(prompt_name),
            key=lambda p: p.version,
            reverse=True,
        )

    def get_active_version(self, prompt_name: str) -> Optional[int]:
        """Get active version number."""
        active = self.get_active(prompt_name)
        return active.version if active else None
