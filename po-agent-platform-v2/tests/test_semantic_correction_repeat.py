from __future__ import annotations

import pytest

from po_agent.harness.contracts import HarnessRequest, HarnessResponse, ResponseStatus
from po_agent.harness.semantic_correction_runtime_v2 import SemanticCorrectionRuntimeV2


class FakeInner:
    def __init__(self) -> None:
        self._pending = {}
        self.calls: list[HarnessRequest] = []

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        self.calls.append(request)
        return HarnessResponse(
            status=ResponseStatus.COMPLETED,
            trace_id=f"trace-{len(self.calls)}",
            session_id=request.session_id,
            answer="ok",
            warnings=[],
        )


class ClassifierMustNotRun:
    def __init__(self) -> None:
        self._last: dict[str, object] = {}
        self.classify_calls = 0

    async def classify_dialogue_act(self, current: str, previous_query: str):
        self.classify_calls += 1
        raise AssertionError("exact repeated query must bypass correction classifier")


@pytest.mark.asyncio
async def test_exact_repeat_in_same_session_is_idempotent_rerun() -> None:
    inner = FakeInner()
    semantic = ClassifierMustNotRun()
    runtime = SemanticCorrectionRuntimeV2(inner, semantic)
    session = "repeat-session"
    query = "У кого наибольшая загрузка в спринте CRM-SPRNT-7?"

    first = await runtime.process(HarnessRequest(query=query, session_id=session))
    assert first.status == ResponseStatus.COMPLETED

    # Model the ConversationAwareSemanticInterpreter cache populated by turn 1.
    semantic._last[session] = {"query": query, "intent_hint": "team_workload"}

    second = await runtime.process(
        HarnessRequest(query="  У КОГО   НАИБОЛЬШАЯ загрузка в спринте CRM-SPRNT-7?  ", session_id=session)
    )

    assert second.status == ResponseStatus.COMPLETED
    assert len(inner.calls) == 2
    assert semantic.classify_calls == 0
    assert session not in semantic._last
    assert second.clarification_id is None
