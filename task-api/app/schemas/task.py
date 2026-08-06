"""Pydantic schemas for task operations."""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Union
from datetime import datetime
from uuid import UUID
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
    """Schema for updating a task."""
    title: Optional[str] = Field(None, description="If provided, must be 1-200 characters")
    description: Optional[str] = Field(None, max_length=1000)
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
    """Schema for task response."""
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
    sprint: Optional[str] = None

def task_to_response(task) -> TaskResponse:
    """Convert Task model to TaskResponse."""
    # Extract deadline from source_data or use model field
    deadline = task.deadline
    if not deadline and task.source_data:
        # Try to get from source_data.deadline
        deadline_str = task.source_data.get('deadline')
        if deadline_str:
            from datetime import datetime, timezone
            deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))

    # Extract sprint from source_data or swtr_attributes
    sprint = None
    if task.source_data:
        sprint = task.source_data.get('sprint_id')
        # If sprint not in source_data.sprint_id, try to get it from swtr_attributes
        if not sprint:
            swtr_attrs = task.source_data.get('swtr_attributes', [])
            for attr in swtr_attrs:
                if attr.get('code') == 'scrum_board_plugin_sprint':
                    value = attr.get('value', {})
                    if isinstance(value, dict):
                        sprint = value.get('code') or value.get('id') or value.get('value')
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
        source_data=task.source_data or {},
        sprint=sprint,
    )
