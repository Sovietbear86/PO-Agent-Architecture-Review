"""Canonical domain models for PO Agent Platform v2.

This module defines transport-independent domain models that represent
the core entities of the PO Agent Platform.

All models use Pydantic v2 for validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, WithJsonSchema


# =============================================================================
# Common Identifiers and Timestamps
# =============================================================================

class TaskKey(str):
    """Task identifier (e.g., WMB-123, DMS-456)."""
    pass


class SprintId(str):
    """Sprint identifier (e.g., DMS-SPRNT-1, WMB-SPRNT-2024-03)."""
    pass


class ReleaseId(str):
    """Release identifier."""
    pass


class MemberId(str):
    """Team member identifier (e.g., login)."""
    pass


# Pydantic v2 schema for custom string types
def task_key_schema() -> dict:
    """Pydantic v2 schema for TaskKey."""
    return {"type": "string", "pattern": r"^[A-Z]+-\d+$"}


def sprint_id_schema() -> dict:
    """Pydantic v2 schema for SprintId."""
    return {"type": "string", "pattern": r"^[A-Z]+-SPRNT-\d+$"}


def release_id_schema() -> dict:
    """Pydantic v2 schema for ReleaseId."""
    return {"type": "string", "pattern": r"^[A-Z]+-\d{4}-[A-Z]+\d*$"}


def member_id_schema() -> dict:
    """Pydantic v2 schema for MemberId."""
    return {"type": "string", "pattern": r"^[A-Z]+\.[A-Z]+\.[A-Z]+$"}


class Timestamp(BaseModel):
    """A timestamp with optional timezone info."""
    value: datetime
    timezone: Optional[str] = None


# =============================================================================
# Status and Workflow Models
# =============================================================================

class StatusCategory(str, Enum):
    """Categories for task status."""
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
    """Task statuses based on AS21 workflow."""
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
    """A status change event in task history."""
    from_status: TaskStatus
    to_status: TaskStatus
    timestamp: datetime
    author: Optional[str] = None
    transition_type: Optional[str] = None  # manual, automated, etc.


# =============================================================================
# Attachment Models
# =============================================================================

class AttachmentType(str, Enum):
    """Types of attachments."""
    EXCEL = "excel"
    WORD = "word"
    PDF = "pdf"
    MSG = "msg"
    IMAGE = "image"
    TEXT = "text"
    OTHER = "other"


class Attachment(BaseModel):
    """Task attachment metadata."""
    id: str
    name: str
    type: AttachmentType
    size_bytes: int
    created_at: datetime
    url: Optional[str] = None
    description: Optional[str] = None


# =============================================================================
# Task Models
# =============================================================================

class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"
    CRITICAL = "Critical"


class Task(BaseModel):
    """Core Task domain model - transport independent."""
    
    # Identifiers
    key: str = Field(..., pattern=r"^[A-Z]+-\d+$")
    id: str  # Internal database ID
    
    # Core attributes
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=10000)
    
    # Status and workflow
    status: TaskStatus
    status_category: StatusCategory
    status_transitions: list[StatusTransition] = []
    
    # Assignment
    assignee: Optional[str] = None
    assignee_id: Optional[str] = None
    
    # Dates
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Priority and effort
    priority: Optional[TaskPriority] = None
    estimate_hours: Optional[float] = None
    time_spent_hours: Optional[float] = None
    
    # Relationships
    sprint_id: Optional[str] = None
    release_id: Optional[str] = None
    parent_key: Optional[str] = None
    depends_on: list[str] = []
    
    # Metadata
    labels: list[str] = []
    components: list[str] = []
    
    # Attachments
    attachments: list[Attachment] = []
    
    # Source tracking
    source: str = "swtr"  # Source system identifier
    source_url: Optional[str] = None
    
    # Computed fields (calculated from status transitions)
    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status in (
            TaskStatus.RESOLVED,
            TaskStatus.CLOSED,
            TaskStatus.CANCELLED,
        )
    
    @property
    def is_blocked(self) -> bool:
        """Check if task is blocked (waiting for info)."""
        return self.status == TaskStatus.NEED_INFO
    
    @property
    def age_days(self) -> int:
        """Calculate task age in days."""
        delta = datetime.now() - self.created_at
        return delta.days
    
    @property
    def time_in_current_status_hours(self) -> float:
        """Calculate time spent in current status."""
        if not self.status_transitions:
            return 0.0
        last_transition = self.status_transitions[-1]
        delta = datetime.now() - last_transition.timestamp
        return delta.total_seconds() / 3600
    
    @property
    def cycle_time_hours(self) -> float:
        """Calculate cycle time (from first In progress to current)."""
        in_progress = None
        for transition in self.status_transitions:
            if transition.to_status == TaskStatus.IN_PROGRESS:
                in_progress = transition.timestamp
                break
        
        if in_progress is None:
            # No In progress status, use created_at
            in_progress = self.created_at
        
        delta = datetime.now() - in_progress
        return delta.total_seconds() / 3600
    
    @property
    def lead_time_hours(self) -> float:
        """Calculate lead time (from creation to current)."""
        delta = datetime.now() - self.created_at
        return delta.total_seconds() / 3600


# =============================================================================
# Sprint Models
# =============================================================================

class SprintState(str, Enum):
    """Sprint states."""
    FUTURE = "future"
    ACTIVE = "active"
    CLOSED = "closed"


class Sprint(BaseModel):
    """Sprint domain model."""

    id: str = Field(..., pattern=r"^[A-Z]+-SPRNT-\d+$")
    name: str
    space: str  # Project space (WMB, DMS, OLP, etc.)

    # Dates
    start_date: datetime
    end_date: datetime
    created_at: datetime
    closed_at: Optional[datetime] = None

    # Status
    state: SprintState

    # Committed scope
    committed_tasks: list[str] = []
    completed_tasks: list[str] = []

    # Metadata
    description: Optional[str] = None
    goal: Optional[str] = None
    velocity_target: Optional[int] = None
    
    @property
    def duration_days(self) -> int:
        """Calculate sprint duration in days."""
        delta = self.end_date - self.start_date
        return delta.days
    
    @property
    def is_current(self) -> bool:
        """Check if sprint is currently active."""
        now = datetime.now()
        return self.start_date <= now <= self.end_date and self.state == SprintState.ACTIVE
    
    @property
    def is_past(self) -> bool:
        """Check if sprint has ended."""
        return self.state == SprintState.CLOSED
    
    @property
    def is_upcoming(self) -> bool:
        """Check if sprint hasn't started yet."""
        now = datetime.now()
        return now < self.start_date and self.state == SprintState.FUTURE


# =============================================================================
# Release Models
# =============================================================================

class ReleaseState(str, Enum):
    """Release states."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    READY_FOR_TESTING = "ready_for_testing"
    RELEASED = "released"
    CANCELLED = "cancelled"


class Release(BaseModel):
    """Release domain model."""

    id: str = Field(..., pattern=r"^[A-Z]+-\d{4}-[A-Z]+\d*$")
    name: str
    space: str

    # Dates
    target_date: Optional[datetime] = None
    created_at: datetime
    released_at: Optional[datetime] = None

    # Status
    state: ReleaseState

    # Scope
    scheduled_tasks: list[str] = []
    completed_tasks: list[str] = []
    blocked_tasks: list[str] = []

    # Sprint linkage
    linked_sprints: list[str] = []

    # Metadata
    description: Optional[str] = None
    version: Optional[str] = None
    epic: Optional[str] = None
    
    @property
    def completion_ratio(self) -> float:
        """Calculate release completion ratio."""
        total = len(self.scheduled_tasks)
        if total == 0:
            return 1.0
        return len(self.completed_tasks) / total
    
    @property
    def is_on_track(self) -> bool:
        """Check if release is on track."""
        if self.state == ReleaseState.CANCELLED:
            return False
        if self.state == ReleaseState.RELEASED:
            return True
        return self.completion_ratio >= 0.8


# =============================================================================
# Team Models
# =============================================================================

class TeamRole(str, Enum):
    """Team member roles."""
    PRODUCT_OWNER = "Владелец продукта"
    TECH_LEAD = "Лидер продукта"
    DEVELOPER = "Участник команды"
    QA = "Участник команды"
    ANALYST = "Участник команды"
    ARCHITECT = "Участник команды"
    OTHER = "Участник команды"


class Competency(BaseModel):
    """A competency/skill of a team member."""
    name: str
    level: int = Field(ge=1, le=10)  # 1-10 proficiency level
    years_experience: Optional[int] = None
    evidence: Optional[str] = None  # Path to evidence file


class TeamMember(BaseModel):
    """Team member domain model."""

    id: str  # Login/employee ID (e.g., Ivanov.I.I, Petrov.P.P)
    full_name: str
    email: Optional[str] = None
    grade: Optional[int] = None

    # Roles
    team_role: TeamRole
    products: list[str] = []

    # Competencies
    competencies: dict[str, Competency] = {}

    # Allocation
    allocation_percent: Optional[float] = Field(None, ge=0, le=100)
    recommended_max_wip: Optional[int] = None

    # Status
    is_active: bool = True
    planned_absences: list[datetime] = []
    
    @property
    def primary_product(self) -> Optional[str]:
        """Get primary product (first in list)."""
        return self.products[0] if self.products else None
    
    @property
    def total_competency_level(self) -> int:
        """Sum of all competency levels."""
        return sum(c.level for c in self.competencies.values())


# =============================================================================
# Dependency Models
# =============================================================================

class DependencyType(str, Enum):
    """Types of dependencies."""
    BLOCKING = "blocking"  # This task blocks the other
    BLOCKED_BY = "blocked_by"  # This task is blocked by the other
    RELATED = "related"  # Related but not blocking
    DUPLICATE = "duplicate"  # Duplicate task


class Dependency(BaseModel):
    """Task dependency relationship."""

    task_key: str = Field(..., pattern=r"^[A-Z]+-\d+$")
    depends_on: str = Field(..., pattern=r"^[A-Z]+-\d+$")
    type: DependencyType
    description: Optional[str] = None
    resolved_at: Optional[datetime] = None

    @property
    def is_blocking(self) -> bool:
        """Check if this dependency is currently blocking."""
        return self.type == DependencyType.BLOCKING


# =============================================================================
# Utility Functions
# =============================================================================

def normalize_task_status(raw_status: str) -> TaskStatus:
    """Normalize a raw status string to TaskStatus enum."""
    status_map = {
        "open": TaskStatus.OPEN,
        "открыта": TaskStatus.OPEN,
        "need info": TaskStatus.NEED_INFO,
        "требуется информация": TaskStatus.NEED_INFO,
        "in progress": TaskStatus.IN_PROGRESS,
        "в работе": TaskStatus.IN_PROGRESS,
        "ready for review": TaskStatus.READY_FOR_REVIEW,
        "готово к ревью": TaskStatus.READY_FOR_REVIEW,
        "in review": TaskStatus.IN_REVIEW,
        "на ревью": TaskStatus.IN_REVIEW,
        "ready for qa": TaskStatus.READY_FOR_QA,
        "готово к qa": TaskStatus.READY_FOR_QA,
        "qa": TaskStatus.QA,
        "тестирование": TaskStatus.QA,
        "reopened": TaskStatus.REOPENED,
        "переоткрыта": TaskStatus.REOPENED,
        "resolved": TaskStatus.RESOLVED,
        "решена": TaskStatus.RESOLVED,
        "closed": TaskStatus.CLOSED,
        "закрыта": TaskStatus.CLOSED,
        "cancelled": TaskStatus.CANCELLED,
        "отменена": TaskStatus.CANCELLED,
    }
    return status_map.get(raw_status.lower().strip(), TaskStatus.OPEN)


def get_status_category(status: TaskStatus) -> StatusCategory:
    """Get the status category for a given status."""
    category_map = {
        TaskStatus.OPEN: StatusCategory.BACKLOG,
        TaskStatus.NEED_INFO: StatusCategory.WAITING,
        TaskStatus.IN_PROGRESS: StatusCategory.ACTIVE_WORK,
        TaskStatus.READY_FOR_REVIEW: StatusCategory.REVIEW_QUEUE,
        TaskStatus.IN_REVIEW: StatusCategory.REVIEW,
        TaskStatus.READY_FOR_QA: StatusCategory.QA_QUEUE,
        TaskStatus.QA: StatusCategory.TESTING,
        TaskStatus.REOPENED: StatusCategory.ACTIVE_WORK,
        TaskStatus.RESOLVED: StatusCategory.COMPLETED_PENDING,
        TaskStatus.CLOSED: StatusCategory.COMPLETED,
        TaskStatus.CANCELLED: StatusCategory.CANCELLED,
    }
    return category_map.get(status, StatusCategory.UNKNOWN)
