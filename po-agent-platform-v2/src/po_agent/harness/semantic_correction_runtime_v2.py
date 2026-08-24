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

    @staticmethod
    def _same_query(current: str, previous: str) -> bool:
        """Treat an exact natural-language repeat as an idempotent rerun."""
        normalize = lambda value: " ".join((value or "").split()).casefold()
        return bool(normalize(current)) and normalize(current) == normalize(previous)

    def _clear_semantic_previous_turn(self, session: str) -> None:
        """Clear only cached semantic history for one session.

        The user-visible Harness session remains intact. Independent requests must
        not inherit entity/filter slots from an older turn merely because they use
        the same session id.
        """
        resetter = getattr(self.semantic_interpreter, "reset_session", None)
        if callable(resetter):
            resetter(session)
            return
        state = getattr(self.semantic_interpreter, "_last", None)
        if isinstance(state, dict):
            state.pop(session, None)

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
        previous = self._last.get(session)

        pending = getattr(self.inner, "_pending", None)
        if isinstance(pending, dict) and session in pending:
            # A literal repeat of the request that opened a clarification is not an
            # answer to that clarification. Restart the request from clean semantic
            # state so repeating A yields the same interpretation of A instead of
            # consuming the whole sentence as (for example) a login answer.
            if previous is not None and self._same_query(current, previous.query):
                pending.pop(session, None)
                self._clear_semantic_previous_turn(session)
                response = await self.inner.process(HarnessRequest(query=current, session_id=session))
                self._last[session] = _PreviousTurn(current, response)
                return response

            response = await self.inner.process(HarnessRequest(query=current, session_id=session))
            if response.status != ResponseStatus.NEEDS_CLARIFICATION:
                self._last[session] = _PreviousTurn(previous.query if previous else current, response)
            return response

        if previous is None:
            # Defensive isolation for reused session ids after an outer runtime/test
            # lifecycle reset: no outer previous turn means no semantic previous turn.
            self._clear_semantic_previous_turn(session)
            response = await self.inner.process(HarnessRequest(query=current, session_id=session))
            self._last[session] = _PreviousTurn(current, response)
            return response

        if self._same_query(current, previous.query):
            self._clear_semantic_previous_turn(session)
            response = await self.inner.process(HarnessRequest(query=current, session_id=session))
            self._last[session] = _PreviousTurn(current, response)
            return response

        act = await self._classify(current, previous.query)
        if act.act == "new":
            # ConversationAwareSemanticInterpreter normally injects previous_turn for
            # every request in the same session. Once the correction classifier has
            # explicitly decided this is a NEW request, retaining that state is a
            # contamination bug: stale sprint/person/status slots may leak into B.
            self._clear_semantic_previous_turn(session)
            response = await self.inner.process(HarnessRequest(query=current, session_id=session))
            self._last[session] = _PreviousTurn(current, response)
            return response

        started = time.perf_counter()
        # For a real correction/recheck preserve the previous semantic turn. Reopen
        # its evidence chain first, then apply the correction in the same session.
        rechecked = await self.inner.process(HarnessRequest(query=previous.query, session_id=session))

        if act.act == "correction" and act.specific_correction:
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
