"""Clarification models for PO Agent Platform v2.

Supports:
- ClarificationRequest: request for user clarification
- ClarificationResponse: response with clarification result
- ClarificationStatus: status enum (NEEDS_CLARIFICATION, COMPLETED, CANCELLED)

ClarificationRequest fields:
- clarification_id: unique ID
- reason: why clarification is needed
- missing_fields: list of missing/ambiguous fields
- question: user-friendly question
- options: optional deterministic options
- original_intent: original intent from query
- original_query: original query text

Precedence for options:
- Code-based options (from product list, sprint list) > LLM-generated > None
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class ClarificationStatus(Enum):
    """Status of clarification request."""
    PENDING = "pending"
    ANSWERED = "answered"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ClarificationOption(BaseModel):
    """Single clarification option."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    label: str
    value: str
    description: Optional[str] = None


class ClarificationRequest(BaseModel):
    """Request for user clarification."""
    clarification_id: str = Field(default_factory=lambda: f"clar-{uuid.uuid4().hex[:12]}")
    reason: str
    missing_fields: List[str]
    question: str
    options: List[ClarificationOption] = Field(default_factory=list)
    original_intent: Optional[str] = None
    original_query: str
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(default_factory=lambda: datetime.now() + timedelta(hours=1))

    def is_expired(self) -> bool:
        """Check if clarification request is expired."""
        return datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "clarification_id": self.clarification_id,
            "reason": self.reason,
            "missing_fields": self.missing_fields,
            "question": self.question,
            "options": [o.model_dump() for o in self.options],
            "original_intent": self.original_intent,
            "original_query": self.original_query,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }


class ClarificationAnswer(BaseModel):
    """Answer to a clarification request."""
    clarification_id: str
    answer: str
    selected_option: Optional[str] = None  # If user clicked a button
    created_at: datetime = Field(default_factory=datetime.now)

    def is_valid(self) -> bool:
        """Check if answer is valid."""
        return bool(self.answer.strip()) or bool(self.selected_option)


class ClarificationResponse(BaseModel):
    """Response with clarification result."""
    status: ClarificationStatus
    clarification_id: Optional[str] = None
    question: Optional[str] = None
    options: Optional[List[Dict[str, Any]]] = None
    resolution: Optional[Dict[str, Any]] = None
    pending_request: Optional[Dict[str, Any]] = None

    @classmethod
    def needs_clarification(
        cls,
        clarification_id: str,
        question: str,
        options: Optional[List[ClarificationOption]] = None,
        pending_request: Optional[Dict[str, Any]] = None,
    ) -> "ClarificationResponse":
        """Create response indicating clarification is needed."""
        return cls(
            status=ClarificationStatus.PENDING,
            clarification_id=clarification_id,
            question=question,
            options=[o.model_dump() for o in options] if options else None,
            pending_request=pending_request,
        )

    @classmethod
    def completed(
        cls,
        resolution: Dict[str, Any],
    ) -> "ClarificationResponse":
        """Create response indicating clarification completed."""
        return cls(
            status=ClarificationStatus.ANSWERED,
            resolution=resolution,
        )

    @classmethod
    def cancelled(
        cls,
    ) -> "ClarificationResponse":
        """Create response indicating clarification cancelled."""
        return cls(
            status=ClarificationStatus.CANCELLED,
        )


# Export for convenience
__all__ = [
    "ClarificationStatus",
    "ClarificationOption",
    "ClarificationRequest",
    "ClarificationAnswer",
    "ClarificationResponse",
]
