from __future__ import annotations

import pytest

from po_agent.harness.contracts import HarnessRequest, HarnessResponse, ResponseStatus
from po_agent.harness.semantic_core_v2 import DialogueAct
from po_agent.harness.semantic_correction_runtime_v2 import SemanticCorrectionRuntimeV2


class _SemanticStub:
    def __init__(self, *, act: str = "new") -> None:
        self._last: dict[str, dict] = {}
        self.act = act
        self.classify_calls = 0

    async def classify_dialogue_act(self, current: str, previous_query: str) -> DialogueAct:
        self.classify_calls += 1
        return DialogueAct(self.act, specific_correction=self.act == "correction")


class _ClarifyingInner:
    def __init__(self) -> None:
        self._pending: dict[str, object] = {}
        self.calls: list[str] = []

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        self.calls.append(request.query)
        session = request.session_id or ""
        if session in self._pending:
            self._pending.pop(session, None)
            return HarnessResponse(
                status=ResponseStatus.COMPLETED,
                trace_id=f"trace-{len(self.calls)}",
                session_id=session,
                answer="clarification consumed",
            )
        self._pending[session] = object()
        return HarnessResponse(
            status=ResponseStatus.NEEDS_CLARIFICATION,
            trace_id=f"trace-{len(self.calls)}",
            session_id=session,
            question="Уточните логин",
            clarification_id=f"{session}:member_login",
        )


class _RecordingInner:
    def __init__(self, semantic: _SemanticStub) -> None:
        self._pending: dict[str, object] = {}
        self.semantic = semantic
        self.semantic_state_seen: list[bool] = []

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        session = request.session_id or ""
        self.semantic_state_seen.append(session in self.semantic._last)
        return HarnessResponse(
            status=ResponseStatus.COMPLETED,
            trace_id=f"trace-{len(self.semantic_state_seen)}",
            session_id=session,
            answer=request.query,
        )


@pytest.mark.asyncio
async def test_repeating_request_that_opened_clarification_restarts_instead_of_becoming_answer() -> None:
    semantic = _SemanticStub()
    inner = _ClarifyingInner()
    runtime = SemanticCorrectionRuntimeV2(inner, semantic)
    query = "Покажи задачи сотрудника в спринте TEAM-SPRNT-2"

    first = await runtime.process(HarnessRequest(query=query, session_id="same-session"))
    second = await runtime.process(HarnessRequest(query=query, session_id="same-session"))

    assert first.status == ResponseStatus.NEEDS_CLARIFICATION
    assert second.status == ResponseStatus.NEEDS_CLARIFICATION
    assert inner.calls == [query, query]
    assert semantic.classify_calls == 0
    assert "same-session" in inner._pending


@pytest.mark.asyncio
async def test_new_independent_turn_does_not_inherit_semantic_previous_turn() -> None:
    semantic = _SemanticStub(act="new")
    inner = _RecordingInner(semantic)
    runtime = SemanticCorrectionRuntimeV2(inner, semantic)

    first = await runtime.process(HarnessRequest(query="Запрос A", session_id="dialogue"))
    assert first.status == ResponseStatus.COMPLETED

    # Emulate ConversationAwareSemanticInterpreter remembering A.
    semantic._last["dialogue"] = {
        "query": "Запрос A",
        "slots": {"sprint_id": "OLD-SPRNT-1"},
    }

    second = await runtime.process(HarnessRequest(query="Независимый запрос B", session_id="dialogue"))

    assert second.status == ResponseStatus.COMPLETED
    assert semantic.classify_calls == 1
    # Both first request and NEW B must enter the inner runtime without stale semantic history.
    assert inner.semantic_state_seen == [False, False]
    assert "dialogue" not in semantic._last
