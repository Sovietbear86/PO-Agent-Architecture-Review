"""Pydantic schemas for task operations."""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Union
from datetime import datetime
from app.models.task import Status


class TaskCreate(BaseModel):
    """Schema for creating a task."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    assignee: Optional[str] = Field(None, max_length=100)
    source_url: Optional[str] = Field(None, max_length=500)
    source_id: Optional[str] = Field(None, max_length=100)
    source: Optional[str] = Field(None, max_length=50)
    source_data: dict = {}
    status: Optional[Union[Status, str]] = Field(None, description="Task status (todo, in_progress, done)")


class TaskUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=1000)
    title: Optional[str] = Field(None, description="If provided, must be 1-200 characters")
    assignee: Optional[str] = Field(None, max_length=100)
    status: Optional[Union[Status, str]] = None

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None and len(v) < 1:
            raise ValueError('Title must be at least 1 character')
        if v is not None and len(v) > 200:
            raise ValueError('Title must be at most 200 characters')
        return v


class TaskResponse(BaseModel):
    """Task API read contract including source-backed AS21 relations."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: Optional[str]
    assignee: Optional[str]
    deadline: Optional[datetime] = None
    source_url: Optional[str] = None
    status: Union[Status, str]
    created_at: datetime
    updated_at: datetime
    source: Optional[str] = None
    source_id: Optional[str] = None
    source_data: dict = {}
    project_space: Optional[str] = None
    sprint_id: Optional[str] = None
    # Backward-compatible alias retained for older consumers.
    sprint: Optional[str] = None


def _identifier(value):
    if isinstance(value, (str, int)):
        text = str(value).strip()
        return text or None
    if isinstance(value, dict):
        for key in ('code', 'id', 'externalId', 'value', 'name'):
            candidate = value.get(key)
            if isinstance(candidate, (str, int)) and str(candidate).strip():
                return str(candidate).strip()
    if isinstance(value, list):
        for item in value:
            candidate = _identifier(item)
            if candidate:
                return candidate
    return None


def task_to_response(task) -> TaskResponse:
    """Convert Task model while preserving proven AS21 space/sprint facts."""
    deadline = task.deadline
    source_data = task.source_data or {}
    if not deadline:
        deadline_str = source_data.get('deadline')
        if deadline_str:
            deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))

    project_space = source_data.get('swtr_space') if isinstance(source_data.get('swtr_space'), str) else None
    sprint_id = _identifier(source_data.get('sprint_id'))
    if not sprint_id:
        for attr in source_data.get('swtr_attributes', []):
            if isinstance(attr, dict) and attr.get('code') == 'scrum_board_plugin_sprint':
                sprint_id = _identifier(attr.get('value'))
                if sprint_id:
                    break

    return TaskResponse(
        id=str(task.id),
        title=task.title,
        description=task.description,
        assignee=task.assignee,
        deadline=deadline,
        source_url=task.source_url,
        status=task.status,
        created_at=task.created_at,
        updated_at=task.updated_at,
        source=task.source,
        source_id=task.source_id,
        source_data=source_data,
        project_space=project_space,
        sprint_id=sprint_id,
        sprint=sprint_id,
    )