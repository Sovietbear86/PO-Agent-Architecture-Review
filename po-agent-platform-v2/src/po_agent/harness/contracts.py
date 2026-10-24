"""Typed contracts for the executable harness runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResponseStatus(str, Enum):
    COMPLETED = "COMPLETED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


@dataclass(frozen=True)
class Evidence:
    """A source-backed fact used to construct an answer."""

    type: str
    source: str
    label: str
    entity_id: str | None = None
    value: Any = None
    freshness: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "source": self.source,
            "entity_id": self.entity_id,
            "label": self.label,
            "value": self.value,
            "freshness": self.freshness,
        }


@dataclass(frozen=True)
class HarnessRequest:
    query: str
    session_id: str | None = None


@dataclass
class CapabilityResult:
    """Structured output returned by an allow-listed capability."""

    answer: str
    data: Any = None
    evidence: list[Evidence] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class HarnessResponse:
    status: ResponseStatus
    trace_id: str
    session_id: str
    answer: str | None = None
    question: str | None = None
    options: list[str] = field(default_factory=list)
    clarification_id: str | None = None
    intent: str | None = None
    skill_id: str | None = None
    skill_version: str | None = None
    data: Any = None
    evidence: list[Evidence] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "answer": self.answer,
            "question": self.question,
            "options": self.options,
            "clarification_id": self.clarification_id,
            "intent": self.intent,
            "skill": (
                {"id": self.skill_id, "version": self.skill_version}
                if self.skill_id
                else None
            ),
            "data": self.data,
            "evidence": [item.to_dict() for item in self.evidence],
            "warnings": self.warnings,
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "latency_ms": round(self.latency_ms, 3),
        }
