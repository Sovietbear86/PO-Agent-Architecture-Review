"""Canonical domain models for PO Agent Platform v2.

Transport-independent domain entities. AS21-specific parsing belongs in adapters;
canonical fields contain only facts that deterministic capabilities may consume.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskKey(str):
    pass


class SprintId(str):
    pass


class ReleaseId(str):
    pass


class MemberId(str):
    pass


def task_key_schema() -> dict:
    return {"type": "string", "pattern": r"^[A-Z]+-\d+$"}


def sprint_id_schema() -> dict:
    return {"type": "string", "pattern": r"^[A-Z]+-SPRNT-\d+$"}


def release_id_schema() -> dict:
    return {"type": "string", "pattern": r"^[A-Z]+-\d{4}-[A-Z]+\d*$"}


def member_id_schema() -> dict:
    return {"type": "string", "pattern": r"^[A-Z]+\.[A-Z]+\.[A-Z]+$"}


class Timestamp(BaseModel):
    value: datetime
    timezone: Optional[str] = None


class StatusCategory(str, Enum):
    BACKLOG = "backlog"
    WAITING = "waiting"
    ACTIVE_WORK = "active_work"
    REVIEW_QUEUE = "review_queue"
    REVIEW = "review"
    QA_QUEUE = "qa_queue"
    TESTING = "testing"
    COMPLETED_PENDING = "completed_pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class TaskStatus(str, Enum):
    UNKNOWN = "Unknown"
    OPEN = "Open"
    NEED_INFO = "Need info"
    IN_PROGRESS = "In progress"
    READY_FOR_REVIEW = "Ready for review"
    IN_REVIEW = "In review"
    READY_FOR_QA = "Ready for QA"
    QA = "QA"
    REOPENED = "Reopened"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    CANCELLED = "Cancelled"


class StatusTransition(BaseModel):
    from_status: TaskStatus
    to_status: TaskStatus
    timestamp: datetime
    author: Optional[str] = None
    transition_type: Optional[str] = None


class AttachmentType(str, Enum):
    EXCEL = "excel"
    WORD = "word"
    PDF = "pdf"
    MSG = "msg"
    IMAGE = "image"
    TEXT = "text"
    OTHER = "other"


class Attachment(BaseModel):
    id: str
    name: str
    type: AttachmentType
    size_bytes: int
    created_at: datetime
    url: Optional[str] = None
    description: Optional[str] = None


class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"
    CRITICAL = "Critical"


class Task(BaseModel):
    key: str = Field(..., pattern=r"^[A-Z]+-\d+$")
    id: str
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=10000)

    status: TaskStatus
    status_category: StatusCategory
    status_raw: Optional[str] = None
    status_transitions: list[StatusTransition] = []

    assignee: Optional[str] = None
    assignee_id: Optional[str] = None
    assignee_login: Optional[str] = None

    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    priority: Optional[TaskPriority] = None
    estimate_hours: Optional[float] = None
    time_spent_hours: Optional[float] = None

    project_space: Optional[str] = None
    sprint_id: Optional[str] = None
    release_id: Optional[str] = None
    parent_key: Optional[str] = None
    depends_on: list[str] = []

    labels: list[str] = []
    components: list[str] = []
    attachments: list[Attachment] = []

    source: str = "swtr"
    source_url: Optional[str] = None
    source_data: dict[str, Any] = Field(default_factory=dict, repr=False)

    @property
    def is_completed(self) -> bool:
        return self.status in (TaskStatus.RESOLVED, TaskStatus.CLOSED, TaskStatus.CANCELLED)

    @property
    def is_blocked(self) -> bool:
        return self.status == TaskStatus.NEED_INFO

    @property
    def age_days(self) -> int:
        return (datetime.now() - self.created_at).days

    @property
    def time_in_current_status_hours(self) -> float:
        if not self.status_transitions:
            return 0.0
        return (datetime.now() - self.status_transitions[-1].timestamp).total_seconds() / 3600

    @property
    def cycle_time_hours(self) -> float:
        in_progress = next(
            (t.timestamp for t in self.status_transitions if t.to_status == TaskStatus.IN_PROGRESS),
            self.created_at,
        )
        end = self.resolved_at or self.closed_at or datetime.now()
        return (end - in_progress).total_seconds() / 3600

    @property
    def lead_time_hours(self) -> float:
        end = self.resolved_at or self.closed_at or datetime.now()
        return (end - self.created_at).total_seconds() / 3600


class SprintState(str, Enum):
    FUTURE = "future"
    ACTIVE = "active"
    CLOSED = "closed"


class Sprint(BaseModel):
    id: str
    name: str
    space: str
    start_date: datetime
    end_date: datetime
    created_at: datetime
    closed_at: Optional[datetime] = None
    state: SprintState
    committed_tasks: list[str] = []
    completed_tasks: list[str] = []
    description: Optional[str] = None
    goal: Optional[str] = None
    velocity_target: Optional[int] = None

    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days

    @property
    def is_current(self) -> bool:
        now = datetime.now()
        return self.start_date <= now <= self.end_date and self.state == SprintState.ACTIVE

    @property
    def is_past(self) -> bool:
        return self.state == SprintState.CLOSED

    @property
    def is_upcoming(self) -> bool:
        return datetime.now() < self.start_date and self.state == SprintState.FUTURE


class ReleaseState(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    READY_FOR_TESTING = "ready_for_testing"
    RELEASED = "released"
    CANCELLED = "cancelled"


class Release(BaseModel):
    id: str
    name: str
    space: str
    state: ReleaseState
    planned_date: Optional[datetime] = None
    released_date: Optional[datetime] = None
    task_keys: list[str] = []
    description: Optional[str] = None
