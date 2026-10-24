"""ResolvedContext model for PO Agent Platform v2.

Context resolution result with source tracking and priority handling.

Context sources:
- current_request: explicit current input from user query
- clarification_answer: answer from clarification loop
- session_memory: values from SessionMemory
- deterministic_lookup: code-based lookup (product list, sprint list)
- approved_curated_memory: approved alias/mapping from CuratedMemory
- default: default value when nothing else available

Precedence order:
current_request > clarification_answer > session_memory > 
deterministic_lookup > approved_curated_memory > default
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, ConfigDict

from po_agent.domain.models import AttachmentType


class ContextSource(Enum):
    """Source of a resolved context value."""
    CURRENT_REQUEST = "current_request"
    CLARIFICATION_ANSWER = "clarification_answer"
    SESSION_MEMORY = "session_memory"
    DETERMINISTIC_LOOKUP = "deterministic_lookup"
    APPROVED_CURATED_MEMORY = "approved_curated_memory"
    DEFAULT = "default"


class ContextConflict(BaseModel):
    """Conflict between context sources."""
    field: str
    source1: str
    value1: str
    source2: str
    value2: str
    resolved_by: str  # which source won
    resolved_at: datetime = Field(default_factory=datetime.now)


class ResolvedContext(BaseModel):
    """Resolved context from query processing.

    Each field includes source tracking to know where the value came from.
    This enables proper precedence handling and debugging.
    """

    model_config = ConfigDict(extra="allow")

    # Core context fields
    product: Optional[str] = None
    sprint_id: Optional[str] = None
    release_id: Optional[str] = None
    task_id: Optional[str] = None
    member_login: Optional[str] = None
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    attachment_type: Optional[AttachmentType] = None

    # Source tracking for each field
    product_source: Optional[ContextSource] = None
    sprint_source: Optional[ContextSource] = None
    release_source: Optional[ContextSource] = None
    task_source: Optional[ContextSource] = None
    member_source: Optional[ContextSource] = None
    date_source: Optional[ContextSource] = None
    attachment_source: Optional[ContextSource] = None

    # Resolution metadata
    missing_fields: List[str] = Field(default_factory=list)
    ambiguous_fields: List[str] = Field(default_factory=list)
    conflicts: List[ContextConflict] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    needs_clarification: bool = False

    # Resolution metadata
    resolution_timestamp: datetime = Field(default_factory=datetime.now)
    query: Optional[str] = None
    session_id: Optional[str] = None

    def get_value(self, field: str) -> tuple[Optional[Any], Optional[ContextSource]]:
        """Get value and source for a field.

        Args:
            field: Field name (product, sprint_id, etc.)

        Returns:
            Tuple of (value, source)
        """
        value_attr = field
        source_attr = f"{field}_source"

        value = getattr(self, value_attr, None)
        source = getattr(self, source_attr, None)

        return value, source

    def set_value(
        self,
        field: str,
        value: Any,
        source: ContextSource,
        override: bool = False,
    ) -> bool:
        """Set value for a field.

        Args:
            field: Field name
            value: Value to set
            source: Source of the value
            override: Whether to override existing value

        Returns:
            True if value was set, False if skipped due to precedence
        """
        # Check if field already has a value from higher-priority source
        existing_source = getattr(self, f"{field}_source", None)

        if existing_source is not None and not override:
            # Check precedence
            source_priority = {
                ContextSource.CURRENT_REQUEST: 6,
                ContextSource.CLARIFICATION_ANSWER: 5,
                ContextSource.SESSION_MEMORY: 4,
                ContextSource.DETERMINISTIC_LOOKUP: 3,
                ContextSource.APPROVED_CURATED_MEMORY: 2,
                ContextSource.DEFAULT: 1,
            }

            if source_priority.get(source, 0) <= source_priority.get(existing_source, 0):
                return False  # Skip - existing source has higher priority

        # Set the value
        setattr(self, field, value)
        setattr(self, f"{field}_source", source)
        return True

    def mark_missing(self, field: str) -> None:
        """Mark a field as missing."""
        if field not in self.missing_fields:
            self.missing_fields.append(field)

    def mark_ambiguous(self, field: str) -> None:
        """Mark a field as ambiguous."""
        if field not in self.ambiguous_fields:
            self.ambiguous_fields.append(field)

    def add_conflict(self, conflict: ContextConflict) -> None:
        """Add a conflict to the list."""
        self.conflicts.append(conflict)

    def has_all_required(self, required_fields: List[str]) -> bool:
        """Check if all required fields are resolved.

        Args:
            required_fields: List of required field names

        Returns:
            True if all fields have values, False otherwise
        """
        for field in required_fields:
            value, _ = self.get_value(field)
            if value is None:
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "product": self.product,
            "product_source": self.product_source.value if self.product_source else None,
            "sprint_id": self.sprint_id,
            "sprint_source": self.sprint_source.value if self.sprint_source else None,
            "release_id": self.release_id,
            "release_source": self.release_source.value if self.release_source else None,
            "task_id": self.task_id,
            "task_source": self.task_source.value if self.task_source else None,
            "member_login": self.member_login,
            "member_source": self.member_source.value if self.member_source else None,
            "date_range_start": self.date_range_start.isoformat() if self.date_range_start else None,
            "date_range_end": self.date_range_end.isoformat() if self.date_range_end else None,
            "date_source": self.date_source.value if self.date_source else None,
            "attachment_type": self.attachment_type.value if self.attachment_type else None,
            "attachment_source": self.attachment_source.value if self.attachment_source else None,
            "missing_fields": self.missing_fields,
            "ambiguous_fields": self.ambiguous_fields,
            "conflicts": [c.model_dump() for c in self.conflicts],
            "confidence": self.confidence,
            "needs_clarification": self.needs_clarification,
            "resolution_timestamp": self.resolution_timestamp.isoformat(),
        }
