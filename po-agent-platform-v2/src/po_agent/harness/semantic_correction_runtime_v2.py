"""Meaning-based correction/recheck runtime for production Harness.

Corrections are interpreted in the same conversation session against the previous
canonical semantic state. The runtime never creates a synthetic natural-language
mega-query, which previously allowed the model to lose or duplicate filters.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

from .contracts import HarnessRequest, HarnessResponse, ResponseStatus
from .semantic_core_v2 import DialogueAct


@dataclass
class _PreviousTurn:
    query: str
    response: HarnessResponse


class SemanticCorrectionRuntimeV2:
    def __init__(self, inner, semantic_interpreter) -> None:
        self.inner = inner
        self.semantic_interpreter = semantic_interpreter
        self._last: dict[str, _PreviousTurn] = {}
        for name in ("adapter", "router", "capabilities", "skills"):
            if hasattr(inner, name):
                setattr(self, name, getattr(inner, name))

    @staticmethod
    def _attach_meta(response: HarnessResponse, *, previous_trace: str, recheck_trace: str, correction: str, act: str) -> None:
        if response.data is None or not isinstance(response.data, dict):
            response.data = {} if response.data is None else {"result": response.data}
        meta = response.data.setdefault("_harness", {})
        if not isinstance(meta, dict):
            meta = {}
            response.data["_harness"] = meta
        meta["correction"] = {
            "dialogue_act": act,
            "correction_text": correction,
            "previous_trace_id": previous_trace,
            "recheck_trace_id": recheck_trace,
            "source_recheck_performed": True,
            "persistent_skill_mutation": False,
            "semantic_state_reused": True,
        }

    async def _classify(self, current: str, previous_query: str) -> DialogueAct:
        classifier = getattr(self.semantic_interpreter, "classify_dialogue_act", None)
        if not callable(classifier):
            return DialogueAct("new")
        try:
            return await classifier(current, previous_query)
        except Exception:
            return DialogueAct("new")

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        session = request.session_id or str(uuid.uuid4())
        current = (request.query or "").strip()

        pending = getattr(self.inner, "_pending", None)
        if isinstance(pending, dict) and session in pending:
            response = await self.inner.process(HarnessRequest(query=current, session_id=session))
            if response.status != ResponseStatus.NEEDS_CLARIFICATION:
                previous = self._last.get(session)
                self._last[session] = _PreviousTurn(previous.query if previous else current, response)
            return response

        previous = self._last.get(session)
        if previous is None:
            response = await self.inner.process(HarnessRequest(query=current, session_id=session))
            self._last[session] = _PreviousTurn(current, response)
            return response

        act = await self._classify(current, previous.query)
        if act.act == "new":
            response = await self.inner.process(HarnessRequest(query=current, session_id=session))
            self._last[session] = _PreviousTurn(current, response)
            return response

        started = time.perf_counter()
        # Reopen the previous evidence chain first. This also refreshes the
        # ConversationAwareSemanticInterpreter's previous_turn with the canonical
        # previous request before a correction is applied.
        rechecked = await self.inner.process(HarnessRequest(query=previous.query, session_id=session))

        if act.act == "correction" and act.specific_correction:
            # Pass only the user's correction in the SAME session. The semantic
            # interpreter receives previous_turn structurally from session state and
            # therefore merges slots without parsing an artificial combined sentence.
            corrected = await self.inner.process(HarnessRequest(query=current, session_id=session))
            self._attach_meta(
                corrected,
                previous_trace=previous.response.trace_id,
                recheck_trace=rechecked.trace_id,
                correction=current,
                act=act.act,
            )
            if "correction_recheck" not in corrected.warnings:
                corrected.warnings.append("correction_recheck")
            self._last[session] = _PreviousTurn(previous.query, corrected)
            return corrected

        question = act.clarification_question or (
            "Я заново перепроверил данные источника. Что именно нужно исправить в предыдущем запросе или результате?"
        )
        return HarnessResponse(
            status=ResponseStatus.NEEDS_CLARIFICATION,
            trace_id=str(uuid.uuid4()),
            session_id=session,
            question=question,
            clarification_id=f"{session}:semantic-correction",
            data={
                "_harness": {
                    "dialogue_state": "correction_clarification",
                    "correction": {
                        "dialogue_act": act.act,
                        "correction_text": current,
                        "previous_trace_id": previous.response.trace_id,
                        "recheck_trace_id": rechecked.trace_id,
                        "recheck_status": rechecked.status.value,
                        "source_recheck_performed": True,
                        "persistent_skill_mutation": False,
                        "semantic_state_reused": True,
                    },
                }
            },
            warnings=["negative_feedback", "source_rechecked", "clarification_required"],
            latency_ms=(time.perf_counter() - started) * 1000,
        )
