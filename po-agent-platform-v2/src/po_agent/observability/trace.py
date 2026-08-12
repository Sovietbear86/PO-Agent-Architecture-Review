"""Execution Trace Model for PO Agent Platform v2.

Minimum fields:
- trace_id, request_id, session_id
- timestamp, request, intent
- intent_confidence, entities
- plan, capability_calls
- adapter_calls, llm_calls
- evidence_refs, warnings, errors
- latency, versions
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CapabilityCall(BaseModel):
    """Single capability call record."""
    capability: str
    input: dict
    output: dict
    latency_ms: float
    timestamp: datetime


class AdapterCall(BaseModel):
    """Single adapter call record."""
    adapter: str
    method: str
    input: dict
    output: dict | None
    latency_ms: float
    timestamp: datetime


class LLCall(BaseModel):
    """Single LLM call record."""
    model: str
    prompt_version: str
    input_messages: list[dict]
    output: dict
    latency_ms: float
    timestamp: datetime


class EvidenceRef(BaseModel):
    """Reference to evidence."""
    source_type: str
    source_id: str | None = None
    capability: str | None = None
    timestamp: datetime


class TraceRecord(BaseModel):
    """Execution trace record."""
    trace_id: str = Field(..., description="Unique trace identifier")
    request_id: str = Field(..., description="Unique request identifier")
    session_id: Optional[str] = Field(None, description="Session ID if available")

    timestamp: datetime = Field(default_factory=datetime.now)
    request: str = Field(..., description="User request text")

    intent: str = Field(..., description="Classified intent")
    intent_confidence: float = Field(..., ge=0.0, le=1.0, description="Intent confidence 0-1")
    entities: list = Field(default_factory=list, description="Extracted entities")

    plan: Optional[dict] = Field(None, description="Execution plan if multi-capability")

    capability_calls: list[CapabilityCall] = Field(default_factory=list)
    adapter_calls: list[AdapterCall] = Field(default_factory=list)
    llm_calls: list[LLCall] = Field(default_factory=list)

    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    latency_ms: float = Field(..., description="Total latency in milliseconds")

    # Version tracking
    agent_version: str = Field("1.0.0")
    router_version: str = Field("1.0.0")
    prompt_version: Optional[str] = Field(None)
    capability_versions: dict[str, str] = Field(default_factory=dict)
    model_version: Optional[str] = Field(None)


class TraceRecorder:
    """Recorder for execution traces."""

    def __init__(self):
        """Initialize trace recorder."""
        self.traces: list[TraceRecord] = []

    def record(
        self,
        trace_id: str,
        request_id: str,
        session_id: Optional[str],
        request: str,
        intent: str,
        intent_confidence: float,
        entities: list,
        capability_calls: list[CapabilityCall],
        adapter_calls: list[AdapterCall],
        llm_calls: list[LLCall],
        evidence_refs: list[EvidenceRef],
        warnings: list[str],
        errors: list[str],
        latency_ms: float,
        agent_version: str = "1.0.0",
        router_version: str = "1.0.0",
        prompt_version: Optional[str] = None,
        capability_versions: Optional[dict[str, str]] = None,
        model_version: Optional[str] = None,
    ) -> TraceRecord:
        """Record a trace.

        Args:
            trace_id: Unique trace identifier
            request_id: Unique request identifier
            session_id: Session ID
            request: User request text
            intent: Classified intent
            intent_confidence: Intent confidence
            entities: Extracted entities
            capability_calls: List of capability calls
            adapter_calls: List of adapter calls
            llm_calls: List of LLM calls
            evidence_refs: List of evidence references
            warnings: List of warnings
            errors: List of errors
            latency_ms: Total latency
            agent_version: Agent version
            router_version: Router version
            prompt_version: Prompt version
            capability_versions: Capability versions
            model_version: Model version

        Returns:
            Recorded trace record
        """
        record = TraceRecord(
            trace_id=trace_id,
            request_id=request_id,
            session_id=session_id,
            request=request,
            intent=intent,
            intent_confidence=intent_confidence,
            entities=entities,
            capability_calls=capability_calls,
            adapter_calls=adapter_calls,
            llm_calls=llm_calls,
            evidence_refs=evidence_refs,
            warnings=warnings,
            errors=errors,
            latency_ms=latency_ms,
            agent_version=agent_version,
            router_version=router_version,
            prompt_version=prompt_version,
            capability_versions=capability_versions or {},
            model_version=model_version,
        )

        self.traces.append(record)
        return record

    def get_trace(self, trace_id: str) -> Optional[TraceRecord]:
        """Get trace by ID.

        Args:
            trace_id: Trace ID

        Returns:
            Trace record or None
        """
        for trace in self.traces:
            if trace.trace_id == trace_id:
                return trace
        return None

    def get_traces_by_session(self, session_id: str) -> list[TraceRecord]:
        """Get all traces for a session.

        Args:
            session_id: Session ID

        Returns:
            List of trace records
        """
        return [t for t in self.traces if t.session_id == session_id]

    def get_traces_by_intent(self, intent: str) -> list[TraceRecord]:
        """Get all traces for an intent.

        Args:
            intent: Intent name

        Returns:
            List of trace records
        """
        return [t for t in self.traces if t.intent == intent]
