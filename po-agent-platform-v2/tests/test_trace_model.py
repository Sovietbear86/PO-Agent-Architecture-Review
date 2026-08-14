"""Tests for Execution Trace Model."""

import uuid
from datetime import datetime, timedelta

import pytest

from po_agent.observability.trace import (
    TraceRecord,
    TraceRecorder,
    CapabilityCall,
    AdapterCall,
    LLCall,
    EvidenceRef,
)


@pytest.fixture
def recorder():
    """Create trace recorder."""
    return TraceRecorder()


class TestTraceRecord:
    """Tests for TraceRecord."""

    def test_trace_record_creation(self, recorder):
        """Test trace record creation."""
        now = datetime.now()
        record = recorder.record(
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            session_id="session-1",
            request="покажи задачи",
            intent="task_search",
            intent_confidence=0.9,
            entities=[],
            capability_calls=[],
            adapter_calls=[],
            llm_calls=[],
            evidence_refs=[],
            warnings=[],
            errors=[],
            latency_ms=150.5,
        )

        assert record.trace_id is not None
        assert record.request_id is not None
        assert record.session_id == "session-1"
        assert record.request == "покажи задачи"
        assert record.intent == "task_search"
        assert record.intent_confidence == 0.9
        assert record.timestamp is not None
        assert record.latency_ms == 150.5

    def test_trace_record_with_versions(self, recorder):
        """Test trace record with version tracking."""
        record = recorder.record(
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            session_id=None,
            request="тест",
            intent="help",
            intent_confidence=0.0,
            entities=[],
            capability_calls=[],
            adapter_calls=[],
            llm_calls=[],
            evidence_refs=[],
            warnings=[],
            errors=[],
            latency_ms=10.0,
            agent_version="1.0.0",
            router_version="1.0.0",
            prompt_version="v1",
            capability_versions={"task_search": "1.0.0"},
            model_version="Qwen-Coder-3.7",
        )

        assert record.agent_version == "1.0.0"
        assert record.router_version == "1.0.0"
        assert record.prompt_version == "v1"
        assert record.capability_versions == {"task_search": "1.0.0"}
        assert record.model_version == "Qwen-Coder-3.7"

    def test_trace_record_with_capability_call(self, recorder):
        """Test trace record with capability call."""
        now = datetime.now()
        capability_call = CapabilityCall(
            capability="task_search",
            input={"query": "тест"},
            output={"results": []},
            latency_ms=50.0,
            timestamp=now,
        )

        record = recorder.record(
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            session_id=None,
            request="тест",
            intent="task_search",
            intent_confidence=0.9,
            entities=[],
            capability_calls=[capability_call],
            adapter_calls=[],
            llm_calls=[],
            evidence_refs=[],
            warnings=[],
            errors=[],
            latency_ms=50.0,
        )

        assert len(record.capability_calls) == 1
        assert record.capability_calls[0].capability == "task_search"

    def test_trace_record_with_adapter_call(self, recorder):
        """Test trace record with adapter call."""
        now = datetime.now()
        adapter_call = AdapterCall(
            adapter="swtr",
            method="search_tasks",
            input={"query": "test"},
            output={"tasks": []},
            latency_ms=100.0,
            timestamp=now,
        )

        record = recorder.record(
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            session_id=None,
            request="тест",
            intent="task_search",
            intent_confidence=0.9,
            entities=[],
            capability_calls=[],
            adapter_calls=[adapter_call],
            llm_calls=[],
            evidence_refs=[],
            warnings=[],
            errors=[],
            latency_ms=100.0,
        )

        assert len(record.adapter_calls) == 1
        assert record.adapter_calls[0].adapter == "swtr"

    def test_trace_record_with_llm_call(self, recorder):
        """Test trace record with LLM call."""
        now = datetime.now()
        llm_call = LLCall(
            model="Qwen-Coder-3.7",
            prompt_version="v1",
            input_messages=[{"role": "user", "content": "test"}],
            output={"choices": [{"message": {"content": "response"}}]},
            latency_ms=300.0,
            timestamp=now,
        )

        record = recorder.record(
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            session_id=None,
            request="тест",
            intent="task_summary",
            intent_confidence=0.9,
            entities=[],
            capability_calls=[],
            adapter_calls=[],
            llm_calls=[llm_call],
            evidence_refs=[],
            warnings=[],
            errors=[],
            latency_ms=300.0,
        )

        assert len(record.llm_calls) == 1
        assert record.llm_calls[0].model == "Qwen-Coder-3.7"


class TestTraceRecorder:
    """Tests for TraceRecorder."""

    def test_get_trace_by_id(self, recorder):
        """Test getting trace by ID."""
        trace_id = str(uuid.uuid4())
        recorder.record(
            trace_id=trace_id,
            request_id=str(uuid.uuid4()),
            session_id=None,
            request="тест",
            intent="help",
            intent_confidence=0.0,
            entities=[],
            capability_calls=[],
            adapter_calls=[],
            llm_calls=[],
            evidence_refs=[],
            warnings=[],
            errors=[],
            latency_ms=10.0,
        )

        result = recorder.get_trace(trace_id)
        assert result is not None
        assert result.trace_id == trace_id

    def test_get_trace_not_found(self, recorder):
        """Test getting non-existent trace."""
        result = recorder.get_trace("non-existent-id")
        assert result is None

    def test_get_traces_by_session(self, recorder):
        """Test getting traces by session."""
        session_id = "session-1"
        recorder.record(
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            session_id=session_id,
            request="тест 1",
            intent="help",
            intent_confidence=0.0,
            entities=[],
            capability_calls=[],
            adapter_calls=[],
            llm_calls=[],
            evidence_refs=[],
            warnings=[],
            errors=[],
            latency_ms=10.0,
        )
        recorder.record(
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            session_id=session_id,
            request="тест 2",
            intent="help",
            intent_confidence=0.0,
            entities=[],
            capability_calls=[],
            adapter_calls=[],
            llm_calls=[],
            evidence_refs=[],
            warnings=[],
            errors=[],
            latency_ms=10.0,
        )

        result = recorder.get_traces_by_session(session_id)
        assert len(result) == 2

    def test_get_traces_by_intent(self, recorder):
        """Test getting traces by intent."""
        recorder.record(
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            session_id=None,
            request="тест",
            intent="help",
            intent_confidence=0.0,
            entities=[],
            capability_calls=[],
            adapter_calls=[],
            llm_calls=[],
            evidence_refs=[],
            warnings=[],
            errors=[],
            latency_ms=10.0,
        )

        result = recorder.get_traces_by_intent("help")
        assert len(result) == 1


class TestTraceRecordValidation:
    """Tests for trace record validation."""

    def test_intent_confidence_range(self, recorder):
        """Test intent confidence range validation."""
        record = recorder.record(
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            session_id=None,
            request="тест",
            intent="help",
            intent_confidence=0.0,
            entities=[],
            capability_calls=[],
            adapter_calls=[],
            llm_calls=[],
            evidence_refs=[],
            warnings=[],
            errors=[],
            latency_ms=10.0,
        )
        assert 0.0 <= record.intent_confidence <= 1.0

    def test_default_timestamp(self, recorder):
        """Test default timestamp generation."""
        record = recorder.record(
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            session_id=None,
            request="тест",
            intent="help",
            intent_confidence=0.0,
            entities=[],
            capability_calls=[],
            adapter_calls=[],
            llm_calls=[],
            evidence_refs=[],
            warnings=[],
            errors=[],
            latency_ms=10.0,
        )
        assert record.timestamp is not None

    def test_default_entities(self, recorder):
        """Test default empty entities."""
        record = recorder.record(
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            session_id=None,
            request="тест",
            intent="help",
            intent_confidence=0.0,
            entities=[],
            capability_calls=[],
            adapter_calls=[],
            llm_calls=[],
            evidence_refs=[],
            warnings=[],
            errors=[],
            latency_ms=10.0,
        )
        assert record.entities == []
