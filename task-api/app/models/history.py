from datetime import datetime
from typing import Optional, List, Any
import json

from pydantic import BaseModel, Field


class HistoryEvent(BaseModel):
    """Represents a single history event (status or assignee transition)."""
    task_code: str = Field(..., description="Task code like DMS-271")
    event_id: Optional[str] = Field(None, description="Event ID if available from source")
    changed_at: datetime = Field(..., description="Timestamp when the change occurred")
    field_code: str = Field(..., description="Field that changed (e.g., 'workflow_status', 'assigned_to')")
    field_name: Optional[str] = Field(None, description="Human-readable field name")
    old_value: Optional[str] = Field(None, description="Previous value (JSON string for structured data)")
    new_value: Optional[str] = Field(None, description="New value (JSON string for structured data)")
    actor: str = Field(..., description="User externalId who made the change")
    
    @classmethod
    def model_validate(cls, obj: Any, *, strict: bool = False, from_attributes: bool = False) -> "HistoryEvent":
        """Validate and convert old_value/new_value to JSON strings if they're dicts."""
        data = dict(obj) if isinstance(obj, dict) else obj
        if isinstance(data, dict):
            # Convert old_value and new_value to JSON strings if they're dicts
            if "old_value" in data and isinstance(data["old_value"], dict):
                data["old_value"] = json.dumps(data["old_value"], ensure_ascii=False)
            if "new_value" in data and isinstance(data["new_value"], dict):
                data["new_value"] = json.dumps(data["new_value"], ensure_ascii=False)
        return super().model_validate(data, strict=strict, from_attributes=from_attributes)


class HistoryResponse(BaseModel):
    """Normalized response containing all history events for a task."""
    task_code: str = Field(..., description="Task code like DMS-271")
    events: List[HistoryEvent] = Field(..., description="List of history events sorted chronologically")
    page_info: dict = Field(..., description="Pagination information from the source API")
