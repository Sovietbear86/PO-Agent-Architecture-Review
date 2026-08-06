"""Task and Status models."""
from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4
from typing import Union


class Status(str, Enum):
    """Task status enum."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

    @classmethod
    def from_value(cls, value: str) -> "Status":
        """Create Status from string value."""
        value_lower = value.lower().strip()
        if value_lower in ('todo', 'waiting', 'backlog', 'blocked'):
            return cls.TODO
        elif value_lower in ('in_progress', 'inprogress', 'working', 'active'):
            return cls.IN_PROGRESS
        elif value_lower in ('done', 'completed', 'finished', 'closed'):
            return cls.DONE
        else:
            return cls.TODO


# Type for status that can be either enum or string (for external sources)
StatusType = Union[Status, str]


class Task:
    """Task model."""

    def __init__(
        self,
        title: str,
        description: str | None = None,
        assignee: str | None = None,
        deadline: datetime | None = None,
        source_url: str | None = None,
        status: StatusType = Status.TODO,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        id: UUID | None = None,
        source: str | None = None,  # 'swtr' for SberWorks Task Tracker
        source_id: str | None = None,  # External task ID (e.g., WMB-29890)
        source_data: dict | None = None,  # Raw data from external source
    ):
        self.id = id or uuid4()
        self.title = title
        self.description = description
        self.assignee = assignee
        self.deadline = deadline
        self.source_url = source_url
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.source = source  # Source identifier (e.g., 'swtr')
        self.source_id = source_id  # External ID (e.g., 'WMB-29890')
        self.source_data = source_data or {}  # Raw data from external source
    
    def update(self, title: str | None = None, description: str | None = None,
               assignee: str | None = None, deadline: datetime | None = None,
               source_url: str | None = None,
               status: StatusType | None = None,
               source: str | None = None, source_id: str | None = None) -> None:
        """Update task fields."""
        if title is not None:
            if len(title) < 1 or len(title) > 200:
                raise ValueError("Title must be between 1 and 200 characters")
            self.title = title
        if description is not None:
            if len(description) > 1000:
                raise ValueError("Description must be 1000 characters or less")
            self.description = description
        if assignee is not None:
            if len(assignee) > 100:
                raise ValueError("Assignee must be 100 characters or less")
            self.assignee = assignee
        if deadline is not None:
            self.deadline = deadline
        if source_url is not None:
            if len(source_url) > 500:
                raise ValueError("Source URL must be 500 characters or less")
            self.source_url = source_url
        if status is not None:
            self.status = status
        if source is not None:
            self.source = source
        if source_id is not None:
            self.source_id = source_id
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "assignee": self.assignee,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "source_url": self.source_url,
            # Handle status - if it's an enum, use .value; if it's a string, use as-is
            "status": self.status.value if hasattr(self.status, 'value') else self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "source": self.source,
            "source_id": self.source_id,
            "source_data": self.source_data,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create task from dictionary."""
        try:
            id_val = UUID(data["id"]) if isinstance(data.get("id"), str) else data.get("id")
        except (ValueError, TypeError):
            id_val = data.get("id")

        # Parse deadline from ISO format string
        deadline = None
        if data.get("deadline"):
            try:
                deadline = datetime.fromisoformat(data["deadline"].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                deadline = None

        return cls(
            id=id_val,
            title=data["title"],
            description=data.get("description"),
            assignee=data.get("assignee"),
            deadline=deadline,
            source_url=data.get("source_url"),
            # Handle status - use string directly for external sources (workflow_status_name)
            status=data.get("status", "todo") if isinstance(data.get("status"), str) else StatusType(data.get("status", "todo")),
            created_at=datetime.fromisoformat(data["created_at"].replace('Z', '+00:00')) if isinstance(data.get("created_at"), str) else data.get("created_at"),
            updated_at=datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00')) if isinstance(data.get("updated_at"), str) else data.get("updated_at"),
            source=data.get("source"),
            source_id=data.get("source_id"),
            source_data=data.get("source_data", {}),
        )
