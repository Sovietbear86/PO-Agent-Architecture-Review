"""Version Registry for PO Agent Platform v2.

Track all component versions:
- prompt: prompt versions
- capability: capability versions
- config: config versions
- model: LLM model versions
- schema: schema versions

Version fields:
- component_type: type of component
- component_name: component name
- version: version number
- released_at: release date
- status: active/deprecated
- release_notes: release notes
- breaking_changes: breaking changes flag
- supported_until: support end date
"""

import sqlite3
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional


class VersionStatus(Enum):
    """Status of version."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    END_OF_LIFE = "end_of_life"


class VersionEntry:
    """Single version entry."""

    def __init__(
        self,
        component_type: str,
        component_name: str,
        version: int,
        released_at: Optional[datetime] = None,
        status: str = VersionStatus.ACTIVE.value,
        release_notes: Optional[str] = None,
        breaking_changes: bool = False,
        supported_until: Optional[datetime] = None,
        created_by: Optional[str] = None,
    ):
        """Initialize version entry.

        Args:
            component_type: Type of component
            component_name: Component name
            version: Version number
            released_at: Release date
            status: Version status
            release_notes: Release notes
            breaking_changes: Breaking changes flag
            supported_until: Support end date
            created_by: User who created
        """
        self.id = str(uuid.uuid4())
        self.component_type = component_type
        self.component_name = component_name
        self.version = version
        self.released_at = released_at or datetime.now()
        self.status = status
        self.release_notes = release_notes
        self.breaking_changes = breaking_changes
        self.supported_until = supported_until
        self.created_by = created_by
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Activate this version."""
        self.status = VersionStatus.ACTIVE.value
        self.updated_at = datetime.now()

    def deprecate(self) -> None:
        """Deprecate this version."""
        self.status = VersionStatus.DEPRECATED.value
        self.updated_at = datetime.now()

    def end_of_life(self) -> None:
        """Set version to end of life."""
        self.status = VersionStatus.END_OF_LIFE.value
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "component_type": self.component_type,
            "component_name": self.component_name,
            "version": self.version,
            "released_at": self.released_at.isoformat() if self.released_at else None,
            "status": self.status,
            "release_notes": self.release_notes,
            "breaking_changes": self.breaking_changes,
            "supported_until": self.supported_until.isoformat() if self.supported_until else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class VersionRegistry:
    """Registry for component versions with SQLite persistence."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize version registry.

        Args:
            db_path: SQLite database path (":memory:" for in-memory, or file path)
        """
        self.db_path = db_path
        self.versions: list[VersionEntry] = []
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS versions (
                id TEXT PRIMARY KEY,
                component_type TEXT NOT NULL,
                component_name TEXT NOT NULL,
                version INTEGER NOT NULL,
                released_at TEXT,
                status TEXT NOT NULL,
                release_notes TEXT,
                breaking_changes INTEGER DEFAULT 0,
                supported_until TEXT,
                created_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_versions_component 
            ON versions(component_type, component_name, version)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_versions_status ON versions(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_versions_type ON versions(component_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_versions_name ON versions(component_name)
        """)
        self._conn.commit()

    def add_version(
        self,
        component_type: str,
        component_name: str,
        version: int,
        released_at: Optional[datetime] = None,
        status: str = VersionStatus.ACTIVE.value,
        release_notes: Optional[str] = None,
        breaking_changes: bool = False,
        supported_until: Optional[datetime] = None,
        created_by: Optional[str] = None,
    ) -> VersionEntry:
        """Add a version.

        Args:
            component_type: Type of component
            component_name: Component name
            version: Version number
            released_at: Release date
            release_notes: Release notes
            breaking_changes: Breaking changes flag
            supported_until: Support end date
            created_by: User who created

        Returns:
            Created version entry
        """
        entry = VersionEntry(
            component_type=component_type,
            component_name=component_name,
            version=version,
            released_at=released_at,
            status=status,
            release_notes=release_notes,
            breaking_changes=breaking_changes,
            supported_until=supported_until,
            created_by=created_by,
        )
        self.versions.append(entry)
        self.save_version(entry)
        return entry

    def save_version(self, entry: VersionEntry) -> None:
        """Save version to database."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO versions
            (id, component_type, component_name, version, released_at, status,
             release_notes, breaking_changes, supported_until, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.id,
                entry.component_type,
                entry.component_name,
                entry.version,
                entry.released_at.isoformat() if entry.released_at else None,
                entry.status,
                entry.release_notes,
                1 if entry.breaking_changes else 0,
                entry.supported_until.isoformat() if entry.supported_until else None,
                entry.created_by,
                entry.created_at.isoformat(),
                entry.updated_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get_by_name(self, component_type: str, component_name: str) -> list[VersionEntry]:
        """Get all versions of a component by name."""
        return [
            v for v in self.versions
            if v.component_type == component_type and v.component_name == component_name
        ]

    def get_active(self, component_type: str, component_name: str) -> Optional[VersionEntry]:
        """Get active version of a component."""
        versions = self.get_by_name(component_type, component_name)
        active = [v for v in versions if v.status == VersionStatus.ACTIVE.value]
        return active[0] if active else None

    def get_all_active(self) -> list[VersionEntry]:
        """Get all active versions."""
        return [v for v in self.versions if v.status == VersionStatus.ACTIVE.value]

    def get_by_type(self, component_type: str) -> list[VersionEntry]:
        """Get all versions of a component type."""
        return [v for v in self.versions if v.component_type == component_type]

    def activate_version(
        self,
        component_type: str,
        component_name: str,
        version: int,
        activated_by: Optional[str] = None,
    ) -> Optional[VersionEntry]:
        """Activate a specific version.

        Args:
            component_type: Component type
            component_name: Component name
            version: Version to activate
            activated_by: User who activated

        Returns:
            Activated version entry
        """
        entry = self.get_by_name_version(component_type, component_name, version)
        if entry:
            # Deactivate other versions first
            for v in self.versions:
                if (v.component_type == component_type 
                    and v.component_name == component_name):
                    v.status = VersionStatus.DEPRECATED.value
                    self.save_version(v)

            entry.activate()
            entry.created_by = activated_by or entry.created_by
            self.save_version(entry)
        return entry

    def get_by_name_version(
        self,
        component_type: str,
        component_name: str,
        version: int,
    ) -> Optional[VersionEntry]:
        """Get version by component name and version."""
        for v in self.versions:
            if (v.component_type == component_type 
                and v.component_name == component_name 
                and v.version == version):
                return v
        return None

    def deactivate_version(self, component_type: str, component_name: str, version: int) -> Optional[VersionEntry]:
        """Deprecate a version."""
        entry = self.get_by_name_version(component_type, component_name, version)
        if entry:
            entry.deprecate()
            self.save_version(entry)
        return entry

    def get_version_history(self, component_type: str, component_name: str) -> list[VersionEntry]:
        """Get history of a component."""
        return sorted(
            self.get_by_name(component_type, component_name),
            key=lambda v: v.version,
            reverse=True,
        )

    def get_active_version(self, component_type: str, component_name: str) -> Optional[int]:
        """Get active version number."""
        active = self.get_active(component_type, component_name)
        return active.version if active else None

    def check_breaking_change(
        self,
        component_type: str,
        component_name: str,
        from_version: int,
        to_version: int,
    ) -> bool:
        """Check if transition between versions has breaking changes."""
        versions = self.get_by_name(component_type, component_name)
        for v in versions:
            if v.version == to_version:
                return v.breaking_changes
        return False

    def get_supported_versions(
        self,
        component_type: str,
        component_name: str,
        date: Optional[datetime] = None,
    ) -> list[VersionEntry]:
        """Get versions supported at a given date."""
        date = date or datetime.now()
        versions = self.get_by_name(component_type, component_name)
        return [
            v for v in versions
            if v.status == VersionStatus.ACTIVE.value and (
                v.supported_until is None or v.supported_until >= date
            )
        ]

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
