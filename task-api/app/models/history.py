from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class HistoryEvent(BaseModel):
    """Represents a single history event (status or assignee transition)."""
    task_code: str = Field(..., description="Task code like DMS-271")
    event_id: Optional[str] = Field(None, description="Event ID if available from source")
    changed_at: datetime = Field(..., description="Timestamp when the change occurred")
    field_code: str = Field(..., description="Field that changed (e.g., 'workflow_status', 'assigned_to')")
    field_name: Optional[str] = Field(None, description="Human-readable field name")
    old_value: Optional[str] = Field(None, description="Previous value")
    new_value: Optional[str] = Field(None, description="New value")
    actor: str = Field(..., description="User externalId who made the change")


class HistoryResponse(BaseModel):
    """Normalized response containing all history events for a task."""
    task_code: str = Field(..., description="Task code like DMS-271")
    events: List[HistoryEvent] = Field(..., description="List of history events sorted chronologically")
    page_info: dict = Field(..., description="Pagination information from the source API")
